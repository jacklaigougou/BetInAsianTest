"""
删除浏览器会话配置
DELETE http://127.0.0.1:40080/sessions/{id}
或 POST http://127.0.0.1:40080/sessions/delete
"""
import logging

logger = logging.getLogger(__name__)


async def delete_browser(self, browser_id: str, **kwargs) -> bool:
    """
    删除浏览器会话配置

    Args:
        browser_id: 浏览器唯一标识ID (uuid)
        **kwargs: 删除参数（预留）

    Returns:
        删除成功返回True,失败返回False

    HTTP请求:
        优先尝试: DELETE http://127.0.0.1:40080/sessions/{id}
        回退方案: POST http://127.0.0.1:40080/sessions/delete
                  Body: {"uuid": "..."}
    """
    try:
        logger.info(f"正在删除浏览器配置: {browser_id}")

        # Linken Sphere 可能使用 DELETE 方法或 POST 方法
        try:
            await self._request("DELETE", f"/sessions/{browser_id}")
        except:
            # 如果 DELETE 不支持，尝试 POST
            payload = {"uuid": browser_id}
            await self._request("POST", "/sessions/delete", json=payload)

        return True
    except Exception as e:
        logger.error(f"删除浏览器配置失败: {browser_id}, 错误: {str(e)}")
        return False
