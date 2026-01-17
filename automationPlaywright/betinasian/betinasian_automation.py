# -*- coding: utf-8 -*-
"""
BetInAsian automation entry point.
"""
from typing import Any, Dict
import logging
from ..interface import AutomationBase
from .operations import (
    prepare_work,
    GetBalance,
    GetOdd,
    BettingOrder,
    MonitorOrderStatus,
    SupplementaryOrder,
    CancelOrder,
)

logger = logging.getLogger(__name__)


class BetInAsianAutomation(AutomationBase):
    """Automation controller for BetInAsian."""

    handler_info: Dict[str, Dict[str, Any]] = {}

    def __init__(
        self,
        browser_controller: Any = None,
        page: Any = None,
        config: Dict[str, Any] = None,
        **kwargs,
    ) -> None:
        super().__init__(browser_controller, page, config, **kwargs)

        self.ws_client = kwargs.get("ws_client")
        self.online_platform = kwargs.get("online_platform", self.config)

        self.order_record: Dict[str, Dict[str, Any]] = {}
        self._is_supplementary_order: bool = False
        self.BIA_CYCLING: bool = True

        if self.handler_name not in BetInAsianAutomation.handler_info:
            BetInAsianAutomation.handler_info[self.handler_name] = {}

        # self.pom = None
        # if self.page:
        #     try:
        #         from .handler.pom import BetInAsianPOM  # type: ignore

        #         self.pom = BetInAsianPOM(self.page)
        #         logger.debug("[%s] POM ready", self.handler_name)
        #     except ImportError:
        #         logger.debug("BetInAsian POM module is not available; skip preload")
        #     except Exception as exc:  # noqa: BLE001
        #         logger.warning("[%s] POM init failed: %s", self.handler_name, exc)

        # logger.info("[%s] BetInAsian automation initialized", self.handler_name)

    prepare_work = prepare_work
    GetBalance = GetBalance
    GetOdd = GetOdd
    BettingOrder = BettingOrder
    MonitorOrderStatus = MonitorOrderStatus
    SupplementaryOrder = SupplementaryOrder
    CancelOrder = CancelOrder
