import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import Tool, TextContent, ErrorData, INVALID_PARAMS, INTERNAL_ERROR
from httpx import AsyncClient, HTTPError

class DiscordMessage(BaseModel):
    """Discord webhook消息模型"""
    content: str
    type: str = Field(default="text", description="消息类型，支持text和markdown")

class DiscordWebhook:
    """Discord webhook处理类"""
    
    def __init__(self, webhook_url: str, client: AsyncClient):
        if not webhook_url:
            raise ValueError("webhook_url不能为空")
        self.webhook_url = webhook_url
        # 使用传入的 client
        self.client = client

    # 移除 __aenter__, __aexit__, close 方法
        
    async def send_message(self, message: DiscordMessage) -> bool:
        """发送消息到Discord"""
        try:
            response = await self.client.post(
                self.webhook_url,
                json=message.model_dump(),
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if response.status_code >= 400:
                raise McpError(ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"发送消息失败 - 状态码 {response.status_code}"
                ))
            return True
        except HTTPError as e:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"发送消息失败: {str(e)}"
            ))
        except Exception as e:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"发送消息时发生未知错误: {str(e)}"
            ))

class DiscordTools:
    """Discord工具函数类"""
    
    def __init__(self, webhook: DiscordWebhook):
        self.webhook = webhook
        
    async def send_message(self, content: str, msg_type: str = "text") -> Dict[str, Any]:
        """发送消息工具函数"""
        if msg_type not in ["text", "markdown"]:
            raise McpError(ErrorData(
                code=INVALID_PARAMS,
                message=f"不支持的消息类型: {msg_type}"
            ))
            
        message = DiscordMessage(content=content, type=msg_type)
        success = await self.webhook.send_message(message)
        
        return {
            "success": success,
            "message": "消息发送成功" if success else "消息发送失败"
        }

async def serve(
    webhook_url: Optional[str] = None,
) -> None:
    """运行Discord MCP服务器
    
    Args:
        webhook_url: Discord webhook URL，如果不提供则从环境变量获取
    """
    webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL",
    "https://discord.com/api/webhooks/1363559361536069834/EOaSnGl4BUifN9n7XscAhuLPnKQ3fHmBeAygmppHBZdGIX19RXltp3UdGmKBB_RRBbIR")
    if not webhook_url:
        raise ValueError("必须提供DISCORD_WEBHOOK_URL环境变量或通过参数传入webhook_url")
        
    server = Server("discord-mcp")
    # 显式创建 AsyncClient
    http_client = AsyncClient()
    
    # 创建 webhook 和 tools 实例，并运行服务器
    webhook = DiscordWebhook(webhook_url, http_client)
    tools = DiscordTools(webhook)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="send_message",
                description="发送消息到Discord，支持text和markdown格式",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "消息内容"
                        },
                        "msg_type": {
                            "type": "string",
                            "description": "消息类型，支持text和markdown",
                            "default": "text",
                            "enum": ["text", "markdown"]
                        }
                    },
                    "required": ["content"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        if name != "send_message":
            raise McpError(ErrorData(
                code=INVALID_PARAMS,
                message=f"未知的工具名称: {name}"
            ))
            
        if "content" not in arguments:
            raise McpError(ErrorData(
                code=INVALID_PARAMS,
                message="消息内容不能为空"
            ))
            
        result = await tools.send_message(
            content=arguments["content"],
            msg_type=arguments.get("msg_type", "text")
        )
        
        return [TextContent(type="text", text=result["message"])]
    try:
        options = server.create_initialization_options()
        async with stdio_server() as (read_stream, write_stream):
                await server.run(read_stream, write_stream, options, raise_exceptions=True)
    finally:
        # 确保 AsyncClient 在 server.run 结束后关闭
        if http_client:
            await http_client.aclose()

def main():
    """主函数"""
    import asyncio
    asyncio.run(serve())

if __name__ == "__main__":
    main()