# -*- coding: utf-8 -*-
"""
COS 插件工具模块
提供凭据解析、文件过滤、格式化等通用功能
"""
import os
import sys
import time
import json
import fnmatch
import threading as _threading


# ============================================================
# SDK header maplist 扩展
# SDK 的 qcloud_cos.cos_comm.maplist 只预置了部分 HTTP 头映射，
# 对齐 coscli 所需的若干扩展头（forbid_overwrite/tagging_directive/
# grant_read_acp/grant_write_acp 等）不在其中；若不扩展，SDK 的
# mapped() 会直接抛出 "No Parameter Named X Please Check It"。
# 模块加载时一次性注入，保证后续所有 put_object/upload_file/copy
# 调用时可以正常透传为 HTTP 头。
# ============================================================
try:
    from qcloud_cos import cos_comm as _cos_comm
    _cos_comm.maplist.setdefault("ForbidOverwrite", "x-cos-forbid-overwrite")
    _cos_comm.maplist.setdefault("GrantReadACP", "x-cos-grant-read-acp")
    _cos_comm.maplist.setdefault("GrantWriteACP", "x-cos-grant-write-acp")
    _cos_comm.maplist.setdefault("TaggingDirective", "x-cos-tagging-directive")
except Exception:
    # SDK 未安装或版本差异时静默忽略，后续调用会自然报错
    pass


def _load_json_file(filepath):
    """加载 JSON 配置文件"""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return {}


def parse_global_arg(parsed_globals):
    """
    从 TCCLI 配置文件和环境变量中加载凭据信息，填充到 parsed_globals 中。
    对齐标准 TCCLI 服务（如 CVM）的 parse_global_arg 逻辑。
    """
    g_param = parsed_globals

    # 确定 profile
    profile = g_param.get("profile") or os.environ.get("TCCLI_PROFILE", "default")
    g_param["profile"] = profile

    # 加载配置文件
    configure_path = os.path.join(os.path.expanduser("~"), ".tccli")
    conf_path = os.path.join(configure_path, profile + ".configure")
    cred_path = os.path.join(configure_path, profile + ".credential")

    conf = _load_json_file(conf_path)
    cred = _load_json_file(cred_path)

    # 从环境变量加载凭据（优先级高于配置文件）
    env_secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID")
    env_secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY")
    env_token = os.environ.get("TENCENTCLOUD_TOKEN")
    env_region = os.environ.get("TENCENTCLOUD_REGION")

    # 填充 secretId
    if g_param.get("secretId") is None:
        if env_secret_id:
            g_param["secretId"] = env_secret_id
        elif "secretId" in cred:
            g_param["secretId"] = cred["secretId"]

    # 填充 secretKey
    if g_param.get("secretKey") is None:
        if env_secret_key:
            g_param["secretKey"] = env_secret_key
        elif "secretKey" in cred:
            g_param["secretKey"] = cred["secretKey"]

    # 填充 token
    if g_param.get("token") is None:
        if env_token:
            g_param["token"] = env_token
        elif "token" in cred:
            g_param["token"] = cred["token"]
        else:
            g_param["token"] = None

    # 填充 region
    if g_param.get("region") is None:
        if env_region:
            g_param["region"] = env_region
        elif isinstance(conf.get("_sys_param"), dict) and "region" in conf["_sys_param"]:
            g_param["region"] = conf["_sys_param"]["region"]

    # 填充 endpoint
    if g_param.get("endpoint") is None:
        g_param["endpoint"] = None

    # 校验必要参数
    if not g_param.get("secretId"):
        raise Exception(
            "secretId 未配置。请通过以下方式之一配置：\n"
            "  1. tccli configure  (交互式配置)\n"
            "  2. 设置环境变量 TENCENTCLOUD_SECRET_ID\n"
            "  3. 命令行参数 --secretId YOUR_SECRET_ID"
        )
    if not g_param.get("secretKey"):
        raise Exception(
            "secretKey 未配置。请通过以下方式之一配置：\n"
            "  1. tccli configure  (交互式配置)\n"
            "  2. 设置环境变量 TENCENTCLOUD_SECRET_KEY\n"
            "  3. 命令行参数 --secretKey YOUR_SECRET_KEY"
        )

    return g_param


def init_cos_client(parsed_globals):
    """
    标准 COS 客户端初始化。
    返回 (client, region) 元组。
    """
    from qcloud_cos import CosConfig
    from qcloud_cos import CosS3Client

    parsed_globals = parse_global_arg(parsed_globals)
    secret_id = parsed_globals["secretId"]
    secret_key = parsed_globals["secretKey"]
    token = parsed_globals["token"]
    region = parsed_globals["region"] or "ap-guangzhou"
    endpoint = parsed_globals["endpoint"]

    config = CosConfig(
        Region=region,
        SecretId=secret_id,
        SecretKey=secret_key,
        Token=token,
        Endpoint=endpoint,
    )
    client = CosS3Client(config)
    return client, region


