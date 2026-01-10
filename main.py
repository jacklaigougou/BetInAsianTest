"""
Main Entry - WebSocket 驱动的异步浏览器控制程序

使用方法:
    python main.py
"""
import asyncio
import logging
from application import Application
from configs.settings import Settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主入口函数"""
    logger.info("🚀 启动应用...")
    app = Application(Settings)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
