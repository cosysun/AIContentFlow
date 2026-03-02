# 10分钟部署你的第一个 OpenClaw：阿里云一键部署全流程实录

> 上周帮朋友部署 OpenClaw，两个人对着屏幕折腾了快两小时才搞定——主要是踩了几个不该踩的坑。事后复盘，其实整个流程走顺了的话，10分钟够了。这篇文章就是那次踩坑经历的整理版，希望你能比我们快。

---

## 为什么选择阿里云？

在开始之前，先回答一个问题：本地部署和云端部署，选哪个？

**本地部署**的问题在于：你的电脑一关机，AI 助理就下班了。更糟糕的是，如果你想在手机上随时用飞书或企业微信呼唤它，本地部署基本没戏——没有公网 IP，外网根本访问不到。

**阿里云部署**的优势：
- 24小时在线，随时可用
- 有公网 IP，可以对接飞书/企业微信/Telegram
- 轻量服务器有预装的 OpenClaw 镜像，省去 90% 的环境配置
- 新用户有免费试用额度

所以，如果你想认真用 OpenClaw，云端部署是正确选择。

---

## 准备工作（5分钟前的清单）

在正式开始前，确认你手头有这些：

| 需要准备的 | 说明 |
|-----------|------|
| 阿里云账号 | 需完成实名认证 |
| 大模型 API Key | 推荐阿里云百炼（新用户免费额度），或 Claude/GPT 的 API Key |
| 消息平台账号 | 飞书/企业微信/Telegram 三选一（也可以先用 Web 界面） |
| SSH 工具 | macOS/Linux 自带终端，Windows 推荐 MobaXterm 或 VS Code |

> 💡 **关于 API Key 的选择**：国内用户首选阿里云百炼，注册即送 90 天免费额度，配置最简单。如果你有 Anthropic 的 Claude API，体验会更好，但需要科学上网购买。

---

## 第一步：购买阿里云轻量服务器（2分钟）

### 1.1 选择服务器配置

