"""
启动浏览器
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def launch_browser(
    self,
    browser_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    启动指定的浏览器

    Args:
        browser_id: 浏览器唯一标识ID (user_id)
        **kwargs: 启动配置参数 (ADS API 不支持额外参数)

    Returns:
        启动结果信息字典,包含:
        - uuid: user_id
        - debug_port: 调试端口
        - ws_url: WebSocket URL (puppeteer)
        - ws: 完整的 ws 对象
        - webdriver: ChromeDriver 路径
    """
    try:
        # 调用 ADS API 启动浏览器
        endpoint = f"/api/v1/browser/start?user_id={browser_id}"
        response = await self._request("GET", endpoint)

        # 解析响应
        if not isinstance(response, dict):
            logger.error(f"ADS API 返回格式错误: {response}")
            # 返回失败结果而不是抛异常
            return {
                'uuid': browser_id,
                'debug_port': '',
                'success': False,
                'error': 'API 返回格式错误',
                'ws_url': '',
                'ws': {},
                'webdriver': '',
            }

        code = response.get('code')
        msg = response.get('msg', '')
        data = response.get('data', {})

        # 根据 code 判断是否成功
        success = (code == 0)

        if not success:
            # 启动失败,返回失败结果
            logger.error(f"启动浏览器失败: code={code}, msg={msg}")
            return {
                'uuid': browser_id,
                'debug_port': '',
                'success': False,
                'error': msg or f'启动失败 (code={code})',
                'ws_url': '',
                'ws': {},
                'webdriver': '',
            }

        # 启动成功,提取核心字段
        debug_port = data.get('debug_port', '')
        ws_data = data.get('ws', {})
        ws_url = ws_data.get('puppeteer', '')
        webdriver = data.get('webdriver', '')

        # 构建返回结果 (符合 validate_launch_browser 要求)
        result = {
            'uuid': browser_id,
            'debug_port': debug_port,
            'success': True,
            # 额外字段
            'ws_url': ws_url,
            'ws': ws_data,
            'webdriver': webdriver,
        }

        # 更新缓存 (仅在成功时更新)
        cached = self._get_from_cache(browser_id)
        if cached:
            # 更新已有缓存的 debug_port 和 ws_url
            self._update_cache(
                uuid=browser_id,
                short_id=cached.get('id', ''),
                name=cached.get('name', ''),
                debug_port=int(debug_port) if debug_port else 0,
                ws_url=ws_url
            )
        else:
            # 缓存中没有,创建基础缓存
            self._update_cache(
                uuid=browser_id,
                short_id=browser_id,  # 暂时使用 user_id
                name=browser_id,
                debug_port=int(debug_port) if debug_port else 0,
                ws_url=ws_url
            )

        logger.info(f"浏览器 {browser_id} 启动成功, debug_port={debug_port}")
        return result

    except Exception as e:
        logger.error(f"启动浏览器 {browser_id} 异常: {e}")
        # 即使发生异常也返回失败结果而不是抛出
        return {
            'uuid': browser_id,
            'debug_port': '',
            'success': False,
            'error': str(e),
            'ws_url': '',
            'ws': {},
            'webdriver': '',
        }
