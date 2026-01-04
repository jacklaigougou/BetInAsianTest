# -*- coding: utf-8 -*-
"""
BetInAsian 补充订单
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def SupplementaryOrder(self, page: Any, order_id: str, **kwargs) -> Dict[str, Any]:
    """
    补充订单

    对已存在的订单进行补充操作,例如:
    - 追加投注金额
    - 修改投注选项
    - 取消订单

    Args:
        page: 页面对象
        order_id: 订单ID
        **kwargs: 额外参数
            - action: 操作类型(add_amount, cancel, modify 等)
            - amount: 追加金额(如果适用)

    Returns:
        {
            'success': bool,
            'order_id': str,
            'action': str,
            'message': str
        }
    """
    pass
