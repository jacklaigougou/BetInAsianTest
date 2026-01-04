# -*- coding: utf-8 -*-
"""
浏览器控制器抽象基类
定义浏览器页面操作的标准接口规范
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Union, Dict


class BrowserControllerBase(ABC):
    """
    浏览器控制器抽象基类

    标准接口：
    1. check_url_exists - 检查是否存在目标 URL 的页面
    2. create_new_page - 新建一个页面
    3. close_single_page - 关闭单个指定的页面
    4. close_other_pages - 关闭除目标页面之外的所有页面
    """

    def __init__(self, browser: Any, **kwargs):
        """
        初始化浏览器控制器基类

        Args:
            browser: Browser 对象（不同工具有不同的类型）
            **kwargs: 其他配置参数
        """
        self.browser = browser
        self.config = kwargs

    @abstractmethod
    async def check_url_exists(self, target_url: str) -> Dict[str, Any]:
        """
        检查是否存在目标 URL 的页面

        Args:
            target_url: 目标 URL（可以是部分 URL，会进行包含匹配）

        Returns:
            {
                'exists': bool,           # 是否存在
                'page': Any,              # 页面对象（如果存在）
                'url': str,               # 实际 URL（如果存在）
            }
        """
        pass

    @abstractmethod
    async def create_new_page(self, url: str, **kwargs) -> Any:
        """
        新建一个页面

        Args:
            url: 要打开的 URL
            **kwargs: 额外参数
                - wait_until: 等待条件（如 'load', 'domcontentloaded', 'networkidle'）
                - timeout: 超时时间（毫秒）

        Returns:
            页面对象
        """
        pass

    @abstractmethod
    async def close_single_page(self, target_url: str) -> Dict[str, Any]:
        """
        关闭单个指定的页面

        Args:
            target_url: 目标页面 URL（支持部分匹配）

        Returns:
            {
                'success': bool,          # 是否成功关闭
                'closed_url': str,        # 关闭的页面 URL
                'message': str,           # 结果消息
            }
        """
        pass

    @abstractmethod
    async def close_other_pages(self, keep_urls: Union[str, List[str]]) -> Dict[str, Any]:
        """
        关闭除目标页面之外的所有页面

        Args:
            keep_urls: 要保留的页面 URL（可以是单个字符串或列表）
                      支持部分匹配，只要页面 URL 包含列表中的任意一个字符串即保留

        Returns:
            {
                'total_pages': int,       # 总页面数
                'closed': int,            # 关闭的页面数
                'kept': int,              # 保留的页面数
                'kept_pages': List[str]   # 保留的页面 URL 列表
            }
        """
        pass


__all__ = ['BrowserControllerBase']
