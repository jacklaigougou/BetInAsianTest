"""
ADS 指纹浏览器API实现
基于 ADS API 文档实现
"""
import aiohttp
from typing import Dict, List, Optional, Any
import logging
import atexit
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
    judge_browser_working,
)


logger = logging.getLogger(__name__)


class ADSBrowser(FingerBrowserBase):
    """ADS 指纹浏览器实现类"""

    # 类级别变量,跟踪所有实例
    _instances = []

    # 端口缓存: {完整UUID: {id, uuid, name, debug_port}}
    _port_cache: Dict[str, Dict[str, Any]] = {}

    # UUID映射缓存: {短ID: 完整UUID}
    _uuid_mapping: Dict[str, str] = {}

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        """
        初始化 ADS 浏览器客户端

        Args:
            api_key: ADS API密钥 (可选,本地API通常不需要)
            base_url: API基础URL (可选,默认为本地API地址)
            **kwargs: 其他配置参数
                - timeout: 请求超时时间(默认30秒)
        """
        super().__init__(api_key=api_key, base_url=base_url)
        self.api_key = api_key or ""
        self.base_url = base_url or "http://127.0.0.1:50325"
        self._session: Optional[aiohttp.ClientSession] = None
        self.timeout = kwargs.get('timeout', 30)

        # 将实例添加到跟踪列表
        ADSBrowser._instances.append(self)

        # 首次注册时设置清理钩子
        if len(ADSBrowser._instances) == 1:
            atexit.register(ADSBrowser._cleanup_all_sessions)

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        获取或创建HTTP会话

        Returns:
            aiohttp会话对象
        """
        if self._session is None or self._session.closed:
            # ADS 本地 API 不需要特殊认证头
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
            响应数据

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

                # 解析 JSON
                try:
                    data = await response.json()
                    return data
                except:
                    text = await response.text()
                    logger.warning(f"无法解析JSON响应，返回文本: {text}")
                    return {"raw_response": text}

        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {method} {url}, 错误: {str(e)}")
            raise Exception(f"网络请求失败: {str(e)}")

    def _transform_browser_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换浏览器数据格式(根据ADS API响应格式调整)

        Args:
            data: 原始浏览器数据

        Returns:
            转换后的数据
        """
        # TODO: 根据实际ADS API响应格式实现
        result = data.copy()
        return result

    def _get_from_cache(self, uuid: str) -> Optional[Dict[str, Any]]:
        """
        从缓存中获取浏览器信息

        Args:
            uuid: 完整的浏览器UUID

        Returns:
            缓存的浏览器信息
        """
        return self._port_cache.get(uuid)

    def _update_cache(
        self,
        uuid: str,
        short_id: str,
        name: str,
        debug_port: int,
        ws_url: Optional[str] = None
    ):
        """
        更新端口缓存

        Args:
            uuid: 完整UUID
            short_id: 短ID
            name: 浏览器名称
            debug_port: CDP调试端口
            ws_url: WebSocket调试URL (可选)
        """
        cache_data = {
            'id': short_id,
            'uuid': uuid,
            'name': name,
            'debug_port': debug_port
        }

        if ws_url:
            cache_data['ws_url'] = ws_url

        self._port_cache[uuid] = cache_data
        logger.debug(f"缓存更新: {name} ({short_id}) -> port {debug_port}")

    def _remove_from_cache(self, uuid: str) -> bool:
        """
        从缓存中移除

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
        解析browser_id为完整UUID

        Args:
            browser_id: 短ID或完整UUID

        Returns:
            (完整UUID, 短ID, 浏览器名称)
        """
        # TODO: 根据ADS API实现UUID解析逻辑
        raise NotImplementedError("ADS UUID解析待实现")

    # ==================== 绑定操作方法 ====================
    get_all_browsers_info = get_all_browsers_info
    get_single_browser_info = get_single_browser_info
    create_new_browser = create_new_browser
    launch_browser = launch_browser
    close_browser = close_browser
    delete_browser = delete_browser
    close_all_browser = close_all_browser
    judge_browser_working = judge_browser_working

    @classmethod
    def _cleanup_all_sessions(cls):
        """
        清理所有实例的会话资源

        在程序退出时自动调用
        """
        for instance in cls._instances:
            if instance._session and not instance._session.closed:
                try:
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        if hasattr(instance._session, '_connector'):
                            if instance._session._connector:
                                instance._session._connector._close()
                        instance._session._connector = None
                except Exception:
                    pass
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
        """异步上下文管理器退出"""
        await self.close_session()
