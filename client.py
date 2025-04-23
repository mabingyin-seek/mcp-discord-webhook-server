# 导入必要的模块和类型
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


# 创建标准输入输出服务器参数配置
# 这些参数用于启动和管理与服务器的通信
server_params = StdioServerParameters(
    command="python",  # 使用 python 直接运行
    args=["src/discord_mcp_server.py"],  # 传递脚本路径作为参数
    env=None,  # 可选的环境变量设置
)

# 定义采样回调函数
# 这个函数用于处理模型生成的消息
async def handle_sampling_message(
    message: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    # 返回一个固定的响应消息
    return types.CreateMessageResult(
        role="assistant",  # 消息角色为助手
        content=types.TextContent(
            type="text",  # 内容类型为文本
            text="Hello, world! from model",  # 消息内容
        ),
        model="gpt-3.5-turbo",  # 使用的模型名称
        stopReason="endTurn",  # 停止原因
    )

# 主运行函数
async def run():
    try:
        print("正在启动客户端...")
        # 使用标准的嵌套异步上下文管理器
        async with stdio_client(server_params) as (read, write):
            print("已建立连接")
            async with ClientSession(
                read, write, sampling_callback=handle_sampling_message
            ) as session:
                print("正在初始化会话...")
                await session.initialize()

                # 列出所有可用的工具
                print("正在获取工具列表...")
                tools = await session.list_tools()
                print("可用的工具:", tools)

                # 调用特定工具并传入参数
                print("正在调用工具...")
                result = await session.call_tool(
                    "send_message", 
                    arguments={"msg_type": 'markdown', 
                               "content": '# 今日黄金\n## 今日黄金价格1060元！'})
                print("工具调用结果:", result)
                
            print("会话已关闭") # Session closed by context manager
        print("客户端连接已关闭") # Client connection closed by context manager

    except Exception as e:
        print(f"客户端运行时出错: {str(e)}", file=sys.stderr)
        # 异常信息会在协程退出时打印
    finally:
        # 清理由 async with 自动处理
        print("客户端完成")

# 程序入口点
if __name__ == "__main__":
    # 在 Windows 上，显式设置 ProactorEventLoop 策略可能有助于解决某些子进程问题
    # 但如果标准 SelectorEventLoop 工作正常，则不需要
    # if sys.platform == "win32":
    #      asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        # 捕获 asyncio.run 可能引发的顶层异常
        print(f"程序顶层运行出错: {str(e)}", file=sys.stderr)