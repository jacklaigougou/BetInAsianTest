# -*- coding: utf-8 -*-
"""
BetInAsian 获取赔率
"""
from typing import Dict, Any
import logging
from utils.matchGameName import fuzzy_match_teams
from ..jsCodeExcutors.queries.events.query_events import query_betinasian_events, query_active_markets

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

    # if not events:
    #     return {
    #         'success': False,
    #         'message': f'未找到 {spider_sport_type} 正在进行的比赛'
    #     }

    # logger.info(f"从 betinasian 获取到 {len(events)} 场比赛")

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

    # 2. 查询 offers (简单数据)
    offers = await query_active_markets(  # 函数名保持不变,但实际返回 offers 列表
        page=self.page,
        event_key=event_key
    )

    if not offers:
        return {
            'success': False,
            'message': f'未找到 offers 数据: {event_key}'
        }

    logger.info(f"查询到 {len(offers)} 种 offer 类型")

    # 3. 订阅 watch_event 获取详细数据
    try:
        # 从 event 中提取 competition_id 和 sport
        competition_id = event.get('competition_id')
        sport = event.get('sport_period', '').split('_')[0] if event.get('sport_period') else 'basket'

        logger.info(f"订阅 watch_event: event_key={event_key}, sport={sport}, competition_id={competition_id}")

        # 检查是否已订阅
        is_watched = await self.page.evaluate(f'''
            window.__watchManager.isWatched("{event_key}")
        ''')

        if not is_watched:
            # 发送 watch_event 订阅
            watch_success = await self.page.evaluate(f'''
                window.__watchManager.watch("{event_key}", "{sport}", {competition_id})
            ''')

            if watch_success:
                logger.info(f"✅ watch_event 订阅成功")
                # 等待数据返回
                import asyncio
                await asyncio.sleep(2)
            else:
                logger.warning(f"⚠️ watch_event 订阅失败")
        else:
            logger.info(f"✅ 事件已订阅")

        # 查询 offers_event 详细数据 - 只获取 ah 盘口
        ah_lines = await self.page.evaluate(f'''
            window.queryData.parseAllOfferEventLines("{event_key}", "ah")
        ''')

        if ah_lines:
            logger.info(f"✅ 获取到 ah 盘口详细数据,共 {len(ah_lines)} 个 line_id")
            logger.info(f"\n{'='*60}")
            logger.info(f"📊 AH 盘口详细数据:")
            logger.info(f"{'='*60}")

            for idx, line_data in enumerate(ah_lines, 1):
                line_id = line_data.get('line_id')
                odds = line_data.get('odds')
                logger.info(f"\n  [{idx}] Line ID: {line_id}")
                logger.info(f"      Odds: {odds}")

            logger.info(f"{'='*60}\n")
        else:
            logger.warning(f"⚠️ 未获取到 ah 盘口数据")

    except Exception as e:
        logger.error(f"❌ watch_event 处理异常: {e}")
        # 不影响主流程,继续使用 offers_hcap 数据

    # 4. 筛选目标 offer
    # TODO: 根据 dispatch_message 中的 offer_type 和 bet_type 筛选具体 offer
    # 默认取第一个 offer
    target_offer = offers[0]

    # 提取赔率
    # target_offer 格式: {'offer_type': 'ah', 'line_id': 20, 'odds': {'a': 1.877, 'h': 1.862}}
    

