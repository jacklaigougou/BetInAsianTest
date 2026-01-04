# -*- coding: utf-8 -*-
"""
自动化操作统一接口
支持多个博彩网站（Pin888, BetInAsian等）
"""
from typing import Any, Dict


class Automation:
    """自动化操作统一接口类"""

    def __init__(self, site: str = "pin888", browser_controller: Any = None, **kwargs):
        """
        初始化自动化操作

        Args:
            site: 网站类型 ("pin888" 或 "betinasian")
            browser_controller: 浏览器控制器对象
            **kwargs: 其他配置参数
        """
        self.site = site
        self.browser_controller = browser_controller
        self.config = kwargs

        # 根据网站类型初始化对应的自动化实现
        if site == "pin888":
            from .pin888.pin888_automation import Pin888Automation
            self._automation = Pin888Automation(browser_controller, **kwargs)
        elif site == "betinasian":
            from .betinasian.betinasian_automation import BetInAsianAutomation
            self._automation = BetInAsianAutomation(browser_controller, **kwargs)
        else:
            raise ValueError(
                f"不支持的网站类型: {site}\n"
                f"支持的类型: pin888, betinasian"
            )

    async def prepare_work(self, page: Any, **kwargs) -> Dict[str, Any]:
        """
        准备工作

        Args:
            page: 页面对象

        Returns:
            准备工作结果字典
        """
        return await self._automation.prepare_work(page, **kwargs)

    async def GetBalance(self, page: Any, **kwargs) -> Dict[str, Any]:
        """
        获取账户余额

        Args:
            page: 页面对象

        Returns:
            余额信息字典
        """
        return await self._automation.GetBalance(page, **kwargs)

    async def GetOdd(self, page: Any, event_id: str, bet_type: str, **kwargs) -> Dict[str, Any]:
        """
        获取赔率

        Args:
            page: 页面对象
            event_id: 赛事ID
            bet_type: 投注类型

        Returns:
            赔率信息字典
        """
        return await self._automation.GetOdd(page, event_id, bet_type, **kwargs)

    async def BettingOrder(
        self,
        page: Any,
        event_id: str,
        bet_type: str,
        amount: float,
        odd: float,
        **kwargs
    ) -> Dict[str, Any]:
        """
        下注订单

        Args:
            page: 页面对象
            event_id: 赛事ID
            bet_type: 投注类型
            amount: 投注金额
            odd: 赔率

        Returns:
            订单信息字典
        """
        return await self._automation.BettingOrder(page, event_id, bet_type, amount, odd, **kwargs)

    async def SupplementaryOrder(self, page: Any, order_id: str, **kwargs) -> Dict[str, Any]:
        """
        补充订单

        Args:
            page: 页面对象
            order_id: 订单ID

        Returns:
            操作结果字典
        """
        return await self._automation.SupplementaryOrder(page, order_id, **kwargs)
