# -*- coding: utf-8 -*-
"""
symlink 操作：COS 对象软链接管理
对齐 coscli symlink 命令（create/get）
"""
from qcloud_cos import CosServiceError
from .utils import init_cos_client


def create_symlink_object(args, parsed_globals):
    """创建 COS 对象软链接。对齐 coscli symlink create"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    cos_key = args["cos_key"]
    target_key = args["target_key"]
    storage_class = args.get("storage_class", "") or ""

    kwargs = {
        "Bucket": bucket,
        "SymlinkName": cos_key,
        "SymlinkTarget": target_key,
    }
    if storage_class:
        kwargs["StorageClass"] = storage_class

    try:
        client.put_symlink(**kwargs)
        print("软链接创建成功: cos://%s/%s -> %s" % (bucket, cos_key, target_key))
    except AttributeError:
        # SDK 未提供 put_symlink，使用底层 put_object + x-cos-symlink-target 头
        try:
            client.put_object(
                Bucket=bucket,
                Key=cos_key,
                Body=b"",
                Metadata={"x-cos-symlink-target": target_key},
            )
            print("软链接创建成功: cos://%s/%s -> %s" % (bucket, cos_key, target_key))
        except CosServiceError as e:
            print("Error: %s (Code: %s, RequestId: %s)" % (
                e.get_error_msg(), e.get_error_code(), e.get_request_id()))
    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))

def get_symlink_object(args, parsed_globals):
    """获取 COS 对象软链接的目标。对齐 coscli symlink get"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    cos_key = args["cos_key"]

    try:
        # SDK 提供 get_symlink 时优先使用
        if hasattr(client, "get_symlink"):
            response = client.get_symlink(Bucket=bucket, SymlinkName=cos_key)
            target = response.get("x-cos-symlink-target") or response.get("SymlinkTarget", "")
        else:
            # 回退到 head_object 读取头部
            response = client.head_object(Bucket=bucket, Key=cos_key)
            target = response.get("x-cos-symlink-target", "")

        if not target:
            print("cos://%s/%s 不是软链接对象，或未设置 x-cos-symlink-target 头" % (bucket, cos_key))
            return
        print("cos://%s/%s -> %s" % (bucket, cos_key, target))

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))
