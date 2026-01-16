# -*- coding: utf-8 -*-
"""
自动化操作抽象基类
定义博彩网站自动化操作的标准接口规范
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import math
import logging

logger = logging.getLogger(__name__)


class AutomationBase(ABC):
    """
    自动化操作抽象基类
    
    标准接口：
    1. prepare_work - 准备工作
    2. GetBalance - 获取余额
    3. GetOdd - 获取赔率
    4. BettingOrder - 下注订单
    5. SupplementaryOrder - 补充订单
    """

    def __init__(self, browser_controller: Any = None, page: Any = None, config: Dict[str, Any] = None, **kwargs):
        """
        初始化自动化操作基类

        Args:
            browser_controller: 浏览器控制器对象
            page: 页面对象 (Playwright Page 或 Puppeteer Page)
            config: 配置字典 (包含 handler_name, platform_name, balance 等)
            **kwargs: 其他配置参数 (兼容旧接口)
        """
        self.browser_controller = browser_controller
        self.page = page
        self.config = config or {}

        # ✅ 从 config 提取 handler_name (优先)
        self.handler_name = self.config.get('handler_name', 'unknown')

        # ✅ 兼容旧架构: 也支持从 kwargs 提取
        if 'handler_name' in kwargs:
            self.handler_name = kwargs['handler_name']

        # 保存其他参数
        self.other = kwargs
        print(f"[Pin888Automation] init config = {self.config}")

    async def check_and_adjust_balance(
        self,
        balance: float,
        bet_amount: float,
        decimal_places: int = 1,
        handler_name: Optional[str] = None
    ) -> Optional[float]:
        """
        检查余额并调整下注金额

        Args:
            balance: 当前余额
            bet_amount: 原始下注金额
            decimal_places: 保留小数位数（默认: 1）
            handler_name: 处理器名称（可选，默认使用 self.handler_name）

        Returns:
            调整后的下注金额，或 None (余额无效)

        Examples:
            >>> # 保留1位小数
            >>> adjusted = await self.check_and_adjust_balance(100.0, 150.0, decimal_places=1)
            >>> adjusted
            100.0

            >>> # 保留2位小数
            >>> adjusted = await self.check_and_adjust_balance(100.55, 150.0, decimal_places=2)
            >>> adjusted
            100.55
        """
        _handler_name = handler_name or self.handler_name

        # 1. 验证余额
        if balance is None or balance < 0:
            logger.error(f"[{_handler_name}] 余额无效: {balance}")
            return None

        logger.info(f"[{_handler_name}] 💰 当前余额: {balance:.{decimal_places}f}")

        # 2. 余额不足时自动调整
        if balance < bet_amount:
            # 根据指定的小数位数向下取整
            multiplier = 10 ** decimal_places
            adjusted_amount = math.floor(balance * multiplier) / multiplier

            logger.warning(
                f"[{_handler_name}] ⚠️ 余额不足，调整下注金额: "
                f"{bet_amount:.{decimal_places}f} → {adjusted_amount:.{decimal_places}f} "
                f"(真实余额: {balance:.{decimal_places}f})"
            )
            return adjusted_amount

        return bet_amount

    @abstractmethod
    async def prepare_work(self, **kwargs) -> Dict[str, Any]:
        """
        准备工作

        执行自动化操作前的准备工作，例如：
        - 登录网站
        - 导航到指定页面
        - 初始化必要的数据

        Args:
            **kwargs: 额外参数

        Returns:
            {
                'success': bool,      # 是否成功
                'message': str,       # 结果消息
                'data': Any,          # 额外数据
            }
        """
        pass

    @abstractmethod
    async def GetBalance(self, **kwargs) -> Dict[str, Any]:
        """
        获取账户余额

        Args:
            **kwargs: 额外参数

        Returns:
            {
                'success': bool,      # 是否成功
                'balance': float,     # 余额
                'currency': str,      # 货币单位
                'message': str,       # 结果消息
            }
        """
        pass

    @abstractmethod
    async def GetOdd(self, dispatch_message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        获取赔率

        Args:
            dispatch_message: 调度消息,包含所有必要的参数
            **kwargs: 额外参数

        Returns:
            {
                'success': bool,      # 是否成功
                'odd': float,         # 赔率
                'message': str,       # 结果消息
                'data': Any,          # 额外数据
            }
        """
        pass

    @abstractmethod
    async def BettingOrder(
        self,
        dispatch_message: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        下注订单

        Args:
            dispatch_message: 调度消息,包含所有必要的参数
            **kwargs: 额外参数

        Returns:
            {
                'success': bool,      # 是否成功
                'order_id': str,      # 订单ID
                'message': str,       # 结果消息
                'data': Any,          # 额外数据
            }
        """
        pass

    @abstractmethod
    async def SupplementaryOrder(self, dispatch_message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        补充订单

        对已存在的订单进行补充操作，例如：
        - 追加投注金额
        - 修改投注选项
        - 取消订单

        Args:
            dispatch_message: 调度消息,包含所有必要的参数
            **kwargs: 额外参数

        Returns:
            {
                'success': bool,      # 是否成功
                'message': str,       # 结果消息
                'data': Any,          # 额外数据
            }
        """
        pass


__all__ = ['AutomationBase']
