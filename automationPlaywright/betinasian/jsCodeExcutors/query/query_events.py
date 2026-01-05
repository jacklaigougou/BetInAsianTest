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

        # 先查看 Offers Store 中的所有数据
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 Offers Store 诊断信息:")
        logger.info(f"{'='*60}")

        # 获取 Offers Store 总数
        total_offers = await page.evaluate('window.__offersStore.count()')
        logger.info(f"Offers Store 总事件数: {total_offers}")

        # 获取前10个 offers 的样本
        if total_offers > 0:
            sample_offers = await page.evaluate('''
                Array.from(window.getOffersData().values()).slice(0, 10).map(o => ({
                    event_key: o.event_key,
                    offer_types: Object.keys(o.raw_data)
                }))
            ''')
            logger.info(f"\n前10个 offers 样本:")
            for i, o in enumerate(sample_offers, 1):
                logger.info(f"  [{i}] event_key: {o.get('event_key')}, offer_types: {o.get('offer_types')}")

        # 查询该 event 的 offers
        offers_js = f'window.queryData.offers("{event_key}")'
        offers = await page.evaluate(offers_js)

        logger.info(f"\n目标比赛 ({event_key}) offers:")

        if not offers:
            logger.warning(f"未找到 offers 数据: {event_key}")
            logger.info(f"{'='*60}\n")
            return []

        # 将 offers 转换为列表格式,方便 Python 处理
        # offers 格式: {"ah": [line_id, odds_array], "ahou": [...], ...}
        offers_list = []
        for offer_type, offer_data in offers.items():
            line_id, odds_array = offer_data
            # 转换 odds_array 为字典
            odds_dict = {side: value for side, value in odds_array}

            offers_list.append({
                'offer_type': offer_type,
                'line_id': line_id,
                'odds': odds_dict,
                'event_key': event_key
            })

        logger.info(f"  - 找到 {len(offers_list)} 种 offer 类型: {list(offers.keys())}")
        logger.info(f"{'='*60}\n")
        logger.info(f"返回 {len(offers_list)} 个 offers")

        return offers_list

    except Exception as e:
        logger.error(f"查询盘口失败: {e}")
        return []
