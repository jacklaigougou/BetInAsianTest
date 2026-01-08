# -*- coding: utf-8 -*-
"""
BetInAsian 获取赔率
"""
from typing import Dict, Any
import logging
import asyncio
from utils.matchGameName import fuzzy_match_teams
from ..jsCodeExcutors.queries.events.query_events import query_betinasian_events, query_active_markets
from ..MappingBetburgerToBetinisian import build_bet_type_from_spider
from ..jsCodeExcutors.http_executors import create_betslip
from ..jsCodeExcutors.queries.pmm import get_price_by_betslip_id

logger = logging.getLogger(__name__)


async def get_event_key_by_team_name(
    self,
    spider_home: str,
    spider_away: str,
    spider_sport_type: str,
    **kwargs
) -> Dict[str, Any]:
    """
    通过队名匹配获取 betinasian 的比赛 event_key

    Args:
        spider_home: 外部平台主队名 (e.g., 'Manchester United')
        spider_away: 外部平台客队名 (e.g., 'Chelsea')
        spider_sport_type: 运动类型 (e.g., 'basket', 'fb')
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
        ...     spider_home='Arsenal',
        ...     spider_away='Chelsea',
        ...     spider_sport_type='fb'
        ... )
        >>> result['success']
        True
    """
    logger.info(f"开始匹配比赛: {spider_home} vs {spider_away} ({spider_sport_type})")

    # 1. 查询 betinasian 比赛列表
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

    # 2. 队名匹配 (先精确匹配,失败后模糊匹配)
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
async def sport_type_to_betinasian_sport_type(
    self,
    spider_sport_type: str,
    **kwargs
) -> str:
    """
            将爬虫运动类型转换为 betinasian 运动类型
        Args:
            spider_sport_type: 爬虫运动类型
            **kwargs: 额外参数
        Returns:
            betinasian 运动类型
    """
    
    if spider_sport_type == 'basketball':
        return 'basket'
    elif spider_sport_type == 'soccer':
        return 'fb'
    else:
        return spider_sport_type

