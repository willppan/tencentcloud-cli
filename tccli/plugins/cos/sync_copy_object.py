# -*- coding: utf-8 -*-
"""
sync_copy 操作：COS -> COS 同步复制
对齐 coscli sync (COS->COS) 命令
- routines: 文件间并发数（同时复制的文件数）
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from qcloud_cos import CosServiceError
from .utils import (init_cos_client, match_filters, build_cos_key, parse_meta,
                    list_all_objects, list_all_objects_with_dirs,
                    TransferProgressMonitor, should_skip_sync_copy,
                    build_extra_copy_headers)


def sync_copy_object(args, parsed_globals):
    """同步复制：COS -> COS"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    cos_prefix = args.get("cos_key", "") or ""
    dest_bucket = args.get("dest_bucket", bucket) or bucket
    dest_prefix = args.get("dest_key", "") or ""
    dest_region = args.get("dest_region", region) or region
    recursive = args.get("recursive", False)
    delete_extra = args.get("delete_extra", False) or args.get("delete", False)
    ignore_existing = args.get("ignore_existing", False)
    update = args.get("update", False)
    include = args.get("include", "") or ""
    exclude = args.get("exclude", "") or ""
    storage_class = args.get("storage_class", "") or ""
    meta = args.get("meta", "") or ""
    routines = args.get("routines", 3) or 3
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
    ignore_empty_file = args.get("ignore_empty_file", False)
    force = args.get("force", False)

    # 构造扩展头
    extra_headers = build_extra_copy_headers(args)

    # 解析自定义元数据
    metadata = parse_meta(meta)

    try:
        src_objects = list_all_objects_with_dirs(client, bucket, cos_prefix)
        dest_objects = list_all_objects(client, dest_bucket, dest_prefix)

        monitor = TransferProgressMonitor("copy")
        monitor.start()

        # 收集待复制的文件任务
        tasks = []
        empty_dir_keys = []
        total_size = 0
        skip_count = 0
        skip_size = 0
        for src_key, obj_info in src_objects.items():
            rel_key = src_key[len(cos_prefix):].lstrip("/") if cos_prefix else src_key

            # 处理 / 结尾的空目录对象
            if obj_info.get("IsDir"):
                if skip_dir:
                    skip_count += 1
                    continue
                if rel_key:
                    dir_rel = rel_key.rstrip("/")
                    if not match_filters(dir_rel, include, exclude):
                        skip_count += 1
                        continue
                    d_key = build_cos_key(dest_prefix, rel_key)
                    if not d_key.endswith("/"):
                        d_key += "/"
                    if d_key not in dest_objects:
                        empty_dir_keys.append(d_key)
                continue

            # only_current_dir：对齐一层
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

            dest_key = build_cos_key(dest_prefix, rel_key)

            # 增量同步：跳过逻辑
            if should_skip_sync_copy(
                    client, bucket, src_key, dest_bucket, dest_key,
                    ignore_existing=ignore_existing, update=update):
                skip_count += 1
                skip_size += obj_info["Size"]
                continue

            total_size += obj_info["Size"]
            tasks.append((src_key, dest_key, obj_info["Size"]))

        monitor.set_scan_info(len(tasks) + len(empty_dir_keys) + skip_count, total_size + skip_size)
        avg_skip_size = skip_size // skip_count if skip_count > 0 else 0
        for i in range(skip_count):
            monitor.update_skip(avg_skip_size)

        def _is_retryable_error(e):
            try:
                code = int(e.get_status_code() or 0)
            except Exception:
                code = 0
            return code == 0 or code >= 500 or code in (408, 429)

        def _do_single(src_key, dest_key):
            source = {
                "Bucket": bucket,
                "Key": src_key,
                "Region": region,
            }
            kwargs = {
                "Bucket": dest_bucket,
                "Key": dest_key,
                "CopySource": source,
            }
            if storage_class:
                kwargs["StorageClass"] = storage_class
            if metadata:
                # SDK 命名参数 CopyStatus='Replaced' 对应 x-cos-metadata-directive
                kwargs["Metadata"] = metadata
                kwargs["CopyStatus"] = "Replaced"
            if extra_headers:
                kwargs.update(extra_headers)
            client.copy(**kwargs)

        def _do_copy(src_key, dest_key, file_size):
            last_err = None
            total_attempts = max(1, retry + 1)
            for attempt in range(total_attempts):
                try:
                    _do_single(src_key, dest_key)
                    monitor.update_ok(file_size)
                    return
                except CosServiceError as e:
                    last_err = e
                    if attempt >= total_attempts - 1 and err_retry_num > 0 and _is_retryable_error(e):
                        for extra in range(err_retry_num):
                            if err_retry_interval > 0:
                                time.sleep(err_retry_interval)
                            try:
                                _do_single(src_key, dest_key)
                                monitor.update_ok(file_size)
                                return
                            except CosServiceError as e2:
                                last_err = e2
            if last_err is not None:
                err_reason = "%s (Code: %s)" % (last_err.get_error_msg(), last_err.get_error_code())
                monitor.update_err(src_path="cos://%s/%s" % (bucket, src_key),
                                   dest_path="cos://%s/%s" % (dest_bucket, dest_key),
                                   reason=err_reason,
                                   request_id=last_err.get_request_id())

        if tasks:
            max_workers = min(routines, len(tasks))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_do_copy, src_key, dest_key, file_size)
                           for src_key, dest_key, file_size in tasks]
                for future in as_completed(futures):
                    future.result()

        # 在目标 COS 上创建空目录标记
        if not skip_dir:
            for d_key in empty_dir_keys:
                try:
                    client.put_object(Bucket=dest_bucket, Key=d_key, Body=b"")
                    monitor.update_ok(0)
                except CosServiceError as e:
                    monitor.update_err(src_path="cos://%s/%s" % (dest_bucket, d_key),
                                       reason="创建空目录失败: %s (Code: %s)" % (e.get_error_msg(), e.get_error_code()),
                                       request_id=e.get_request_id())

        # 删除目标多余的文件和文件夹
        deleted = 0
        if delete_extra:
            dest_all_objects = list_all_objects_with_dirs(client, dest_bucket, dest_prefix)
            for dest_key, obj_info in dest_all_objects.items():
                rel_key = dest_key[len(dest_prefix):].lstrip("/") if dest_prefix else dest_key
                src_key = build_cos_key(cos_prefix, rel_key)
                if obj_info.get("IsDir"):
                    src_dir_key = src_key if src_key.endswith("/") else src_key + "/"
                    if src_dir_key not in src_objects:
                        client.delete_object(Bucket=dest_bucket, Key=dest_key)
                        deleted += 1
                else:
                    if src_key not in src_objects:
                        client.delete_object(Bucket=dest_bucket, Key=dest_key)
                        deleted += 1

        monitor.stop(log_file=effective_log)

        if deleted > 0:
            print("已删除目标端多余文件: %d" % deleted)

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))