def format_size(size_bytes):
    """格式化文件大小为人类可读的字符串"""
    if size_bytes < 1024:
        return "%d B" % size_bytes
    elif size_bytes < 1024 * 1024:
        return "%.2f KB" % (size_bytes / 1024.0)
    elif size_bytes < 1024 * 1024 * 1024:
        return "%.2f MB" % (size_bytes / (1024.0 * 1024))
    elif size_bytes < 1024 * 1024 * 1024 * 1024:
        return "%.2f GB" % (size_bytes / (1024.0 * 1024 * 1024))
    else:
        return "%.2f TB" % (size_bytes / (1024.0 * 1024 * 1024 * 1024))


def match_filters(name, include, exclude):
    """
    根据 include/exclude 模式过滤文件名。
    返回 True 表示文件应被处理，False 表示应跳过。
    """
    if include and not fnmatch.fnmatch(name, include):
        return False
    if exclude and fnmatch.fnmatch(name, exclude):
        return False
    return True


# ============================================================
# 公共参数解析辅助：对齐 coscli 的 cp / sync 的 ACL / SSE / tags 参数
# ============================================================
_VALID_ACL = {"default", "private", "public-read", "public-read-write", "authenticated-read",
              "bucket-owner-read", "bucket-owner-full-control"}


def parse_acl_args(args):
    """
    解析 ACL 相关参数，返回可用于 put_object / upload_file / copy_object 的 header dict：
        {"ACL": "...", "GrantRead": "...", "GrantReadACP": "...", ...}
    支持参数：acl / grant_read / grant_read_acp / grant_write_acp / grant_full_control
    返回空 dict 表示未设置。
    """
    headers = {}
    acl = args.get("acl", "") or ""
    if acl and acl in _VALID_ACL:
        headers["ACL"] = acl
    for k, sdk_key in (("grant_read", "GrantRead"),
                       ("grant_read_acp", "GrantReadACP"),
                       ("grant_write", "GrantWrite"),
                       ("grant_write_acp", "GrantWriteACP"),
                       ("grant_full_control", "GrantFullControl")):
        v = args.get(k, "") or ""
        if v:
            headers[sdk_key] = v
    return headers


def parse_sse_args(args):
    """
    解析服务端加密参数，返回可直接合并到 upload_file / put_object 的 kwargs dict。
    - encryption_type / server_side_encryption: "AES256" / "cos/kms"（与 coscli 对齐）
    - sse_customer_algorithm: SSE-C 算法，固定为 "AES256"
    - sse_customer_key: SSE-C 密钥（32 字节，Base64 编码或原文，直接透传给 SDK）
    - sse_customer_key_md5: SSE-C 密钥 MD5
    """
    kwargs = {}
    enc = args.get("encryption_type", "") or args.get("server_side_encryption", "") or ""
    if enc:
        # 对齐 coscli：encryption_type=AES256 或 cos/kms
        kwargs["ServerSideEncryption"] = enc
    sse_alg = args.get("sse_customer_algorithm", "") or ""
    sse_key = args.get("sse_customer_key", "") or ""
    sse_key_md5 = args.get("sse_customer_key_md5", "") or ""
    if sse_alg:
        kwargs["SSECustomerAlgorithm"] = sse_alg
    if sse_key:
        kwargs["SSECustomerKey"] = sse_key
    if sse_key_md5:
        kwargs["SSECustomerKeyMD5"] = sse_key_md5
    return kwargs


def parse_tags(tags_str):
    """
    解析对象标签字符串，支持两种分隔符：
    - "key1=value1&key2=value2"（coscli 风格）
    - "key1=value1,key2=value2"（tccli 旧风格，兼容）
    返回 URL 编码后的 "k1=v1&k2=v2" 字符串，可直接作为 x-cos-tagging / Tagging 头使用。
    空串/无有效键值对时返回空串。
    """
    if not tags_str:
        return ""
    try:
        from urllib.parse import quote
    except ImportError:
        from urllib import quote
    # 同时支持 & 和 , 作为分隔符
    parts = []
    for seg in tags_str.replace(",", "&").split("&"):
        seg = seg.strip()
        if not seg or "=" not in seg:
            continue
        k, v = seg.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            continue
        parts.append("%s=%s" % (quote(k, safe=""), quote(v, safe="")))
    return "&".join(parts)


def build_extra_put_headers(args):
    """
    为 put_object / upload_file 构造通用扩展 headers，包括：
    - ACL / grant_*（来自 parse_acl_args）
    - 服务端加密（来自 parse_sse_args）
    - 对象标签（tags）
    - 禁止覆盖（forbid_overwrite）
    返回可直接合并到 SDK 调用 kwargs 的 dict。
    """
    kwargs = {}
    kwargs.update(parse_acl_args(args))
    kwargs.update(parse_sse_args(args))
    tags = parse_tags(args.get("tags", "") or "")
    if tags:
        # SDK 支持 'Tagging' 参数或 'x-cos-tagging' 头
        kwargs["Tagging"] = tags
    if args.get("forbid_overwrite", False):
        # 对齐 coscli 的 --forbid-overwrite，设置 x-cos-forbid-overwrite 头
        kwargs["ForbidOverwrite"] = "true"
    return kwargs


