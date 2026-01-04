"""
获取所有浏览器配置信息
"""
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


async def get_all_browsers_info(
    self,
    auto_close_running: bool = False,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    获取所有浏览器配置信息

    Args:
        auto_close_running: 是否在获取前关闭所有运行中的浏览器
        **kwargs: 额外的查询参数
            - platforms: 平台名称列表,用于生成 handler_name (如 ['pin888', 'sportsbet'])
            - page: 页码 (默认 1)
            - page_size: 每页数量 (默认 100)

    Returns:
        包含所有浏览器配置的列表,每个元素包含:
        - handler_name: serial_number_平台名
        - uuid: user_id
        - id: serial_number
        - status: None (ADS API 不返回状态)
        - 其他原始字段...
    """
    # 1. 如果需要先关闭所有浏览器
    if auto_close_running:
        logger.info("auto_close_running=True, 正在关闭所有运行中的浏览器...")
        await self.close_all_browser()

    # 2. 提取参数
    platforms = kwargs.get('platforms', [])
    page = kwargs.get('page', 1)
    page_size = kwargs.get('page_size', 100)

    # 3. 调用 ADS API
    endpoint = f"/api/v1/user/list?page={page}&page_size={page_size}"

    try:
        response = await self._request("GET", endpoint)

        # 4. 解析响应
        if not isinstance(response, dict) or 'data' not in response:
            logger.error(f"ADS API 返回格式错误: {response}")
            raise Exception("ADS API 返回格式错误")

        data = response.get('data', {})
        browser_list = data.get('list', [])

        if not isinstance(browser_list, list):
            logger.error(f"ADS API 返回的 list 不是列表类型: {type(browser_list)}")
            raise Exception("ADS API 返回数据格式错误")

        # 5. 转换数据格式
        result = []
        for item in browser_list:
            serial_number = item.get('serial_number', '')
            user_id = item.get('user_id', '')
            name = item.get('name', '')

            # 生成 handler_name: serial_number_平台名
            # 如果提供了 platforms,循环使用;否则使用原始 name 或空字符串
            if platforms:
                platform_index = int(serial_number) % len(platforms) if serial_number.isdigit() else 0
                platform_name = platforms[platform_index]
            else:
                platform_name = name or 'unknown'

            handler_name = f"{serial_number}_{platform_name}"

            # 构建符合验证器要求的数据结构
            transformed = {
                'handler_name': handler_name,
                'uuid': user_id,
                'id': serial_number,
                'status': None,  # ADS API 不返回运行状态
                # 保留原始数据
                'name': name,
                'domain_name': item.get('domain_name', ''),
                'created_time': item.get('created_time', ''),
                'ip': item.get('ip', ''),
                'ip_country': item.get('ip_country', ''),
                'user_proxy_config': item.get('user_proxy_config', {}),
                'group_id': item.get('group_id', '0'),
                'group_name': item.get('group_name', ''),
                'remark': item.get('remark', ''),
                'last_open_time': item.get('last_open_time', '0'),
            }

            result.append(transformed)

        logger.info(f"获取到 {len(result)} 个浏览器配置")
        return result

    except Exception as e:
        logger.error(f"获取浏览器列表失败: {e}")
        raise
