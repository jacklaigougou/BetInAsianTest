"""
Task Builder - 任务构造器
负责创建和管理异步任务
"""
import asyncio
from typing import Dict, Callable
from uuid import uuid4
import time


class TaskBuilder:
    """
    任务构造器 - 创建、管理和执行异步任务

    支持:
    - 订单级别任务 (多平台并发)
    - 平台级别任务 (单平台操作)
    - 任务状态跟踪
    """

    def __init__(self, online_platform, ws_client):
        """
        Args:
            online_platform: OnlinePlatform 单例实例
            ws_client: WebSocket 客户端实例
        """
        self.online_platform = online_platform
        self.ws_client = ws_client

        # 任务管理
        self.tasks: Dict[str, asyncio.Task] = {}      # task_id -> Task
        self.task_results: Dict[str, any] = {}        # task_id -> result

    # ==================== 订单任务构造 ====================

    def build_new_order_task(self, message: dict) -> str:
        """
        构造新订单任务 (多平台并发获取赔率)

        Args:
            message: {
                "order_id": "ORDER_123",
                "platforms": [
                    {"handler_name": "218_sportsbet", "data": {...}},
                    {"handler_name": "218_pin888", "data": {...}}
                ]
            }

        Returns:
            task_id: 任务ID
        """
        order_id = message.get('order_id', 'unknown')
        task_id = f"new_order_{order_id}_{uuid4().hex[:8]}"

        task = asyncio.create_task(
            self._execute_new_order(task_id, message)
        )

        self.tasks[task_id] = task
        print(f"🧠 构造新订单任务: {order_id} (task_id: {task_id})")
        return task_id

    def build_betting_order_task(self, message: dict) -> str:
        """
            构造下注订单任务 (多平台并发下注)

            Args:
                message: {
                    "order_id": "ORDER_123",
                    "platforms": [
                        {"handler_name": "218_sportsbet", "data": {...}},
                        {"handler_name": "218_pin888", "data": {...}}
                    ]
                }

            Returns:
                task_id: 任务ID
        """
        order_id = message.get('order_id', 'unknown')
        task_id = f"betting_order_{order_id}_{uuid4().hex[:8]}"

        task = asyncio.create_task(
            self._execute_betting_order(task_id, message)
        )

        self.tasks[task_id] = task
        print(f"🧠 构造下注订单任务: {order_id} (task_id: {task_id})")
        return task_id

    def build_single_side_success_task(self, message: dict) -> str:
        """
        构造单边成功任务
        """
        order_id = message.get('order_id', 'unknown')
        task_id = f"single_side_success_{order_id}_{uuid4().hex[:8]}"
        task = asyncio.create_task(
            self._execute_single_side_success(task_id, message)
        )
        self.tasks[task_id] = task
        print(f"🧠 构造补单成功任务: {order_id} (task_id: {task_id})")
        return task_id
    
    
    # ==================== 订单任务执行 ====================

    async def _execute_new_order(self, task_id: str, message: dict):
        """
        执行新订单任务 (获取赔率)

        Args:
            task_id: 任务ID
            message: 消息数据 {type, from, to, data}
        """
        try:
            data = message.get('data', {})
            order_id = data.get('order_id')
            handler_name = data.get('handler_name')

            if not handler_name:
                raise Exception(f"订单 {order_id} 缺少 handler_name")

            print(f"▶️ [{task_id}] 开始执行: {handler_name}")

            # 获取 ActionChain
            ac = self.online_platform.get_action_chain(handler_name)
            
            if not ac:
                raise Exception(f"未找到 ActionChain: {handler_name}")

            # 直接调用 GetOdd
            print(f"  → [{order_id}] {handler_name} 开始获取赔率")
            try:
                result = await ac.GetOdd(dispatch_message=data)
            except Exception as e:
                import traceback
                traceback.print_exc()
                result = {
                    'platform_odd':'',
                    'handler_name':handler_name,
                    'order_id':order_id,
                    'platform_max_stake':'',
                    'timestamp':time.time(),
                    'success':False,
                }
            


            if not result:
                result = {
                    'handler_name':handler_name,
                    'order_id':order_id,
                    'platform_odd':'',
                    'platform_max_stake':'',
                    'timestamp':time.time(),
                    'success':False,
                }

            
            await self._send_to_dispatch_odd_result(result)


        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"执行新订单失败: {e}"
            print(f"? [{task_id}] {error_msg}")
            self.task_results[task_id] = {"success": False, "error": str(e)}

        finally:
            # 从活跃任务中移除
            self.tasks.pop(task_id, None)

    async def _execute_betting_order(self, task_id: str, message: dict):
        """
        执行下注订单任务

        Args:
            task_id: 任务ID
            message: 订单消息
        """
        try:
            data = message.get('data', {})
            order_id = data.get('order_id')
            handler_name = data.get('handler_name')

            if not handler_name:
                raise Exception(f"订单 {order_id} 缺少 handler_name")

            print(f"▶️ [{task_id}] 开始执行: {handler_name}")

            # 获取 ActionChain
            ac = self.online_platform.get_action_chain(handler_name)
            if not ac:
                raise Exception(f"未找到 ActionChain: {handler_name}")

            # 直接调用 BettingOrder
            print(f"  → [{order_id}] {handler_name} 开始下注")
            result = await ac.BettingOrder(dispatch_message=data)

            # 解析新的返回格式
            if isinstance(result, Exception):
                print(f"  ? [{order_id}] {handler_name} 下注失败: {result}")
                summary = {
                    "order_id": order_id,
                    "handler_name": handler_name,
                    "success": False,
                    "error": str(result)
                }
            elif isinstance(result, dict):
                # 新的返回格式
                success = result.get('success', False)

                if success:
                    print(f"  ? [{order_id}] {handler_name} 下注成功")
                    # PIN888 平台
                    if 'wager_id' in result:
                        summary = {
                            "order_id": order_id,
                            "handler_name": handler_name,
                            "success": True,
                            "ticket_id": result.get('ticket_id'),
                            "betting_odd": result.get('betting_odd'),
                            "betting_amount": result.get('betting_amount'),
                            
                        }
                    # Sportsbet 平台
                    elif 'ticket_id' in result:
                        summary = {
                            "order_id": order_id,
                            "handler_name": handler_name,
                            "success": True,
                            "ticket_id": result.get('ticket_id'),
                            "betting_odd": result.get('betting_odd'),
                            "betting_amount": result.get('betting_amount'),
                        }
                    else:
                        summary = {
                            "order_id": order_id,
                            "handler_name": handler_name,
                            "success": True
                        }
                else:
                    print(f"  ? [{order_id}] {handler_name} 下注失败")
                    # PIN888 平台错误
                    if 'error_code' in result:
                        print(f"    错误代码: {result.get('error_code')}")
                        print(f"    错误信息: {result.get('error_message')}")
                        summary = {
                            "order_id": order_id,
                            "handler_name": handler_name,
                            "success": False,
                            "error_code": result.get('error_code'),
                            "error_message": result.get('error_message')
                        }
                    # Sportsbet 平台错误
                    elif 'betErrors' in result:
                        bet_errors = result.get('betErrors', [])
                        if bet_errors:
                            error = bet_errors[0]
                            print(f"    错误代码: {error.get('code')}")
                            print(f"    错误信息: {error.get('message')}")
                        summary = {
                            "order_id": order_id,
                            "handler_name": handler_name,
                            "success": False,
                            "betErrors": bet_errors,
                            "error": result.get('error')
                        }
                    else:
                        summary = {
                            "order_id": order_id,
                            "handler_name": handler_name,
                            "success": False,
                            "error": result.get('error', 'Unknown error')
                        }
            else:
                # 旧的返回格式 (True/False/None)
                if result:
                    print(f"  ? [{order_id}] {handler_name} 下注完成")
                else:
                    print(f"  ? [{order_id}] {handler_name} 下注失败")
                summary = {
                    "order_id": order_id,
                    "handler_name": handler_name,
                    "success": bool(result)
                }

            # 发送结果给 dispatch
            await self._send_to_dispatch_betting_result(summary)

            # 存储结果
            self.task_results[task_id] = summary

            print(f"? [{task_id}] 完成: {'成功' if summary['success'] else '失败'}")

        except Exception as e:
            error_msg = f"执行下注订单失败: {e}"
            print(f"? [{task_id}] {error_msg}")
            self.task_results[task_id] = {"success": False, "error": str(e)}

        finally:
            # 从活跃任务中移除
            self.tasks.pop(task_id, None)
    

    async def _execute_single_side_success(self, task_id: str, message: dict):
        """
        执行单边成功任务
        """
        try:
            data = message.get('data', {})
            order_id = data.get('order_id')
            handler_name = data.get('handler_name')

            if not handler_name:
                raise Exception(f"订单 {order_id} 缺少 handler_name")

            print(f"▶️ [{task_id}] 开始执行: {handler_name}")

            # 获取 ActionChain
            ac = self.online_platform.get_action_chain(handler_name)
            if not ac:
                raise Exception(f"未找到 ActionChain: {handler_name}")

            # 直接调用 BettingOrder
            print(f"  → [{order_id}] {handler_name} 开始补单")
            try:
                result = await ac.SupplementaryOrder(dispatch_message=data)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)
                
            if isinstance(result, Exception):
                print(f"  ? [{order_id}] {handler_name} 补单失败: {result}")
            elif not result:
                print(f"  ? [{order_id}] {handler_name} 补单失败: {result}")
            else:
                print(f"  ? [{order_id}] {handler_name} 补单完成")

            # 汇总结果
           

            

        except Exception as e:
            error_msg = f"执行下注订单失败: {e}"
            print(f"? [{task_id}] {error_msg}")
            self.task_results[task_id] = {"success": False, "error": str(e)}

        finally:
            # 从活跃任务中移除
            self.tasks.pop(task_id, None)

    def build_request_balance_task(self, message: dict) -> str:
        """
        构造余额查询任务 (单个 handler 查询余额)

        Args:
            message: {
                "type": "request_balance",
                "from": "dispatch",
                "data": {
                    "handler_name": "215_sportsbet"
                }
            }

        Returns:
            task_id: 任务ID
        """
        data = message.get('data', {})
        handler_name = data.get('handler_name', 'unknown')
        task_id = f"request_balance_{handler_name}_{uuid4().hex[:8]}"

        task = asyncio.create_task(
            self._execute_request_balance(task_id, message)
        )

        self.tasks[task_id] = task
        print(f"🧮 构造余额查询任务: {handler_name} (task_id: {task_id})")
        return task_id

    async def _execute_request_balance(self, task_id: str, message: dict):
        """
        执行余额查询任务

        Args:
            task_id: 任务ID
            message: 消息数据
        """
        try:
            data = message.get('data', {})
            handler_name = data.get('handler_name')

            if not handler_name:
                raise Exception(f"缺少 handler_name")

            print(f"▶️ [{task_id}] 开始查询余额: {handler_name}")

            # 获取 ActionChain
            ac = self.online_platform.get_action_chain(handler_name)

            if not ac:
                raise Exception(f"未找到 ActionChain: {handler_name}")

            # 调用 GetBalance
            balance = await ac.pom.find_balance_by_request()

            if balance:
                print(f"? [{task_id}] 余额查询成功: {balance}")

                # 发送余额给 dispatch
                await self.ws_client.send({
                    'type': 'balance_update',
                    'from': 'automation',
                    'to': 'dispatch',
                    'data': {
                        'handler_name': handler_name,
                        
                        'balance': balance
                    }
                })
                print(f"📤 [{task_id}] 已发送余额到 dispatch")

                # 存储结果
                self.task_results[task_id] = {
                    "success": True,
                    "handler_name": handler_name,
                    "balance": balance
                }
            else:
                print(f"? [{task_id}] 余额查询失败")
                self.task_results[task_id] = {
                    "success": False,
                    "handler_name": handler_name,
                    "error": "获取余额失败"
                }

        except Exception as e:
            error_msg = f"执行余额查询失败: {e}"
            print(f"? [{task_id}] {error_msg}")
            self.task_results[task_id] = {"success": False, "error": str(e)}

        finally:
            # 从活跃任务中移除
            self.tasks.pop(task_id, None)

    # ==================== 结果处理 ====================
    

    async def _execute_single_side_failure(self, task_id: str, message: dict):
        """
        执行单边失败任务
        """
        try:
            data = message.get('data', {})
            order_id = data.get('order_id')
            handler_name = data.get('handler_name')
        except Exception as e:
            error_msg = f"执行单边失败任务失败: {e}"
            print(f"? [{task_id}] {error_msg}")
            self.task_results[task_id] = {"success": False, "error": str(e)}

        finally:
            # 从活跃任务中移除
            self.tasks.pop(task_id, None)
    
    
    async def _send_to_dispatch_odd_result(self, data: dict):
        """
        发送结果给 Dispatch

        Args:
            data: 要发送的数据
        """
        message = {
            "type": "odd_result",
            "from": "automation",
            "to": "dispatch",
            "data": data
        }
        await self.ws_client.send(message)


    async def _send_to_dispatch_betting_result(self, data: dict):
        """
        发送结果给 Dispatch

        Args:
            data: 要发送的数据
        """
        message = {
            "type": "betting_result",
            "from": "automation",
            "to": "dispatch",
            "data": data
        }
        print(f"📨 发送结果给 Dispatch: {message}")
        await self.ws_client.send(message)




    # ==================== 任务管理 ====================

    def get_task_status(self, task_id: str) -> dict:
        """
        查询任务状态

        Args:
            task_id: 任务ID

        Returns:
            {
                "status": "running" | "completed" | "not_found",
                "result": {...} (如果已完成)
            }
        """
        # 检查是否还在运行
        if task_id in self.tasks:
            return {"status": "running"}

        # 检查是否已完成
        if task_id in self.task_results:
            result = self.task_results.pop(task_id)
            return {"status": "completed", "result": result}

        return {"status": "not_found"}

    def get_running_tasks_count(self) -> int:
        """获取当前运行中的任务数量"""
        return len(self.tasks)

    def get_running_tasks(self) -> Dict[str, asyncio.Task]:
        """获取所有运行中的任务"""
        return self.tasks.copy()