def build_extra_copy_headers(args):
    """
    为 copy_object 构造通用扩展 headers。
    在 build_extra_put_headers 基础上，按 copy 接口的约定：
    - 标签默认从源对象继承，若显式指定 tags 则需 TaggingDirective="Replaced"
    - 元数据同理，已在命令层处理 MetadataDirective
    """
    kwargs = build_extra_put_headers(args)
    if "Tagging" in kwargs:
        kwargs["TaggingDirective"] = "Replaced"
    return kwargs


# ============================================================
# SnapshotDB：对齐 coscli 的 --snapshot-path
# 用于加速同步跳过判断，避免每次都 HEAD + CRC64 计算。
# 使用 Python 标准库 sqlite3 作为后端（零额外依赖，跨平台），
# 对齐 coscli 使用 LevelDB 文件型 KV 的思路。
#
# 表结构：
#   CREATE TABLE IF NOT EXISTS snapshot (
#       key        TEXT PRIMARY KEY,
#       mtime      REAL NOT NULL,
#       size       INTEGER NOT NULL,
#       crc64      TEXT,
#       updated_at REAL NOT NULL
#   )
# ============================================================
class SnapshotDB(object):
    """基于 SQLite 文件的快照数据库，线程安全。

    使用方式：
        snap = SnapshotDB.open(path)   # path 为空/None 时返回 None
        if snap.is_synced(key, mtime, size): ...
        snap.update(key, mtime, size, crc64)  # 即时 UPSERT 并 commit
        snap.save()                           # 做最终 commit + close（幂等）

    特性：
      - 每个线程持有自己的 connection（通过 threading.local），避免
        SQLite 同连接跨线程使用的限制；并发场景下通过 SQLite 的文件锁
        自动串行化写入。
      - WAL 模式 + synchronous=NORMAL，在崩溃安全与吞吐之间做平衡。
      - update() 即时写库并 commit，Ctrl+C 时也不会丢失已同步记录。
    """

    _VERSION = 1

    def __init__(self, path):
        self._path = path
        # 每个线程独立 connection
        self._tls = _threading.local()
        # 仅用于保护 connection 集合（用于 save 时统一 close 所有连接）
        self._conns_lock = _threading.Lock()
        self._conns = []
        self._closed = False

    @classmethod
    def open(cls, path):
        """打开或创建一个 SnapshotDB；path 为空返回 None。"""
        if not path:
            return None
        db = cls(path)
        # 预先确保父目录存在并初始化表结构
        snap_dir = os.path.dirname(path)
        if snap_dir and not os.path.isdir(snap_dir):
            try:
                os.makedirs(snap_dir, exist_ok=True)
            except OSError as e:
                sys.stderr.write("警告：创建快照目录失败: %s\n" % str(e))
                sys.stderr.flush()
        try:
            conn = db._get_conn()
            conn.execute(
                "CREATE TABLE IF NOT EXISTS snapshot ("
                "  key TEXT PRIMARY KEY,"
                "  mtime REAL NOT NULL,"
                "  size INTEGER NOT NULL,"
                "  crc64 TEXT,"
                "  updated_at REAL NOT NULL"
                ")"
            )
            conn.commit()
        except Exception as e:
            sys.stderr.write("警告：打开快照数据库失败: %s\n" % str(e))
            sys.stderr.flush()
        return db

    def _get_conn(self):
        """为当前线程懒创建一个 sqlite3 connection。"""
        import sqlite3
        conn = getattr(self._tls, "conn", None)
        if conn is not None:
            return conn
        # check_same_thread=True 是默认值，但我们为每个线程独立建连接，所以允许保持默认
        conn = sqlite3.connect(self._path, timeout=30.0, isolation_level=None)
        # 性能与并发相关 pragma
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA temp_store=MEMORY")
        except Exception:
            pass
        self._tls.conn = conn
        with self._conns_lock:
            self._conns.append(conn)
        return conn

    def is_synced(self, key, mtime, size):
        """快速判断：指定 key 在快照中且 {mtime, size} 一致 → 已同步"""
        if mtime is None or size is None or self._closed:
            return False
        try:
            conn = self._get_conn()
            cur = conn.execute(
                "SELECT mtime, size FROM snapshot WHERE key=? LIMIT 1", (key,)
            )
            row = cur.fetchone()
        except Exception:
            return False
        if not row:
            return False
        try:
            rec_mtime, rec_size = row
            # 允许 mtime 微小浮点误差（<= 1s）
            return (abs(float(rec_mtime) - float(mtime)) <= 1.0 and
                    int(rec_size) == int(size))
        except (TypeError, ValueError):
            return False

    def get_crc64(self, key):
        if self._closed:
            return None
        try:
            conn = self._get_conn()
            cur = conn.execute(
                "SELECT crc64 FROM snapshot WHERE key=? LIMIT 1", (key,)
            )
            row = cur.fetchone()
        except Exception:
            return None
        return row[0] if row else None

    def update(self, key, mtime, size, crc64=None):
        """UPSERT 单条记录并立即写入（isolation_level=None 下为自动提交）。"""
        if self._closed:
            return
        try:
            conn = self._get_conn()
            conn.execute(
                "INSERT INTO snapshot(key, mtime, size, crc64, updated_at) "
                "VALUES(?, ?, ?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET "
                "  mtime=excluded.mtime, size=excluded.size, "
                "  crc64=excluded.crc64, updated_at=excluded.updated_at",
                (
                    key,
                    float(mtime) if mtime is not None else 0.0,
                    int(size) if size is not None else 0,
                    crc64 or "",
                    time.time(),
                ),
            )
        except Exception as e:
            sys.stderr.write("警告：快照写入失败（key=%s）: %s\n" % (key, str(e)))
            sys.stderr.flush()

    def remove(self, key):
        if self._closed:
            return
        try:
            conn = self._get_conn()
            conn.execute("DELETE FROM snapshot WHERE key=?", (key,))
        except Exception:
            pass

    def save(self):
        """最终落盘并关闭所有线程的 connection（幂等）。

        由于 update/remove 在 isolation_level=None 下已自动提交，
        save() 主要用于显式关闭连接、触发 WAL checkpoint。
        """
        if self._closed:
            return
        self._closed = True
        with self._conns_lock:
            conns, self._conns = self._conns, []
        for conn in conns:
            try:
                try:
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                except Exception:
                    pass
                conn.close()
            except Exception:
                pass


