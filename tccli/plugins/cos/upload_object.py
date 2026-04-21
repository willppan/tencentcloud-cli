# -*- coding: utf-8 -*-
"""
upload 操作：上传本地文件到 COS
对齐 coscli cp (本地->COS) 命令
- thread_num: 单文件分块上传并发线程数（传给 SDK 的 MAXThread）
- routines: 文件间并发数（同时上传的文件数）
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from qcloud_cos import CosServiceError
from .utils import (init_cos_client, match_filters, parse_meta,
                    build_extra_put_headers, TransferProgressMonitor,
                    calculate_local_crc64)


def upload_object(args, parsed_globals):
    """上传本地文件到 COS"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    local_path = args["local_path"]
    cos_key = args["cos_key"]
    storage_class = args.get("storage_class", "") or ""
    content_type = args.get("content_type", "") or ""
    meta = args.get("meta", "") or ""
    recursive = args.get("recursive", False)
    include = args.get("include", "") or ""
    exclude = args.get("exclude", "") or ""
    thread_num = args.get("thread_num", 5) or 5
    routines = args.get("routines", 3) or 3
    part_size = args.get("part_size", 20) or 20
    rate_limiting = args.get("rate_limiting", 0) or 0
    retry = args.get("retry", 3)
    if retry is None:
        retry = 3
    retry = int(retry)

    # === coscli 对齐扩展参数 ===
    # 日志
    log_file = args.get("log_file", "") or ""
    fail_output = args.get("fail_output", False)
    fail_output_path = args.get("fail_output_path", "") or ""
    # 仅当启用 fail_output 时才写日志；若同时指定 log_file，则 log_file 优先
    effective_log = log_file or (fail_output_path if fail_output else "")

    # 可重试错误的额外控制
    err_retry_num = int(args.get("err_retry_num", 0) or 0)
    err_retry_interval = int(args.get("err_retry_interval", 0) or 0)

    # 范围控制
    only_current_dir = args.get("only_current_dir", False)
    skip_dir = args.get("skip_dir", False)

    # 校验开关
    disable_crc64 = args.get("disable_crc64", False)

    # 符号链接
    disable_all_symlink = args.get("disable_all_symlink", False)
    enable_symlink_dir = args.get("enable_symlink_dir", False)

    # 构造扩展头（ACL/SSE/tags/forbid_overwrite）
    extra_headers = build_extra_put_headers(args)

    # 解析自定义元数据
    metadata = parse_meta(meta)

    try:
        if recursive and os.path.isdir(local_path):
            # 对齐 coscli cp 行为：
            # - local_path 以 / 结尾（如 /tmp/dir/）：不保留目录名，直接映射内容
            # - local_path 不以 / 结尾（如 /tmp/dir）：保留目录名，映射为 cos_key/dir/
            if not local_path.endswith(os.sep) and not local_path.endswith("/"):
                dir_name = os.path.basename(local_path.rstrip(os.sep))
                if cos_key:
                    cos_key = cos_key.rstrip("/") + "/" + dir_name + "/"
                else:
                    cos_key = dir_name + "/"
            _upload_directory(client, bucket, local_path, cos_key, include, exclude,
                              storage_class, content_type, metadata, thread_num, routines,
                              part_size, rate_limiting, retry, effective_log,
                              extra_headers=extra_headers,
                              err_retry_num=err_retry_num,
                              err_retry_interval=err_retry_interval,
                              only_current_dir=only_current_dir,
                              skip_dir=skip_dir,
                              disable_crc64=disable_crc64,
                              disable_all_symlink=disable_all_symlink,
                              enable_symlink_dir=enable_symlink_dir)
        else:
            if not os.path.exists(local_path):
                print("Error: 本地文件不存在: %s" % local_path)
                return
            if not os.path.isfile(local_path):
                print("Error: 指定路径不是文件: %s（如需上传目录请使用 --recursive true）" % local_path)
                return

            _upload_single(client, bucket, local_path, cos_key,
                           storage_class, content_type, metadata, thread_num, part_size,
                           rate_limiting, retry, effective_log,
                           extra_headers=extra_headers,
                           err_retry_num=err_retry_num,
                           err_retry_interval=err_retry_interval,
                           disable_crc64=disable_crc64)

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))
    except Exception as e:
        print("Error: %s" % str(e))


