# -*- coding: utf-8 -*-
"""
Close Order - 关闭订单
"""
from typing import Dict, Any
import logging
from utils.js_loader import get_js_loader

logger = logging.getLogger(__name__)


async def close_order(
    page,
    order_id: int
) -> Dict[str, Any]:
    """
    关闭订单

    Args:
        page: Playwright Page 对象
        order_id: 订单ID (例如: 1050357659)

    Returns:
        {
            'success': True/False,
            'status': int,
            'statusText': str,
            'data': dict/None,
            'timestamp': str,
            'request': {
                'url': str,
                'method': 'POST',
                'body': dict
            }
        }

    Examples:
        >>> result = await close_order(page, 1050357659)
        >>> if result['success']:
        ...     print("订单关闭成功")
    """
    try:
        logger.info(f"关闭订单: {order_id}")

        # Load JS function from JSLoader
        js_loader = get_js_loader()
        js_code = js_loader.get_js_content("betinasian", "httpRequest/close_order.js")

        if not js_code:
            raise FileNotFoundError("close_order.js not found in JSLoader cache")

        # Wrap JS code and call closeOrder function
        wrapped_js = f"""
async function(orderId) {{
{js_code}

    // Call the closeOrder function
    return await closeOrder(orderId);
}}
"""

        # Execute request
        result = await page.evaluate(wrapped_js, order_id)

        # Handle None result (when JS returns undefined)
        if result is None:
            logger.error(f"❌ closeOrder 返回 null/undefined")
            return {
                'success': False,
                'error': 'closeOrder returned null/undefined',
                'status': 0
            }

        if result.get('success'):
            logger.info(f"✅ 订单关闭成功: {order_id}")
        else:
            logger.error(f"❌ 订单关闭失败: {result.get('error', 'Unknown error')}")

        return result

    except Exception as e:
        logger.error(f"❌ 关闭订单异常: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'status': 0
        }