def parse_meta(meta_str):
    """
    解析自定义元数据字符串。
    格式: key1=value1#key2=value2
    返回 dict，key 自动加上 x-cos-meta- 前缀。
    """
    metadata = {}
    if meta_str:
        for pair in meta_str.split("#"):
            pair = pair.strip()
            if "=" in pair:
                k, v = pair.split("=", 1)
                metadata["x-cos-meta-" + k.strip()] = v.strip()
    return metadata


def build_cos_key(prefix, rel_path):
    """
    根据前缀和相对路径构造 COS 对象键。
    """
    if not prefix:
        return rel_path
    if prefix.endswith("/"):
        return prefix + rel_path
    return prefix + "/" + rel_path


def list_all_objects(client, bucket, prefix=""):
    """列出存储桶中指定前缀下的所有对象（跳过目录标记）"""
    objects = {}
    marker = ""
    while True:
        response = client.list_objects(
            Bucket=bucket,
            Prefix=prefix,
            Marker=marker,
            MaxKeys=1000,
        )
        if "Contents" in response:
            for content in response["Contents"]:
                key = content["Key"]
                if key.endswith("/"):
                    continue
                objects[key] = {
                    "Size": int(content.get("Size", 0)),
                    "ETag": content.get("ETag", ""),
                    "LastModified": content.get("LastModified", ""),
                    "StorageClass": content.get("StorageClass", "STANDARD"),
                }
        if response.get("IsTruncated") == "true":
            marker = response.get("NextMarker", "")
        else:
            break
    return objects


def list_all_objects_with_dirs(client, bucket, prefix=""):
    """列出存储桶中指定前缀下的所有对象（包含 / 结尾的目录标记）"""
    objects = {}
    marker = ""
    while True:
        response = client.list_objects(
            Bucket=bucket,
            Prefix=prefix,
            Marker=marker,
            MaxKeys=1000,
        )
        if "Contents" in response:
            for content in response["Contents"]:
                key = content["Key"]
                objects[key] = {
                    "Size": int(content.get("Size", 0)),
                    "ETag": content.get("ETag", ""),
                    "LastModified": content.get("LastModified", ""),
                    "StorageClass": content.get("StorageClass", "STANDARD"),
                    "IsDir": key.endswith("/"),
                }
        if response.get("IsTruncated") == "true":
            marker = response.get("NextMarker", "")
        else:
            break
    return objects


