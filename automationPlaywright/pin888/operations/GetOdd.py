# -*- coding: utf-8 -*-
"""
Pin888 获取赔率
"""
from typing import Dict, Any, Optional, Tuple
import logging
import time
import json
# 导入必要的函数
from ..jsCodeExecutors import (
    subscribe_events_detail_euro,
    unsubscribe_events_detail_euro,
    subscribe_live_euro_odds
)
from ..responseAnalysis import (
    parse_event_from_all_events,
    parse_team_names_from_detail_data
)
from ..handler.timeAnalysis import analyze_remaining_time
from ..mapping import map_handicap_full
from ..responseAnalysis import find_odds_from_detail_data
from ..handler.mappingBetParamsToIds import map_bet_params_to_ids
from ..jsCodeExecutors import request_all_odds_selections
logger = logging.getLogger(__name__)


def transfan_sport(sport_type: str) -> Tuple[Optional[int], Optional[str]]:
    """
    转换运动类型 → (sportId, period_num)

    Args:
        sport_type: 运动类型 ('soccer', 'basketball')

    Returns:
        (sportId, period_num) 或 (None, None)

    Examples:
        >>> transfan_sport('soccer')
        (29, "0,8,39,3,4,5,6,7")
        >>> transfan_sport('basketball')
        (4, "0,2")
    """
    if sport_type == 'soccer':
        return 29, "0,8,39,3,4,5,6,7"
    elif sport_type == 'basketball':
        return 4, "0,2"
    else:
        logger.error(f"不支持的球类: {sport_type}")
        return None, None


