# -*- coding: utf-8 -*-
"""
Pin888 补充订单
"""
from typing import Dict, Any, Optional, Tuple
import logging
import time
import asyncio
import json

from core.config import config
from ..responseAnalysis import (
    find_odds_from_detail_data,
    find_odds_from_detail_data_with_range,
)
from ..handler import map_bet_params_to_ids, calculate_arbitrage_range
from ..jsCodeExecutors import request_all_odds_selections, unsubscribe_events_detail_euro

logger = logging.getLogger(__name__)


# ==================== 辅助函数 ====================

def _extract_supplement_context(
    self,
    dispatch_message: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    从调度消息和订单记录中提取补单所需的上下文数据
    """
    handler_name = self.handler_name

    order_id = dispatch_message.get('order_id')
    if not order_id:
        logger.error(f"[{handler_name}] 补单缺少 order_id")
        return None

    record = self.order_record.get(order_id)
    if not record:
        logger.error(f"[{handler_name}] 补单未找到订单记录: {order_id}")
        return None

    bet_core = dispatch_message.get('bet_data') or {}
    bet_info = dict(bet_core)
    for key, value in dispatch_message.items():
        if key == 'bet_data':
            continue
        bet_info[key] = value

    def _pick(key: str) -> Any:
        value = dispatch_message.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            value = bet_core.get(key)
        return value

    pin_home = record.get('pin888_standard_home_name') or _pick('fail_platform_home')
    pin_away = record.get('pin888_standard_away_name') or _pick('fail_platform_away')
    event_id = record.get('event_id') or _pick('bookmaker_event_direct_link') or _pick('event_id')

    sport_id = record.get('sportId')
    if sport_id in (None, ''):
        sport_id = _pick('sportsID')
    try:
        sport_id = int(sport_id) if sport_id not in (None, '') else None
    except (TypeError, ValueError):
        logger.warning(f"[{handler_name}] sportId 无法解析: {sport_id}")

    period_num = record.get('period_num') or _pick('periodNum')
    sport_type = record.get('sport_type') or bet_core.get('spider_sport_type')

    mapped_fields = [
        record.get('mapped_market'),
        record.get('mapped_handicap'),
        record.get('mapped_handicap_param'),
        record.get('mapped_direction'),
        record.get('mapped_match'),
        record.get('mapped_period'),
    ]
    if any(value is None for value in mapped_fields):
        logger.error(f"[{handler_name}] 订单记录缺少盘口映射信息")
        return None

    if not all([pin_home, pin_away, event_id, sport_id, period_num, sport_type]):
        logger.error(f"[{handler_name}] 补单缺少必要的赛事信息")
        return None

    if not all([
        record.get('spider_handicap'),
        record.get('spider_period'),
        record.get('spider_sport_type'),
    ]):
        logger.error(f"[{handler_name}] 订单记录缺少 spider_* 参数,无法映射下注ID")
        return None

    return {
        'order_id': order_id,
        'record': record,
        'bet_info': bet_info,
        'pin_home': pin_home,
        'pin_away': pin_away,
        'event_id': event_id,
        'sport_id': sport_id,
        'sport_type': sport_type,
        'period_num': period_num,
        'mapped_market': record.get('mapped_market'),
        'mapped_handicap': record.get('mapped_handicap'),
        'mapped_handicap_param': record.get('mapped_handicap_param'),
        'mapped_direction': record.get('mapped_direction'),
        'mapped_match': record.get('mapped_match'),
        'mapped_period': record.get('mapped_period'),
        'spider_handicap': record.get('spider_handicap'),
        'spider_period': record.get('spider_period'),
        'spider_sport_type': record.get('spider_sport_type'),
    }


def _init_retry_context(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    初始化补单重试与超时配置
    """
    retry_count = int(record.get('retry_count', 0) or 0)
    max_retry = config.get_max_retry_count()
    remaining_seconds = record.get('remaining_seconds')
    try:
        remaining_seconds = float(remaining_seconds)
    except (TypeError, ValueError):
        remaining_seconds = None

    if not remaining_seconds or remaining_seconds <= 0:
        remaining_seconds = config.get_supplementary_order_timeout()

    return {
        'retry_count': retry_count,
        'max_retry': max_retry,
        'remaining_seconds': remaining_seconds,
    }


def _cycle_control_allows_retry(self) -> bool:
    """
    检查补单循环总开关
    """
    platform_state = self.online_platform
    if platform_state is None:
        platform_state = {}
        self.online_platform = platform_state
    if 'PIN888_CYCLEING' not in platform_state:
        platform_state['PIN888_CYCLEING'] = True

    if not platform_state['PIN888_CYCLEING']:
        logger.warning(f"[{self.handler_name}] PIN888_CYCLEING 已关闭,终止补单循环")
        platform_state['PIN888_CYCLEING'] = True
        return False
    return True


async def _fetch_event_detail(
    self,
    context: Dict[str, Any]
) -> Tuple[Optional[str], Optional[Any]]:
    """
    根据球队信息获取最新的 event_id 以及详细赔率
    """
    try:
        event_id, event_detail_data = await self.get_event_id(
            sportId=context['sport_id'],
            period_num=context['period_num'],
            spider_home=context['pin_home'],
            spider_away=context['pin_away'],
            event_id=context['event_id'],
        )
        return event_id, event_detail_data
    except Exception as exc:
        logger.error(f"[{self.handler_name}] 获取赛事详情失败: {exc}", exc_info=True)
        return None, None


def _locate_target_odds(
    self,
    context: Dict[str, Any],
    event_detail_data: Any
) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    在赔率详情中定位目标盘口

    Returns:
        (result, need_refresh)
    """
    bet_info = context['bet_info']
    success_handicap = (bet_info.get('success_platform_handicap') or '').lower()
    success_param = bet_info.get('success_platform_handicap_param', '')

    is_draw_no_bet = "draw no bet" in success_handicap
    is_total = "total" in success_handicap and (
        "over" in success_handicap or "under" in success_handicap
    )
    is_handicap = (
        "handicap" in success_handicap
        and ("handicap1" in success_handicap or "handicap2" in success_handicap)
        and not is_draw_no_bet
    )

    if (is_total or is_handicap) and success_param:
        arbitrage_condition = calculate_arbitrage_range(
            success_platform_handicap=bet_info.get('success_platform_handicap', ''),
            success_platform_handicap_param=success_param
        )
        if not arbitrage_condition:
            return None, False

        odds_result = find_odds_from_detail_data_with_range(
            sport_type=context['sport_type'],
            market_group=context['mapped_market'],
            platform_handicap=context['mapped_handicap'],
            platform_direction=context['mapped_direction'],
            platform_match=context['mapped_match'],
            period=context['mapped_period'],
            detail_odds=event_detail_data,
            range_condition=arbitrage_condition
        )
    else:
        odds_result = find_odds_from_detail_data(
            sport_type=context['sport_type'],
            market_group=context['mapped_market'],
            platform_handicap=context['mapped_handicap'],
            platform_handicap_param=context['mapped_handicap_param'],
            platform_direction=context['mapped_direction'],
            platform_match=context['mapped_match'],
            period=context['mapped_period'],
            detail_odds=event_detail_data
        )

    if odds_result == 'need refresh':
        return None, True

    if odds_result:
        logger.info(
            f"[{self.handler_name}] 赔率匹配成功: lineID={odds_result.get('lineID')} odd={odds_result.get('odd')}"
        )
    else:
        logger.warning(f"[{self.handler_name}] 未在详细赔率数据中找到匹配盘口")

    return odds_result, False


def _evaluate_odds_change(
    bet_info: Dict[str, Any],
    current_odd: Any
) -> Optional[Dict[str, float]]:
    """
    评估当前赔率相对对手成功赔率的变化幅度
    """
    fail_odd = bet_info.get('fail_platform_final_odd')
    if fail_odd is None or current_odd is None:
        return None

    try:
        fail_value = float(fail_odd)
        current_value = float(current_odd)
    except (TypeError, ValueError):
        return None

    if fail_value == 0:
        return None

    odds_change_percent = ((current_value - fail_value) / fail_value) * 100
    drop_threshold = config.get_odds_drop_threshold()

    return {
        'percent': odds_change_percent,
        'should_wait': odds_change_percent < -drop_threshold
    }


def _calculate_optimal_betting_amount(
    opponent_amount: float,
    opponent_odds: float,
    our_odds: float
) -> float:
    """
    计算套利时的最优投注金额
    """
    if our_odds in (None, 0):
        return 0.0

    return (opponent_amount * opponent_odds) / our_odds


async def _calculate_target_amount(
    self,
    record: Dict[str, Any],
    bet_info: Dict[str, Any],
    current_odd: Any
) -> float:
    """
    根据套利信息或原始记录计算本次补单金额
    """
    def _to_float(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    opponent_amount = _to_float(bet_info.get('success_platform_final_bet'))
    opponent_odds = _to_float(bet_info.get('success_platform_final_odd'))
    our_odds = _to_float(current_odd)

    if opponent_amount and opponent_odds and our_odds:
        try:
            optimal_amount = _calculate_optimal_betting_amount(
                opponent_amount=opponent_amount,
                opponent_odds=opponent_odds,
                our_odds=our_odds
            )
            betting_amount = round(float(optimal_amount), 1)
            await self._send_message_to_electron(
                f"[PIN888] 套利计算: 对手${opponent_amount}@{opponent_odds}, "
                f"最优金额${betting_amount}"
            )
            return betting_amount
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"[{self.handler_name}] 套利金额计算失败: {exc}")

    fallback = record.get('betting_amount', bet_info.get('betting_amount'))
    fallback_value = _to_float(fallback)
    return fallback_value or 0.0


async def _prepare_selection_update(
    self,
    context: Dict[str, Any],
    odds_result: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    重新映射盘口参数并通过请求确认可用性
    """
    mapping_result = map_bet_params_to_ids(
        sport_type=context['spider_sport_type'],
        handicap=context['spider_handicap'],
        period=context['spider_period'],
        direction=context['mapped_direction'],
        match=context['mapped_match'],
        handicap_param=context['mapped_handicap_param'],
        line_id=odds_result.get('lineID'),
        market_group_id=odds_result.get('market_group_id'),
        is_alt=odds_result.get('isAlt') or False,
        specials_i=odds_result.get('specials_i') or 0,
        specials_event_id=odds_result.get('specials_event_id') or 0
    )

    if not mapping_result:
        logger.error(f"[{self.handler_name}] 映射下注参数失败")
        return None

    response = await request_all_odds_selections(
        page=self.page,
        odds_id=mapping_result['oddsID'],
        selection_id=mapping_result['selectionID'],
        odds_selections_type=mapping_result['oddsSelectionsType'],
        handler_name=self.handler_name
    )

    if not response:
        logger.error(f"[{self.handler_name}] 请求 [添加订单] 失败")
        return None

    try:
        parsed_response = json.loads(response.get('response', '[]'))
    except json.JSONDecodeError as exc:
        logger.error(f"[{self.handler_name}] 解析 [添加订单] 响应失败: {exc}")
        return None

    if isinstance(parsed_response, list) and parsed_response:
        data = parsed_response[0]
    elif isinstance(parsed_response, dict):
        data = parsed_response
    else:
        logger.error(f"[{self.handler_name}] [添加订单] 响应数据为空")
        return None

    status = data.get('status')
    if status == 'UNAVAILABLE':
        logger.warning(f"[{self.handler_name}] [添加订单] 成功但盘口已封盘")
        await self._send_message_to_electron('[PIN888] [添加订单]成功,但已封盘,不能下单')
        return None

    odds = data.get('odds') or data.get('odd')
    selection_id = data.get('selectionId') or mapping_result['selectionID']
    odds_id = data.get('oddsId') or mapping_result['oddsID']

    if odds is None:
        logger.error(f"[{self.handler_name}] [添加订单] 响应缺少赔率字段")
        await self._send_message_to_electron('[PIN888] [添加订单]成功,但回复数据不完整')
        return None

    return {
        'selection_id': selection_id,
        'odds_id': odds_id,
        'odds': odds,
        'max_stake': data.get('maxStake')
    }


# ==================== 主函数 ====================

async def SupplementaryOrder(
    self,
    dispatch_message: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
    Pin888 补单主流程
    """
    handler_name = self.handler_name
    logger.info(f"[{handler_name}] ========== 开始 SupplementaryOrder ==========")

    self._is_SupplementaryOrder = True
    failure_reason = 'timeout'

    try:
        context = _extract_supplement_context(self, dispatch_message)
        if not context:
            return {'success': False, 'message': '补单缺少必要参数'}

        retry_state = _init_retry_context(context['record'])
        start_time = time.time()
        timeout_seconds = retry_state['remaining_seconds']

        await self._send_message_to_electron(
            f"[PIN888] 补单窗口 {timeout_seconds:.0f} 秒,最多重试 {retry_state['max_retry']} 次"
        )

        while time.time() - start_time < timeout_seconds:
            attempt = retry_state['retry_count'] + 1
            if attempt > retry_state['max_retry']:
                failure_reason = 'retry_count_max'
                break

            if not _cycle_control_allows_retry(self):
                failure_reason = 'cycle_closed'
                break

            logger.info(
                f"[{handler_name}] 第 {attempt}/{retry_state['max_retry']} 次尝试补单, "
                f"已耗时 {time.time() - start_time:.1f}s"
            )

            event_id, event_detail_data = await _fetch_event_detail(self, context)
            context['event_id'] = event_id

            if not event_id or not event_detail_data:
                retry_state['retry_count'] += 1
                context['record']['retry_count'] = retry_state['retry_count']
                await asyncio.sleep(2)
                continue

            try:
                odds_result, need_refresh = _locate_target_odds(self, context, event_detail_data)
                if need_refresh:
                    logger.info(f"[{handler_name}] 赔率数据需要刷新,等待重试")
                    await asyncio.sleep(2)
                    continue

                if not odds_result:
                    retry_state['retry_count'] += 1
                    context['record']['retry_count'] = retry_state['retry_count']
                    await asyncio.sleep(2)
                    continue

                parsed_odd = odds_result.get('odd')
                odds_change = _evaluate_odds_change(context['bet_info'], parsed_odd)
                if odds_change:
                    percent = odds_change['percent']
                    if odds_change['should_wait']:
                        logger.info(
                            f"[{handler_name}] 赔率下降 {abs(percent):.2f}%,超过阈值,等待更好盘口"
                        )
                        await self._send_message_to_electron(
                            f"[PIN888] 赔率下降 {abs(percent):.2f}% 超过阈值,继续等待"
                        )
                        await asyncio.sleep(2)
                        continue
                    else:
                        trend = "下降" if percent < 0 else "上升"
                        logger.info(f"[{handler_name}] 赔率{trend} {percent:.2f}% 在可接受范围内")

                betting_amount = await _calculate_target_amount(
                    self,
                    context['record'],
                    context['bet_info'],
                    parsed_odd
                )

                if betting_amount <= 0:
                    failure_reason = 'invalid_amount'
                    logger.error(f"[{handler_name}] 无法确定补单金额")
                    break

                selection_update = await _prepare_selection_update(self, context, odds_result)
                if not selection_update:
                    retry_state['retry_count'] += 1
                    context['record']['retry_count'] = retry_state['retry_count']
                    await asyncio.sleep(2)
                    continue

                record = context['record']
                record['selectionId'] = selection_update['selection_id']
                record['odds'] = str(selection_update['odds'])
                record['oddsId'] = selection_update['odds_id']
                record['betting_amount'] = betting_amount
                if selection_update.get('max_stake') is not None:
                    record['maxStake'] = selection_update['max_stake']

                retry_msg = {
                    'order_id': context['order_id'],
                    'betting_amount': betting_amount
                }
                result = await self.BettingOrder(retry_msg)

                if result and result.get('success'):
                    ticket_id = result.get('ticket_id')
                    success_message = {
                        "type": "supplement_order",
                        "from": "automation",
                        "to": "dispatch",
                        "data": {
                            "order_id": context['order_id'],
                            "handler_name": handler_name,
                            "betting_amount": betting_amount,
                            "betting_odd": record['odds'],
                            "betting_success": True,
                            "ticket_id": ticket_id,
                            "is_supplementary_order": self._is_SupplementaryOrder,
                        }
                    }
                    if self.ws_client:
                        await self.ws_client.send(success_message)

                    await self._send_message_to_electron(
                        f"[{handler_name}] [PIN888] 补单成功,订单号: {ticket_id}, "
                        f"赔率: {record['odds']}, 金额: {betting_amount}"
                    )

                    return {
                        'success': True,
                        'order_id': context['order_id'],
                        'ticket_id': ticket_id,
                        'betting_amount': betting_amount,
                        'betting_odd': record['odds'],
                        'message': '补单成功'
                    }

                logger.warning(f"[{handler_name}] 补单下注失败,准备重试")
                retry_state['retry_count'] += 1
                context['record']['retry_count'] = retry_state['retry_count']

                if retry_state['retry_count'] >= retry_state['max_retry']:
                    failure_reason = 'retry_count_max'
                    break

                await asyncio.sleep(2)

            finally:
                if event_id:
                    try:
                        await unsubscribe_events_detail_euro(self.page, event_id)
                    except Exception as exc:  # noqa: BLE001
                        logger.debug(f"[{handler_name}] 取消订阅赛事失败: {exc}")

        failure_message = {
            "type": "supplement_order_failed",
            "from": "automation",
            "to": "dispatch",
            "data": {
                "order_id": context['order_id'],
                "handler_name": handler_name,
                "result": failure_reason,
                "is_supplementary_order": self._is_SupplementaryOrder,
            }
        }
        if self.ws_client:
            await self.ws_client.send(failure_message)

        await self._send_message_to_electron(f"[PIN888] 补单失败: {failure_reason}")
        return {'success': False, 'order_id': context['order_id'], 'message': f'补单失败: {failure_reason}'}

    except Exception as exc:  # noqa: BLE001
        logger.error(f"[{handler_name}] 补单流程异常: {exc}", exc_info=True)
        order_id = dispatch_message.get('order_id')
        if self.ws_client and order_id:
            await self.ws_client.send({
                "type": "supplement_order_failed",
                "from": "automation",
                "to": "dispatch",
                "data": {
                    "order_id": order_id,
                    "handler_name": handler_name,
                    "result": "exception",
                    "is_supplementary_order": self._is_SupplementaryOrder,
                }
            })
        await self._send_message_to_electron(f"[PIN888] 补单异常: {exc}")
        return {'success': False, 'message': f'补单异常: {exc}'}

    finally:
        self._is_SupplementaryOrder = False
