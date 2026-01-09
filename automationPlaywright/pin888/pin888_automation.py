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
            config: 配置字典 (包含 handler_name, platform_name, balance 等)
                推荐从 onlinePlatform.py 的 account 字典传入
            **kwargs: 其他配置参数
                - ws_client: WebSocket 客户端 (可选)
                - online_platform: 平台状态字典 (兼容旧架构)
        """
        super().__init__(browser_controller, page, config, **kwargs)
        print(config)
        # ✅ handler_name 已经在父类中从 config 提取
        # self.handler_name 可以直接使用

        # ==================== 从 kwargs 提取参数 ====================
        self.ws_client = kwargs.get('ws_client')

        # ✅ 兼容旧架构: 支持 online_platform 参数
        # 如果传入了 online_platform,使用它;否则使用 config
        self.online_platform = kwargs.get('online_platform', self.config)

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

        # ==================== 初始化 handler_info ====================
        if self.handler_name not in Pin888Automation.handler_info:
            Pin888Automation.handler_info[self.handler_name] = {
                'balance': None  # 余额缓存
            }
            logger.debug(f"[{self.handler_name}] 初始化 handler_info 存储空间")

        logger.info(f"[{self.handler_name}] Pin888 自动化操作初始化完成")

    # ==================== 辅助方法 ====================
    async def _send_message_to_electron(self, message: str):
        """
        发送消息到 Electron (通过 WebSocket)

        Args:
            message: 要发送的消息内容

        Examples:
            >>> await self._send_message_to_electron("余额查询成功")
        """
        if self.ws_client:
            try:
                await self.ws_client.send({
                    "from": "automation",
                    "to": "electron",
                    "type": "log",
                    "data": {
                        "type": "warn",
                        "message": f"[{self.handler_name}] {message}"
                    }
                })
            except Exception as e:
                logger.warning(f"[{self.handler_name}] 发送消息到 Electron 失败: {e}")

    async def get_event_id(
        self,
        sportId: int,
        period_num: str,
        spider_home: str,
        spider_away: str,
        event_id: str = None
    ) -> tuple:
        """
        获取 event_id 和 event_detail_data

        Args:
            sportId: 运动类型ID
            period_num: 时段编号
            spider_home: 主队名称
            spider_away: 客队名称
            event_id: 可选的初始 event_id (如果提供则先尝试直接订阅)

        Returns:
            (event_id, event_detail_data) 或 (None, None)

        Examples:
            >>> event_id, data = await self.get_event_id(29, "0,8", "Arsenal", "Chelsea")
        """
        from .jsCodeExecutors import (
            subscribe_events_detail_euro,
            unsubscribe_events_detail_euro,
            subscribe_live_euro_odds
        )
        from .responseAnalysis import parse_event_from_all_events

        matched_event_id = event_id
        event_detail_data = None

        # 如果提供了 event_id，先尝试直接订阅
        if matched_event_id:
            event_detail_data = await subscribe_events_detail_euro(self.page, matched_event_id)

        if not event_detail_data:
            logger.warning(f"[{self.handler_name}] Betburger 提供的 eventId 无效，需要通过球队名重新匹配")
            await unsubscribe_events_detail_euro(self.page, event_id)
            all_events = await subscribe_live_euro_odds(self.page, sportId, period_num)

            if not all_events:
                logger.error(f"[{self.handler_name}] 获取 all_events 失败")
                if self.connect_count == 0:
                    # 尝试重新连接 WebSocket
                    try:
                        from .operations.prepare_work import hookWebSocket
                        await hookWebSocket(self)
                        self.connect_count += 1
                    except Exception as e:
                        logger.error(f"[{self.handler_name}] hookWebSocket 失败: {e}")

                return None, None

            # 解析并匹配比赛
            parsed_result = parse_event_from_all_events(all_events, spider_home, spider_away)

            if not parsed_result:
                logger.error(
                    f"[{self.handler_name}] all_events 获取成功，但未能匹配到比赛 "
                    f"{spider_home} vs {spider_away}"
                )
                return None, None

            # 提取解析结果
            matched_event_id = parsed_result['event_id']
            event_id = matched_event_id
            pin888_standard_home_name = parsed_result['home_name']
            pin888_standard_away_name = parsed_result['away_name']

            logger.info(
                f"[{self.handler_name}] ✅ 通过球队名匹配成功: "
                f"{pin888_standard_home_name} vs {pin888_standard_away_name}"
            )
            logger.debug(f"[{self.handler_name}]   event_id: {matched_event_id}")

            event_detail_data = await subscribe_events_detail_euro(self.page, matched_event_id)
            if not event_detail_data:
                logger.error(
                    f"[{self.handler_name}] 没有该场比赛 {spider_home} -- {spider_away}"
                )
                return None, None

        return event_id, event_detail_data

    # ==================== 绑定操作方法 ====================
    prepare_work = prepare_work
    GetBalance = GetBalance
    GetOdd = GetOdd
    BettingOrder = BettingOrder
    SupplementaryOrder = SupplementaryOrder
