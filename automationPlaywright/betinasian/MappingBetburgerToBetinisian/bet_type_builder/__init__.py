# -*- coding: utf-8 -*-
"""
BetInAsian Bet Type Builder

This module constructs BetInAsian bet_type strings from mapping results.

Usage:
    from .builder import build

    mapping = {"betinasian_market": "ah", "betinasian_side": "h", "line_id": -22}
    bet_type = build(mapping)  # "for,ah,h,-22"
"""

from .builder import build

__all__ = ['build']
