"""
指纹浏览器对外接口
提供简单易用的浏览器操作方法，支持多种指纹浏览器(Linken Sphere, ADS等)
"""
from typing import Dict, List, Optional, Any, Union
from .LinkenSphere.linken_sphere import LinkenSphere
from .output import (
    validate_get_all_browsers_info,
    validate_get_single_browser_info,
    validate_create_new_browser,
    validate_launch_browser,
    validate_close_browser,
    validate_delete_browser,
    validate_close_all_browser,
)


class FingerBrowser:
    """指纹浏览器统一接口类，支持多种浏览器"""

    def __init__(self, browser_type: str = "ads", **kwargs):
        """
            初始化指纹浏览器

            Args:
                browser_type: 浏览器类型 ("linken_sphere" 或 "ads")
                **kwargs: 其他初始化参数
                    - api_key: API密钥
                    - base_url: API基础URL(可选)
                    - timeout: 请求超时时间(可选)
                    - 其他浏览器特定参数

        """
        self.browser_type = browser_type
        self.config = kwargs

        # 根据类型初始化对应的浏览器实例
        if browser_type == "linken_sphere":
            self._browser = LinkenSphere(**kwargs)
        elif browser_type == "ads":
            from .ADS.ads_browser import ADSBrowser
            self._browser = ADSBrowser(**kwargs)
        else:
            raise ValueError(f"不支持的浏览器类型: {browser_type}，目前支持: linken_sphere, ads")

    @validate_get_all_browsers_info
    async def get_all_browsers_info(
        self,
        auto_close_running: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
            获取所有浏览器配置信息

            Args:
                auto_close_running: 如果为 True,在获取信息前先关闭所有运行中的浏览器(默认 False)
                **kwargs: 额外的查询参数
                    - page: 页码(可选)
                    - page_size: 每页数量(可选)
                    - filter: 筛选条件(可选)
                    - sort: 排序方式(可选)
                    - status: 浏览器状态筛选(可选)
                    - group_id: 分组ID筛选(可选)

            Returns:
                包含所有浏览器配置的列表,每个配置为一个字典

        """
        return await self._browser.get_all_browsers_info(
            auto_close_running=auto_close_running,
            **kwargs
        )

    @validate_get_single_browser_info
    async def get_single_browser_info(
        self,
        browser_id: str,
        auto_launch: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
            获取单个浏览器的详细信息

            Args:
                browser_id: 浏览器唯一标识ID
                auto_launch: 如果浏览器未启动,是否自动启动以获取完整信息(默认True)
                **kwargs: 额外的查询参数
                    - include_fingerprint: 是否包含指纹详情(可选)
                    - include_proxy: 是否包含代理详情(可选)
                    - include_cookies: 是否包含Cookie信息(可选)

            Returns:
                浏览器详细信息字典,包含配置、状态等完整信息:
                - uuid: 完整UUID
                - id: 短ID
                - handler_name: 浏览器名称
                - debug_port: 调试端口 (auto_launch=True时保证存在)
                - ws_url: WebSocket连接地址 (auto_launch=True时保证存在)
                - status: 运行状态
                - 其他配置信息...

       
        """
        return await self._browser.get_single_browser_info(
            browser_id,
            auto_launch=auto_launch,
            **kwargs
        )

    @validate_create_new_browser
    async def create_new_browser(
        self,
        name: Optional[str] = None,
        proxy: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
            创建新的浏览器配置

            Args:
                name: 浏览器名称(可选)
                proxy: 代理配置(可选)
                    {
                        "type": "http/https/socks5",
                        "host": "proxy.example.com",
                        "port": 8080,
                        "username": "user",
                        "password": "pass"
                    }
                fingerprint: 指纹配置(可选)
                **kwargs: 其他配置参数
                    - user_agent: 自定义UA(可选)
                    - platform: 操作系统平台(可选)
                    - webgl_vendor: WebGL厂商(可选)
                    - webgl_renderer: WebGL渲染器(可选)
                    - timezone: 时区(可选)
                    - language: 语言(可选)
                    - geolocation: 地理位置(可选)
                    - screen_resolution: 屏幕分辨率(可选)
                    - fonts: 字体列表(可选)
                    - canvas: Canvas指纹(可选)
                    - audio: Audio指纹(可选)
                    - group_id: 分组ID(可选)
                    - tags: 标签列表(可选)
                    - notes: 备注信息(可选)

            Returns:
                创建成功后返回的浏览器信息,包含生成的browser_id

            
        """
        # 构建配置字典
        config = {}
        if name is not None:
            config["name"] = name
        if proxy is not None:
            config["proxy"] = proxy
        if fingerprint is not None:
            config["fingerprint"] = fingerprint

        # 合并其他参数
        config.update(kwargs)

        return await self._browser.create_new_browser(config)

    @validate_launch_browser
    async def launch_browser(
        self,
        browser_id: str,
        headless: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
            启动指定的浏览器

            Args:
                browser_id: 浏览器唯一标识ID
                
            Returns:
                启动结果信息字典,包含:
                - debug_port: Chrome调试端口
                - ws_endpoint: WebSocket连接地址
                - pid: 进程ID
                - automation_port: 自动化端口(如适用)

        """
        launch_config = {"headless": headless}
        launch_config.update(kwargs)

        return await self._browser.launch_browser(browser_id, **launch_config)

    @validate_close_browser
    async def close_browser(self, browser_id: str, **kwargs) -> bool:
        """
            关闭正在运行的浏览器

            Args:
                browser_id: 浏览器唯一标识ID
                **kwargs: 其他关闭参数
                    - force: 是否强制关闭(可选)
                    - save_session: 是否保存会话(可选)
                    - timeout: 关闭超时时间(可选)

            Returns:
                关闭成功返回True,失败返回False

        """
        return await self._browser.close_browser(browser_id, **kwargs)

    async def force_close_browser(self, browser_id: str, **kwargs) -> bool:
        """
            强制关闭正在运行的浏览器

            与 close_browser 的区别:
            - close_browser: 正常关闭,如果浏览器被占用会失败
            - force_close_browser: 强制关闭,即使被其他客户端占用也会强制停止

            Args:
                browser_id: 浏览器唯一标识ID
                **kwargs: 其他关闭参数

            Returns:
                关闭成功返回True,失败返回False

            示例:
                >>> # 强制关闭被占用的浏览器
                >>> await finger_browser.force_close_browser("abc123")
        """
        return await self._browser.force_close_browser(browser_id, **kwargs)

    @validate_delete_browser
    async def delete_browser(self, browser_id: str, **kwargs) -> bool:
        """
            删除浏览器配置

            注意: 删除前请确保浏览器已关闭

            Args:
                browser_id: 浏览器唯一标识ID
                **kwargs: 其他删除参数
                    - delete_data: 是否删除用户数据(可选)
                    - force: 是否强制删除(可选)

            Returns:
                删除成功返回True,失败返回False

        
        """
        return await self._browser.delete_browser(browser_id, **kwargs)

    @validate_close_all_browser
    async def close_all_browser(self, **kwargs) -> Dict[str, Any]:
        """
            关闭所有运行中的浏览器

            Args:
                **kwargs: 额外参数
                    - force: 是否强制关闭(可选)

            Returns:
                关闭结果统计字典:
                {
                    "total": 运行中的浏览器总数,
                    "closed": 成功关闭的数量,
                    "failed": 失败的数量,
                    "details": [详细信息列表]
                }

        """
        return await self._browser.close_all_browser(**kwargs)

    async def update_browser(
        self,
        browser_id: str,
        name: Optional[str] = None,
        proxy: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
            更新浏览器配置

            Args:
                browser_id: 浏览器唯一标识ID
                name: 新的浏览器名称(可选)
                proxy: 新的代理配置(可选)
                **kwargs: 其他更新参数
                    - user_agent: 更新UA(可选)
                    - fingerprint: 更新指纹(可选)
                    - tags: 更新标签(可选)
                    - notes: 更新备注(可选)

            Returns:
                更新后的浏览器信息

        """
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if proxy is not None:
            update_data["proxy"] = proxy
        update_data.update(kwargs)

        if hasattr(self._browser, 'update_browser'):
            return await self._browser.update_browser(browser_id, update_data)
        else:
            raise NotImplementedError(f"{self.browser_type} 暂不支持更新操作")

    async def get_websocket_url(self, browser_id: str) -> Optional[str]:
        """
            获取浏览器的 WebSocket 调试 URL (通用实现)

            通过 Chrome DevTools Protocol (CDP) 获取 WebSocket 连接地址。
            此方法适用于所有基于 Chromium 的指纹浏览器。

            工作流程:
            1. 从底层浏览器缓存获取 debug_port
            2. 如果缓存中已有 ws_url,直接返回
            3. 否则调用 CDP API 获取并缓存

            Args:
                browser_id: 浏览器ID (短ID或完整UUID)

       
        """
        import aiohttp
        import logging

        logger = logging.getLogger(__name__)

        # 1. 解析 UUID (使用底层浏览器的方法)
        try:
            full_uuid, short_id, handler_name = await self._browser._resolve_uuid(browser_id)
        except Exception as e:
            logger.error(f"解析浏览器ID失败: {e}")
            return None

        # 2. 从底层缓存获取 debug_port
        cached = self._browser._get_from_cache(full_uuid)
        if not cached or 'debug_port' not in cached:
            logger.warning(f"浏览器 {handler_name} ({short_id}) 未启动或缺少 debug_port")
            return None

        debug_port = cached['debug_port']

        # 3. 如果缓存中已有 ws_url,直接返回
        if 'ws_url' in cached:
            logger.debug(f"从缓存获取 WebSocket URL: {cached['ws_url']}")
            return cached['ws_url']

        # 4. 调用 CDP API 获取 WebSocket URL
        try:
            # 直接访问浏览器的 debug_port
            url = f"http://127.0.0.1:{debug_port}/json/version"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status != 200:
                        logger.error(f"CDP API 返回错误状态码: {resp.status}")
                        return None

                    data = await resp.json()
                    ws_url = data.get('webSocketDebuggerUrl')

                    # 5. 更新底层缓存
                    if ws_url:
                        cached['ws_url'] = ws_url
                        self._browser._port_cache[full_uuid] = cached
                        logger.info(f"获取并缓存 WebSocket URL: {ws_url}")
                    else:
                        logger.warning("CDP 响应中未找到 webSocketDebuggerUrl")

                    return ws_url

        except aiohttp.ClientError as e:
            logger.error(f"连接 CDP 失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取 WebSocket URL 失败: {e}")
            return None

    async def get_cdp_object(
        self,
        ws_url: str = None,
        port: str = None,
        tool: str = "playwright",
        model: str = "ws_url",
        **kwargs
    ) -> Any:
        """
            连接到浏览器的 CDP 端点

            Args:
                ws_url: WebSocket URL (用于 playwright/puppeteer)
                port: 调试端口 (用于 selenium)
                tool: 使用的自动化工具 ("playwright", "puppeteer", "selenium")
                model: 连接模式 ("port" 或 "ws_url"), 默认 "port"
                **kwargs: 传递给 CDP 连接器的额外参数
                    - timeout: 连接超时时间 (Playwright 专用, 默认 30000ms)
                    - slow_mo: 减慢操作速度 (Playwright 专用, 默认 0ms)

            Returns:
                连接好的浏览器对象:
                - Playwright: Browser 对象
                - Puppeteer: Browser 对象
                - Selenium: WebDriver 对象

            Raises:
                ImportError: 如果所需的自动化工具未安装
                ValueError: 如果工具类型不支持
                Exception: 如果连接失败

            示例:
                >>> # 使用 Playwright 连接 (ws_url)
                >>> browser = await finger_browser.get_cdp_object(
                ...     ws_url="ws://127.0.0.1:9222/...",
                ...     tool="playwright"
                ... )
                >>> page = await browser.new_page()
                >>>
                >>> # 使用 Selenium 连接 (port)
                >>> driver = await finger_browser.get_cdp_object(
                ...     port="9222",
                ...     tool="selenium"
                ... )
                >>> driver.get("https://example.com")
        """
        # 根据 model 参数验证必需参数
        if model == "port":
            if not port:
                raise Exception(f"model 为 'port' 时,port 参数不能为空")
        elif model == "ws_url":
            if not ws_url:
                raise Exception(f"model 为 'ws_url' 时,ws_url 参数不能为空")

        # 根据工具类型进行连接
        if tool == "playwright":
            from .cdp import CDPConnector
            return await CDPConnector.get_playwright_cdp(
                ws_url=ws_url,
                port=port,
                model=model,
                **kwargs
            )

        else:

            raise ValueError(
                f"不支持的工具类型: {tool}\n"
                f"支持的类型: playwright"
            )

    async def judge_browser_working(self, browser_id: str, **kwargs) -> Dict[str, Any]:
        """
            判断浏览器是否正常工作

            Args:
                browser_id: 浏览器唯一标识ID
                **kwargs: 其他参数(保留用于未来扩展)

            Returns:
                工作状态信息字典:
                {
                    'is_working': bool,      # 是否正在运行
                    'status': str,           # 浏览器状态
                    'browser_id': str,       # 浏览器ID
                    'debug_port': str,       # 调试端口(如果运行中)
                    'ws_url': str,           # WebSocket URL(如果运行中)
                }

            示例:
                >>> # 检查浏览器是否运行
                >>> status = await finger_browser.judge_browser_working("abc123")
                >>> if status['is_working']:
                ...     print(f"浏览器正在运行，端口: {status['debug_port']}")
                ... else:
                ...     print(f"浏览器未运行: {status.get('message', '')}")
        """
        if hasattr(self._browser, 'judge_browser_working'):
            return await self._browser.judge_browser_working(browser_id, **kwargs)
        else:
            raise NotImplementedError(f"{self.browser_type} 暂不支持 judge_browser_working 操作")

    async def close_session(self):
        """关闭HTTP会话,释放资源"""
        if hasattr(self._browser, 'close_session'):
            await self._browser.close_session()

    async def __aenter__(self):
        """支持异步上下文管理器"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出时清理资源"""
        await self.close_session()
