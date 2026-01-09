# -*- coding: utf-8 -*-
"""
BetInAsian 网站自动化操作实现
"""
from typing import Any, Dict
import logging
from ..interface import AutomationBase

# 导入操作方法
from .operations import (
    prepare_work,
    GetBalance,
    GetOdd,
    BettingOrder,
    SupplementaryOrder,
)

logger = logging.getLogger(__name__)


class BetInAsianAutomation(AutomationBase):
    """BetInAsian 网站自动化操作实现"""

    def __init__(self, browser_controller: Any = None, page: Any = None,config: Dict[str, Any] = None, **kwargs):
        """
        初始化 BetInAsian 自动化操作

        Args:
            browser_controller: 浏览器控制器对象
            page: 页面对象
            **kwargs: 其他配置参数
        """
        super().__init__(browser_controller, page,config, **kwargs)
        logger.info("初始化 BetInAsian 自动化操作")

    # ==================== 绑定操作方法 ====================
    prepare_work = prepare_work
    GetBalance = GetBalance
    GetOdd = GetOdd
    BettingOrder = BettingOrder
    SupplementaryOrder = SupplementaryOrder
