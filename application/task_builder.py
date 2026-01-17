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
        return task_id

    def build_cancel_order_task(self, message: dict) -> str:
        """
        构造取消订单任务

        Args:
            message: {
                "type": "cancel_order",
                "from": "dispatch",
                "to": "automation",
                "data": {
                    "order_id": "ORDER_123",
                    "handler_name": "218_betinasian",
                    "ticket_id": "betslip_456",
                    "betting_amount": 100,
                    "betting_odd": 1.95,
                    "reason": "pin888_failed"
                }
            }

        Returns:
            task_id: 任务ID
        """
        data = message.get('data', {})
        order_id = data.get('order_id', 'unknown')
        task_id = f"cancel_order_{order_id}_{uuid4().hex[:8]}"

        task = asyncio.create_task(
            self._execute_cancel_order(task_id, message)
        )

        self.tasks[task_id] = task
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

            # 获取 ActionChain
            ac = self.online_platform.get_action_chain(handler_name)

            if not ac:
                raise Exception(f"未找到 ActionChain: {handler_name}")

            # 直接调用 GetOdd
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

            # 获取 ActionChain
            ac = self.online_platform.get_action_chain(handler_name)
            if not ac:
                raise Exception(f"未找到 ActionChain: {handler_name}")

            # 直接调用 BettingOrder
            result = await ac.BettingOrder(dispatch_message=data)

            # 🆕 BetInAsian 平台特殊处理：立即发送 WS + 后台监控
            is_betinasian = 'betinasian' in handler_name.lower()
            if isinstance(result, dict) and result.get('needs_monitoring') and is_betinasian:
                # 发送第一次 WS 信号（订单创建成功）
                immediate_summary = {
                    "order_id": order_id,
                    "handler_name": handler_name,
                    "success": result.get('success', True),
                    "ticket_id": result.get('betslip_id'),
                    "betting_odd": result.get('price'),
                    "betting_amount": result.get('stake'),
                    "placed_order_id": result.get('placed_order_id'),  # 🆕 添加 place_order 返回的 order_id
                    "status": "order_created",
                    "message": result.get('message', '订单创建成功')
                }
                await self._send_to_dispatch_betting_result(immediate_summary)
                print(f"✅ [BetInAsian] 已发送第一次 WS 信号: 订单创建成功 (order_id: {order_id})")

                # 🆕 启动后台监控任务
                asyncio.create_task(
                    self._monitor_and_report_order(
                        ac=ac,
                        result=result,
                        order_id=order_id,
                        handler_name=handler_name
                    )
                )
                print(f"🔄 [BetInAsian] 已启动后台监控任务 (order_id: {order_id})")

                # 立即返回，不再继续处理
                self.task_results[task_id] = immediate_summary
                return

            # 解析新的返回格式
            if isinstance(result, Exception):
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
                    # BetInAsian 平台（替代 Sportsbet）
                    elif 'betslip_id' in result:
                        summary = {
                            "order_id": order_id,
                            "handler_name": handler_name,
                            "success": True,
                            "ticket_id": result.get('betslip_id'),      # 映射：betslip_id → ticket_id
                            "betting_odd": result.get('price'),         # 映射：price → betting_odd
                            "betting_amount": result.get('stake'),      # 映射：stake → betting_amount
                        }
                    else:
                        summary = {
                            "order_id": order_id,
                            "handler_name": handler_name,
                            "success": True
                        }
                else:
                    # PIN888 平台错误
                    if 'error_code' in result:
                        summary = {
                            "order_id": order_id,
                            "handler_name": handler_name,
                            "success": False,
                            "error_code": result.get('error_code'),
                            "error_message": result.get('error_message')
                        }
                    # BetInAsian 平台错误（替代 Sportsbet）
                    elif 'betErrors' in result:
                        summary = {
                            "order_id": order_id,
                            "handler_name": handler_name,
                            "success": False,
                            "betErrors": result.get('betErrors'),
                            "error": result.get('message') or result.get('error')  # 优先使用 message
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
                summary = {
                    "order_id": order_id,
                    "handler_name": handler_name,
                    "success": bool(result)
                }

            # 🆕 检查是否需要发送第二次 WS 信号（订单最终结果）
            if isinstance(result, dict) and 'immediate_result' in result:
                # BetInAsian 平台：发送第二次 WS 信号（订单最终状态）
                final_summary = {
                    "order_id": order_id,
                    "handler_name": handler_name,
                    "success": summary.get('success'),
                    "ticket_id": result.get('betslip_id'),
                    "betting_odd": result.get('price'),
                    "betting_amount": result.get('stake'),
                    "order_status": result.get('order_status'),
                    "matched_amount": result.get('matched_amount'),
                    "unmatched_amount": result.get('unmatched_amount'),
                    "status": "order_completed",
                    "message": result.get('message', '订单已完成')
                }
                await self._send_to_dispatch_order_status(final_summary)
                print(f"✅ 已发送第二次 WS 信号: 订单最终结果 (order_id: {order_id})")
            else:
                # PIN888 或其他平台：发送标准 betting_result
                await self._send_to_dispatch_betting_result(summary)

            # 存储结果
            self.task_results[task_id] = summary

        except Exception as e:
            error_msg = f"执行下注订单失败: {e}"
            print(f"? [{task_id}] {error_msg}")
            self.task_results[task_id] = {"success": False, "error": str(e)}

        finally:
            # 从活跃任务中移除
            self.tasks.pop(task_id, None)

    async def _execute_cancel_order(self, task_id: str, message: dict):
        """
        执行取消订单任务

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

            # 获取 ActionChain
            ac = self.online_platform.get_action_chain(handler_name)

            if not ac:
                raise Exception(f"未找到 ActionChain: {handler_name}")

            # 调用 CancelOrder
            try:
                result = await ac.CancelOrder(**data)
            except Exception as e:
                import traceback
                traceback.print_exc()
                result = {
                    'success': False,
                    'order_id': order_id,
                    'handler_name': handler_name,
                    'message': f'取消订单异常: {str(e)}',
                    'reason': data.get('reason', 'unknown')
                }

            # 发送结果到 dispatch
            await self._send_to_dispatch_cancel_result(result)

            # 存储结果
            self.task_results[task_id] = result

        except Exception as e:
            error_msg = f"执行取消订单失败: {e}"
            print(f"❌ [{task_id}] {error_msg}")
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

            # 获取 ActionChain
            ac = self.online_platform.get_action_chain(handler_name)
            if not ac:
                raise Exception(f"未找到 ActionChain: {handler_name}")

            # 直接调用 BettingOrder
            try:
                result = await ac.SupplementaryOrder(dispatch_message=data)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)

            if isinstance(result, Exception):
                pass
            elif not result:
                pass
            else:
                pass

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

            # 获取 ActionChain
            ac = self.online_platform.get_action_chain(handler_name)

            if not ac:
                raise Exception(f"未找到 ActionChain: {handler_name}")

            # 调用 GetBalance
            balance = await ac.pom.find_balance_by_request()

            if balance:
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

                # 存储结果
                self.task_results[task_id] = {
                    "success": True,
                    "handler_name": handler_name,
                    "balance": balance
                }
            else:
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

        try:
            await self.ws_client.send(message)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise


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
        await self.ws_client.send(message)


    async def _send_to_dispatch_order_status(self, data: dict):
        """
        发送订单状态更新给 Dispatch（第二次信号）

        Args:
            data: 订单状态数据
        """
        message = {
            "type": "order_status_update",
            "from": "automation",
            "to": "dispatch",
            "data": data
        }
        await self.ws_client.send(message)

    async def _send_to_dispatch_cancel_result(self, data: dict):
        """
        发送取消订单结果给 Dispatch

        Args:
            data: 取消订单结果数据
        """
        message = {
            "type": "cancel_order_result",
            "from": "automation",
            "to": "dispatch",
            "data": data
        }
        await self.ws_client.send(message)


    async def _monitor_and_report_order(
        self,
        ac,
        result: dict,
        order_id: str,
        handler_name: str
    ):
        """
        后台监控订单并发送第二次 WS 信号

        Args:
            ac: ActionChain 实例
            result: BettingOrder 的返回结果
            order_id: 订单ID
            handler_name: 处理器名称
        """
        try:
            print(f"🔄 [后台监控] 开始监控订单: {order_id}")

            # 调用 MonitorOrderStatus 函数
            monitor_result = await ac.MonitorOrderStatus(
                order_id=result.get('order_id'),
                betslip_id=result.get('betslip_id'),
                event_id=result.get('event_id'),
                bet_type=result.get('bet_type'),
                price=result.get('price'),
                bookie=result.get('bookie'),
                stake=result.get('stake'),
                currency=result.get('currency'),
                duration=result.get('duration')
            )

            # 构造第二次 WS 信号
            final_summary = {
                "order_id": order_id,
                "handler_name": handler_name,
                "success": monitor_result.get('success'),
                "ticket_id": result.get('betslip_id'),
                "betting_odd": result.get('price'),
                "betting_amount": result.get('stake'),
                "order_status": monitor_result.get('order_status'),
                "matched_amount": monitor_result.get('matched_amount'),
                "unmatched_amount": monitor_result.get('unmatched_amount'),
                "status": "order_completed",
                "message": monitor_result.get('message')
            }

            # 发送第二次 WS 信号
            await self._send_to_dispatch_order_status(final_summary)
            print(f"✅ [后台监控] 已发送第二次 WS 信号: 订单最终结果 (order_id: {order_id})")

        except Exception as e:
            import traceback
            print(f"❌ [后台监控] 监控订单失败: {e}")
            traceback.print_exc()


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
