# -*- coding: utf-8 -*-
"""
BetInAsian 获取赔率
"""
from typing import Dict, Any
import logging
from utils.matchGameName import fuzzy_match_teams
from ..jsCodeExcutors.query import query_betinasian_events, query_active_markets

logger = logging.getLogger(__name__)


async def get_event_key_by_team_name(
    self,
    dispatch_message: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
    通过队名匹配获取 betinasian 的比赛 event_key

    Args:
        dispatch_message: {
            'spider_sport_type': 'fb',
            'spider_home': 'Manchester United',
            'spider_away': 'Chelsea'
        }
        **kwargs: 额外参数

    Returns:
        {
            'success': True,
            'event_key': '2026-01-04,31629,36428',
            'match_type': 'exact' | 'fuzzy',
            'score': 1.0,
            'event': {...}  # 完整的 event 对象
        }
        或
        {
            'success': False,
            'message': '错误信息'
        }

    Examples:
        >>> result = await get_event_key_by_team_name(
        ...     self,
        ...     {'spider_sport_type': 'fb', 'spider_home': 'Arsenal', 'spider_away': 'Chelsea'}
        ... )
        >>> result['success']
        True
    """
    # 1. 提取参数
    spider_sport_type = dispatch_message.get('spider_sport_type', '')
    spider_home = dispatch_message.get('spider_home', '')
    spider_away = dispatch_message.get('spider_away', '')

    logger.info(f"开始匹配比赛: {spider_home} vs {spider_away} ({spider_sport_type})")

    # 2. 查询 betinasian 比赛列表
    events = await query_betinasian_events(
        page=self.page,
        sport_type=spider_sport_type,
        in_running_only=True
    )

    if not events:
        return {
            'success': False,
            'message': f'未找到 {spider_sport_type} 正在进行的比赛'
        }

    logger.info(f"从 betinasian 获取到 {len(events)} 场比赛")

    # 3. 模糊匹配
    match_result = fuzzy_match_teams(
        spider_home=spider_home,
        spider_away=spider_away,
        events=events,
        threshold=0.8
    )

    if match_result:
        logger.info(f"匹配成功: event_key={match_result['event_key']}, "
                   f"type={match_result['match_type']}, score={match_result['score']:.2f}")
        # 返回完整的匹配结果,包含完整的 event 对象
        return {
            'success': True,
            'event_key': match_result['event_key'],
            'match_type': match_result['match_type'],
            'score': match_result['score'],
            'event': match_result['matched_event']  # 完整的 event 对象
        }
    else:
        logger.warning(f"未找到匹配的比赛: {spider_home} vs {spider_away}")
        return {
            'success': False,
            'message': f'未找到匹配的比赛: {spider_home} vs {spider_away}'
        }


async def GetOdd(
    self,
    dispatch_message: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
        获取赔率

        Args:
            dispatch_message: {
                'spider_sport_type': 'fb',
                'spider_home': 'Manchester United',
                'spider_away': 'Chelsea',
                'market_group': 'ahou',  # 可选: 盘口类型
                'bet_type': 'home'       # 可选: 投注类型
            }
            **kwargs: 额外参数

        Returns:
            {
                'success': True,
                'event_key': str,
                'odd': float,
                'market_data': {...},
                'total_markets': int
            }
            或
            {
                'success': False,
                'message': str
            }

        Examples:
            >>> result = await GetOdd(
            ...     self,
            ...     {'spider_sport_type': 'fb', 'spider_home': 'Arsenal', 'spider_away': 'Chelsea'}
            ... )
            >>> result['success']
        True
    """
    # 1. 获取 event_key
    match_result = await get_event_key_by_team_name(self, dispatch_message, **kwargs)

    if not match_result.get('success'):
        return match_result
    event = match_result.get('event')
    print(event)
    event_key = match_result.get('event_key')
    logger.info(f"获取赔率: event_key={event_key}")

    # 2. 查询盘口
    markets = await query_active_markets(
        page=self.page,
        event_key=event_key
    )
    print('markets', markets)
    if not markets:
        return {
            'success': False,
            'message': f'未找到盘口数据: {event_key}'
        }

    logger.info(f"查询到 {len(markets)} 个活跃盘口")

    # 3. 筛选目标盘口 (示例: 返回第一个盘口的赔率)
    # TODO: 根据 dispatch_message 中的 market_group 和 bet_type 筛选具体盘口
    target_market = markets[0]

    # 提取赔率 (示例: 假设赔率在 odds 字段中)
    odd_value = None
    if 'odds' in target_market:
        odds = target_market['odds']
        # 根据 bet_type 提取对应赔率
        bet_type = dispatch_message.get('bet_type', 'home')
        odd_value = odds.get(bet_type)

    return {
        'success': True,
        'event_key': event_key,
        'odd': odd_value,
        'market_data': target_market,
        'total_markets': len(markets),
        'match_info': {
            'match_type': match_result.get('match_type'),
            'score': match_result.get('score'),
            'event': match_result.get('event')  # 完整的 event 对象
        }
    }

