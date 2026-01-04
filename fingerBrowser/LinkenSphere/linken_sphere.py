"""
Linken Sphere 指纹浏览器API实现
基于本地客户端 API (http://127.0.0.1:40080)
"""
import aiohttp
from typing import Dict, List, Optional, Any
import logging
import atexit
import asyncio
from ..interface import FingerBrowserBase

# 导入操作方法
from .operations import (
    get_all_browsers_info,
    get_single_browser_info,
    create_new_browser,
    launch_browser,
    close_browser,
    delete_browser,
    close_all_browser,
    force_close_browser,
)


logger = logging.getLogger(__name__)


class LinkenSphere(FingerBrowserBase):
    """Linken Sphere 指纹浏览器实现类 - 本地客户端 API"""

    # 类级别变量,跟踪所有实例
    _instances = []

    # 端口缓存: {完整UUID: {id, uuid, handler_name, debug_port}}
    _port_cache: Dict[str, Dict[str, Any]] = {}

    # UUID映射缓存: {短ID: 完整UUID}
    _uuid_mapping: Dict[str, str] = {}

    def __init__(self, base_url: Optional[str] = None, **kwargs):
        """
        初始化 Linken Sphere 客户端

        Args:
            base_url: API基础URL，默认为本地客户端地址 http://127.0.0.1:40080
            **kwargs: 其他配置参数（兼容参数）
        """
        # Linken Sphere 本地 API 不需要 api_key
        super().__init__(api_key="", base_url=base_url)
        self.base_url = base_url or "http://127.0.0.1:40080"
        self._session: Optional[aiohttp.ClientSession] = None
        self.timeout = kwargs.get('timeout', 30)  # 默认30秒超时

        # 将实例添加到跟踪列表
        LinkenSphere._instances.append(self)

        # 首次注册时设置清理钩子
        if len(LinkenSphere._instances) == 1:
            atexit.register(LinkenSphere._cleanup_all_sessions)

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        获取或创建HTTP会话

        Returns:
            aiohttp会话对象
        """
        if self._session is None or self._session.closed:
            # 本地 API 不需要 Authorization 头
            self._session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        发送HTTP请求

        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE等)
            endpoint: API端点路径
            **kwargs: 其他请求参数

        Returns:
            响应数据（可能是字典、列表或其他类型）

        Raises:
            Exception: 请求失败时抛出异常
        """
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with session.request(method, url, **kwargs) as response:
                # 检查响应状态
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API请求失败: {method} {url}, 状态码: {response.status}, 响应: {error_text}")
                    raise Exception(f"API请求失败 ({response.status}): {error_text}")

                # 尝试解析 JSON
                try:
                    data = await response.json()
                    return data
                except:
                    # 如果JSON解析失败,返回原始文本
                    text = await response.text()
                    # 尝试手动解析(可能是编码问题)
                    try:
                        import json
                        data = json.loads(text)
                        return data
                    except:
                        logger.warning(f"无法解析JSON响应，返回文本: {text}")
                        return {"raw_response": text}

        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {method} {url}, 错误: {str(e)}")
            raise Exception(f"网络请求失败: {str(e)}")

    def _transform_browser_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换浏览器数据格式

        转换规则:
        - name → handler_name
        - id 只取 uuid 的第一段 (按 - 分割)

        Args:
            data: 原始浏览器数据

        Returns:
            转换后的数据
        """
        result = data.copy()

        # name → handler_name
        if 'name' in result:
            result['handler_name'] = result.pop('name')

        # id 只取 uuid 第一段
        if 'uuid' in result:
            uuid_full = result['uuid']
            result['id'] = uuid_full.split('-')[0]

        return result

    def _get_from_cache(self, uuid: str) -> Optional[Dict[str, Any]]:
        """
        从缓存中获取浏览器信息(仅支持完整UUID)

        Args:
            uuid: 完整的浏览器UUID

        Returns:
            缓存的浏览器信息,包含 id, uuid, handler_name, debug_port
        """
        return self._port_cache.get(uuid)

    def _update_cache(
        self,
        uuid: str,
        short_id: str,
        handler_name: str,
        debug_port: int,
        ws_url: Optional[str] = None
    ):
        """
        更新端口缓存

        Args:
            uuid: 完整UUID
            short_id: 短ID (UUID第一段)
            handler_name: 浏览器名称
            debug_port: CDP调试端口
            ws_url: WebSocket调试URL (可选)
        """
        cache_data = {
            'id': short_id,
            'uuid': uuid,
            'handler_name': handler_name,
            'debug_port': debug_port
        }

        # 如果提供了 ws_url,添加到缓存
        if ws_url:
            cache_data['ws_url'] = ws_url

        self._port_cache[uuid] = cache_data
        logger.debug(f"缓存更新: {handler_name} ({short_id}) -> port {debug_port}")

    def _remove_from_cache(self, uuid: str) -> bool:
        """
        从缓存中移除(仅支持完整UUID)

        Args:
            uuid: 完整UUID

        Returns:
            是否成功移除
        """
        if uuid in self._port_cache:
            del self._port_cache[uuid]
            logger.debug(f"缓存已清理: {uuid}")
            return True
        return False

    async def _resolve_uuid(self, browser_id: str) -> tuple[str, str, str]:
        """
        解析browser_id为完整UUID(带缓存优化)

        Args:
            browser_id: 短ID或完整UUID

        Returns:
            (完整UUID, 短ID, handler_name)
        """
        # 1. 如果是完整UUID格式
        if '-' in browser_id and len(browser_id) == 36:
            short_id = browser_id.split('-')[0]
            # 更新映射缓存
            self._uuid_mapping[short_id] = browser_id
            # 尝试从端口缓存获取handler_name
            cached = self._get_from_cache(browser_id)
            if cached:
                return browser_id, short_id, cached['handler_name']
            # 需要查询API获取handler_name
            response = await self._request("GET", "/sessions")
            raw_sessions = response if isinstance(response, list) else response.get("data", [])
            for session in raw_sessions:
                if session.get('uuid') == browser_id:
                    return browser_id, short_id, session.get('name')
            raise Exception(f"未找到 UUID 为 {browser_id} 的会话")

        # 2. 短ID,先检查映射缓存
        if browser_id in self._uuid_mapping:
            full_uuid = self._uuid_mapping[browser_id]
            # 尝试从端口缓存获取handler_name
            cached = self._get_from_cache(full_uuid)
            if cached:
                return full_uuid, browser_id, cached['handler_name']

        # 3. 缓存未命中,查询API
        response = await self._request("GET", "/sessions")
        raw_sessions = response if isinstance(response, list) else response.get("data", [])

        for session in raw_sessions:
            session_uuid = session.get('uuid')
            session_id = session_uuid.split('-')[0] if session_uuid else None

            if session_uuid == browser_id or session_id == browser_id:
                # 更新映射缓存
                if session_id:
                    self._uuid_mapping[session_id] = session_uuid
                return session_uuid, session_id, session.get('name')

        raise Exception(f"未找到 ID 为 {browser_id} 的会话")

    # ==================== 绑定操作方法 ====================
    # 这些方法从 operations/ 模块导入,每个方法独立成文件
    get_all_browsers_info = get_all_browsers_info
    get_single_browser_info = get_single_browser_info
    create_new_browser = create_new_browser
    launch_browser = launch_browser
    close_browser = close_browser
    delete_browser = delete_browser
    close_all_browser = close_all_browser
    force_close_browser = force_close_browser

    @classmethod
    def _cleanup_all_sessions(cls):
        """
        清理所有实例的会话资源 (类方法,用于 atexit)

        在程序退出时自动调用,关闭所有 aiohttp 会话
        """
        for instance in cls._instances:
            if instance._session and not instance._session.closed:
                try:
                    # 强制同步关闭
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        # 直接关闭,忽略事件循环
                        if hasattr(instance._session, '_connector'):
                            if instance._session._connector:
                                instance._session._connector._close()
                        instance._session._connector = None
                except Exception:
                    pass  # 静默失败
        cls._instances.clear()

    async def close_session(self):
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("HTTP会话已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出，自动关闭会话"""
        await self.close_session()
