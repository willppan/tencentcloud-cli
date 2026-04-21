# -*- coding: utf-8 -*-
"""
COS 命令行工具插件
将 COS 的所有命令集成到 tencentcloud-cli 中
"""
from .list_object import list_object
from .upload_object import upload_object
from .download_object import download_object
from .delete_object import delete_object
from .copy_object import copy_object
from .move_object import move_object
from .list_buckets import list_buckets
from .create_bucket import create_bucket
from .delete_bucket import delete_bucket
from .head_object import head_object
from .restore_object import restore_object
from .sync_upload_object import sync_upload_object
from .sync_download_object import sync_download_object
from .sync_copy_object import sync_copy_object
from .signurl_object import signurl_object
from .acl_object import get_bucket_acl, put_bucket_acl, get_object_acl, put_object_acl
from .abort_multipart import abort_multipart
from .hash_object import hash_object
from .tagging_object import (get_object_tagging, put_object_tagging,
                             add_object_tagging, delete_object_tagging)
from .du_object import du_object
from .cat_object import cat_object
from .lsparts_object import lsparts_object
from .symlink_object import create_symlink_object, get_symlink_object
from .inventory_bucket import (put_bucket_inventory, get_bucket_inventory,
                               list_bucket_inventory, delete_bucket_inventory,
                               post_bucket_inventory)

service_name = "cos"
service_version = "2021-02-24"