async def GetOdd(
    self,
    dispatch_message: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
        获取赔率并创建 Betslip

        Args:
            dispatch_message: {
                'spider_sport_type': 'basket',           # 运动类型
                'spider_home': 'Manchester United',      # 主队
                'spider_away': 'Chelsea',                # 客队
                'spider_market_id': '17',                # Spider market ID
                'spider_handicap_value': -5.5            # 让分值 (可选)
            }
            **kwargs: 额外参数

        Returns:
            {
                'success': True,
                'event_id': str,
                'event_key': str,
                'bet_type': str,
                'betslip_result': {...},
                'match_info': {
                    'match_type': 'exact'/'fuzzy',
                    'score': float,
                    'event': {...}
                }
            }
            或
            {
                'success': False,
                'message': str
            }

        Examples:
            >>> result = await GetOdd(
            ...     self,
            ...     {
            ...         'spider_sport_type': 'basket',
            ...         'spider_home': 'Arsenal',
            ...         'spider_away': 'Chelsea',
            ...         'spider_market_id': '17',
            ...         'spider_handicap_value': -5.5
            ...     }
            ... )
            >>> result['success']
            True
    """
    # 1. 提取参数
    spider_home = dispatch_message.get('spider_home')
    spider_away = dispatch_message.get('spider_away')
    spider_sport_type = dispatch_message.get('spider_sport_type')
    spider_market_id = dispatch_message.get('spider_market_id')
    spider_handicap_value = dispatch_message.get('spider_handicap_value')

    # 2. 将爬虫运动类型转换为 betinasian 运动类型  如: basketball -> basket,soccer -> fb
    spider_sport_type = await sport_type_to_betinasian_sport_type(
        self,
        spider_sport_type=spider_sport_type,
        **kwargs
    )

    # 2. 获取 event_key (通过队名匹配) 如:2026-01-04,31629,36428
    match_result = await get_event_key_by_team_name(
        self,
        spider_home=spider_home,
        spider_away=spider_away,
        spider_sport_type=spider_sport_type,
        **kwargs
    )

    if not match_result.get('success'):
        return match_result

    event = match_result.get('event')
    event_key = match_result.get('event_key')
    logger.info(f"✅ 队名匹配成功: event_key={event_key}")

    # 3. event_id = event_key (BetInAsian 使用相同格式) 如:2026-01-04,31629,36428
    event_id = event_key

    # 4. 验证必需参数
    if not spider_market_id:
        return {
            'success': False,
            'message': '缺少必需参数: spider_market_id'
        }

    logger.info(f"Spider Market: ID={spider_market_id}, Handicap={spider_handicap_value}")

    # 5. 构造 bet_type (使用统一映射接口) 
    """
        ("basket", "17", -5.5)	{"betinasian_market": "ah", "betinasian_side": "h", "line_id": -22}	"for,ah,h,-22"
        输入17 ,其实已经包含了 两个信息: market_type 和 side
        所以不需要再进行映射
    """
    bet_type = build_bet_type_from_spider(
        sport_type=spider_sport_type,
        spider_market_id=spider_market_id,
        handicap_value=spider_handicap_value
    )

    if not bet_type:
        return {
            'success': False,
            'message': f'无法映射 market ID: {spider_market_id} (sport: {spider_sport_type})'
        }

    logger.info(f"✅ 构造 bet_type: {bet_type}")

    # 6. 调用 create_betslip, 申请一个 betslip ,并且会触发 ws 中接收 pmm 的数据.
    logger.info(f"📋 创建 Betslip: sport={spider_sport_type}, event_id={event_id}, bet_type={bet_type}")

    betslip_result = await create_betslip(
        page=self.page,
        sport=spider_sport_type,
        event_id=event_id,
        bet_type=bet_type
    )

    # 7. 处理 betslip 创建结果
    if not betslip_result.get('success'):
        logger.error(f"❌ Betslip 创建失败: {betslip_result.get('error')}")
        return {
            'success': False,
            'message': f"Betslip 创建失败: {betslip_result.get('error')}",
            'event_id': event_id,
            'event_key': event_key,
            'bet_type': bet_type,
            'betslip_result': betslip_result,
            'match_info': {
                'match_type': match_result.get('match_type'),
                'score': match_result.get('score'),
                'event': event
            }
        }

    logger.info(f"✅ Betslip 创建成功!")

    # 提取 betslip_id (尝试两种可能的路径)
    betslip_data = betslip_result.get('data', {})
    betslip_id = betslip_data.get('betslip_id')

    # 如果第一层没有,尝试嵌套的 data.data.betslip_id
    if not betslip_id and 'data' in betslip_data:
        betslip_id = betslip_data.get('data', {}).get('betslip_id')

    if not betslip_id:
        logger.error(f"❌ 无法从响应中提取 betslip_id")
        logger.error(f"响应结构: {betslip_result}")
        return {
            'success': False,
            'message': 'Betslip 创建成功但无法提取 betslip_id',
            'betslip_result': betslip_result
        }

    logger.info(f"📋 Betslip ID: {betslip_id}")

    # 8. 等待 PMM 数据到达并获取最佳赔率
    logger.info(f"⏳ 等待 PMM 数据...")
    await asyncio.sleep(3)  # 等待 3 秒让 PMM 数据到达

    logger.info(f"🔍 获取最佳赔率...")
    best_price_result = await get_price_by_betslip_id(
        page=self.page,
        betslip_id=betslip_id,
        required_amount=10.0,
        required_currency="GBP"
    )

    # 9. 返回完整结果
    return {
        'success': True,
        'event_id': event_id,
        'event_key': event_key,
        'bet_type': bet_type,
        'betslip_id': betslip_id,
        'betslip_result': betslip_result,
        'best_price': best_price_result,  # 新增: 最佳赔率信息
        'match_info': {
            'match_type': match_result.get('match_type'),
            'score': match_result.get('score'),
            'event': event
        }
    }
