# -*- coding: utf-8 -*-
"""
Pin888 获取余额
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def GetBalance(self, **kwargs) -> Dict[str, Any]:
    """
    获取账户余额 (双重策略: HTTP请求 + 元素定位)

    策略:
    1. 优先使用 HTTP 请求获取余额 (快速、准确)
    2. 失败则降级为元素定位 (兜底方案)

    Args:
        **kwargs: 额外参数

    Returns:
        {
            'success': bool,        # 是否成功
            'balance': str,         # 余额字符串 (如 "19.31")
            'currency': str,        # 货币单位 (如 "USD")
            'method': str,          # 获取方式 ('request' 或 'element')
            'message': str          # 结果消息
        }

    Examples:
        >>> result = await GetBalance(self)
        >>> result['success']
        True
        >>> result['balance']
        '19.31'
        >>> result['method']
        'request'
    """
    # ✅ 直接使用 self.handler_name (已在父类 AutomationBase 中从 config 提取)
    handler_name = self.handler_name

    # ========== 方法1: 通过 HTTP 请求获取余额 (优先) ==========
    try:
        if not self.pom:
            logger.warning(f"[{handler_name}] POM 对象未初始化")
        else:
            balance = await self.pom.find_balance_by_request()
            if balance:
                logger.info(f"[{handler_name}] 💰 通过请求获取余额: {balance}")
                return {
                    'success': True,
                    'balance': balance,
                    'currency': 'USD',  # Pin888 默认货币
                    'method': 'request',
                    'message': '通过请求获取余额成功'
                }
    except Exception as e:
        logger.warning(f"[{handler_name}] ⚠️ 请求方式获取余额失败,尝试元素定位: {e}")

    # ========== 方法2: 通过元素定位获取余额 (兜底) ==========
    try:
        if not self.pom:
            return {
                'success': False,
                'balance': None,
                'currency': None,
                'method': None,
                'message': 'POM 对象未初始化'
            }

        # 1. 获取余额元素定位器
        balance_locator = await self.pom.find_balance_element()

        if not balance_locator:
            return {
                'success': False,
                'balance': None,
                'currency': None,
                'method': 'element',
                'message': '余额元素未找到'
            }

        # 2. 等待元素出现
        await balance_locator.wait_for(timeout=10000)

        # 3. 获取文本内容
        balance_text = await balance_locator.text_content()

        if balance_text:
            balance = balance_text.strip()
            logger.info(f"[{handler_name}] 💰 通过元素定位获取余额: {balance}")
            return {
                'success': True,
                'balance': balance,
                'currency': 'USD',
                'method': 'element',
                'message': '通过元素定位获取余额成功'
            }
        else:
            logger.warning(f"[{handler_name}] ⚠️ 余额文本为空")
            return {
                'success': False,
                'balance': None,
                'currency': None,
                'method': 'element',
                'message': '余额文本为空'
            }

    except Exception as e:
        logger.error(f"[{handler_name}] ❌ 获取余额失败: {e}", exc_info=True)
        return {
            'success': False,
            'balance': None,
            'currency': None,
            'method': None,
            'message': f'获取余额失败: {str(e)}'
        }


async def GetBalanceByRequest(self, **kwargs) -> str:
    """
    通过 HTTP 请求获取余额 (仅返回余额字符串)

    这是一个简化版本的 GetBalance，专门用于下注后快速更新余额。
    与 GetBalance 的区别：
    - GetBalance: 返回完整的字典，包含 success、balance、currency 等
    - GetBalanceByRequest: 仅返回余额字符串，失败返回 None

    Args:
        **kwargs: 额外参数

    Returns:
        余额字符串 (如 "19.31")，失败返回 None

    Examples:
        >>> balance = await GetBalanceByRequest(self)
        >>> balance
        '19.31'
    """
    handler_name = self.handler_name

    try:
        if not self.pom:
            logger.warning(f"[{handler_name}] POM 对象未初始化")
            return None

        balance = await self.pom.find_balance_by_request()

        if balance:
            logger.info(f"[{handler_name}] 💰 通过请求获取余额: {balance}")
            return balance
        else:
            logger.warning(f"[{handler_name}] ❌ 通过请求获取余额失败")
            return None

    except Exception as e:
        logger.error(f"[{handler_name}] ❌ GetBalanceByRequest 失败: {e}", exc_info=True)
        return None
