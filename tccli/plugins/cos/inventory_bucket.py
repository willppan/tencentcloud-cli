# -*- coding: utf-8 -*-
"""
inventory 操作：存储桶清单（Inventory）管理
对齐 coscli inventory 命令（put / get / list / delete / post）
"""
from qcloud_cos import CosServiceError
from .utils import init_cos_client


def _build_inventory_config(args):
    """根据命令行参数构造 InventoryConfiguration dict。"""
    inventory_id = args["id"]
    is_enabled = args.get("is_enabled", True)
    frequency = args.get("frequency", "Daily") or "Daily"
    included_object_versions = args.get("included_object_versions", "Current") or "Current"
    fields = args.get("fields", "") or ""
    prefix = args.get("prefix", "") or ""

    dest_bucket = args.get("dest_bucket", "") or ""
    dest_account_id = args.get("dest_account_id", "") or ""
    dest_prefix = args.get("dest_prefix", "") or ""
    dest_format = args.get("dest_format", "CSV") or "CSV"

    config = {
        "Id": inventory_id,
        "IsEnabled": "true" if is_enabled else "false",
        "IncludedObjectVersions": included_object_versions,
        "Schedule": {"Frequency": frequency},
    }
    if prefix:
        config["Filter"] = {"Prefix": prefix}
    if fields:
        optional = [f.strip() for f in fields.split(",") if f.strip()]
        if optional:
            config["OptionalFields"] = {"Field": optional}
    dest = {}
    if dest_bucket:
        dest["Bucket"] = dest_bucket
    if dest_account_id:
        dest["AccountId"] = dest_account_id
    if dest_prefix:
        dest["Prefix"] = dest_prefix
    if dest:
        dest["Format"] = dest_format
        config["Destination"] = {"COSBucketDestination": dest}
    return config


def put_bucket_inventory(args, parsed_globals):
    """创建/更新存储桶清单。对齐 coscli inventory put"""
    client, region = init_cos_client(parsed_globals)
    bucket = args["bucket"]
    inventory_id = args["id"]

    config = _build_inventory_config(args)

    try:
        client.put_bucket_inventory(
            Bucket=bucket,
            Id=inventory_id,
            InventoryConfiguration=config,
        )
        print("存储桶清单任务创建/更新成功: %s (Id=%s)" % (bucket, inventory_id))
    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def get_bucket_inventory(args, parsed_globals):
    """获取存储桶清单配置。对齐 coscli inventory get"""
    client, region = init_cos_client(parsed_globals)
    bucket = args["bucket"]
    inventory_id = args["id"]

    try:
        response = client.get_bucket_inventory(Bucket=bucket, Id=inventory_id)
        print("存储桶清单配置: %s (Id=%s)" % (bucket, inventory_id))
        print("-" * 60)
        _print_inventory(response)
    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def list_bucket_inventory(args, parsed_globals):
    """列出存储桶所有清单任务。对齐 coscli inventory list"""
    client, region = init_cos_client(parsed_globals)
    bucket = args["bucket"]

    try:
        # SDK 支持 continuation_token 分页
        continuation_token = ""
        total = 0
        while True:
            list_kwargs = {"Bucket": bucket}
            if continuation_token:
                list_kwargs["ContinuationToken"] = continuation_token
            response = client.list_bucket_inventory_configurations(**list_kwargs)

            configs = response.get("InventoryConfiguration", [])
            if not isinstance(configs, list):
                configs = [configs]
            for cfg in configs:
                total += 1
                print("-" * 60)
                _print_inventory(cfg)

            if response.get("IsTruncated") == "true":
                continuation_token = response.get("NextContinuationToken", "")
                if not continuation_token:
                    break
            else:
                break

        print("\n共 %d 个清单任务" % total)
    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def delete_bucket_inventory(args, parsed_globals):
    """删除存储桶清单任务。对齐 coscli inventory delete"""
    client, region = init_cos_client(parsed_globals)
    bucket = args["bucket"]
    inventory_id = args["id"]

    try:
        client.delete_bucket_inventory(Bucket=bucket, Id=inventory_id)
        print("存储桶清单任务删除成功: %s (Id=%s)" % (bucket, inventory_id))
    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def post_bucket_inventory(args, parsed_globals):
    """一次性清单任务。对齐 coscli inventory post。

    注：COS 的一次性清单实际通过 POST 操作触发（某些 SDK 不直接暴露，
    此处回退为创建一个频率为 Once 的常规清单。
    """
    client, region = init_cos_client(parsed_globals)
    bucket = args["bucket"]
    inventory_id = args["id"]

    # 一次性清单：Frequency 固定为 Once
    args = dict(args)
    args["frequency"] = "Once"
    config = _build_inventory_config(args)

    # 优先使用 SDK 的 post_bucket_inventory；否则回退 put_bucket_inventory
    try:
        if hasattr(client, "post_bucket_inventory"):
            client.post_bucket_inventory(
                Bucket=bucket,
                Id=inventory_id,
                InventoryConfiguration=config,
            )
        else:
            client.put_bucket_inventory(
                Bucket=bucket,
                Id=inventory_id,
                InventoryConfiguration=config,
            )
        print("一次性清单任务已提交: %s (Id=%s)" % (bucket, inventory_id))
    except CosServiceError as e:
        print("Error: %s (Code: %s, RequestId: %s)" % (
            e.get_error_msg(), e.get_error_code(), e.get_request_id()))


def _print_inventory(cfg):
    """打印单个清单配置"""
    print("  Id                      : %s" % cfg.get("Id", ""))
    print("  IsEnabled               : %s" % cfg.get("IsEnabled", ""))
    print("  IncludedObjectVersions  : %s" % cfg.get("IncludedObjectVersions", ""))
    schedule = cfg.get("Schedule", {}) or {}
    print("  Frequency               : %s" % schedule.get("Frequency", ""))
    fil = cfg.get("Filter", {}) or {}
    if fil.get("Prefix"):
        print("  Prefix                  : %s" % fil["Prefix"])
    opt = cfg.get("OptionalFields", {}) or {}
    if opt.get("Field"):
        fields = opt["Field"]
        if not isinstance(fields, list):
            fields = [fields]
        print("  OptionalFields          : %s" % ", ".join(fields))
    dest = (cfg.get("Destination") or {}).get("COSBucketDestination", {}) or {}
    if dest:
        print("  Destination.Bucket      : %s" % dest.get("Bucket", ""))
        if dest.get("AccountId"):
            print("  Destination.AccountId   : %s" % dest["AccountId"])
        if dest.get("Prefix"):
            print("  Destination.Prefix      : %s" % dest["Prefix"])
        print("  Destination.Format      : %s" % dest.get("Format", ""))
