# -*- coding: utf-8 -*-
"""
BetInAsian 获取赔率
"""
from typing import Dict, Any
import logging
import asyncio
import time
from utils.matchGameName import fuzzy_match_teams
from ..jsCodeExcutors.queries.events.query_events import query_betinasian_events, query_active_markets, get_event_score
from ..MappingBetburgerToBetinisian import build_bet_type_from_spider
from ..jsCodeExcutors.http_executors import create_betslip, delete_betslip
from ..jsCodeExcutors.queries.pmm import get_price_by_betslip_id, wait_for_pmm_ready

logger = logging.getLogger(__name__)


def _create_error_response(handler_name: str, order_id: str, message: str) -> Dict[str, Any]:
    """
    创建统一的错误响应格式

    Args:
        handler_name: 处理器名称
        order_id: 订单ID（可能为空）
        message: 错误消息

    Returns:
        统一格式的错误响应
    """
    return {
        'success': False,
        'handler_name': handler_name if handler_name else '',
        'order_id': order_id if order_id else '',
        'message': message,
        'platform_odd': None,
        'platform_max_stake': None,
        'timestamp': time.time()
    }


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
    logger.info(f"📡 查询 BetInAsian 比赛列表...")
    events = await query_betinasian_events(
        page=self.page,
        sport_type=spider_sport_type,
        in_running_only=True
    )

    if not events:
        logger.error(f"❌ 未找到 {spider_sport_type} 正在进行的比赛")
        return {
            'success': False,
            'message': f'未找到 {spider_sport_type} 正在进行的比赛'
        }

    logger.info(f"✅ 从 BetInAsian 获取到 {len(events)} 场比赛")

    # 显示前5场比赛
    if len(events) > 0:
        logger.info(f"\n前 {min(5, len(events))} 场比赛:")
        for i, evt in enumerate(events[:5], 1):
            logger.info(f"  [{i}] {evt.get('home')} vs {evt.get('away')} ({evt.get('competition_name')})")

    # 2. 队名匹配 (先精确匹配,失败后模糊匹配)
    logger.info(f"\n🔍 开始队名匹配...")
    logger.info(f"  - 目标主队: {spider_home}")
    logger.info(f"  - 目标客队: {spider_away}")
    logger.info(f"  - 匹配阈值: 0.8")

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
    required_amount: float = 10.0,
    required_currency: str = "GBP",
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
            required_amount: 所需投注金额 (默认: 10.0)
            required_currency: 所需货币 (默认: "GBP")
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
            ...     },
            ...     required_amount=20.0  # 自定义投注金额
            ... )
            >>> result['success']
            True
    """
    # 🔍 调试日志：检查 self.page 状态
    # print(f"🔍 [DEBUG] GetOdd 开始执行")
    # print(f"  - self.page: {self.page}")
    # print(f'dispatch_message : {dispatch_message}')
    # 检查 page 是否有效
    if not self.page:
        print("❌ self.page 为 None，无法执行 GetOdd")
        return _create_error_response('', '', 'page 对象为 None，请先执行 prepare_work()')

    try:
        print(f"  - page.url: {self.page.url}")
        print(f"  - page.is_closed: {self.page.is_closed()}")
    except Exception as e:
        logger.error(f"❌ 无法访问 page 对象: {e}")
        return _create_error_response('', '', f'page 对象无效: {e}')

    # logger.info(f"  - dispatch_message: {dispatch_message}")

    # 1. 提取参数 (从 bet_data 中获取)
    original_msg = dispatch_message  # 保存原始消息
    order_id = dispatch_message.get('order_id', '')  # 获取 order_id
    handler_name = self.handler_name  # 获取 handler_name

    bet_data = dispatch_message.get('bet_data', {})
    spider_home = bet_data.get('spider_home')
    spider_away = bet_data.get('spider_away')
    spider_sport_type = bet_data.get('spider_sport_type')
    spider_market_id = str(bet_data.get('spider_market_id'))  # 转换为字符串
    spider_handicap_value = bet_data.get('spider_handicap_value')
    spider_period = bet_data.get('spider_period', 'Full Time')  # 默认全场

    print(f"\n{'='*60}")
    print(f"📋 获取赔率参数:")
    print(f"  - 主队: {spider_home}")
    print(f"  - 客队: {spider_away}")
    print(f"  - 运动类型: {spider_sport_type}")
    print(f"  - 盘口ID: {spider_market_id}")
    print(f"  - 让分值: {spider_handicap_value}")
    print(f"  - 时段: {spider_period}")
    print(f"{'='*60}\n")

    # 2. 将爬虫运动类型转换为 betinasian 运动类型  如: basketball -> basket,soccer -> fb
    original_sport_type = spider_sport_type
    spider_sport_type = await sport_type_to_betinasian_sport_type(
        self,
        spider_sport_type=spider_sport_type,
        **kwargs
    )

    if original_sport_type != spider_sport_type:
        logger.info(f"🔄 运动类型转换: {original_sport_type} -> {spider_sport_type}")

    # 2. 获取 event_key (通过队名匹配) 如:2026-01-04,31629,36428
    print(f"\n🔍 开始匹配比赛...")
    print(f"  - 查询运动类型: {spider_sport_type}")
    print(f"  - 查询主队: {spider_home}")
    print(f"  - 查询客队: {spider_away}")
    
    # window.queryData.inRunningSport,获取所有的正在进行的比赛,并进行匹配
    match_result = await get_event_key_by_team_name(
        self,
        spider_home=spider_home,
        spider_away=spider_away,
        spider_sport_type=spider_sport_type,
        **kwargs
    )

    if not match_result.get('success'):
        print(f"\n❌ 比赛匹配失败:")
        print(f"  - 原因: {match_result.get('message')}")
        print(f"  - 查询的主队: {spider_home}")
        print(f"  - 查询的客队: {spider_away}")
        print(f"  - 运动类型: {spider_sport_type}")

        # 补充缺失的字段
        match_result['handler_name'] = handler_name
        match_result['order_id'] = order_id
        match_result['platform_odd'] = None
        match_result['platform_max_stake'] = None
        match_result['timestamp'] = time.time()

        return match_result

    event = match_result.get('event')
    event_key = match_result.get('event_key')

    print(f"\n✅ 比赛匹配成功!")
    print(f"  - 比赛键: {event_key}")
    print(f"  - 匹配类型: {match_result.get('match_type')}")
    print(f"  - 匹配分数: {match_result.get('score'):.2f}")
    print(f"  - 平台主队: {event.get('home')}")
    print(f"  - 平台客队: {event.get('away')}")
    print(f"  - 联赛: {event.get('competition_name')}")
    print(f"  - 是否进行中: {event.get('isInRunning')}")

    # 3. event_id = event_key (BetInAsian 使用相同格式) 如:2026-01-04,31629,36428
    event_id = event_key

    # 3.1 获取比赛实时比分
    home_score = 0  # 默认值
    away_score = 0  # 默认值

    try:
        score_data = await get_event_score(self.page, event_key)
        if score_data.get('has_score'):
            home_score = score_data.get('home_score', 0)
            away_score = score_data.get('away_score', 0)
            print(f"\n⚽ 实时比分: {home_score} - {away_score}")
        else:
            print(f"\n⚠️  暂无比分数据 (比赛可能未开始)")
    except Exception as e:
        logger.warning(f"获取比分失败: {e}")
        print(f"\n⚠️  获取比分失败: {e}")

    # 3.2 提取时间信息（如果有）
    match_phase = "UNKNOWN"
    remaining_seconds = 0

    try:
        if event.get('ir_status') and event.get('ir_status').get('time'):
            # 从 ir_status.time 提取时间信息
            time_info = event.get('ir_status').get('time')
            # 如果有时间信息，标记为进行中
            match_phase = "IN_PLAY" if event.get('isInRunning') else "NOT_STARTED"
            # TODO: 根据实际 time 格式解析 remaining_seconds
            # 暂时使用默认值 0
        else:
            match_phase = "IN_PLAY" if event.get('isInRunning') else "NOT_STARTED"
    except Exception as e:
        logger.warning(f"提取时间信息失败: {e}")
        match_phase = "UNKNOWN"

    # 4. 验证必需参数
    if not spider_market_id:
        logger.error(f"❌ 缺少必需参数: spider_market_id")
        return _create_error_response(handler_name, order_id, '缺少必需参数: spider_market_id')

    print(f"\n📊 盘口参数:")
    print(f"  - 爬虫盘口ID: {spider_market_id}")
    print(f"  - 让分值: {spider_handicap_value}")

    # 5. 构造 bet_type (使用统一映射接口)
    """
        ("basket", "17", -5.5)	{"betinasian_market": "ah", "betinasian_side": "h", "line_id": -22}	"for,ah,h,-22"
        输入17 ,其实已经包含了 两个信息: market_type 和 side
        所以不需要再进行映射

        足球 IR 格式盘口会使用实时比分:
        ("fb", "17", -0.5, home_score=1, away_score=2) -> "for,ir,1,2,ah,h,-2"
    """
    bet_type = build_bet_type_from_spider(
        sport_type=spider_sport_type,
        spider_market_id=spider_market_id,
        handicap_value=spider_handicap_value,
        home_score=home_score if spider_sport_type in ['fb', 'soccer'] else 0,
        away_score=away_score if spider_sport_type in ['fb', 'soccer'] else 0
    )

    if not bet_type:
        print(f"\n❌ 无法映射盘口ID:")
        print(f"  - 爬虫盘口ID: {spider_market_id}")
        print(f"  - 运动类型: {spider_sport_type}")
        print(f"  - 让分值: {spider_handicap_value}")
        return _create_error_response(
            handler_name,
            order_id,
            f'无法映射 market ID: {spider_market_id} (sport: {spider_sport_type})'
        )

    print(f"\n✅ 投注类型构造成功:")
    print(f"  - 投注类型: {bet_type}")

    # 5.5 映射 spider_period 到 BetInAsian sport
    betinasian_sport = spider_sport_type
    print(f"  - 爬虫时段: {spider_period}")
    # 足球时段映射
    if spider_sport_type in ['fb', 'soccer']:
        from ..MappingBetburgerToBetinisian.soccer.period_mapper import map_period_to_sport
        betinasian_sport = map_period_to_sport(
            spider_period=spider_period,
            spider_market_id=spider_market_id
        )
        if betinasian_sport != spider_sport_type:
            print(f"\n🔄 时段映射 (足球):")
            print(f"  - 爬虫时段: {spider_period}")
            print(f"  - 爬虫盘口ID: {spider_market_id}")
            print(f"  - 映射前: {spider_sport_type}")
            print(f"  - 映射后: {betinasian_sport}")

    # 篮球时段映射
    elif spider_sport_type in ['basket', 'basketball']:
        from ..MappingBetburgerToBetinisian.basket.period_mapper import map_period_to_sport
        betinasian_sport = map_period_to_sport(spider_period=spider_period)
        if betinasian_sport != spider_sport_type:
            print(f"\n🔄 时段映射 (篮球):")
            print(f"  - 爬虫时段: {spider_period}")
            print(f"  - 映射前: {spider_sport_type}")
            print(f"  - 映射后: {betinasian_sport}")

    # 6. 调用 create_betslip, 申请一个 betslip ,并且会触发 ws 中接收 pmm 的数据.
    print(f"\n{'='*60}")
    print(f"📋 创建投注单")
    print(f"{'='*60}")
    print(f"  - 运动类型: {betinasian_sport}")
    print(f"  - 比赛ID: {event_id}")
    print(f"  - 投注类型: {bet_type}")
    print(f"  - 比赛: {event.get('home')} vs {event.get('away')}")
    print(f"{'='*60}\n")

    betslip_result = await create_betslip(
        page=self.page,
        sport=betinasian_sport,
        event_id=event_id,
        bet_type=bet_type
    )

    # 7. 处理 betslip 创建结果
    if not betslip_result.get('success'):
        logger.error(f"\n❌ 投注单创建失败:")
        logger.error(f"  - 错误: {betslip_result.get('error')}")
        logger.error(f"  - 状态码: {betslip_result.get('status')}")
        logger.error(f"  - 完整响应: {betslip_result}")
        return {
            'success': False,
            'handler_name': handler_name,
            'order_id': order_id,
            'message': f"投注单创建失败: {betslip_result.get('error')}",
            'platform_odd': None,
            'platform_max_stake': None,
            'timestamp': time.time(),
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

    logger.info(f"\n✅ 投注单创建成功!")
    logger.info(f"  - 状态码: {betslip_result.get('status')}")

    # 提取 betslip_id (尝试两种可能的路径)
    betslip_data = betslip_result.get('data', {})
    betslip_id = betslip_data.get('betslip_id')

    # 如果第一层没有,尝试嵌套的 data.data.betslip_id
    if not betslip_id and 'data' in betslip_data:
        betslip_id = betslip_data.get('data', {}).get('betslip_id')

    if not betslip_id:
        print(f"\n❌ 无法从响应中提取投注单ID")
        print(f"  - 响应键: {list(betslip_result.keys())}")
        print(f"  - 数据键: {list(betslip_data.keys())}")
        print(f"  - 完整响应: {betslip_result}")

        # ⚠️ 无法清理 betslip（因为没有 betslip_id）
        logger.warning("⚠️ 投注单已创建但无法提取ID，无法清理")

        return {
            'success': False,
            'handler_name': handler_name,
            'order_id': order_id,
            'message': '投注单创建成功但无法提取ID',
            'platform_odd': None,
            'platform_max_stake': None,
            'timestamp': time.time(),
            'betslip_result': betslip_result
        }

    print(f"\n✅ 投注单ID提取成功:")
    print(f"  - 投注单ID: {betslip_id}")

    # 8. 等待 PMM 数据到达并获取最佳赔率
    print(f"\n{'='*60}")
    print(f"⏳ 等待赔率数据准备...")
    print(f"{'='*60}")
    print(f"  - 投注单ID: {betslip_id}")
    print(f"  - 所需金额: {required_amount} {required_currency}")
    print(f"{'='*60}\n")

    # 使用智能等待机制：等待 PMM 数据稳定且满足执行条件
    wait_result = await wait_for_pmm_ready(
        page=self.page,
        betslip_id=betslip_id,
        required_amount=required_amount,
        required_currency=required_currency,
        poll_interval=50,      # 轮询间隔 50ms
        stable_ms=300,         # 稳定时间 300ms
        total_timeout=4000,    # 总超时 4 秒
        min_updates=1          # 最少更新次数
    )

    # 检查等待结果
    if not wait_result.get('ready'):
        print(f"\n⚠️ 赔率数据未准备好:")
        print(f"  - 原因: {wait_result.get('reason')}")
        print(f"  - 耗时: {wait_result.get('elapsed')}ms")
        print(f"  - 更新次数: {wait_result.get('update_count')}")
        print(f"  - 最佳价格: {wait_result.get('best_price')}")
        print(f"  - 最佳庄家: {wait_result.get('best_bookie')}")

        # 清理 betslip
        logger.info(f"🗑️ 清理投注单: {betslip_id}")
        try:
            delete_result = await delete_betslip(self.page, betslip_id)
            if delete_result.get('success'):
                logger.info(f"✅ 投注单已清理")
            else:
                logger.warning(f"⚠️ 投注单清理失败: {delete_result.get('error')}")
        except Exception as e:
            logger.warning(f"⚠️ 投注单清理异常: {e}")

        return {
            'success': False,
            'handler_name': handler_name,
            'order_id': order_id,
            'message': f"赔率数据未准备好: {wait_result.get('reason')}",
            'platform_odd': None,
            'platform_max_stake': None,
            'timestamp': time.time(),
            'betslip_id': betslip_id,
            'wait_result': wait_result
        }
    else:
        print(f"\n✅ 赔率数据已准备:")
        print(f"  - 耗时: {wait_result.get('elapsed')}ms")
        print(f"  - 更新次数: {wait_result.get('update_count')}")
        print(f"  - 稳定时长: {wait_result.get('stable_duration')}ms")
        print(f"  - 最佳价格: {wait_result.get('best_price')}")
        print(f"  - 最佳庄家: {wait_result.get('best_bookie')}")
        print(f"  - 可用金额: {wait_result.get('best_amount')}")

    # 获取最佳赔率
    logger.info(f"\n🔍 获取最佳赔率...")
    logger.info(f"  - 投注单ID: {betslip_id}")
    logger.info(f"  - 所需金额: {required_amount} {required_currency}")

    best_price_result = await get_price_by_betslip_id(
        page=self.page,
        betslip_id=betslip_id,
        required_amount=required_amount,
        required_currency=required_currency
    )

    # 显示最佳赔率结果
    if best_price_result.get('success'):
        logger.info(f"\n✅ 找到可执行赔率:")
        logger.info(f"  - 庄家: {best_price_result.get('bookie')}")
        logger.info(f"  - 价格: {best_price_result.get('price')}")
        logger.info(f"  - 可用额度: {best_price_result.get('available')}")
        logger.info(f"  - 更新时间: {best_price_result.get('updated_at')}")
    else:
        logger.warning(f"\n⚠️ 未找到可执行赔率:")
        logger.warning(f"  - 原因: {best_price_result.get('reason')}")
        if best_price_result.get('best_odds'):
            logger.warning(f"  - 最高赔率(不可执行): {best_price_result.get('best_odds')}")

        # 清理 betslip
        logger.info(f"🗑️ 清理投注单: {betslip_id}")
        try:
            delete_result = await delete_betslip(self.page, betslip_id)
            if delete_result.get('success'):
                logger.info(f"✅ 投注单已清理")
            else:
                logger.warning(f"⚠️ 投注单清理失败: {delete_result.get('error')}")
        except Exception as e:
            logger.warning(f"⚠️ 投注单清理异常: {e}")

        return {
            'success': False,
            'handler_name': handler_name,
            'order_id': order_id,
            'message': f"未找到可执行赔率: {best_price_result.get('reason')}",
            'platform_odd': None,
            'platform_max_stake': None,
            'timestamp': time.time(),
            'betslip_id': betslip_id,
            'best_price_result': best_price_result
        }

    # 9. 存储订单记录
    self.order_record[order_id] = {
        # Handler 信息
        'handler_name': handler_name,
        'order_id': order_id,

        # 基本信息
        'event_key': event_key,
        'event_id': event_id,
        'betslip_id': betslip_id,
        'bet_type': bet_type,

        # 赔率信息
        'odds': best_price_result.get('price'),
        'max_stake': best_price_result.get('available', {}).get('amount') if best_price_result.get('available') else None,
        'bookie': best_price_result.get('bookie'),

        # 队伍信息
        'home': event.get('home'),
        'away': event.get('away'),
        'competition_name': event.get('competition_name'),

        # 比赛信息
        'sport_type': spider_sport_type,
        'match_phase': match_phase,
        'remaining_seconds': remaining_seconds,
        'is_in_running': event.get('isInRunning'),

        # Spider 参数
        'spider_home': spider_home,
        'spider_away': spider_away,
        'spider_market_id': spider_market_id,
        'spider_handicap_value': spider_handicap_value,
        'spider_handicap': bet_data.get('spider_handicap'),
        'spider_period': bet_data.get('spider_period'),
        'spider_sport_type': spider_sport_type,

        # 匹配信息
        'match_type': match_result.get('match_type'),
        'match_score': match_result.get('score'),

        # 比分信息
        'home_score': home_score,
        'away_score': away_score,

        # 原始消息和重试
        'msg': original_msg,
        'retry_count': 0,

        # 时间戳
        'created_at': time.time()
    }

    # 10. 返回完整结果（按照 Pin888 格式）
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 GetOdd 完成")
    logger.info(f"{'='*60}")
    logger.info(f"  - Success: True")
    logger.info(f"  - Handler: {handler_name}")
    logger.info(f"  - Order ID: {order_id}")
    logger.info(f"  - Event: {event.get('home')} vs {event.get('away')}")
    logger.info(f"  - Event Key: {event_key}")
    logger.info(f"  - Betslip ID: {betslip_id}")
    logger.info(f"  - Platform Odd: {best_price_result.get('price') if best_price_result.get('success') else 'N/A'}")
    platform_max_stake = best_price_result.get('available', {}).get('amount') if best_price_result.get('success') and best_price_result.get('available') else 'N/A'
    logger.info(f"  - Platform Max Stake: {platform_max_stake}")
    logger.info(f"  - Match Phase: {match_phase}")
    logger.info(f"  - Remaining Seconds: {remaining_seconds}")
    logger.info(f"{'='*60}\n")

    return {
        'success': True,
        'handler_name': handler_name,
        'order_id': order_id,
        'platform_odd': best_price_result.get('price') if best_price_result.get('success') else None,
        'platform_max_stake': best_price_result.get('available', {}).get('amount') if best_price_result.get('success') and best_price_result.get('available') else None,
        'match_phase': match_phase,
        'remaining_seconds': remaining_seconds,
        'spider_handicap': bet_data.get('spider_handicap'),
        'spider_period': bet_data.get('spider_period'),
        'sport_type': spider_sport_type
    }
