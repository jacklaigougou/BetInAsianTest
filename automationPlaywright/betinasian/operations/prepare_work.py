# -*- coding: utf-8 -*-
"""
BetInAsian 准备工作
"""
from typing import Dict, Any
import logging
import asyncio

logger = logging.getLogger(__name__)


async def prepare_work(
    controller: Any,
    target_url: str = "https://black.betinasia.com/sportsbook/basketball?group=in+running",
    subscribe_sports: list = None,
    **kwargs
) -> Dict[str, Any]:
    """
    准备工作:检查/打开目标页面,注入 WebSocket Hook

    Args:
        controller: BrowserControler 实例
        target_url: 目标页面 URL
        subscribe_sports: 要订阅的运动列表,如 ['basket', 'fb'],默认 ['basket']
        **kwargs: 额外参数

    Returns:
        {
            'success': bool,
            'message': str,
            'page': Page对象,
            'ws_status': WebSocket状态
        }
    """
    # 设置默认订阅运动
    if subscribe_sports is None:
        subscribe_sports = ['basket']

    try:
        # ========== 第1步: 检查目标 URL 是否存在 ==========
        logger.info(f"检查目标页面是否已打开: {target_url}")
        check_result = await controller.check_url_exists(target_url)

        if check_result['exists']:
            logger.info(f"✓ 目标页面已存在: {check_result['url']}")
            target_page = check_result.get('page')
        else:
            # 创建新页面
            logger.info(f"✗ 未找到目标页面，正在打开: {target_url}")
            create_result = await controller.create_new_page(target_url)
            target_page = create_result.get('page')

            if target_page:
                logger.info(f"✓ 成功打开页面: {target_page.url}")
            else:
                return {
                    'success': False,
                    'message': '创建页面失败',
                    'page': None,
                    'ws_status': None
                }

        # ========== 第2步: 注入 WebSocket Hook ==========
        if not target_page:
            logger.error("✗ 未能获取页面对象，无法注入 Hook")
            return {
                'success': False,
                'message': '未能获取页面对象',
                'page': None,
                'ws_status': None
            }

        logger.info("\n开始注入 WebSocket Hook...")

        # 导入注入函数
        from automationPlaywright.betinasian.jsCodeExcutors import inject_websocket_hook, check_websocket_status

        hook_success = await inject_websocket_hook(
            target_page,
            handler_name="BetInAsian",
            subscribe_sports=subscribe_sports
        )

        if not hook_success:
            logger.warning("⚠ WebSocket Hook 注入失败")
            return {
                'success': False,
                'message': 'WebSocket Hook 注入失败',
                'page': target_page,
                'ws_status': None
            }

        logger.info("✓ WebSocket Hook 注入成功!")

        # ========== 第3步: 等待 WebSocket 连接建立 ==========
        logger.info("等待 WebSocket 连接建立...")
        await asyncio.sleep(3)

        # ========== 第4步: 检查 WebSocket 状态 ==========
        ws_status = await check_websocket_status(target_page, handler_name="BetInAsian")
        logger.info(f"WebSocket 连接状态: {ws_status}")

        # ========== 第5步: 等待自动订阅完成 ==========
        logger.info(f"等待自动订阅完成 (配置: {subscribe_sports}, 延迟: 10秒)...")
        await asyncio.sleep(12)  # 10秒订阅延迟 + 2秒缓冲

        # 查看订阅统计
        try:
            sub_stats = await target_page.evaluate("window.getSubscriptionStats()")
            logger.info(f"订阅统计: {sub_stats}")
        except Exception as e:
            logger.warning(f"获取订阅统计失败: {e}")

        # ========== 返回成功 ==========
        return {
            'success': True,
            'message': '准备工作完成',
            'page': target_page,
            'ws_status': ws_status
        }

    except Exception as e:
        logger.error(f"准备工作失败: {e}", exc_info=True)
        return {
            'success': False,
            'message': f'准备工作异常: {str(e)}',
            'page': None,
            'ws_status': None
        }
