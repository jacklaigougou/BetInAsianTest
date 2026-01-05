# -*- coding: utf-8 -*-
"""
球队名称模糊匹配工具
"""
from difflib import SequenceMatcher
from typing import List, Dict, Optional
from .clearName import normalize_name


def calculate_team_similarity(team1: str, team2: str) -> float:
    """
    计算两个队名的相似度

    Args:
        team1: 队名1
        team2: 队名2

    Returns:
        float: 相似度分数 (0-1)
    """
    return SequenceMatcher(None, team1, team2).ratio()


def fuzzy_match_teams(
    spider_home: str,
    spider_away: str,
    events: List[Dict],
    threshold: float = 0.8
) -> Optional[Dict]:
    """
    对队名进行模糊匹配

    策略:
    1. 先尝试精确匹配 (主队或客队任一匹配即可)
    2. 如果精确匹配失败,使用相似度匹配

    Args:
        spider_home: 外部平台主队名
        spider_away: 外部平台客队名
        events: betinasian 比赛列表
        threshold: 相似度阈值 (默认 0.8)

    Returns:
        {
            'success': bool,
            'event_key': str,
            'match_type': 'exact' | 'fuzzy',
            'score': float,
            'matched_event': dict
        }
        或 None (未找到匹配)
    """
    # 清洗外部队名
    normalized_spider_home = normalize_name(spider_home)
    normalized_spider_away = normalize_name(spider_away)

    # 第一轮: 精确匹配 (OR 逻辑 - 主队或客队任一匹配即可)
    for event in events:
        betinasian_home = normalize_name(event.get('home', ''))
        betinasian_away = normalize_name(event.get('away', ''))

        if normalized_spider_home == betinasian_home or \
           normalized_spider_away == betinasian_away:
            return {
                'success': True,
                'event_key': event.get('event_key'),
                'match_type': 'exact',
                'score': 1.0,
                'matched_event': event
            }

    # 第二轮: 相似度匹配
    best_score = 0
    best_match = None

    for event in events:
        betinasian_home = normalize_name(event.get('home', ''))
        betinasian_away = normalize_name(event.get('away', ''))

        # 计算主队和客队的相似度
        home_score = calculate_team_similarity(normalized_spider_home, betinasian_home)
        away_score = calculate_team_similarity(normalized_spider_away, betinasian_away)

        # 总分 = 平均值
        total_score = (home_score + away_score) / 2

        if total_score > best_score:
            best_score = total_score
            best_match = event

    # 检查是否超过阈值
    if best_score >= threshold:
        return {
            'success': True,
            'event_key': best_match.get('event_key'),
            'match_type': 'fuzzy',
            'score': best_score,
            'matched_event': best_match
        }
    else:
        return None
