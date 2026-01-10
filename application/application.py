"""
Application - 应用主类
整合所有组件
"""
import asyncio

from websocket import WebSocketClient, HeartbeatHandler
from .task_builder import TaskBuilder
from .handlers.electron_handler import handle_electron_message
from .handlers.dispatch_handler import handle_dispatch_message
from core import OnlinePlatform
from utils import get_js_loader


class Application:
    """主应用程序类"""

    def __init__(self, settings):
        """初始化应用."""
        self.settings = settings

        self.ws_client = WebSocketClient(
            uri=f"ws://{settings.WS_HOST}:{settings.WS_PORT}",
            on_message=self.handle_message,
            on_connect=self.on_ws_connect,
            on_ping=self.on_ws_ping
        )

        self.online_platform = OnlinePlatform(
            platform_info=settings.PLATFORM_INFO,
            ws_client=self.ws_client
        )

        self.heartbeat_handler = None
        self.js_loader = get_js_loader()
        self.task_builder = TaskBuilder(
            online_platform=self.online_platform,
            ws_client=self.ws_client
        )

    async def setup(self):
        """初始化平台控制器"""
        print("🛠 初始化平台控制器...")

        print("🧩 预加载 JS 文件...")
        for platform_name, platform_config in self.settings.PLATFORM_INFO.items():
            js_base_path = platform_config.get('js_base_path')
            if not js_base_path:
                print(f"  ⚠️ {platform_name}: 未配置 js_base_path")
                continue

            count = self.js_loader.load_platform_js(platform_name, js_base_path)
            if count > 0:
                print(f"  ? {platform_name}: {count} 个文件")
            else:
                print(f"  ⚠️ {platform_name}: 未找到 JS 文件")

        self.heartbeat_handler = HeartbeatHandler(
            ws_client=self.ws_client,
            interval=self.settings.HEARTBEAT_INTERVAL
        )

        print("? 平台初始化完成")

    async def on_ws_connect(self):
        await self.heartbeat_handler.send_register()
        await self.heartbeat_handler.start_heartbeat()

    async def on_ws_ping(self, data):
        await self.heartbeat_handler.handle_ping(data)

    async def handle_message(self, message: dict):
        """路由 WebSocket 业务消息."""
        msg_type = message.get('type')
        if msg_type in ['ping', 'pong', 'heartbeat']:
            return

        from_ = message.get('from')

        match from_:
            case 'electron' | 'logWindow':
                await handle_electron_message(self, message)
            case 'dispatch':
                # 不阻塞 WebSocket 消息循环：创建后台任务处理 dispatch 消息
                # 这样可以继续接收 PMM 数据等后续消息
                asyncio.create_task(handle_dispatch_message(self, message))
            case 'server' | 'websocket':
                print('收到 server 消息:', message)
            case _:
                print(f"⚠️ 未知消息来源: {from_}")

    async def run(self):
        try:
            await self.setup()
            print("🌐 开始连接 WebSocket...")
            await self.ws_client.connect()
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号")
        except Exception as exc:  # noqa: BLE001
            print(f"? 程序错误: {exc}")
        finally:
            if self.heartbeat_handler:
                self.heartbeat_handler.cancel()
            await self.online_platform.cleanup()
            print("👋 程序退出")
            await self.ws_client.close()
