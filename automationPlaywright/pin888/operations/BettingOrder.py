# -*- coding: utf-8 -*-
"""
Pin888 下注订单
"""
from typing import Dict, Any, Optional
import logging
import time
import asyncio
import json
import math

# 导入 jsCodeExecutors
from ..jsCodeExecutors import request_buy_v2, request_my_bets
from .GetBalance import GetBalanceByRequest

logger = logging.getLogger(__name__)


# ==================== 辅助函数 ====================

def _validate_betting_params(
    self,
    dispatch_message: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    验证下注参数

    Args:
        dispatch_message: 调度消息，包含 order_id 和 betting_amount

    Returns:
        {
            'order_id': str,
            'record': dict,
            'bet_amount_usd': float
        }
        或 None (验证失败)

    Examples:
        >>> params = _validate_betting_params(self, msg)
        >>> params['order_id']
        'order_123'
    """
    handler_name = self.handler_name

    # 1. 验证 order_id
    order_id = dispatch_message.get('order_id', '')
    if not order_id:
        logger.error(f"[{handler_name}] 缺少必要参数 order_id")
        return None

    # 2. 验证订单记录存在
    record = self.order_record.get(order_id)
    if not record:
        logger.error(f"[{handler_name}] 未找到订单记录: {order_id}")
        return None

    # 3. 验证下注金额
    bet_amount_usd = float(dispatch_message.get('betting_amount', 0))
    if not bet_amount_usd or bet_amount_usd <= 0:
        logger.error(f"[{handler_name}] bet_amount 为空或无效: {bet_amount_usd}")
        return None

    logger.info(f"[{handler_name}] 💰 下注金额: {bet_amount_usd} USD")

    return {
        'order_id': order_id,
        'record': record,
        'bet_amount_usd': bet_amount_usd
    }


async def _check_and_adjust_balance(
    self,
    bet_amount_usd: float
) -> Optional[float]:
    """
    检查余额并调整下注金额

    Args:
        bet_amount_usd: 原始下注金额

    Returns:
        调整后的下注金额，或 None (余额获取失败)

    Examples:
        >>> adjusted = await _check_and_adjust_balance(self, 100.0)
        >>> adjusted
        50.0  # 余额不足时自动调整
    """
    handler_name = self.handler_name

    # 1. 获取余额
    balance = self.online_platform.get('balance')
    if balance is None:
        logger.error(f"[{handler_name}] 获取余额失败")
        return None

    balance = float(balance)
    logger.info(f"[{handler_name}] 💰 当前余额: {balance:.1f} XRP")

    # 2. 余额不足时自动调整
    if balance < bet_amount_usd:
        # 向下取整到1位小数，确保不超过余额
        adjusted_amount = math.floor(balance * 10) / 10
        logger.warning(
            f"[{handler_name}] ⚠️ 余额不足，调整下注金额: "
            f"{bet_amount_usd} → {adjusted_amount} XRP (真实余额: {balance})"
        )
        return adjusted_amount

    return bet_amount_usd


async def _send_betting_request(
    self,
    bet_amount: float,
    record: Dict[str, Any],
    order_id: str
) -> Optional[Dict[str, Any]]:
    """
    发送下注请求

    Args:
        bet_amount: 下注金额
        record: 订单记录
        order_id: 订单 ID

    Returns:
        响应数据字典，或 None (失败)

    Examples:
        >>> response = await _send_betting_request(self, 10.5, record, 'order_123')
        >>> response['status']
        200
    """
    handler_name = self.handler_name

    logger.info(
        f"[{handler_name}] ✅ 发送下注请求: "
        f"order_id={order_id}, stake={bet_amount}, odds={record['odds']}"
    )
    await self._send_message_to_electron(
        f"✅ [PIN888] 发送下注请求: order_id={order_id}, "
        f"stake={bet_amount}, odds={record['odds']}"
    )

    # 调用 jsCodeExecutor
    response = await request_buy_v2(
        page=self.page,
        stake=bet_amount,
        odds=record['odds'],
        odds_id=record['oddsId'],
        selection_id=record['selectionId'],
        handler_name=handler_name
    )

    if not response:
        logger.error(f"[{handler_name}] 下注请求返回空响应")
        await self._send_message_to_electron("[PIN888] 下注请求返回空响应")
        return None

    if response.get('error'):
        logger.error(f"[{handler_name}] 下注失败: {response.get('error')}")
        await self._send_message_to_electron(f"[PIN888] 下注失败: {response.get('error')}")
        return None

    if response.get('status') != 200:
        logger.error(f"[{handler_name}] 下注失败，HTTP状态码: {response.get('status')}")
        logger.debug(f"[{handler_name}] 响应: {json.dumps(response, indent=2)}")
        await self._send_message_to_electron(
            f"[PIN888] 下注失败，HTTP状态码: {response.get('status')}"
        )
        return None

    return response


def _parse_betting_response(
    self,
    response: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    解析下注响应数据

    Args:
        response: 原始响应数据

    Returns:
        {
            'wager_id': str,
            'odds': float,
            'status': str,
            'bet_result': dict  # 原始数据
        }
        或 None (解析失败)

    Examples:
        >>> parsed = _parse_betting_response(self, response)
        >>> parsed['status']
        'ACCEPTED'
    """
    handler_name = self.handler_name

    try:
        response_content = response.get('response', '{}')

        # 尝试解析为 JSON
        if isinstance(response_content, str):
            response_data = json.loads(response_content)
        else:
            response_data = response_content

        # 如果 response_data 是字典且包含 'response' 键，提取内层数组
        if isinstance(response_data, dict) and 'response' in response_data:
            response_data = response_data['response']

        # 检查是否有错误码
        error_code = None
        error_message = None

        if error_code or error_message:
            logger.error(f"[{handler_name}] 下注失败")
            logger.error(f"[{handler_name}]   错误代码: {error_code}")
            logger.error(f"[{handler_name}]   错误信息: {error_message}")
            logger.debug(
                f"[{handler_name}]   完整响应: "
                f"{json.dumps(response, indent=2, ensure_ascii=False)}"
            )

            await self._send_message_to_electron(
                f"[PIN888] 下注失败 - 错误码: {error_code}, 错误信息: {error_message}"
            )

            return None

        # 检查是否是数组格式的成功响应
        if isinstance(response_data, list) and len(response_data) > 0:
            bet_result = response_data[0]
            wager_id = bet_result.get('wagerId')
            odds = bet_result.get('odds')
            status = bet_result.get('status')

            return {
                'wager_id': wager_id,
                'odds': odds,
                'status': status,
                'bet_result': bet_result
            }
        else:
            logger.error(f"[{handler_name}] 响应格式不正确")
            logger.debug(
                f"[{handler_name}]   响应数据: "
                f"{json.dumps(response_data, indent=2, ensure_ascii=False)}"
            )
            await self._send_message_to_electron("[PIN888] 响应格式不正确")
            return None

    except json.JSONDecodeError as e:
        logger.error(f"[{handler_name}] 解析响应数据失败: {e}")
        logger.debug(f"[{handler_name}] 原始响应: {response.get('response')}")
        return None


async def _handle_pending_acceptance(
    self,
    wager_id: str,
    odds: float,
    bet_amount_usd: float
) -> Optional[Dict[str, Any]]:
    """
    处理 PENDING_ACCEPTANCE 状态（轮询查询订单状态）

    Args:
        wager_id: 投注 ID
        odds: 赔率
        bet_amount_usd: 下注金额

    Returns:
        {
            'success': True,
            'ticket_id': str,
            'betting_odd': float,
            'betting_amount': float,
            'status': str,
            'is_supplementary_order': bool
        }
        或 None (失败/超时)

    Examples:
        >>> result = await _handle_pending_acceptance(self, '123456', 1.95, 10.0)
        >>> result['success']
        True
    """
    handler_name = self.handler_name

    logger.info(f'[{handler_name}] 状态为 PENDING_ACCEPTANCE ....')
    await self._send_message_to_electron("[PIN888] PENDING_ACCEPTANCE ....")

    await asyncio.sleep(1)

    # 第一次获取投注记录
    my_bets_response = await request_my_bets(self.page, handler_name)

    if my_bets_response is None:
        logger.error(f"[{handler_name}] 获取投注记录失败")
        return None

    logger.debug(f"[{handler_name}] 📊 初次获取投注记录数: {len(my_bets_response)}")

    # 轮询查询订单状态（最多30次）
    num = 0
    while num < 30:
        logger.info(f"[{handler_name}] 🔄 [轮询 {num+1}/30] 检查投注状态...")

        # 遍历所有投注记录
        for bet in my_bets_response:
            if not isinstance(bet, list) or len(bet) < 12:
                logger.debug(f"[{handler_name}] ⚠️ 跳过无效记录，类型: {type(bet)}")
                continue

            logger.debug(
                f"[{handler_name}] 📝 检查投注记录: "
                f"WagerID={bet[0]}, 状态={bet[11] if len(bet) > 11 else 'unknown'}"
            )

            # 检查是否是当前的 wager_id
            if str(bet[0]) == str(wager_id):
                logger.info(f"[{handler_name}] ✅ [找到匹配] WagerID: {wager_id}")

                # 获取状态字段（索引 11）
                bet_status = bet[11] if len(bet) > 11 else ""
                logger.debug(
                    f"[{handler_name}] 📊 [状态检查] "
                    f"bet_status = {bet_status}, 类型 = {type(bet_status)}"
                )

                # 1. 判断是否为 PENDING
                if bet_status == 'PENDING':
                    logger.info(f"[{handler_name}] ⏳ [PENDING] 订单还在处理中，继续等待...")
                    await asyncio.sleep(1)
                    break  # 跳出 for 循环，继续 while 循环等待

                # 2. 不是 PENDING，说明已经结算了
                # 3. 只有在非 PENDING 状态下，验证是否有 reject
                has_rejected = any('rejected' in str(value).lower() for value in bet)

                if has_rejected:
                    # 整个数组中发现 rejected，判定为失败
                    logger.error(f"[{handler_name}] ❌ 下注失败 - 数组中发现 'rejected'")
                    logger.debug(f"[{handler_name}]    完整记录: {bet}")
                    await self._send_message_to_electron(
                        f"[PIN888] 下注失败 - WagerID: {wager_id}, 状态: Rejected"
                    )
                    return None
                else:
                    # 整个数组中都没有 rejected，判定为成功
                    logger.info(
                        f"[{handler_name}] ✅ 下注成功 - "
                        f"数组中无 'rejected'，状态: {bet_status}"
                    )
                    await self._send_message_to_electron(
                        f"[PIN888] 下注成功 - WagerID: {wager_id}, 状态: {bet_status}"
                    )

                    # 更新余额
                    await _update_balance_after_bet(self)

                    return {
                        'success': True,
                        'ticket_id': wager_id,
                        'betting_odd': bet[9] if len(bet) > 9 else odds,
                        'betting_amount': bet_amount_usd,
                        'status': bet_status,
                        'is_supplementary_order': self._is_SupplementaryOrder,
                    }

        # 未找到匹配记录，继续等待
        num += 1
        if num >= 30:
            logger.warning(f"[{handler_name}] ⏱️ [超时] 已等待 30 次，仍未找到 WagerID: {wager_id}")
            await asyncio.sleep(1)
            break

        await asyncio.sleep(1)

        # 重新获取投注记录
        my_bets_response = await request_my_bets(self.page, handler_name)
        if my_bets_response is None:
            logger.error(f"[{handler_name}] 重新获取投注记录失败")
            return None

        logger.debug(f"[{handler_name}] 🔄 [刷新] 投注记录数: {len(my_bets_response)}")

    # 超时仍未找到
    await self._send_message_to_electron("[PIN888] 超时 - 未能确认投注状态")
    return None


async def _update_balance_after_bet(self):
    """
    下注成功后更新余额

    流程:
    1. 调用 GetBalanceByRequest 获取最新余额
    2. 更新 online_platform['balance']
    3. 发送 WebSocket 消息到 dispatch

    Examples:
        >>> await _update_balance_after_bet(self)
    """
    handler_name = self.handler_name

    # 重新获取最新余额
    new_balance = await GetBalanceByRequest(self)

    if new_balance:
        # 更新到 online_platform
        self.online_platform['balance'] = new_balance

        # 发送余额更新给 dispatch
        if self.ws_client:
            try:
                await self.ws_client.send({
                    'type': 'balance_update',
                    'from': 'automation',
                    'to': 'dispatch',
                    'data': {
                        'handler_name': handler_name,
                        'balance': new_balance
                    }
                })
                logger.info(f"[{handler_name}] 📤 余额已更新并发送: {new_balance}")
            except Exception as e:
                logger.warning(f"[{handler_name}] ⚠️ 发送余额失败: {e}")


# ==================== 主函数 ====================

async def BettingOrder(
    self,
    dispatch_message: Dict[str, Any],
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    下注订单（完整流程）

    6步流程:
    1. 参数提取与验证
    2. 余额检查与调整
    3. 发送下注请求
    4. 解析响应数据
    5. 处理不同状态（ACCEPTED/PENDING_ACCEPTANCE/ERROR）
    6. 更新余额并返回结果

    Args:
        dispatch_message: {
            'order_id': str,
            'betting_amount': float
        }
        **kwargs: 额外参数

    Returns:
        {
            'success': True,
            'ticket_id': str,
            'betting_odd': float,
            'betting_amount': float,
            'status': str,
            'is_supplementary_order': bool
        }
        或 None (失败)

    Examples:
        >>> result = await BettingOrder(self, {
        ...     'order_id': 'order_123',
        ...     'betting_amount': 10.5
        ... })
        >>> result['success']
        True
    """
    bet_start_time = time.time()
    handler_name = self.handler_name

    logger.info(f"[{handler_name}] ========== 开始 BettingOrder 流程 ==========")

    try:
        # ========== Step 1: 参数提取与验证 ==========
        logger.info(f"[{handler_name}] Step 1: 参数提取与验证")

        params = _validate_betting_params(self, dispatch_message)
        if not params:
            return None

        order_id = params['order_id']
        record = params['record']
        bet_amount_usd = params['bet_amount_usd']

        # 存储下注金额到订单记录
        self.order_record[order_id]['betting_amount'] = bet_amount_usd

        # ========== Step 2: 余额检查与调整 ==========
        logger.info(f"[{handler_name}] Step 2: 余额检查与调整")

        bet_amount = await _check_and_adjust_balance(self, bet_amount_usd)
        if bet_amount is None:
            return None

        # ========== Step 3: 发送下注请求 ==========
        logger.info(f"[{handler_name}] Step 3: 发送下注请求")

        response = await _send_betting_request(self, bet_amount, record, order_id)
        if not response:
            return None

        # ========== Step 4: 解析响应数据 ==========
        logger.info(f"[{handler_name}] Step 4: 解析响应数据")

        parsed = _parse_betting_response(self, response)
        if not parsed:
            # 响应格式不正确，尝试更新余额
            new_balance = await GetBalanceByRequest(self)
            if new_balance:
                self.online_platform['balance'] = new_balance
            return None

        wager_id = parsed['wager_id']
        odds = parsed['odds']
        status = parsed['status']

        # ========== Step 5: 处理不同状态 ==========
        logger.info(f"[{handler_name}] Step 5: 处理状态 - {status}")

        # 5.1 ACCEPTED - 下注成功
        if status == 'ACCEPTED':
            logger.info(f"[{handler_name}] ✅ 下注成功")
            logger.info(f"[{handler_name}]   Wager ID: {wager_id}")
            logger.info(f"[{handler_name}]   赔率: {odds}")
            logger.info(f"[{handler_name}]   状态: {status}")

            # 计算下注执行时间
            bet_duration = time.time() - bet_start_time
            logger.info(f"[{handler_name}] ⏱️ BettingOrder 执行时间: {bet_duration:.3f}秒")

            # 发送 WebSocket 日志
            await self._send_message_to_electron(
                f"[PIN888] 下注成功 - WagerID: {wager_id}, "
                f"状态: {status}, 耗时: {bet_duration:.3f}秒"
            )
            await self._send_message_to_electron(
                f"[PIN888] 下注成功 - 金额：${bet_amount}, 赔率： {odds}"
            )

            # 更新余额
            await _update_balance_after_bet(self)

            return {
                'success': True,
                'ticket_id': wager_id,
                'betting_odd': odds,
                'betting_amount': bet_amount_usd,
                'status': status,
                'is_supplementary_order': self._is_SupplementaryOrder,
            }

        # 5.2 PENDING_ACCEPTANCE - 需要轮询查询
        elif status == 'PENDING_ACCEPTANCE':
            return await _handle_pending_acceptance(
                self, wager_id, odds, bet_amount_usd
            )

        # 5.3 PROCESSED_WITH_ERROR - 下注失败
        elif status == 'PROCESSED_WITH_ERROR':
            logger.error(f"[{handler_name}] ❌ 下注失败，状态: PROCESSED_WITH_ERROR")
            logger.debug(f"[{handler_name}]   错误信息: {parsed['bet_result']}")
            await self._send_message_to_electron(
                f"[PIN888] 下注失败 - 状态: PROCESSED_WITH_ERROR"
            )
            return None

        # 5.4 其他状态
        else:
            logger.error(f"[{handler_name}] ❌ 下注失败，状态: {status}")
            await self._send_message_to_electron(
                f"[PIN888] 下注失败 - WagerID: {wager_id}, 状态: {status}"
            )
            return None

    except Exception as e:
        logger.error(f"[{handler_name}] ❌ 执行下注请求失败: {e}", exc_info=True)
        return None
