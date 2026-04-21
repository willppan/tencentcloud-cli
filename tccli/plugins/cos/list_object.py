# -*- coding: utf-8 -*-
"""
list 操作：列出 COS 存储桶中的文件
对齐 coscli ls 命令
"""
from qcloud_cos import CosServiceError
from .utils import init_cos_client, format_size, match_filters


def list_object(args, parsed_globals):
    """列出 COS 存储桶中的文件"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    prefix = args.get("prefix", "") or ""
    marker = args.get("marker", "") or ""
    max_keys = args.get("max_keys", 1000) or 1000
    delimiter = args.get("delimiter", "") or ""
    recursive = args.get("recursive", False)
    include = args.get("include", "") or ""
    exclude = args.get("exclude", "") or ""
    # 对齐 coscli ls：
    all_versions = args.get("all_versions", False)
    limit = int(args.get("limit", 0) or 0)

    # 递归模式下不使用 delimiter，以列出所有层级的对象
    # 非递归模式下若未指定 delimiter，默认使用 / 只列出当前层级
    if recursive:
        delimiter = ""
    elif not delimiter:
        delimiter = "/"

    try:
        if all_versions:
            _list_versions(client, bucket, prefix, delimiter, include, exclude, limit)
            return

        total_count = 0
        total_size = 0
        reached_limit = False

        while not reached_limit:
            response = client.list_objects(
                Bucket=bucket,
                Prefix=prefix,
                Marker=marker,
                MaxKeys=max_keys,
                Delimiter=delimiter,
            )

            # 输出公共前缀（目录）
            if "CommonPrefixes" in response:
                for common_prefix in response["CommonPrefixes"]:
                    print("DIR  %s" % common_prefix["Prefix"])
                    total_count += 1
                    if limit and total_count >= limit:
                        reached_limit = True
                        break

            # 输出文件列表
            if not reached_limit and "Contents" in response:
                for content in response["Contents"]:
                    key = content["Key"]

                    # include/exclude 过滤
                    if not match_filters(key, include, exclude):
                        continue

                    size = int(content.get("Size", 0))
                    last_modified = content.get("LastModified", "")
                    storage_class = content.get("StorageClass", "STANDARD")
                    total_count += 1
                    total_size += size
                    print("%-12s  %-20s  %-25s  %s" % (
                        format_size(size), storage_class, last_modified, key))
                    if limit and total_count >= limit:
                        reached_limit = True
                        break

            # 分页处理
            if reached_limit:
                break
            if response.get("IsTruncated") == "true":
                marker = response.get("NextMarker", "")
                if not recursive:
                    print("\n结果已截断，下一页 Marker: %s" % marker)
                    break
            else:
                break

        # 输出统计信息
        if recursive or total_count > 0:
            print("\n共 %d 个对象, 总大小: %s" % (total_count, format_size(total_size)))

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def _list_versions(client, bucket, prefix, delimiter, include, exclude, limit):
    """列出对象所有历史版本，对齐 coscli ls --all-versions"""
    key_marker = ""
    version_id_marker = ""
    total = 0
    total_size = 0

    print("%-12s  %-20s  %-25s  %-10s  %-40s  %s" % (
        "Size", "StorageClass", "LastModified", "IsLatest", "VersionId", "Key"))
    print("-" * 140)

    try:
        while True:
            list_kwargs = {
                "Bucket": bucket,
                "Prefix": prefix,
                "MaxKeys": 1000,
            }
            if delimiter:
                list_kwargs["Delimiter"] = delimiter
            if key_marker:
                list_kwargs["KeyMarker"] = key_marker
            if version_id_marker:
                list_kwargs["VersionIdMarker"] = version_id_marker
            response = client.list_objects_versions(**list_kwargs)

            for item_key in ("Version", "DeleteMarker"):
                if item_key not in response:
                    continue
                items = response[item_key]
                if not isinstance(items, list):
                    items = [items]
                for item in items:
                    key = item.get("Key", "")
                    if not match_filters(key, include, exclude):
                        continue
                    size = int(item.get("Size", 0))
                    last_modified = item.get("LastModified", "")
                    storage_class = item.get("StorageClass", "" if item_key == "DeleteMarker" else "STANDARD")
                    is_latest = item.get("IsLatest", "false")
                    version_id = item.get("VersionId", "")
                    marker_str = "[DEL]" if item_key == "DeleteMarker" else format_size(size)
                    print("%-12s  %-20s  %-25s  %-10s  %-40s  %s" % (
                        marker_str, storage_class, last_modified, is_latest, version_id, key))
                    total += 1
                    total_size += size
                    if limit and total >= limit:
                        print("\n共 %d 个版本, 总大小: %s" % (total, format_size(total_size)))
                        return

            if response.get("IsTruncated") == "true":
                key_marker = response.get("NextKeyMarker", "")
                version_id_marker = response.get("NextVersionIdMarker", "")
            else:
                break
    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))
        return

    print("\n共 %d 个版本, 总大小: %s" % (total, format_size(total_size)))