"""
创建新的浏览器配置
"""
from typing import Dict, Any
import logging
import random

logger = logging.getLogger(__name__)


async def create_new_browser(
    self,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    创建新的浏览器配置

    Args:
        config: 浏览器配置参数字典
            - name: 浏览器名称 (必需)
            - proxy: 代理配置 (可选)
                {
                    "proxy_type": "socks5/http",
                    "proxy_host": "IP",
                    "proxy_port": "端口",
                    "proxy_user": "用户名",
                    "proxy_password": "密码"
                }
            - version_choices: 浏览器版本列表 (可选,默认 ['131', '132', '133'])
            - group_id: 分组ID (可选,默认 "0")
            - platforms: 平台名称列表 (可选,用于生成 handler_name)

    Returns:
        创建成功后返回的浏览器信息:
        {
            'handler_name': 浏览器名称,
            'uuid': user_id,
            'id': serial_number,
            'status': 状态
        }
    """
    try:
        # 1. 验证必需参数
        if 'name' not in config:
            logger.error("缺少必需参数: name")
            raise ValueError("缺少必需参数: name")

        # 2. 构建 user_proxy_config
        # 如果没有提供代理,使用 no_proxy
        if 'proxy' not in config or not config['proxy']:
            user_proxy_config = {
                "proxy_soft": "no_proxy"
            }
            logger.debug("未提供代理配置,使用 no_proxy")
        else:
            proxy = config['proxy']
            user_proxy_config = {
                "proxy_soft": "other",
                "proxy_type": proxy.get('proxy_type', 'socks5'),
                "proxy_host": proxy.get('proxy_host'),
                "proxy_port": proxy.get('proxy_port'),
                "proxy_user": proxy.get('proxy_user', ''),
                "proxy_password": proxy.get('proxy_password', '')
            }
            logger.debug(f"代理配置: {user_proxy_config}")

        # 3. 构建 fingerprint_config
        version_choices = config.get('version_choices', ['131', '132', '133'])
        selected_version = random.choice(version_choices)

        fingerprint_config = {
            "automatic_timezone": "1",  # 自动时区
            "webrtc": "forward",
            "language": ["en-US", "en"],
            "language_switch": "0",
            "page_language_switch": "0",
            "page_language": "en-US",
            "flash": "block",
            "hardware_concurrency": random.choice(['6', '8', '10']),
            "device_memory": random.choice(['16', '32']),
            "scan_port_type": "1",
            "browser_kernel_config": {
                "version": selected_version,
                "type": "chrome"
            },
            "random_ua": {
                "ua_browser": ["chrome"],
                "ua_version": [selected_version],
                "ua_system_version": random.choice([
                    ["Windows 10"],
                    ["Windows 11"]
                ])
            }
        }

        # 4. 构建请求数据
        request_data = {
            "group_id": config.get('group_id', '0'),
            "name": config['name'],
            "fingerprint_config": fingerprint_config,
            "user_proxy_config": user_proxy_config  # 必需字段
        }

        # 5. 发送请求
        endpoint = "/api/v1/user/create"
        response = await self._request("POST", endpoint, json=request_data)

        # 6. 解析响应
        if not isinstance(response, dict):
            logger.error(f"ADS API 返回格式错误: {response}")
            # 返回失败结果而不是抛异常
            return {
                'handler_name': config['name'],
                'uuid': '',
                'id': '',
                'status': None,
                'success': False,
                'error': 'API 返回格式错误'
            }

        code = response.get('code')
        msg = response.get('msg', '')
        data = response.get('data', {})

        # 7. 根据 code 判断是否成功
        success = (code == 0)

        if not success:
            # 创建失败,返回失败结果
            logger.error(f"创建浏览器失败: code={code}, msg={msg}")
            return {
                'handler_name': config['name'],
                'uuid': '',
                'id': '',
                'status': None,
                'success': False,
                'error': msg or f'创建失败 (code={code})'
            }

        # 8. 提取返回的 user_id
        user_id = data.get('id') or data.get('user_id')
        if not user_id:
            logger.error(f"API 返回数据中未找到 user_id: {data}")
            return {
                'handler_name': config['name'],
                'uuid': '',
                'id': '',
                'status': None,
                'success': False,
                'error': 'API 返回数据中未找到 user_id'
            }

        logger.info(f"浏览器创建成功: user_id={user_id}")

        # 9. 查询浏览器列表获取 serial_number 和 handler_name
        # 因为创建后需要从列表中查询才能得到 serial_number
        platforms = config.get('platforms', [])
        all_browsers = await self.get_all_browsers_info(platforms=platforms)

        # 查找刚创建的浏览器
        browser_info = next((b for b in all_browsers if b['uuid'] == user_id), None)

        if browser_info:
            # 从列表中获取完整信息
            result = {
                'handler_name': browser_info['handler_name'],
                'uuid': browser_info['uuid'],
                'id': browser_info['id'],
                'status': browser_info.get('status'),
                'success': True
            }
        else:
            # 列表中未找到,使用基础信息
            logger.warning(f"未在列表中找到新创建的浏览器 {user_id},使用基础信息")
            result = {
                'handler_name': config['name'],
                'uuid': user_id,
                'id': user_id,  # 暂时使用 user_id 作为 id
                'status': None,
                'success': True
            }

        logger.info(f"创建结果: {result}")
        return result

    except Exception as e:
        logger.error(f"创建浏览器异常: {e}")
        # 即使发生异常也返回失败结果
        return {
            'handler_name': config.get('name', ''),
            'uuid': '',
            'id': '',
            'status': None,
            'success': False,
            'error': str(e)
        }
