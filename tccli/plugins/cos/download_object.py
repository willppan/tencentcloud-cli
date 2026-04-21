# -*- coding: utf-8 -*-
"""
download 操作：从 COS 下载文件到本地
对齐 coscli cp (COS->本地) 命令
- thread_num: 单文件分块下载并发线程数（传给 SDK 的 MAXThread）
- routines: 文件间并发数（同时下载的文件数）
"""
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from qcloud_cos import CosServiceError
from .utils import (init_cos_client, match_filters, TransferProgressMonitor,
                    calculate_local_crc64)


def download_object(args, parsed_globals):
    """从 COS 下载文件到本地"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    cos_key = args["cos_key"]
    local_path = args["local_path"]
    recursive = args.get("recursive", False)
    include = args.get("include", "") or ""
    exclude = args.get("exclude", "") or ""
    thread_num = args.get("thread_num", 5) or 5
    routines = args.get("routines", 3) or 3
    part_size = args.get("part_size", 20) or 20
    rate_limiting = args.get("rate_limiting", 0) or 0
    version_id = args.get("version_id", "") or ""
    retry = args.get("retry", 3)
    if retry is None:
        retry = 3
    retry = int(retry)

    # === coscli 对齐扩展参数 ===
    log_file = args.get("log_file", "") or ""
    fail_output = args.get("fail_output", False)
    fail_output_path = args.get("fail_output_path", "") or ""
    effective_log = log_file or (fail_output_path if fail_output else "")

    err_retry_num = int(args.get("err_retry_num", 0) or 0)
    err_retry_interval = int(args.get("err_retry_interval", 0) or 0)

    only_current_dir = args.get("only_current_dir", False)
    disable_crc64 = args.get("disable_crc64", False)
    forbid_overwrite = args.get("forbid_overwrite", False)

    # SSE-C 下载参数（上传时加密过的对象，下载也必须带）
    sse_customer_algorithm = args.get("sse_customer_algorithm", "") or ""
    sse_customer_key = args.get("sse_customer_key", "") or ""
    sse_customer_key_md5 = args.get("sse_customer_key_md5", "") or ""

    try:
        if recursive:
            _download_directory(client, bucket, cos_key, local_path, include, exclude,
                                thread_num, routines, part_size, rate_limiting, version_id,
                                effective_log, retry,
                                err_retry_num=err_retry_num,
                                err_retry_interval=err_retry_interval,
                                only_current_dir=only_current_dir,
                                disable_crc64=disable_crc64,
                                forbid_overwrite=forbid_overwrite,
                                sse_customer_algorithm=sse_customer_algorithm,
                                sse_customer_key=sse_customer_key,
                                sse_customer_key_md5=sse_customer_key_md5)
        else:
            # 确保本地目录存在
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)

            _download_single(client, bucket, cos_key, local_path,
                             thread_num, part_size, rate_limiting, version_id,
                             effective_log, retry,
                             err_retry_num=err_retry_num,
                             err_retry_interval=err_retry_interval,
                             disable_crc64=disable_crc64,
                             forbid_overwrite=forbid_overwrite,
                             sse_customer_algorithm=sse_customer_algorithm,
                             sse_customer_key=sse_customer_key,
                             sse_customer_key_md5=sse_customer_key_md5)

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))
    except Exception as e:
        print("Error: %s" % str(e))


def _build_download_kwargs(bucket, cos_key, local_path, thread_num, part_size, rate_limiting,
                           version_id, sse_customer_algorithm="", sse_customer_key="",
                           sse_customer_key_md5=""):
    """构造 download_file 的参数"""
    kwargs = {
        "Bucket": bucket,
        "Key": cos_key,
        "DestFilePath": local_path,
        "PartSize": part_size,
        "MAXThread": thread_num,
    }
    if rate_limiting:
        kwargs["TrafficLimit"] = str(int(rate_limiting) * 1024 * 1024 * 8)
    if version_id:
        kwargs["VersionId"] = version_id
    if sse_customer_algorithm:
        kwargs["SSECustomerAlgorithm"] = sse_customer_algorithm
    if sse_customer_key:
        kwargs["SSECustomerKey"] = sse_customer_key
    if sse_customer_key_md5:
        kwargs["SSECustomerKeyMD5"] = sse_customer_key_md5
    return kwargs


def _is_retryable_error(e):
    """判断 CosServiceError 是否属于可重试错误（服务端错误/网络超时类）。"""
    try:
        code = int(e.get_status_code() or 0)
    except Exception:
        code = 0
    return code == 0 or code >= 500 or code in (408, 429)


def _verify_local_crc64(client, bucket, cos_key, local_path, version_id=""):
    """下载后 CRC64 校验"""
    try:
        head_kwargs = {"Bucket": bucket, "Key": cos_key}
        if version_id:
            head_kwargs["VersionId"] = version_id
        head = client.head_object(**head_kwargs)
    except Exception:
        return True, ""
    cos_crc = head.get("x-cos-hash-crc64ecma", "")
    if not cos_crc:
        return True, ""
    local_crc = calculate_local_crc64(local_path)
    if local_crc is None:
        return True, ""
    if local_crc != cos_crc:
        return False, "CRC64 不一致（本地=%s, COS=%s）" % (local_crc, cos_crc)
    return True, ""


def _download_with_retry(client, monitor, cos_key, local_path, file_size,
                         build_kwargs, retry, err_retry_num, err_retry_interval,
                         bucket, disable_crc64, version_id):
    """下载 + 重试 + CRC64 校验通用逻辑"""
    last_err = None
    progress_cb, file_id = monitor.create_progress_callback(file_size)
    total_attempts = max(1, retry + 1)
    for attempt in range(total_attempts):
        try:
            kwargs = build_kwargs()
            kwargs["progress_callback"] = progress_cb
            client.download_file(**kwargs)
            if not disable_crc64:
                ok, msg = _verify_local_crc64(client, bucket, cos_key, local_path, version_id)
                if not ok:
                    raise CosServiceError("GET", "CRC64Mismatch", 400, "CRC64Mismatch", msg, "")
            monitor.update_ok(file_size, file_id)
            return None
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
                        kwargs = build_kwargs()
                        kwargs["progress_callback"] = progress_cb
                        client.download_file(**kwargs)
                        if not disable_crc64:
                            ok, msg = _verify_local_crc64(client, bucket, cos_key, local_path, version_id)
                            if not ok:
                                raise CosServiceError("GET", "CRC64Mismatch", 400,
                                                      "CRC64Mismatch", msg, "")
                        monitor.update_ok(file_size, file_id)
                        return None
                    except CosServiceError as e2:
                        last_err = e2
    return last_err


def _download_single(client, bucket, cos_key, local_path,
                     thread_num, part_size, rate_limiting, version_id, log_file="", retry=3,
                     err_retry_num=0, err_retry_interval=0,
                     disable_crc64=False, forbid_overwrite=False,
                     sse_customer_algorithm="", sse_customer_key="", sse_customer_key_md5=""):
    """下载单个文件（带进度监控）"""
    if forbid_overwrite and os.path.exists(local_path):
        print("Error: 本地文件已存在，--forbid_overwrite 开启，不覆盖: %s" % local_path)
        return

    monitor = TransferProgressMonitor("download")

    # 先获取文件大小
    try:
        head_kwargs = {"Bucket": bucket, "Key": cos_key}
        if version_id:
            head_kwargs["VersionId"] = version_id
        if sse_customer_algorithm:
            head_kwargs["SSECustomerAlgorithm"] = sse_customer_algorithm
        if sse_customer_key:
            head_kwargs["SSECustomerKey"] = sse_customer_key
        if sse_customer_key_md5:
            head_kwargs["SSECustomerKeyMD5"] = sse_customer_key_md5
        head_resp = client.head_object(**head_kwargs)
        file_size = int(head_resp.get("Content-Length", 0))
    except Exception:
        file_size = 0

    monitor.set_scan_info(1, file_size)
    monitor.start()

    def _build():
        return _build_download_kwargs(bucket, cos_key, local_path,
                                      thread_num, part_size, rate_limiting, version_id,
                                      sse_customer_algorithm, sse_customer_key, sse_customer_key_md5)

    last_err = _download_with_retry(client, monitor, cos_key, local_path, file_size,
                                    _build, retry, err_retry_num, err_retry_interval,
                                    bucket, disable_crc64, version_id)
    if last_err is not None:
        err_reason = "%s (Code: %s)" % (last_err.get_error_msg(), last_err.get_error_code())
        monitor.update_err(src_path="cos://%s/%s" % (bucket, cos_key),
                           dest_path=local_path,
                           reason=err_reason,
                           request_id=last_err.get_request_id())
    monitor.stop(log_file=log_file)
    if last_err is not None:
        raise last_err


def _download_directory(client, bucket, prefix, local_dir, include, exclude,
                        thread_num, routines, part_size, rate_limiting, version_id, log_file="", retry=3,
                        err_retry_num=0, err_retry_interval=0,
                        only_current_dir=False, disable_crc64=False, forbid_overwrite=False,
                        sse_customer_algorithm="", sse_customer_key="", sse_customer_key_md5=""):
    """递归下载 COS 前缀下的所有对象
    - thread_num: 单文件分块并发（传给 SDK MAXThread）
    - routines: 文件间并发（同时下载的文件数）
    """
    monitor = TransferProgressMonitor("download")
    monitor.start()

    # 先收集所有待下载的文件任务
    tasks = []
    empty_local_dirs = []  # COS 上 / 结尾的空目录对象，需在本地创建对应目录
    total_size = 0
    skip_count = 0
    marker = ""
    # only_current_dir 时使用 delimiter=/ 只列当前层
    list_delimiter = "/" if only_current_dir else ""

    while True:
        list_kwargs = {
            "Bucket": bucket,
            "Prefix": prefix,
            "Marker": marker,
            "MaxKeys": 1000,
        }
        if list_delimiter:
            list_kwargs["Delimiter"] = list_delimiter
        response = client.list_objects(**list_kwargs)

        if "Contents" in response:
            for content in response["Contents"]:
                key = content["Key"]
                rel_key = key[len(prefix):].lstrip("/") if prefix else key

                # 处理 COS 上的空目录对象（以 / 结尾，Size=0）
                if key.endswith("/") and int(content.get("Size", 0)) == 0:
                    if rel_key:
                        # include/exclude 过滤目录
                        dir_rel = rel_key.rstrip("/")
                        if not match_filters(dir_rel, include, exclude):
                            skip_count += 1
                            continue
                        local_subdir = os.path.join(local_dir, dir_rel.replace("/", os.sep))
                        empty_local_dirs.append(local_subdir)
                    continue

                # include/exclude 过滤
                if not match_filters(rel_key, include, exclude):
                    skip_count += 1
                    continue

                file_size = int(content.get("Size", 0))
                local_file = os.path.join(local_dir, rel_key.replace("/", os.sep))

                # forbid_overwrite：已存在则跳过
                if forbid_overwrite and os.path.exists(local_file):
                    skip_count += 1
                    continue

                total_size += file_size
                tasks.append((key, local_file, file_size))

        if response.get("IsTruncated") == "true":
            marker = response.get("NextMarker", "")
        else:
            break

    # 设置扫描结果（文件数 + 空目录数 + 跳过数）
    monitor.set_scan_info(len(tasks) + len(empty_local_dirs) + skip_count, total_size)
    for _ in range(skip_count):
        monitor.update_skip(0)

    # 预先创建所有需要的本地目录（避免并发时目录创建冲突）
    dir_lock = threading.Lock()
    created_dirs = set()

    def _ensure_dir(file_path):
        """线程安全地创建目录"""
        file_dir = os.path.dirname(file_path)
        if file_dir and file_dir not in created_dirs:
            with dir_lock:
                if file_dir not in created_dirs:
                    if not os.path.exists(file_dir):
                        os.makedirs(file_dir)
                    created_dirs.add(file_dir)

    def _do_download(key, local_file, file_size):
        """单个文件下载任务（含重试）"""
        _ensure_dir(local_file)

        def _build():
            return _build_download_kwargs(bucket, key, local_file,
                                          thread_num, part_size, rate_limiting, version_id,
                                          sse_customer_algorithm, sse_customer_key, sse_customer_key_md5)

        last_err = _download_with_retry(client, monitor, key, local_file, file_size,
                                        _build, retry, err_retry_num, err_retry_interval,
                                        bucket, disable_crc64, version_id)
        if last_err is not None:
            err_reason = "%s (Code: %s)" % (last_err.get_error_msg(), last_err.get_error_code())
            monitor.update_err(src_path="cos://%s/%s" % (bucket, key),
                               dest_path=local_file,
                               reason=err_reason,
                               request_id=last_err.get_request_id())

    # 使用线程池并发下载多个文件，routines 控制文件间并发
    if tasks:
        max_workers = min(routines, len(tasks))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for key, local_file, file_size in tasks:
                futures.append(executor.submit(_do_download, key, local_file, file_size))
            for future in as_completed(futures):
                future.result()

    # 在本地创建 COS 上的空目录
    for local_subdir in empty_local_dirs:
        if local_subdir and not os.path.exists(local_subdir):
            os.makedirs(local_subdir, exist_ok=True)
        monitor.update_ok(0)

    monitor.stop(log_file=log_file)