"""
删除浏览器配置
"""
import logging

logger = logging.getLogger(__name__)


async def delete_browser(
    self,
    browser_id: str,
    **kwargs
) -> bool:
    """
    删除浏览器配置

    Args:
        browser_id: 浏览器唯一标识ID (user_id)
        **kwargs: 其他删除参数 (ADS API 不支持额外参数)

    Returns:
        删除成功返回True,失败返回False
    """
    try:
        # 调用 ADS API 删除浏览器
        # 注意: ADS API 使用 POST 方法,需要传递 JSON 数据
        endpoint = "/api/v1/user/delete"

        payload = {
            "user_ids": [browser_id]
        }

        response = await self._request("POST", endpoint, json=payload)

        # 解析响应
        if not isinstance(response, dict):
            logger.error(f"ADS API 返回格式错误: {response}")
            return False

        code = response.get('code')
        msg = response.get('msg', '')

        # 根据 code 判断是否成功
        success = (code == 0)

        if success:
            logger.info(f"浏览器 {browser_id} 删除成功")
            # 清理缓存
            self._remove_from_cache(browser_id)
        else:
            logger.error(f"删除浏览器失败: code={code}, msg={msg}")

        return success

    except Exception as e:
        logger.error(f"删除浏览器 {browser_id} 异常: {e}")
        return False
