# tccli cos 插件使用文档

腾讯云 COS（对象存储）命令行工具插件，集成于 `tccli` 中，全量对齐 `coscli` 的命令与参数，提供完整的 COS 文件管理能力。

## 目录

- [全局参数](#全局参数)
- [文件操作](#文件操作)
  - [list - 列出文件](#list---列出文件)
  - [upload - 上传文件](#upload---上传文件)
  - [download - 下载文件](#download---下载文件)
  - [delete - 删除文件](#delete---删除文件)
  - [copy - 复制文件](#copy---复制文件)
  - [move - 移动/重命名文件](#move---移动重命名文件)
  - [cat - 查看文件内容](#cat---查看文件内容)
  - [head - 查询对象元信息](#head---查询对象元信息)
  - [hash - 计算哈希值](#hash---计算哈希值)
- [同步操作](#同步操作)
  - [同步跳过策略](#同步跳过策略)
  - [sync_upload - 同步上传](#sync_upload---同步上传)
  - [sync_download - 同步下载](#sync_download---同步下载)
  - [sync_copy - 同步复制](#sync_copy---同步复制)
- [存储桶操作](#存储桶操作)
  - [list_buckets - 列出存储桶](#list_buckets---列出存储桶)
  - [create_bucket - 创建存储桶](#create_bucket---创建存储桶)
  - [delete_bucket - 删除存储桶](#delete_bucket---删除存储桶)
- [统计操作](#统计操作)
  - [du - 统计大小](#du---统计大小)
- [归档恢复](#归档恢复)
  - [restore - 恢复归档文件](#restore---恢复归档文件)
- [预签名 URL](#预签名-url)
  - [signurl - 生成预签名URL](#signurl---生成预签名url)
- [ACL 权限管理](#acl-权限管理)
  - [get_bucket_acl - 获取存储桶ACL](#get_bucket_acl---获取存储桶acl)
  - [put_bucket_acl - 设置存储桶ACL](#put_bucket_acl---设置存储桶acl)
  - [get_object_acl - 获取对象ACL](#get_object_acl---获取对象acl)
  - [put_object_acl - 设置对象ACL](#put_object_acl---设置对象acl)
- [标签管理](#标签管理)
  - [get_object_tagging - 获取对象标签](#get_object_tagging---获取对象标签)
  - [put_object_tagging - 设置对象标签](#put_object_tagging---设置对象标签)
  - [add_object_tagging - 追加对象标签](#add_object_tagging---追加对象标签)
  - [delete_object_tagging - 删除对象标签](#delete_object_tagging---删除对象标签)
- [对象软链接](#对象软链接)
  - [create_symlink - 创建对象软链接](#create_symlink---创建对象软链接)
  - [get_symlink - 查询对象软链接](#get_symlink---查询对象软链接)
- [存储桶清单](#存储桶清单)
  - [put_bucket_inventory - 创建/更新清单](#put_bucket_inventory---创建更新清单)
  - [get_bucket_inventory - 查询清单](#get_bucket_inventory---查询清单)
  - [list_bucket_inventory - 列出清单任务](#list_bucket_inventory---列出清单任务)
  - [delete_bucket_inventory - 删除清单任务](#delete_bucket_inventory---删除清单任务)
  - [post_bucket_inventory - 一次性清单](#post_bucket_inventory---一次性清单)
- [分片上传管理](#分片上传管理)
  - [lsparts - 列出分片上传](#lsparts---列出分片上传)
  - [abort - 清理分片上传](#abort---清理分片上传)
- [附录](#附录)
  - [coscli 参数对齐速查表](#coscli-参数对齐速查表)
  - [存储类型说明](#存储类型说明)
  - [失败日志格式](#失败日志格式)

---

## 全局参数

所有命令均支持以下全局参数（通过 `tccli` 统一配置）：

| 参数 | 说明 |
|------|------|
| `--region` | 地域，如 `ap-guangzhou`、`ap-beijing` |
| `--secretId` | 腾讯云 SecretId |
| `--secretKey` | 腾讯云 SecretKey |
| `--token` | 腾讯云临时 Token（可选） |
| `--profile` | 使用指定的 tccli 配置文件 |

凭据优先级：**命令行参数 > 环境变量（`TENCENTCLOUD_SECRET_ID/KEY/TOKEN/REGION`）> tccli 配置文件（`~/.tccli/<profile>.credential`）**。

---

## 文件操作

### list - 列出文件

列出 COS 存储桶中的文件，默认只列出当前层级（非递归），支持按前缀过滤和 include/exclude 过滤。

**命令格式：**
```bash
tccli cos list [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称，格式如 `my-bucket-1250000000` |
| `--prefix` | string | ❌ | 空 | 对象键前缀，用于过滤列出的对象 |
| `--marker` | string | ❌ | 空 | 分页标记，从该标记之后开始列出 |
| `--max_keys` | int | ❌ | 1000 | 最大返回数量（单次请求），最大 1000 |
| `--delimiter` | string | ❌ | `/` | 分隔符，默认 `/` 模拟目录结构 |
| `--recursive` | bool | ❌ | false | 是否递归列出所有对象（忽略 delimiter） |
| `--include` | string | ❌ | 空 | 包含匹配模式，支持通配符，如 `*.txt` |
| `--exclude` | string | ❌ | 空 | 排除匹配模式，支持通配符，如 `*.log` |
| `--all_versions` | bool | ❌ | false | 列出对象的所有历史版本。对齐 coscli `ls --all-versions` |
| `--limit` | int | ❌ | 0 | 列出对象数量上限，0 表示不限。对齐 coscli `ls --limit` |

**示例：**
```bash
# 列出存储桶根目录（只显示当前层级）
tccli cos list --bucket my-bucket-1250000000

# 列出指定前缀下的所有文件（递归）
tccli cos list --bucket my-bucket-1250000000 --prefix data/ --recursive true

# 只列出 txt 文件
tccli cos list --bucket my-bucket-1250000000 --prefix logs/ --recursive true --include "*.txt"

# 限制只显示 50 条
tccli cos list --bucket my-bucket-1250000000 --recursive true --limit 50

# 列出所有历史版本
tccli cos list --bucket my-bucket-1250000000 --prefix data/ --all_versions true
```

---

### upload - 上传文件

上传本地文件或目录到 COS，自动根据文件大小选择简单上传或分片上传（默认分片阈值 20MB）。上传后自动进行 CRC64 校验（可通过 `--disable_crc64` 关闭）。

**命令格式：**
```bash
tccli cos upload [参数]
```

**基础参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 目标存储桶名称 |
| `--local_path` | string | ✅ | - | 本地文件或目录路径 |
| `--cos_key` | string | ✅ | - | COS 上的目标对象键（Key），递归上传时作为前缀 |
| `--recursive` | bool | ❌ | false | 是否递归上传目录 |
| `--include` | string | ❌ | 空 | 包含匹配模式（递归时生效），支持通配符 |
| `--exclude` | string | ❌ | 空 | 排除匹配模式（递归时生效），支持通配符 |
| `--only_current_dir` | bool | ❌ | false | 仅上传当前目录下的文件，不递归子目录。对齐 coscli `--only-current-dir` |
| `--skip_dir` | bool | ❌ | false | 不上传空目录标记（`/` 结尾对象）。对齐 coscli `--skip-dir` |
| `--disable_all_symlink` | bool | ❌ | false | 不上传任何符号链接（文件和目录）。对齐 coscli `--disable-all-symlink` |
| `--enable_symlink_dir` | bool | ❌ | false | 允许跟随符号链接目录。对齐 coscli `--enable-symlink-dir` |

**对象属性参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--storage_class` | string | ❌ | STANDARD | 存储类型，见[存储类型说明](#存储类型说明) |
| `--content_type` | string | ❌ | 空 | 文件内容类型（MIME），如 `text/plain` |
| `--meta` | string | ❌ | 空 | 自定义元数据，格式：`key1=value1#key2=value2` |
| `--acl` | string | ❌ | 空 | 对象 ACL，可选：`default` / `private` / `public-read` / `public-read-write` / `authenticated-read` / `bucket-owner-read` / `bucket-owner-full-control` |
| `--grant_read` | string | ❌ | 空 | 授予读权限，格式：`id="账号ID"` |
| `--grant_read_acp` | string | ❌ | 空 | 授予读 ACP 权限，格式：`id="账号ID"` |
| `--grant_write_acp` | string | ❌ | 空 | 授予写 ACP 权限，格式：`id="账号ID"` |
| `--grant_full_control` | string | ❌ | 空 | 授予完全控制权限，格式：`id="账号ID"` |
| `--tags` | string | ❌ | 空 | 对象标签，格式：`key1=value1&key2=value2` |
| `--forbid_overwrite` | bool | ❌ | false | 禁止覆盖同名对象（需服务端支持）。对齐 coscli `--forbid-overwrite` |
| `--encryption_type` | string | ❌ | 空 | 服务端加密类型：`AES256`（SSE-COS）或 `cos/kms`（SSE-KMS） |
| `--sse_customer_algorithm` | string | ❌ | 空 | SSE-C 加密算法，固定为 `AES256` |
| `--sse_customer_key` | string | ❌ | 空 | SSE-C 加密密钥（32 字节） |
| `--sse_customer_key_md5` | string | ❌ | 空 | SSE-C 加密密钥的 MD5 |

**性能 / 重试 / 校验参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--thread_num` | int | ❌ | 5 | 单文件分片上传并发线程数 |
| `--routines` | int | ❌ | 3 | 文件间并发数（同时传输的文件数） |
| `--part_size` | int | ❌ | 20 | 分片大小（MB） |
| `--rate_limiting` | int | ❌ | 0 | 单链接限速（MB/s），0 表示不限速 |
| `--retry` | int | ❌ | 3 | 失败重试次数，0 表示不重试 |
| `--err_retry_num` | int | ❌ | 0 | 可重试错误（超时 / 5xx / 429）的额外重试次数。对齐 coscli `--err-retry-num` |
| `--err_retry_interval` | int | ❌ | 0 | 可重试错误的重试间隔（秒），0 表示立即重试。对齐 coscli `--err-retry-interval` |
| `--disable_crc64` | bool | ❌ | false | 关闭上传后 CRC64 校验。对齐 coscli `--disable-crc64` |

**日志参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--log_file` | string | ❌ | 空 | 失败日志文件路径 |
| `--fail_output` | bool | ❌ | false | 启用失败日志输出（需配合 `--fail_output_path`）。对齐 coscli `--fail-output` |
| `--fail_output_path` | string | ❌ | 空 | 失败日志输出路径。对齐 coscli `--fail-output-path` |

> 说明：`--log_file` 与 `--fail_output_path` 任意一个指定即可启用失败日志写入，两者指向相同的格式（见[失败日志格式](#失败日志格式)）。

**目录上传行为说明：**
- `local_path` 以 `/` 结尾（如 `/tmp/dir/`）：不保留目录名，直接映射内容到 `cos_key` 前缀下
- `local_path` 不以 `/` 结尾（如 `/tmp/dir`）：保留目录名，映射为 `cos_key/dir/` 前缀下

**示例：**
```bash
# 上传单个文件
tccli cos upload --bucket my-bucket-1250000000 --local_path /tmp/test.txt --cos_key data/test.txt

# 上传目录（保留目录名）
tccli cos upload --bucket my-bucket-1250000000 --local_path /tmp/mydir --cos_key backup/ --recursive true

# 上传目录（不保留目录名，直接映射内容）
tccli cos upload --bucket my-bucket-1250000000 --local_path /tmp/mydir/ --cos_key backup/ --recursive true

# 仅上传当前目录层（不递归子目录）
tccli cos upload --bucket my-bucket-1250000000 --local_path /tmp/mydir/ --cos_key top/ \
  --recursive true --only_current_dir true

# 只上传 jpg 图片，使用低频存储，限速 10MB/s
tccli cos upload --bucket my-bucket-1250000000 --local_path /tmp/photos --cos_key images/ \
  --recursive true --include "*.jpg" --storage_class STANDARD_IA --rate_limiting 10

# 上传时设置自定义元数据和标签
tccli cos upload --bucket my-bucket-1250000000 --local_path /tmp/test.txt --cos_key data/test.txt \
  --meta "author=panwei#env=prod" --tags "owner=team1&version=v1"

# 上传时设置 ACL 和 SSE 加密
tccli cos upload --bucket my-bucket-1250000000 --local_path /tmp/test.txt --cos_key data/test.txt \
  --acl private --encryption_type AES256

# 禁止覆盖同名对象
tccli cos upload --bucket my-bucket-1250000000 --local_path /tmp/test.txt --cos_key data/test.txt \
  --forbid_overwrite true

# 上传并记录失败日志
tccli cos upload --bucket my-bucket-1250000000 --local_path /tmp/data --cos_key data/ \
  --recursive true --retry 5 --err_retry_num 2 --err_retry_interval 3 --log_file /tmp/upload_fail.log
```

---

### download - 下载文件

从 COS 下载文件到本地，自动根据文件大小选择简单下载或分片下载。下载后自动进行 CRC64 校验（可通过 `--disable_crc64` 关闭）。

**命令格式：**
```bash
tccli cos download [参数]
```

**基础参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 源存储桶名称 |
| `--cos_key` | string | ✅ | - | COS 上的源对象键（Key），递归下载时作为前缀 |
| `--local_path` | string | ✅ | - | 本地保存路径，递归下载时为目标目录 |
| `--recursive` | bool | ❌ | false | 是否递归下载前缀下所有对象 |
| `--include` | string | ❌ | 空 | 包含匹配模式（递归时生效），支持通配符 |
| `--exclude` | string | ❌ | 空 | 排除匹配模式（递归时生效），支持通配符 |
| `--only_current_dir` | bool | ❌ | false | 仅下载当前目录下的对象，不递归。对齐 coscli `--only-current-dir` |
| `--version_id` | string | ❌ | 空 | 指定下载的对象版本 ID（开启版本控制时使用） |
| `--forbid_overwrite` | bool | ❌ | false | 禁止覆盖本地已存在文件 |

**SSE-C 参数（若源对象使用 SSE-C 加密）：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--sse_customer_algorithm` | string | ❌ | 空 | SSE-C 加密算法，固定为 `AES256` |
| `--sse_customer_key` | string | ❌ | 空 | SSE-C 加密密钥 |
| `--sse_customer_key_md5` | string | ❌ | 空 | SSE-C 加密密钥的 MD5 |

**性能 / 重试 / 校验参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--thread_num` | int | ❌ | 5 | 单文件分片下载并发线程数 |
| `--routines` | int | ❌ | 3 | 文件间并发数（同时下载的文件数） |
| `--part_size` | int | ❌ | 20 | 分片大小（MB） |
| `--rate_limiting` | int | ❌ | 0 | 单链接限速（MB/s），0 表示不限速 |
| `--retry` | int | ❌ | 3 | 失败重试次数，0 表示不重试 |
| `--err_retry_num` | int | ❌ | 0 | 可重试错误的额外重试次数。对齐 coscli `--err-retry-num` |
| `--err_retry_interval` | int | ❌ | 0 | 可重试错误的重试间隔（秒）。对齐 coscli `--err-retry-interval` |
| `--disable_crc64` | bool | ❌ | false | 关闭下载后 CRC64 校验。对齐 coscli `--disable-crc64` |

**日志参数：** `--log_file` / `--fail_output` / `--fail_output_path`，同 [upload](#upload---上传文件)。

**示例：**
```bash
# 下载单个文件
tccli cos download --bucket my-bucket-1250000000 --cos_key data/test.txt --local_path /tmp/test.txt

# 递归下载整个目录
tccli cos download --bucket my-bucket-1250000000 --cos_key data/ --local_path /tmp/data --recursive true

# 仅下载当前目录层（不递归子目录）
tccli cos download --bucket my-bucket-1250000000 --cos_key data/ --local_path /tmp/data \
  --recursive true --only_current_dir true

# 只下载 txt 文件，限速 5MB/s
tccli cos download --bucket my-bucket-1250000000 --cos_key logs/ --local_path /tmp/logs \
  --recursive true --include "*.txt" --rate_limiting 5

# 下载指定版本的文件
tccli cos download --bucket my-bucket-1250000000 --cos_key data/test.txt \
  --local_path /tmp/test.txt --version_id MTg0NDUxNTc1NjIzMTQ1MDAwODg

# 禁止覆盖本地已存在文件
tccli cos download --bucket my-bucket-1250000000 --cos_key data/test.txt --local_path /tmp/test.txt \
  --forbid_overwrite true

# 关闭 CRC64 校验（大文件下载性能敏感场景）
tccli cos download --bucket my-bucket-1250000000 --cos_key big.bin --local_path /tmp/big.bin \
  --disable_crc64 true
```

---

### delete - 删除文件

删除 COS 存储桶中的指定文件，支持递归批量删除。

**命令格式：**
```bash
tccli cos delete [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--cos_key` | string | ✅ | - | 要删除的对象键（Key），递归删除时作为前缀 |
| `--recursive` | bool | ❌ | false | 是否递归删除前缀下所有对象 |
| `--force` | bool | ❌ | false | 递归删除时跳过确认提示 |
| `--include` | string | ❌ | 空 | 包含匹配模式（递归时生效），支持通配符 |
| `--exclude` | string | ❌ | 空 | 排除匹配模式（递归时生效），支持通配符 |
| `--version_id` | string | ❌ | 空 | 指定删除的对象版本 ID（开启版本控制时使用） |

> ⚠️ 递归删除时，默认会提示确认，使用 `--force true` 可跳过确认。

**示例：**
```bash
# 删除单个文件
tccli cos delete --bucket my-bucket-1250000000 --cos_key data/test.txt

# 递归删除目录（会提示确认）
tccli cos delete --bucket my-bucket-1250000000 --cos_key data/ --recursive true

# 递归删除目录（跳过确认）
tccli cos delete --bucket my-bucket-1250000000 --cos_key data/ --recursive true --force true

# 只删除 log 文件
tccli cos delete --bucket my-bucket-1250000000 --cos_key logs/ --recursive true --force true --include "*.log"

# 删除指定版本的文件
tccli cos delete --bucket my-bucket-1250000000 --cos_key data/test.txt --version_id MTg0NDUxNTc1NjIzMTQ1MDAwODg
```

---

### copy - 复制文件

复制 COS 上的文件到另一个位置，支持跨存储桶和跨地域复制，支持并发和失败重试。指定 `--meta` / `--tags` 时使用 Replaced 模式（覆盖源对象对应字段），否则继承源对象。

**命令格式：**
```bash
tccli cos copy [参数]
```

**基础参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 源存储桶名称 |
| `--cos_key` | string | ✅ | - | 源对象键（Key），递归复制时作为前缀 |
| `--dest_key` | string | ✅ | - | 目标对象键（Key），递归复制时作为目标前缀 |
| `--dest_bucket` | string | ❌ | 同源桶 | 目标存储桶名称 |
| `--dest_region` | string | ❌ | 当前地域 | 目标地域 |
| `--recursive` | bool | ❌ | false | 是否递归复制前缀下所有对象 |
| `--include` | string | ❌ | 空 | 包含匹配模式（递归时生效），支持通配符 |
| `--exclude` | string | ❌ | 空 | 排除匹配模式（递归时生效），支持通配符 |
| `--only_current_dir` | bool | ❌ | false | 仅复制当前目录下的对象，不递归 |
| `--skip_dir` | bool | ❌ | false | 不复制空目录标记 |
| `--version_id` | string | ❌ | 空 | 指定复制源对象的版本 ID（单文件复制时生效） |

**目标对象属性参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--storage_class` | string | ❌ | 空 | 目标存储类型，见[存储类型说明](#存储类型说明) |
| `--meta` | string | ❌ | 空 | 自定义元数据，格式：`key1=value1#key2=value2`（设置后使用 Replaced 模式） |
| `--acl` | string | ❌ | 空 | 目标对象 ACL |
| `--grant_read` | string | ❌ | 空 | 授予读权限，格式：`id="账号ID"` |
| `--grant_read_acp` | string | ❌ | 空 | 授予读 ACP 权限 |
| `--grant_write_acp` | string | ❌ | 空 | 授予写 ACP 权限 |
| `--grant_full_control` | string | ❌ | 空 | 授予完全控制权限 |
| `--tags` | string | ❌ | 空 | 目标对象标签，格式：`key1=value1&key2=value2`（设置后使用 Replaced 模式） |
| `--forbid_overwrite` | bool | ❌ | false | 禁止覆盖目标已存在对象 |
| `--encryption_type` | string | ❌ | 空 | 目标对象服务端加密类型：`AES256` / `cos/kms` |

**性能 / 重试 / 日志参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--routines` | int | ❌ | 3 | 文件间并发数 |
| `--retry` | int | ❌ | 3 | 失败重试次数 |
| `--err_retry_num` | int | ❌ | 0 | 可重试错误的额外重试次数 |
| `--err_retry_interval` | int | ❌ | 0 | 可重试错误的重试间隔（秒） |
| `--log_file` | string | ❌ | 空 | 失败日志文件路径 |
| `--fail_output` | bool | ❌ | false | 启用失败日志输出 |
| `--fail_output_path` | string | ❌ | 空 | 失败日志输出路径 |

**示例：**
```bash
# 同桶内复制单个文件
tccli cos copy --bucket my-bucket-1250000000 --cos_key data/test.txt --dest_key backup/test.txt

# 跨存储桶复制
tccli cos copy --bucket src-bucket-1250000000 --cos_key data/test.txt \
  --dest_bucket dst-bucket-1250000000 --dest_key data/test.txt

# 跨地域复制整个目录
tccli cos copy --bucket src-bucket-1250000000 --cos_key data/ \
  --dest_bucket dst-bucket-1250000000 --dest_key data/ \
  --dest_region ap-beijing --recursive true

# 复制时修改元数据（Replaced 模式）
tccli cos copy --bucket my-bucket-1250000000 --cos_key data/src.txt --dest_key data/dst.txt \
  --meta "env=prod#version=v2"

# 复制时修改标签（Replaced 模式）
tccli cos copy --bucket my-bucket-1250000000 --cos_key data/src.txt --dest_key data/dst.txt \
  --tags "owner=team2&status=archived"

# 复制并修改存储类型
tccli cos copy --bucket my-bucket-1250000000 --cos_key data/ --dest_key archive/ \
  --recursive true --storage_class ARCHIVE
```

---

### move - 移动/重命名文件

移动或重命名 COS 上的文件（通过复制 + 删除实现），支持跨存储桶移动，支持并发和失败重试。

**命令格式：**
```bash
tccli cos move [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 源存储桶名称 |
| `--cos_key` | string | ✅ | - | 源对象键（Key），递归移动时作为前缀 |
| `--dest_key` | string | ✅ | - | 目标对象键（Key），递归移动时作为目标前缀 |
| `--dest_bucket` | string | ❌ | 同源桶 | 目标存储桶名称 |
| `--dest_region` | string | ❌ | 当前地域 | 目标地域 |
| `--storage_class` | string | ❌ | 空 | 目标存储类型 |
| `--recursive` | bool | ❌ | false | 是否递归移动前缀下所有对象 |
| `--include` | string | ❌ | 空 | 包含匹配模式（递归时生效），支持通配符 |
| `--exclude` | string | ❌ | 空 | 排除匹配模式（递归时生效），支持通配符 |
| `--routines` | int | ❌ | 3 | 文件间并发数 |
| `--retry` | int | ❌ | 3 | 失败重试次数 |
| `--log_file` | string | ❌ | 空 | 失败日志文件路径 |

**示例：**
```bash
# 重命名单个文件
tccli cos move --bucket my-bucket-1250000000 --cos_key data/old.txt --dest_key data/new.txt

# 移动整个目录
tccli cos move --bucket my-bucket-1250000000 --cos_key data/ --dest_key archive/ --recursive true

# 跨存储桶移动
tccli cos move --bucket src-bucket-1250000000 --cos_key data/ \
  --dest_bucket dst-bucket-1250000000 --dest_key data/ --recursive true
```

---

### cat - 查看文件内容

查看 COS 对象的文本内容，默认最大读取 10MB，支持指定字节范围读取。

**命令格式：**
```bash
tccli cos cat [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--cos_key` | string | ✅ | - | 对象键（Key） |
| `--range` | string | ❌ | 空 | 指定读取范围，格式：`bytes=0-1023` |
| `--max_size` | int | ❌ | 10 | 最大读取大小（MB），超过此大小仅显示部分内容 |

**示例：**
```bash
# 查看文件内容
tccli cos cat --bucket my-bucket-1250000000 --cos_key logs/app.log

# 查看文件的前 1KB
tccli cos cat --bucket my-bucket-1250000000 --cos_key logs/app.log --range "bytes=0-1023"

# 查看大文件（最多显示 50MB）
tccli cos cat --bucket my-bucket-1250000000 --cos_key data/large.txt --max_size 50
```

---

### head - 查询对象元信息

查询 COS 对象的元数据信息，包括大小、类型、修改时间、ETag、CRC64、自定义元数据等。

**命令格式：**
```bash
tccli cos head [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--cos_key` | string | ✅ | - | 要查询的对象键（Key） |
| `--version_id` | string | ❌ | 空 | 指定查询的对象版本 ID（开启版本控制时使用） |

**示例：**
```bash
# 查询对象元信息
tccli cos head --bucket my-bucket-1250000000 --cos_key data/test.txt

# 查询指定版本的元信息
tccli cos head --bucket my-bucket-1250000000 --cos_key data/test.txt --version_id MTg0NDUxNTc1NjIzMTQ1MDAwODg
```

**输出示例：**
```
对象元信息: cos://my-bucket-1250000000/data/test.txt
--------------------------------------------------
Content-Length:  1024
Content-Type:    text/plain
ETag:            "d41d8cd98f00b204e9800998ecf8427e"
Last-Modified:   Mon, 07 Apr 2025 10:00:00 GMT
Storage-Class:   STANDARD
CRC64:           1234567890123456789
Version-Id:      MTg0NDUxNTc1NjIzMTQ1MDAwODg
x-cos-meta-author: panwei
x-cos-meta-env:  prod
```

---

### hash - 计算哈希值

计算本地文件的哈希值，或获取 COS 对象的 ETag / CRC64 信息。**本地模式（仅 `--local_path`）不需要 COS 凭据**。

**命令格式：**
```bash
tccli cos hash [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--local_path` | string | ❌ | 空 | 本地文件路径（计算本地文件哈希时使用） |
| `--bucket` | string | ❌ | 空 | 存储桶名称（获取 COS 对象哈希时使用） |
| `--cos_key` | string | ❌ | 空 | 对象键（获取 COS 对象哈希时使用） |
| `--hash_type` | string | ❌ | md5 | 哈希类型：`md5`、`sha1`、`sha256`、`crc64` |

> 注意：`--local_path` 和 `--bucket + --cos_key` 至少指定一组，也可同时指定两组进行对比。

**示例：**
```bash
# 计算本地文件 MD5
tccli cos hash --local_path /tmp/test.txt

# 计算本地文件 CRC64（与 COS 保持一致）
tccli cos hash --local_path /tmp/test.txt --hash_type crc64

# 计算本地文件 SHA256
tccli cos hash --local_path /tmp/test.txt --hash_type sha256

# 获取 COS 对象的 ETag 和 CRC64
tccli cos hash --bucket my-bucket-1250000000 --cos_key data/test.txt

# 同时计算本地和 COS 对象的哈希（用于校验一致性）
tccli cos hash --local_path /tmp/test.txt --bucket my-bucket-1250000000 --cos_key data/test.txt
```

---

## 同步操作

### 同步跳过策略

三个 sync 命令（`sync_upload` / `sync_download` / `sync_copy`）全量对齐 **coscli sync** 的跳过逻辑。判定优先级从高到低：

1. **`--ignore_existing true`**：目标已存在即跳过，不做任何内容比较
2. **`--update true`**：按 `Last-Modified` 时间比较，目标 ≥ 源 时跳过（只向新版本推送）
3. **`--snapshot_path <path>`**（仅 `sync_upload` / `sync_download`）：使用本地 SQLite 快照库记录文件的 `(mtime, size, crc64)`，命中且内容未变时快速跳过（**无需发起 `HEAD` 请求**），极大加速大目录的增量判断
4. **默认**：**CRC64 校验** —— 对比 COS `x-cos-hash-crc64ecma` 与本地/目标 CRC64，相同则跳过

> 目标不存在时，一律不跳过；`--ignore_existing` 与 `--update` 互斥，`--ignore_existing` 优先。

**对齐 coscli 的公共参数：**

| 参数 | 说明 |
|---|---|
| `--delete` / `--delete_extra` | 两者等价，镜像同步（删除目标端多余文件） |
| `--backup_dir <dir>` | 删除多余文件前先备份到本地目录（sync_upload 备份远端对象到本地；sync_download 备份本地文件到本地） |
| `--force` | 跳过交互确认（当前 sync 无交互，保留作兼容） |
| `--only_current_dir` | 仅同步当前目录层，不递归 |
| `--skip_dir` | 不同步空目录标记 |
| `--ignore_empty_file` | 忽略 0 字节文件 / 空对象 |

---

### sync_upload - 同步上传

同步本地目录到 COS，增量上传，支持删除 COS 上多余的文件。

**命令格式：**
```bash
tccli cos sync_upload [参数]
```

**基础 / 过滤参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 目标存储桶名称 |
| `--local_path` | string | ✅ | - | 本地文件或目录路径 |
| `--cos_key` | string | ❌ | 空 | COS 上的目标前缀 |
| `--recursive` | bool | ❌ | false | 是否递归同步目录 |
| `--include` | string | ❌ | 空 | 包含匹配模式，支持通配符 |
| `--exclude` | string | ❌ | 空 | 排除匹配模式，支持通配符 |
| `--only_current_dir` | bool | ❌ | false | 仅同步当前目录下的文件，不递归 |
| `--skip_dir` | bool | ❌ | false | 不创建空目录标记 |
| `--ignore_empty_file` | bool | ❌ | false | 忽略空文件（0 字节）。对齐 coscli `--ignore-empty-file` |
| `--disable_all_symlink` | bool | ❌ | false | 禁用所有符号链接 |
| `--enable_symlink_dir` | bool | ❌ | false | 允许跟随符号链接目录 |

**跳过策略参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--ignore_existing` | bool | ❌ | false | 目标已存在即跳过（优先级最高） |
| `--update` | bool | ❌ | false | 仅源文件更新（Last-Modified 更新）时才上传 |
| `--snapshot_path` | string | ❌ | 空 | SQLite 快照数据库文件路径。对齐 coscli `--snapshot-path` |

**删除多余参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--delete_extra` | bool | ❌ | false | 删除 COS 上多余文件（本地不存在的） |
| `--delete` | bool | ❌ | false | 同 `--delete_extra`，对齐 coscli `--delete` |
| `--backup_dir` | string | ❌ | 空 | 删除多余文件前先下载备份到该目录 |
| `--force` | bool | ❌ | false | 跳过确认提示 |

**对象属性参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--storage_class` | string | ❌ | STANDARD | 上传时的存储类型 |
| `--content_type` | string | ❌ | 空 | 文件内容类型（MIME） |
| `--meta` | string | ❌ | 空 | 自定义元数据，格式：`key1=value1#key2=value2` |
| `--acl` | string | ❌ | 空 | 对象 ACL |
| `--grant_read` / `--grant_read_acp` / `--grant_write_acp` / `--grant_full_control` | string | ❌ | 空 | 授权，格式：`id="账号ID"` |
| `--tags` | string | ❌ | 空 | 对象标签，格式：`k1=v1&k2=v2` |
| `--forbid_overwrite` | bool | ❌ | false | 禁止覆盖同名对象 |
| `--encryption_type` | string | ❌ | 空 | 服务端加密类型：`AES256` / `cos/kms` |
| `--sse_customer_algorithm` / `--sse_customer_key` / `--sse_customer_key_md5` | string | ❌ | 空 | SSE-C 参数 |

**性能 / 重试 / 日志参数：**

同 [upload](#upload---上传文件)：`--thread_num` / `--routines` / `--part_size` / `--rate_limiting` / `--retry` / `--err_retry_num` / `--err_retry_interval` / `--disable_crc64` / `--log_file` / `--fail_output` / `--fail_output_path`。

**示例：**
```bash
# 同步本地目录到 COS（默认 CRC64 校验跳过）
tccli cos sync_upload --bucket my-bucket-1250000000 --local_path /data/backup --cos_key backup/ --recursive true

# 使用 snapshot 快照加速增量判断
tccli cos sync_upload --bucket my-bucket-1250000000 --local_path /data/backup --cos_key backup/ \
  --recursive true --snapshot_path /data/.snapshot.db

# 目标存在就跳过（最快的增量同步）
tccli cos sync_upload --bucket my-bucket-1250000000 --local_path /data/backup --cos_key backup/ \
  --recursive true --ignore_existing true

# 只向新版本推送（按 Last-Modified）
tccli cos sync_upload --bucket my-bucket-1250000000 --local_path /data/backup --cos_key backup/ \
  --recursive true --update true

# 镜像同步（删除 COS 上多余的文件）
tccli cos sync_upload --bucket my-bucket-1250000000 --local_path /data/backup --cos_key backup/ \
  --recursive true --delete true

# 镜像同步 + 删除前先备份远端多余对象到本地
tccli cos sync_upload --bucket my-bucket-1250000000 --local_path /data/backup --cos_key backup/ \
  --recursive true --delete true --backup_dir /data/.cos_backup

# 同步并记录失败日志
tccli cos sync_upload --bucket my-bucket-1250000000 --local_path /data --cos_key data/ \
  --recursive true --retry 5 --log_file /tmp/sync_fail.log
```

---

### sync_download - 同步下载

同步 COS 到本地目录，增量下载，支持删除本地多余的文件。

**命令格式：**
```bash
tccli cos sync_download [参数]
```

**基础 / 过滤 / 跳过 / 删除参数：**

与 `sync_upload` 基本对称，区别：
- 无 `--storage_class` / `--content_type` / `--meta` / `--acl` / `--grant_*` / `--tags` / `--encryption_type`（下载侧不需要）
- 保留 `--sse_customer_algorithm` / `--sse_customer_key` / `--sse_customer_key_md5`（源端 SSE-C 解密）
- `--forbid_overwrite` 语义改为：本地文件已存在即跳过（不覆盖）
- `--backup_dir`：删除本地多余文件前先备份到该目录

完整参数列表：

| 参数 | 类型 | 说明 |
|---|---|---|
| `--bucket` / `--local_path` | string | 必填 |
| `--cos_key` | string | COS 源前缀 |
| `--recursive` | bool | 是否递归 |
| `--ignore_existing` / `--update` / `--snapshot_path` | bool/string | 跳过策略 |
| `--delete_extra` / `--delete` / `--backup_dir` / `--force` | bool/string | 删除多余 |
| `--include` / `--exclude` | string | 过滤 |
| `--only_current_dir` / `--ignore_empty_file` | bool | 对齐 coscli |
| `--forbid_overwrite` | bool | 本地存在则跳过 |
| `--sse_customer_algorithm` / `--sse_customer_key` / `--sse_customer_key_md5` | string | SSE-C |
| `--thread_num` / `--routines` / `--part_size` / `--rate_limiting` | int | 性能 |
| `--retry` / `--err_retry_num` / `--err_retry_interval` / `--disable_crc64` | int/bool | 重试 / 校验 |
| `--log_file` / `--fail_output` / `--fail_output_path` | string/bool | 失败日志 |

**示例：**
```bash
# 同步 COS 目录到本地（增量下载）
tccli cos sync_download --bucket my-bucket-1250000000 --cos_key data/ --local_path /tmp/data --recursive true

# 镜像同步（删除本地多余的文件）
tccli cos sync_download --bucket my-bucket-1250000000 --cos_key data/ --local_path /tmp/data \
  --recursive true --delete true

# 使用快照加速
tccli cos sync_download --bucket my-bucket-1250000000 --cos_key data/ --local_path /tmp/data \
  --recursive true --snapshot_path /tmp/data/.snapshot.db

# 按 Last-Modified 比较
tccli cos sync_download --bucket my-bucket-1250000000 --cos_key data/ --local_path /tmp/data \
  --recursive true --update true

# 只同步图片文件
tccli cos sync_download --bucket my-bucket-1250000000 --cos_key images/ --local_path /tmp/images \
  --recursive true --include "*.jpg" --include "*.png"
```

---

### sync_copy - 同步复制

同步 COS 到另一个 COS 位置，增量复制，支持删除目标端多余的文件。**sync_copy 不支持 `--snapshot_path`**（快照仅适用于本地端）。

**命令格式：**
```bash
tccli cos sync_copy [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 源存储桶名称 |
| `--cos_key` | string | ❌ | 空 | 源 COS 前缀 |
| `--dest_bucket` | string | ❌ | 同源桶 | 目标存储桶名称 |
| `--dest_key` | string | ❌ | 空 | 目标 COS 前缀 |
| `--dest_region` | string | ❌ | 当前地域 | 目标地域 |
| `--recursive` | bool | ❌ | false | 是否递归同步复制 |
| `--include` / `--exclude` | string | ❌ | 空 | 过滤 |
| `--only_current_dir` / `--skip_dir` / `--ignore_empty_file` | bool | ❌ | false | 同 sync_upload |
| `--ignore_existing` / `--update` | bool | ❌ | false | 跳过策略（无 snapshot） |
| `--delete_extra` / `--delete` / `--force` | bool | ❌ | false | 删除多余文件 |
| `--storage_class` / `--meta` / `--acl` / `--grant_*` / `--tags` / `--forbid_overwrite` / `--encryption_type` | - | ❌ | - | 目标对象属性，同 copy |
| `--routines` | int | ❌ | 3 | 文件间并发数 |
| `--retry` / `--err_retry_num` / `--err_retry_interval` | int | ❌ | 3/0/0 | 失败重试 |
| `--log_file` / `--fail_output` / `--fail_output_path` | string/bool | ❌ | - | 失败日志 |

**示例：**
```bash
# 同桶不同前缀同步复制
tccli cos sync_copy --bucket my-bucket-1250000000 --cos_key data/ --dest_key backup/ --recursive true

# 跨桶镜像同步复制
tccli cos sync_copy --bucket src-bucket-1250000000 --cos_key data/ \
  --dest_bucket dst-bucket-1250000000 --dest_key data/ \
  --recursive true --delete true

# 跨地域同步复制
tccli cos sync_copy --bucket src-bucket-1250000000 --cos_key data/ \
  --dest_bucket dst-bucket-1250000000 --dest_key data/ \
  --dest_region ap-beijing --recursive true

# 同步复制时修改存储类型和标签
tccli cos sync_copy --bucket my-bucket-1250000000 --cos_key data/ --dest_key archive/ \
  --recursive true --storage_class STANDARD_IA --tags "archived=true"
```

---

## 存储桶操作

### list_buckets - 列出存储桶

列出当前账号下的所有存储桶，支持按地域过滤。

**命令格式：**
```bash
tccli cos list_buckets [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--filter_region` | string | ❌ | 空 | 按地域过滤，如 `ap-guangzhou` |

**示例：**
```bash
# 列出所有存储桶
tccli cos list_buckets

# 列出广州地域的存储桶
tccli cos list_buckets --filter_region ap-guangzhou
```

---

### create_bucket - 创建存储桶

创建一个新的 COS 存储桶。

**命令格式：**
```bash
tccli cos create_bucket [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称，格式如 `my-bucket-1250000000` |
| `--acl` | string | ❌ | private | 访问控制策略：`private`、`public-read`、`public-read-write` |

**示例：**
```bash
# 创建私有存储桶
tccli cos create_bucket --bucket my-bucket-1250000000

# 创建公开读存储桶
tccli cos create_bucket --bucket my-bucket-1250000000 --acl public-read
```

---

### delete_bucket - 删除存储桶

删除指定的 COS 存储桶，使用 `--force` 可强制清空后删除。

**命令格式：**
```bash
tccli cos delete_bucket [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 要删除的存储桶名称 |
| `--force` | bool | ❌ | false | 强制删除：先清空所有对象、版本对象和未完成的分片上传，再删除存储桶 |

> ⚠️ `--force true` 会**不可逆地**删除存储桶内所有数据，请谨慎使用。

**示例：**
```bash
# 删除空存储桶
tccli cos delete_bucket --bucket my-bucket-1250000000

# 强制清空并删除存储桶
tccli cos delete_bucket --bucket my-bucket-1250000000 --force true
```

---

## 统计操作

### du - 统计大小

统计存储桶或指定前缀下的对象总大小、文件数量和文件夹数量，按存储类型分类统计。

**命令格式：**
```bash
tccli cos du [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--prefix` | string | ❌ | 空 | 对象键前缀 |

**示例：**
```bash
# 统计整个存储桶
tccli cos du --bucket my-bucket-1250000000

# 统计指定目录
tccli cos du --bucket my-bucket-1250000000 --prefix data/
```

**输出示例：**
```
统计: cos://my-bucket-1250000000/data/
------------------------------------------------------------
总文件数: 100
总文件夹数: 5
总大小:   1.23 GB (1321205760 字节)

按存储类型统计:
  STANDARD              95 个对象, 1.20 GB
  STANDARD_IA           5 个对象, 30.00 MB
```

---

## 归档恢复

### restore - 恢复归档文件

恢复归档存储类型（ARCHIVE / DEEP_ARCHIVE）的 COS 对象，使其可被下载。

**命令格式：**
```bash
tccli cos restore [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--cos_key` | string | ✅ | - | 要恢复的归档对象键，递归恢复时作为前缀 |
| `--days` | int | ❌ | 7 | 恢复后的有效天数 |
| `--tier` | string | ❌ | Standard | 恢复模式：`Standard`（3-5 小时）、`Expedited`（1-5 分钟）、`Bulk`（5-12 小时） |
| `--recursive` | bool | ❌ | false | 是否递归恢复前缀下所有归档对象 |
| `--include` | string | ❌ | 空 | 包含匹配模式，支持通配符 |
| `--exclude` | string | ❌ | 空 | 排除匹配模式，支持通配符 |
| `--fail_output` | bool | ❌ | false | 启用失败日志。对齐 coscli `--fail-output` |
| `--fail_output_path` | string | ❌ | 空 | 失败日志输出路径 |

**示例：**
```bash
# 恢复单个归档文件（标准模式，有效期 7 天）
tccli cos restore --bucket my-bucket-1250000000 --cos_key archive/data.zip

# 极速恢复，有效期 30 天
tccli cos restore --bucket my-bucket-1250000000 --cos_key archive/data.zip --tier Expedited --days 30

# 递归恢复整个归档目录
tccli cos restore --bucket my-bucket-1250000000 --cos_key archive/ --recursive true --days 7

# 记录失败日志
tccli cos restore --bucket my-bucket-1250000000 --cos_key archive/ --recursive true \
  --fail_output true --fail_output_path /tmp/restore_fail.log
```

---

## 预签名 URL

### signurl - 生成预签名URL

生成 COS 对象的预签名 URL，可用于临时授权访问，无需鉴权即可访问。

**命令格式：**
```bash
tccli cos signurl [参数]
```

**参数说明：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--cos_key` | string | ✅ | - | 对象键（Key） |
| `--expired` | int | ❌ | 3600 | URL 有效期（秒），默认 1 小时 |
| `--method` | string | ❌ | GET | HTTP 方法：`GET`（下载）、`PUT`（上传） |

**示例：**
```bash
# 生成下载链接（有效期 1 小时）
tccli cos signurl --bucket my-bucket-1250000000 --cos_key data/test.txt

# 生成下载链接（有效期 24 小时）
tccli cos signurl --bucket my-bucket-1250000000 --cos_key data/test.txt --expired 86400

# 生成上传链接（有效期 10 分钟）
tccli cos signurl --bucket my-bucket-1250000000 --cos_key data/upload.txt --method PUT --expired 600
```

---

## ACL 权限管理

### get_bucket_acl - 获取存储桶ACL

```bash
tccli cos get_bucket_acl --bucket <存储桶名称>
```

### put_bucket_acl - 设置存储桶ACL

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--acl` | string | ❌ | 空 | 访问控制策略：`private` / `public-read` / `public-read-write` |
| `--grant_read` | string | ❌ | 空 | 授予读权限，格式：`id="账号ID"` |
| `--grant_write` | string | ❌ | 空 | 授予写权限，格式：`id="账号ID"` |
| `--grant_full_control` | string | ❌ | 空 | 授予完全控制权限，格式：`id="账号ID"` |

```bash
# 设置存储桶为公开读
tccli cos put_bucket_acl --bucket my-bucket-1250000000 --acl public-read

# 授予指定账号读权限
tccli cos put_bucket_acl --bucket my-bucket-1250000000 --grant_read 'id="100000000001"'
```

### get_object_acl - 获取对象ACL

```bash
tccli cos get_object_acl --bucket <存储桶名称> --cos_key <对象键>
```

### put_object_acl - 设置对象ACL

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--cos_key` | string | ✅ | - | 对象键（Key） |
| `--acl` | string | ❌ | 空 | 访问控制策略：`private` / `public-read` |
| `--grant_read` | string | ❌ | 空 | 授予读权限 |
| `--grant_full_control` | string | ❌ | 空 | 授予完全控制权限 |

```bash
# 设置对象为公开读
tccli cos put_object_acl --bucket my-bucket-1250000000 --cos_key data/test.txt --acl public-read

# 授予指定账号完全控制权限
tccli cos put_object_acl --bucket my-bucket-1250000000 --cos_key data/test.txt \
  --grant_full_control 'id="100000000001"'
```

---

## 标签管理

### get_object_tagging - 获取对象标签

```bash
tccli cos get_object_tagging --bucket <存储桶名称> --cos_key <对象键>
```

### put_object_tagging - 设置对象标签

设置/覆盖对象标签（现有标签会被完全替换）。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--cos_key` | string | ✅ | - | 对象键（Key） |
| `--tags` | string | ✅ | - | 标签列表，格式：`key1=value1,key2=value2` |

```bash
tccli cos put_object_tagging --bucket my-bucket-1250000000 --cos_key data/test.txt \
  --tags "env=prod,project=myapp,owner=team1"
```

### add_object_tagging - 追加对象标签

在已有标签基础上追加（同 key 覆盖旧值，不影响其它 key）。对齐 coscli `object-tagging add`。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--cos_key` | string | ✅ | - | 对象键（Key） |
| `--tags` | string | ✅ | - | 追加的标签，格式：`k1=v1,k2=v2` |

```bash
tccli cos add_object_tagging --bucket my-bucket-1250000000 --cos_key data/test.txt \
  --tags "owner=team2,version=v2"
```

### delete_object_tagging - 删除对象标签

删除对象所有标签。

```bash
tccli cos delete_object_tagging --bucket my-bucket-1250000000 --cos_key data/test.txt
```

---

## 对象软链接

### create_symlink - 创建对象软链接

创建 COS 对象软链接（symlink），指向另一个对象。对齐 coscli `symlink create`。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--cos_key` | string | ✅ | - | 软链接对象键 |
| `--target_key` | string | ✅ | - | 软链接指向的目标对象键 |
| `--storage_class` | string | ❌ | 空 | 软链接对象的存储类型 |

```bash
tccli cos create_symlink --bucket my-bucket-1250000000 \
  --cos_key links/latest.txt --target_key data/v20240101.txt
```

### get_symlink - 查询对象软链接

获取软链接对象指向的目标对象键。对齐 coscli `symlink get`。

```bash
tccli cos get_symlink --bucket my-bucket-1250000000 --cos_key links/latest.txt
```

---

## 存储桶清单

COS 存储桶清单（Inventory）用于定期或一次性导出桶内对象列表到指定的目标桶中，常用于大规模数据分析。对齐 coscli `inventory` 命令。

### put_bucket_inventory - 创建/更新清单

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--id` | string | ✅ | - | 清单任务 ID |
| `--is_enabled` | bool | ❌ | true | 是否启用该清单任务 |
| `--frequency` | string | ❌ | Daily | 生成频率：`Daily` / `Weekly` |
| `--included_object_versions` | string | ❌ | Current | 版本范围：`Current` / `All` |
| `--prefix` | string | ❌ | 空 | 过滤源对象前缀 |
| `--fields` | string | ❌ | 空 | 可选字段列表，逗号分隔 |
| `--dest_bucket` | string | ❌ | 空 | 清单结果目标桶（完整 QCS 格式） |
| `--dest_account_id` | string | ❌ | 空 | 清单结果目标账号 ID |
| `--dest_prefix` | string | ❌ | 空 | 清单结果 key 前缀 |
| `--dest_format` | string | ❌ | CSV | 清单结果格式：`CSV` / `ORC` |

```bash
tccli cos put_bucket_inventory --bucket my-bucket-1250000000 --id daily-report \
  --frequency Daily --included_object_versions Current \
  --fields "Size,LastModifiedDate,StorageClass,ETag" \
  --dest_bucket "qcs::cos:ap-guangzhou::dst-bucket-1250000000" \
  --dest_prefix "inventory/" --dest_format CSV
```

### get_bucket_inventory - 查询清单

```bash
tccli cos get_bucket_inventory --bucket my-bucket-1250000000 --id daily-report
```

### list_bucket_inventory - 列出清单任务

```bash
tccli cos list_bucket_inventory --bucket my-bucket-1250000000
```

### delete_bucket_inventory - 删除清单任务

```bash
tccli cos delete_bucket_inventory --bucket my-bucket-1250000000 --id daily-report
```

### post_bucket_inventory - 一次性清单

一次性触发清单任务（Frequency 固定为 Once），参数与 `put_bucket_inventory` 类似，但无 `is_enabled` / `frequency`。对齐 coscli `inventory post`。

```bash
tccli cos post_bucket_inventory --bucket my-bucket-1250000000 --id onetime-001 \
  --dest_bucket "qcs::cos:ap-guangzhou::dst-bucket-1250000000"
```

---

## 分片上传管理

### lsparts - 列出分片上传

列出存储桶中未完成的分片上传任务。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--prefix` | string | ❌ | 空 | 对象键前缀 |

```bash
tccli cos lsparts --bucket my-bucket-1250000000
tccli cos lsparts --bucket my-bucket-1250000000 --prefix data/
```

### abort - 清理分片上传

清理存储桶中未完成的分片上传任务，释放存储空间。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--bucket` | string | ✅ | - | 存储桶名称 |
| `--prefix` | string | ❌ | 空 | 对象键前缀，用于过滤要清理的分片上传 |
| `--cos_key` | string | ❌ | 空 | 对象键（指定 `upload_id` 时必填） |
| `--upload_id` | string | ❌ | 空 | 指定要取消的分片上传 ID，不填则清理所有未完成的分片上传 |

```bash
# 清理所有未完成的分片上传
tccli cos abort --bucket my-bucket-1250000000

# 清理指定前缀下的未完成分片上传
tccli cos abort --bucket my-bucket-1250000000 --prefix data/

# 取消指定的分片上传
tccli cos abort --bucket my-bucket-1250000000 --cos_key data/large.zip \
  --upload_id 1585130821cbb7df1d11846c073ad7cf9d27a33
```

---

## 附录

### coscli 参数对齐速查表

本插件全量对齐 coscli 核心命令与参数。参数命名风格保留 tccli 约定（`snake_case`），与 coscli 的 `kebab-case` 一一对应。

**单文件传输（upload / download / copy）新增参数：**

| tccli 参数 | coscli 参数 | 说明 |
|---|---|---|
| `--fail_output` / `--fail_output_path` | `--fail-output` / `--fail-output-path` | 启用并指定失败日志路径 |
| `--err_retry_num` / `--err_retry_interval` | `--err-retry-num` / `--err-retry-interval` | 可重试错误（超时 / 5xx / 429）的额外重试次数与间隔（秒） |
| `--only_current_dir` | `--only-current-dir` | 仅当前目录层，不递归 |
| `--skip_dir` | `--skip-dir` | 不创建空目录标记（upload/copy） |
| `--disable_crc64` | `--disable-crc64` | 关闭 CRC64 校验 |
| `--disable_all_symlink` | `--disable-all-symlink` | 禁用所有符号链接（upload/sync_upload） |
| `--enable_symlink_dir` | `--enable-symlink-dir` | 允许跟随符号链接目录（upload/sync_upload） |
| `--version_id` | `--version-id` | 指定版本 ID（download/copy/delete） |
| `--acl` / `--grant_read` / `--grant_read_acp` / `--grant_write_acp` / `--grant_full_control` | 同名 | 上传/复制时设置 ACL 或授权 |
| `--tags` | `--tags`（格式 `k1=v1&k2=v2`） | 上传/复制时设置对象标签 |
| `--forbid_overwrite` | `--forbid-overwrite` | 禁止覆盖同名对象 |
| `--encryption_type` | `--encryption-type` | 服务端加密类型 `AES256` / `cos/kms` |
| `--sse_customer_algorithm` / `--sse_customer_key` / `--sse_customer_key_md5` | 同名 | SSE-C 自定义密钥加密 |

**同步传输（sync_upload / sync_download / sync_copy）新增参数：**

| tccli 参数 | coscli 参数 | 说明 |
|---|---|---|
| `--ignore_existing` | `--ignore-existing` | 目标存在即跳过（不比内容） |
| `--update` | `--update` | 源端 Last-Modified 更新时才传输 |
| `--snapshot_path` | `--snapshot-path` | 本地 SQLite 快照数据库（零依赖，基于 stdlib `sqlite3`），加速增量判断（仅 sync_upload/sync_download） |
| `--delete_extra` / `--delete` | `--delete` | 删除目标端多余文件；两者等价 |
| `--backup_dir` | `--backup-dir` | 删除多余文件前先备份（sync_upload 备份远端对象到本地；sync_download 备份本地文件到本地） |
| `--ignore_empty_file` | `--ignore-empty-file` | 忽略 0 字节文件 |
| `--force` | `--force` | 跳过确认（当前 sync 无交互，保留作兼容） |

**跳过策略优先级（对齐 coscli sync）：**

1. `--ignore_existing`：目标存在即跳过
2. `--update`：源端 Last-Modified 更新时才传输
3. `--snapshot_path`：本地 `(mtime, size, crc64)` 与快照一致时快速跳过
4. 默认：CRC64 校验（对比对端 `x-cos-hash-crc64ecma`）

**其他扩展：**

- `list` 新增 `--all_versions` / `--limit`
- `restore` 新增 `--fail_output` / `--fail_output_path`
- 新增 `add_object_tagging`（标签合并追加）
- 新增 `create_symlink` / `get_symlink`（对齐 coscli symlink）
- 新增 `put_bucket_inventory` / `get_bucket_inventory` / `list_bucket_inventory` / `delete_bucket_inventory` / `post_bucket_inventory`（对齐 coscli inventory）

> coscli 的 `config init/add/set/show/delete` 不在本插件实现，凭据与 profile 管理请统一使用 `tccli configure`。

---

### 存储类型说明

| 存储类型 | 说明 | 适用场景 |
|----------|------|----------|
| `STANDARD` | 标准存储（默认） | 高频访问数据 |
| `STANDARD_IA` | 低频存储 | 低频访问，存储 30 天以上 |
| `ARCHIVE` | 归档存储 | 极少访问，需要恢复后才能下载 |
| `DEEP_ARCHIVE` | 深度归档存储 | 长期保存，访问频率极低 |
| `INTELLIGENT_TIERING` | 智能分层存储 | 访问模式不固定的数据 |
| `MAZ_STANDARD` | 多 AZ 标准存储 | 高可用要求的高频访问数据 |
| `MAZ_STANDARD_IA` | 多 AZ 低频存储 | 高可用要求的低频访问数据 |

### 失败日志格式

当通过 `--log_file <path>` 或 `--fail_output true --fail_output_path <path>` 指定失败日志路径时，命令会将所有失败项以 **结构化文本（人类友好）** 格式写入日志文件。

**样例：**
```
# upload 失败日志
# 生成时间: 2026-04-21 17:30:00
# 执行耗时: 10.5s
# 失败总数: 2

[1]
  Time      : 2026-04-21 17:30:05
  Source    : /local/path/file.txt
  Dest      : cos://my-bucket-1250000000/data/file.txt
  Reason    : NoSuchBucket (Code: NoSuchBucket)
  RequestId : NjYxMjM0NTY...

[2]
  Time      : 2026-04-21 17:30:06
  Source    : /local/path/other.txt
  Dest      : cos://my-bucket-1250000000/data/other.txt
  Reason    : AccessDenied (Code: AccessDenied)
  RequestId : NjYxMjM0Nzg...
```

**字段说明：**

| 字段 | 说明 |
|------|------|
| `Time` | 失败发生的时间 |
| `Source` | 源路径（本地路径或 `cos://` 路径） |
| `Dest` | 目标路径（本地路径或 `cos://` 路径） |
| `Reason` | 失败原因（包含错误信息和错误码） |
| `RequestId` | COS 请求 ID，用于排查问题 |

**注意：**
- 日志总是以 "追加" 方式写入（多次执行不会清空历史日志）
- 若命令全程无失败项，日志文件**不会**被创建
- `--log_file` 与 `--fail_output_path` 任选其一即可，两者等价；若同时指定，`--fail_output_path` 优先（需 `--fail_output true`）

**使用示例：**
```bash
# upload 使用 log_file
tccli cos upload --bucket my-bucket-1250000000 --local_path /data --cos_key data/ \
  --recursive true --log_file /tmp/upload_fail.log

# upload 使用 coscli 风格（--fail_output + --fail_output_path）
tccli cos upload --bucket my-bucket-1250000000 --local_path /data --cos_key data/ \
  --recursive true --fail_output true --fail_output_path /tmp/upload_fail.log

# 查看失败日志
cat /tmp/upload_fail.log
```
