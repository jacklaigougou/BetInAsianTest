"""
关闭正在运行的浏览器会话
POST http://127.0.0.1:40080/sessions/stop

关闭成功后自动清理缓存
"""
import logging

logger = logging.getLogger(__name__)


async def close_browser(self, browser_id: str, **kwargs) -> bool:
    """
    关闭正在运行的浏览器会话

    Args:
        browser_id: 浏览器唯一标识ID (uuid或短id)
        **kwargs: 关闭参数（预留）

    Returns:
        关闭成功返回True,失败返回False

    HTTP请求:
        POST http://127.0.0.1:40080/sessions/stop
        Body: {"uuid": "..."}
    """
    try:
        logger.info(f"正在关闭浏览器: {browser_id}")

        # 1. 解析UUID(使用缓存优化)
        full_uuid, short_id, handler_name = await self._resolve_uuid(browser_id)

        # 2. 关闭浏览器
        stop_payload = {"uuid": full_uuid}
        stop_payload.update(kwargs)

        await self._request("POST", "/sessions/stop", json=stop_payload)

        # 3. 清理缓存
        if self._remove_from_cache(full_uuid):
            logger.info(f"已清理浏览器 {browser_id} 的端口缓存")

        logger.info(f"浏览器已关闭: {browser_id}")
        return True

    except Exception as e:
        logger.error(f"关闭浏览器失败: {browser_id}, 错误: {str(e)}")
        return False
