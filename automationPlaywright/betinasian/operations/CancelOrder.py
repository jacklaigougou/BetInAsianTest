# -*- coding: utf-8 -*-
"""
BetInAsian 取消订单
"""
from typing import Dict, Any
import logging
from ..jsCodeExcutors.http_executors.close_order import close_order

logger = logging.getLogger(__name__)


async def CancelOrder(self, **kwargs) -> Dict[str, Any]:
    """
    取消订单

    从 dispatch 接收取消订单请求，执行订单取消操作

    Args:
        **kwargs:
            - order_id: 订单ID (dispatch 分配的订单ID)
            - ticket_id: betslip_id
            - betting_amount: 下注金额
            - betting_odd: 下注赔率
            - reason: 取消原因 (例如: "pin888_failed")

    Returns:
        {
            'success': bool,
            'order_id': str,
            'placed_order_id': int,
            'message': str,
            'reason': str,
            'handler_name': str
        }

    Examples:
        >>> result = await self.CancelOrder(
        ...     order_id="ORDER_123",
        ...     ticket_id="betslip_456",
        ...     betting_amount=100,
        ...     betting_odd=1.95,
        ...     reason="pin888_failed"
        ... )
    """
    handler_name = self.handler_name
    order_id = kwargs.get('order_id')
    ticket_id = kwargs.get('ticket_id')
    betting_amount = kwargs.get('betting_amount')
    betting_odd = kwargs.get('betting_odd')
    reason = kwargs.get('reason', 'unknown')

    try:
        logger.info(f"[{handler_name}] 开始取消订单...")
        logger.info(f"  - Order ID: {order_id}")
        logger.info(f"  - Ticket ID: {ticket_id}")
        logger.info(f"  - Reason: {reason}")

        # ========== Step 1: 从 order_record 获取 placed_order_id ==========
        if not order_id or order_id not in self.order_record:
            logger.error(f"❌ order_record 中没有数据（order_id: {order_id}）")
            return {
                'success': False,
                'order_id': order_id,
                'message': 'order_record 中没有该订单数据',
                'reason': reason,
                'handler_name': handler_name
            }

        cached_data = self.order_record[order_id]
        placed_order_id = cached_data.get('placed_order_id')

        if not placed_order_id:
            logger.error(f"❌ order_record 中缺少 placed_order_id")
            return {
                'success': False,
                'order_id': order_id,
                'message': 'order_record 中缺少 placed_order_id',
                'reason': reason,
                'handler_name': handler_name
            }

        logger.info(f"  - Placed Order ID: {placed_order_id}")

        # ========== Step 2: 调用 close_order 执行取消 ==========
        logger.info("\n🚫 Step 2: 执行取消订单...")

        close_result = await close_order(self.page, placed_order_id)

        if not close_result.get('success'):
            error_msg = close_result.get('error', 'Unknown error')
            logger.error(f"❌ 取消订单失败: {error_msg}")
            return {
                'success': False,
                'order_id': order_id,
                'placed_order_id': placed_order_id,
                'message': f'取消订单失败: {error_msg}',
                'reason': reason,
                'handler_name': handler_name,
                'close_result': close_result
            }

        # ========== Step 3: 返回成功结果 ==========
        logger.info(f"✅ 订单取消成功: {placed_order_id}")

        return {
            'success': True,
            'order_id': order_id,
            'placed_order_id': placed_order_id,
            'ticket_id': ticket_id,
            'betting_amount': betting_amount,
            'betting_odd': betting_odd,
            'message': '订单取消成功',
            'reason': reason,
            'handler_name': handler_name,
            'close_result': close_result
        }

    except Exception as e:
        logger.error(f"❌ 取消订单异常: {e}", exc_info=True)
        return {
            'success': False,
            'order_id': order_id,
            'message': f'取消订单异常: {str(e)}',
            'reason': reason,
            'handler_name': handler_name
        }
