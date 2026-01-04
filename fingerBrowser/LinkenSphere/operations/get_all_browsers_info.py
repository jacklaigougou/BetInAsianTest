"""
获取所有浏览器会话信息
GET http://127.0.0.1:40080/sessions
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


async def get_all_browsers_info(self, auto_close_running: bool = False, **kwargs) -> List[Dict[str, Any]]:
    """
    获取所有浏览器会话信息

    Args:
        auto_close_running: 如果为 True,在获取信息前先关闭所有运行中的浏览器(默认 False)
        **kwargs: 额外查询参数（预留）

    Returns:
        包含所有浏览器会话的列表

    HTTP请求:
        GET http://127.0.0.1:40080/sessions
    """
    logger.info("正在获取所有浏览器会话信息")

    # 1. 如果需要,先关闭所有运行中的浏览器
    if auto_close_running:
        logger.info("检测到 auto_close_running=True,先关闭所有运行中的浏览器...")

        # 获取当前所有浏览器
        response = await self._request("GET", "/sessions")
        raw_data = response if isinstance(response, list) else response.get("data", [])

        # 筛选运行中的浏览器
        running_browsers = [
            s for s in raw_data
            if s.get('status') in ['running', 'automationRunning']
        ]

        if running_browsers:
            logger.info(f"找到 {len(running_browsers)} 个运行中的浏览器,正在关闭...")

            # 逐个关闭
            for session in running_browsers:
                uuid = session.get('uuid')
                name = session.get('name')

                try:
                    await self.close_browser(uuid)
                    logger.info(f"✓ 已关闭: {name} ({uuid[:8]}...)")
                except Exception as e:
                    logger.warning(f"✗ 关闭失败: {name}, 错误: {e}")

            logger.info("所有运行中的浏览器已关闭")
        else:
            logger.info("没有运行中的浏览器需要关闭")

    # 2. 获取最新的浏览器列表
    response = await self._request("GET", "/sessions")

    # 获取原始数据
    if isinstance(response, list):
        raw_data = response
    else:
        raw_data = response.get("data", []) if isinstance(response, dict) else []

    # 转换数据格式
    return [self._transform_browser_data(item) for item in raw_data]
