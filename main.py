"""
Main Entry - WebSocket 驱动的异步浏览器控制程序

使用方法:
    python main.py
"""
import asyncio
from application import Application
from configs.settings import Settings


async def main():
    """主入口函数"""
    app = Application(Settings)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
