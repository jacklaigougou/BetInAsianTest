# -*- coding: utf-8 -*-
"""
球队名称模糊匹配工具
"""
from typing import List, Dict, Optional
import logging
from .clearName import normalize_name

logger = logging.getLogger(__name__)

# 尝试导入 FuzzyWuzzy，如果不可用则回退到 difflib
try:
    from fuzzywuzzy import fuzz
    USE_FUZZYWUZZY = True
    logger.info("✅ 使用 FuzzyWuzzy 进行模糊匹配")
except ImportError:
    from difflib import SequenceMatcher
    USE_FUZZYWUZZY = False
    logger.warning("⚠️ FuzzyWuzzy 未安装，使用 difflib.SequenceMatcher（建议安装: pip install fuzzywuzzy python-Levenshtein）")


def calculate_team_similarity(team1: str, team2: str) -> float:
    """
    计算两个队名的相似度

    Args:
        team1: 队名1（标准化后）
        team2: 队名2（标准化后）

    Returns:
        float: 相似度分数 (0-1)

    Examples:
        >>> calculate_team_similarity("manresa", "basquetmanresa")
        0.85  # FuzzyWuzzy partial_ratio

        >>> calculate_team_similarity("breogan", "cbbreogánlugo")
        0.80  # FuzzyWuzzy partial_ratio
    """
    if USE_FUZZYWUZZY:
        # 使用 FuzzyWuzzy partial_ratio（支持部分匹配）
        score = fuzz.partial_ratio(team1, team2)
        return score / 100.0  # 转换为 0-1 范围
    else:
        # 回退到 SequenceMatcher
        return SequenceMatcher(None, team1, team2).ratio()


def fuzzy_match_teams(
    spider_home: str,
    spider_away: str,
    events: List[Dict],
    threshold: float = 0.7  # 降低阈值到 0.7（从 0.8）
) -> Optional[Dict]:
    """
    对队名进行模糊匹配

    策略:
    1. 先尝试精确匹配 (主队或客队任一匹配即可)
    2. 如果精确匹配失败,使用 FuzzyWuzzy 相似度匹配

    Args:
        spider_home: 外部平台主队名
        spider_away: 外部平台客队名
        events: betinasian 比赛列表
        threshold: 相似度阈值 (默认 0.7，使用 FuzzyWuzzy 时推荐 0.7)

    Returns:
        {
            'success': bool,
            'event_key': str,
            'match_type': 'exact' | 'fuzzy',
            'score': float,
            'matched_event': dict
        }
        或 None (未找到匹配)

    Examples:
        >>> # 案例1: 精确匹配
        >>> fuzzy_match_teams("Lakers", "Warriors", events)
        {'success': True, 'match_type': 'exact', 'score': 1.0, ...}

        >>> # 案例2: FuzzyWuzzy 模糊匹配
        >>> fuzzy_match_teams("Assignia Manresa", "Breogan", events)
        {'success': True, 'match_type': 'fuzzy', 'score': 0.75, ...}
    """
    # 清洗外部队名
    normalized_spider_home = normalize_name(spider_home)
    normalized_spider_away = normalize_name(spider_away)

    # logger.info(f"开始匹配: {spider_home} vs {spider_away}")
    # logger.info(f"标准化后: {normalized_spider_home} vs {normalized_spider_away}")
    # logger.info(f"使用算法: {'FuzzyWuzzy partial_ratio' if USE_FUZZYWUZZY else 'difflib.SequenceMatcher'}")

    # 第一轮: 精确匹配 (OR 逻辑 - 主队或客队任一匹配即可)
    for event in events:
        betinasian_home = normalize_name(event.get('home', ''))
        betinasian_away = normalize_name(event.get('away', ''))

        if normalized_spider_home == betinasian_home or \
           normalized_spider_away == betinasian_away:
            logger.info(f"✅ 精确匹配: {event.get('home')} vs {event.get('away')} (score=1.0)")
            return {
                'success': True,
                'event_key': event.get('event_key'),
                'match_type': 'exact',
                'score': 1.0,
                'matched_event': event
            }

    # 第二轮: 相似度匹配
    # logger.info("精确匹配失败,开始相似度匹配...")
    best_score = 0
    best_match = None
    best_home_score = 0
    best_away_score = 0

    for event in events:
        betinasian_home = normalize_name(event.get('home', ''))
        betinasian_away = normalize_name(event.get('away', ''))

        # 计算主队和客队的相似度
        home_score = calculate_team_similarity(normalized_spider_home, betinasian_home)
        away_score = calculate_team_similarity(normalized_spider_away, betinasian_away)

        # 总分 = 平均值
        total_score = (home_score + away_score) / 2

        logger.debug(f"  比较 {event.get('home')} vs {event.get('away')}: "
                    f"home_score={home_score:.3f}, away_score={away_score:.3f}, "
                    f"total={total_score:.3f}")

        if total_score > best_score:
            best_score = total_score
            best_match = event
            best_home_score = home_score
            best_away_score = away_score

    # 检查是否超过阈值
    if best_score >= threshold:
        logger.info(f"✅ 模糊匹配成功: {best_match.get('home')} vs {best_match.get('away')}")
        logger.info(f"   分数详情: home={best_home_score:.3f}, away={best_away_score:.3f}, "
                   f"total={best_score:.3f}, threshold={threshold}")
        return {
            'success': True,
            'event_key': best_match.get('event_key'),
            'match_type': 'fuzzy',
            'score': best_score,
            'matched_event': best_match
        }
    else:
        # logger.warning(f"❌ 模糊匹配失败: 最高分数={best_score:.3f} < 阈值={threshold}")
        # if best_match:
        #     logger.warning(f"   最接近的比赛: {best_match.get('home')} vs {best_match.get('away')}")
        #     logger.warning(f"   分数详情: home={best_home_score:.3f}, away={best_away_score:.3f}")
        return None
