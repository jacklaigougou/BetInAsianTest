# -*- coding: utf-8 -*-
"""
BetInAsian 获取余额

从 WebSocket 数据存储中获取实时余额信息
"""
from typing import Dict, Any
import logging
import time
import math

logger = logging.getLogger(__name__)


def truncate_to_2_decimals(value: float) -> float:
    """
    截断到2位小数（不四舍五入）

    Args:
        value: 原始数值

    Returns:
        截断后的数值

    Examples:
        >>> truncate_to_2_decimals(100.34719999999999)
        100.34
        >>> truncate_to_2_decimals(99.999)
        99.99
    """
    return math.floor(value * 100) / 100


async def GetBalance(self, **kwargs) -> Dict[str, Any]:
    """
    获取账户余额

    从 WebSocket 数据存储中查询当前余额，并更新到 self.online_platform

    Args:
        **kwargs: 额外参数
            - update_platform: 是否更新 online_platform (默认: True)
            - wait_timeout: 等待余额数据的超时时间（秒，默认: 5）

    Returns:
        {
            'success': bool,
            'balance': float,
            'currency': str,
            'open_stake': float,
            'smart_credit': float,
            'last_update': int,
            'message': str,
            'handler_name': str,
            'timestamp': float
        }

    Examples:
        >>> # 获取余额
        >>> result = await self.GetBalance()
        >>> if result['success']:
        ...     print(f"余额: {result['balance']} {result['currency']}")
        ...     print(f"未结算: {result['open_stake']}")
    """
    handler_name = self.handler_name
    update_platform = kwargs.get('update_platform', True)
    wait_timeout = kwargs.get('wait_timeout', 5)

    try:
        logger.info(f"[{handler_name}] 开始获取余额...")

        # 从 WebSocket 数据存储查询余额
        balance_data = await self.page.evaluate(
            """
            () => {
                if (!window.queryData || !window.queryData.balance) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                const balance = window.queryData.balance();

                if (!balance) {
                    return {
                        success: false,
                        reason: 'balance_not_available'
                    };
                }

                return {
                    success: true,
                    data: balance
                };
            }
            """
        )

        # 处理查询结果
        if not balance_data.get('success'):
            reason = balance_data.get('reason')

            if reason == 'query_function_not_available':
                error_msg = 'WebSocket 数据存储未初始化'
                logger.error(f"[{handler_name}] ❌ {error_msg}")
            elif reason == 'balance_not_available':
                error_msg = f'余额数据未就绪（等待 WebSocket 消息，超时: {wait_timeout}s）'
                logger.warning(f"[{handler_name}] ⚠️ {error_msg}")
            else:
                error_msg = f'获取余额失败: {reason}'
                logger.error(f"[{handler_name}] ❌ {error_msg}")

            return {
                'success': False,
                'balance': None,
                'currency': None,
                'open_stake': None,
                'smart_credit': None,
                'last_update': None,
                'message': error_msg,
                'handler_name': handler_name,
                'timestamp': time.time()
            }

        # 提取余额数据（格式可能是: ["USD", 145.9245] 或 145.9245）
        data = balance_data.get('data', {})

        # 提取原始数据
        balance_raw = data.get('balance', [])
        open_stake_raw = data.get('open_stake', [])
        smart_credit_raw = data.get('smart_credit', [])

        # 解析货币和金额（兼容数组和直接数值两种格式）
        if isinstance(balance_raw, list) and len(balance_raw) >= 2:
            currency = balance_raw[0]
            total_balance = balance_raw[1]
        elif isinstance(balance_raw, (int, float)):
            currency = 'USD'
            total_balance = float(balance_raw)
        else:
            currency = 'USD'
            total_balance = 0.0

        if isinstance(open_stake_raw, list) and len(open_stake_raw) >= 2:
            open_stake = open_stake_raw[1]
        elif isinstance(open_stake_raw, (int, float)):
            open_stake = float(open_stake_raw)
        else:
            open_stake = 0.0

        if isinstance(smart_credit_raw, list) and len(smart_credit_raw) >= 2:
            smart_credit = smart_credit_raw[1]
        elif isinstance(smart_credit_raw, (int, float)):
            smart_credit = float(smart_credit_raw)
        else:
            smart_credit = 0.0

        # 计算可用余额 = 总余额 - 未结算金额
        available_balance_raw = total_balance - open_stake
        # 截断到2位小数（不四舍五入）
        available_balance = truncate_to_2_decimals(available_balance_raw)

        last_update = data.get('last_update')

        logger.info(f"[{handler_name}] ✅ 余额获取成功:")
        logger.info(f"  - 总余额: {total_balance} {currency}")
        logger.info(f"  - 未结算: {open_stake} {currency}")
        logger.info(f"  - 可用余额: {available_balance} {currency}")
       
        # 更新到 online_platform
        if update_platform:
            self.online_platform['balance'] = available_balance  # 使用可用余额
            self.online_platform['currency'] = currency
            logger.info(f"[{handler_name}] 📝 已更新 online_platform['balance'] = {available_balance}")

        return {
            'success': True,
            'balance': available_balance,        # 可用余额
            'total_balance': total_balance,      # 总余额（新增）
            'currency': currency,
            'open_stake': open_stake,
            'smart_credit': smart_credit,
            'last_update': last_update,
            'message': '余额获取成功',
            'handler_name': handler_name,
            'timestamp': time.time()
        }

    except Exception as e:
        error_msg = f'获取余额异常: {str(e)}'
        logger.error(f"[{handler_name}] ❌ {error_msg}", exc_info=True)

        return {
            'success': False,
            'balance': None,
            'currency': None,
            'open_stake': None,
            'smart_credit': None,
            'last_update': None,
            'message': error_msg,
            'handler_name': handler_name,
            'timestamp': time.time(),
            'error': str(e)
        }
