"""
关闭所有运行中的浏览器
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def close_all_browser(self, **kwargs) -> Dict[str, Any]:
    """
    关闭所有运行中的浏览器

    Args:
        **kwargs: 额外参数
            - force: 是否强制关闭(可选)

    Returns:
        关闭结果统计:
        {
            "total": 总数,
            "closed": 成功关闭数,
            "failed": 失败数,
            "details": [详细信息列表]
        }
    """
    logger.info("开始关闭所有运行中的浏览器...")

    # 1. 获取所有浏览器
    response = await self._request("GET", "/sessions")
    raw_sessions = response if isinstance(response, list) else response.get("data", [])

    # 2. 筛选运行中的浏览器
    running_browsers = [
        s for s in raw_sessions
        if s.get('status') in ['running', 'automationRunning']
    ]

    total = len(running_browsers)
    closed = 0
    failed = 0
    details = []

    logger.info(f"找到 {total} 个运行中的浏览器")

    if total == 0:
        logger.info("没有运行中的浏览器")
        return {
            "total": 0,
            "closed": 0,
            "failed": 0,
            "details": []
        }

    # 3. 逐个关闭
    for session in running_browsers:
        uuid = session.get('uuid')
        name = session.get('name')
        status = session.get('status')

        try:
            logger.info(f"正在关闭浏览器: {name} ({uuid[:8]}...) [{status}]")

            # 调用 close_browser
            success = await self.close_browser(uuid, **kwargs)

            if success:
                closed += 1
                details.append({
                    "uuid": uuid,
                    "name": name,
                    "status": "success"
                })
                logger.info(f"✓ 成功关闭: {name}")
            else:
                failed += 1
                details.append({
                    "uuid": uuid,
                    "name": name,
                    "status": "failed",
                    "error": "close_browser returned False"
                })
                logger.warning(f"✗ 关闭失败: {name}")

        except Exception as e:
            failed += 1
            details.append({
                "uuid": uuid,
                "name": name,
                "status": "error",
                "error": str(e)
            })
            logger.error(f"✗ 关闭出错: {name}, 错误: {e}")

    # 4. 返回统计结果
    result = {
        "total": total,
        "closed": closed,
        "failed": failed,
        "details": details
    }

    logger.info(
        f"关闭完成 - 总数: {total}, 成功: {closed}, 失败: {failed}"
    )

    return result
