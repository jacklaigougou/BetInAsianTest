# -*- coding: utf-8 -*-
"""
Spider to BetInAsian Market Mapping Module
Supports Basketball and Soccer (Football)

Directory Structure:
    MappingBetburgerToBetinisian/
    ├── basket/           # Basketball mapping
    │   ├── basket.py
    │   └── README.md
    ├── soccer/           # Soccer mapping
    │   ├── soccer.py
    │   └── README.md
    ├── mapping.py        # Unified interface
    └── __init__.py       # This file

Unified Interface Usage:
    from MappingBetburgerToBetinisian import parse_spider_market

    # Basketball
    mapping = parse_spider_market("basket", "17", -5.5)

    # Soccer
    mapping = parse_spider_market("soccer", "11")

Object-Oriented Usage:
    from MappingBetburgerToBetinisian import MarketMapper

    mapper = MarketMapper("basket")
    mapping = mapper.parse("17", -5.5)

Direct Module Access:
    from MappingBetburgerToBetinisian import basket, soccer

    # Basketball specific
    basket_mapping = basket.parse_spider_market("17", -5.5)

    # Soccer specific
    soccer_mapping = soccer.parse_spider_market("11")
"""

# Import sport-specific modules
from . import basket
from . import soccer

# Import unified interface
from .mapping import (
    parse_spider_market,
    get_betinasian_market_type,
    get_betinasian_side,
    needs_line_id,
    get_side_name,
    get_market_name,
    get_supported_sports,
    is_sport_supported,
    MarketMapper,
    map_market,
    validate_mapping,
    build_bet_type_from_spider
)

__all__ = [
    # Sport modules
    'basket',
    'soccer',

    # Unified interface functions
    'parse_spider_market',
    'get_betinasian_market_type',
    'get_betinasian_side',
    'needs_line_id',
    'get_side_name',
    'get_market_name',
    'get_supported_sports',
    'is_sport_supported',
    'map_market',
    'validate_mapping',
    'build_bet_type_from_spider',

    # Object-oriented interface
    'MarketMapper'
]
