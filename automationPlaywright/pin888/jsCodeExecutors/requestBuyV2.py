# -*- coding: utf-8 -*-
"""
Pin888 - 发送下注请求 (RequestBuyV2)
"""
from typing import Dict, Any, Optional
import logging
from utils import get_js_loader

logger = logging.getLogger(__name__)


async def request_buy_v2(
    page,
    stake: float,
    odds: str,
    odds_id: str,
    selection_id: str,
    handler_name: str = ""
) -> Optional[Dict[str, Any]]:
    """
    发送下注请求 (使用 RequestBuyV2.js)

    Args:
        page: Playwright Page 对象
        stake: 下注金额
        odds: 赔率
        odds_id: 赔率 ID
        selection_id: 选择 ID
        handler_name: Handler 名称 (用于日志)

    Returns:
        {
            'status': 200,
            'response': str,  # JSON 字符串
            'error': str      # 错误信息 (如果有)
        }
        或 None (失败时)

    Examples:
        >>> response = await request_buy_v2(
        ...     page=page,
        ...     stake=10.5,
        ...     odds="1.95",
        ...     odds_id="123456",
        ...     selection_id="789012",
        ...     handler_name="pin888_handler_1"
        ... )
        >>> response['status']
        200
    """
    try:
        # 1. 加载 JS 模板
        js_loader = get_js_loader()
        js_template = js_loader.get_js_content('pin888', 'RequestBuyV2.js')

        if not js_template:
            logger.error(f"[{handler_name}] 加载 RequestBuyV2.js 失败")
            return None

        # 2. 替换占位符
        js_code = js_template.replace('__STAKE__', str(stake))
        js_code = js_code.replace('__ODDS__', str(odds))
        js_code = js_code.replace('__ODDS_ID__', str(odds_id))
        js_code = js_code.replace('__SELECTION_ID__', str(selection_id))

        logger.info(f"[{handler_name}] 发送下注请求: stake={stake}, odds={odds}, odds_id={odds_id}")

        # 3. 执行 JS 代码
        wrapped_code = f"(() => {{ {js_code} }})()"
        response = await page.evaluate(wrapped_code)

        # 4. 验证响应
        if not response:
            logger.error(f"[{handler_name}] 下注请求返回空响应")
            return None

        if response.get('error'):
            logger.error(f"[{handler_name}] 下注失败: {response.get('error')}")
            return response

        if response.get('status') != 200:
            logger.error(f"[{handler_name}] 下注失败，HTTP状态码: {response.get('status')}")
            return response

        logger.info(f"[{handler_name}] 下注请求成功，状态码: {response.get('status')}")
        return response

    except Exception as e:
        logger.error(f"[{handler_name}] 执行下注请求失败: {e}", exc_info=True)
        return None
