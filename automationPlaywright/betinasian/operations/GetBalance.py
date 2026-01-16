# -*- coding: utf-8 -*-
"""
BetInAsian 获取余额

从 WebSocket 数据存储中获取实时余额信息
"""
from typing import Dict, Any
import logging
import time

logger = logging.getLogger(__name__)


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

        # 提取余额数据
        data = balance_data.get('data', {})
        balance = data.get('balance')
        currency = data.get('currency', 'USD')
        open_stake = data.get('open_stake', 0.0)
        smart_credit = data.get('smart_credit', 0.0)
        last_update = data.get('last_update')

        logger.info(f"[{handler_name}] ✅ 余额获取成功:")
        logger.info(f"  - 余额: {balance} {currency}")
       
        # 更新到 online_platform
        if update_platform:
            self.online_platform['balance'] = balance
            self.online_platform['currency'] = currency
            logger.info(f"[{handler_name}] 📝 已更新 online_platform['balance'] = {balance}")

        return {
            'success': True,
            'balance': balance,
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
