# -*- coding: utf-8 -*-
"""
Pin888 请求所有赔率选项
"""
from typing import Dict, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)


async def request_all_odds_selections(
    page: Any,
    odds_id: str,
    selection_id: str,
    odds_selections_type: str,
    handler_name: str = 'pin888'
) -> Optional[Dict[str, Any]]:
    """
    发送获取所有赔率选项的请求

    Args:
        page: Playwright Page 对象
        odds_id: 完整的oddsId字符串 (例如: "123456|0|1|0|0|0")
        selection_id: 完整的selectionId字符串 (例如: "789012|123456|0|1|0|0|0|0")
        odds_selections_type: 赔率选择类型 (例如: "NORMAL")
        handler_name: Handler 名称 (用于日志)

    Returns:
        响应数据字典，包含status、response等字段，失败返回None
        {
            'status': 200,
            'response': '[{...}]',  # JSON 字符串
            'error': None
        }

    Examples:
        >>> response = await request_all_odds_selections(
        ...     page=page,
        ...     odds_id="123456|0|1|0|0|0",
        ...     selection_id="789012|123456|0|1|0|0|0|0",
        ...     odds_selections_type="NORMAL"
        ... )
        >>> response['status']
        200
    """
    try:
        # 检查必要参数
        if not odds_id:
            logger.error(f"[{handler_name}] odds_id不能为空")
            return None
        if not selection_id:
            logger.error(f"[{handler_name}] selection_id不能为空")
            return None
        if not odds_selections_type:
            logger.error(f"[{handler_name}] odds_selections_type不能为空")
            return None

        # 生成时间戳（毫秒）
        timestamp = int(time.time() * 1000)

        # 加载JS模板文件
        from utils import get_js_loader
        js_loader = get_js_loader()
        js_template = js_loader.get_js_content('pin888', 'RequestAllOddsSelections.js')

        if not js_template:
            logger.error(f"[{handler_name}] 加载 RequestAllOddsSelections.js 文件失败")
            return None

        # 替换占位符
        js_code = js_template.replace('__ODDS_ID__', f'"{odds_id}"')
        js_code = js_code.replace('__SELECTION_ID__', f'"{selection_id}"')
        js_code = js_code.replace('__ODDS_SELECTIONS_TYPE__', f'"{odds_selections_type}"')
        js_code = js_code.replace('__TIMESTAMP__', str(timestamp))

        logger.info(f"[{handler_name}] 开始发送 RequestAllOddsSelections 请求")
        logger.debug(f"[{handler_name}]   Odds ID: {odds_id}")
        logger.debug(f"[{handler_name}]   Selection ID: {selection_id}")
        logger.debug(f"[{handler_name}]   Odds Selections Type: {odds_selections_type}")

        # 包装并执行JS代码
        wrapped_code = f"(() => {{ {js_code} }})()"
        response_data = await page.evaluate(wrapped_code)

        # 检查响应
        if not response_data:
            logger.error(f"[{handler_name}] 请求返回空响应")
            return None

        if response_data.get('error'):
            logger.error(f"[{handler_name}] 请求失败: {response_data.get('error')}")
            return None

        if response_data.get('status') != 200:
            logger.error(f"[{handler_name}] 请求失败，状态码: {response_data.get('status')}")
            return None

        logger.info(f"[{handler_name}] RequestAllOddsSelections 请求成功")

        return response_data

    except Exception as e:
        logger.error(f"[{handler_name}] 执行 RequestAllOddsSelections 失败: {e}", exc_info=True)
        return None