登录[阿里云控制台](https://www.aliyun.com/)，搜索「轻量应用服务器」。

**推荐配置**：
- **CPU/内存**：2核 2GB（个人使用够了，OpenClaw 最低要求 2GB）
- **地域**：
  - 国内用户：选**华东1（杭州）**或**华北2（北京）**，延迟低
  - 不想备案：选**中国香港**或**新加坡**，免 ICP 备案直接用
- **镜像**：这里是关键——在「应用镜像」里找 **OpenClaw**，选最新版本

> ⚠️ **注意**：一定要选「应用镜像」里的 OpenClaw，不要选系统镜像（Ubuntu/CentOS），否则你需要手动安装所有依赖，至少多花 1 小时。

### 1.2 放行防火墙端口

服务器创建完成后，进入实例详情页，点击「防火墙」，添加以下规则：

| 协议 | 端口 | 说明 |
|------|------|------|
| TCP | 22 | SSH 连接（默认已开） |
| TCP | 18789 | OpenClaw Web 控制台及 Webhook 回调 |

点击「确定」，规则立即生效。

---

## 第二步：SSH 连接服务器（1分钟）

在实例详情页找到公网 IP（格式类似 `47.xxx.xxx.xxx`），打开终端：

```bash
ssh root@你的公网IP
```

首次连接会提示确认指纹，输入 `yes` 回车。然后输入购买时设置的密码（或使用密钥登录）。

看到这个提示说明登录成功：

```
Welcome to Alibaba Cloud Elastic Compute Service!
```

> 💡 **Windows 用户**：推荐用 VS Code 安装 Remote-SSH 插件，体验比 PuTTY 好很多。

---

## 第三步：配置 OpenClaw（核心步骤，3分钟）

### 3.1 检查服务状态

登录后先确认 OpenClaw 是否已经在运行：

```bash
openclaw --version
# 输出类似：2026.2.3-1

openclaw doctor
# 应该看到：✔ Gateway running
```

如果 `doctor` 命令显示 Gateway 未运行，执行：

```bash
openclaw gateway start
```

### 3.2 配置大模型 API Key

**方案 A：使用阿里云百炼（推荐国内用户）**

先去[阿里云百炼平台](https://bailian.console.aliyun.com/)创建 API Key，然后在服务器上执行：

```bash
openclaw config set models.providers.bailian.apiKey "sk-你的百炼APIKey"
openclaw config set models.providers.bailian.baseUrl "https://dashscope.aliyuncs.com/compatible-mode/v1"
openclaw config set models.default "qwen3-max"
openclaw gateway restart
```

**方案 B：使用 Claude（需要海外 API）**

```bash
export ANTHROPIC_API_KEY="sk-ant-你的Claude密钥"
openclaw config set models.default "claude-opus-4-5"
openclaw gateway restart
```

**方案 C：使用 GPT-4**

```bash
openclaw config set models.providers.openai.apiKey "sk-你的OpenAI密钥"
openclaw config set models.default "gpt-4o"
openclaw gateway restart
```

### 3.3 打开 Web 控制台验证

在浏览器访问：`http://你的公网IP:18789`

如果看到 OpenClaw 的登录界面，恭喜你——服务器端已经配置完成！

在 Web 控制台里发一条消息测试一下，比如「你好，介绍一下你自己」，如果 AI 正常回复，说明模型接入成功。

---

## 第四步：对接消息平台（选做，2分钟）

Web 界面虽然能用，但真正的「随时随地 AI 助理」需要对接你日常使用的消息工具。下面介绍三种最常用的接入方式：

### 4.1 接入飞书（推荐）

**第一步：创建飞书应用**

1. 登录[飞书开放平台](https://open.feishu.cn/)
2. 点击「创建企业自建应用」，填写应用名称（比如「我的AI助理」）
3. 在「添加应用能力」里选择「机器人」
4. 在「权限管理」里开通：`im:message`、`im:message:send_as_bot`
5. 在「事件订阅」里选择「长连接」模式，添加「接收消息」事件
6. 记录 `App ID` 和 `App Secret`

**第二步：在 OpenClaw 里配置飞书**

```bash
openclaw config set channels.feishu.appId "你的AppID"
openclaw config set channels.feishu.appSecret "你的AppSecret"
openclaw gateway restart
```

**第三步：发布应用并测试**

在飞书开放平台点击「发布版本」，然后在飞书里找到你的机器人，发一条消息，它应该会回复你了。

### 4.2 接入企业微信

1. 登录企业微信管理后台，创建「自建应用」
2. 在「接收消息」配置里，URL 填：`http://你的公网IP:18789/wecom/bot`
3. 记录 `CorpID`、`CorpSecret`、`AgentID`

```bash
openclaw plugins install @william.qian/simple-wecom
openclaw config set channels.wecom.corpId "你的CorpID"
openclaw config set channels.wecom.corpSecret "你的CorpSecret"
openclaw config set channels.wecom.agentId "你的AgentID"
openclaw gateway restart
```

### 4.3 接入 Telegram（适合个人用户）

1. 在 Telegram 里找到 `@BotFather`，发送 `/newbot`
2. 按提示设置机器人名称，获取 API Token

```bash
openclaw config set channels.telegram.enabled true
openclaw config set channels.telegram.token "你的TelegramToken"
openclaw gateway restart
```

配置完成后，在 Telegram 里找到你的机器人，发送 `/start`，它就会响应了。

---

## 第五步：安装必备技能（加分项）

OpenClaw 的强大之处在于 Skills 生态。安装几个常用技能，让它真正「能干活」：

```bash
# 网络搜索能力（必装）
openclaw skills install tavily-search

# 主动推送/定时任务
openclaw skills install proactive-agent

# 文件读写操作
openclaw skills install file-manager

# 代码执行环境
openclaw skills install code-runner
```

安装完成后，重启网关：

```bash
openclaw gateway restart
```

现在试试让它帮你搜索一个问题，或者写一段代码并执行，感受一下真正的 AI Agent 体验。

---

## 常见报错排查手册

部署过程中最容易遇到的几个问题，直接给解法：

### ❌ 报错：`EBADENGINE Unsupported engine: requires node >=22.0.0`

Node.js 版本太低，升级：

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v  # 确认输出 v22.x.x
```

### ❌ 报错：`EACCES: permission denied`

权限问题，配置用户级 npm 目录：

```bash
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### ❌ 浏览器访问 `IP:18789` 超时

检查防火墙是否放行了 18789 端口（回到第一步的防火墙配置），然后验证服务是否在运行：

```bash
netstat -tulnp | grep 18789
# 应该看到 LISTEN 状态
```

如果没有监听，重启网关：

```bash
openclaw gateway restart
```

### ❌ 报错：下载依赖超时（国内网络）

切换 npm 镜像源：

```bash
npm config set registry https://registry.npmmirror.com
npm cache clean --force
# 然后重新安装
```

### ❌ AI 不回复/回复报错

检查 API Key 是否正确配置：

```bash
openclaw config get models
# 确认 apiKey 不为空，baseUrl 正确
```

---

## 进阶配置：让它更好用

### 设置开机自启

避免服务器重启后需要手动启动 OpenClaw：

```bash
systemctl enable openclaw
systemctl status openclaw  # 确认状态为 active
```

### 配置多模型故障转移

当主模型出问题时自动切换备用模型：

```bash
# 编辑配置文件
vim ~/.openclaw/openclaw.json
```

在 `models` 配置里添加 `fallback` 列表，按优先级排列：Claude Opus → Qwen3-Max → GPT-4o。

### 定制 AI 人格（SOUL 配置）

OpenClaw 支持四层记忆架构，最外层的 SOUL 决定了 AI 的基础人格。编辑：

```bash
vim ~/.openclaw/soul.md
```

写入你希望 AI 具备的特质，比如：「你是一个专注于技术和效率的助理，回答简洁直接，不废话」。保存后重启网关生效。

---

## 总结：10分钟部署清单

回顾一下整个流程：

| 步骤 | 操作 | 耗时 |
|------|------|------|
| 1 | 购买阿里云轻量服务器（选 OpenClaw 镜像） | 2分钟 |
| 2 | 放行 18789 端口 | 30秒 |
| 3 | SSH 登录服务器 | 1分钟 |
| 4 | 配置 API Key 并重启网关 | 2分钟 |
| 5 | 验证 Web 控制台 | 30秒 |
| 6 | 对接飞书/企业微信（可选） | 3分钟 |
| 7 | 安装常用 Skills | 1分钟 |

**总计：约 10 分钟**

整个过程最大的坑是：
1. 镜像一定要选「应用镜像」里的 OpenClaw，不要自己从头安装
2. 防火墙端口 18789 必须手动放行
3. 国内用户优先用阿里云百炼，省去网络问题

如果你按这篇文章操作还是卡住了，把报错信息贴到评论区，基本上都是上面那几个问题之一。我会持续更新踩坑记录——毕竟 OpenClaw 迭代很快，每个版本都可能有新坑。

---

> **相关阅读**：
> - OpenClaw MCP 协议完全手册：从「会用」到「自己开发工具」
> - OpenClaw 四层记忆架构实战：让你的 AI 真正「记住你」
> - Skills 必装清单：2026年最强 10 个插件实测
