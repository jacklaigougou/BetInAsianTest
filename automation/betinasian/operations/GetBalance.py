# -*- coding: utf-8 -*-
"""
BetInAsian 获取余额
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def GetBalance(self, page: Any, **kwargs) -> Dict[str, Any]:
    """
    获取账户余额

    Args:
        page: 页面对象
        **kwargs: 额外参数

    Returns:
        {
            'success': bool,
            'balance': float,
            'currency': str,
            'message': str
        }
    """
    pass