def list_local_files(local_dir, only_current_dir=False,
                      disable_all_symlink=False, enable_symlink_dir=False):
    """递归列出本地目录下的所有文件

    - only_current_dir: 仅列出当前目录一层（不递归）
    - disable_all_symlink: 禁用所有符号链接（文件和目录都跳过）
    - enable_symlink_dir: 允许跟随符号链接目录（默认不跟随目录链接，文件链接始终跟随，
      除非 disable_all_symlink=True）
    """
    files = {}
    if only_current_dir:
        # 只列出当前目录一层
        try:
            for entry in os.listdir(local_dir):
                full_path = os.path.join(local_dir, entry)
                if not os.path.isfile(full_path):
                    continue
                if disable_all_symlink and os.path.islink(full_path):
                    continue
                files[entry] = {
                    "Size": os.path.getsize(full_path),
                    "FullPath": full_path,
                    "MTime": os.path.getmtime(full_path),
                }
        except OSError:
            pass
        return files

    # followlinks 控制是否跟随符号链接目录
    followlinks = enable_symlink_dir and not disable_all_symlink
    for root, dirs, filenames in os.walk(local_dir, followlinks=followlinks):
        # 过滤符号链接目录
        if disable_all_symlink:
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        elif not enable_symlink_dir:
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]

        for filename in filenames:
            full_path = os.path.join(root, filename)
            # 过滤符号链接文件
            if disable_all_symlink and os.path.islink(full_path):
                continue
            rel_path = os.path.relpath(full_path, local_dir)
            rel_path = rel_path.replace(os.sep, "/")
            try:
                files[rel_path] = {
                    "Size": os.path.getsize(full_path),
                    "FullPath": full_path,
                    "MTime": os.path.getmtime(full_path),
                }
            except OSError:
                # 符号链接指向不存在的目标等情况
                continue
    return files


def calculate_local_crc64(file_path):
    """
    计算本地文件的 CRC64 (ECMA-182 多项式)，对齐 COS 返回的 x-cos-hash-crc64ecma 头。
    参数：polynomial=0x142F0E1EBA9EA3693, initCrc=0, xorOut=0xFFFFFFFFFFFFFFFF, rev=True
    （该参数组合经实测与 COS 服务端 CRC64 结果精确匹配；与 Go 标准库 hash/crc64 搭配
    crc64.MakeTable(crc64.ECMA) 并以 ^uint64(0) 作为 xorOut 的行为一致。）
    返回字符串形式的无符号十进制数；失败返回 None（例如未安装 crcmod 时）。
    """
    try:
        import crcmod
    except ImportError:
        return None
    try:
        crc64_fn = crcmod.mkCrcFun(
            0x142F0E1EBA9EA3693,
            initCrc=0,
            xorOut=0xFFFFFFFFFFFFFFFF,
            rev=True,
        )
        crc = 0
        with open(file_path, "rb") as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                crc = crc64_fn(data, crc)
        return str(crc)
    except (IOError, OSError):
        return None


def get_object_head(client, bucket, cos_key):
    """
    获取 COS 对象的 HEAD 响应。返回 dict（可直接取 'x-cos-hash-crc64ecma'/'Last-Modified' 等头）。
    对象不存在或任何异常时返回 None。用于 sync 跳过判断。
    """
    from qcloud_cos import CosServiceError
    try:
        return client.head_object(Bucket=bucket, Key=cos_key)
    except CosServiceError:
        return None
    except Exception:
        return None


def parse_http_time(time_str):
    """
    解析 HTTP 时间字符串（RFC1123/RFC3339），返回 Unix 时间戳（float）；失败返回 None。
    用于 sync --update 模式对比 Last-Modified 时间。
    """
    if not time_str:
        return None
    import calendar
    from email.utils import parsedate_tz, mktime_tz
    # 优先按 RFC1123/RFC822（如 "Mon, 02 Jan 2006 15:04:05 GMT"）
    parsed = parsedate_tz(time_str)
    if parsed is not None:
        try:
            return float(mktime_tz(parsed))
        except (TypeError, ValueError, OverflowError):
            pass
    # 回退按 RFC3339（如 "2006-01-02T15:04:05Z"）
    try:
        import datetime
        s = time_str.rstrip("Z")
        dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        return float(calendar.timegm(dt.timetuple()))
    except ValueError:
        return None


def should_skip_sync_upload(client, bucket, cos_key, local_full_path, local_mtime,
                             ignore_existing=False, update=False, snapshot_db=None):
    """
    判断同步上传时是否跳过该文件，对齐 coscli 的 skipUpload。
    跳过规则（优先级从高到低）：
      1. --ignore-existing：目标存在即跳过
      2. --update：目标存在且 Last-Modified >= 本地 mtime 则跳过
      3. snapshot_db（快速路径）：本地 {mtime, size} 与快照一致 → 直接跳过，无需访问 COS
      4. 默认（CRC64）：对比本地 CRC64 与 COS HEAD 的 x-cos-hash-crc64ecma；相等则跳过
    返回 True 表示跳过，False 表示需要上传。
    目标不存在、无法获取 CRC64 或比较不相等时均返回 False。
    """
    # snapshot_db 快速路径：若快照已记录本地文件，则直接跳过（coscli 行为）
    # ignore_existing 和 update 有更高优先级
    if not ignore_existing and not update and snapshot_db is not None:
        try:
            local_size = os.path.getsize(local_full_path)
        except OSError:
            local_size = None
        if local_size is not None and snapshot_db.is_synced(cos_key, local_mtime, local_size):
            return True

    head = get_object_head(client, bucket, cos_key)
    if head is None:
        return False  # 目标不存在或异常，不跳过
    if ignore_existing:
        return True
    if update:
        last_modified = head.get("Last-Modified") or head.get("last-modified", "")
        remote_ts = parse_http_time(last_modified)
        if remote_ts is not None and remote_ts >= local_mtime:
            return True
        return False
    # 默认：CRC64 比较
    cos_crc = head.get("x-cos-hash-crc64ecma", "")
    if not cos_crc:
        return False
    local_crc = calculate_local_crc64(local_full_path)
    if local_crc is None:
        return False
    skipped = (cos_crc == local_crc)
    # 若校验一致并启用快照，同步更新快照
    if skipped and snapshot_db is not None:
        try:
            local_size = os.path.getsize(local_full_path)
            snapshot_db.update(cos_key, local_mtime, local_size, local_crc)
        except OSError:
            pass
    return skipped


