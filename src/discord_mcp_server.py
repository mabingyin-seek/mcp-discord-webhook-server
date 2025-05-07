import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import Tool, TextContent, ErrorData, INVALID_PARAMS, INTERNAL_ERROR
from httpx import AsyncClient, HTTPError

class DiscordMessage(BaseModel):
    """Discord webhook消息模型
    
    用于构建发送到Discord的消息结构
    Attributes:
        content: 消息内容
        type: 消息类型，目前支持text和markdown两种格式
    """
    content: str
    type: str = Field(default="text", description="消息类型，支持text和markdown")

class DiscordWebhook:
    """Discord webhook处理类
    
    负责与Discord webhook API进行交互，发送消息
    
    Attributes:
        webhook_url: Discord webhook的URL地址
        client: HTTP客户端实例，用于发送请求
    """
    
    def __init__(self, webhook_url: str, client: AsyncClient):
        """初始化Discord webhook处理器
        
        Args:
            webhook_url: Discord webhook的URL地址
            client: HTTP客户端实例
            
        Raises:
            ValueError: 当webhook_url为空时抛出
        """
        if not webhook_url:
            raise ValueError("webhook_url不能为空")
        self.webhook_url = webhook_url
        self.client = client

    async def send_message(self, message: DiscordMessage) -> bool:
        """发送消息到Discord
        
        通过webhook API发送消息到指定的Discord频道
        
        Args:
            message: 要发送的消息对象
            
        Returns:
            bool: 发送是否成功
            
        Raises:
            McpError: 当发送失败时抛出，包含错误详情
        """
        try:
            # Discord webhook 只需要 content 字段
            payload = {"content": message.content}
            response = await self.client.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if response.status_code >= 400:
                raise McpError(ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"发送消息失败 - 状态码 {response.status_code}, 响应: {response.text}"
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
    """Discord工具函数类
    
    提供高级工具函数，封装了底层的webhook操作
    
    Attributes:
        webhook: DiscordWebhook实例，用于实际的消息发送
    """
    
    def __init__(self, webhook: DiscordWebhook):
        """初始化Discord工具类
        
        Args:
            webhook: DiscordWebhook实例
        """
        self.webhook = webhook
        
    async def send_message(self, content: str, msg_type: str = "text") -> Dict[str, Any]:
        """发送消息工具函数
        
        提供更友好的接口来发送消息，支持不同的消息类型
        
        Args:
            content: 消息内容
            msg_type: 消息类型，支持text和markdown
            
        Returns:
            Dict[str, Any]: 包含发送结果的字典
            
        Raises:
            McpError: 当消息类型不支持或发送失败时抛出
        """
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
    
    初始化并启动Discord MCP服务器，处理消息发送请求
    
    Args:
        webhook_url: Discord webhook URL，如果不提供则从环境变量获取
        
    Raises:
        ValueError: 当webhook_url未提供且环境变量中也不存在时抛出
    """
    webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
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
        """列出可用的工具
        
        Returns:
            list[Tool]: 可用工具列表，目前只包含send_message工具
        """
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
        """调用工具函数
        
        处理工具调用请求，目前只支持send_message工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            list[TextContent]: 工具执行结果
            
        Raises:
            McpError: 当工具名称无效或参数错误时抛出
        """
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
    """主函数
    
    程序入口点，处理命令行参数并启动服务器
    """
    import asyncio
    import sys
    if len(sys.argv) > 1 :
        webhook_url = sys.argv[1]
    else:
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    asyncio.run(serve(webhook_url))

if __name__ == "__main__":
    main()
