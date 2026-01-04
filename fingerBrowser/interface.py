"""
指纹浏览器基础抽象类
定义指纹浏览器的标准接口规范
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class FingerBrowserBase(ABC):
    """
    指纹浏览器抽象基类

    标准接口：
    1. get_all_browsers_info - 获取所有浏览器配置信息
    2. get_single_browser_info - 获取单个浏览器的详细信息
    3. create_new_browser - 创建新的浏览器配置
    4. launch_browser - 启动指定的浏览器
    5. close_browser - 关闭正在运行的浏览器
    6. delete_browser - 删除浏览器配置
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        """
        初始化指纹浏览器基类

        Args:
            api_key: API密钥（某些浏览器可能不需要）
            base_url: API基础URL(可选)
            **kwargs: 其他配置参数
        """
        self.api_key = api_key or ""
        self.base_url = base_url
        self.config = kwargs

    @abstractmethod
    async def get_all_browsers_info(self, **kwargs) -> List[Dict[str, Any]]:
        """
        获取所有浏览器配置信息

        Returns:
            List[Dict]: 浏览器信息列表
        """
        pass

    @abstractmethod
    async def get_single_browser_info(self, browser_id: str, **kwargs) -> Dict[str, Any]:
        """
        获取单个浏览器的详细信息

        Args:
            browser_id: 浏览器唯一标识ID

        Returns:
            Dict: 浏览器详细信息
        """
        pass

    @abstractmethod
    async def create_new_browser(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新的浏览器配置

        Args:
            config: 浏览器配置参数

        Returns:
            Dict: 创建成功后的浏览器信息
        """
        pass

    @abstractmethod
    async def launch_browser(self, browser_id: str, **kwargs) -> Dict[str, Any]:
        """
        启动指定的浏览器

        Args:
            browser_id: 浏览器唯一标识ID

        Returns:
            Dict: 启动结果信息
        """
        pass

    @abstractmethod
    async def close_browser(self, browser_id: str, **kwargs) -> bool:
        """
        关闭正在运行的浏览器

        Args:
            browser_id: 浏览器唯一标识ID

        Returns:
            bool: 关闭成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def delete_browser(self, browser_id: str, **kwargs) -> bool:
        """
        删除浏览器配置

        Args:
            browser_id: 浏览器唯一标识ID

        Returns:
            bool: 删除成功返回True，失败返回False
        """
        pass


__all__ = ['FingerBrowserBase']
