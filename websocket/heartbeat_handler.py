"""
Heartbeat Handler - 心跳处理器
负责注册、心跳发送、ping/pong 响应
"""
import asyncio
import os


class HeartbeatHandler:
    """心跳处理器 - 独立管理 WebSocket 心跳机制"""

    def __init__(self, ws_client, interval=3):
        """
        Args:
            ws_client: WebSocketClient 实例
            interval: 心跳间隔(秒), 默认3秒
        """
        self.ws_client = ws_client
        self.interval = interval
        self.heartbeat_task = None

    async def send_register(self):
        """
        发送注册请求
        连接成功后立即调用
        """
        await self.ws_client.send({
            "type": "register",
            "from": "automation",
            "pid": os.getpid()
        })
        print("📝 已发送注册请求")

    async def start_heartbeat(self):
        """
        启动心跳循环任务
        作为后台任务独立运行
        """
        self.heartbeat_task = asyncio.create_task(
            self._heartbeat_loop()
        )
        print("💓 心跳任务已启动")

    async def _heartbeat_loop(self):
        """
        心跳循环 - 每 N 秒发送一次心跳包
        """
        try:
            while self.ws_client.running:
                await asyncio.sleep(self.interval)

                # 只在连接状态下发送
                if self.ws_client.websocket:
                    await self.ws_client.send({
                        "type": "heartbeat",
                        "from": "automation",
                        "pid": os.getpid()
                    })
                    # print("💓 发送心跳")

        except asyncio.CancelledError:
            print("心跳任务已取消")
        except Exception as e:
            print(f"❌ 心跳任务错误: {e}")

    async def handle_ping(self, data):
        """
        处理服务器 ping 消息,立即回复 pong

        Args:
            data: ping 消息数据
        """
        await self.ws_client.send({
            "type": "pong",
            "from": "automation",
            "pid": os.getpid()
        })
        print("🏓 收到 ping, 已回复 pong")

    def cancel(self):
        """
        取消心跳任务
        程序退出时调用
        """
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            print("心跳任务已请求取消")
