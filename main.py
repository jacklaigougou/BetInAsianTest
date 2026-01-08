# -*- coding: utf-8 -*-
"""
BetInAsian 主程序
使用 ADS 指纹浏览器启动和管理浏览器实例
"""
import asyncio
import logging
from fingerBrowser import FingerBrowser
from browserControler import BrowserControler
from automationPlaywright.automation import Automation
from utils.init_js_loader import initialize_js_loader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    # ========== 第0步: 初始化 JS 加载器 ==========
    logger.info("🔧 初始化 JS 加载器...")
    initialize_js_loader()

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
        else:
            # 浏览器未启动，需要启动
            logger.info(f"✗ 浏览器未运行，正在启动...")

            # 启动浏览器
            launch_result = await finger_browser.launch_browser(browser_id)

            if launch_result.get('success'):
                logger.info(f"✓ 浏览器启动成功")
            else:
                logger.error(f"✗ 浏览器启动失败: {launch_result.get('error', 'Unknown error')}")
                return

        # 再次检查浏览器状态
        
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

                # 初始化自动化操作类
                logger.info("\n初始化自动化操作...")
                automation = Automation(
                    platform="betinasian",
                    browser_controller=controller,
                    page=None  # page 会在 prepare_work 中获取
                )

                # 执行准备工作 (检查/打开页面 + 注入 Hook + 等待订阅)
                logger.info("\n开始执行准备工作...")
                result = await automation.prepare_work(
                    target_url="https://black.betinasia.com/sportsbook/basketball?group=in+running",
                    subscribe_sports=['basket']  # 只订阅篮球
                )

                if not result['success']:
                    logger.error(f"✗ 准备工作失败: {result['message']}")
                    return

                logger.info(f"✓ 准备工作完成!")
                target_page = result['page']

                # 更新 automation 的 page 对象 (需要同时更新包装类和内部实现类)
                automation.page = target_page
                automation._automation.page = target_page
                logger.info(f"✓ 已更新 automation.page: {target_page}")

               

                try:
                    basket_events = await target_page.evaluate('window.queryData.inRunningSport("basket")')

                    if basket_events:
                        logger.info(f"\n找到 {len(basket_events)} 场正在进行的篮球比赛")

                        # 找到测试比赛并检查盘口
                        test_event_key = None
                        for event in basket_events:
                            if 'Rilski' in event.get('home', '') or 'Balkan' in event.get('away', ''):
                                test_event_key = event.get('event_key')
                                logger.info(f"\n找到测试比赛:")
                                logger.info(f"  - Event Key: {test_event_key}")
                                logger.info(f"  - {event.get('home')} vs {event.get('away')}")
                                break

                        # 如果找到测试比赛，检查盘口数据
                        if test_event_key:
                            logger.info(f"\n检查盘口数据...")

                            # 查询所有盘口
                            all_markets = await target_page.evaluate(f'window.queryData.marketsByEvent("{test_event_key}")')
                            active_markets = await target_page.evaluate(f'window.queryData.activeMarketsByEvent("{test_event_key}")')

                            logger.info(f"  - 所有盘口: {len(all_markets) if all_markets else 0} 个")
                            logger.info(f"  - 活跃盘口: {len(active_markets) if active_markets else 0} 个")

                            # 检查原始数据存储
                            markets_data = await target_page.evaluate(f'''
                                Array.from(window.getMarketsData().values()).filter(m => m.event_key === "{test_event_key}")
                            ''')
                            logger.info(f"  - Markets Store 中的盘口: {len(markets_data) if markets_data else 0} 个")

                            # 检查是否已订阅
                            is_watched = await target_page.evaluate(f'window.isWatched("{test_event_key}")')
                            logger.info(f"  - 是否已订阅: {is_watched}")

                            # 如果没有盘口数据且未订阅，尝试订阅
                            if not markets_data and not is_watched:
                                logger.info(f"\n  ⚠️ 比赛未订阅，尝试手动订阅...")
                                await target_page.evaluate(f'window.__subscriptionManager.watch("{test_event_key}", "basket")')
                                await asyncio.sleep(3)

                                # 重新查询
                                markets_data = await target_page.evaluate(f'''
                                    Array.from(window.getMarketsData().values()).filter(m => m.event_key === "{test_event_key}")
                                ''')
                                logger.info(f"  - 订阅后盘口数: {len(markets_data) if markets_data else 0} 个")

                            if markets_data:
                                logger.info(f"\n  前3个盘口:")
                                for i, m in enumerate(markets_data[:3], 1):
                                    logger.info(f"    [{i}] {m.get('market_group')} - Active: {m.get('active')} - Odds: {m.get('odds')}")
                    else:
                        logger.warning("⚠ 未找到正在进行的篮球比赛")
                except Exception as e:
                    logger.error(f"查询篮球比赛失败: {e}")
                
                logger.info("="*60 + "\n")

                # ========== 测试 GetOdd 功能 ==========
                logger.info("\n" + "="*60)
                logger.info("🧪 测试 GetOdd 功能")
                logger.info("="*60)

                # 构造测试消息
                test_dispatch_message = {
                    'spider_sport_type': 'basket',
                    'spider_home': 'dubai',
                    'spider_away': 'fenerbahce',
                    'spider_market_id': '17',        # Asian Handicap - Home
                    'spider_handicap_value': -10    # 让分 -5.5
                }

                

                # 打印实际的 WebSocket 消息样本
                logger.info("\n📡 检查实际收到的 WebSocket 消息...")
                sample_messages = await automation.page.evaluate('window.__offersHandler.recentMessages.slice(-5)')

                if sample_messages and len(sample_messages) > 0:
                    logger.info(f"找到 {len(sample_messages)} 条 offers 消息")
                    logger.info(f"\n第一条消息的数据结构:")
                    import json
                    logger.info(json.dumps(sample_messages[0], indent=2, ensure_ascii=False))
                else:
                    logger.warning("⚠️ 未找到 offers 消息")

                # 调用 GetOdd
                logger.info("\n🔍 开始获取赔率...")
                odd_result = await automation.GetOdd(test_dispatch_message)

                # 显示结果
                logger.info("\n📊 GetOdd 结果:")
                if odd_result:
                    logger.info(f"  - 成功: {odd_result.get('success')}")

                    if odd_result.get('success'):
                        logger.info(f"\n  📌 基本信息:")
                        logger.info(f"    - Event ID: {odd_result.get('event_id')}")
                        logger.info(f"    - Event Key: {odd_result.get('event_key')}")
                        logger.info(f"    - Bet Type: {odd_result.get('bet_type')}")
                        logger.info(f"    - Betslip ID: {odd_result.get('betslip_id')}")

                        # Betslip 结果
                        betslip_result = odd_result.get('betslip_result', {})
                        logger.info(f"\n  📋 Betslip 创建结果:")
                        logger.info(f"    - 成功: {betslip_result.get('success')}")
                        logger.info(f"    - 状态码: {betslip_result.get('status')}")

                        # 最佳赔率信息 (新增)
                        best_price = odd_result.get('best_price', {})
                        logger.info(f"\n  💰 最佳赔率:")
                        if best_price.get('success'):
                            logger.info(f"    - Bookie: {best_price.get('bookie')}")
                            logger.info(f"    - Price: {best_price.get('price')}")
                            available = best_price.get('available')
                            if available:
                                logger.info(f"    - Available: {available.get('amount')} {available.get('currency')}")
                            else:
                                logger.info(f"    - Available: N/A")
                            logger.info(f"    - Updated At: {best_price.get('updated_at')}")
                        else:
                            logger.warning(f"    - 未找到可执行赔率: {best_price.get('reason')}")
                            if best_price.get('best_odds'):
                                logger.info(f"    - 最高赔率(不可执行): {best_price.get('best_odds')}")

                        # 匹配信息
                        match_info = odd_result.get('match_info', {})
                        logger.info(f"\n  🎯 匹配信息:")
                        logger.info(f"    - 匹配类型: {match_info.get('match_type')}")
                        logger.info(f"    - 匹配分数: {match_info.get('score')}")

                        # 显示完整的 event 信息
                        event = match_info.get('event', {})
                        logger.info(f"\n  🏀 Event 详情:")
                        logger.info(f"    - 主队: {event.get('home')}")
                        logger.info(f"    - 客队: {event.get('away')}")
                        logger.info(f"    - 联赛: {event.get('competition_name')}")
                        logger.info(f"    - 运动: {event.get('sport')}")
                        logger.info(f"    - 是否进行中: {event.get('isInRunning')}")
                    else:
                        logger.error(f"  ❌ 错误信息: {odd_result.get('message')}")
                else:
                    logger.warning("  ⚠️ GetOdd 返回 None，跳过结果显示")

                logger.info("\n" + "="*60)
                logger.info("🧪 GetOdd 测试完成")
                logger.info("="*60 + "\n")



                return
                # ========== 测试 CreateBetslip 功能 ==========
                # 不依赖 GetOdd 结果，直接测试
                logger.info("\n" + "="*60)
                logger.info("🧪 测试 CreateBetslip 功能")
                logger.info("="*60)

                # 测试使用简单的 Money Line 投注
                from automationPlaywright.betinasian.jsCodeExcutors.http_executors import create_betslip

                # 测试数据: 简单的 Money Line 投注
                logger.info("\n📋 测试数据:")
                event_id = "2026-01-07,96326,41086"
                bet_type = "for,ml,a"  # ✅ 修正：使用正确的 bet_type（与 PMM 匹配）
                logger.info(f"  - Event ID: {event_id}")
                logger.info(f"  - Bet Type: {bet_type} (Away)")
                logger.info(f"  - Sport: basket")

                betslip_result = None  # 初始化变量

                try:
                    betslip_result = await create_betslip(
                        page=target_page,
                        sport="basket",
                        event_id=event_id,
                        bet_type=bet_type
                    )

                    # 显示结果
                    logger.info("\n📊 CreateBetslip 结果:")
                    logger.info(f"  - 成功: {betslip_result.get('success')}")
                    logger.info(f"  - 状态码: {betslip_result.get('status')}")

                    if betslip_result.get('success'):
                        logger.info(f"  - 响应数据:")
                        import json
                        logger.info(json.dumps(betslip_result.get('data'), indent=4, ensure_ascii=False))
                    else:
                        logger.error(f"  - 错误: {betslip_result.get('error')}")

                except Exception as e:
                    logger.error(f"❌ CreateBetslip 测试失败: {e}", exc_info=True)
                    betslip_result = {'success': False}

                logger.info("\n" + "="*60)
                logger.info("🧪 CreateBetslip 测试完成")
                logger.info("="*60 + "\n")

                # ========== 测试 GetPrice 功能 ==========
                if betslip_result and betslip_result.get('success'):
                    logger.info("\n" + "="*60)
                    logger.info("🧪 测试 GetPrice 功能")
                    logger.info("="*60)

                    from automationPlaywright.betinasian.jsCodeExcutors.queries.pmm import get_price_by_betslip_id, get_pmm_stats

                    # 检查 PMM 模块是否加载
                    logger.info("\n🔍 检查 PMM 模块...")
                    pmm_check = await target_page.evaluate("""
                        () => {
                            return {
                                pmmStore: typeof window.pmmStore !== 'undefined',
                                pmmHandler: typeof window.__pmmHandler !== 'undefined',
                                queryBetslipById: typeof window.queryData?.queryBetslipById === 'function',
                                getTotalAmountAtPrice: typeof window.queryData?.getTotalAmountAtPrice === 'function'
                            };
                        }
                    """)
                    logger.info(f"PMM 模块状态: {json.dumps(pmm_check, indent=2)}")

                    if not pmm_check.get('pmmStore'):
                        logger.error("❌ PMM Store 未加载！请检查 JS 文件是否正确注入。")
                        logger.info("提示：PMM 模块文件应该在 jsCode/wsDataRegistor/core/ 目录下")

                    # 提取 betslip_id (字段名是 betslip_id 不是 id)
                    # Debug: 打印完整结构
                    logger.info(f"\n🔍 调试 betslip_result 结构:")
                    logger.info(f"  - betslip_result keys: {list(betslip_result.keys())}")
                    logger.info(f"  - betslip_result['data'] keys: {list(betslip_result.get('data', {}).keys())}")
                    logger.info(f"  - betslip_result['data']['data'] exists: {'data' in betslip_result.get('data', {})}")

                    # 尝试两种可能的路径
                    betslip_id = betslip_result.get('data', {}).get('betslip_id')
                    if not betslip_id:
                        # 可能有嵌套的 data 字段
                        betslip_id = betslip_result.get('data', {}).get('data', {}).get('betslip_id')

                    if not betslip_id:
                        logger.error("❌ 无法获取 betslip_id，跳过 GetPrice 测试")
                        logger.error(f"betslip_result: {json.dumps(betslip_result, indent=2, ensure_ascii=False)}")
                    else:
                        logger.info(f"\n✅ Betslip ID: {betslip_id}")

                        # 等待 PMM 数据到达
                        logger.info("\n⏳ 等待 PMM 数据...")
                        await asyncio.sleep(3)

                        # 查看 PMM 统计
                        logger.info("\n📊 PMM 统计信息:")
                        stats = await get_pmm_stats(target_page)
                        logger.info(json.dumps(stats, indent=2))

                        # 先查看原始 PMM 数据
                        logger.info(f"\n🔍 查看原始 PMM 数据...")

                        # 1. 查看 Store 中的原始数据
                        raw_store_data = await target_page.evaluate(
                            f'''
                            () => {{
                                const betslip = window.pmmStore.store.get("{betslip_id}");
                                if (!betslip) return null;

                                // Convert Map to Object for JSON serialization
                                const bookiesObj = {{}};
                                for (const [key, value] of betslip.bookies) {{
                                    bookiesObj[key] = value;
                                }}

                                return {{
                                    ...betslip,
                                    bookies: bookiesObj
                                }};
                            }}
                            '''
                        )

                        if raw_store_data:
                            logger.info(f"✅ Store 中的 betslip 数据:")
                            logger.info(f"  - Event ID: {raw_store_data.get('event_id')}")
                            logger.info(f"  - Bet Type: {raw_store_data.get('bet_type')}")
                            logger.info(f"  - Bookies count: {len(raw_store_data.get('bookies', {}))}")
                            logger.info(f"  - Bookies keys: {list(raw_store_data.get('bookies', {}).keys())}")

                            # 显示每个 bookie 的详细信息
                            for bookie, data in raw_store_data.get('bookies', {}).items():
                                logger.info(f"\n  [{bookie}]:")
                                logger.info(f"    - Status: {data.get('status')}")
                                logger.info(f"    - Top price: {data.get('top_price')}")
                                logger.info(f"    - Top available: {data.get('top_available')}")
                                logger.info(f"    - Price Tiers: {len(data.get('price_tiers', []))} tiers")
                                for i, tier in enumerate(data.get('price_tiers', [])[:3]):
                                    logger.info(f"      Tier {i+1}: price={tier.get('price')}, min={tier.get('min')}, max={tier.get('max')}")
                        else:
                            logger.error("❌ Store 中未找到 betslip 数据!")

                        # 获取最优价格 (使用 betslip_id 查询)
                        logger.info(f"\n🔍 获取最优价格 (by betslip_id)...")
                        logger.info(f"  - Betslip ID: {betslip_id}")

                        try:
                            price_result = await get_price_by_betslip_id(
                                page=target_page,
                                betslip_id=betslip_id,
                                required_amount=10.0,
                                required_currency="GBP"
                            )

                            # 显示结果
                            logger.info("\n📊 GetPrice 结果:")
                            logger.info(f"  - 成功: {price_result.get('success')}")

                            if price_result.get('success'):
                                logger.info(f"  - Betslip ID: {price_result.get('betslip_id')}")
                                logger.info(f"  - Event ID: {price_result.get('event_id')}")
                                logger.info(f"  - Bet Type: {price_result.get('bet_type')}")
                                logger.info(f"  - Bookie: {price_result.get('bookie')}")
                                logger.info(f"  - Price: {price_result.get('price')}")
                                logger.info(f"  - Available: {price_result.get('available')}")
                                logger.info(f"  - Updated At: {price_result.get('updated_at')}")
                                logger.info(f"  - Total Bookies: {price_result.get('all_bookies')}")
                            else:
                                logger.warning(f"  - Reason: {price_result.get('reason')}")

                        except Exception as e:
                            logger.error(f"❌ GetPrice 测试失败: {e}", exc_info=True)

                        # ========== 测试 PlaceOrder 功能 ==========
                        if price_result and price_result.get('success'):
                            logger.info("\n" + "="*60)
                            logger.info("🧪 测试 PlaceOrder 功能")
                            logger.info("="*60)

                            from automationPlaywright.betinasian.jsCodeExcutors.http_executors import place_order

                            # 直接从 Store 获取最高价格 (不过滤 required_amount)
                            highest_price_data = await target_page.evaluate(
                                f'''
                                () => {{
                                    const betslip = window.pmmStore.store.get("{betslip_id}");
                                    if (!betslip) return null;

                                    let highestPrice = 0;
                                    let highestBookie = null;

                                    for (const [bookie, data] of betslip.bookies) {{
                                        if (data.status.code === 'success' && data.top_price > highestPrice) {{
                                            highestPrice = data.top_price;
                                            highestBookie = bookie;
                                        }}
                                    }}

                                    return {{
                                        price: highestPrice,
                                        bookie: highestBookie
                                    }};
                                }}
                                '''
                            )

                            best_price = highest_price_data.get('price') if highest_price_data else None
                            best_bookie = highest_price_data.get('bookie') if highest_price_data else None

                            if not best_price:
                                logger.error("❌ 无法获取最高价格,跳过下单")
                            else:
                                logger.info(f"\n📋 下单参数:")
                                logger.info(f"  - Betslip ID: {betslip_id}")
                                logger.info(f"  - Price: {best_price} (来自 {best_bookie} 的最高价格)")
                                logger.info(f"  - Stake: 2 USD")
                                logger.info(f"  - Duration: 30 seconds")

                                try:
                                    order_result = await place_order(
                                        page=target_page,
                                        betslip_id=betslip_id,
                                        price=best_price,
                                        stake=2,
                                        currency="USD",
                                        duration=30
                                    )

                                    # 显示结果
                                    logger.info("\n📊 PlaceOrder 结果:")
                                    logger.info(f"  - 成功: {order_result.get('success')}")
                                    logger.info(f"  - 状态码: {order_result.get('status')}")

                                    if order_result.get('success'):
                                        logger.info(f"  - 响应数据:")
                                        logger.info(json.dumps(order_result.get('data'), indent=4, ensure_ascii=False))
                                    else:
                                        logger.error(f"  - 错误: {order_result.get('error')}")

                                except Exception as e:
                                    logger.error(f"❌ PlaceOrder 测试失败: {e}", exc_info=True)

                                # ========== 测试 GetOrder 功能 (查询下单结果) ==========
                                if order_result.get('success') and order_result.get('data'):
                                    logger.info("\n" + "="*60)
                                    logger.info("🧪 测试 GetOrder 功能 - 查询下单结果")
                                    logger.info("="*60)

                                    from automationPlaywright.betinasian.jsCodeExcutors.queries.orders.get_order import (
                                        get_order_by_id,
                                        get_order_with_bets,
                                        check_order_slippage
                                    )

                                    # 从下单响应中提取 order_id (可能是数字或字符串)
                                    order_id = order_result['data']['data'].get('order_id')

                                    if not order_id:
                                        logger.error("❌ 无法从响应中提取 order_id")
                                    else:
                                        # 转换为字符串
                                        order_id_str = str(order_id)
                                        logger.info(f"\n📋 订单ID: {order_id_str}")

                                        # 🔍 调试: 检查 Adapter 和 Store 状态
                                        debug_info = await target_page.evaluate("""
                                            () => {
                                                return {
                                                    adapter_loaded: !!window.orderAdapter,
                                                    store_loaded: !!window.orderStore,
                                                    handler_loaded: !!window.__orderHandler,
                                                    store_size: window.orderStore ? window.orderStore.store.size : 0,
                                                    handler_stats: window.__orderHandler ? window.__orderHandler.getStats() : null
                                                };
                                            }
                                        """)
                                        logger.info(f"🔍 Debug Info:")
                                        logger.info(f"  - Adapter Loaded: {debug_info.get('adapter_loaded')}")
                                        logger.info(f"  - Store Loaded: {debug_info.get('store_loaded')}")
                                        logger.info(f"  - Handler Loaded: {debug_info.get('handler_loaded')}")
                                        logger.info(f"  - Store Size: {debug_info.get('store_size')}")
                                        logger.info(f"  - Handler Stats: {debug_info.get('handler_stats')}")

                                        # 🔍 等待2秒后再次检查 Store
                                        await asyncio.sleep(2)

                                        store_check = await target_page.evaluate(f"""
                                            () => {{
                                                const orderId = "{order_id_str}";

                                                // 检查 Store 中是否有这个订单
                                                const hasOrder = window.orderStore && window.orderStore.store.has(orderId);

                                                // 获取所有订单ID (限制前10个)
                                                let allOrderIds = [];
                                                if (window.orderStore) {{
                                                    allOrderIds = Array.from(window.orderStore.store.keys()).slice(0, 10);
                                                }}

                                                return {{
                                                    has_order: hasOrder,
                                                    current_store_size: window.orderStore ? window.orderStore.store.size : 0,
                                                    all_order_ids: allOrderIds,
                                                    looking_for: orderId
                                                }};
                                            }}
                                        """)

                                        logger.info(f"\n🔍 Store Check (2秒后):")
                                        logger.info(f"  - Looking for: {store_check.get('looking_for')}")
                                        logger.info(f"  - Has Order: {store_check.get('has_order')}")
                                        logger.info(f"  - Store Size: {store_check.get('current_store_size')}")
                                        logger.info(f"  - All Order IDs: {store_check.get('all_order_ids')}")

                                        # 🔍 检查 API Handler 和 Router 是否有新代码
                                        code_check = await target_page.evaluate("""
                                            () => {
                                                // 检查 API Handler
                                                const handlerSource = window.__apiHandler?.handle?.toString() || '';
                                                const hasNestedMessageDetection = handlerSource.includes('检测到嵌套消息');

                                                // 检查 Message Router
                                                const routerSource = window.__messageRouter?.route?.toString() || '';
                                                const hasApiSpecialHandling = routerSource.includes('特殊处理: API 消息');

                                                // 检查 Bet Adapter (ID 类型转换)
                                                const betAdapterSource = window.betAdapter?.normalizeBetData?.toString() || '';
                                                const hasBetIdConversion = betAdapterSource.includes('Convert IDs to strings');

                                                // 检查 Router 统计
                                                const routerStats = window.__messageRouter?.getStats() || {};

                                                return {
                                                    api_handler_exists: !!window.__apiHandler,
                                                    api_handler_new_code: hasNestedMessageDetection,
                                                    router_exists: !!window.__messageRouter,
                                                    router_new_code: hasApiSpecialHandling,
                                                    bet_adapter_exists: !!window.betAdapter,
                                                    bet_adapter_new_code: hasBetIdConversion,
                                                    router_stats: routerStats
                                                };
                                            }
                                        """)

                                        logger.info(f"\n🔍 代码版本检查:")
                                        logger.info(f"  - API Handler: {code_check.get('api_handler_new_code')}")
                                        logger.info(f"  - Router: {code_check.get('router_new_code')}")
                                        logger.info(f"  - Bet Adapter: {code_check.get('bet_adapter_new_code')}")
                                        logger.info(f"  - Router Stats: {code_check.get('router_stats')}")

                                        needs_reload = (not code_check.get('api_handler_new_code') or
                                                       not code_check.get('router_new_code') or
                                                       not code_check.get('bet_adapter_new_code'))

                                        if needs_reload:
                                            logger.error("❌ 检测到旧代码！正在重新加载...")

                                            # 重新加载所有 Handler、Router 和 Adapter
                                            from automationPlaywright.betinasian.jsCodeExcutors.inject_hook import load_js_file

                                            files_to_reload = [
                                                'wsDataRegistor/message_router.js',
                                                'wsDataRegistor/handlers/api_handler.js',
                                                'wsDataRegistor/handlers/order_handler.js',
                                                'wsDataRegistor/handlers/bet_handler.js',
                                                'wsDataRegistor/core/bet_adapter.js',  # 添加 Bet Adapter
                                                'wsDataRegistor/core/order_adapter.js'  # 添加 Order Adapter
                                            ]

                                            for file_path in files_to_reload:
                                                file_code = load_js_file(file_path, 'betinasian')
                                                if file_code:
                                                    await target_page.evaluate(file_code)
                                                    logger.info(f"  ✅ 重新加载: {file_path}")

                                            # 再次检查所有组件
                                            recheck = await target_page.evaluate("""
                                                () => {
                                                    const apiHandlerOk = window.__apiHandler?.handle?.toString().includes('检测到嵌套消息');
                                                    const routerOk = window.__messageRouter?.route?.toString().includes('特殊处理: API 消息');
                                                    const betAdapterOk = window.betAdapter?.normalizeBetData?.toString().includes('Convert IDs to strings');
                                                    return { apiHandlerOk, routerOk, betAdapterOk };
                                                }
                                            """)
                                            logger.info(f"  🔍 重新检查: API Handler={recheck.get('apiHandlerOk')}, Router={recheck.get('routerOk')}, Bet Adapter={recheck.get('betAdapterOk')}")
                                        else:
                                            logger.info("  ✅ 所有组件已是最新代码")

                                        # 获取 duration (从下单参数获取，默认30秒)
                                        duration = 30
                                        timeout = duration + 5  # duration + 5秒缓冲

                                        logger.info(f"\n⏳ 开始监控订单状态 (最长 {timeout} 秒)...")

                                        import time
                                        start_time = time.time()
                                        found_order = False

                                        try:
                                            # 轮询查询订单状态
                                            while time.time() - start_time < timeout:
                                                elapsed = int(time.time() - start_time)
                                                logger.info(f"\n[{elapsed}s] 查询订单状态...")

                                                order = await get_order_by_id(target_page, order_id_str)

                                                if order:
                                                    found_order = True
                                                    state = order.get('state')
                                                    bet_bar = order.get('bet_bar', {})

                                                    logger.info(f"  ✅ 找到订单 - State: {state}")
                                                    logger.info(f"     Bet Bar: success={bet_bar.get('success', 0)}, "
                                                              f"inprogress={bet_bar.get('inprogress', 0)}, "
                                                              f"danger={bet_bar.get('danger', 0)}, "
                                                              f"unplaced={bet_bar.get('unplaced', 0)}")

                                                    # 检查是否完成
                                                    if state in ['FINISHED', 'EXPIRED_LOCAL']:
                                                        logger.info(f"\n{'✅' if state == 'FINISHED' else '⏱️'} 订单已结束: {state}")
                                                        break
                                                else:
                                                    logger.info("  ⏳ 订单还未进入 Store，继续等待...")

                                                # 等待1秒后继续轮询
                                                await asyncio.sleep(1)

                                            # 轮询结束后显示最终结果
                                            if found_order and order:
                                                logger.info(f"\n" + "="*60)
                                                logger.info("📊 最终订单状态:")
                                                logger.info("="*60)
                                                logger.info(f"  - Order ID: {order.get('order_id')}")
                                                logger.info(f"  - State: {order.get('state')}")
                                                logger.info(f"  - Raw Status: {order.get('raw_status')}")
                                                logger.info(f"  - Event ID: {order.get('event_id')}")
                                                logger.info(f"  - Betslip ID: {order.get('betslip_id')}")

                                                # 显示 bet_bar
                                                bet_bar = order.get('bet_bar', {})
                                                logger.info(f"\n  📊 Bet Bar:")
                                                logger.info(f"    - Success: {bet_bar.get('success', 0)}")
                                                logger.info(f"    - In Progress: {bet_bar.get('inprogress', 0)}")
                                                logger.info(f"    - Danger: {bet_bar.get('danger', 0)}")
                                                logger.info(f"    - Unplaced: {bet_bar.get('unplaced', 0)}")

                                                # 显示状态机摘要
                                                state_summary = order.get('state_summary', {})
                                                if state_summary:
                                                    logger.info(f"\n  🔄 State Summary:")
                                                    logger.info(f"    - Current State: {state_summary.get('state')}")
                                                    logger.info(f"    - Is Done: {state_summary.get('isDone')}")
                                                    logger.info(f"    - Next State: {state_summary.get('nextState')}")

                                                # 先检查 Bet Store 和 Handler 状态
                                                logger.info("\n🔍 检查 Bet Store 状态...")
                                                bet_info = await target_page.evaluate("""
                                                    (order_id) => {
                                                        // Bet Store 信息
                                                        const bet_store_exists = !!window.betStore;
                                                        const bet_store_size = window.betStore ? window.betStore.store.size : 0;
                                                        const bet_handler_exists = !!window.__betHandler;
                                                        const bet_handler_stats = window.__betHandler ? window.__betHandler.getStats() : null;

                                                        // 直接检查索引
                                                        let byOrder_index = null;
                                                        if (window.betStore && window.betStore.indexes.byOrder) {
                                                            const orderBets = window.betStore.indexes.byOrder.get(order_id);
                                                            byOrder_index = orderBets ? Array.from(orderBets) : null;
                                                        }

                                                        // 检查 Store 中所有 bet
                                                        let all_bets = [];
                                                        if (window.betStore && window.betStore.store) {
                                                            all_bets = Array.from(window.betStore.store.entries()).map(([bet_id, bet]) => ({
                                                                bet_id: bet_id,
                                                                order_id: bet.order_id,
                                                                bookie: bet.bookie,
                                                                status: bet.status
                                                            }));
                                                        }

                                                        // 测试 getBetsByOrder
                                                        let getBetsByOrder_result = null;
                                                        if (window.betStore && window.betStore.getBetsByOrder) {
                                                            getBetsByOrder_result = window.betStore.getBetsByOrder(order_id);
                                                        }

                                                        // Order 内部数组
                                                        const order_arrays = window.orderStore ?
                                                            Array.from(window.orderStore.store.values()).map(o => ({
                                                                order_id: o.order_id,
                                                                success: o.success,
                                                                inprogress: o.inprogress,
                                                                danger: o.danger,
                                                                unplaced: o.unplaced
                                                            })) : [];

                                                        return {
                                                            bet_store_exists,
                                                            bet_store_size,
                                                            bet_handler_exists,
                                                            bet_handler_stats,
                                                            byOrder_index,
                                                            all_bets,
                                                            getBetsByOrder_result,
                                                            order_arrays
                                                        };
                                                    }
                                                """, order_id_str)

                                                logger.info(f"  - Bet Store Exists: {bet_info.get('bet_store_exists')}")
                                                logger.info(f"  - Bet Store Size: {bet_info.get('bet_store_size')}")
                                                logger.info(f"  - Bet Handler Exists: {bet_info.get('bet_handler_exists')}")
                                                logger.info(f"  - Bet Handler Stats: {bet_info.get('bet_handler_stats')}")

                                                # 显示索引检查
                                                byOrder_index = bet_info.get('byOrder_index')
                                                logger.info(f"\n  🔍 Bet Store byOrder Index:")
                                                logger.info(f"    - Order {order_id_str} 的索引: {byOrder_index}")

                                                # 显示所有 Bet
                                                all_bets = bet_info.get('all_bets', [])
                                                if all_bets:
                                                    logger.info(f"\n  📊 Bet Store 中所有 Bet ({len(all_bets)} 个):")
                                                    for bet in all_bets:
                                                        logger.info(f"    - Bet {bet.get('bet_id')}: order_id={bet.get('order_id')}, bookie={bet.get('bookie')}, status={bet.get('status')}")

                                                # 显示 getBetsByOrder 结果
                                                getBetsByOrder_result = bet_info.get('getBetsByOrder_result')
                                                logger.info(f"\n  🔍 getBetsByOrder('{order_id_str}') 返回: {len(getBetsByOrder_result) if getBetsByOrder_result else 0} 个 bet")

                                                # 显示 Order 内部的 bet 数组
                                                order_arrays = bet_info.get('order_arrays', [])
                                                if order_arrays:
                                                    logger.info(f"\n  📊 Order 内部的 Bet 数组:")
                                                    for o in order_arrays:
                                                        logger.info(f"    Order {o.get('order_id')}:")
                                                        logger.info(f"      - success: {o.get('success')}")
                                                        logger.info(f"      - inprogress: {o.get('inprogress')}")
                                                        logger.info(f"      - danger: {o.get('danger')}")
                                                        logger.info(f"      - unplaced: {o.get('unplaced')}")

                                                # 查询所有 bets
                                                logger.info("\n📊 查询所有 Bets...")
                                                result_with_bets = await get_order_with_bets(target_page, order_id_str)

                                                if result_with_bets:
                                                    bets = result_with_bets.get('bets', [])
                                                    logger.info(f"\n  ✅ 找到 {len(bets)} 个 Bet:")

                                                    for i, bet in enumerate(bets, 1):
                                                        logger.info(f"\n  Bet #{i}:")
                                                        logger.info(f"    - Bet ID: {bet.get('bet_id')}")
                                                        logger.info(f"    - Bookie: {bet.get('bookie')}")
                                                        logger.info(f"    - Status: {bet.get('status')}")
                                                        logger.info(f"    - Price: {bet.get('price')}")
                                                        logger.info(f"    - Stake: {bet.get('stake')}")
                                                        logger.info(f"    - Matched Price: {bet.get('matched_price')}")
                                                        logger.info(f"    - Matched Stake: {bet.get('matched_stake')}")
                                                        logger.info(f"    - Unmatched Stake: {bet.get('unmatched_stake')}")

                                                # 检查滑点
                                                logger.info("\n📊 检查价格滑点...")
                                                slippage = await check_order_slippage(target_page, order_id_str)

                                                if slippage:
                                                    logger.info(f"\n  ✅ 滑点分析:")
                                                    logger.info(f"    - Total Slippage: {slippage.get('total_slippage')}")
                                                    logger.info(f"    - Avg Slippage: {slippage.get('avg_slippage')}")
                                                    logger.info(f"    - Avg Slippage %: {slippage.get('avg_slippage_pct')}")
                                                    logger.info(f"    - Bet Count: {slippage.get('bet_count')}")

                                                    for bet_slip in slippage.get('bets', []):
                                                        logger.info(f"\n    Bet {bet_slip.get('bet_id')} ({bet_slip.get('bookie')}):")
                                                        logger.info(f"      - Requested: {bet_slip.get('requested_price')}")
                                                        logger.info(f"      - Matched: {bet_slip.get('matched_price')}")
                                                        logger.info(f"      - Slippage: {bet_slip.get('slippage_pct')}")
                                                else:
                                                    logger.info("  ⚠️ 无滑点数据 (可能还没有matched的bet)")
                                            else:
                                                logger.warning(f"\n⚠️ 超时 ({timeout}秒) - 订单未找到或未进入 Store")

                                        except Exception as e:
                                            logger.error(f"❌ GetOrder 测试失败: {e}", exc_info=True)

                                        logger.info("\n" + "="*60)
                                        logger.info("🧪 GetOrder 测试完成")
                                        logger.info("="*60 + "\n")

                            logger.info("\n" + "="*60)
                            logger.info("🧪 PlaceOrder 测试完成")
                            logger.info("="*60 + "\n")

                        # ========== 测试按赔率查询总金额功能 ==========
                        logger.info("\n" + "="*60)
                        logger.info("🧪 测试按赔率查询总金额功能")
                        logger.info("="*60)

                        from automationPlaywright.betinasian.jsCodeExcutors.queries.pmm import get_total_amount_at_price

                        # 测试目标赔率 (根据实际价格范围)
                        target_prices = [1.2, 1.15, 1.1,1.0]

                        for target_price in target_prices:
                            logger.info(f"\n🎯 查询赔率 >= {target_price} 的总金额...")

                            try:
                                amount_result = await get_total_amount_at_price(
                                    page=target_page,
                                    event_id=event_id,
                                    bet_type=bet_type,
                                    target_price=target_price,
                                    required_currency="GBP"
                                )

                                if amount_result.get('success'):
                                    logger.info(f"✅ 找到可下单金额:")
                                    logger.info(f"  - 目标赔率: >= {amount_result.get('target_price')}")
                                    logger.info(f"  - 总金额: {amount_result.get('total_amount')} {amount_result.get('currency')}")
                                    logger.info(f"  - Bookie 数量: {amount_result.get('bookie_count')}")

                                    logger.info(f"\n  📋 各 Bookie 明细:")
                                    for bookie_data in amount_result.get('bookies', []):
                                        logger.info(f"\n  [{bookie_data.get('bookie')}]:")
                                        logger.info(f"    - 小计: {bookie_data.get('total_amount')} {bookie_data.get('currency')}")
                                        logger.info(f"    - 价格层级:")
                                        for tier in bookie_data.get('tiers', []):
                                            logger.info(f"      · 赔率 {tier['price']}: {tier['amount']} (最小: {tier['min']})")
                                else:
                                    logger.warning(f"⚠️ 未找到符合条件的金额: {amount_result.get('reason')}")

                            except Exception as e:
                                logger.error(f"❌ 查询失败: {e}", exc_info=True)

                        logger.info("\n" + "="*60)
                        logger.info("🧪 GetPrice 测试完成")
                        logger.info("="*60 + "\n")

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
