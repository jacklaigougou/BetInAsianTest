# -*- coding: utf-8 -*-
"""
BetInAsian JS Code Executors
"""
from .inject_hook import (
    load_js_file,
    inject_websocket_hook,
    check_websocket_status,
    get_recent_ws_messages,
    send_websocket_data
)

from .inject_registors import (
    inject_data_registors,
    get_registor_stats,
    get_router_stats
)

from .PlaceOrder import (
    place_order
)

from .queries.orders.get_order import (
    get_order_by_id,
    get_orders_by_status,
    get_orders_by_event,
    get_order_with_bets,
    check_order_slippage,
    get_bet_by_id,
    get_bets_by_order,
    get_order_bet_stats
)

__all__ = [
    # Hook 相关
    'load_js_file',
    'inject_websocket_hook',
    'check_websocket_status',
    'get_recent_ws_messages',
    'send_websocket_data',

    # 数据注册器相关
    'inject_data_registors',
    'get_registor_stats',
    'get_router_stats',

    # 订单相关
    'place_order',

    # Order/Bet 查询相关
    'get_order_by_id',
    'get_orders_by_status',
    'get_orders_by_event',
    'get_order_with_bets',
    'check_order_slippage',
    'get_bet_by_id',
    'get_bets_by_order',
    'get_order_bet_stats'
]
