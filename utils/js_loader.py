# -*- coding: utf-8 -*-
"""
JS 文件加载器
职责: 预加载所有平台的 JS 文件到内存,提供统一访问接口
"""
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class JSLoader:
    """JS 文件加载器"""

    def __init__(self):
        """初始化加载器"""
        self._js_cache: Dict[str, str] = {}  # 存储格式: {platform_name/relative_path: content}
        self._file_count: Dict[str, int] = {}  # 每个平台加载的文件数量

    def load_platform_js(self, platform_name: str, js_base_path: str) -> int:
        """
        加载指定平台的所有 JS 文件

        Args:
            platform_name: 平台名称 (如 'betinasian', 'pin888')
            js_base_path: JS 文件基础路径

        Returns:
            int: 加载的文件数量
        """
        if not os.path.exists(js_base_path):
            logger.error(f"[{platform_name}] JS 基础路径不存在: {js_base_path}")
            return 0

        count = 0
        logger.info(f"[{platform_name}] 开始加载 JS 文件: {js_base_path}")

        # 递归扫描目录
        for root, dirs, files in os.walk(js_base_path):
            for file in files:
                if file.endswith('.js'):
                    # 构建完整路径
                    full_path = os.path.join(root, file)

                    # 计算相对路径
                    relative_path = os.path.relpath(full_path, js_base_path)
                    # 统一使用正斜杠
                    relative_path = relative_path.replace('\\', '/')

                    # 读取文件内容
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # 存储到缓存
                        cache_key = f"{platform_name}/{relative_path}"
                        self._js_cache[cache_key] = content
                        count += 1

                        logger.debug(f"[{platform_name}] ✅ 已加载: {relative_path}")

                    except Exception as e:
                        logger.error(f"[{platform_name}] ❌ 加载失败: {relative_path}, 错误: {e}")

        # 记录统计
        self._file_count[platform_name] = count
        logger.info(f"[{platform_name}] ✅ 加载完成: {count} 个文件")

        return count

    def get_js_content(self, platform_name: str, relative_path: str) -> Optional[str]:
        """
        获取指定 JS 文件内容

        Args:
            platform_name: 平台名称
            relative_path: 相对路径 (例如: 'wsDataRegistor/core/events_store.js')

        Returns:
            str: JS 文件内容,如果不存在返回 None
        """
        # 统一使用正斜杠
        relative_path = relative_path.replace('\\', '/')

        cache_key = f"{platform_name}/{relative_path}"
        content = self._js_cache.get(cache_key)

        if content is None:
            logger.warning(f"[{platform_name}] JS 文件未找到: {relative_path}")

        return content

    def get_file_count(self, platform_name: str) -> int:
        """
        获取指定平台加载的文件数量

        Args:
            platform_name: 平台名称

        Returns:
            int: 文件数量
        """
        return self._file_count.get(platform_name, 0)

    def clear_cache(self, platform_name: Optional[str] = None):
        """
        清空缓存

        Args:
            platform_name: 平台名称,如果为 None 则清空所有缓存
        """
        if platform_name is None:
            # 清空所有
            self._js_cache.clear()
            self._file_count.clear()
            logger.info("已清空所有 JS 缓存")
        else:
            # 清空指定平台
            keys_to_remove = [key for key in self._js_cache.keys() if key.startswith(f"{platform_name}/")]
            for key in keys_to_remove:
                del self._js_cache[key]

            if platform_name in self._file_count:
                del self._file_count[platform_name]

            logger.info(f"[{platform_name}] 已清空 JS 缓存")

    def get_stats(self) -> Dict[str, int]:
        """
        获取加载统计信息

        Returns:
            dict: {platform_name: file_count}
        """
        return self._file_count.copy()

    def is_loaded(self, platform_name: str) -> bool:
        """
        检查指定平台是否已加载

        Args:
            platform_name: 平台名称

        Returns:
            bool: 是否已加载
        """
        return platform_name in self._file_count and self._file_count[platform_name] > 0


# 全局单例
_js_loader_instance = None


def get_js_loader() -> JSLoader:
    """
    获取 JS 加载器单例

    Returns:
        JSLoader: 加载器实例
    """
    global _js_loader_instance
    if _js_loader_instance is None:
        _js_loader_instance = JSLoader()
    return _js_loader_instance
