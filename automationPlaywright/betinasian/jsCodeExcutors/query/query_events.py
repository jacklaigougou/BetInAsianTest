# -*- coding: utf-8 -*-
"""
BetInAsian 事件查询工具
"""
from typing import Any, List, Dict
import logging

logger = logging.getLogger(__name__)


async def query_betinasian_events(
    page: Any,
    sport_type: str,
    in_running_only: bool = True
) -> List[Dict]:
    """
    查询 betinasian 的比赛事件

    Args:
        page: Playwright Page 对象
        sport_type: 运动类型 (如: 'fb', 'basket')
        in_running_only: 是否只查询正在进行的比赛 (默认 True)

    Returns:
        List[Dict]: 比赛列表
        [
            {
                'event_key': '2026-01-04,31629,36428',
                'sport': 'fb',
                'home': 'Arsenal',
                'away': 'Chelsea',
                'competition_name': 'England Premier League',
                ...
            }
        ]

    Examples:
        >>> # 查询正在进行的足球比赛
        >>> events = await query_betinasian_events(page, 'fb', in_running_only=True)
        >>> len(events) > 0
        True
    """
    try:
        # 根据参数选择查询方法
        if in_running_only:
            js_code = f'window.queryData.inRunningSport("{sport_type}")'
        else:
            # 查询所有比赛 (需要指定 period,这里默认使用 ht)
            js_code = f'window.queryData.bySport("{sport_type}_ht")'

        logger.info(f"查询 betinasian 比赛: {js_code}")

        # 执行查询
        events = await page.evaluate(js_code)

        if events is None:
            logger.warning(f"未找到 {sport_type} 比赛数据")
            return []

        logger.info(f"查询到 {len(events)} 场比赛")
        return events

    except Exception as e:
        logger.error(f"查询 betinasian 比赛失败: {e}")
        return []


async def query_active_markets(
    page: Any,
    event_key: str
) -> List[Dict]:
    """
    查询指定比赛的活跃盘口

    Args:
        page: Playwright Page 对象
        event_key: 比赛唯一标识 (如: '2026-01-04,31629,36428')

    Returns:
        List[Dict]: 盘口列表
        [
            {
                'market_key': 'xxx',
                'market_group': 'ahou',
                'odds': {
                    'home': 2.05,
                    'away': 1.85
                },
                ...
            }
        ]

    Examples:
        >>> markets = await query_active_markets(page, '2026-01-04,31629,36428')
        >>> len(markets) > 0
        True
    """
    try:
        logger.info(f"查询盘口: {event_key}")

        # 先查看 Markets Store 中的所有数据
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 Markets Store 诊断信息:")
        logger.info(f"{'='*60}")

        # 获取 Markets Store 总数
        total_markets = await page.evaluate('window.__marketsStore.count()')
        logger.info(f"Markets Store 总盘口数: {total_markets}")

        # 获取前10个 market 的 event_key 样本
        if total_markets > 0:
            sample_markets = await page.evaluate('''
                Array.from(window.getMarketsData().values()).slice(0, 10).map(m => ({
                    event_key: m.event_key,
                    market_group: m.market_group,
                    market_key: m.market_key
                }))
            ''')
            logger.info(f"\n前10个盘口样本:")
            for i, m in enumerate(sample_markets, 1):
                logger.info(f"  [{i}] event_key: {m.get('event_key')}, market_group: {m.get('market_group')}")

        # 查询所有盘口
        all_markets_js = f'window.queryData.marketsByEvent("{event_key}")'
        all_markets = await page.evaluate(all_markets_js)

        # 查询活跃盘口
        active_markets_js = f'window.queryData.activeMarketsByEvent("{event_key}")'
        active_markets = await page.evaluate(active_markets_js)
        

        logger.info(f"\n目标比赛 ({event_key}) 盘口:")
        logger.info(f"  - 所有盘口: {len(all_markets) if all_markets else 0} 个")
        logger.info(f"  - 活跃盘口: {len(active_markets) if active_markets else 0} 个")
        logger.info(f"{'='*60}\n")

        # 优先返回活跃盘口，如果没有则返回所有盘口
        markets = active_markets if active_markets else all_markets

        if markets is None:
            logger.warning(f"未找到盘口数据: {event_key}")
            return []

        logger.info(f"返回 {len(markets)} 个盘口")
        return markets

    except Exception as e:
        logger.error(f"查询盘口失败: {e}")
        return []
