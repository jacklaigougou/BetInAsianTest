"""
CDP 连接构造器
支持多种自动化工具连接到浏览器的 CDP 端点
"""
import logging
from typing import Optional, Any, Literal

logger = logging.getLogger(__name__)

# 支持的工具类型
CDPToolType = Literal["playwright"]


class CDPConnector:
    """CDP 连接构造器,支持多种自动化工具"""

    @staticmethod
    async def connect_playwright(
        ws_url: str,
        **kwargs
    ) -> Any:
        """
        使用 Playwright 连接到浏览器

        Args:
            ws_url: WebSocket 调试地址 (如: ws://127.0.0.1:9222/devtools/browser/xxx)
            **kwargs: Playwright 额外配置
                - timeout: 连接超时时间(毫秒,默认 30000)
                - slow_mo: 减慢操作速度(毫秒,默认 0)

        Returns:
            Playwright Browser 对象

        Raises:
            ImportError: 如果 playwright 未安装
            Exception: 连接失败
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "需要安装 playwright: pip install playwright\n"
                "安装后运行: playwright install"
            )

        logger.info(f"使用 Playwright 连接到: {ws_url}")

        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.connect_over_cdp(
                ws_url,
                timeout=kwargs.get('timeout', 30000),
                slow_mo=kwargs.get('slow_mo', 0)
            )

            logger.info(f"Playwright 连接成功")
            return browser

        except Exception as e:
            logger.error(f"Playwright 连接失败: {e}")
            raise Exception(f"Playwright 连接失败: {e}")

    @staticmethod
    async def get_playwright_cdp(
        ws_url: Optional[str] = None,
        port: Optional[str] = None,
        model: str = "ws_url",
        **kwargs
    ) -> Any:
        """
        使用 Playwright 连接到浏览器 (支持 port 和 ws_url 两种模式)

        Args:
            ws_url: WebSocket 调试地址 (model="ws_url" 时使用)
            port: 调试端口 (model="port" 时使用)
            model: 连接模式 ("port" 或 "ws_url"), 默认 "port"
            **kwargs: Playwright 额外配置
                - timeout: 连接超时时间(毫秒,默认 30000)
                - slow_mo: 减慢操作速度(毫秒,默认 0)

        Returns:
            Playwright Browser 对象

        Raises:
            ImportError: 如果 playwright 未安装
            ValueError: 如果 model 类型不支持
            Exception: 连接失败
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "需要安装 playwright: pip install playwright\n"
                "安装后运行: playwright install"
            )

        try:
            playwright = await async_playwright().start()

            # 根据 model 参数选择连接方式
            if model == "ws_url":
                # 使用 WebSocket URL 连接
                logger.info(f"使用 Playwright (ws_url模式) 连接到: {ws_url}")
                browser = await playwright.chromium.connect_over_cdp(
                    ws_url,
                    timeout=kwargs.get('timeout', 30000),
                    slow_mo=kwargs.get('slow_mo', 0)
                )
            elif model == "port":
                # 使用 port 连接
                endpoint_url = f"http://127.0.0.1:{port}"
                logger.info(f"使用 Playwright (port模式) 连接到: {endpoint_url}")
                browser = await playwright.chromium.connect_over_cdp(
                    endpoint_url,
                    timeout=kwargs.get('timeout', 30000),
                    slow_mo=kwargs.get('slow_mo', 0)
                )
            else:
                raise ValueError(f"不支持的 model 类型: {model}")

            logger.info(f"Playwright 连接成功")
            return browser

        except Exception as e:
            logger.error(f"Playwright 连接失败: {e}")
            raise Exception(f"Playwright 连接失败: {e}")

    
   


__all__ = ['CDPConnector', 'CDPToolType']
