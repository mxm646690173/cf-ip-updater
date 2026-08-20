# CF优选IP自动更新器

自动从 [cf.junzhen.qzz.io/full_ips_bj.txt](https://cf.junzhen.qzz.io/full_ips_bj.txt) 获取优选IP列表，筛选出**香港(HK)** 与 **韩国(KR)** 的高质量节点，通过 [cfnew](https://github.com/byJoey/cfnew) API 批量推送到你的 Cloudflare Worker。

## 运行逻辑

- **每次运行都会先清空** Worker 中所有优选IP，再批量添加新抓取的IP
- **节点筛选**：仅保留 `#HK`（香港）和 `#KR`（韩国）地区的节点
- **速度筛选**：仅保留速度 > 10M 的节点（数据格式 `[XXM]`）
- **节点命名**：`YYYY-MM-DD-N`（日期-当日第N次运行）

## 数据源格式

数据源是一个纯文本列表，每行一个节点：

```
152.67.210.234:443#KR [12M]
```

| 字段 | 说明 |
|---|---|
| `152.67.210.234` | 优选IP地址 |
| `443` | 端口 |
| `KR` | 地区编码（脚本筛选 HK / KR） |
| `[12M]` | 测速结果（脚本筛选 > 10M） |

## 工作流程

```
定时触发 (每6小时)
    ↓
获取 full_ips_bj.txt 数据
    ↓
解析 & 筛选（HK/KR 地区 + 速度>10M）
    ↓
DELETE 清空 Worker 中所有优选IP
    ↓
批量 POST 添加筛选后的节点
```

## 必要条件

1. 已部署 [cfnew](https://github.com/byJoey/cfnew) 项目到 Cloudflare Workers
2. **已在 cfnew 后台开启「允许API管理」**（访问你的 Worker 地址 `/` 找到开关并开启）
3. 知道你的 cfnew Worker 完整地址

## 使用方式

### 1. Fork 本仓库

点击右上角 **Fork** 按钮，将本仓库复制到你的 GitHub 账号下。

### 2. 配置 GitHub Secrets

在 Fork 后的仓库中，进入 **Settings → Secrets and variables → Actions**，点击 **New repository secret**，添加以下 Secret：

| Secret 名称 | 说明 | 示例 |
|---|---|---|
| `CFNEW_URL` | **必填**。cfnew API 完整地址 | `https://你的worker.workers.dev/你的UUID/api/preferred-ips` |

### 3. 启用 Workflow

进入 **Actions** 标签页，点击 **"I understand my workflows, go ahead and enable them"**。

之后 Workflow 会每6小时自动运行一次，你也可以在 Actions 页面手动触发运行。

## 本地运行

```bash
python update_ip.py
```

需先设置环境变量：

```bash
# Linux / macOS
export CFNEW_URL="https://你的worker.workers.dev/你的UUID/api/preferred-ips"

# Windows (PowerShell)
$env:CFNEW_URL="https://你的worker.workers.dev/你的UUID/api/preferred-ips"
```

## 相关项目

- [cfnew](https://github.com/byJoey/cfnew) - Cloudflare Workers 优选IP管理面板
- [cf.junzhen.qzz.io](https://cf.junzhen.qzz.io/full_ips_bj.txt) - CF优选IP数据源