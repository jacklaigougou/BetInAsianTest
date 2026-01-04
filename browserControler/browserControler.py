# -*- coding: utf-8 -*-
"""
浏览器控制器统一接口
支持多种自动化工具（Playwright, Puppeteer等）
"""
from typing import Any, Union, List, Dict


class BrowserControler:
    """浏览器控制器统一接口类"""

    def __init__(self, browser_object: Any, tool: str = "playwright", **kwargs):
        """
        初始化浏览器控制器

        Args:
            browser_object: Browser 对象（Playwright Browser 或 Puppeteer Browser）
            tool: 自动化工具类型 ("playwright" 或 "puppeteer")
            **kwargs: 其他配置参数
        """
        self.tool = tool
        self.config = kwargs

        # 根据工具类型初始化对应的控制器
        if tool == "playwright":
            from ._Playwright.playwright_controller import PlaywrightController
            self._controller = PlaywrightController(browser_object, **kwargs)
        elif tool == "puppeteer":
            from ._Puppeteer.puppeteer_controller import PuppeteerController
            self._controller = PuppeteerController(browser_object, **kwargs)
        else:
            raise ValueError(
                f"不支持的工具类型: {tool}\n"
                f"支持的类型: playwright, puppeteer"
            )

    async def check_url_exists(self, target_url: str) -> Dict[str, Any]:
        """
        检查是否存在目标 URL 的页面

        Args:
            target_url: 目标 URL

        Returns:
            检查结果字典:
            {
                'exists': bool,
                'page': Any,
                'url': str
            }
        """
        return await self._controller.check_url_exists(target_url)

    async def create_new_page(self, url: str, **kwargs) -> Any:
        """
        新建一个页面

        Args:
            url: 要打开的 URL
            **kwargs: 额外参数
                - wait_until: 等待条件
                - timeout: 超时时间

        Returns:
            页面对象
        """
        return await self._controller.create_new_page(url, **kwargs)

    async def close_single_page(self, target_url: str) -> Dict[str, Any]:
        """
        关闭单个指定的页面

        Args:
            target_url: 目标页面 URL（支持部分匹配）

        Returns:
            关闭结果字典:
            {
                'success': bool,
                'closed_url': str,
                'message': str
            }
        """
        return await self._controller.close_single_page(target_url)

    async def close_other_pages(self, keep_urls: Union[str, List[str]]) -> Dict[str, Any]:
        """
        关闭除目标页面之外的所有页面

        Args:
            keep_urls: 要保留的页面 URL（可以是单个字符串或列表）

        Returns:
            关闭结果统计字典:
            {
                'total_pages': int,
                'closed': int,
                'kept': int,
                'kept_pages': List[str]
            }
        """
        return await self._controller.close_other_pages(keep_urls)
