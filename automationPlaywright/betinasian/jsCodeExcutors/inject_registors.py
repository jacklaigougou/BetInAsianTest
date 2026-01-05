# -*- coding: utf-8 -*-
"""
数据注册器注入器
职责: 按依赖顺序加载所有 JS 文件,初始化数据注册器系统
"""
from typing import Any
import logging
from utils import get_js_loader

logger = logging.getLogger(__name__)


def load_js_file_from_path(relative_path: str, platform_name: str = 'betinasian') -> str:
    """
    从缓存中加载 JS 文件

    Args:
        relative_path: 相对于 jsCode 目录的路径 (例如: 'wsDataRegistor/core/events_store.js')
        platform_name: 平台名称

    Returns:
        str: JS文件内容
    """
    try:
        js_loader = get_js_loader()
        content = js_loader.get_js_content(platform_name, relative_path)

        if content is None:
            logger.error(f"[{platform_name}] JS 文件未找到: {relative_path}")
            return ""

        logger.info(f"[{platform_name}] ✅ 从缓存加载: {relative_path}")
        return content

    except Exception as e:
        logger.error(f"[{platform_name}] ❌ 加载失败: {relative_path}, 错误: {e}")
        return ""


async def inject_data_registors(page: Any, handler_name: str = "BetInAsian") -> bool:
    """
    注入数据注册器系统到页面

    按依赖顺序加载所有 JS 文件:
    1. Core 模块 (store 和 index)
    2. Handler 模块
    3. Router 和 Query Engine
    4. 统一入口

    Args:
        page: Playwright Page 对象
        handler_name: 处理器名称

    Returns:
        bool: 注入成功返回 True
    """
    try:
        print(f"[{handler_name}] 🔧 开始注入数据注册器系统...")

        # 定义加载顺序 (按依赖关系)
        js_files = [
            # 第1层: Core 存储模块
            'wsDataRegistor/core/events_store.js',
            'wsDataRegistor/core/offers_store.js',
            'wsDataRegistor/core/events_manager.js',
            'wsDataRegistor/core/offers_manager.js',

            # 第2层: Handler 模块
            'wsDataRegistor/handlers/event_handler.js',
            'wsDataRegistor/handlers/offers_handler.js',
            'wsDataRegistor/handlers/api_handler.js',

            # 第3层: Router 和 Query Engine
            'wsDataRegistor/message_router.js',
            'wsDataRegistor/query_engine.js',

            # 第4层: 统一入口
            'wsDataRegistor/index.js'
        ]

        # 按顺序加载和执行
        for js_file in js_files:
            # 1. 加载文件内容
            code = load_js_file_from_path(js_file, 'betinasian')

            if not code:
                print(f"[{handler_name}] ❌ 加载失败: {js_file}")
                return False

            # 2. 执行代码
            try:
                await page.evaluate(code)
                print(f"[{handler_name}] ✅ 已加载: {js_file}")
            except Exception as e:
                print(f"[{handler_name}] ❌ 执行失败: {js_file}, 错误: {e}")
                return False

        # 验证注册器是否成功初始化
        print(f"[{handler_name}] 🔍 验证数据注册器...")

        # 检查关键函数是否存在
        checks = {
            'window.registerMessage': await page.evaluate("typeof window.registerMessage"),
            'window.queryData': await page.evaluate("typeof window.queryData"),
            'window.__eventsStore': await page.evaluate("typeof window.__eventsStore"),
            'window.__offersStore': await page.evaluate("typeof window.__offersStore"),
            'window.__eventsManager': await page.evaluate("typeof window.__eventsManager"),
            'window.__offersManager': await page.evaluate("typeof window.__offersManager")
        }

        all_ok = True
        for name, type_result in checks.items():
            expected = 'function' if 'register' in name or 'query' in name else 'object'
            if type_result != expected:
                print(f"[{handler_name}] ❌ {name} 不存在或类型错误: {type_result}")
                all_ok = False
            else:
                print(f"[{handler_name}] ✅ {name} 已就绪")

        if not all_ok:
            print(f"[{handler_name}] ❌ 数据注册器验证失败!")
            return False

        print(f"[{handler_name}] ✅ 数据注册器系统注入成功!")
        return True

    except Exception as e:
        logger.error(f"[{handler_name}] ❌ 注入数据注册器失败: {e}")
        return False


async def get_registor_stats(page: Any, handler_name: str = "BetInAsian") -> dict:
    """
    获取数据注册器统计信息

    Args:
        page: Playwright Page 对象
        handler_name: 处理器名称

    Returns:
        dict: 统计信息
    """
    try:
        stats = await page.evaluate("window.queryData.stats()")
        print(f"[{handler_name}] 数据注册器统计:")
        print(f"  - 总事件数: {stats.get('totalEvents', 0)}")
        print(f"  - 总市场数: {stats.get('totalMarkets', 0)}")
        return stats
    except Exception as e:
        logger.error(f"[{handler_name}] 获取统计信息失败: {e}")
        return {}


async def get_router_stats(page: Any, handler_name: str = "BetInAsian") -> dict:
    """
    获取消息路由统计信息

    Args:
        page: Playwright Page 对象
        handler_name: 处理器名称

    Returns:
        dict: 路由统计
    """
    try:
        stats = await page.evaluate("window.getRouterStats()")
        print(f"[{handler_name}] 消息路由统计:")
        print(f"  - 总消息数: {stats.get('totalMessages', 0)}")
        print(f"  - 成功处理: {stats.get('successCount', 0)}")
        print(f"  - 处理失败: {stats.get('errorCount', 0)}")
        print(f"  - 成功率: {stats.get('successRate', '0%')}")
        return stats
    except Exception as e:
        logger.error(f"[{handler_name}] 获取路由统计失败: {e}")
        return {}
