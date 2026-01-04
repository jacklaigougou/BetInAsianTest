"""
关闭浏览器
"""
import logging

logger = logging.getLogger(__name__)


async def close_browser(
    self,
    browser_id: str,
    **kwargs
) -> bool:
    """
    关闭正在运行的浏览器

    Args:
        browser_id: 浏览器唯一标识ID (user_id)
        **kwargs: 其他关闭参数 (ADS API 不支持额外参数)

    Returns:
        关闭成功返回True,失败返回False
    """
    try:
        # 调用 ADS API 关闭浏览器
        endpoint = f"/api/v1/browser/stop?user_id={browser_id}"
        response = await self._request("GET", endpoint)

        # 解析响应
        if not isinstance(response, dict):
            logger.error(f"ADS API 返回格式错误: {response}")
            return False

        code = response.get('code')
        msg = response.get('msg', '')

        # 根据 code 判断是否成功
        success = (code == 0)

        if success:
            logger.info(f"浏览器 {browser_id} 关闭成功")
            # 清理缓存中的端口信息
            self._remove_from_cache(browser_id)
        else:
            logger.error(f"关闭浏览器失败: code={code}, msg={msg}")

        return success

    except Exception as e:
        logger.error(f"关闭浏览器 {browser_id} 异常: {e}")
        return False
