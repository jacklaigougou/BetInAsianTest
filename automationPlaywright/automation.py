# -*- coding: utf-8 -*-
"""
自动化操作统一接口
支持多个博彩网站（Pin888, BetInAsian等）
"""
from typing import Any, Dict


class Automation:
    """自动化操作统一接口类"""

    def __init__(self, platform: str = "pin888", browser_controller: Any = None, page: Any = None, **kwargs):
        """
        初始化自动化操作

        Args:
            platform: 平台类型 ("pin888" 或 "betinasian")
            browser_controller: 浏览器控制器对象
            page: 页面对象
            **kwargs: 其他配置参数
        """
        self.platform = platform
        self.browser_controller = browser_controller
        self.page = page
        self.config = kwargs

        # 根据平台类型初始化对应的自动化实现
        if platform == "pin888":
            from .pin888.pin888_automation import Pin888Automation
            self._automation = Pin888Automation(browser_controller, page, **kwargs)
        elif platform == "betinasian":
            from .betinasian.betinasian_automation import BetInAsianAutomation
            self._automation = BetInAsianAutomation(browser_controller, page, **kwargs)
        else:
            raise ValueError(
                f"不支持的平台类型: {platform}\n"
                f"支持的类型: pin888, betinasian"
            )

    async def prepare_work(self, **kwargs) -> Dict[str, Any]:
        """
        准备工作

        Args:
            **kwargs: 额外参数

        Returns:
            准备工作结果字典
        """
        return await self._automation.prepare_work(**kwargs)

    async def GetBalance(self, **kwargs) -> Dict[str, Any]:
        """
        获取账户余额

        Args:
            **kwargs: 额外参数

        Returns:
            余额信息字典
        """
        return await self._automation.GetBalance(**kwargs)

    async def GetOdd(self, dispatch_message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        获取赔率

        Args:
            dispatch_message: 调度消息,包含所有必要的参数

        Returns:
            赔率信息字典
        """
        return await self._automation.GetOdd(dispatch_message, **kwargs)

    async def BettingOrder(
        self,
        dispatch_message: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        下注订单

        Args:
            dispatch_message: 调度消息,包含所有必要的参数

        Returns:
            订单信息字典
        """
        return await self._automation.BettingOrder(dispatch_message, **kwargs)

    async def SupplementaryOrder(self, dispatch_message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        补充订单

        Args:
            dispatch_message: 调度消息,包含所有必要的参数

        Returns:
            操作结果字典
        """
        return await self._automation.SupplementaryOrder(dispatch_message, **kwargs)
