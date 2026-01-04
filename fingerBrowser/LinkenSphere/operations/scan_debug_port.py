"""
扫描并查找浏览器的调试端口

用于处理手动启动的浏览器(无缓存 debug_port 的情况)
"""
import aiohttp
import asyncio
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


async def scan_debug_port(
    self,
    start_port: int = 9222,
    end_port: int = 9270,
    timeout: float = 0.3
) -> Optional[Tuple[int, str]]:
    """
    扫描端口范围,查找活动的 Chrome 调试端口

    Args:
        start_port: 起始端口 (默认 9222)
        end_port: 结束端口 (默认 9270)
        timeout: 每个端口的超时时间(秒,默认 0.3)

    Returns:
        如果找到活动端口,返回 (port, ws_url)
        否则返回 None

    注意:
        - 此方法扫描所有可能的端口,可能返回其他浏览器的端口
        - 主要用于找到手动启动的浏览器
    """
    logger.info(f"开始扫描调试端口 ({start_port}-{end_port})...")

    found_ports = []

    async with aiohttp.ClientSession() as session:
        # 创建扫描任务
        async def check_port(port: int):
            try:
                url = f"http://127.0.0.1:{port}/json/version"
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        ws_url = data.get('webSocketDebuggerUrl')
                        return (port, ws_url)
            except:
                pass
            return None

        # 并发扫描所有端口
        tasks = [check_port(port) for port in range(start_port, end_port + 1)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集成功的结果
        for result in results:
            if result and not isinstance(result, Exception):
                found_ports.append(result)

    if found_ports:
        logger.info(f"找到 {len(found_ports)} 个活动调试端口")
        # 返回第一个找到的端口(通常是最早启动的浏览器)
        port, ws_url = found_ports[0]
        logger.info(f"使用端口: {port}, WebSocket URL: {ws_url}")
        return (port, ws_url)
    else:
        logger.warning(f"未找到任何活动的调试端口 ({start_port}-{end_port})")
        return None


async def find_browser_port_by_scan(
    self,
    uuid: str,
    handler_name: str
) -> Optional[Tuple[int, str]]:
    """
    为特定浏览器查找调试端口(通过扫描)

    Args:
        uuid: 浏览器的完整UUID
        handler_name: 浏览器名称

    Returns:
        如果找到,返回 (debug_port, ws_url)
        否则返回 None

    注意:
        这是一个兜底方案,用于处理手动启动的浏览器
        由于无法精确匹配 UUID,返回的可能是其他浏览器的端口
    """
    logger.info(f"通过端口扫描查找浏览器: {handler_name} ({uuid[:8]}...)")

    result = await self.scan_debug_port()

    if result:
        port, ws_url = result
        logger.warning(
            f"浏览器 {handler_name} 可能使用端口 {port}\n"
            f"   注意: 由于 Linken Sphere UUID 与 CDP UUID 不同,无法精确匹配\n"
            f"   如果环境中有多个浏览器,此端口可能不是目标浏览器"
        )
        return result

    return None
