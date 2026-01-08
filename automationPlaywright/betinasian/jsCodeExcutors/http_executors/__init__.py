# -*- coding: utf-8 -*-
"""
BetInAsian HTTP Executors

This module contains HTTP request executors that call BetInAsian APIs through JavaScript.

Modules:
- create_betslip: Create a new betslip
- place_order: Place a betting order on a betslip

Usage:
    from automationPlaywright.betinasian.jsCodeExcutors.http_executors import (
        create_betslip,
        place_order
    )
"""

from .create_betslip import create_betslip, create_betslip_from_mapping, parse_bet_type_from_mapping
from .place_order import place_order

__all__ = [
    'create_betslip',
    'create_betslip_from_mapping',
    'parse_bet_type_from_mapping',
    'place_order'
]