_spec = {
    "metadata": {
        "serviceShortName": service_name,
        "apiVersion": service_version,
        "description": "COS (Cloud Object Storage) command line tool",
    },
    "actions": {
        # ===== 文件操作 =====
        "list": {
            "name": "列出文件",
            "document": "列出 COS 存储桶中的文件，支持按前缀过滤和分页",
            "input": "listRequest",
            "output": "listResponse",
            "action_caller": list_object,
        },
        "upload": {
            "name": "上传文件",
            "document": "上传本地文件到 COS，自动根据文件大小选择简单上传或分片上传",
            "input": "uploadRequest",
            "output": "uploadResponse",
            "action_caller": upload_object,
        },
        "download": {
            "name": "下载文件",
            "document": "从 COS 下载文件到本地，自动根据文件大小选择简单下载或分片下载",
            "input": "downloadRequest",
            "output": "downloadResponse",
            "action_caller": download_object,
        },
        "delete": {
            "name": "删除文件",
            "document": "删除 COS 存储桶中的指定文件，支持递归批量删除",
            "input": "deleteRequest",
            "output": "deleteResponse",
            "action_caller": delete_object,
        },
        "copy": {
            "name": "复制文件",
            "document": "复制 COS 上的文件到另一个位置，支持跨存储桶和跨地域复制",
            "input": "copyRequest",
            "output": "copyResponse",
            "action_caller": copy_object,
        },
        "move": {
            "name": "移动/重命名文件",
            "document": "移动或重命名 COS 上的文件（通过复制+删除实现），支持跨存储桶移动",
            "input": "moveRequest",
            "output": "moveResponse",
            "action_caller": move_object,
        },
        # ===== 存储桶操作 =====
        "list_buckets": {
            "name": "列出存储桶",
            "document": "列出当前账号下的所有存储桶",
            "input": "list_bucketsRequest",
            "output": "list_bucketsResponse",
            "action_caller": list_buckets,
        },
        "create_bucket": {
            "name": "创建存储桶",
            "document": "创建一个新的 COS 存储桶",
            "input": "create_bucketRequest",
            "output": "create_bucketResponse",
            "action_caller": create_bucket,
        },
        "delete_bucket": {
            "name": "删除存储桶",
            "document": "删除指定的 COS 存储桶，使用 --force 可强制清空后删除",
            "input": "delete_bucketRequest",
            "output": "delete_bucketResponse",
            "action_caller": delete_bucket,
        },
        # ===== 对象元信息操作 =====
        "head": {
            "name": "查询对象元信息",
            "document": "查询 COS 对象的元数据信息，包括大小、类型、修改时间、CRC64 等",
            "input": "headRequest",
            "output": "headResponse",
            "action_caller": head_object,
        },
        "restore": {
            "name": "恢复归档文件",
            "document": "恢复归档存储类型（ARCHIVE/DEEP_ARCHIVE）的 COS 对象，使其可被下载",
            "input": "restoreRequest",
            "output": "restoreResponse",
            "action_caller": restore_object,
        },
        # ===== 同步操作（拆分为三个独立接口） =====
        "sync_upload": {
            "name": "同步上传",
            "document": "同步本地目录到 COS，增量上传（默认 CRC64 校验，支持 --ignore_existing/--update/--snapshot_path），支持删除目标端多余文件。对齐 coscli sync",
            "input": "sync_uploadRequest",
            "output": "sync_uploadResponse",
            "action_caller": sync_upload_object,
        },
        "sync_download": {
            "name": "同步下载",
            "document": "同步 COS 到本地目录，增量下载（默认 CRC64 校验，支持 --ignore_existing/--update/--snapshot_path），支持删除本地多余文件。对齐 coscli sync",
            "input": "sync_downloadRequest",
            "output": "sync_downloadResponse",
            "action_caller": sync_download_object,
        },
        "sync_copy": {
            "name": "同步复制",
            "document": "同步 COS 到另一个 COS 位置，增量复制（默认 CRC64 校验，支持 --ignore_existing/--update），支持删除目标端多余文件。对齐 coscli sync",
            "input": "sync_copyRequest",
            "output": "sync_copyResponse",
            "action_caller": sync_copy_object,
        },
        # ===== 预签名 URL =====
        "signurl": {
            "name": "生成预签名URL",
            "document": "生成 COS 对象的预签名 URL，可用于临时授权访问",
            "input": "signurlRequest",
            "output": "signurlResponse",
            "action_caller": signurl_object,
        },
        # ===== ACL 操作 =====
        "get_bucket_acl": {
            "name": "获取存储桶ACL",
            "document": "获取存储桶的访问控制列表（ACL）",
            "input": "get_bucket_aclRequest",
            "output": "get_bucket_aclResponse",
            "action_caller": get_bucket_acl,
        },
        "put_bucket_acl": {
            "name": "设置存储桶ACL",
            "document": "设置存储桶的访问控制策略",
            "input": "put_bucket_aclRequest",
            "output": "put_bucket_aclResponse",
            "action_caller": put_bucket_acl,
        },
        "get_object_acl": {
            "name": "获取对象ACL",
            "document": "获取 COS 对象的访问控制列表（ACL）",
            "input": "get_object_aclRequest",
            "output": "get_object_aclResponse",
            "action_caller": get_object_acl,
        },
        "put_object_acl": {
            "name": "设置对象ACL",
            "document": "设置 COS 对象的访问控制策略",
            "input": "put_object_aclRequest",
            "output": "put_object_aclResponse",
            "action_caller": put_object_acl,
        },
        # ===== 分片上传管理 =====
        "abort": {
            "name": "清理分片上传",
            "document": "清理存储桶中未完成的分片上传任务",
            "input": "abortRequest",
            "output": "abortResponse",
            "action_caller": abort_multipart,
        },
        # ===== 哈希计算 =====
        "hash": {
            "name": "计算哈希值",
            "document": "计算本地文件的哈希值（md5/sha1/sha256/crc64），或获取 COS 对象的 ETag/CRC64 信息",
            "input": "hashRequest",
            "output": "hashResponse",
            "action_caller": hash_object,
        },
        # ===== 标签管理 =====
        "get_object_tagging": {
            "name": "获取对象标签",
            "document": "获取 COS 对象的标签信息",
            "input": "get_object_taggingRequest",
            "output": "get_object_taggingResponse",
            "action_caller": get_object_tagging,
        },
        "put_object_tagging": {
            "name": "设置对象标签",
            "document": "设置 COS 对象的标签，格式为 key1=value1,key2=value2",
            "input": "put_object_taggingRequest",
            "output": "put_object_taggingResponse",
            "action_caller": put_object_tagging,
        },
        "delete_object_tagging": {
            "name": "删除对象标签",
            "document": "删除 COS 对象的所有标签",
            "input": "delete_object_taggingRequest",
            "output": "delete_object_taggingResponse",
            "action_caller": delete_object_tagging,
        },
        # ===== 统计操作 =====
        "du": {
            "name": "统计大小",
            "document": "统计存储桶或指定前缀下的对象总大小和数量，按存储类型分类统计",
            "input": "duRequest",
            "output": "duResponse",
            "action_caller": du_object,
        },
        # ===== 查看文件内容 =====
        "cat": {
            "name": "查看文件内容",
            "document": "查看 COS 对象的文本内容，默认最大读取 10MB，支持指定范围读取",
            "input": "catRequest",
            "output": "catResponse",
            "action_caller": cat_object,
        },
        # ===== 列出分片上传 =====
        "lsparts": {
            "name": "列出分片上传",
            "document": "列出存储桶中未完成的分片上传任务",
            "input": "lspartsRequest",
            "output": "lspartsResponse",
            "action_caller": lsparts_object,
        },
        # ===== 对象软链接 =====
        "create_symlink": {
            "name": "创建对象软链接",
            "document": "创建 COS 对象软链接（symlink），对齐 coscli symlink create",
            "input": "create_symlinkRequest",
            "output": "create_symlinkResponse",
            "action_caller": create_symlink_object,
        },
        "get_symlink": {
            "name": "查询对象软链接",
            "document": "获取 COS 对象软链接的目标，对齐 coscli symlink get",
            "input": "get_symlinkRequest",
            "output": "get_symlinkResponse",
            "action_caller": get_symlink_object,
        },
        # ===== 标签追加 =====
        "add_object_tagging": {
            "name": "追加对象标签",
            "document": "追加 COS 对象标签（合并已有标签，同 key 覆盖），对齐 coscli object-tagging add",
            "input": "add_object_taggingRequest",
            "output": "add_object_taggingResponse",
            "action_caller": add_object_tagging,
        },
        # ===== 存储桶清单 =====
        "put_bucket_inventory": {
            "name": "创建/更新存储桶清单",
            "document": "创建或更新存储桶清单任务，对齐 coscli inventory put",
            "input": "put_bucket_inventoryRequest",
            "output": "put_bucket_inventoryResponse",
            "action_caller": put_bucket_inventory,
        },
        "get_bucket_inventory": {
            "name": "查询存储桶清单",
            "document": "查询存储桶单个清单任务配置，对齐 coscli inventory get",
            "input": "get_bucket_inventoryRequest",
            "output": "get_bucket_inventoryResponse",
            "action_caller": get_bucket_inventory,
        },
        "list_bucket_inventory": {
            "name": "列出存储桶清单任务",
            "document": "列出存储桶的所有清单任务，对齐 coscli inventory list",
            "input": "list_bucket_inventoryRequest",
            "output": "list_bucket_inventoryResponse",
            "action_caller": list_bucket_inventory,
        },
        "delete_bucket_inventory": {
            "name": "删除存储桶清单",
            "document": "删除存储桶的清单任务，对齐 coscli inventory delete",
            "input": "delete_bucket_inventoryRequest",
            "output": "delete_bucket_inventoryResponse",
            "action_caller": delete_bucket_inventory,
        },
        "post_bucket_inventory": {
            "name": "一次性存储桶清单",
            "document": "一次性触发存储桶清单任务，对齐 coscli inventory post",
            "input": "post_bucket_inventoryRequest",
            "output": "post_bucket_inventoryResponse",
            "action_caller": post_bucket_inventory,
        },
    },
    "objects": {
        # ===== list 接口参数 =====
        "listRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "prefix", "member": "string", "type": "string", "required": False,
                 "document": "对象键前缀，用于过滤列出的对象"},
                {"name": "marker", "member": "string", "type": "string", "required": False,
                 "document": "分页标记，从该标记之后开始列出对象"},
                {"name": "max_keys", "member": "int64", "type": "int64", "required": False,
                 "document": "最大返回数量，默认1000，最大为 1000 （单次请求）"},
                {"name": "delimiter", "member": "string", "type": "string", "required": False,
                 "document": "分隔符，通常设为 / 以模拟目录结构"},
                {"name": "recursive", "member": "bool", "type": "bool", "required": False,
                 "document": "是否递归列出所有对象（忽略 delimiter），默认 false"},
                {"name": "include", "member": "string", "type": "string", "required": False,
                 "document": "包含匹配模式，支持通配符，如 *.txt"},
                {"name": "exclude", "member": "string", "type": "string", "required": False,
                 "document": "排除匹配模式，支持通配符，如 *.log"},
                {"name": "all_versions", "member": "bool", "type": "bool", "required": False,
                 "document": "列出对象的所有历史版本，默认 false。对齐 coscli ls --all-versions"},
                {"name": "limit", "member": "int64", "type": "int64", "required": False,
                 "document": "列出最多的对象数量上限，默认 0 (不限)。对齐 coscli ls --limit"},
            ],
        },
        "listResponse": {
            "members": [],
        },
        # ===== upload 接口参数 =====
        "uploadRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "目标存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "local_path", "member": "string", "type": "string", "required": True,
                 "document": "本地文件或目录路径"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "COS 上的目标对象键（Key），递归上传时作为前缀"},
                {"name": "storage_class", "member": "string", "type": "string", "required": False,
                 "document": "存储类型: STANDARD(默认), STANDARD_IA, ARCHIVE, DEEP_ARCHIVE, INTELLIGENT_TIERING, MAZ_STANDARD, MAZ_STANDARD_IA"},
                {"name": "content_type", "member": "string", "type": "string", "required": False,
                 "document": "文件内容类型（MIME），如 text/plain, image/jpeg"},
                {"name": "meta", "member": "string", "type": "string", "required": False,
                 "document": "自定义元数据，格式: key1=value1#key2=value2"},
                {"name": "recursive", "member": "bool", "type": "bool", "required": False,
                 "document": "是否递归上传目录，默认 false"},
                {"name": "include", "member": "string", "type": "string", "required": False,
                 "document": "包含匹配模式（递归上传时生效），支持通配符"},
                {"name": "exclude", "member": "string", "type": "string", "required": False,
                 "document": "排除匹配模式（递归上传时生效），支持通配符"},
                {"name": "only_current_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "仅上传当前目录下的文件，不递归子目录，默认 false。对齐 coscli --only-current-dir"},
                {"name": "skip_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "不上传空目录标记（/ 结尾的空对象），默认 false。对齐 coscli --skip-dir"},
                {"name": "disable_all_symlink", "member": "bool", "type": "bool", "required": False,
                 "document": "不上传任何符号链接（文件和目录），默认 false。对齐 coscli --disable-all-symlink"},
                {"name": "enable_symlink_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "允许跟随符号链接目录，默认 false（不跟随）。对齐 coscli --enable-symlink-dir"},
                {"name": "thread_num", "member": "int64", "type": "int64", "required": False,
                 "document": "单文件分片上传并发线程数，默认 5"},
                {"name": "routines", "member": "int64", "type": "int64", "required": False,
                 "document": "文件间并发数（同时传输的文件数），默认 3"},
                {"name": "part_size", "member": "int64", "type": "int64", "required": False,
                 "document": "分片大小（MB），默认 20"},
                {"name": "rate_limiting", "member": "int64", "type": "int64", "required": False,
                 "document": "单链接限速（MB/s），0 表示不限速"},
                {"name": "retry", "member": "int64", "type": "int64", "required": False,
                 "document": "失败重试次数，默认 3，设为 0 表示不重试"},
                {"name": "err_retry_num", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误（超时/5xx等）的额外重试次数，默认 0。对齐 coscli --err-retry-num"},
                {"name": "err_retry_interval", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的重试间隔（秒），默认 0（立即重试）。对齐 coscli --err-retry-interval"},
                {"name": "disable_crc64", "member": "bool", "type": "bool", "required": False,
                 "document": "关闭上传后 CRC64 校验，默认 false。对齐 coscli --disable-crc64"},
                {"name": "acl", "member": "string", "type": "string", "required": False,
                 "document": "对象 ACL，可选 default/private/public-read/public-read-write/authenticated-read/bucket-owner-read/bucket-owner-full-control"},
                {"name": "grant_read", "member": "string", "type": "string", "required": False,
                 "document": "授予读权限，格式: id=\"账号ID\""},
                {"name": "grant_read_acp", "member": "string", "type": "string", "required": False,
                 "document": "授予读 ACP 权限，格式: id=\"账号ID\""},
                {"name": "grant_write_acp", "member": "string", "type": "string", "required": False,
                 "document": "授予写 ACP 权限，格式: id=\"账号ID\""},
                {"name": "grant_full_control", "member": "string", "type": "string", "required": False,
                 "document": "授予完全控制权限，格式: id=\"账号ID\""},
                {"name": "tags", "member": "string", "type": "string", "required": False,
                 "document": "对象标签，格式: key1=value1&key2=value2"},
                {"name": "forbid_overwrite", "member": "bool", "type": "bool", "required": False,
                 "document": "禁止覆盖同名对象，默认 false。对齐 coscli --forbid-overwrite"},
                {"name": "encryption_type", "member": "string", "type": "string", "required": False,
                 "document": "服务端加密类型: AES256(SSE-COS) 或 cos/kms(SSE-KMS)"},
                {"name": "sse_customer_algorithm", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密算法，固定为 AES256"},
                {"name": "sse_customer_key", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密密钥（32 字节）"},
                {"name": "sse_customer_key_md5", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密密钥的 MD5"},
                {"name": "log_file", "member": "string", "type": "string", "required": False,
                 "document": "失败日志文件路径，指定后将失败记录写入该文件，默认不输出日志"},
                {"name": "fail_output", "member": "bool", "type": "bool", "required": False,
                 "document": "启用失败日志输出（需配合 --fail_output_path 使用），默认 false。对齐 coscli --fail-output"},
                {"name": "fail_output_path", "member": "string", "type": "string", "required": False,
                 "document": "失败日志输出路径（--fail_output 为 true 时生效）。对齐 coscli --fail-output-path"},
            ],
        },
        "uploadResponse": {
            "members": [],
        },
        # ===== download 接口参数 =====
        "downloadRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "源存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "COS 上的源对象键（Key），递归下载时作为前缀"},
                {"name": "local_path", "member": "string", "type": "string", "required": True,
                 "document": "本地保存路径，递归下载时为目标目录"},
                {"name": "recursive", "member": "bool", "type": "bool", "required": False,
                 "document": "是否递归下载前缀下所有对象，默认 false"},
                {"name": "include", "member": "string", "type": "string", "required": False,
                 "document": "包含匹配模式（递归下载时生效），支持通配符"},
                {"name": "exclude", "member": "string", "type": "string", "required": False,
                 "document": "排除匹配模式（递归下载时生效），支持通配符"},
                {"name": "only_current_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "仅下载当前目录下的对象，不递归，默认 false。对齐 coscli --only-current-dir"},
                {"name": "thread_num", "member": "int64", "type": "int64", "required": False,
                 "document": "单文件分片下载并发线程数，默认 5"},
                {"name": "routines", "member": "int64", "type": "int64", "required": False,
                 "document": "文件间并发数（同时传输的文件数），默认 3"},
                {"name": "part_size", "member": "int64", "type": "int64", "required": False,
                 "document": "分片大小（MB），默认 20"},
                {"name": "rate_limiting", "member": "int64", "type": "int64", "required": False,
                 "document": "单链接限速（MB/s），0 表示不限速"},
                {"name": "version_id", "member": "string", "type": "string", "required": False,
                 "document": "指定下载的对象版本 ID（开启版本控制时使用）"},
                {"name": "retry", "member": "int64", "type": "int64", "required": False,
                 "document": "失败重试次数，默认 3，设为 0 表示不重试"},
                {"name": "err_retry_num", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的额外重试次数，默认 0。对齐 coscli --err-retry-num"},
                {"name": "err_retry_interval", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的重试间隔（秒），默认 0。对齐 coscli --err-retry-interval"},
                {"name": "disable_crc64", "member": "bool", "type": "bool", "required": False,
                 "document": "关闭下载后 CRC64 校验，默认 false。对齐 coscli --disable-crc64"},
                {"name": "forbid_overwrite", "member": "bool", "type": "bool", "required": False,
                 "document": "禁止覆盖本地已存在文件，默认 false"},
                {"name": "sse_customer_algorithm", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密算法，固定为 AES256"},
                {"name": "sse_customer_key", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密密钥"},
                {"name": "sse_customer_key_md5", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密密钥的 MD5"},
                {"name": "log_file", "member": "string", "type": "string", "required": False,
                 "document": "失败日志文件路径，指定后将失败记录写入该文件，默认不输出日志"},
                {"name": "fail_output", "member": "bool", "type": "bool", "required": False,
                 "document": "启用失败日志输出，默认 false。对齐 coscli --fail-output"},
                {"name": "fail_output_path", "member": "string", "type": "string", "required": False,
                 "document": "失败日志输出路径，对齐 coscli --fail-output-path"},
            ],
        },
        "downloadResponse": {
            "members": [],
        },
        # ===== delete 接口参数 =====
        "deleteRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "要删除的对象键（Key），递归删除时作为前缀"},
                {"name": "recursive", "member": "bool", "type": "bool", "required": False,
                 "document": "是否递归删除前缀下所有对象，默认 false"},
                {"name": "force", "member": "bool", "type": "bool", "required": False,
                 "document": "递归删除时跳过确认提示，默认 false"},
                {"name": "include", "member": "string", "type": "string", "required": False,
                 "document": "包含匹配模式（递归删除时生效），支持通配符"},
                {"name": "exclude", "member": "string", "type": "string", "required": False,
                 "document": "排除匹配模式（递归删除时生效），支持通配符"},
                {"name": "version_id", "member": "string", "type": "string", "required": False,
                 "document": "指定删除的对象版本 ID（开启版本控制时使用）"},
            ],
        },
        "deleteResponse": {
            "members": [],
        },
        # ===== copy 接口参数 =====
        "copyRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "源存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "源对象键（Key），递归复制时作为前缀"},
                {"name": "dest_bucket", "member": "string", "type": "string", "required": False,
                 "document": "目标存储桶名称，不填则与源存储桶相同"},
                {"name": "dest_key", "member": "string", "type": "string", "required": True,
                 "document": "目标对象键（Key），递归复制时作为目标前缀"},
                {"name": "dest_region", "member": "string", "type": "string", "required": False,
                 "document": "目标地域，不填则与当前地域相同"},
                {"name": "storage_class", "member": "string", "type": "string", "required": False,
                 "document": "目标存储类型: STANDARD, STANDARD_IA, ARCHIVE, DEEP_ARCHIVE, INTELLIGENT_TIERING, MAZ_STANDARD, MAZ_STANDARD_IA"},
                {"name": "meta", "member": "string", "type": "string", "required": False,
                 "document": "自定义元数据，格式: key1=value1#key2=value2（设置后使用 Replaced 模式）"},
                {"name": "recursive", "member": "bool", "type": "bool", "required": False,
                 "document": "是否递归复制前缀下所有对象，默认 false"},
                {"name": "include", "member": "string", "type": "string", "required": False,
                 "document": "包含匹配模式（递归复制时生效），支持通配符"},
                {"name": "exclude", "member": "string", "type": "string", "required": False,
                 "document": "排除匹配模式（递归复制时生效），支持通配符"},
                {"name": "only_current_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "仅复制当前目录下的对象，不递归，默认 false"},
                {"name": "skip_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "不复制空目录标记，默认 false"},
                {"name": "version_id", "member": "string", "type": "string", "required": False,
                 "document": "指定复制源对象的版本 ID（单文件复制时生效）"},
                {"name": "routines", "member": "int64", "type": "int64", "required": False,
                 "document": "文件间并发数（同时复制的文件数），默认 3"},
                {"name": "retry", "member": "int64", "type": "int64", "required": False,
                 "document": "失败重试次数，默认 3，设为 0 表示不重试"},
                {"name": "err_retry_num", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的额外重试次数，默认 0"},
                {"name": "err_retry_interval", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的重试间隔（秒），默认 0"},
                {"name": "acl", "member": "string", "type": "string", "required": False,
                 "document": "目标对象 ACL"},
                {"name": "grant_read", "member": "string", "type": "string", "required": False,
                 "document": "授予读权限，格式: id=\"账号ID\""},
                {"name": "grant_read_acp", "member": "string", "type": "string", "required": False,
                 "document": "授予读 ACP 权限，格式: id=\"账号ID\""},
                {"name": "grant_write_acp", "member": "string", "type": "string", "required": False,
                 "document": "授予写 ACP 权限，格式: id=\"账号ID\""},
                {"name": "grant_full_control", "member": "string", "type": "string", "required": False,
                 "document": "授予完全控制权限，格式: id=\"账号ID\""},
                {"name": "tags", "member": "string", "type": "string", "required": False,
                 "document": "目标对象标签，格式: key1=value1&key2=value2（设置后使用 Replaced 模式）"},
                {"name": "forbid_overwrite", "member": "bool", "type": "bool", "required": False,
                 "document": "禁止覆盖目标已存在对象，默认 false"},
                {"name": "encryption_type", "member": "string", "type": "string", "required": False,
                 "document": "目标对象服务端加密类型: AES256 或 cos/kms"},
                {"name": "log_file", "member": "string", "type": "string", "required": False,
                 "document": "失败日志文件路径，指定后将失败记录写入该文件，默认不输出日志"},
                {"name": "fail_output", "member": "bool", "type": "bool", "required": False,
                 "document": "启用失败日志输出，默认 false"},
                {"name": "fail_output_path", "member": "string", "type": "string", "required": False,
                 "document": "失败日志输出路径"},
            ],
        },
        "copyResponse": {
            "members": [],
        },
        # ===== move 接口参数 =====
        "moveRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "源存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "源对象键（Key），递归移动时作为前缀"},
                {"name": "dest_bucket", "member": "string", "type": "string", "required": False,
                 "document": "目标存储桶名称，不填则与源存储桶相同"},
                {"name": "dest_key", "member": "string", "type": "string", "required": True,
                 "document": "目标对象键（Key），递归移动时作为目标前缀"},
                {"name": "dest_region", "member": "string", "type": "string", "required": False,
                 "document": "目标地域，不填则与当前地域相同"},
                {"name": "storage_class", "member": "string", "type": "string", "required": False,
                 "document": "目标存储类型: STANDARD, STANDARD_IA, ARCHIVE, DEEP_ARCHIVE, INTELLIGENT_TIERING, MAZ_STANDARD, MAZ_STANDARD_IA"},
                {"name": "recursive", "member": "bool", "type": "bool", "required": False,
                 "document": "是否递归移动前缀下所有对象，默认 false"},
                {"name": "include", "member": "string", "type": "string", "required": False,
                 "document": "包含匹配模式（递归移动时生效），支持通配符"},
                {"name": "exclude", "member": "string", "type": "string", "required": False,
                 "document": "排除匹配模式（递归移动时生效），支持通配符"},
                {"name": "routines", "member": "int64", "type": "int64", "required": False,
                 "document": "文件间并发数（同时移动的文件数），默认 3"},
                {"name": "retry", "member": "int64", "type": "int64", "required": False,
                 "document": "失败重试次数，默认 3，设为 0 表示不重试"},
                {"name": "log_file", "member": "string", "type": "string", "required": False,
                 "document": "失败日志文件路径，指定后将失败记录写入该文件，默认不输出日志"},
            ],
        },
        "moveResponse": {
            "members": [],
        },
        # ===== list_buckets 接口参数 =====
        "list_bucketsRequest": {
            "members": [
                {"name": "filter_region", "member": "string", "type": "string", "required": False,
                 "document": "按地域过滤存储桶，如 ap-guangzhou"},
            ],
        },
        "list_bucketsResponse": {
            "members": [],
        },
        # ===== create_bucket 接口参数 =====
        "create_bucketRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "acl", "member": "string", "type": "string", "required": False,
                 "document": "访问控制策略，可选值: private(默认), public-read, public-read-write"},
            ],
        },
        "create_bucketResponse": {
            "members": [],
        },
        # ===== delete_bucket 接口参数 =====
        "delete_bucketRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "要删除的存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "force", "member": "bool", "type": "bool", "required": False,
                 "document": "强制删除：先清空存储桶中所有对象、版本对象和未完成的分片上传，再删除存储桶，默认 false"},
            ],
        },
        "delete_bucketResponse": {
            "members": [],
        },
        # ===== head 接口参数 =====
        "headRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "要查询的对象键（Key）"},
                {"name": "version_id", "member": "string", "type": "string", "required": False,
                 "document": "指定查询的对象版本 ID（开启版本控制时使用）"},
            ],
        },
        "headResponse": {
            "members": [],
        },
        # ===== restore 接口参数 =====
        "restoreRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "要恢复的归档对象键（Key），递归恢复时作为前缀"},
                {"name": "days", "member": "int64", "type": "int64", "required": False,
                 "document": "恢复后的有效天数，默认 7 天"},
                {"name": "tier", "member": "string", "type": "string", "required": False,
                 "document": "恢复模式: Standard(标准，3-5小时), Expedited(极速，1-5分钟), Bulk(批量，5-12小时)，默认 Standard"},
                {"name": "recursive", "member": "bool", "type": "bool", "required": False,
                 "document": "是否递归恢复前缀下所有归档对象，默认 false"},
                {"name": "include", "member": "string", "type": "string", "required": False,
                 "document": "包含匹配模式（递归恢复时生效），支持通配符"},
                {"name": "exclude", "member": "string", "type": "string", "required": False,
                 "document": "排除匹配模式（递归恢复时生效），支持通配符"},
                {"name": "fail_output", "member": "bool", "type": "bool", "required": False,
                 "document": "启用失败日志输出，默认 false。对齐 coscli --fail-output"},
                {"name": "fail_output_path", "member": "string", "type": "string", "required": False,
                 "document": "失败日志输出路径（--fail_output 为 true 时生效）"},
            ],
        },
        "restoreResponse": {
            "members": [],
        },
        # ===== sync_upload 接口参数 =====
        "sync_uploadRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "目标存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "local_path", "member": "string", "type": "string", "required": True,
                 "document": "本地文件或目录路径"},
                {"name": "cos_key", "member": "string", "type": "string", "required": False,
                 "document": "COS 上的目标对象键（Key），作为前缀"},
                {"name": "recursive", "member": "bool", "type": "bool", "required": False,
                 "document": "是否递归同步目录，默认 false"},
                # 跳过策略
                {"name": "ignore_existing", "member": "bool", "type": "bool", "required": False,
                 "document": "目标已存在即跳过，默认 false。与 --update 互斥，优先级高于 --update"},
                {"name": "update", "member": "bool", "type": "bool", "required": False,
                 "document": "仅在源文件比目标文件新时更新（按 Last-Modified 比较），默认 false。未指定 --ignore-existing 和 --update 时使用 CRC64 校验判断是否跳过"},
                {"name": "snapshot_path", "member": "string", "type": "string", "required": False,
                 "document": "快照数据库文件路径（JSON），用于加速增量判断。对齐 coscli --snapshot-path"},
                # 删除多余
                {"name": "delete_extra", "member": "bool", "type": "bool", "required": False,
                 "document": "是否删除 COS 上多余的文件（本地不存在的），默认 false"},
                {"name": "delete", "member": "bool", "type": "bool", "required": False,
                 "document": "等同 --delete_extra，对齐 coscli --delete"},
                {"name": "backup_dir", "member": "string", "type": "string", "required": False,
                 "document": "删除多余文件前将其下载备份到该本地目录。对齐 coscli --backup-dir"},
                {"name": "force", "member": "bool", "type": "bool", "required": False,
                 "document": "跳过确认提示，默认 false。对齐 coscli --force"},
                # 过滤
                {"name": "include", "member": "string", "type": "string", "required": False,
                 "document": "包含匹配模式，支持通配符，如 *.txt"},
                {"name": "exclude", "member": "string", "type": "string", "required": False,
                 "document": "排除匹配模式，支持通配符，如 *.log"},
                {"name": "only_current_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "仅同步当前目录下的文件，不递归，默认 false"},
                {"name": "skip_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "不创建空目录标记，默认 false"},
                {"name": "ignore_empty_file", "member": "bool", "type": "bool", "required": False,
                 "document": "忽略空文件（0 字节），默认 false。对齐 coscli --ignore-empty-file"},
                {"name": "disable_all_symlink", "member": "bool", "type": "bool", "required": False,
                 "document": "禁用所有符号链接，默认 false"},
                {"name": "enable_symlink_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "允许跟随符号链接目录，默认 false"},
                # 对象属性
                {"name": "storage_class", "member": "string", "type": "string", "required": False,
                 "document": "上传时的存储类型: STANDARD, STANDARD_IA, ARCHIVE, DEEP_ARCHIVE, INTELLIGENT_TIERING, MAZ_STANDARD, MAZ_STANDARD_IA"},
                {"name": "content_type", "member": "string", "type": "string", "required": False,
                 "document": "文件内容类型（MIME），如 text/plain, image/jpeg"},
                {"name": "meta", "member": "string", "type": "string", "required": False,
                 "document": "自定义元数据，格式: key1=value1#key2=value2"},
                {"name": "acl", "member": "string", "type": "string", "required": False,
                 "document": "对象 ACL，对齐 coscli --acl"},
                {"name": "grant_read", "member": "string", "type": "string", "required": False,
                 "document": "授予读权限，格式: id=\"账号ID\""},
                {"name": "grant_read_acp", "member": "string", "type": "string", "required": False,
                 "document": "授予读 ACP 权限"},
                {"name": "grant_write_acp", "member": "string", "type": "string", "required": False,
                 "document": "授予写 ACP 权限"},
                {"name": "grant_full_control", "member": "string", "type": "string", "required": False,
                 "document": "授予完全控制权限"},
                {"name": "tags", "member": "string", "type": "string", "required": False,
                 "document": "对象标签，格式: key1=value1&key2=value2"},
                {"name": "forbid_overwrite", "member": "bool", "type": "bool", "required": False,
                 "document": "禁止覆盖同名对象，默认 false"},
                {"name": "encryption_type", "member": "string", "type": "string", "required": False,
                 "document": "服务端加密类型: AES256 或 cos/kms"},
                {"name": "sse_customer_algorithm", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密算法，固定 AES256"},
                {"name": "sse_customer_key", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密密钥"},
                {"name": "sse_customer_key_md5", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密密钥 MD5"},
                # 性能
                {"name": "thread_num", "member": "int64", "type": "int64", "required": False,
                 "document": "单文件分片上传并发线程数，默认 5"},
                {"name": "routines", "member": "int64", "type": "int64", "required": False,
                 "document": "文件间并发数（同时传输的文件数），默认 3"},
                {"name": "part_size", "member": "int64", "type": "int64", "required": False,
                 "document": "分片大小（MB），默认 20"},
                {"name": "rate_limiting", "member": "int64", "type": "int64", "required": False,
                 "document": "单链接限速（MB/s），0 表示不限速"},
                # 重试 / 校验
                {"name": "retry", "member": "int64", "type": "int64", "required": False,
                 "document": "失败重试次数，默认 3，设为 0 表示不重试"},
                {"name": "err_retry_num", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的额外重试次数，默认 0"},
                {"name": "err_retry_interval", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的重试间隔（秒），默认 0"},
                {"name": "disable_crc64", "member": "bool", "type": "bool", "required": False,
                 "document": "关闭上传后 CRC64 校验，默认 false"},
                # 日志
                {"name": "log_file", "member": "string", "type": "string", "required": False,
                 "document": "失败日志文件路径，指定后将失败记录写入该文件，默认不输出日志"},
                {"name": "fail_output", "member": "bool", "type": "bool", "required": False,
                 "document": "启用失败日志输出，默认 false"},
                {"name": "fail_output_path", "member": "string", "type": "string", "required": False,
                 "document": "失败日志输出路径"},
            ],
        },
        "sync_uploadResponse": {
            "members": [],
        },
        # ===== sync_download 接口参数 =====
        "sync_downloadRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "源存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "local_path", "member": "string", "type": "string", "required": True,
                 "document": "本地目标目录路径"},
                {"name": "cos_key", "member": "string", "type": "string", "required": False,
                 "document": "COS 上的源对象键（Key），作为前缀"},
                {"name": "recursive", "member": "bool", "type": "bool", "required": False,
                 "document": "是否递归同步目录，默认 false"},
                # 跳过策略
                {"name": "ignore_existing", "member": "bool", "type": "bool", "required": False,
                 "document": "本地已存在即跳过，默认 false"},
                {"name": "update", "member": "bool", "type": "bool", "required": False,
                 "document": "仅在源文件比目标文件新时更新（按 Last-Modified 比较），默认 false"},
                {"name": "snapshot_path", "member": "string", "type": "string", "required": False,
                 "document": "快照数据库文件路径，用于加速增量判断"},
                # 删除多余
                {"name": "delete_extra", "member": "bool", "type": "bool", "required": False,
                 "document": "是否删除本地多余的文件，默认 false"},
                {"name": "delete", "member": "bool", "type": "bool", "required": False,
                 "document": "等同 --delete_extra，对齐 coscli --delete"},
                {"name": "backup_dir", "member": "string", "type": "string", "required": False,
                 "document": "删除本地多余文件前先备份到该目录"},
                {"name": "force", "member": "bool", "type": "bool", "required": False,
                 "document": "跳过确认提示，默认 false"},
                # 过滤
                {"name": "include", "member": "string", "type": "string", "required": False,
                 "document": "包含匹配模式，支持通配符，如 *.txt"},
                {"name": "exclude", "member": "string", "type": "string", "required": False,
                 "document": "排除匹配模式，支持通配符，如 *.log"},
                {"name": "only_current_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "仅同步当前目录下的对象，不递归，默认 false"},
                {"name": "ignore_empty_file", "member": "bool", "type": "bool", "required": False,
                 "document": "忽略空对象，默认 false"},
                {"name": "forbid_overwrite", "member": "bool", "type": "bool", "required": False,
                 "document": "禁止覆盖本地已存在文件，默认 false"},
                # SSE-C
                {"name": "sse_customer_algorithm", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密算法"},
                {"name": "sse_customer_key", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密密钥"},
                {"name": "sse_customer_key_md5", "member": "string", "type": "string", "required": False,
                 "document": "SSE-C 加密密钥 MD5"},
                # 性能
                {"name": "thread_num", "member": "int64", "type": "int64", "required": False,
                 "document": "单文件分片下载并发线程数，默认 5"},
                {"name": "routines", "member": "int64", "type": "int64", "required": False,
                 "document": "文件间并发数（同时传输的文件数），默认 3"},
                {"name": "part_size", "member": "int64", "type": "int64", "required": False,
                 "document": "分片大小（MB），默认 20"},
                {"name": "rate_limiting", "member": "int64", "type": "int64", "required": False,
                 "document": "单链接限速（MB/s），0 表示不限速"},
                # 重试 / 校验
                {"name": "retry", "member": "int64", "type": "int64", "required": False,
                 "document": "失败重试次数，默认 3，设为 0 表示不重试"},
                {"name": "err_retry_num", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的额外重试次数，默认 0"},
                {"name": "err_retry_interval", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的重试间隔（秒），默认 0"},
                {"name": "disable_crc64", "member": "bool", "type": "bool", "required": False,
                 "document": "关闭下载后 CRC64 校验，默认 false"},
                # 日志
                {"name": "log_file", "member": "string", "type": "string", "required": False,
                 "document": "失败日志文件路径"},
                {"name": "fail_output", "member": "bool", "type": "bool", "required": False,
                 "document": "启用失败日志输出，默认 false"},
                {"name": "fail_output_path", "member": "string", "type": "string", "required": False,
                 "document": "失败日志输出路径"},
            ],
        },
        "sync_downloadResponse": {
            "members": [],
        },
        # ===== sync_copy 接口参数 =====
        "sync_copyRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "源存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": False,
                 "document": "源 COS 对象键（Key），作为前缀"},
                {"name": "dest_bucket", "member": "string", "type": "string", "required": False,
                 "document": "目标存储桶名称，不填则与源存储桶相同"},
                {"name": "dest_key", "member": "string", "type": "string", "required": False,
                 "document": "目标 COS 对象键（Key），作为目标前缀"},
                {"name": "dest_region", "member": "string", "type": "string", "required": False,
                 "document": "目标地域，不填则与当前地域相同"},
                {"name": "recursive", "member": "bool", "type": "bool", "required": False,
                 "document": "是否递归同步复制，默认 false"},
                # 跳过策略
                {"name": "ignore_existing", "member": "bool", "type": "bool", "required": False,
                 "document": "目标已存在即跳过，默认 false"},
                {"name": "update", "member": "bool", "type": "bool", "required": False,
                 "document": "仅在源对象比目标对象新时更新，默认 false"},
                # 删除多余
                {"name": "delete_extra", "member": "bool", "type": "bool", "required": False,
                 "document": "是否删除目标端多余的文件，默认 false"},
                {"name": "delete", "member": "bool", "type": "bool", "required": False,
                 "document": "等同 --delete_extra"},
                {"name": "force", "member": "bool", "type": "bool", "required": False,
                 "document": "跳过确认提示，默认 false"},
                # 过滤
                {"name": "include", "member": "string", "type": "string", "required": False,
                 "document": "包含匹配模式，支持通配符，如 *.txt"},
                {"name": "exclude", "member": "string", "type": "string", "required": False,
                 "document": "排除匹配模式，支持通配符，如 *.log"},
                {"name": "only_current_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "仅同步当前目录下的对象，不递归，默认 false"},
                {"name": "skip_dir", "member": "bool", "type": "bool", "required": False,
                 "document": "不同步空目录标记，默认 false"},
                {"name": "ignore_empty_file", "member": "bool", "type": "bool", "required": False,
                 "document": "忽略空对象，默认 false"},
                # 对象属性
                {"name": "storage_class", "member": "string", "type": "string", "required": False,
                 "document": "目标存储类型: STANDARD, STANDARD_IA, ARCHIVE, DEEP_ARCHIVE, INTELLIGENT_TIERING, MAZ_STANDARD, MAZ_STANDARD_IA"},
                {"name": "meta", "member": "string", "type": "string", "required": False,
                 "document": "自定义元数据，格式: key1=value1#key2=value2（设置后使用 Replaced 模式）"},
                {"name": "acl", "member": "string", "type": "string", "required": False,
                 "document": "目标对象 ACL"},
                {"name": "grant_read", "member": "string", "type": "string", "required": False,
                 "document": "授予读权限"},
                {"name": "grant_read_acp", "member": "string", "type": "string", "required": False,
                 "document": "授予读 ACP 权限"},
                {"name": "grant_write_acp", "member": "string", "type": "string", "required": False,
                 "document": "授予写 ACP 权限"},
                {"name": "grant_full_control", "member": "string", "type": "string", "required": False,
                 "document": "授予完全控制权限"},
                {"name": "tags", "member": "string", "type": "string", "required": False,
                 "document": "目标对象标签，设置后使用 Replaced 模式"},
                {"name": "forbid_overwrite", "member": "bool", "type": "bool", "required": False,
                 "document": "禁止覆盖目标已存在对象，默认 false"},
                {"name": "encryption_type", "member": "string", "type": "string", "required": False,
                 "document": "目标服务端加密类型: AES256 或 cos/kms"},
                # 性能
                {"name": "routines", "member": "int64", "type": "int64", "required": False,
                 "document": "文件间并发数（同时复制的文件数），默认 3"},
                # 重试
                {"name": "retry", "member": "int64", "type": "int64", "required": False,
                 "document": "失败重试次数，默认 3，设为 0 表示不重试"},
                {"name": "err_retry_num", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的额外重试次数，默认 0"},
                {"name": "err_retry_interval", "member": "int64", "type": "int64", "required": False,
                 "document": "可重试错误的重试间隔（秒），默认 0"},
                # 日志
                {"name": "log_file", "member": "string", "type": "string", "required": False,
                 "document": "失败日志文件路径"},
                {"name": "fail_output", "member": "bool", "type": "bool", "required": False,
                 "document": "启用失败日志输出，默认 false"},
                {"name": "fail_output_path", "member": "string", "type": "string", "required": False,
                 "document": "失败日志输出路径"},
            ],
        },
        "sync_copyResponse": {
            "members": [],
        },
        # ===== signurl 接口参数 =====
        "signurlRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "对象键（Key）"},
                {"name": "expired", "member": "int64", "type": "int64", "required": False,
                 "document": "URL 有效期（秒），默认 3600"},
                {"name": "method", "member": "string", "type": "string", "required": False,
                 "document": "HTTP 方法: GET(下载，默认), PUT(上传)"},
            ],
        },
        "signurlResponse": {
            "members": [],
        },
        # ===== get_bucket_acl 接口参数 =====
        "get_bucket_aclRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
            ],
        },
        "get_bucket_aclResponse": {
            "members": [],
        },
        # ===== put_bucket_acl 接口参数 =====
        "put_bucket_aclRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "acl", "member": "string", "type": "string", "required": False,
                 "document": "访问控制策略: private(默认), public-read, public-read-write"},
                {"name": "grant_read", "member": "string", "type": "string", "required": False,
                 "document": "授予读权限的用户，格式: id=\"账号ID\""},
                {"name": "grant_write", "member": "string", "type": "string", "required": False,
                 "document": "授予写权限的用户，格式: id=\"账号ID\""},
                {"name": "grant_full_control", "member": "string", "type": "string", "required": False,
                 "document": "授予完全控制权限的用户，格式: id=\"账号ID\""},
            ],
        },
        "put_bucket_aclResponse": {
            "members": [],
        },
        # ===== get_object_acl 接口参数 =====
        "get_object_aclRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "对象键（Key）"},
            ],
        },
        "get_object_aclResponse": {
            "members": [],
        },
        # ===== put_object_acl 接口参数 =====
        "put_object_aclRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "对象键（Key）"},
                {"name": "acl", "member": "string", "type": "string", "required": False,
                 "document": "访问控制策略: private(默认), public-read"},
                {"name": "grant_read", "member": "string", "type": "string", "required": False,
                 "document": "授予读权限的用户，格式: id=\"账号ID\""},
                {"name": "grant_full_control", "member": "string", "type": "string", "required": False,
                 "document": "授予完全控制权限的用户，格式: id=\"账号ID\""},
            ],
        },
        "put_object_aclResponse": {
            "members": [],
        },
        # ===== abort 接口参数 =====
        "abortRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "prefix", "member": "string", "type": "string", "required": False,
                 "document": "对象键前缀，用于过滤要清理的分片上传"},
                {"name": "cos_key", "member": "string", "type": "string", "required": False,
                 "document": "对象键（指定 upload_id 时必填）"},
                {"name": "upload_id", "member": "string", "type": "string", "required": False,
                 "document": "指定要取消的分片上传 ID，不填则清理所有未完成的分片上传"},
            ],
        },
        "abortResponse": {
            "members": [],
        },
        # ===== hash 接口参数 =====
        "hashRequest": {
            "members": [
                {"name": "local_path", "member": "string", "type": "string", "required": False,
                 "document": "本地文件路径（计算本地文件哈希时使用）"},
                {"name": "bucket", "member": "string", "type": "string", "required": False,
                 "document": "存储桶名称（获取 COS 对象哈希时使用）"},
                {"name": "cos_key", "member": "string", "type": "string", "required": False,
                 "document": "对象键（获取 COS 对象哈希时使用）"},
                {"name": "hash_type", "member": "string", "type": "string", "required": False,
                 "document": "哈希类型: md5(默认), sha1, sha256, crc64"},
            ],
        },
        "hashResponse": {
            "members": [],
        },
        # ===== get_object_tagging 接口参数 =====
        "get_object_taggingRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "对象键（Key）"},
            ],
        },
        "get_object_taggingResponse": {
            "members": [],
        },
        # ===== put_object_tagging 接口参数 =====
        "put_object_taggingRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "对象键（Key）"},
                {"name": "tags", "member": "string", "type": "string", "required": True,
                 "document": "标签列表，格式: key1=value1,key2=value2"},
            ],
        },
        "put_object_taggingResponse": {
            "members": [],
        },
        # ===== delete_object_tagging 接口参数 =====
        "delete_object_taggingRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "对象键（Key）"},
            ],
        },
        "delete_object_taggingResponse": {
            "members": [],
        },
        # ===== du 接口参数 =====
        "duRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "prefix", "member": "string", "type": "string", "required": False,
                 "document": "对象键前缀，用于统计指定目录的大小"},
            ],
        },
        "duResponse": {
            "members": [],
        },
        # ===== cat 接口参数 =====
        "catRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "对象键（Key）"},
                {"name": "range", "member": "string", "type": "string", "required": False,
                 "document": "指定读取范围，格式: bytes=0-1023"},
                {"name": "max_size", "member": "int64", "type": "int64", "required": False,
                 "document": "最大读取大小（MB），超过此大小仅显示部分内容，默认 10"},
            ],
        },
        "catResponse": {
            "members": [],
        },
        # ===== lsparts 接口参数 =====
        "lspartsRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称，格式如 my-bucket-1250000000"},
                {"name": "prefix", "member": "string", "type": "string", "required": False,
                 "document": "对象键前缀，用于过滤列出的分片上传"},
            ],
        },
        "lspartsResponse": {
            "members": [],
        },
        # ===== create_symlink =====
        "create_symlinkRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "软链接对象键"},
                {"name": "target_key", "member": "string", "type": "string", "required": True,
                 "document": "软链接指向的目标对象键"},
                {"name": "storage_class", "member": "string", "type": "string", "required": False,
                 "document": "软链接对象的存储类型"},
            ],
        },
        "create_symlinkResponse": {"members": []},
        # ===== get_symlink =====
        "get_symlinkRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "软链接对象键"},
            ],
        },
        "get_symlinkResponse": {"members": []},
        # ===== add_object_tagging =====
        "add_object_taggingRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称"},
                {"name": "cos_key", "member": "string", "type": "string", "required": True,
                 "document": "对象键"},
                {"name": "tags", "member": "string", "type": "string", "required": True,
                 "document": "追加的标签列表，格式: key1=value1,key2=value2（同 key 覆盖旧值）"},
            ],
        },
        "add_object_taggingResponse": {"members": []},
        # ===== inventory put =====
        "put_bucket_inventoryRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称"},
                {"name": "id", "member": "string", "type": "string", "required": True,
                 "document": "清单任务 ID"},
                {"name": "is_enabled", "member": "bool", "type": "bool", "required": False,
                 "document": "是否启用该清单任务，默认 true"},
                {"name": "frequency", "member": "string", "type": "string", "required": False,
                 "document": "清单生成频率: Daily(默认) / Weekly"},
                {"name": "included_object_versions", "member": "string", "type": "string", "required": False,
                 "document": "清单包含的版本: Current(默认) / All"},
                {"name": "prefix", "member": "string", "type": "string", "required": False,
                 "document": "清单过滤前缀"},
                {"name": "fields", "member": "string", "type": "string", "required": False,
                 "document": "可选字段列表，逗号分隔，如 Size,LastModifiedDate,StorageClass,ETag"},
                {"name": "dest_bucket", "member": "string", "type": "string", "required": False,
                 "document": "清单结果目标存储桶（完整 QCS 格式，如 qcs::cos:ap-guangzhou::my-bucket-1250000000）"},
                {"name": "dest_account_id", "member": "string", "type": "string", "required": False,
                 "document": "清单结果目标账号 ID"},
                {"name": "dest_prefix", "member": "string", "type": "string", "required": False,
                 "document": "清单结果目标 key 前缀"},
                {"name": "dest_format", "member": "string", "type": "string", "required": False,
                 "document": "清单结果格式: CSV(默认) / ORC"},
            ],
        },
        "put_bucket_inventoryResponse": {"members": []},
        # ===== inventory get =====
        "get_bucket_inventoryRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称"},
                {"name": "id", "member": "string", "type": "string", "required": True,
                 "document": "清单任务 ID"},
            ],
        },
        "get_bucket_inventoryResponse": {"members": []},
        # ===== inventory list =====
        "list_bucket_inventoryRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称"},
            ],
        },
        "list_bucket_inventoryResponse": {"members": []},
        # ===== inventory delete =====
        "delete_bucket_inventoryRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称"},
                {"name": "id", "member": "string", "type": "string", "required": True,
                 "document": "清单任务 ID"},
            ],
        },
        "delete_bucket_inventoryResponse": {"members": []},
        # ===== inventory post =====
        "post_bucket_inventoryRequest": {
            "members": [
                {"name": "bucket", "member": "string", "type": "string", "required": True,
                 "document": "存储桶名称"},
                {"name": "id", "member": "string", "type": "string", "required": True,
                 "document": "清单任务 ID"},
                {"name": "included_object_versions", "member": "string", "type": "string", "required": False,
                 "document": "清单包含的版本: Current(默认) / All"},
                {"name": "prefix", "member": "string", "type": "string", "required": False,
                 "document": "清单过滤前缀"},
                {"name": "fields", "member": "string", "type": "string", "required": False,
                 "document": "可选字段列表，逗号分隔"},
                {"name": "dest_bucket", "member": "string", "type": "string", "required": False,
                 "document": "清单结果目标存储桶"},
                {"name": "dest_account_id", "member": "string", "type": "string", "required": False,
                 "document": "清单结果目标账号 ID"},
                {"name": "dest_prefix", "member": "string", "type": "string", "required": False,
                 "document": "清单结果目标 key 前缀"},
                {"name": "dest_format", "member": "string", "type": "string", "required": False,
                 "document": "清单结果格式: CSV(默认) / ORC"},
            ],
        },
        "post_bucket_inventoryResponse": {"members": []},
    },
    "version": "1.0",
}


def register_service(specs):
    specs[service_name] = {
        service_version: _spec,
    }
