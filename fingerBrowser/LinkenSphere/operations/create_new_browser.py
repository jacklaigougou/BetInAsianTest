"""
创建新的浏览器会话
POST http://127.0.0.1:40080/sessions/create_quick
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def create_new_browser(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建新的浏览器会话

    Args:
        config: 浏览器配置参数字典
            - name: 会话名称（可选）
            - quick: 是否使用快速创建（默认 True）
            - 其他配置参数...

    Returns:
        创建成功后返回的浏览器信息

    HTTP请求:
        POST http://127.0.0.1:40080/sessions/create_quick (快速创建)
        POST http://127.0.0.1:40080/sessions/create (标准创建)
    """
    logger.info(f"正在创建新浏览器会话: {config.get('name', 'Quick Session')}")

    # 使用快速创建端点
    if not config or config.get('quick', True):
        response = await self._request("POST", "/sessions/create_quick")
    else:
        # 如果有详细配置，使用标准创建端点
        response = await self._request("POST", "/sessions/create", json=config)

    # API 返回的是列表,提取第一个元素
    if isinstance(response, list) and len(response) > 0:
        raw_data = response[0]
    elif isinstance(response, dict):
        raw_data = response
    else:
        raise Exception(f"创建浏览器返回的数据格式异常: {response}")

    # 转换数据格式
    return self._transform_browser_data(raw_data)