async def GetOdd(
    self,
    dispatch_message: Dict[str, Any],
    event_id: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    获取赔率 (6步流程)

    Args:
        dispatch_message: {
            'order_id': str,
            'bet_data': {
                'spider_sport_type': 'soccer',
                'spider_home': 'Arsenal',
                'spider_away': 'Chelsea',
                'spider_handicap': 'Total Over(2.5)',
                'spider_period': 'Full Time',
                'spider_handicap_param': '2.5',
                'bookmaker_event_direct_link': '123456',
                'event_id': '123456'
            }
        }
        event_id: 可选的 event_id (优先级高于 bet_data 中的)
        **kwargs: 额外参数

    Returns:
        {
            'success': True,
            'handler_name': str,
            'order_id': str,
            'platform_odd': float,
            'platform_max_stake': float,
            'match_phase': str,
            'remaining_seconds': int,
            'spider_handicap': str,
            'spider_period': str,
            'sport_type': str
        }
    """
    start_time = time.time()
    handler_name = self.handler_name
    self._is_SupplementaryOrder = False

    logger.info(f"[{handler_name}] ========== 开始 GetOdd 流程 ==========")

    # ========== Step 1: 参数提取与验证 ==========
    logger.info(f"[{handler_name}] Step 1: 参数提取与验证")

    original_msg = dispatch_message
    bet_data = dispatch_message.get('bet_data', {})

    if not bet_data:
        logger.error(f"[{handler_name}] msg缺少必要参数 bet_data")
        return {'success': False, 'message': 'msg缺少必要参数 bet_data'}

    order_id = dispatch_message.get('order_id', '')
    if not order_id:
        logger.error(f"[{handler_name}] msg 缺少必要参数 order_id")
        return {'success': False, 'message': 'msg 缺少必要参数 order_id'}

    # 提取 event_id
    bookmaker_event_direct_link = bet_data.get('bookmaker_event_direct_link', '')
    if not event_id:
        event_id = bookmaker_event_direct_link

    eventId = bet_data.get('event_id', '')
    matched_event_id = event_id or eventId

    # 提取运动类型
    sport_type = bet_data.get('spider_sport_type')
    sportId, period_num = transfan_sport(sport_type)

    if not sportId:
        logger.error(f"[{handler_name}] 不支持的运动类型: {sport_type}")
        return {'success': False, 'message': f'不支持的运动类型: {sport_type}'}

    logger.info(f"[{handler_name}] ✅ 参数提取成功: order_id={order_id}, sport_type={sport_type}, event_id={matched_event_id}")

    # ========== Step 2: 获取比赛事件数据 ==========
    logger.info(f"[{handler_name}] Step 2: 获取比赛事件数据")

    

    # 2.1 优先使用 event_id 订阅事件详情
    event_detail_data = await subscribe_events_detail_euro(self.page, matched_event_id)

    if not event_detail_data:
        logger.warning(f"[{handler_name}] Betburger 提供的 eventId 无效,需要通过球队名重新匹配")

        # 2.2 降级: 通过球队名匹配
        all_events = await subscribe_live_euro_odds(self.page, sportId, period_num)

        if not all_events:
            logger.error(f"[{handler_name}] 获取 all_events 失败")
            return {'success': False, 'message': '获取 all_events 失败'}

        spider_home = bet_data.get('spider_home', '')
        spider_away = bet_data.get('spider_away', '')

        parsed_result = parse_event_from_all_events(all_events, spider_home, spider_away)

        if not parsed_result:
            logger.error(f"[{handler_name}] 未能从 all_events 中匹配到比赛")
            return {'success': False, 'message': '未能从 all_events 中匹配到比赛'}

        matched_event_id = parsed_result['event_id']
        event_id = matched_event_id
        pin888_standard_home_name = parsed_result['home_name']
        pin888_standard_away_name = parsed_result['away_name']

        logger.info(f"[{handler_name}] ✅ 通过球队名匹配成功: {pin888_standard_home_name} vs {pin888_standard_away_name}")

        event_detail_data = await subscribe_events_detail_euro(self.page, matched_event_id)
        if not event_detail_data:
            logger.error(f"[{handler_name}] 没有该场比赛 {spider_home} -- {spider_away}")
            return {'success': False, 'message': f'没有该场比赛 {spider_home} -- {spider_away}'}

    # 2.3 提取标准球队名称和剩余时间
    team_names_result = parse_team_names_from_detail_data(event_detail_data)

    if not team_names_result:
        logger.error(f"[{handler_name}] 未能提取标准球队名称")
        return {'success': False, 'message': '未能提取标准球队名称'}

    pin888_standard_home_name = team_names_result['pin888_home_name']
    pin888_standard_away_name = team_names_result['pin888_away_name']
    matchStateType = team_names_result['matchStateType']

    logger.info(f"[{handler_name}] ✅ 提取标准球队名称: {pin888_standard_home_name} vs {pin888_standard_away_name}")

    # 分析剩余时间
    remaining_time = analyze_remaining_time(match_state_type=matchStateType, sport_type=sport_type)

    if not remaining_time:
        logger.error(f"[{handler_name}] 未能分析剩余时间")
        return {'success': False, 'message': '未能分析剩余时间'}

    match_phase = remaining_time['match_phase']
    remaining_seconds = remaining_time['remaining_seconds']

    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    time_display = f"{minutes:02d}:{seconds:02d}"

    logger.info(f"[{handler_name}] ⏱️ 剩余时间: {match_phase} - {time_display} ({remaining_seconds}秒)")
    await self._send_message_to_electron(f"剩余时间: {match_phase} - {time_display} ({remaining_seconds}秒)")

    # ========== Step 3: 映射盘口参数 ==========
    logger.info(f"[{handler_name}] Step 3: 映射盘口参数")

    

    mapping_result = map_handicap_full(
        sport_type=sport_type,
        handicap=bet_data.get('spider_handicap'),
        period=bet_data.get('spider_period'),
        handicap_param=bet_data.get('spider_handicap_param'),
        home_team=pin888_standard_home_name,
        away_team=pin888_standard_away_name
    )

    if mapping_result is None:
        logger.error(f"[{handler_name}] Mapping 返回 None,不支持此盘口或时段")
        await unsubscribe_events_detail_euro(self.page, event_id)
        return {'success': False, 'message': 'Mapping 返回 None,不支持此盘口或时段'}

    mapped_market = mapping_result['mapped_market']
    mapped_handicap = mapping_result['mapped_handicap']
    mapped_handicap_param = mapping_result['mapped_handicap_param']
    mapped_period = mapping_result['mapped_period']
    mapped_direction = mapping_result.get('mapped_direction', '')
    mapped_match = mapping_result.get('mapped_match', '')

    logger.info(f"[{handler_name}] ✅ 映射成功: market={mapped_market}, handicap={mapped_handicap}")

    # ========== Step 4: 查找赔率 ==========
    logger.info(f"[{handler_name}] Step 4: 查找赔率")

   

    odds_result = find_odds_from_detail_data(
        sport_type=sport_type,
        market_group=mapped_market,
        platform_handicap=mapped_handicap,
        platform_handicap_param=mapped_handicap_param,
        platform_direction=mapped_direction,
        platform_match=mapped_match,
        period=mapped_period,
        detail_odds=event_detail_data
    )

    if odds_result == 'need refresh':
        logger.warning(f"[{handler_name}] 需要刷新详细赔率数据")
        await unsubscribe_events_detail_euro(self.page, event_id)
        return {'success': False, 'message': '需要刷新详细赔率数据'}

    if not odds_result:
        logger.error(f"[{handler_name}] 未能从详细赔率数据中找到匹配的赔率")
        await unsubscribe_events_detail_euro(self.page, event_id)
        return {'success': False, 'message': '未能从详细赔率数据中找到匹配的赔率'}

    parsed_odd = odds_result.get('odd')
    parsed_lineID = odds_result.get('lineID')
    parsed_market_group_id = odds_result.get('market_group_id')
    parsed_isAlt = odds_result.get('isAlt')
    parsed_specials_i = odds_result.get('specials_i')
    parsed_specials_event_id = odds_result.get('specials_event_id')

    logger.info(f"[{handler_name}] ✅ 成功解析赔率: odd={parsed_odd}, lineID={parsed_lineID}")

    # ========== Step 5: 构造下单参数 ==========
    logger.info(f"[{handler_name}] Step 5: 构造下单参数")

    

    mapping_result = map_bet_params_to_ids(
        sport_type=sport_type,
        handicap=bet_data.get('spider_handicap'),
        period=bet_data.get('spider_period'),
        direction=mapped_direction,
        match=mapped_match,
        handicap_param=mapped_handicap_param,
        line_id=parsed_lineID,
        market_group_id=parsed_market_group_id,
        is_alt=parsed_isAlt if parsed_isAlt else False,
        specials_i=parsed_specials_i if parsed_specials_i else 0,
        specials_event_id=parsed_specials_event_id if parsed_specials_event_id else 0
    )

    if not mapping_result:
        logger.error(f"[{handler_name}] 映射失败")
        await unsubscribe_events_detail_euro(self.page, event_id)
        return {'success': False, 'message': '映射失败'}

    oddsID = mapping_result['oddsID']
    oddsSelectionsType = mapping_result['oddsSelectionsType']
    selectionID = mapping_result['selectionID']

    logger.info(f"[{handler_name}] ✅ 成功映射参数: oddsID={oddsID}")

    # ========== Step 6: 验证盘口可用性 ==========
    logger.info(f"[{handler_name}] Step 6: 验证盘口可用性")

    

    response = await request_all_odds_selections(
        page=self.page,
        odds_id=oddsID,
        selection_id=selectionID,
        odds_selections_type=oddsSelectionsType,
        handler_name=handler_name
    )

    if not response:
        logger.error(f"[{handler_name}] 请求 [添加订单] 失败")
        await unsubscribe_events_detail_euro(self.page, event_id)
        return {'success': False, 'message': '请求 [添加订单] 失败'}

    # 解析响应数据
    try:
        response_data = json.loads(response['response'])
        if not response_data or len(response_data) == 0:
            logger.error(f"[{handler_name}] [添加订单] 响应数据为空")
            await unsubscribe_events_detail_euro(self.page, event_id)
            return {'success': False, 'message': '[添加订单] 响应数据为空'}

        data = response_data[0]

        response_selection_id = data.get('selectionId')
        odds_id = data.get('oddsId')
        odds = data.get('odds') or data.get('odd')
        max_stake = data.get('maxStake')
        status = data.get('status')

        if status == 'UNAVAILABLE':
            logger.warning(f"[{handler_name}] [添加订单]成功,但已封盘,不能下单")
            await self._send_message_to_electron('[添加订单]成功,但已封盘,不能下单')
            await unsubscribe_events_detail_euro(self.page, event_id)
            return {'success': False, 'message': '盘口已封盘'}

        if not oddsID or odds is None:
            logger.error(f"[{handler_name}] [添加订单]成功,但回复数据不完整")
            await self._send_message_to_electron('[添加订单]成功,但回复数据不完整')
            await unsubscribe_events_detail_euro(self.page, event_id)
            return {'success': False, 'message': '回复数据不完整'}

        # 存储订单记录
        self.order_record[order_id] = {
            'selectionId': response_selection_id,
            'oddsId': oddsID,
            'odds': str(odds),
            'maxStake': max_stake,
            'pin888_standard_home_name': pin888_standard_home_name,
            'pin888_standard_away_name': pin888_standard_away_name,
            'event_id': event_id,
            'event_detail_data': event_detail_data,
            'sport_type': sport_type,
            'sportId': sportId,
            'period_num': period_num,
            'msg': original_msg,
            'retry_count': 0,
            'spider_handicap': bet_data.get('spider_handicap'),
            'spider_period': bet_data.get('spider_period'),
            'spider_sport_type': sport_type,
            'mapped_market': mapped_market,
            'mapped_handicap': mapped_handicap,
            'mapped_handicap_param': mapped_handicap_param,
            'mapped_period': mapped_period,
            'mapped_direction': mapped_direction,
            'mapped_match': mapped_match,
            'remaining_seconds': remaining_seconds
        }

        await unsubscribe_events_detail_euro(self.page, event_id)

        # 计算执行时间
        duration = time.time() - start_time
        logger.info(f"[{handler_name}] ✅ GetOdd 完成 (耗时: {duration:.2f}秒)")

        return {
            'success': True,
            'handler_name': handler_name,
            'order_id': order_id,
            'platform_odd': odds,
            'platform_max_stake': max_stake,
            'match_phase': match_phase,
            'remaining_seconds': remaining_seconds,
            'spider_handicap': bet_data.get('spider_handicap'),
            'spider_period': bet_data.get('spider_period'),
            'sport_type': sport_type
        }

    except Exception as e:
        logger.error(f"[{handler_name}] 解析响应数据失败: {e}", exc_info=True)
        await unsubscribe_events_detail_euro(self.page, event_id)
        return {'success': False, 'message': f'解析响应数据失败: {str(e)}'}
