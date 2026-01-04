# -*- coding: utf-8 -*-
"""
BetInAsian Hook 注入器
"""
import os
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


def load_js_file(file_name: str, platform_name: str = 'betinasian') -> str:
    """
    加载指定平台的 JS 文件

    Args:
        file_name: JS文件名 (例如: '_0websocket_hook.js')
        platform_name: 平台名称 (默认: 'betinasian')

    Returns:
        str: JS文件内容,如果失败返回空字符串
    """
    try:
        # 获取当前文件的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 构建 jsCode 目录路径
        js_code_dir = os.path.join(current_dir, '..', 'jsCode')

        # 构建完整的文件路径
        file_path = os.path.join(js_code_dir, file_name)

        # 规范化路径
        file_path = os.path.normpath(file_path)

        logger.info(f"[{platform_name}] 尝试加载 JS 文件: {file_path}")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"[{platform_name}] JS 文件不存在: {file_path}")
            return ""

        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"[{platform_name}] ✅ 成功加载 JS 文件: {file_name} ({len(content)} 字符)")
        return content

    except Exception as e:
        logger.error(f"[{platform_name}] ❌ 加载 JS 文件失败: {e}")
        return ""


async def inject_websocket_hook(page: Any, handler_name: str = "BetInAsian") -> bool:
    """
    注入 WebSocket Hook 到页面

    Args:
        page: Playwright Page 对象
        handler_name: 处理器名称(用于日志)

    Returns:
        bool: 注入成功返回 True,失败返回 False
    """
    try:
        print(f"[{handler_name}] 🔧 开始注入 WebSocket Hook...")

        # 1. 加载 hook 脚本
        hook_code = load_js_file(
            file_name='_0websocket_hook.js',
            platform_name='betinasian'
        )

        if not hook_code:
            print(f"[{handler_name}] ❌ [BetInAsian] 加载 _0websocket_hook.js 失败")
            return False

        # 2. 使用 add_init_script 在页面加载前注入 hook (关键!)
        try:
            await page.add_init_script(hook_code)
            print(f"[{handler_name}] ✅ [BetInAsian] hook 脚本已添加到页面初始化脚本")
        except Exception as e:
            print(f"[{handler_name}] ❌ [BetInAsian] 添加 init_script 失败: {e}")
            return False

        # 3. 刷新页面,使 hook 在 WebSocket 创建之前生效
        print(f"[{handler_name}] 🔄 [BetInAsian] 刷新页面以激活 hook...")
        try:
            # 使用更宽松的等待策略,避免 networkidle 超时
            await page.reload(wait_until='domcontentloaded', timeout=15000)
            print(f"[{handler_name}] ✅ [BetInAsian] 页面刷新完成")
        except Exception as e:
            print(f"[{handler_name}] ⚠️ [BetInAsian] 页面刷新超时,但可能已加载: {e}")

        # 4. ⚠️ 调试: 页面刷新后立即手动执行 hook 脚本
        # 因为 add_init_script 在 CDP 连接的浏览器中可能不生效
        print(f"[{handler_name}] 🔧 [DEBUG] 手动执行 hook 脚本...")
        try:
            await page.evaluate(hook_code)
            print(f"[{handler_name}] ✅ [DEBUG] hook 脚本手动执行完成")

            # 5. 立即检查 hook 是否生效
            hook_check = await page.evaluate("typeof window.getWebSocketStatus")
            print(f"[{handler_name}] 🔍 [DEBUG] hook 检查: window.getWebSocketStatus = {hook_check}")

            if hook_check != 'function':
                print(f"[{handler_name}] ❌ [BetInAsian] Hook 未生效!")
                return False

        except Exception as e:
            print(f"[{handler_name}] ❌ [DEBUG] 手动执行 hook 失败: {e}")
            return False

        print(f"[{handler_name}] ✅ [BetInAsian] WebSocket Hook 注入成功!")
        return True

    except Exception as e:
        logger.error(f"[{handler_name}] ❌ 注入 WebSocket Hook 失败: {e}")
        return False


async def check_websocket_status(page: Any, handler_name: str = "BetInAsian") -> Dict[str, Any]:
    """
    检查 WebSocket 连接状态

    Args:
        page: Playwright Page 对象
        handler_name: 处理器名称

    Returns:
        Dict: WebSocket状态信息
    """
    try:
        status = await page.evaluate("window.getWebSocketStatus()")
        print(f"[{handler_name}] WebSocket 状态: {status}")
        return status
    except Exception as e:
        logger.error(f"[{handler_name}] 获取 WebSocket 状态失败: {e}")
        return {"error": str(e)}


async def get_recent_ws_messages(page: Any, count: int = 10, handler_name: str = "BetInAsian") -> list:
    """
    获取最近的 WebSocket 消息

    Args:
        page: Playwright Page 对象
        count: 获取消息数量
        handler_name: 处理器名称

    Returns:
        list: 消息列表
    """
    try:
        messages = await page.evaluate(f"window.getRecentMessages({count})")
        print(f"[{handler_name}] 获取到 {len(messages)} 条最近消息")
        return messages
    except Exception as e:
        logger.error(f"[{handler_name}] 获取 WebSocket 消息失败: {e}")
        return []


async def send_websocket_data(page: Any, data: str, handler_name: str = "BetInAsian") -> bool:
    """
    通过 WebSocket 发送数据

    Args:
        page: Playwright Page 对象
        data: 要发送的数据(字符串)
        handler_name: 处理器名称

    Returns:
        bool: 发送成功返回 True
    """
    try:
        result = await page.evaluate(f"window.sendWebSocketData({data})")
        if result:
            print(f"[{handler_name}] ✅ WebSocket 数据发送成功")
        else:
            print(f"[{handler_name}] ❌ WebSocket 数据发送失败")
        return result
    except Exception as e:
        logger.error(f"[{handler_name}] 发送 WebSocket 数据失败: {e}")
        return False