def should_skip_sync_download(client, bucket, cos_key, cos_head_info, local_full_path,
                               ignore_existing=False, update=False, snapshot_db=None):
    """
    判断同步下载时是否跳过该文件，对齐 coscli 的 skipDownload。
    - cos_head_info: 从 list_objects 得到的对象信息 dict（含 'Size' / 'LastModified' 等）
    跳过规则（优先级从高到低）：
      1. --ignore-existing：本地存在即跳过
      2. --update：本地 mtime >= COS LastModified 则跳过
      3. snapshot_db（快速路径）：本地 {mtime, size} 与快照一致 → 跳过
      4. 默认（CRC64）：对比本地 CRC64 与 COS HEAD 的 x-cos-hash-crc64ecma；相等则跳过
    返回 True 表示跳过，False 表示需要下载。
    """
    if not os.path.exists(local_full_path):
        return False
    if ignore_existing:
        return True
    if update:
        local_mtime = os.path.getmtime(local_full_path)
        remote_ts = parse_http_time(cos_head_info.get("LastModified", ""))
        if remote_ts is not None and local_mtime >= remote_ts:
            return True
        return False
    # snapshot 快速路径
    if snapshot_db is not None:
        try:
            local_size = os.path.getsize(local_full_path)
            local_mtime = os.path.getmtime(local_full_path)
        except OSError:
            local_size = None
            local_mtime = None
        if local_size is not None and snapshot_db.is_synced(cos_key, local_mtime, local_size):
            return True
    # 默认：CRC64 比较
    local_crc = calculate_local_crc64(local_full_path)
    if local_crc is None:
        return False
    head = get_object_head(client, bucket, cos_key)
    if head is None:
        return False
    cos_crc = head.get("x-cos-hash-crc64ecma", "")
    if not cos_crc:
        return False
    skipped = (cos_crc == local_crc)
    if skipped and snapshot_db is not None:
        try:
            local_size = os.path.getsize(local_full_path)
            local_mtime = os.path.getmtime(local_full_path)
            snapshot_db.update(cos_key, local_mtime, local_size, local_crc)
        except OSError:
            pass
    return skipped


def should_skip_sync_copy(client, src_bucket, src_key, dest_bucket, dest_key,
                           ignore_existing=False, update=False):
    """
    判断同步复制时是否跳过该文件，对齐 coscli 的 skipCopy。
    跳过规则（优先级从高到低）：
      1. --ignore-existing：目标存在即跳过
      2. --update：目标 Last-Modified >= 源 Last-Modified 则跳过
      3. 默认（CRC64）：对比源 CRC64 与目标 CRC64；相等则跳过
    返回 True 表示跳过，False 表示需要复制。
    """
    dest_head = get_object_head(client, dest_bucket, dest_key)
    if dest_head is None:
        return False
    if ignore_existing:
        return True
    src_head = get_object_head(client, src_bucket, src_key)
    if src_head is None:
        return False
    if update:
        src_ts = parse_http_time(src_head.get("Last-Modified", ""))
        dest_ts = parse_http_time(dest_head.get("Last-Modified", ""))
        if src_ts is not None and dest_ts is not None and dest_ts >= src_ts:
            return True
        return False
    # 默认：CRC64 比较
    src_crc = src_head.get("x-cos-hash-crc64ecma", "")
    dest_crc = dest_head.get("x-cos-hash-crc64ecma", "")
    if not src_crc or not dest_crc:
        return False
    return src_crc == dest_crc


# ============================================================
# 进度监控模块 - 对齐 COSCLI 的 FileProcessMonitor
# ============================================================


