# -*- coding: utf-8 -*-
"""
sync_download 操作：COS -> 本地同步下载
对齐 coscli sync (COS->本地) 命令
- thread_num: 单文件分块下载并发线程数（传给 SDK 的 MAXThread）
- routines: 文件间并发数（同时下载的文件数）
"""
import os
import time
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from qcloud_cos import CosServiceError
from .utils import (init_cos_client, match_filters, build_cos_key,
                    list_all_objects, list_all_objects_with_dirs, list_local_files,
                    TransferProgressMonitor, should_skip_sync_download,
                    SnapshotDB, calculate_local_crc64)


def sync_download_object(args, parsed_globals):
    """同步下载：COS -> 本地目录"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    local_path = args["local_path"]
    cos_prefix = args.get("cos_key", "") or ""
    recursive = args.get("recursive", False)
    delete_extra = args.get("delete_extra", False) or args.get("delete", False)
    ignore_existing = args.get("ignore_existing", False)
    update = args.get("update", False)
    include = args.get("include", "") or ""
    exclude = args.get("exclude", "") or ""
    thread_num = args.get("thread_num", 5) or 5
    routines = args.get("routines", 3) or 3
    part_size = args.get("part_size", 20) or 20
    rate_limiting = args.get("rate_limiting", 0) or 0
    log_file = args.get("log_file", "") or ""
    retry = args.get("retry", 3)
    if retry is None:
        retry = 3
    retry = int(retry)

    # === coscli 对齐扩展参数 ===
    fail_output = args.get("fail_output", False)
    fail_output_path = args.get("fail_output_path", "") or ""
    effective_log = log_file or (fail_output_path if fail_output else "")

    err_retry_num = int(args.get("err_retry_num", 0) or 0)
    err_retry_interval = int(args.get("err_retry_interval", 0) or 0)

    only_current_dir = args.get("only_current_dir", False)
    disable_crc64 = args.get("disable_crc64", False)
    forbid_overwrite = args.get("forbid_overwrite", False)
    ignore_empty_file = args.get("ignore_empty_file", False)
    force = args.get("force", False)

    snapshot_path = args.get("snapshot_path", "") or ""
    backup_dir = args.get("backup_dir", "") or ""

    # SSE-C 参数
    sse_customer_algorithm = args.get("sse_customer_algorithm", "") or ""
    sse_customer_key = args.get("sse_customer_key", "") or ""
    sse_customer_key_md5 = args.get("sse_customer_key_md5", "") or ""

    snapshot_db = SnapshotDB.open(snapshot_path) if snapshot_path else None

    if not os.path.exists(local_path):
        os.makedirs(local_path)

    try:
        cos_objects = list_all_objects_with_dirs(client, bucket, cos_prefix)
        local_files = list_local_files(local_path)

        monitor = TransferProgressMonitor("download")
        monitor.start()

        # 收集待下载的文件任务
        tasks = []
        empty_dirs = []
        total_size = 0
        skip_count = 0
        skip_size = 0
        for cos_key, obj_info in cos_objects.items():
            rel_key = cos_key[len(cos_prefix):].lstrip("/") if cos_prefix else cos_key

            # 处理 COS 上的空目录对象
            if obj_info.get("IsDir"):
                if rel_key:
                    dir_rel = rel_key.rstrip("/")
                    if not match_filters(dir_rel, include, exclude):
                        skip_count += 1
                        continue
                    local_dir = os.path.join(local_path, dir_rel.replace("/", os.sep))
                    if local_dir and not os.path.exists(local_dir):
                        empty_dirs.append(local_dir)
                continue

            # only_current_dir：对齐一层目录
            if only_current_dir and "/" in rel_key:
                skip_count += 1
                continue

            # include/exclude 过滤
            if not match_filters(rel_key, include, exclude):
                skip_count += 1
                continue

            # 跳过空文件
            if ignore_empty_file and obj_info.get("Size", 0) == 0:
                skip_count += 1
                continue

            local_file = os.path.join(local_path, rel_key.replace("/", os.sep))

            # forbid_overwrite
            if forbid_overwrite and os.path.exists(local_file):
                skip_count += 1
                skip_size += obj_info["Size"]
                continue

            # 增量同步：跳过逻辑
            if should_skip_sync_download(
                    client, bucket, cos_key, obj_info, local_file,
                    ignore_existing=ignore_existing, update=update,
                    snapshot_db=snapshot_db):
                skip_count += 1
                skip_size += obj_info["Size"]
                continue

            total_size += obj_info["Size"]
            tasks.append((cos_key, local_file, obj_info["Size"]))

        monitor.set_scan_info(len(tasks) + len(empty_dirs) + skip_count, total_size + skip_size)
        avg_skip_size = skip_size // skip_count if skip_count > 0 else 0
        for i in range(skip_count):
            monitor.update_skip(avg_skip_size)

        # 预先创建所有需要的本地目录（避免并发时目录创建冲突）
        dir_lock = threading.Lock()
        created_dirs = set()

        def _ensure_dir(file_path):
            file_dir = os.path.dirname(file_path)
            if file_dir and file_dir not in created_dirs:
                with dir_lock:
                    if file_dir not in created_dirs:
                        if not os.path.exists(file_dir):
                            os.makedirs(file_dir)
                        created_dirs.add(file_dir)

        def _is_retryable_error(e):
            try:
                code = int(e.get_status_code() or 0)
            except Exception:
                code = 0
            return code == 0 or code >= 500 or code in (408, 429)

        def _do_single(cos_key, local_file, file_size, progress_cb):
            _ensure_dir(local_file)
            kwargs = {
                "Bucket": bucket,
                "Key": cos_key,
                "DestFilePath": local_file,
                "PartSize": part_size,
                "MAXThread": thread_num,
                "progress_callback": progress_cb,
            }
            if rate_limiting:
                kwargs["TrafficLimit"] = str(int(rate_limiting) * 1024 * 1024 * 8)
            if sse_customer_algorithm:
                kwargs["SSECustomerAlgorithm"] = sse_customer_algorithm
            if sse_customer_key:
                kwargs["SSECustomerKey"] = sse_customer_key
            if sse_customer_key_md5:
                kwargs["SSECustomerKeyMD5"] = sse_customer_key_md5
            client.download_file(**kwargs)

            # CRC64 校验
            if not disable_crc64:
                try:
                    head = client.head_object(Bucket=bucket, Key=cos_key)
                except Exception:
                    head = {}
                cos_crc = head.get("x-cos-hash-crc64ecma", "")
                if cos_crc:
                    local_crc = calculate_local_crc64(local_file)
                    if local_crc and local_crc != cos_crc:
                        raise CosServiceError("GET", {
                            "code": "CRC64Mismatch",
                            "message": "CRC64 不一致（本地=%s, COS=%s）" % (local_crc, cos_crc),
                            "resource": cos_key,
                            "requestid": "",
                            "traceid": "",
                        }, 400)
                    if snapshot_db is not None and local_crc:
                        try:
                            snapshot_db.update(cos_key,
                                               os.path.getmtime(local_file),
                                               os.path.getsize(local_file), local_crc)
                        except OSError:
                            pass
                else:
                    if snapshot_db is not None:
                        try:
                            snapshot_db.update(cos_key,
                                               os.path.getmtime(local_file),
                                               os.path.getsize(local_file), "")
                        except OSError:
                            pass
            else:
                if snapshot_db is not None:
                    try:
                        snapshot_db.update(cos_key,
                                           os.path.getmtime(local_file),
                                           os.path.getsize(local_file), "")
                    except OSError:
                        pass

        def _do_download(cos_key, local_file, file_size):
            last_err = None
            progress_cb, file_id = monitor.create_progress_callback(file_size)
            total_attempts = max(1, retry + 1)
            for attempt in range(total_attempts):
                try:
                    _do_single(cos_key, local_file, file_size, progress_cb)
                    monitor.update_ok(file_size, file_id)
                    return
                except CosServiceError as e:
                    last_err = e
                    if attempt < total_attempts - 1:
                        progress_cb, file_id = monitor.create_progress_callback(file_size)
                    elif err_retry_num > 0 and _is_retryable_error(e):
                        for extra in range(err_retry_num):
                            if err_retry_interval > 0:
                                time.sleep(err_retry_interval)
                            progress_cb, file_id = monitor.create_progress_callback(file_size)
                            try:
                                _do_single(cos_key, local_file, file_size, progress_cb)
                                monitor.update_ok(file_size, file_id)
                                return
                            except CosServiceError as e2:
                                last_err = e2
            if last_err is not None:
                err_reason = "%s (Code: %s)" % (last_err.get_error_msg(), last_err.get_error_code())
                monitor.update_err(file_id,
                                   src_path="cos://%s/%s" % (bucket, cos_key),
                                   dest_path=local_file,
                                   reason=err_reason,
                                   request_id=last_err.get_request_id())

        if tasks:
            max_workers = min(routines, len(tasks))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_do_download, cos_key, local_file, file_size)
                           for cos_key, local_file, file_size in tasks]
                for future in as_completed(futures):
                    future.result()

        # 在本地创建 COS 上的空目录
        for local_dir in empty_dirs:
            os.makedirs(local_dir, exist_ok=True)
            monitor.update_ok(0)

        # 删除本地多余的文件和空目录
        deleted = 0
        if delete_extra:
            # 第一步：删除多余的文件
            for rel_path, file_info in local_files.items():
                cos_key = build_cos_key(cos_prefix, rel_path)
                if cos_key not in cos_objects:
                    _try_backup_local(file_info["FullPath"], local_path, backup_dir)
                    os.remove(file_info["FullPath"])
                    deleted += 1
                    if snapshot_db is not None:
                        snapshot_db.remove(cos_key)
            # 第二步：删除多余的本地目录
            for root, dirs, files in os.walk(local_path, topdown=False):
                if root == local_path:
                    continue
                rel_dir = os.path.relpath(root, local_path).replace(os.sep, "/")
                cos_dir_key = build_cos_key(cos_prefix, rel_dir) + "/"
                dir_exists_in_cos = (cos_dir_key in cos_objects or
                                     any(k.startswith(cos_dir_key) for k in cos_objects))
                if not dir_exists_in_cos:
                    if not os.listdir(root):
                        os.rmdir(root)
                        deleted += 1

        monitor.stop(log_file=effective_log)

        if snapshot_db is not None:
            snapshot_db.save()

        if deleted > 0:
            print("已删除本地多余文件: %d" % deleted)

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def _try_backup_local(file_path, base_dir, backup_dir):
    """删除本地文件前，按相对路径将文件复制到 backup_dir"""
    if not backup_dir:
        return
    try:
        rel = os.path.relpath(file_path, base_dir)
        dest = os.path.join(backup_dir, rel)
        dest_dir = os.path.dirname(dest)
        if dest_dir and not os.path.isdir(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(file_path, dest)
    except Exception as e:
        import sys
        sys.stderr.write("警告：备份本地文件 %s 失败: %s\n" % (file_path, str(e)))
        sys.stderr.flush()
