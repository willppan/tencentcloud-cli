# -*- coding: utf-8 -*-
"""
tagging 操作：对象标签管理
对齐 coscli 的标签管理能力
"""
from qcloud_cos import CosServiceError
from .utils import init_cos_client


def get_object_tagging(args, parsed_globals):
    """获取对象的标签"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    cos_key = args["cos_key"]

    try:
        response = client.get_object_tagging(
            Bucket=bucket,
            Key=cos_key,
        )

        tag_set = (response.get("TagSet") or {}).get("Tag", [])
        if not isinstance(tag_set, list):
            tag_set = [tag_set]

        print("对象标签: cos://%s/%s" % (bucket, cos_key))
        print("-" * 50)

        if not tag_set or (len(tag_set) == 1 and not tag_set[0]):
            print("(无标签)")
        else:
            for tag in tag_set:
                if tag:
                    print("  %s = %s" % (tag.get("Key", ""), tag.get("Value", "")))

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def put_object_tagging(args, parsed_globals):
    """设置对象的标签"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    cos_key = args["cos_key"]
    tags_str = args.get("tags", "") or ""

    # 解析标签字符串，格式: key1=value1,key2=value2
    tag_list = []
    if tags_str:
        for pair in tags_str.split(","):
            pair = pair.strip()
            if "=" in pair:
                k, v = pair.split("=", 1)
                tag_list.append({"Key": k.strip(), "Value": v.strip()})
            else:
                print("Error: 标签格式错误，应为 key=value 格式: %s" % pair)
                return

    if not tag_list:
        print("Error: 请指定至少一个标签，格式: key1=value1,key2=value2")
        return

    try:
        tagging = {
            "TagSet": {
                "Tag": tag_list,
            }
        }
        client.put_object_tagging(
            Bucket=bucket,
            Key=cos_key,
            Tagging=tagging,
        )
        print("对象标签设置成功: cos://%s/%s" % (bucket, cos_key))
        for tag in tag_list:
            print("  %s = %s" % (tag["Key"], tag["Value"]))

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def delete_object_tagging(args, parsed_globals):
    """删除对象的所有标签"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    cos_key = args["cos_key"]

    try:
        client.delete_object_tagging(
            Bucket=bucket,
            Key=cos_key,
        )
        print("对象标签删除成功: cos://%s/%s" % (bucket, cos_key))

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def add_object_tagging(args, parsed_globals):
    """追加对象标签（合并已有标签，同 key 则覆盖）。对齐 coscli object-tagging add"""
    client, region = init_cos_client(parsed_globals)

    bucket = args["bucket"]
    cos_key = args["cos_key"]
    tags_str = args.get("tags", "") or ""

    # 解析新增标签
    new_pairs = {}
    if tags_str:
        for pair in tags_str.split(","):
            pair = pair.strip()
            if "=" in pair:
                k, v = pair.split("=", 1)
                new_pairs[k.strip()] = v.strip()
            else:
                print("Error: 标签格式错误，应为 key=value 格式: %s" % pair)
                return

    if not new_pairs:
        print("Error: 请指定至少一个标签，格式: key1=value1,key2=value2")
        return

    try:
        # 先读取已有标签
        existing = {}
        try:
            response = client.get_object_tagging(Bucket=bucket, Key=cos_key)
            tag_set = (response.get("TagSet") or {}).get("Tag", [])
            if not isinstance(tag_set, list):
                tag_set = [tag_set]
            for tag in tag_set:
                if tag and tag.get("Key"):
                    existing[tag["Key"]] = tag.get("Value", "")
        except CosServiceError as e:
            if e.get_error_code() not in ("NoSuchTagSet", "NoSuchTagSetError"):
                raise

        # 合并（新标签覆盖同 key 的旧值）
        existing.update(new_pairs)

        tagging = {
            "TagSet": {
                "Tag": [{"Key": k, "Value": v} for k, v in existing.items()]
            }
        }
        client.put_object_tagging(
            Bucket=bucket,
            Key=cos_key,
            Tagging=tagging,
        )
        print("对象标签追加成功: cos://%s/%s" % (bucket, cos_key))
        for k, v in existing.items():
            marker = " (新)" if k in new_pairs else ""
            print("  %s = %s%s" % (k, v, marker))

    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))