def _build_upload_kwargs(bucket, local_path, cos_key, storage_class, content_type,
                         metadata, thread_num, part_size, rate_limiting,
                         extra_headers=None):
    """构造 upload_file 的参数"""
    kwargs = {
        "Bucket": bucket,
        "LocalFilePath": local_path,
        "Key": cos_key,
        "PartSize": part_size,
        "MAXThread": thread_num,
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
    return kwargs


def _is_retryable_error(e):
    """判断 CosServiceError 是否属于可重试错误（服务端错误/网络超时类）。"""
    try:
        code = int(e.get_status_code() or 0)
    except Exception:
        code = 0
    return code == 0 or code >= 500 or code in (408, 429)


def _verify_crc64(client, bucket, cos_key, local_path):
    """上传后 CRC64 校验，返回 (ok, msg)"""
    try:
        head = client.head_object(Bucket=bucket, Key=cos_key)
    except Exception as e:
        return False, "head_object 失败: %s" % str(e)
    cos_crc = head.get("x-cos-hash-crc64ecma", "")
    if not cos_crc:
        return True, ""  # 服务端未返回，视为通过
    local_crc = calculate_local_crc64(local_path)
    if local_crc is None:
        return True, ""  # 本地无法计算（未安装 crcmod），跳过
    if local_crc != cos_crc:
        return False, "CRC64 不一致（本地=%s, COS=%s）" % (local_crc, cos_crc)
    return True, ""


def _upload_with_retry(client, monitor, full_path, cos_key, file_size,
                       build_kwargs, retry, err_retry_num, err_retry_interval,
                       bucket, disable_crc64):
    """封装上传 + 重试 + CRC64 校验的通用逻辑。"""
    last_err = None
    progress_cb, file_id = monitor.create_progress_callback(file_size)
    # 总重试次数 = retry + err_retry_num（err_retry_num 仅对"可重试错误"生效）
    total_attempts = max(1, retry + 1)
    for attempt in range(total_attempts):
        try:
            kwargs = build_kwargs()
            kwargs["progress_callback"] = progress_cb
            client.upload_file(**kwargs)
            # 校验 CRC64
            if not disable_crc64:
                ok, msg = _verify_crc64(client, bucket, cos_key, full_path)
                if not ok:
                    raise CosServiceError("PUT", {
                        "code": "CRC64Mismatch",
                        "message": msg,
                        "resource": cos_key,
                        "requestid": "",
                        "traceid": "",
                    }, 400)
            monitor.update_ok(file_size, file_id)
            return None
        except CosServiceError as e:
            last_err = e
            if attempt < total_attempts - 1:
                progress_cb, file_id = monitor.create_progress_callback(file_size)
            elif err_retry_num > 0 and _is_retryable_error(e):
                # 超出 retry 后，若为可重试错误，再重试 err_retry_num 次
                for extra in range(err_retry_num):
                    if err_retry_interval > 0:
                        time.sleep(err_retry_interval)
                    progress_cb, file_id = monitor.create_progress_callback(file_size)
                    try:
                        kwargs = build_kwargs()
                        kwargs["progress_callback"] = progress_cb
                        client.upload_file(**kwargs)
                        if not disable_crc64:
                            ok, msg = _verify_crc64(client, bucket, cos_key, full_path)
                            if not ok:
                                raise CosServiceError("PUT", {
                                    "code": "CRC64Mismatch",
                                    "message": msg,
                                    "resource": cos_key,
                                    "requestid": "",
                                    "traceid": "",
                                }, 400)
                        monitor.update_ok(file_size, file_id)
                        return None
                    except CosServiceError as e2:
                        last_err = e2
    return last_err


def _upload_single(client, bucket, local_path, cos_key,
                   storage_class, content_type, metadata, thread_num, part_size,
                   rate_limiting, retry=3, log_file="",
                   extra_headers=None, err_retry_num=0, err_retry_interval=0,
                   disable_crc64=False):
    """上传单个文件（带进度监控）"""
    monitor = TransferProgressMonitor("upload")
    file_size = os.path.getsize(local_path)
    monitor.set_scan_info(1, file_size)
    monitor.start()

    def _build():
        return _build_upload_kwargs(bucket, local_path, cos_key, storage_class, content_type,
                                    metadata, thread_num, part_size, rate_limiting,
                                    extra_headers=extra_headers)

    last_err = _upload_with_retry(client, monitor, local_path, cos_key, file_size,
                                  _build, retry, err_retry_num, err_retry_interval,
                                  bucket, disable_crc64)

    if last_err is not None:
        err_reason = "%s (Code: %s)" % (last_err.get_error_msg(), last_err.get_error_code())
        monitor.update_err(src_path=local_path,
                           dest_path="cos://%s/%s" % (bucket, cos_key),
                           reason=err_reason,
                           request_id=last_err.get_request_id())
    monitor.stop(log_file=log_file)
    if last_err is not None:
        raise last_err


def _upload_directory(client, bucket, local_dir, cos_prefix, include, exclude,
                      storage_class, content_type, metadata, thread_num, routines,
                      part_size, rate_limiting, retry=3, log_file="",
                      extra_headers=None, err_retry_num=0, err_retry_interval=0,
                      only_current_dir=False, skip_dir=False,
                      disable_crc64=False,
                      disable_all_symlink=False, enable_symlink_dir=False):
    """递归上传目录
    - thread_num: 单文件分块并发（传给 SDK MAXThread）
    - routines: 文件间并发（同时上传的文件数）
    """
    monitor = TransferProgressMonitor("upload")
    monitor.start()

    # 先收集所有待上传的文件任务，同时统计总大小
    tasks = []
    empty_dir_keys = []  # 空目录对应的 COS key（以 / 结尾的空对象）
    total_size = 0
    skip_count = 0

    # 决定遍历方式
    if only_current_dir:
        # 仅当前一层
        walker = [(local_dir, [], [f for f in os.listdir(local_dir)
                                    if os.path.isfile(os.path.join(local_dir, f))])]
    else:
        # followlinks 控制是否跟随符号链接目录
        followlinks = enable_symlink_dir and not disable_all_symlink
        walker = os.walk(local_dir, followlinks=followlinks)

    for root, dirs, files in walker:
        # 过滤符号链接目录（在 walk 过程中）
        if not only_current_dir:
            if disable_all_symlink:
                dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
            elif not enable_symlink_dir:
                dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]

        # 检测空目录（仅在不 skip_dir 时创建目录标记）
        if not skip_dir and not files and not dirs:
            rel_dir = os.path.relpath(root, local_dir).replace(os.sep, "/")
            if rel_dir == ".":
                dir_key = cos_prefix.rstrip("/") + "/" if cos_prefix else ""
            else:
                if not match_filters(rel_dir, include, exclude):
                    skip_count += 1
                    continue
                if cos_prefix:
                    if cos_prefix.endswith("/"):
                        dir_key = cos_prefix + rel_dir + "/"
                    else:
                        dir_key = cos_prefix + "/" + rel_dir + "/"
                else:
                    dir_key = rel_dir + "/"
            if dir_key:
                empty_dir_keys.append(dir_key)

        for filename in files:
            full_path = os.path.join(root, filename)

            # 过滤符号链接文件
            if disable_all_symlink and os.path.islink(full_path):
                skip_count += 1
                continue

            rel_path = os.path.relpath(full_path, local_dir).replace(os.sep, "/")

            # include/exclude 过滤
            if not match_filters(rel_path, include, exclude):
                skip_count += 1
                continue

            # 构造 COS key
            if cos_prefix:
                if cos_prefix.endswith("/"):
                    key = cos_prefix + rel_path
                else:
                    key = cos_prefix + "/" + rel_path
            else:
                key = rel_path

            try:
                file_size = os.path.getsize(full_path)
            except OSError:
                skip_count += 1
                continue
            total_size += file_size
            tasks.append((full_path, key, file_size))

    # 设置扫描结果（文件数 + 空目录数 + 跳过数）
    monitor.set_scan_info(len(tasks) + len(empty_dir_keys) + skip_count, total_size)
    for _ in range(skip_count):
        monitor.update_skip(0)

    def _do_upload(full_path, key, file_size):
        """单个文件上传任务（含重试）"""
        def _build():
            return _build_upload_kwargs(bucket, full_path, key, storage_class, content_type,
                                        metadata, thread_num, part_size, rate_limiting,
                                        extra_headers=extra_headers)

        last_err = _upload_with_retry(client, monitor, full_path, key, file_size,
                                      _build, retry, err_retry_num, err_retry_interval,
                                      bucket, disable_crc64)
        if last_err is not None:
            err_reason = "%s (Code: %s)" % (last_err.get_error_msg(), last_err.get_error_code())
            monitor.update_err(src_path=full_path,
                               dest_path="cos://%s/%s" % (bucket, key),
                               reason=err_reason,
                               request_id=last_err.get_request_id())

    # 使用线程池并发上传多个文件，routines 控制文件间并发
    if tasks:
        max_workers = min(routines, len(tasks))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for full_path, key, file_size in tasks:
                futures.append(executor.submit(_do_upload, full_path, key, file_size))
            for future in as_completed(futures):
                future.result()

    # 在 COS 上创建空目录标记（以 / 结尾的空对象），skip_dir 时跳过
    if not skip_dir:
        for dir_key in empty_dir_keys:
            try:
                client.put_object(Bucket=bucket, Key=dir_key, Body=b"")
                monitor.update_ok(0)
            except CosServiceError as e:
                monitor.update_err(src_path=dir_key,
                                   reason="创建空目录失败: %s (Code: %s)" % (e.get_error_msg(), e.get_error_code()),
                                   request_id=e.get_request_id())

    monitor.stop(log_file=log_file)