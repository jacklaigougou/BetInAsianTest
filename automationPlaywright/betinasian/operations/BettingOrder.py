# -*- coding: utf-8 -*-
"""
BetInAsian 下注订单

简化的下单流程：
1. 从 order_record 获取 betslip_id（需要先调用 GetOdd）
2. 实时查询最新价格（通过 get_price_by_betslip_id）
3. 提交订单
4. 等待订单数据（可选）
5. 查询订单结果
6. 监控订单状态（可选）
"""
from typing import Dict, Any
import logging
import asyncio
from ..jsCodeExcutors.queries.pmm import get_price_by_betslip_id
from ..jsCodeExcutors.http_executors import place_order, delete_betslip

from configs.settings import Settings as settings

logger = logging.getLogger(__name__)


async def BettingOrder(
    self,
    dispatch_message: Dict[str, Any],
    stake: float = 5,
    currency: str = "USD",
    duration: int = settings.BETINASIAN_DURATION,
    required_amount: float = 10.0,
    required_currency: str = "GBP",  # 修改为 GBP，与 GetOdd 保持一致
    wait_for_order: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
        下注订单（简化流程）

        注意：调用此函数前必须先调用 GetOdd 创建 betslip 并存储到 order_record

        Args:
            dispatch_message: {
                'order_id': str,  # 必需，用于从 order_record 获取 betslip_id
                'stake': float,   # 可选，投注金额（默认: 5）
                'currency': str,  # 可选，货币（默认: "USD"）
                'duration': int   # 可选，订单有效期（秒，默认: 10）
            }
            stake: 投注金额 (默认: 5.0)
            currency: 货币 (默认: "USD")
            duration: 订单有效期（秒，默认: 10）
            required_amount: PMM 查询所需金额 (默认: 10.0)
            required_currency: PMM 查询所需货币 (默认: "GBP")
            wait_for_order: 是否等待订单数据 (默认: True)
            **kwargs: 额外参数
                - monitor_order: 是否监控订单状态 (默认: True)

        注意：
            - dispatch_message 中的参数优先级高于函数参数
            - 例如：dispatch_message={'duration': 10} 会覆盖函数参数 duration=30

        Returns:
            {
                'success': True/False,
                'order_id': str,
                'betslip_id': str,
                'event_id': str,
                'bet_type': str,
                'price': float,
                'bookie': str,
                'stake': float,
                'currency': str,
                'duration': int,
                'order_status': str,
                'matched_amount': float,
                'unmatched_amount': float,
                'bets': list,
                'final_order_state': dict,
                'message': str,
                'order_result': dict,
                'order_query_result': dict
            }

        Examples:
            >>> # 先调用 GetOdd
            >>> odd_result = await self.GetOdd(dispatch_message)
            >>>
            >>> # 使用默认参数下注（duration=30秒）
            >>> result = await BettingOrder(
            ...     self,
            ...     dispatch_message={'order_id': '123'}
            ... )
            >>>
            >>> # 通过 dispatch_message 设置 duration=10秒
            >>> result = await BettingOrder(
            ...     self,
            ...     dispatch_message={
            ...         'order_id': '123',
            ...         'stake': 10.0,
            ...         'currency': 'GBP',
            ...         'duration': 10  # ← 设置为 10 秒
            ...     }
            ... )
            >>>
            >>> # 通过函数参数设置 duration=10秒
            >>> result = await BettingOrder(
            ...     self,
            ...     dispatch_message={'order_id': '123'},
            ...     stake=10.0,
            ...     currency='GBP',
            ...     duration=10  # ← 设置为 10 秒
            ... )
    """
    betslip_id = None  # 初始化,用于 finally 块清理
    try:
        logger.info("="*60)
        logger.info("🎯 开始下注流程")
        logger.info("="*60)
        
        # ========== Step 1: 从 order_record 获取 betslip_id ==========
        logger.info("\n📋 Step 1: 从 order_record 获取 betslip_id...")

        # bet_data = dispatch_message.get('bet_data', {})
        order_id = dispatch_message.get('order_id', '')
        
        # betting_amount = dispatch_message.get('betting_amount', 0)
        
        # print(f'下单的dispatch_message : {dispatch_message}')

        # 从 dispatch_message 中获取参数（如果有的话）
        # 优先使用 dispatch_message 中的参数，否则使用函数默认参数
        stake = dispatch_message.get('betting_amount', stake)
        currency = dispatch_message.get('currency', currency)
        duration = dispatch_message.get('duration', duration)

        # 检查并调整余额
        balance_result = await self.GetBalance()
        balance = balance_result.get('balance')
        if balance is None:
            logger.error(f"❌ 获取余额失败，无法下注")
            return {
                'success': False,
                'message': '获取余额失败',
                'order_id': order_id
            }

        adjusted_stake = await self.check_and_adjust_balance(
            balance=float(balance),
            bet_amount=stake,
            decimal_places=1
        )
        if adjusted_stake is None:
            logger.error(f"❌ 余额无效，无法下注")
            return {
                'success': False,
                'message': '余额无效',
                'order_id': order_id
            }
        stake = adjusted_stake

        logger.info(f"📝 下单参数:")
        logger.info(f"  - Stake: {stake} {currency}")
        logger.info(f"  - Duration: {duration} seconds")

        if not order_id or order_id not in self.order_record:
            logger.error(f"❌ order_record 中没有数据（order_id: {order_id}）")
            logger.error(f"   请先调用 GetOdd 获取赔率信息")
            return {
                'success': False,
                'message': '请先调用 GetOdd 获取赔率信息',
                'order_id': order_id
            }

        cached_data = self.order_record[order_id]
        betslip_id = cached_data.get('betslip_id')
        event_id = cached_data.get('event_id')
        bet_type = cached_data.get('bet_type')

        if not betslip_id:
            logger.error(f"❌ order_record 中缺少 betslip_id")
            return {
                'success': False,
                'message': 'order_record 中缺少 betslip_id',
                'order_id': order_id
            }

        

        # ========== Step 2: 实时查询最新价格 ==========
        logger.info("\n💰 Step 2: 实时查询最新价格...")
       
        

        # best_price_result = await get_price_by_betslip_id(
        #     page=self.page,
        #     betslip_id=betslip_id,
        #     required_amount=required_amount,
        #     required_currency=required_currency
        # )

        # if not best_price_result.get('success'):
        #     logger.error(f"❌ 获取价格失败: {best_price_result.get('reason')}")
        #     return {
        #         'success': False,
        #         'message': f"获取价格失败: {best_price_result.get('reason')}",
        #         'betslip_id': betslip_id,
        #         'order_id': order_id
        #     }

        # best_price = best_price_result.get('price')
        # best_bookie = best_price_result.get('bookie')
        # available = best_price_result.get('available')

        # logger.info(f"✅ 获取最新价格成功:")
        # logger.info(f"  - Price: {best_price}")
        # logger.info(f"  - Bookie: {best_bookie}")
        # logger.info(f"  - Available: {available}")

        # if not best_price or best_price <= 0:
        #     logger.error(f"❌ 价格无效: {best_price}")
        #     return {
        #         'success': False,
        #         'message': f'价格无效: {best_price}',
        #         'betslip_id': betslip_id,
        #         'price': best_price,
        #         'order_id': order_id
        #     }

        # ========== Step 3: 提交订单 ==========
        best_price = cached_data.get('order_odds')
        best_bookie = cached_data.get('bookie')
        logger.info("\n📤 Step 3: 提交订单...")
        logger.info(f"  - Price: {best_price} (来自 {best_bookie})")
        logger.info(f"  - Stake: {stake} {currency}")
        logger.info(f"  - Duration: {duration} seconds")

        
        order_result = await place_order(
            page=self.page,
            betslip_id=betslip_id,
            price=best_price,
            stake=stake,
            currency=currency,
            duration=duration
        )

        if not order_result.get('success'):
            error_msg = order_result.get('error', 'Unknown error')
            status = order_result.get('status', 0)
            response_data = order_result.get('data')

            logger.error(f"❌ 下单失败: {error_msg}")
            logger.error(f"   HTTP Status: {status}")
            if response_data:
                import json
                logger.error(f"   响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

            return {
                'success': False,
                'message': f"下单失败: {error_msg}",
                'error': error_msg,
                'status': status,
                'response_data': response_data,
                'betslip_id': betslip_id,
                'price': best_price,
                'bookie': best_bookie,
                'stake': stake,
                'currency': currency,
                'order_result': order_result,
                'betErrors':'order 挂载失败',
                'status':'failed'
            }

        # 提取 order_id（从 place_order 响应中）
        # 响应格式: {"data": {"data": {"order_id": 1054169958, ...}, "status": "ok"}}
        placed_order_id = order_result.get('data', {}).get('data', {}).get('order_id')
        if not placed_order_id:
            logger.error("❌ 无法从响应中提取 order_id")
            logger.error(f"   响应数据: {order_result}")
            return {
                'success': False,
                'message': '下单成功但无法提取 order_id',
                'betslip_id': betslip_id,
                'price': best_price,
                'bookie': best_bookie,
                'stake': stake,
                'currency': currency,
                'order_result': order_result,
                'betErrors':'order 挂载失败',
                'status':'failed'
            }

        order_id_str = str(placed_order_id)
        logger.info(f"✅ 订单提交成功:")
        logger.info(f"  - Order ID: {order_id_str}")
        logger.info(f"  - Status: {order_result.get('status')}")

        # 🆕 将 placed_order_id 存储到 order_record 中
        self.order_record[order_id]['placed_order_id'] = placed_order_id
        logger.info(f"💾 已将 placed_order_id 存储到 order_record[{order_id}]")

        # ========== 立即返回订单创建成功的结果 ==========
        logger.info("📡 订单创建成功，立即返回结果，后台将继续监控...")

        return {
            'success': True,
            'order_id': order_id_str,
            'placed_order_id': placed_order_id,  # 🆕 添加原始 order_id（整数）
            'betslip_id': betslip_id,
            'event_id': event_id,
            'bet_type': bet_type,
            'price': best_price,
            'bookie': best_bookie,
            'stake': stake,
            'currency': currency,
            'duration': duration,
            'message': '订单创建成功',
            'order_result': order_result,
            'betErrors': '',
            'status': 'order_created',
            'betting_amount': stake,
            'betting_odd': best_price,
            'needs_monitoring': True,  # 标识：需要后台监控
        }

        # ========== 以下代码将被移到 MonitorOrderStatus 函数 ==========
        # ========== Step 5: 查询订单结果 ==========
        logger.info(f"\n🔍 Step 5: 查询订单结果...")

        from ..jsCodeExcutors.queries.orders.get_order import (
            get_order_by_id,
            get_order_with_bets,
            check_order_slippage
        )

        order_query_result = await get_order_by_id(
            page=self.page,
            order_id=order_id_str
        )

        # 处理查询结果
        if order_query_result.get('success'):
            order_status = order_query_result.get('status')
            matched_amount = order_query_result.get('matched_amount', 0)
            unmatched_amount = order_query_result.get('unmatched_amount', 0)
            bets = order_query_result.get('bets', [])

            logger.info(f"✅ 订单查询成功:")
            logger.info(f"  - Status: {order_status}")
            logger.info(f"  - Matched: {matched_amount}")
            logger.info(f"  - Unmatched: {unmatched_amount}")
            logger.info(f"  - Bets: {len(bets)} bets")
        else:
            logger.warning(f"⚠️ 订单查询失败: {order_query_result.get('reason')}")
            logger.warning(f"  订单已提交成功，但无法查询状态")
            order_status = 'unknown'
            matched_amount = 0
            unmatched_amount = 0
            bets = []

        # ========== Step 6: 监控订单状态（可选） ==========
        monitor_order = kwargs.get('monitor_order', True)
        final_order_state = None

        if monitor_order:
            logger.info(f"\n📡 Step 6: 监控订单状态...")

            timeout = duration + 5  # duration + 5秒缓冲
            logger.info(f"  - 监控时长: {timeout} 秒")

            import time
            start_time = time.time()
            found_order = False

            try:
                # 轮询查询订单状态
                while time.time() - start_time < timeout:
                    elapsed = int(time.time() - start_time)

                    order = await get_order_by_id(self.page, order_id_str)

                    if order and order.get('success'):
                        found_order = True
                        state = order.get('state')
                        bet_bar = order.get('bet_bar', {})

                        logger.info(f"  [{elapsed}s] State: {state}, "
                                  f"Success: {bet_bar.get('success', 0)}, "
                                  f"InProgress: {bet_bar.get('inprogress', 0)}, "
                                  f"Danger: {bet_bar.get('danger', 0)}")

                        # 检查是否完成
                        if state in ['FINISHED', 'EXPIRED_LOCAL']:
                            logger.info(f"\n{'✅' if state == 'FINISHED' else '⏱️'} 订单已结束: {state}")
                            final_order_state = order
                            break
                    else:
                        if elapsed % 5 == 0:  # 每5秒打印一次
                            logger.info(f"  [{elapsed}s] 等待订单进入 Store...")

                    # 等待1秒后继续轮询
                    await asyncio.sleep(1)

                # 监控结束后显示最终结果
                if found_order and final_order_state:
                    logger.info(f"\n" + "="*60)
                    logger.info("📊 最终订单状态:")
                    logger.info("="*60)
                    logger.info(f"  - 订单ID: {final_order_state.get('order_id')}")
                    logger.info(f"  - 状态: {final_order_state.get('state')}")
                    logger.info(f"  - 原始状态: {final_order_state.get('raw_status')}")
                    logger.info(f"  - 赛事ID: {final_order_state.get('event_id')}")
                    logger.info(f"  - Betslip ID: {final_order_state.get('betslip_id')}")

                    # 显示 bet_bar
                    bet_bar = final_order_state.get('bet_bar', {})
                    logger.info(f"\n  📊 投注进度条:")
                    logger.info(f"    - 成功: {bet_bar.get('success', 0)}")
                    logger.info(f"    - 进行中: {bet_bar.get('inprogress', 0)}")
                    logger.info(f"    - 危险: {bet_bar.get('danger', 0)}")
                    logger.info(f"    - 未下注: {bet_bar.get('unplaced', 0)}")

                    # 显示状态机摘要
                    state_summary = final_order_state.get('state_summary', {})
                    if state_summary:
                        logger.info(f"\n  🔄 状态机摘要:")
                        logger.info(f"    - 当前状态: {state_summary.get('state')}")
                        logger.info(f"    - 是否完成: {state_summary.get('isDone')}")
                        logger.info(f"    - 下一状态: {state_summary.get('nextState')}")

                    # 检查 Bet Store 状态
                    logger.info("\n🔍 检查 Bet Store 状态...")
                    bet_info = await self.page.evaluate("""
                        (order_id) => {
                            // Bet Store 信息
                            const bet_store_exists = !!window.betStore;
                            const bet_store_size = window.betStore ? window.betStore.store.size : 0;
                            const bet_handler_exists = !!window.__betHandler;
                            const bet_handler_stats = window.__betHandler ? window.__betHandler.getStats() : null;

                            // 直接检查索引
                            let byOrder_index = null;
                            if (window.betStore && window.betStore.indexes.byOrder) {
                                const orderBets = window.betStore.indexes.byOrder.get(order_id);
                                byOrder_index = orderBets ? Array.from(orderBets) : null;
                            }

                            // 检查 Store 中所有 bet
                            let all_bets = [];
                            if (window.betStore && window.betStore.store) {
                                all_bets = Array.from(window.betStore.store.entries()).map(([bet_id, bet]) => ({
                                    bet_id: bet_id,
                                    order_id: bet.order_id,
                                    bookie: bet.bookie,
                                    status: bet.status
                                }));
                            }

                            // 测试 getBetsByOrder
                            let getBetsByOrder_result = null;
                            if (window.betStore && window.betStore.getBetsByOrder) {
                                getBetsByOrder_result = window.betStore.getBetsByOrder(order_id);
                            }

                            // Order 内部数组
                            const order_arrays = window.orderStore ?
                                Array.from(window.orderStore.store.values()).map(o => ({
                                    order_id: o.order_id,
                                    success: o.success,
                                    inprogress: o.inprogress,
                                    danger: o.danger,
                                    unplaced: o.unplaced
                                })) : [];

                            return {
                                bet_store_exists,
                                bet_store_size,
                                bet_handler_exists,
                                bet_handler_stats,
                                byOrder_index,
                                all_bets,
                                getBetsByOrder_result,
                                order_arrays
                            };
                        }
                    """, order_id_str)

                    logger.info(f"  - Bet Store 是否存在: {bet_info.get('bet_store_exists')}")
                    logger.info(f"  - Bet Store 大小: {bet_info.get('bet_store_size')}")
                    logger.info(f"  - Bet Handler 是否存在: {bet_info.get('bet_handler_exists')}")
                    logger.info(f"  - Bet Handler 统计: {bet_info.get('bet_handler_stats')}")

                    # 显示索引检查
                    byOrder_index = bet_info.get('byOrder_index')
                    logger.info(f"\n  🔍 Bet Store byOrder 索引:")
                    logger.info(f"    - 订单 {order_id_str} 的索引: {byOrder_index}")

                    # 显示所有 Bet
                    all_bets = bet_info.get('all_bets', [])
                    if all_bets:
                        logger.info(f"\n  📊 Bet Store 中所有 Bet ({len(all_bets)} 个):")
                        for bet in all_bets:
                            logger.info(f"    - Bet {bet.get('bet_id')}: 订单ID={bet.get('order_id')}, 庄家={bet.get('bookie')}, 状态={bet.get('status')}")

                    # 显示 getBetsByOrder 结果
                    getBetsByOrder_result = bet_info.get('getBetsByOrder_result')
                    logger.info(f"\n  🔍 getBetsByOrder('{order_id_str}') 返回: {len(getBetsByOrder_result) if getBetsByOrder_result else 0} 个 bet")

                    # 显示 Order 内部的 bet 数组
                    order_arrays = bet_info.get('order_arrays', [])
                    if order_arrays:
                        logger.info(f"\n  📊 订单内部的 Bet 数组:")
                        for o in order_arrays:
                            logger.info(f"    订单 {o.get('order_id')}:")
                            logger.info(f"      - 成功: {o.get('success')}")
                            logger.info(f"      - 进行中: {o.get('inprogress')}")
                            logger.info(f"      - 危险: {o.get('danger')}")
                            logger.info(f"      - 未下注: {o.get('unplaced')}")

                    # 查询所有 bets
                    logger.info("\n📊 查询所有 Bets...")
                    result_with_bets = await get_order_with_bets(self.page, order_id_str)

                    if result_with_bets:
                        bets = result_with_bets.get('bets', [])
                        logger.info(f"\n  ✅ 找到 {len(bets)} 个 Bet:")

                        for i, bet in enumerate(bets, 1):
                            logger.info(f"\n  投注 #{i}:")
                            logger.info(f"    - 投注ID: {bet.get('bet_id')}")
                            logger.info(f"    - 庄家: {bet.get('bookie')}")
                            logger.info(f"    - 状态: {bet.get('status')}")
                            logger.info(f"    - 价格: {bet.get('price')}")
                            logger.info(f"    - 投注额: {bet.get('stake')}")
                            logger.info(f"    - 成交价格: {bet.get('matched_price')}")
                            logger.info(f"    - 成交金额: {bet.get('matched_stake')}")
                            logger.info(f"    - 未成交金额: {bet.get('unmatched_stake')}")

                    # 检查滑点
                    logger.info("\n📊 检查价格滑点...")
                    slippage = await check_order_slippage(self.page, order_id_str)

                    if slippage:
                        logger.info(f"\n  ✅ 滑点分析:")
                        logger.info(f"    - 总滑点: {slippage.get('total_slippage')}")
                        logger.info(f"    - 平均滑点: {slippage.get('avg_slippage')}")
                        logger.info(f"    - 平均滑点百分比: {slippage.get('avg_slippage_pct')}")
                        logger.info(f"    - 投注数量: {slippage.get('bet_count')}")

                        for bet_slip in slippage.get('bets', []):
                            logger.info(f"\n    投注 {bet_slip.get('bet_id')} ({bet_slip.get('bookie')}):")
                            logger.info(f"      - 请求价格: {bet_slip.get('requested_price')}")
                            logger.info(f"      - 成交价格: {bet_slip.get('matched_price')}")
                            logger.info(f"      - 滑点: {bet_slip.get('slippage')}")
                            logger.info(f"      - 滑点百分比: {bet_slip.get('slippage_pct')}")

                    # 更新返回值
                    order_status = final_order_state.get('state')
                    bets = result_with_bets.get('bets', []) if result_with_bets else final_order_state.get('bets', [])
                elif not found_order:
                    logger.warning(f"⚠️ 监控超时，订单未进入 Store")
                else:
                    logger.warning(f"⚠️ 监控超时，订单未完成")

            except Exception as e:
                logger.error(f"❌ 监控订单异常: {e}")

        # ========== 判定最终成功状态 ==========
        success = False
        message = '下注失败'

        if monitor_order and final_order_state:
            # 监控完成，有最终状态
            state = final_order_state.get('state')
            raw_status = final_order_state.get('raw_status', '').lower()
            closed = final_order_state.get('closed', False)
            close_reason = final_order_state.get('close_reason')
            bet_bar = final_order_state.get('bet_bar', {})
            success_count = bet_bar.get('success', 0)
            danger_count = bet_bar.get('danger', 0)
            unplaced_count = bet_bar.get('unplaced', 0)

            # 优先级 1: 检查 API 原始状态 (raw_status)
            if raw_status in ['failed', 'timed_out', 'rejected', 'cancelled']:
                success = False
                message = f'订单失败 (API状态: {raw_status}, 成功: {success_count}, 危险: {danger_count}, 未下注: {unplaced_count})'
                logger.warning(f"\n❌ {message}")

            # 优先级 2: 检查 closed 和 close_reason
            elif closed and close_reason:
                # 优先检查是否有成功的投注
                if success_count > 0:
                    # 有成功投注，即使订单关闭也算成功
                    success = True
                    message = f'下注成功 (成功: {success_count}, 危险: {danger_count}, 未下注: {unplaced_count}, 关闭原因: {close_reason})'
                    logger.info(f"\n✅ {message}")
                elif close_reason in ['timed_out', 'rejected', 'cancelled', 'expired']:
                    # 没有成功投注，且订单关闭
                    success = False
                    message = f'订单关闭但无成功投注 (原因: {close_reason}, 危险: {danger_count}, 未下注: {unplaced_count})'
                    logger.warning(f"\n❌ {message}")
                else:
                    # 其他关闭原因，没有成功投注
                    success = False
                    message = f'订单关闭但无成功投注 (原因: {close_reason}, 危险: {danger_count}, 未下注: {unplaced_count})'
                    logger.warning(f"\n⚠️ {message}")

            # 优先级 3: 检查 state 和 bet_bar
            elif state == 'FINISHED':
                if success_count > 0:
                    # 有成功的投注
                    success = True
                    message = f'下注成功 (成功: {success_count}, 危险: {danger_count}, 未下注: {unplaced_count})'
                    logger.info(f"\n✅ {message}")
                else:
                    # 订单完成但没有成功的投注
                    success = False
                    message = f'订单完成但所有投注被拒绝 (危险: {danger_count}, 未下注: {unplaced_count})'
                    logger.warning(f"\n⚠️ {message}")

            elif state == 'EXPIRED_LOCAL':
                # 订单过期
                success = False
                message = f'订单已过期 (成功: {success_count}, 危险: {danger_count}, 未下注: {unplaced_count})'
                logger.warning(f"\n⏱️ {message}")

            else:
                # 其他状态
                success = False
                message = f'订单状态异常 (state: {state}, raw_status: {raw_status})'
                logger.warning(f"\n⚠️ {message}")

        elif monitor_order and found_order and not final_order_state:
            # 监控超时，订单未完成
            success = False
            message = '监控超时，订单未完成'
            logger.warning(f"\n⚠️ {message}")

        elif monitor_order and not found_order:
            # 监控超时，订单未进入 Store
            success = False
            message = '监控超时，订单未进入 Store'
            logger.warning(f"\n⚠️ {message}")

        elif not monitor_order:
            # 未开启监控，根据初始查询结果判断
            if matched_amount > 0:
                success = True
                message = f'下注成功 (未监控，成交金额: {matched_amount})'
                logger.info(f"\n✅ {message}")
            else:
                success = False
                message = '下注状态未知 (未开启监控)'
                logger.warning(f"\n⚠️ {message}")

        # ========== 返回完整结果 ==========
        logger.info("\n" + "="*60)
        logger.info(f"{'✅' if success else '❌'} 下注流程完成")
        logger.info("="*60)

        return {
            'success': success,
            'order_id': order_id_str,
            'betslip_id': betslip_id,
            'event_id': event_id,
            'bet_type': bet_type,
            'price': best_price,
            'bookie': best_bookie,
            'stake': stake,
            'currency': currency,
            'duration': duration,
            'order_status': order_status,
            'matched_amount': matched_amount,
            'unmatched_amount': unmatched_amount,
            'bets': bets,
            'final_order_state': final_order_state,  # 最终订单状态
            'message': message,
            'order_result': order_result,
            'order_query_result': order_query_result,

            'betErrors':'',
            'status':'',
            'betting_amount':stake,
            'betting_odd': best_price,

            # 🆕 添加立即响应结果（用于第一次 WS 信号）
            'immediate_result': immediate_result,
        }

    except Exception as e:
        logger.error(f"❌ 下注流程异常: {e}", exc_info=True)
        return {
            'success': False,
            'message': f'下注流程异常: {str(e)}',
            'error': str(e)
        }
    finally:
        # 统一清理 betslip (无论成功、失败还是异常)
        if betslip_id:
            logger.info(f"\n🗑️ 清理 Betslip: {betslip_id}")
            try:
                delete_result = await delete_betslip(self.page, betslip_id)
                if delete_result.get('success'):
                    logger.info(f"✅ Betslip 已清理")
                else:
                    logger.warning(f"⚠️ Betslip 清理失败: {delete_result.get('error')}")
            except Exception as e:
                logger.warning(f"⚠️ Betslip 清理异常: {e}")


async def MonitorOrderStatus(
    self,
    order_id: str,
    betslip_id: str,
    event_id: str,
    bet_type: str,
    price: float,
    bookie: str,
    stake: float,
    currency: str,
    duration: int,
    **kwargs
) -> Dict[str, Any]:
    """
    监控订单状态（后台异步执行）
    
    这个函数会在后台运行，不阻塞主流程
    
    Args:
        order_id: 订单ID
        betslip_id: Betslip ID
        event_id: 赛事ID
        bet_type: 投注类型
        price: 价格
        bookie: 庄家
        stake: 投注金额
        currency: 货币
        duration: 订单有效期
        **kwargs: 额外参数
    
    Returns:
        订单最终状态
    """
    try:
        logger.info(f"\n🔄 [后台监控] 开始监控订单: {order_id}")
        
        # ========== Step 5: 查询订单结果 ==========
        from ..jsCodeExcutors.queries.orders.get_order import (
            get_order_by_id,
            get_order_with_bets,
            check_order_slippage
        )
        
        order_query_result = await get_order_by_id(
            page=self.page,
            order_id=order_id
        )
        
        # 处理查询结果
        if order_query_result.get('success'):
            order_status = order_query_result.get('status')
            matched_amount = order_query_result.get('matched_amount', 0)
            unmatched_amount = order_query_result.get('unmatched_amount', 0)
            bets = order_query_result.get('bets', [])
            logger.info(f"✅ [后台监控] 订单查询成功: {order_status}")
        else:
            logger.warning(f"⚠️ [后台监控] 订单查询失败")
            order_status = 'unknown'
            matched_amount = 0
            unmatched_amount = 0
            bets = []
        
        # ========== Step 6: 监控订单状态 ==========
        monitor_order = kwargs.get('monitor_order', True)
        final_order_state = None
        
        if monitor_order:
            logger.info(f"📡 [后台监控] 开始轮询订单状态...")
            timeout = duration + 5
            import time
            start_time = time.time()
            found_order = False
            
            try:
                while time.time() - start_time < timeout:
                    elapsed = int(time.time() - start_time)
                    order = await get_order_by_id(self.page, order_id)
                    
                    if order and order.get('success'):
                        found_order = True
                        state = order.get('state')
                        
                        if state in ['FINISHED', 'EXPIRED_LOCAL']:
                            logger.info(f"✅ [后台监控] 订单已结束: {state}")
                            final_order_state = order
                            break
                    
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ [后台监控] 监控异常: {e}")
        
        # ========== 判定最终成功状态 ==========
        success = False
        message = '下注失败'
        
        if monitor_order and final_order_state:
            state = final_order_state.get('state')
            bet_bar = final_order_state.get('bet_bar', {})
            success_count = bet_bar.get('success', 0)
            
            if state == 'FINISHED' and success_count > 0:
                success = True
                message = f'下注成功 (成功: {success_count})'
                logger.info(f"✅ [后台监控] {message}")
            else:
                success = False
                message = f'订单完成但无成功投注'
                logger.warning(f"⚠️ [后台监控] {message}")
        elif not monitor_order and matched_amount > 0:
            success = True
            message = f'下注成功 (成交金额: {matched_amount})'
        
        # 返回监控结果
        return {
            'success': success,
            'order_id': order_id,
            'order_status': order_status,
            'matched_amount': matched_amount,
            'unmatched_amount': unmatched_amount,
            'bets': bets,
            'final_order_state': final_order_state,
            'message': message
        }
    
    except Exception as e:
        logger.error(f"❌ [后台监控] 异常: {e}", exc_info=True)
        return {
            'success': False,
            'order_id': order_id,
            'message': f'监控异常: {str(e)}'
        }
