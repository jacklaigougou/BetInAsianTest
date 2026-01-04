"""
获取单个浏览器详细信息
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def get_single_browser_info(
    self,
    browser_id: str,
    auto_launch: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    获取单个浏览器的详细信息

    Args:
        browser_id: 浏览器唯一标识ID (user_id)
        auto_launch: 如果浏览器未启动,是否自动启动 (默认 True)
        **kwargs: 额外的查询参数
            - platforms: 平台名称列表 (用于生成 handler_name)

    Returns:
        浏览器详细信息字典,包含:
        - uuid: user_id
        - id: serial_number (需要从 get_all_browsers_info 获取)
        - handler_name: serial_number_平台名
        - debug_port: 调试端口
        - ws_url: WebSocket 连接地址 (puppeteer)
        - status: 浏览器状态
        - 其他原始字段...
    """
    try:
        # 1. 如果需要自动启动浏览器
        if auto_launch:
            logger.info(f"auto_launch=True, 正在启动浏览器 {browser_id}...")
            launch_result = await self.launch_browser(browser_id)
            logger.debug(f"启动结果: {launch_result}")

        # 2. 调用 ADS API 获取浏览器活动信息
        endpoint = f"/api/v1/browser/active?user_id={browser_id}"
        response = await self._request("GET", endpoint)

        # 3. 解析响应
        if not isinstance(response, dict) or 'data' not in response:
            logger.error(f"ADS API 返回格式错误: {response}")
            raise Exception("ADS API 返回格式错误")

        data = response.get('data', {})

        # 4. 提取核心字段
        debug_port = data.get('debug_port', '')
        ws_data = data.get('ws', {})
        ws_url = ws_data.get('puppeteer', '')  # 使用 puppeteer 的 WebSocket URL
        status = data.get('status', 'Unknown')

        # 5. 获取 serial_number 和 handler_name
        # 需要从 get_all_browsers_info 中查找对应的浏览器
        # 先尝试从缓存中获取
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

        # 6. 构建符合验证器要求的数据结构
        result = {
            'uuid': browser_id,
            'id': serial_number,
            'handler_name': handler_name,
            'debug_port': debug_port,
            'ws_url': ws_url,
            # 额外字段
            'status': status,
            'ws': ws_data,
            'webdriver': data.get('webdriver', ''),
        }

        logger.info(f"获取浏览器信息成功: {handler_name} (debug_port={debug_port})")
        return result

    except Exception as e:
        logger.error(f"获取浏览器 {browser_id} 信息失败: {e}")
        raise
