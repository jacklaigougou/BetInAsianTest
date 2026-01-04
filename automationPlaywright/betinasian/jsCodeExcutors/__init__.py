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
    'get_router_stats'
]
