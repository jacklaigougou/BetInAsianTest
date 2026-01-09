# -*- coding: utf-8 -*-
"""
自动化操作抽象基类
定义博彩网站自动化操作的标准接口规范
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


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
            **kwargs: 其他配置参数
        """
        self.browser_controller = browser_controller
        self.page = page
        self.config = config
        self.other = kwargs

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
