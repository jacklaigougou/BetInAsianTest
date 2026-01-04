"""
获取单个浏览器的详细信息
GET http://127.0.0.1:40080/sessions

支持自动启动并获取 debug_port
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def get_single_browser_info(
    self,
    browser_id: str,
    auto_launch: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    获取单个浏览器的详细信息

    Args:
        browser_id: 浏览器唯一标识ID (uuid或短id)
        auto_launch: 如果为 True 且浏览器未启动,则自动启动并获取端口
        **kwargs: 额外查询参数（预留）

    Returns:
        浏览器详细信息字典,包含:
        - handler_name: 浏览器名称
        - uuid: 完整UUID
        - id: 短ID (UUID第一段)
        - status: 运行状态
        - debug_port: 调试端口 (如果可用,从缓存或启动获取)
        - 其他运行时信息...
    """
    logger.info(f"正在获取浏览器信息: {browser_id}, auto_launch={auto_launch}")

    # 1. 解析UUID(使用缓存优化,可能不需要调用API)
    full_uuid, short_id, handler_name = await self._resolve_uuid(browser_id)

    # 2. 获取最新的浏览器状态(还是需要获取status)
    response = await self._request("GET", "/sessions")
    raw_sessions = response if isinstance(response, list) else response.get("data", [])

    # 3. 查找目标浏览器的状态信息
    target_session = None
    for session in raw_sessions:
        if session.get('uuid') == full_uuid:
            target_session = session
            break

    if not target_session:
        raise Exception(f"未找到 UUID 为 {full_uuid} 的会话")

    # 4. 转换基本数据
    result = self._transform_browser_data(target_session)
    status = target_session.get('status', '')

    # 5. 使用完整UUID检查缓存
    cached_data = self._get_from_cache(full_uuid)

    # 6. 处理 debug_port 和 ws_url
    # 6.1 如果有缓存且浏览器正在运行,使用缓存的端口
    if cached_data and status in ['running', 'automationRunning']:
        result['debug_port'] = cached_data['debug_port']

        # 获取 WebSocket URL (优先从缓存,缓存没有则调用 API 获取)
        if 'ws_url' in cached_data:
            result['ws_url'] = cached_data['ws_url']
        else:
            # 主动获取 WebSocket URL
            import aiohttp
            try:
                debug_port = cached_data['debug_port']
                url = f"http://127.0.0.1:{debug_port}/json/version"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            ws_url = data.get('webSocketDebuggerUrl')
                            if ws_url:
                                result['ws_url'] = ws_url
                                # 更新缓存
                                cached_data['ws_url'] = ws_url
                                self._port_cache[full_uuid] = cached_data
                                logger.info(f"获取并缓存 WebSocket URL: {ws_url}")
            except Exception as e:
                logger.debug(f"获取 WebSocket URL 失败: {e}")

        logger.info(f"浏览器 {handler_name} ({short_id}) 已启动,端口: {cached_data['debug_port']} (缓存)")
        return result

    # 6.2 如果浏览器已启动但无缓存 (可能是手动启动的)
    if status in ['running', 'automationRunning']:
        if auto_launch:
            logger.info(f"浏览器 {handler_name} ({short_id}) 已启动但无缓存,尝试通过端口扫描获取...")

            # 导入端口扫描方法
            from .scan_debug_port import scan_debug_port

            # 扫描端口查找浏览器
            scan_result = await scan_debug_port(self)

            if scan_result:
                debug_port, ws_url = scan_result
                result['debug_port'] = debug_port
                result['ws_url'] = ws_url

                # 更新缓存
                self._update_cache(
                    uuid=full_uuid,
                    short_id=short_id,
                    handler_name=handler_name,
                    debug_port=debug_port,
                    ws_url=ws_url
                )

                logger.info(
                    f"通过端口扫描找到浏览器 {handler_name} ({short_id})\n"
                    f"   端口: {debug_port}, WebSocket: {ws_url}\n"
                    f"   ⚠️  注意: 如果有多个浏览器运行,此端口可能不准确"
                )
            else:
                logger.error(f"浏览器 {handler_name} ({short_id}) 已启动但无法找到调试端口")
        else:
            logger.warning(f"浏览器 {handler_name} ({short_id}) 已启动但无端口缓存,设置 auto_launch=True 可自动获取")

    # 6.3 如果浏览器未启动且 auto_launch=True
    elif auto_launch and status not in ['running', 'automationRunning']:
        logger.info(f"浏览器 {handler_name} ({short_id}) 未启动,自动启动中...")
        # 直接传递完整UUID,避免launch_browser再次查询
        launch_result = await self.launch_browser(full_uuid)
        result['debug_port'] = launch_result.get('debug_port')
        result['status'] = 'running'

        # 主动获取 WebSocket URL
        import aiohttp
        try:
            debug_port = result['debug_port']
            url = f"http://127.0.0.1:{debug_port}/json/version"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        ws_url = data.get('webSocketDebuggerUrl')
                        if ws_url:
                            result['ws_url'] = ws_url
                            # 更新缓存
                            cached_after_launch = self._get_from_cache(full_uuid)
                            if cached_after_launch:
                                cached_after_launch['ws_url'] = ws_url
                                self._port_cache[full_uuid] = cached_after_launch
                                logger.info(f"获取并缓存 WebSocket URL: {ws_url}")
        except Exception as e:
            logger.debug(f"获取 WebSocket URL 失败: {e}")

    return result
