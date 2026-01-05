# -*- coding: utf-8 -*-
"""
BetInAsian 补充订单
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def SupplementaryOrder(self, dispatch_message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    补充订单

    对已存在的订单进行补充操作,例如:
    - 追加投注金额
    - 修改投注选项
    - 取消订单

    Args:
        dispatch_message: 调度消息,包含所有必要的参数
        **kwargs: 额外参数

    Returns:
        {
            'success': bool,
            'message': str,
            'data': Any
        }
    """
    pass
