# -*- coding: utf-8 -*-
"""
BetInAsian 下注订单

完整的下单流程：
1. 调用 GetOdd 获取 betslip 和价格信息
2. 获取最佳价格（优先使用 GetOdd 返回值，失败则从 Store 获取）
3. 提交订单
4. 等待订单数据（可选）
5. 查询订单结果
"""
from typing import Dict, Any
import logging
import asyncio

logger = logging.getLogger(__name__)


async def BettingOrder(
    self,
    dispatch_message: Dict[str, Any],
    stake: float = 10.0,
    currency: str = "GBP",
    duration: int = 30,
    required_amount: float = 10.0,
    required_currency: str = "GBP",
    wait_for_order: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    下注订单（完整流程）

    Args:
        dispatch_message: {
            'spider_sport_type': 'basket',           # 运动类型
            'spider_home': 'Manchester United',      # 主队
            'spider_away': 'Chelsea',                # 客队
            'spider_market_id': '17',                # Spider market ID
            'spider_handicap_value': -5.5            # 让分值 (可选)
        }
        stake: 投注金额 (默认: 10.0)
        currency: 货币 (默认: "GBP")
        duration: 订单有效期（秒，默认: 30）
        required_amount: PMM 查询所需金额 (默认: 10.0)
        required_currency: PMM 查询所需货币 (默认: "GBP")
        wait_for_order: 是否等待订单数据 (默认: True)
        **kwargs: 额外参数

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
            'message': str,
            'odd_result': dict,
            'order_result': dict,
            'order_query_result': dict
        }

    Examples:
        >>> # 基本调用
        >>> result = await BettingOrder(
        ...     self,
        ...     {
        ...         'spider_sport_type': 'basket',
        ...         'spider_home': 'Lakers',
        ...         'spider_away': 'Warriors',
        ...         'spider_market_id': '17',
        ...         'spider_handicap_value': -5.5
        ...     }
        ... )

        >>> # 自定义投注金额和货币
        >>> result = await BettingOrder(
        ...     self,
        ...     {...},
        ...     stake=20.0,
        ...     currency='USD',
        ...     duration=60
        ... )
    """
    try:
        logger.info("="*60)
        logger.info("🎯 开始下注流程")
        logger.info("="*60)

        # ========== Step 1: 获取 Betslip 和价格信息 ==========
        logger.info("\n📋 Step 1: 获取 Betslip 和价格信息...")

        # 1.1 从 dispatch_message 提取 order_id
        bet_data = dispatch_message.get('bet_data', {})
        order_id = bet_data.get('order_id', '')

        # 1.2 尝试从 order_record 获取缓存数据
        if order_id and order_id in self.order_record:
            # 从缓存获取
            cached_data = self.order_record[order_id]
            logger.info(f"✅ 从 order_record 获取缓存数据")
            logger.info(f"  - Order ID: {order_id}")
            logger.info(f"  - Handler: {cached_data.get('handler_name')}")
            logger.info(f"  - Betslip ID: {cached_data.get('betslip_id')}")
            logger.info(f"  - Event: {cached_data.get('home')} vs {cached_data.get('away')}")

            # 提取关键信息
            betslip_id = cached_data.get('betslip_id')
            event_id = cached_data.get('event_id')
            bet_type = cached_data.get('bet_type')

            # 构造 best_price_info（与 GetOdd 返回格式一致）
            best_price_info = {
                'success': True,
                'price': cached_data.get('odds'),
                'bookie': cached_data.get('bookie'),
                'available': cached_data.get('max_stake')
            }

        else:
            # 1.3 降级：重新调用 GetOdd
            if order_id:
                logger.warning(f"⚠️ order_record 中没有数据（order_id: {order_id}），重新调用 GetOdd")
            else:
                logger.warning(f"⚠️ dispatch_message 中没有 order_id，重新调用 GetOdd")

            odd_result = await self.GetOdd(
                dispatch_message=dispatch_message,
                required_amount=required_amount,
                required_currency=required_currency
            )

            if not odd_result.get('success'):
                logger.error(f"❌ GetOdd 失败: {odd_result.get('message')}")
                return {
                    'success': False,
                    'message': f"GetOdd 失败: {odd_result.get('message')}",
                    'odd_result': odd_result
                }

            # 从 GetOdd 返回值提取信息（注意：GetOdd 现在返回 Pin888 格式）
            # 需要从 order_record 重新获取详细信息
            order_id = odd_result.get('order_id', '')
            if order_id and order_id in self.order_record:
                cached_data = self.order_record[order_id]
                betslip_id = cached_data.get('betslip_id')
                event_id = cached_data.get('event_id')
                bet_type = cached_data.get('bet_type')
                best_price_info = {
                    'success': True,
                    'price': cached_data.get('odds'),
                    'bookie': cached_data.get('bookie'),
                    'available': cached_data.get('max_stake')
                }
            else:
                logger.error(f"❌ GetOdd 成功但无法从 order_record 获取数据")
                return {
                    'success': False,
                    'message': 'GetOdd 成功但无法从 order_record 获取数据'
                }

        logger.info(f"✅ 数据获取成功:")
        logger.info(f"  - Betslip ID: {betslip_id}")
        logger.info(f"  - Event ID: {event_id}")
        logger.info(f"  - Bet Type: {bet_type}")

        # ========== Step 2: 获取最佳价格 ==========
        logger.info("\n💰 Step 2: 获取最佳价格...")

        best_price = None
        best_bookie = None

        # 优先使用缓存的价格信息
        if best_price_info and best_price_info.get('success'):
            best_price = best_price_info.get('price')
            best_bookie = best_price_info.get('bookie')
            logger.info(f"✅ 使用缓存价格:")
            logger.info(f"  - Price: {best_price}")
            logger.info(f"  - Bookie: {best_bookie}")
        else:
            # 降级方案：直接从 Store 获取最高价格
            logger.warning(f"⚠️ 缓存未返回价格信息，使用降级方案...")

            highest_price_data = await self.page.evaluate(f"""
                () => {{
                    const betslip = window.pmmStore.store.get("{betslip_id}");
                    if (!betslip) return null;

                    let highestPrice = 0;
                    let highestBookie = null;

                    for (const [bookie, data] of betslip.bookies) {{
                        if (data.status.code === 'success' && data.top_price > highestPrice) {{
                            highestPrice = data.top_price;
                            highestBookie = bookie;
                        }}
                    }}

                    return {{ price: highestPrice, bookie: highestBookie }};
                }}
            """)

            if highest_price_data:
                best_price = highest_price_data.get('price')
                best_bookie = highest_price_data.get('bookie')
                logger.info(f"✅ 从 Store 获取最高价格:")
                logger.info(f"  - Price: {best_price}")
                logger.info(f"  - Bookie: {best_bookie}")
            else:
                logger.error("❌ 无法获取价格信息")
                return {
                    'success': False,
                    'message': '无法获取价格信息',
                    'betslip_id': betslip_id,
                    'odd_result': odd_result
                }

        if not best_price or best_price <= 0:
            logger.error(f"❌ 价格无效: {best_price}")
            return {
                'success': False,
                'message': f'价格无效: {best_price}',
                'betslip_id': betslip_id,
                'price': best_price,
                'odd_result': odd_result
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
                'odd_result': odd_result,
                'order_result': order_result
            }

        # 提取 order_id
        order_id = order_result.get('data', {}).get('data', {}).get('order_id')
        if not order_id:
            logger.error("❌ 无法从响应中提取 order_id")
            return {
                'success': False,
                'message': '下单成功但无法提取 order_id',
                'betslip_id': betslip_id,
                'price': best_price,
                'bookie': best_bookie,
                'stake': stake,
                'currency': currency,
                'odd_result': odd_result,
                'order_result': order_result
            }

        order_id_str = str(order_id)
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
            'final_order_state': final_order_state,  # 新增：最终订单状态
            'message': '下注成功',
            'odd_result': odd_result,
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