class TransferProgressMonitor(object):
    """
    文件传输进度监控器，对齐 COSCLI 的 FileProcessMonitor。
    支持实时显示：总数/已处理数/成功/跳过/失败/进度百分比/速度。
    支持通过 SDK progress_callback 实现分片级别的实时进度更新。
    """

    def __init__(self, op_type="upload"):
        self.op_type = op_type  # upload / download / copy / move
        self._lock = _threading.Lock()
        # 扫描统计
        self.total_num = 0
        self.total_size = 0
        self.scan_end = False
        # 处理统计
        self.ok_num = 0
        self.skip_num = 0
        self.err_num = 0
        self.deal_size = 0       # 已处理的总大小（含跳过）
        self.transfer_size = 0   # 实际传输的大小（通过 progress_callback 实时更新）
        self.skip_size = 0
        # 每个文件的已传输字节数追踪（用于 progress_callback）
        self._file_progress = {}  # file_id -> consumed_bytes
        self._file_id_counter = 0
        # 失败记录列表：每项为 dict {"path": ..., "reason": ...}
        self._fail_records = []
        # 速度计算
        self._start_time = time.time()
        self._last_snap_time = time.time()
        self._last_snap_size = 0
        self._tick_duration = 0.5  # 刷新间隔（秒）
        self._finished = False
        # 上一次输出的可见字符长度（用于清除残留）
        self._last_bar_len = 0
        # 进度条线程
        self._progress_thread = None
        self._stop_event = _threading.Event()

    def set_scan_info(self, total_num, total_size):
        """设置扫描结果（文件总数和总大小）"""
        with self._lock:
            self.total_num = total_num
            self.total_size = total_size
            self.scan_end = True

    def update_ok(self, size, file_id=None):
        """更新成功计数
        如果使用了 progress_callback（file_id 不为 None），则不再累加 transfer_size，
        因为已经通过 _update_file_progress 实时更新了。
        """
        with self._lock:
            self.ok_num += 1
            if file_id is not None:
                # 使用了 progress_callback，确保该文件的进度被标记为完成
                already = self._file_progress.pop(file_id, 0)
                # 修正：确保 transfer_size 精确等于文件大小
                delta = size - already
                if delta > 0:
                    self.transfer_size += delta
                self.deal_size += size
            else:
                # 没有使用 progress_callback，直接累加
                self.deal_size += size
                self.transfer_size += size

    def update_skip(self, size):
        """更新跳过计数"""
        with self._lock:
            self.skip_num += 1
            self.deal_size += size
            self.skip_size += size

    def update_err(self, file_id=None, path=None, reason=None,
                   src_path=None, dest_path=None, request_id=None):
        """更新失败计数，可选记录失败路径和原因
        - path: 兼容旧接口，作为 src_path 使用（若 src_path 未指定）
        - src_path: 源路径（本地文件路径或 COS key）
        - dest_path: 目标路径（本地文件路径或 COS key）
        - request_id: SDK 返回的 RequestId
        - reason: 失败原因（SDK 错误信息）
        """
        import datetime
        with self._lock:
            self.err_num += 1
            if file_id is not None:
                self._file_progress.pop(file_id, None)
            record_src = src_path or path or ""
            record_dest = dest_path or ""
            if record_src or reason:
                self._fail_records.append({
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "src_path": record_src,
                    "dest_path": record_dest,
                    "reason": reason or "",
                    "request_id": request_id or "",
                })

    def create_progress_callback(self, file_size):
        """创建一个可以传给 COS SDK 的 progress_callback 函数。
        SDK 会在每个分片上传/下载完成后调用 callback(consumed_bytes, total_bytes)。
        返回 (callback_func, file_id) 元组。
        """
        with self._lock:
            self._file_id_counter += 1
            file_id = self._file_id_counter
            self._file_progress[file_id] = 0

        def _callback(consumed_bytes, total_bytes):
            with self._lock:
                old_consumed = self._file_progress.get(file_id, 0)
                delta = consumed_bytes - old_consumed
                if delta > 0:
                    self.transfer_size += delta
                    self._file_progress[file_id] = consumed_bytes

        return _callback, file_id

    def start(self):
        """启动进度条刷新线程"""
        self._start_time = time.time()
        self._last_snap_time = time.time()
        self._stop_event.clear()
        self._progress_thread = _threading.Thread(target=self._progress_loop, daemon=True)
        self._progress_thread.start()

    def stop(self, log_file=None):
        """停止进度条并输出最终结果，如果指定 log_file 则写入失败日志"""
        self._stop_event.set()
        if self._progress_thread:
            self._progress_thread.join(timeout=2)
        self._print_finish_bar()
        if log_file and self._fail_records:
            self._write_log_file(log_file)

    def _write_log_file(self, log_file):
        """将失败记录写入日志文件（结构化格式，每条记录含时间/源路径/目标路径/错误信息/RequestId）"""
        import datetime
        try:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            elapsed = time.time() - self._start_time
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("# %s 失败日志\n" % self.op_type)
                f.write("# 生成时间: %s\n" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                f.write("# 执行耗时: %.1fs\n" % elapsed)
                f.write("# 失败总数: %d\n" % len(self._fail_records))
                f.write("#\n")
                for i, record in enumerate(self._fail_records, 1):
                    f.write("[%d]\n" % i)
                    f.write("  Time      : %s\n" % record.get("time", ""))
                    f.write("  Source    : %s\n" % record.get("src_path", ""))
                    if record.get("dest_path"):
                        f.write("  Dest      : %s\n" % record["dest_path"])
                    f.write("  Reason    : %s\n" % record.get("reason", ""))
                    if record.get("request_id"):
                        f.write("  RequestId : %s\n" % record["request_id"])
                    f.write("\n")
            sys.stderr.write("失败日志已写入: %s\n" % log_file)
            sys.stderr.flush()
        except Exception as e:
            sys.stderr.write("写入失败日志出错: %s\n" % str(e))
            sys.stderr.flush()

    def _progress_loop(self):
        """进度条刷新循环"""
        while not self._stop_event.is_set():
            self._print_progress_bar()
            self._stop_event.wait(self._tick_duration)

    def _print_progress_bar(self):
        """打印实时进度条（覆盖当前行）"""
        with self._lock:
            now = time.time()
            duration = now - self._last_snap_time
            if duration < self._tick_duration:
                return

            increment_size = self.transfer_size - self._last_snap_size
            speed = increment_size / duration if duration > 0 else 0
            self._last_snap_time = now
            self._last_snap_size = self.transfer_size

            deal_num = self.ok_num + self.skip_num + self.err_num
            # 已传输 + 已跳过 = 总进度字节数
            progress_size = self.transfer_size + self.skip_size

            if self.scan_end and self.total_num > 0:
                # 扫描完成，显示百分比
                if self.total_size > 0:
                    percent = min(float(progress_size) * 100.0 / float(self.total_size), 99.9)
                else:
                    percent = min(float(deal_num) * 100.0 / float(self.total_num), 99.9)
                bar = "Total num: %d, size: %s. Processed num: %d(%d ok, %d skip, %d err), " \
                      "OK size: %s, Progress: %.1f%%, Speed: %s/s" % (
                          self.total_num, format_size(self.total_size),
                          deal_num, self.ok_num, self.skip_num, self.err_num,
                          format_size(progress_size),
                          percent, format_size(int(speed)))
            else:
                # 扫描中
                scan_num = max(self.total_num, deal_num)
                bar = "Scanned num: %d. Processed num: %d(%d ok, %d skip, %d err), " \
                      "OK size: %s, Speed: %s/s" % (
                          scan_num,
                          deal_num, self.ok_num, self.skip_num, self.err_num,
                          format_size(progress_size),
                          format_size(int(speed)))

        # 回到行首，写入新内容，用空格覆盖上一次多出的部分
        padding = max(0, self._last_bar_len - len(bar))
        sys.stderr.write("\r" + bar + " " * padding)
        sys.stderr.flush()
        self._last_bar_len = len(bar)

    def _print_finish_bar(self):
        """打印最终完成信息（显示100%）"""
        with self._lock:
            elapsed = time.time() - self._start_time
            avg_speed = self.transfer_size / elapsed if elapsed > 0 else 0
            deal_num = self.ok_num + self.skip_num + self.err_num
            total_done_size = self.transfer_size + self.skip_size

            if self.err_num == 0:
                status = "Succeed"
            else:
                status = "FinishWithError"

            if self.scan_end:
                bar = "%s: Total num: %d, size: %s. OK num: %d" % (
                    status, self.total_num, format_size(self.total_size), self.ok_num)
            else:
                bar = "%s: Scanned num: %d. OK num: %d" % (
                    status, max(self.total_num, deal_num), self.ok_num)

            detail_parts = []
            if self.skip_num > 0:
                detail_parts.append("skip %d" % self.skip_num)
            if self.err_num > 0:
                detail_parts.append("err %d" % self.err_num)
            if detail_parts:
                bar += "(%s)" % ", ".join(detail_parts)

            if self.skip_size > 0:
                bar += ", Skip size: %s" % format_size(self.skip_size)
            bar += ", OK size: %s" % format_size(self.transfer_size)

            # 显示最终进度 100%（如果没有错误）
            if self.err_num == 0 and self.total_num > 0:
                bar += ", Progress: 100.0%"
            elif self.total_size > 0:
                percent = float(total_done_size) * 100.0 / float(self.total_size)
                bar += ", Progress: %.1f%%" % percent

        # 回到行首，写入最终结果，用空格覆盖上一次多出的部分
        padding = max(0, self._last_bar_len - len(bar))
        sys.stderr.write("\r" + bar + " " * padding + "\n")
        sys.stderr.flush()

        # 输出平均速度和总耗时
        if elapsed > 0:
            sys.stderr.write("AvgSpeed: %s/s, Elapsed: %.1fs\n" % (format_size(int(avg_speed)), elapsed))
            sys.stderr.flush()