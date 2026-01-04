"""
强制关闭指定的浏览器会话
POST http://127.0.0.1:40080/sessions/force_stop

与普通 close 的区别:
- close: 正常关闭,如果浏览器被占用会失败
- force_stop: 强制关闭,即使被其他客户端占用也会强制停止
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def force_close_browser(self, browser_id: str, **kwargs) -> bool:
    """
    强制关闭指定的浏览器会话

    Args:
        browser_id: 浏览器唯一标识ID (uuid或短id)
        **kwargs: 额外参数

    Returns:
        成功返回 True, 失败返回 False

    HTTP请求:
        POST http://127.0.0.1:40080/sessions/force_stop
        Body: {"uuid": "..."}
    """
    # 1. 解析UUID
    full_uuid, short_id, handler_name = await self._resolve_uuid(browser_id)

    logger.info(f"正在强制关闭浏览器: {handler_name} ({short_id})")

    try:
        # 2. 调用强制关闭API
        stop_payload = {"uuid": full_uuid}
        await self._request("POST", "/sessions/force_stop", json=stop_payload)

        # 3. 清理缓存
        self._clear_cache(full_uuid)

        logger.info(f"浏览器强制关闭成功: {handler_name} ({short_id})")
        return True

    except Exception as e:
        logger.error(f"强制关闭浏览器失败: {handler_name} ({short_id}), 错误: {e}")
        return False
