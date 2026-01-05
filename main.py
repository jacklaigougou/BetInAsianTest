# -*- coding: utf-8 -*-
"""
BetInAsian 主程序
使用 ADS 指纹浏览器启动和管理浏览器实例
"""
import asyncio
import logging
from fingerBrowser import FingerBrowser
from browserControler import BrowserControler
from automationPlaywright.betinasian.operations.prepare_work import prepare_work

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    # 浏览器ID
    browser_id = "k18awkl7"

    # 初始化 ADS 浏览器
    logger.info("初始化 ADS 浏览器客户端...")
    finger_browser = FingerBrowser(browser_type="ads")

    try:
        # 判断浏览器是否已经启动
        logger.info(f"检查浏览器 {browser_id} 是否已经启动...")
        status = await finger_browser.judge_browser_working(browser_id)

        if status['is_working']:
            # 浏览器已经启动
            logger.info(f"✓ 浏览器已经在运行中")
            logger.info(f"  - 浏览器名称: {status.get('handler_name', 'N/A')}")
            logger.info(f"  - 调试端口: {status.get('debug_port', 'N/A')}")
            logger.info(f"  - WebSocket URL: {status.get('ws_url', 'N/A')}")
        else:
            # 浏览器未启动，需要启动
            logger.info(f"✗ 浏览器未运行，正在启动...")

            # 启动浏览器
            launch_result = await finger_browser.launch_browser(browser_id)

            if launch_result.get('success'):
                logger.info(f"✓ 浏览器启动成功")
                logger.info(f"  - 调试端口: {launch_result.get('debug_port', 'N/A')}")
                logger.info(f"  - WebSocket URL: {launch_result.get('ws_url', 'N/A')}")
            else:
                logger.error(f"✗ 浏览器启动失败: {launch_result.get('error', 'Unknown error')}")
                return

        # 再次检查浏览器状态
        logger.info("\n再次检查浏览器状态...")
        final_status = await finger_browser.judge_browser_working(browser_id)
        logger.info(f"最终状态: {'运行中' if final_status['is_working'] else '未运行'}")

        # 获取 CDP browser 对象
        if final_status['is_working']:
            logger.info("\n获取 CDP Browser 对象...")
            ws_url = final_status.get('ws_url', '')
            debug_port = final_status.get('debug_port', '')

            if ws_url:
                # 使用 WebSocket URL 连接
                logger.info(f"使用 WebSocket URL 连接: {ws_url}")
                playwright_browser = await finger_browser.get_cdp_object(
                    ws_url=ws_url,
                    tool="playwright",
                    model="ws_url"
                )
                logger.info(f"✓ 成功获取 Playwright Browser 对象: {playwright_browser}")

                # 使用 BrowserControler 管理页面
                logger.info("\n初始化浏览器控制器...")
                controller = BrowserControler(playwright_browser, tool="playwright")

                # 执行准备工作 (检查/打开页面 + 注入 Hook + 等待订阅)
                logger.info("\n开始执行准备工作...")
                result = await prepare_work(
                    controller=controller,
                    target_url="https://black.betinasia.com/sportsbook/basketball?group=in+running",
                    subscribe_sports=['basket']  # 只订阅篮球
                )

                if not result['success']:
                    logger.error(f"✗ 准备工作失败: {result['message']}")
                    return

                logger.info(f"✓ 准备工作完成!")
                target_page = result['page']

                # 进入死循环，保持程序运行
                logger.info("\n✓ 初始化完成，程序进入运行状态...")
                logger.info("按 Ctrl+C 停止程序\n")

                try:
                    while True:
                        # 每隔一段时间检查一次浏览器状态（可选）
                        await asyncio.sleep(60)  # 每60秒检查一次

                        # 可以在这里添加定期任务
                        # 例如：检查浏览器是否还在运行
                        # status_check = await finger_browser.judge_browser_working(browser_id)
                        # if not status_check['is_working']:
                        #     logger.warning("⚠ 浏览器已停止运行")
                        #     break

                except KeyboardInterrupt:
                    logger.info("\n接收到停止信号 (Ctrl+C)，正在退出...")

    except Exception as e:
        logger.error(f"发生错误: {e}", exc_info=True)
    finally:
        # 清理资源
        await finger_browser.close_session()
        logger.info("资源清理完成")


if __name__ == "__main__":
    asyncio.run(main())
