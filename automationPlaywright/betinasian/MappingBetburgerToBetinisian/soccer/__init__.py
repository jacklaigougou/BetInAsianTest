# -*- coding: utf-8 -*-
"""
Soccer (Football) Market Mapping Module
"""

from .soccer import (
    SPIDER_TO_BETINASIAN_MARKET,
    parse_spider_market,
    get_betinasian_market_type,
    get_betinasian_side,
    needs_line_id,
    BETINASIAN_SIDE_NAMES,
    BETINASIAN_MARKET_NAMES
)

__all__ = [
    'SPIDER_TO_BETINASIAN_MARKET',
    'parse_spider_market',
    'get_betinasian_market_type',
    'get_betinasian_side',
    'needs_line_id',
    'BETINASIAN_SIDE_NAMES',
    'BETINASIAN_MARKET_NAMES'
]
