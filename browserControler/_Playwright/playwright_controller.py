# -*- coding: utf-8 -*-
"""
Playwright 浏览器控制器实现
"""
from typing import Any, Union, List, Dict
import logging
from ..interface import BrowserControllerBase

logger = logging.getLogger(__name__)


class PlaywrightController(BrowserControllerBase):
    """Playwright 浏览器控制器实现"""

    def __init__(self, browser: Any, **kwargs):
        """
        初始化 Playwright 控制器

        Args:
            browser: Playwright Browser 对象
            **kwargs: 其他配置参数
        """
        super().__init__(browser, **kwargs)
        logger.info("初始化 Playwright 浏览器控制器")

    async def check_url_exists(self, target_url: str) -> Dict[str, Any]:
        """
        检查是否存在目标 URL 的页面

        Args:
            target_url: 目标 URL

        Returns:
            {
                'exists': bool,
                'page': Page | None,
                'url': str
            }
        """
        logger.info(f"检查页面是否存在: {target_url}")

        # 遍历所有上下文和页面
        for context in self.browser.contexts:
            for page in context.pages:
                page_url = page.url
                if target_url in page_url:
                    logger.info(f"✓ 找到目标页面: {page_url}")
                    return {
                        'exists': True,
                        'page': page,
                        'url': page_url
                    }

        logger.info(f"✗ 未找到目标页面: {target_url}")
        return {
            'exists': False,
            'page': None,
            'url': ''
        }

    async def create_new_page(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        新建一个页面

        Args:
            url: 要打开的 URL
            **kwargs: 额外参数
                - wait_until: 'load' | 'domcontentloaded' | 'networkidle'
                - timeout: 超时时间（毫秒）

        Returns:
            {
                'success': bool,
                'page': Page | None,
                'url': str,
                'message': str
            }
        """
        logger.info(f"创建新页面: {url}")

        try:
            # 获取或创建上下文
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
                logger.debug("使用现有浏览器上下文")
            else:
                context = await self.browser.new_context()
                logger.debug("创建新的浏览器上下文")

            # 创建新页面
            page = await context.new_page()

            # 导航到目标 URL
            goto_options = {}
            if 'wait_until' in kwargs:
                goto_options['wait_until'] = kwargs['wait_until']
            if 'timeout' in kwargs:
                goto_options['timeout'] = kwargs['timeout']

            await page.goto(url, **goto_options)
            logger.info(f"✓ 页面创建成功: {page.url}")

            return {
                'success': True,
                'page': page,
                'url': page.url,
                'message': '页面创建成功'
            }

        except Exception as e:
            logger.error(f"✗ 页面创建失败: {e}")
            return {
                'success': False,
                'page': None,
                'url': '',
                'message': f'页面创建失败: {e}'
            }

    async def close_single_page(self, target_url: str) -> Dict[str, Any]:
        """
        关闭单个指定的页面

        Args:
            target_url: 目标页面 URL（支持部分匹配）

        Returns:
            {
                'success': bool,
                'closed_url': str,
                'message': str
            }
        """
        logger.info(f"关闭单个页面: {target_url}")

        # 遍历所有上下文和页面，查找并关闭目标页面
        for context in self.browser.contexts:
            for page in context.pages:
                page_url = page.url
                if target_url in page_url:
                    # 找到目标页面，关闭它
                    await page.close()
                    logger.info(f"✓ 成功关闭页面: {page_url}")
                    return {
                        'success': True,
                        'closed_url': page_url,
                        'message': f'成功关闭页面: {page_url}'
                    }

        # 未找到目标页面
        logger.warning(f"✗ 未找到目标页面: {target_url}")
        return {
            'success': False,
            'closed_url': '',
            'message': f'未找到目标页面: {target_url}'
        }

    async def close_other_pages(self, keep_urls: Union[str, List[str]]) -> Dict[str, Any]:
        """
        关闭除目标页面之外的所有页面

        Args:
            keep_urls: 要保留的页面 URL（可以是单个字符串或列表）

        Returns:
            {
                'total_pages': int,
                'closed': int,
                'kept': int,
                'kept_pages': List[str]
            }
        """
        # 转换为列表
        if isinstance(keep_urls, str):
            keep_urls = [keep_urls]

        logger.info(f"关闭其他页面，保留: {keep_urls}")

        total_pages = 0
        closed = 0
        kept_pages = []

        # 遍历所有上下文和页面
        for context in self.browser.contexts:
            for page in context.pages:
                total_pages += 1
                page_url = page.url

                # 检查是否需要保留（部分匹配）
                should_keep = any(keep_url in page_url for keep_url in keep_urls)

                if should_keep:
                    kept_pages.append(page_url)
                    logger.debug(f"保留页面: {page_url}")
                else:
                    await page.close()
                    closed += 1
                    logger.debug(f"关闭页面: {page_url}")

        result = {
            'total_pages': total_pages,
            'closed': closed,
            'kept': len(kept_pages),
            'kept_pages': kept_pages
        }

        logger.info(f"✓ 关闭完成: 总计 {total_pages} 个页面，关闭 {closed} 个，保留 {len(kept_pages)} 个")
        return result
