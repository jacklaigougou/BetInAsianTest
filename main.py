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

                # ========== 先查看正在进行的篮球比赛 ==========
                logger.info("\n" + "="*60)
                logger.info("🏀 查看正在进行的篮球比赛")
                logger.info("="*60)

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
                    'spider_home': 'fenerbahce sk',
                    'spider_away': 'olympiacos piraeus bc'
                }

                logger.info(f"📋 测试数据:")
                logger.info(f"  - 运动类型: {test_dispatch_message['spider_sport_type']}")
                logger.info(f"  - 主队: {test_dispatch_message['spider_home']}")
                logger.info(f"  - 客队: {test_dispatch_message['spider_away']}")

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
                        logger.info(f"  - Event Key: {odd_result.get('event_key')}")
                        logger.info(f"  - 赔率: {odd_result.get('odd')}")
                        logger.info(f"  - 盘口总数: {odd_result.get('total_markets')}")
                        logger.info(f"  - 匹配类型: {odd_result.get('match_info', {}).get('match_type')}")
                        logger.info(f"  - 匹配分数: {odd_result.get('match_info', {}).get('score')}")

                        # 显示完整的 event 信息
                        event = odd_result.get('match_info', {}).get('event', {})
                        logger.info(f"\n  - Event 详情:")
                        logger.info(f"    · 主队: {event.get('home')}")
                        logger.info(f"    · 客队: {event.get('away')}")
                        logger.info(f"    · 联赛: {event.get('competition_name')}")
                        logger.info(f"    · 运动: {event.get('sport')}")
                        logger.info(f"    · 是否进行中: {event.get('isInRunning')}")
                    else:
                        logger.error(f"  - 错误信息: {odd_result.get('message')}")
                else:
                    logger.warning("  - GetOdd 返回 None，跳过结果显示")

                logger.info("\n" + "="*60)
                logger.info("🧪 GetOdd 测试完成")
                logger.info("="*60 + "\n")

                # ========== 测试 CreateBetslip 功能 ==========
                # 不依赖 GetOdd 结果，直接测试
                logger.info("\n" + "="*60)
                logger.info("🧪 测试 CreateBetslip 功能")
                logger.info("="*60)

                # 测试使用简单的 Money Line 投注
                from automationPlaywright.betinasian.operations.CreateBetslip import create_betslip

                # 测试数据: 简单的 Money Line 投注
                logger.info("\n📋 测试数据:")
                event_id = "2026-01-07,35064,64397"
                bet_type = "for,a"  # ✅ 修正：使用正确的 bet_type（与 PMM 匹配）
                logger.info(f"  - Event ID: {event_id}")
                logger.info(f"  - Bet Type: {bet_type} (Away)")
                logger.info(f"  - Sport: fb")

                betslip_result = None  # 初始化变量

                try:
                    betslip_result = await create_betslip(
                        page=target_page,
                        sport="fb",
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

                    from automationPlaywright.betinasian.operations.GetPrice import get_price_by_betslip_id, get_pmm_stats

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

                        # ========== 测试按赔率查询总金额功能 ==========
                        logger.info("\n" + "="*60)
                        logger.info("🧪 测试按赔率查询总金额功能")
                        logger.info("="*60)

                        from automationPlaywright.betinasian.operations.GetPrice import get_total_amount_at_price

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
