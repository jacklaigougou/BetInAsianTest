# -*- coding: utf-8 -*-
"""
Pin888 - 查询我的投注记录 (Request_myBets)
"""
from typing import List, Any, Optional
import logging
import json
from utils import get_js_loader

logger = logging.getLogger(__name__)


def parse_my_bets_response(raw_response, handler_name: str = "") -> List[List[Any]]:
    """
    解析 my_bets 响应数据，返回投注记录数组

    Args:
        raw_response: 原始响应数据
        handler_name: Handler 名称 (用于日志)

    Returns:
        投注记录数组，每条记录是一个列表
        格式: [[wager_id, ...其他字段..., status], ...]

    Examples:
        >>> raw = {'response': '[[[123, ...], [456, ...]]]'}
        >>> records = parse_my_bets_response(raw)
        >>> len(records)
        2
    """
    logger.debug(f"[{handler_name}] 原始响应类型: {type(raw_response)}")

    # 情况1: 直接是数组 (最理想)
    if isinstance(raw_response, list):
        logger.debug(f"[{handler_name}] 直接获得数组，长度: {len(raw_response)}")
        return raw_response

    # 情况2: 是字典，包含 'response' 字段
    if isinstance(raw_response, dict) and 'response' in raw_response:
        response_value = raw_response['response']
        logger.debug(f"[{handler_name}] 从字典中提取 response 字段，类型: {type(response_value)}")

        # 如果是字符串，尝试解析为 JSON
        if isinstance(response_value, str):
            try:
                parsed = json.loads(response_value)
                logger.debug(f"[{handler_name}] JSON 解析成功，类型: {type(parsed)}")
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                logger.error(f"[{handler_name}] JSON 解析失败")
                return []

        # 如果已经是数组或对象，直接返回
        return response_value if isinstance(response_value, list) else []

    # 情况3: 其他格式，返回空数组
    logger.warning(f"[{handler_name}] 无法识别的格式，返回空数组")
    return []


async def request_my_bets(
    page,
    handler_name: str = ""
) -> Optional[List[List[Any]]]:
    """
    查询我的投注记录 (使用 Request_myBets.js)

    Args:
        page: Playwright Page 对象
        handler_name: Handler 名称 (用于日志)

    Returns:
        投注记录数组，每条记录是一个列表
        格式: [[wager_id, ...其他字段..., status], ...]
        或 None (失败时)

    Examples:
        >>> bets = await request_my_bets(page, handler_name="pin888_handler_1")
        >>> len(bets)
        5
        >>> bets[0][0]  # 第一条记录的 wager_id
        123456
    """
    try:
        # 1. 加载 JS 模板
        js_loader = get_js_loader()
        js_template = js_loader.get_js_content('pin888', 'Request_myBets.js')

        if not js_template:
            logger.error(f"[{handler_name}] 加载 Request_myBets.js 失败")
            return None

        # 2. 执行 JS 代码
        wrapped_code = f"(() => {{ {js_template} }})()"
        raw_response = await page.evaluate(wrapped_code)

        # 3. 解析响应
        my_bets_response = parse_my_bets_response(raw_response, handler_name)

        logger.debug(f"[{handler_name}] 获取投注记录数: {len(my_bets_response)}")
        return my_bets_response

    except Exception as e:
        logger.error(f"[{handler_name}] 查询投注记录失败: {e}", exc_info=True)
        return None
