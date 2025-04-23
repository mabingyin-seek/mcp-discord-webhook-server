# Discord MCP Server

一个基于MCP的Discord webhook服务器。

## 安装

```bash
pip install discord-mcp-server
```

## 使用方法

1. 设置Discord webhook URL环境变量：
```bash
export DISCORD_WEBHOOK_URL="your-discord-webhook-url"
```

2. 运行服务器：
```bash
discord-mcp
```

## 环境变量

- `DISCORD_WEBHOOK_URL`: Discord webhook URL（必需）

## 功能

- 支持发送文本消息
- 支持发送Markdown格式消息
- 通过MCP提供API接口
