"""
WebSocket Client - 接收消息驱动
"""
import asyncio
import json
import websockets
from typing import Callable


class WebSocketClient:
    """异步 WebSocket 客户端"""

    def __init__(self, uri: str, on_message: Callable, on_connect: Callable = None, on_ping: Callable = None):
        """
        Args:
            uri: WebSocket 服务器地址 (ws://host:port)
            on_message: 业务消息处理回调 async def on_message(msg)
            on_connect: 连接成功回调 async def on_connect() (可选)
            on_ping: ping 消息回调 async def on_ping(data) (可选)
        """
        self.uri = uri
        self.on_message = on_message
        self.on_connect = on_connect
        self.on_ping = on_ping
        self.websocket = None
        self.running = False

    async def connect(self):
        """连接并持续接收消息"""
        self.running = True

        while self.running:
            try:
                async with websockets.connect(self.uri) as ws:
                    self.websocket = ws
                    print(f"✅ WebSocket 已连接: {self.uri}")

                    # 连接成功回调 (发送注册、启动心跳)
                    if self.on_connect:
                        await self.on_connect()

                    # 持续接收消息
                    async for message in ws:
                        try:
                            data = json.loads(message)

                            # 拦截 ping 消息,不进入业务逻辑
                            if data.get('type') == 'ping' and self.on_ping:
                                await self.on_ping(data)
                                continue  # 跳过业务处理

                            # 业务消息
                            await self.on_message(data)
                        except json.JSONDecodeError:
                            print(f"⚠️ 无法解析消息: {message}")
                        except Exception as e:
                            print(f"❌ 处理消息错误: {e}")

            except websockets.exceptions.ConnectionClosed:
                print("⚠️ WebSocket 连接断开")
                if self.running:
                    print("5秒后重连...")
                    await asyncio.sleep(5)
            except Exception as e:
                print(f"❌ WebSocket 错误: {e}")
                if self.running:
                    await asyncio.sleep(5)

        print("WebSocket 客户端已停止")

    async def send(self, message: dict):
        """发送消息到服务器"""
        if self.websocket:
            try:
                # 确保 message 是字典类型
                if not isinstance(message, dict):
                    raise TypeError(f"message 必须是 dict 类型，当前类型: {type(message)}")
                
                # 递归处理不能序列化的对象，将其转换为字符串
                def default_serializer(obj):
                    """处理不能序列化的对象"""
                    try:
                        return str(obj)
                    except:
                        return repr(obj)
                
                # 序列化为 JSON 字符串
                json_str = json.dumps(message, ensure_ascii=False, default=default_serializer)
                
                # 确保发送的是字符串类型
                if not isinstance(json_str, str):
                    json_str = str(json_str)
                
                await self.websocket.send(json_str)
            except TypeError as e:
                print(f"❌ 发送消息失败 - 类型错误: {e}")
                print(f"   消息内容: {message}")
            except json.JSONEncodeError as e:
                print(f"❌ 发送消息失败 - JSON 编码错误: {e}")
                print(f"   消息内容: {message}")
            except Exception as e:
                print(f"❌ 发送消息失败: {e}")
                print(f"   消息类型: {type(message)}")
                print(f"   消息内容: {message}")
        else:
            print("⚠️ WebSocket 未连接")

    async def close(self):
        """关闭连接"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
