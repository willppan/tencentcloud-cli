# -*- coding: utf-8 -*-
"""
sync_upload 操作：本地 -> COS 同步上传
对齐 coscli sync (本地->COS) 命令
- thread_num: 单文件分块上传并发线程数（传给 SDK 的 MAXThread）
- routines: 文件间并发数（同时上传的文件数）
"""
import os
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from qcloud_cos import CosServiceError
from .utils import (init_cos_client, match_filters, build_cos_key, parse_meta,
                    list_all_objects, list_local_files, TransferProgressMonitor,
                    should_skip_sync_upload, build_extra_put_headers,
                    SnapshotDB, calculate_local_crc64)


def sync_upload_object(args, parsed_globals):
    """同步上传：本地目录 -> COS"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    local_path = args["local_path"]
    cos_prefix = args.get("cos_key", "") or ""
    recursive = args.get("recursive", False)
    # delete_extra 与 delete 互为别名，对齐 coscli --delete
    delete_extra = args.get("delete_extra", False) or args.get("delete", False)
    ignore_existing = args.get("ignore_existing", False)
    update = args.get("update", False)
    include = args.get("include", "") or ""
    exclude = args.get("exclude", "") or ""
    storage_class = args.get("storage_class", "") or ""
    content_type = args.get("content_type", "") or ""
    meta = args.get("meta", "") or ""
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
    skip_dir = args.get("skip_dir", False)
    disable_crc64 = args.get("disable_crc64", False)
    disable_all_symlink = args.get("disable_all_symlink", False)
    enable_symlink_dir = args.get("enable_symlink_dir", False)
    ignore_empty_file = args.get("ignore_empty_file", False)
    force = args.get("force", False)  # 保留占位，sync_upload 目前不涉及交互

    snapshot_path = args.get("snapshot_path", "") or ""
    backup_dir = args.get("backup_dir", "") or ""  # 删除多余前备份到本地目录

    # 构造扩展头（ACL/SSE/tags/forbid_overwrite）
    extra_headers = build_extra_put_headers(args)

    # 解析自定义元数据
    metadata = parse_meta(meta)

    if not os.path.isdir(local_path):
        print("Error: 本地路径不是目录: %s" % local_path)
        return

    # 打开快照数据库（若指定）
    snapshot_db = SnapshotDB.open(snapshot_path) if snapshot_path else None

    try:
        local_files = list_local_files(
            local_path,
            only_current_dir=only_current_dir,
            disable_all_symlink=disable_all_symlink,
            enable_symlink_dir=enable_symlink_dir,
        )
        cos_objects = list_all_objects(client, bucket, cos_prefix)

        # 收集本地空目录（skip_dir 时跳过）
        empty_dir_keys = []
        if not skip_dir and not only_current_dir:
            followlinks = enable_symlink_dir and not disable_all_symlink
            for root, dirs, files in os.walk(local_path, followlinks=followlinks):
                if not files and not dirs:
                    rel_dir = os.path.relpath(root, local_path).replace(os.sep, "/")
                    if rel_dir == ".":
                        dir_key = cos_prefix.rstrip("/") + "/" if cos_prefix else ""
                    else:
                        if not match_filters(rel_dir, include, exclude):
                            continue
                        dir_key = build_cos_key(cos_prefix, rel_dir) + "/"
                    if dir_key and dir_key not in cos_objects:
                        empty_dir_keys.append(dir_key)

        monitor = TransferProgressMonitor("upload")
        monitor.start()

        # 收集待上传的文件任务
        tasks = []
        total_size = 0
        skip_count = 0
        skip_size = 0
        for rel_path, file_info in local_files.items():
            # include/exclude 过滤
            if not match_filters(rel_path, include, exclude):
                skip_count += 1
                continue

            # 跳过空文件（coscli --ignore-empty-file）
            if ignore_empty_file and file_info["Size"] == 0:
                skip_count += 1
                continue

            cos_key = build_cos_key(cos_prefix, rel_path)

            # 增量同步：对齐 coscli sync 跳过逻辑
            # - 默认：对比本地 CRC64 与 COS CRC64（x-cos-hash-crc64ecma）
            # - --ignore-existing：目标存在即跳过
            # - --update：按 Last-Modified 时间比较
            # - snapshot_db：本地 {mtime, size} 与快照一致 → 快速跳过
            if should_skip_sync_upload(
                    client, bucket, cos_key,
                    file_info["FullPath"], file_info.get("MTime", 0),
                    ignore_existing=ignore_existing, update=update,
                    snapshot_db=snapshot_db):
                skip_count += 1
                skip_size += file_info["Size"]
                continue

            total_size += file_info["Size"]
            tasks.append((file_info, cos_key))

        # 设置扫描结果（文件数 + 空目录数 + 跳过数）
        monitor.set_scan_info(len(tasks) + len(empty_dir_keys) + skip_count, total_size + skip_size)
        # 跳过大小按平均分摊到每个 skip 记录
        avg_skip_size = skip_size // skip_count if skip_count > 0 else 0
        for i in range(skip_count):
            monitor.update_skip(avg_skip_size)

        def _is_retryable_error(e):
            try:
                code = int(e.get_status_code() or 0)
            except Exception:
                code = 0
            return code == 0 or code >= 500 or code in (408, 429)

        def _do_single(file_info, cos_key, progress_cb, file_id):
            """执行一次上传 + 可选 CRC64 校验"""
            kwargs = {
                "Bucket": bucket,
                "LocalFilePath": file_info["FullPath"],
                "Key": cos_key,
                "PartSize": part_size,
                "MAXThread": thread_num,
                "progress_callback": progress_cb,
            }
            if storage_class:
                kwargs["StorageClass"] = storage_class
            if content_type:
                kwargs["ContentType"] = content_type
            if metadata:
                kwargs["Metadata"] = metadata
            if rate_limiting:
                kwargs["TrafficLimit"] = str(int(rate_limiting) * 1024 * 1024 * 8)
            if extra_headers:
                kwargs.update(extra_headers)
            client.upload_file(**kwargs)

            # CRC64 校验（默认开启）
            if not disable_crc64:
                try:
                    head = client.head_object(Bucket=bucket, Key=cos_key)
                except Exception:
                    head = {}
                cos_crc = head.get("x-cos-hash-crc64ecma", "")
                if cos_crc:
                    local_crc = calculate_local_crc64(file_info["FullPath"])
                    if local_crc and local_crc != cos_crc:
                        raise CosServiceError("PUT", {
                            "code": "CRC64Mismatch",
                            "message": "CRC64 不一致（本地=%s, COS=%s）" % (local_crc, cos_crc),
                            "resource": cos_key,
                            "requestid": "",
                            "traceid": "",
                        }, 400)
                    # 更新快照
                    if snapshot_db is not None and local_crc:
                        snapshot_db.update(cos_key, file_info.get("MTime", 0),
                                           file_info["Size"], local_crc)
                else:
                    # 服务端未返回 CRC，也更新快照（使用 mtime+size 作为快照依据）
                    if snapshot_db is not None:
                        snapshot_db.update(cos_key, file_info.get("MTime", 0),
                                           file_info["Size"], "")
            else:
                # 关闭校验时也刷新快照（快速路径依赖 mtime+size）
                if snapshot_db is not None:
                    snapshot_db.update(cos_key, file_info.get("MTime", 0),
                                       file_info["Size"], "")

        def _do_upload(file_info, cos_key):
            """单个文件上传任务（含重试）"""
            last_err = None
            progress_cb, file_id = monitor.create_progress_callback(file_info["Size"])
            total_attempts = max(1, retry + 1)
            for attempt in range(total_attempts):
                try:
                    _do_single(file_info, cos_key, progress_cb, file_id)
                    monitor.update_ok(file_info["Size"], file_id)
                    return
                except CosServiceError as e:
                    last_err = e
                    if attempt < total_attempts - 1:
                        progress_cb, file_id = monitor.create_progress_callback(file_info["Size"])
                    elif err_retry_num > 0 and _is_retryable_error(e):
                        for extra in range(err_retry_num):
                            if err_retry_interval > 0:
                                time.sleep(err_retry_interval)
                            progress_cb, file_id = monitor.create_progress_callback(file_info["Size"])
                            try:
                                _do_single(file_info, cos_key, progress_cb, file_id)
                                monitor.update_ok(file_info["Size"], file_id)
                                return
                            except CosServiceError as e2:
                                last_err = e2
            if last_err is not None:
                err_reason = "%s (Code: %s)" % (last_err.get_error_msg(), last_err.get_error_code())
                monitor.update_err(file_id,
                                   src_path=file_info["FullPath"],
                                   dest_path="cos://%s/%s" % (bucket, cos_key),
                                   reason=err_reason,
                                   request_id=last_err.get_request_id())

        # 使用线程池并发上传多个文件
        if tasks:
            max_workers = min(routines, len(tasks))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_do_upload, file_info, cos_key)
                           for file_info, cos_key in tasks]
                for future in as_completed(futures):
                    future.result()

        # 在 COS 上创建空目录标记
        for dir_key in empty_dir_keys:
            try:
                client.put_object(Bucket=bucket, Key=dir_key, Body=b"")
                monitor.update_ok(0)
            except CosServiceError as e:
                monitor.update_err(src_path=dir_key,
                                   reason="创建空目录失败: %s (Code: %s)" % (e.get_error_msg(), e.get_error_code()),
                                   request_id=e.get_request_id())

        # 删除 COS 上多余的文件和文件夹
        deleted = 0
        if delete_extra:
            from .utils import list_all_objects_with_dirs
            cos_all_objects = list_all_objects_with_dirs(client, bucket, cos_prefix)
            for cos_key, obj_info in cos_all_objects.items():
                rel_key = cos_key[len(cos_prefix):].lstrip("/") if cos_prefix else cos_key
                if obj_info.get("IsDir"):
                    dir_rel = rel_key.rstrip("/")
                    if dir_rel and not os.path.isdir(os.path.join(local_path, dir_rel.replace("/", os.sep))):
                        # 备份目录对象（空对象，只记录路径）
                        _try_backup_cos_object(client, bucket, cos_key, backup_dir)
                        client.delete_object(Bucket=bucket, Key=cos_key)
                        deleted += 1
                        if snapshot_db is not None:
                            snapshot_db.remove(cos_key)
                else:
                    if rel_key not in local_files:
                        _try_backup_cos_object(client, bucket, cos_key, backup_dir)
                        client.delete_object(Bucket=bucket, Key=cos_key)
                        deleted += 1
                        if snapshot_db is not None:
                            snapshot_db.remove(cos_key)

        monitor.stop(log_file=effective_log)

        # 持久化快照
        if snapshot_db is not None:
            snapshot_db.save()

        if deleted > 0:
            print("已删除 COS 上多余文件: %d" % deleted)

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def _try_backup_cos_object(client, bucket, cos_key, backup_dir):
    """删除前将 COS 对象下载备份到本地 backup_dir。
    backup_dir 为空时不备份。失败仅告警，不影响主流程。
    """
    if not backup_dir:
        return
    try:
        if not os.path.isdir(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, cos_key.replace("/", "_"))
        client.download_file(Bucket=bucket, Key=cos_key, DestFilePath=backup_path)
    except Exception as e:
        import sys
        sys.stderr.write("警告：备份 cos://%s/%s 失败: %s\n" % (bucket, cos_key, str(e)))
        sys.stderr.flush()
