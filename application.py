"""
Application - 应用主类
整合所有组件
"""
from .websocket import WebSocketClient, HeartbeatHandler
from .task_builder import TaskBuilder
from .core import OnlinePlatform
from .core.config import config
from .utils import js_loader
from configs.settings import Settings
import asyncio
import json
class Application:
    """主应用程序类"""

    def __init__(self, settings):
        """
        Args:
            settings: Settings 配置类
        """
        self.settings = settings

        # WebSocket 客户端 (先初始化,因为 OnlinePlatform 需要它)
        self.ws_client = WebSocketClient(
            uri=f"ws://{settings.WS_HOST}:{settings.WS_PORT}",
            on_message=self.handle_message,
            on_connect=self.on_ws_connect,
            on_ping=self.on_ws_ping
        )

        # 在线平台单例 (传入平台配置和 ws_client)
        self.online_platform = OnlinePlatform(
            platform_info=settings.PLATFORM_INFO,
            ws_client=self.ws_client
        )

        # 心跳处理器
        self.heartbeat_handler = None

        # 任务构造器 (需要在 ws_client 之后初始化)
        self.task_builder = TaskBuilder(
            online_platform=self.online_platform,
            ws_client=self.ws_client
        )

    async def setup(self):
        """初始化平台控制器"""
        print("🚀 初始化平台控制器...")

        # 预加载所有平台的 JS 文件到内存
        print("📦 预加载 JS 文件...")
        for platform_name, platform_config in self.settings.PLATFORM_INFO.items():
            js_base_path = platform_config.get('js_base_path')
            if js_base_path:
                count = js_loader.load_platform_js(platform_name, js_base_path)
                if count > 0:
                    print(f"  ✅ {platform_name}: {count} 个文件")

        # 初始化心跳处理器
        self.heartbeat_handler = HeartbeatHandler(
            ws_client=self.ws_client,
            interval=self.settings.HEARTBEAT_INTERVAL
        )

        print("✅ 平台初始化完成")

        # 已禁用定时余额轮询任务
        # 余额查询现在只在以下情况触发:
        # 1. 收到 request_balance 消息时
        # 2. prepare_work 初始化成功后
        # asyncio.create_task(self.balance_polling_task())

    async def on_ws_connect(self):
        """WebSocket 连接成功回调"""
        # 1. 发送注册请求
        await self.heartbeat_handler.send_register()

        # 2. 启动心跳任务
        await self.heartbeat_handler.start_heartbeat()

    async def on_ws_ping(self, data):
        """处理 ping 消息"""
        await self.heartbeat_handler.handle_ping(data)

    async def handle_message(self, message: dict):
        """
        处理 WebSocket 业务消息

        消息格式:
        {
            "from": "dispatch" | "electron" | "logWindow",
            "type": "new_order" | "betting" | ...,
            "data": {...}
        }
        """
        # print(f"📨 收到消息: {message}")

        # 过滤心跳相关消息 (已在 ws_client 中拦截 ping)
        msg_type = message.get('type')
        if msg_type in ['ping', 'pong', 'heartbeat']:
            return

        # 根据来源路由消息
        from_ = message.get('from')

        match from_:
            case 'electron' | 'logWindow':
                # TODO: 处理来自 Electron 的消息
                match msg_type:
                    case 'onlineAccount':
                        # print(f"🔍 收到 onlineAccount 消息: {message.get('data')}")
                        if self.settings.ENABLE_AUTO_MONITOR:
                        # # 更新在线账号数据 (异步创建 page 和 ac)

                            added = await self.online_platform.update_accounts(message)
                        # print('added:', self.online_platform.get_all_accounts())
                        # if added > 0:
                        #     print(f"📊 当前调度账号总数: {self.online_platform.count()}")
                        # else:   
                        #     pass
                            
                    
                    
                    case 'set_automation_config':
                        print(f"📝 [配置更新] 收到配置: {message.get('data')}")

                        data = message.get('data', {})

                        # 设置赔率下降阈值 (acceptableDropRate)
                        acceptable_drop_rate = data.get('acceptableDropRate')
                        if acceptable_drop_rate is not None:
                            try:
                                config.set_odds_drop_threshold(float(acceptable_drop_rate))
                            except Exception as e:
                                print(f"❌ [配置错误] 设置 acceptableDropRate 失败: {e}")

                        # 设置补单超时时间 (firstRetryTime)
                        first_retry_time = data.get('firstRetryTime')
                        if first_retry_time is not None:
                            try:
                                config.set_supplementary_order_timeout(float(first_retry_time))
                            except Exception as e:
                                print(f"❌ [配置错误] 设置 firstRetryTime 失败: {e}")

                        # 设置最大重试次数 (retryCount)
                        retry_count = data.get('retryCount')
                        if retry_count is not None:
                            try:
                                config.set_max_retry_count(int(retry_count))
                            except Exception as e:
                                print(f"❌ [配置错误] 设置 retryCount 失败: {e}")

                        print(f"✅ [配置完成] 当前配置: {config}")

                    case _:
                        print(f"⚠️ 未知的 electron 消息类型: {message}")
    
            case 'dispatch':
                # 处理调度系统的消息
                match msg_type:
                    case 'betting_order':
                        # 处理下注订单 (使用任务构造器)
                        task_id = self.task_builder.build_betting_order_task(message)

                    case 'new_order':
                        # 处理新订单 (使用任务构造器)

                        # print(f'收到new_order: {json.dumps(message.get("data"), indent=2)}')
                        task_id = self.task_builder.build_new_order_task(message)

                    case 'stop_pin888_cycle':
                        # 停止 PIN888 补单循环
                        data = message.get('data', {})
                        handler_name = data.get('handler_name')

                        if handler_name:
                            account = self.online_platform.get_account(handler_name)
                            if account:
                                account['PIN888_CYCLEING'] = False
                                print(f"⛔ [{handler_name}] 已设置 PIN888_CYCLEING = False, 补单循环将在下次迭代时退出")
                            else:
                                print(f"⚠️ 未找到账号: {handler_name}")
                        else:
                            print(f"⚠️ stop_pin888_cycle 消息缺少 handler_name")

                    case 'request_balance':
                        # print(f"💰 收到请求余额消息: {message.get('data')}")
                        task_id = self.task_builder.build_request_balance_task(message)
                        if task_id:
                            print(f"💰 已构造余额请求任务: {task_id}")
                        else:
                            print(f"💰 构造余额请求任务失败")

                    case 'betting':
                        # TODO: 处理下注请求
                        # print(f"🎲 下注请求: {message.get('message')}")
                        task_id = self.task_builder.build_betting_order_task(message)

                    case 'single_side_success':  
                        # 处理单边成功消息
                        try:
                            
                            task_id = self.task_builder.build_single_side_success_task(message)
                            if task_id:
                                print(f"🎉 已构造单边成功任务: {task_id}")
                            else:
                                print(f"🎉 构造单边成功任务失败")
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            print(e)

                    case 'onlineAccount':
                        # print(f"🔍 收到 1111onlineAccount 消息: {message}")
                        added = await self.online_platform.update_accounts(message)
                        # if added > 0:
                        #     print(f"📊 当前调度账号总数: {self.online_platform.count()}")

                    case 'single_side_failure':
                        # 处理单边失败消息
                        # print(f"❌ 单边失败消息: {message.get('data')}")
                        task_id = self.task_builder.build_single_side_failure_task(message)
                    
                   
                    case _:
                        print(f"⚠️ 未知的 dispatch 消息类型: {msg_type}")


            case 'server' | 'websocket':
                print('收到 server 消息:', message)
            case _:
                print(f"⚠️ 未知消息来源: {from_}")

    async def run(self):
        """运行应用"""
        try:
            # 初始化
            await self.setup()

            # 启动 WebSocket 连接 (会一直运行)
            # 连接成功后会自动发送注册和启动心跳
            print("🔌 开始连接 WebSocket...")
            await self.ws_client.connect()

        except KeyboardInterrupt:
            print("\n⚠️ 收到停止信号")
        except Exception as e:
            print(f"❌ 程序错误: {e}")
        finally:
            # 停止心跳任务
            if self.heartbeat_handler:
                self.heartbeat_handler.cancel()

            # 清理 OnlinePlatform 资源 (FingerBrowser 会话)
            await self.online_platform.cleanup()

            print("🛑 程序退出")
            await self.ws_client.close()
