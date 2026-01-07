# -*- coding: utf-8 -*-
"""
CDP 双向通信示例

展示浏览器如何主动向 Python 程序发送消息
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def main():
    """演示双向通信"""

    async with async_playwright() as p:
        # 连接到已存在的浏览器
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].pages[0]

        print("✅ 已连接到浏览器")

        # ==================== 方法 1: expose_function ====================
        print("\n📌 方法 1: 使用 expose_function()")

        # Python 端定义处理函数
        async def handle_pmm_update(data):
            """处理 PMM 更新"""
            print(f"\n🔔 收到 PMM 更新:")
            print(f"  Betslip ID: {data.get('betslip_id')}")
            print(f"  Bookie: {data.get('bookie')}")
            print(f"  Price: {data.get('price')}")
            return {"status": "received"}  # 可以返回数据给浏览器

        # 暴露给浏览器
        await page.expose_function("onPmmUpdate", handle_pmm_update)

        # 在浏览器中注入监听代码
        await page.evaluate("""
            () => {
                // 监听 PMM Store 变化
                if (window.pmmStore) {
                    const originalStore = window.pmmStore.storePMM;
                    window.pmmStore.storePMM = function(pmmData) {
                        // 调用原始函数
                        const result = originalStore.call(this, pmmData);

                        // 通知 Python
                        window.onPmmUpdate({
                            betslip_id: pmmData.betslip_id,
                            bookie: pmmData.bookie,
                            price: pmmData.price_list?.[0]?.effective?.price,
                            timestamp: Date.now()
                        });

                        return result;
                    };
                    console.log('[Demo] PMM 监听已启用');
                }
            }
        """)

        # ==================== 方法 2: console 监听 ====================
        print("\n📌 方法 2: 监听 console 消息")

        def handle_console(msg):
            """处理 console 消息"""
            text = msg.text
            if "[PMM]" in text or "[PlaceOrder]" in text:
                print(f"📄 Console: {text}")

        page.on("console", handle_console)

        # ==================== 方法 3: 定时轮询 ====================
        print("\n📌 方法 3: 定时轮询数据")

        async def poll_pmm_stats():
            """定时获取 PMM 统计"""
            while True:
                try:
                    stats = await page.evaluate("""
                        () => {
                            if (!window.pmmStore) return null;
                            return window.pmmStore.getStats();
                        }
                    """)

                    if stats:
                        print(f"\n📊 PMM 统计: {stats.get('total_betslips')} betslips, {stats.get('total_bookies')} bookies")

                except Exception as e:
                    print(f"❌ 轮询错误: {e}")

                await asyncio.sleep(5)  # 每5秒查询一次

        # 启动轮询任务
        poll_task = asyncio.create_task(poll_pmm_stats())

        print("\n✅ 监听已启动,等待浏览器消息...")
        print("按 Ctrl+C 停止\n")

        try:
            # 保持运行
            await asyncio.sleep(3600)
        except KeyboardInterrupt:
            print("\n停止监听...")
            poll_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
