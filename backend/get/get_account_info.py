# -*- coding: utf-8 -*-
"""
获取账号信息
GET {BASE_URL}/account/{ads_id}_pin888

返回账号的用户名和密码
"""
from typing import Dict, Any, Optional
import logging
import aiohttp

logger = logging.getLogger(__name__)


async def get_account_info(
    ads_id: str,
    platform: str = 'pin888',
    base_url: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    获取账号信息 (用户名和密码)

    Args:
        ads_id: 浏览器ID (ADS ID)
        platform: 平台名称 (默认: 'pin888')
        base_url: API 基础URL (默认从 Settings 获取)
        **kwargs: 额外参数

    Returns:
        {
            'success': bool,
            'username': str,
            'password': str,
            'message': str
        }

    Examples:
        >>> result = await get_account_info(ads_id='xxx123')
        >>> result['success']
        True
        >>> result['username']
        'user123'
        >>> result['password']
        'pass456'
    """
    try:
        # 1. 获取 BASE_URL
        if not base_url:
            from configs.settings import Settings
            base_url = Settings.BASE_URL

        # 2. 构造 API URL
        uri = f"/account/{ads_id}_{platform}"
        url = f"{base_url}{uri}"

        logger.info(f"[Backend] 请求账号信息: {url}")

        # 3. 发送 HTTP GET 请求
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                # 4. 检查状态码
                if response.status != 200:
                    logger.error(f"[Backend] API 请求失败,状态码: {response.status}")
                    return {
                        'success': False,
                        'username': None,
                        'password': None,
                        'message': f'API 请求失败,状态码: {response.status}'
                    }

                # 5. 解析响应
                data = await response.json()

                username = data.get('username')
                password = data.get('password')

                # 6. 验证响应数据
                if not username or not password:
                    logger.error(f"[Backend] API 响应中缺少账号信息")
                    logger.error(f"[Backend] 响应数据: {data}")
                    return {
                        'success': False,
                        'username': None,
                        'password': None,
                        'message': 'API 响应中缺少账号信息'
                    }

                logger.info(f"[Backend] ✅ 成功获取账号信息: username={username}")

                return {
                    'success': True,
                    'username': username,
                    'password': password,
                    'message': '成功获取账号信息'
                }

    except aiohttp.ClientError as e:
        logger.error(f"[Backend] HTTP 请求异常: {e}")
        return {
            'success': False,
            'username': None,
            'password': None,
            'message': f'HTTP 请求异常: {str(e)}'
        }
    except Exception as e:
        logger.error(f"[Backend] 获取账号信息失败: {e}", exc_info=True)
        return {
            'success': False,
            'username': None,
            'password': None,
            'message': f'获取账号信息失败: {str(e)}'
        }
