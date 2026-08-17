# CF优选IP自动更新器

自动从 [api.uouin.com/cloudflare.html](https://api.uouin.com/cloudflare.html) 获取**电信线路**的第一条优选IP，并通过 [cfnew](https://github.com/byJoey/cfnew) API 推送到你的 Cloudflare Worker。

## 工作流程

```
定时触发 (每6小时)
    ↓
Playwright 无头浏览器访问页面
    ↓
等待 30-90 秒至数据刷新
    ↓
提取电信线路第一条优选IP
    ↓
POST → cfnew API (/api/preferred-ips)
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
| `CFNEW_URL` | **必填**。cfnew API 完整地址，格式为 `https://你的worker域名/{UUID}/api/preferred-ips` | `https://你的worker.workers.dev/你的UUID/api/preferred-ips` |

可选 Secret（不设置则使用默认值）：

| Secret 名称 | 默认值 | 说明 |
|---|---|---|
| `CFNEW_PORT` | `443` | 优选IP端口 |
| `CFNEW_NAME` | `ip优选` | 节点名称 |

### 3. 启用 Workflow

进入 **Actions** 标签页，点击 **"I understand my workflows, go ahead and enable them"**。

之后 Workflow 会每6小时自动运行一次，你也可以在 Actions 页面手动触发运行。

## 相关项目

- [cfnew](https://github.com/byJoey/cfnew) - Cloudflare Workers 优选IP管理面板
- [麒麟域名检测](https://api.uouin.com/cloudflare.html) - CF优选IP数据源