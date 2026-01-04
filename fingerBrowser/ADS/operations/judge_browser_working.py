"""
判断浏览器是否正常工作
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def judge_browser_working(
    self,
    browser_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    判断浏览器是否正常工作

    Args:
        browser_id: 浏览器唯一标识ID (user_id)
        **kwargs: 额外参数
            - platforms: 平台名称列表 (用于生成 handler_name)

    Returns:
        工作状态信息字典:
        {
            'is_working': bool,      # 是否正在运行
            'status': str,           # 浏览器状态('Active', 'Inactive', 'Unknown')
            'uuid': str,             # 浏览器UUID (user_id)
            'id': str,               # serial_number
            'handler_name': str,     # 浏览器名称
            'browser_id': str,       # 浏览器ID (同uuid)
            'debug_port': str,       # 调试端口(如果运行中)
            'ws_url': str,           # WebSocket URL(如果运行中)
        }
    """
    try:
        # 调用 ADS API 获取浏览器活动信息（与 get_single_browser_info 使用相同的接口）
        endpoint = f"/api/v1/browser/active?user_id={browser_id}"
        response = await self._request("GET", endpoint)

        # 解析响应
        if not isinstance(response, dict) or 'data' not in response:
            logger.warning(f"ADS API 返回格式异常: {response}")
            return {
                'is_working': False,
                'status': 'Unknown',
                'uuid': browser_id,
                'id': '',
                'handler_name': '',
                'browser_id': browser_id,
                'debug_port': '',
                'ws_url': '',
                'error': 'API 返回格式错误'
            }

        data = response.get('data', {})

        # 提取核心字段
        debug_port = data.get('debug_port', '')
        ws_data = data.get('ws', {})
        ws_url = ws_data.get('puppeteer', '')  # 使用 puppeteer 的 WebSocket URL
        status = data.get('status', 'Unknown')

        # 获取 serial_number 和 handler_name（与 get_single_browser_info 相同的逻辑）
        cached = self._get_from_cache(browser_id)

        if cached:
            # 从缓存获取
            serial_number = cached.get('id', '')
            handler_name = cached.get('name', '')
        else:
            # 缓存未命中,需要查询列表获取 serial_number
            logger.debug(f"缓存未命中,查询浏览器列表获取 serial_number...")
            platforms = kwargs.get('platforms', [])
            all_browsers = await self.get_all_browsers_info(platforms=platforms)

            # 查找匹配的浏览器
            browser_info = next((b for b in all_browsers if b['uuid'] == browser_id), None)

            if browser_info:
                serial_number = browser_info['id']
                handler_name = browser_info['handler_name']
                # 更新缓存
                self._update_cache(
                    uuid=browser_id,
                    short_id=serial_number,
                    name=handler_name,
                    debug_port=int(debug_port) if debug_port else 0,
                    ws_url=ws_url
                )
            else:
                logger.warning(f"未找到浏览器 {browser_id} 的信息,使用默认值")
                serial_number = browser_id
                handler_name = f"{browser_id}_unknown"

        # 判断浏览器是否正在工作：debug_port 或 ws_url 不为空则表示已启动
        is_working = bool(debug_port) or bool(ws_url)

        if is_working:
            logger.info(f"浏览器 {handler_name} ({serial_number}) 正在运行, debug_port={debug_port}")
            return {
                'is_working': True,
                'status': status if status != 'Unknown' else 'Active',
                'uuid': browser_id,
                'id': serial_number,
                'handler_name': handler_name,
                'browser_id': browser_id,
                'debug_port': debug_port,
                'ws_url': ws_url,
            }
        else:
            logger.info(f"浏览器 {handler_name} ({serial_number}) 未运行")
            return {
                'is_working': False,
                'status': 'Inactive',
                'uuid': browser_id,
                'id': serial_number,
                'handler_name': handler_name,
                'browser_id': browser_id,
                'debug_port': '',
                'ws_url': '',
                'message': '浏览器未运行'
            }

    except Exception as e:
        logger.error(f"判断浏览器 {browser_id} 工作状态异常: {e}")
        return {
            'is_working': False,
            'status': 'Error',
            'uuid': browser_id,
            'id': '',
            'handler_name': '',
            'browser_id': browser_id,
            'debug_port': '',
            'ws_url': '',
            'error': str(e)
        }
