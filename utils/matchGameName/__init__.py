# -*- coding: utf-8 -*-
"""
球队名称匹配模块
"""
from .clearName import normalize_name, clear_name
from .fuzzy_match import fuzzy_match_teams, calculate_team_similarity

__all__ = [
    'normalize_name',
    'clear_name',
    'fuzzy_match_teams',
    'calculate_team_similarity'
]
