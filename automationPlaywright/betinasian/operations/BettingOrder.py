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

logger = logging.getLogger(__name__)


async def BettingOrder(
    self,
    dispatch_message: Dict[str, Any],
    stake: float = 5,
    currency: str = "GBP",
    duration: int = 30,
    required_amount: float = 10.0,
    required_currency: str = "GBP",
    wait_for_order: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    下注订单（简化流程）

    注意：调用此函数前必须先调用 GetOdd 创建 betslip 并存储到 order_record

    Args:
        dispatch_message: {
            'bet_data': {
                'order_id': str  # 必需，用于从 order_record 获取 betslip_id
            }
        }
        stake: 投注金额 (默认: 2.0)
        currency: 货币 (默认: "GBP")
        duration: 订单有效期（秒，默认: 30）
        required_amount: PMM 查询所需金额 (默认: 10.0)
        required_currency: PMM 查询所需货币 (默认: "GBP")
        wait_for_order: 是否等待订单数据 (默认: True)
        **kwargs: 额外参数
            - monitor_order: 是否监控订单状态 (默认: True)

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
        >>> # 再调用 BettingOrder
        >>> result = await BettingOrder(
        ...     self,
        ...     dispatch_message,
        ...     stake=10.0,
        ...     currency='GBP',
        ...     duration=30
        ... )
    """
    try:
        logger.info("="*60)
        logger.info("🎯 开始下注流程")
        logger.info("="*60)

        # ========== Step 1: 从 order_record 获取 betslip_id ==========
        logger.info("\n📋 Step 1: 从 order_record 获取 betslip_id...")

        bet_data = dispatch_message.get('bet_data', {})
        order_id = bet_data.get('order_id', '')

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

        logger.info(f"✅ 从 order_record 获取数据成功:")
        logger.info(f"  - Order ID: {order_id}")
        logger.info(f"  - Handler: {cached_data.get('handler_name')}")
        logger.info(f"  - Betslip ID: {betslip_id}")
        logger.info(f"  - Event: {cached_data.get('home')} vs {cached_data.get('away')}")
        logger.info(f"  - Event ID: {event_id}")
        logger.info(f"  - Bet Type: {bet_type}")

        # ========== Step 2: 实时查询最新价格 ==========
        logger.info("\n💰 Step 2: 实时查询最新价格...")
        logger.info(f"  - Betslip ID: {betslip_id}")
        logger.info(f"  - Required Amount: {required_amount} {required_currency}")

        from ..jsCodeExcutors.queries.pmm import get_price_by_betslip_id

        best_price_result = await get_price_by_betslip_id(
            page=self.page,
            betslip_id=betslip_id,
            required_amount=required_amount,
            required_currency=required_currency
        )

        if not best_price_result.get('success'):
            logger.error(f"❌ 获取价格失败: {best_price_result.get('reason')}")
            return {
                'success': False,
                'message': f"获取价格失败: {best_price_result.get('reason')}",
                'betslip_id': betslip_id,
                'order_id': order_id
            }

        best_price = best_price_result.get('price')
        best_bookie = best_price_result.get('bookie')
        available = best_price_result.get('available')

        logger.info(f"✅ 获取最新价格成功:")
        logger.info(f"  - Price: {best_price}")
        logger.info(f"  - Bookie: {best_bookie}")
        logger.info(f"  - Available: {available}")

        if not best_price or best_price <= 0:
            logger.error(f"❌ 价格无效: {best_price}")
            return {
                'success': False,
                'message': f'价格无效: {best_price}',
                'betslip_id': betslip_id,
                'price': best_price,
                'order_id': order_id
            }

        # ========== Step 3: 提交订单 ==========
        logger.info("\n📤 Step 3: 提交订单...")
        logger.info(f"  - Betslip ID: {betslip_id}")
        logger.info(f"  - Price: {best_price} (来自 {best_bookie})")
        logger.info(f"  - Stake: {stake} {currency}")
        logger.info(f"  - Duration: {duration} seconds")

        from ..jsCodeExcutors.http_executors import place_order

        order_result = await place_order(
            page=self.page,
            betslip_id=betslip_id,
            price=best_price,
            stake=stake,
            currency=currency,
            duration=duration
        )

        if not order_result.get('success'):
            logger.error(f"❌ 下单失败: {order_result.get('error')}")
            return {
                'success': False,
                'message': f"下单失败: {order_result.get('error')}",
                'betslip_id': betslip_id,
                'price': best_price,
                'bookie': best_bookie,
                'stake': stake,
                'currency': currency,
                'order_result': order_result
            }

        # 提取 order_id
        placed_order_id = order_result.get('data', {}).get('data', {}).get('order_id')
        if not placed_order_id:
            logger.error("❌ 无法从响应中提取 order_id")
            return {
                'success': False,
                'message': '下单成功但无法提取 order_id',
                'betslip_id': betslip_id,
                'price': best_price,
                'bookie': best_bookie,
                'stake': stake,
                'currency': currency,
                'order_result': order_result
            }

        order_id_str = str(placed_order_id)
        logger.info(f"✅ 订单提交成功:")
        logger.info(f"  - Order ID: {order_id_str}")
        logger.info(f"  - Status: {order_result.get('status')}")

        # ========== Step 4: 等待订单数据（可选） ==========
        if wait_for_order:
            logger.info(f"\n⏳ Step 4: 等待订单数据...")
            await asyncio.sleep(2)  # 等待 WebSocket 接收订单状态
            logger.info("✅ 等待完成")

        # ========== Step 5: 查询订单结果 ==========
        logger.info(f"\n🔍 Step 5: 查询订单结果...")

        from ..jsCodeExcutors.queries.orders.get_order import get_order_by_id

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
                    logger.info(f"\n📊 最终订单状态:")
                    logger.info(f"  - State: {final_order_state.get('state')}")
                    logger.info(f"  - Raw Status: {final_order_state.get('raw_status')}")

                    bet_bar = final_order_state.get('bet_bar', {})
                    logger.info(f"  - Success: {bet_bar.get('success', 0)}")
                    logger.info(f"  - In Progress: {bet_bar.get('inprogress', 0)}")
                    logger.info(f"  - Danger: {bet_bar.get('danger', 0)}")
                    logger.info(f"  - Unplaced: {bet_bar.get('unplaced', 0)}")

                    # 更新返回值
                    order_status = final_order_state.get('state')
                    bets = final_order_state.get('bets', [])
                elif not found_order:
                    logger.warning(f"⚠️ 监控超时，订单未进入 Store")
                else:
                    logger.warning(f"⚠️ 监控超时，订单未完成")

            except Exception as e:
                logger.error(f"❌ 监控订单异常: {e}")

        # ========== 返回完整结果 ==========
        logger.info("\n" + "="*60)
        logger.info("✅ 下注流程完成")
        logger.info("="*60)

        return {
            'success': True,
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
            'message': '下注成功',
            'order_result': order_result,
            'order_query_result': order_query_result
        }

    except Exception as e:
        logger.error(f"❌ 下注流程异常: {e}", exc_info=True)
        return {
            'success': False,
            'message': f'下注流程异常: {str(e)}',
            'error': str(e)
        }
