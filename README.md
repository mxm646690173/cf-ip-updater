# CF优选IP自动更新器

自动从 [api.uouin.com/cloudflare.html](https://api.uouin.com/cloudflare.html) 获取**电信线路**的第一条优选IP，并通过 [cfnew](https://github.com/byJoey/cfnew) API 推送到你的 Cloudflare Worker。

## 运行逻辑

- **每天第1次运行**：先清空 cfnew 中所有优选IP，再添加新获取的IP
- **同天后续运行**：直接添加新IP，不再清空
- **节点命名**：`YYYY-MM-DD-N`（日期-当日第N次获取）

## 工作流程

```
定时触发 (每6小时)
    ↓
判断是否当天第1次运行
    ↓
是 → 清空所有优选IP → 获取新IP → 添加
否 → 直接获取新IP → 添加
    ↓
节点名称: {日期}-{次数}
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

可选 Secret（不设置则使用默认值）：

| Secret 名称 | 默认值 | 说明 |
|---|---|---|
| `CFNEW_PORT` | `443` | 优选IP端口 |
| `WAIT_TIMEOUT` | `90` | 等待页面数据刷新最大秒数 |

### 3. 启用 Workflow

进入 **Actions** 标签页，点击 **"I understand my workflows, go ahead and enable them"**。

之后 Workflow 会每6小时自动运行一次，你也可以在 Actions 页面手动触发运行。

## 相关项目

- [cfnew](https://github.com/byJoey/cfnew) - Cloudflare Workers 优选IP管理面板
- [麒麟域名检测](https://api.uouin.com/cloudflare.html) - CF优选IP数据源