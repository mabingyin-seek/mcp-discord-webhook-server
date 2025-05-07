# Discord MCP Server

一个基于 MCP 的 Discord webhook 服务器，用于通过 MCP 接口发送消息到 Discord。

## 功能特性

- 支持发送文本消息
- 支持发送 Markdown 格式消息
- 通过 MCP 提供标准化的 API 接口
- 支持命令行参数和环境变量配置
- 自动错误处理和重试机制

## 安装

```bash
pip install discord-mcp-server
```

## 使用方法

### 1. 配置 Discord Webhook URL

可以通过以下两种方式设置 Discord webhook URL：

1. 环境变量方式：
```bash
export DISCORD_WEBHOOK_URL="your-discord-webhook-url"
```

2. 命令行参数方式：
```bash
discord-mcp-server "your-discord-webhook-url"
```

### 2. 运行服务器

使用 uvx 运行服务器：

```bash
uvx discord-mcp-server@latest
```

### 3. MCP 接口说明

服务器提供以下 MCP 工具：

- `send_message`: 发送消息到 Discord
  - 参数：
    - `content`: 消息内容（必需）
    - `msg_type`: 消息类型，支持 "text" 或 "markdown"（可选，默认为 "text"）

## 环境变量

- `DISCORD_WEBHOOK_URL`: Discord webhook URL（必需）

## 错误处理

服务器会自动处理以下错误情况：
- 无效的 webhook URL
- 网络连接问题
- 消息发送失败
- 无效的消息类型

## 开发

### 项目结构

```
discord-mcp-server/
├── src/
│   ├── __init__.py
│   └── discord_mcp_server.py
├── pyproject.toml
└── README.md
```

### 依赖项

- fastapi>=0.68.0
- uvicorn>=0.15.0
- pydantic>=2.0.0
- requests>=2.31.0
- mcp[cli]>=1.6.0

## 许可证

MIT License
