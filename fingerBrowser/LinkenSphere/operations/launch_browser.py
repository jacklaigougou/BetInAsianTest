"""
启动指定的浏览器会话
POST http://127.0.0.1:40080/sessions/start

启动成功后自动缓存端口信息
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def launch_browser(self, browser_id: str, **kwargs) -> Dict[str, Any]:
    """
    启动指定的浏览器会话

    Args:
        browser_id: 浏览器唯一标识ID (uuid或短id)
        **kwargs: 启动参数
            - headless: 是否无头模式（默认 False）
            - 其他启动参数...

    Returns:
        启动结果信息,包含调试端口等连接信息
        {
            "uuid": "...",
            "debug_port": 9222
        }

    HTTP请求:
        POST http://127.0.0.1:40080/sessions/start
        Body: {"uuid": "...", "headless": false}
    """
    logger.info(f"正在启动浏览器: {browser_id}")

    # 1. 解析UUID(使用缓存优化)
    full_uuid, short_id, handler_name = await self._resolve_uuid(browser_id)

    # 2. 检查浏览器是否已在运行(幂等性检查)
    sessions_response = await self._request("GET", "/sessions")
    sessions = sessions_response if isinstance(sessions_response, list) else sessions_response.get("data", [])

    for session in sessions:
        if session.get("uuid") == full_uuid:
            status = session.get("status")
            if status in ["running", "automationRunning"]:
                logger.warning(
                    f"浏览器 {handler_name} ({short_id}) 已在运行 (状态: {status}),强制关闭后重启"
                )

                # 导入 force_close_browser 方法
                from .force_close_browser import force_close_browser

                # 强制关闭浏览器
                force_closed = await force_close_browser(self, full_uuid)
                if not force_closed:
                    logger.error(f"强制关闭浏览器失败: {handler_name} ({short_id})")
                    return {
                        "uuid": full_uuid,
                        "debug_port": None,
                        "error": "强制关闭浏览器失败"
                    }

                # 等待浏览器完全关闭
                import asyncio
                logger.info("等待浏览器完全关闭...")
                await asyncio.sleep(3)

                # 继续后续的启动流程(不 return,继续执行到第3步)
                logger.info(f"浏览器已关闭,准备重新启动...")
            break

    # 3. 启动浏览器
    start_payload = {
        "uuid": full_uuid,
        "headless": kwargs.get("headless", False)
    }

    # 合并其他参数
    for key, value in kwargs.items():
        if key not in start_payload:
            start_payload[key] = value

    start_response = await self._request("POST", "/sessions/start", json=start_payload)

    # 4. 提取 debug_port 并更新缓存
    debug_port = start_response.get('debug_port')

    if debug_port and full_uuid:
        self._update_cache(
            uuid=full_uuid,
            short_id=short_id,
            handler_name=handler_name,
            debug_port=debug_port
        )
        logger.info(f"浏览器启动成功: {handler_name} ({short_id}), 端口: {debug_port}")

    return {
        "uuid": full_uuid,
        "debug_port": debug_port,
        "success": True
    }
