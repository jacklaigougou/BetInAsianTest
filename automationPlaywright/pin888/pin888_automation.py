# -*- coding: utf-8 -*-
"""
Pin888 网站自动化操作实现
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


class Pin888Automation(AutomationBase):
    """Pin888 网站自动化操作实现"""

    # 类变量: 存储所有 handler 的共享信息 (如余额)
    handler_info: Dict[str, Dict[str, Any]] = {}

    def __init__(self, browser_controller: Any = None, page: Any = None, config: Dict[str, Any] = None, **kwargs):
        """
        初始化 Pin888 自动化操作

        Args:
            browser_controller: 浏览器控制器对象
            page: 页面对象
            config : online_platform 的所有数据
            **kwargs: 其他配置参数
                - ws_client: WebSocket 客户端 (可选)
                - handler_name: Handler 名称 (可选)
                - online_platform: 平台状态字典 (可选)
        """
        
        super().__init__(browser_controller, page, config **kwargs)
        # ==================== 订单管理 ====================
        self.order_record: Dict[str, Dict[str, Any]] = {}  # 存储订单信息 {order_id: {...}}

        # ==================== 补单控制 ====================
        self._is_SupplementaryOrder: bool = False  # 是否正在执行补单
        self.PIN888_CYCLEING: bool = True  # 补单循环控制开关

        # ==================== POM 对象 (页面对象模型) ====================
        self.pom = None
        if self.page:
            try:
                from .handler.pom import Pin888POM
                self.pom = Pin888POM(self.page)
                logger.debug(f"[{self.handler_name}] POM 对象初始化成功")
            except ImportError as e:
                logger.warning(f"[{self.handler_name}] POM 模块未找到,将在 prepare_work 中初始化: {e}")

        # ==================== 计数器 ====================
        self.count_get_ws_result: int = 0  # WebSocket 结果获取计数器 (避免日志刷屏)
        self.connect_count: int = 0  # WebSocket 连接尝试计数器

        

    # ==================== 绑定操作方法 ====================
    prepare_work = prepare_work
    GetBalance = GetBalance
    GetOdd = GetOdd
    BettingOrder = BettingOrder
    SupplementaryOrder = SupplementaryOrder
