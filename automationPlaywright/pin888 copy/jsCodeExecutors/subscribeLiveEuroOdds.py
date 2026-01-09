"""
PIN888 平台 - LIVE_EURO_ODDS 订阅相关的 JS 代码执行器
"""

import asyncio
from src.utils import load_js_file
import time

async def subscribe_live_euro_odds(page, sport_id, period_num):
    """
    发送 LIVE_EURO_ODDS 订阅请求
    如果当前状态是 EVENTS_DETAIL_EURO,先取消订阅
    自动从 cookies 获取 dpMs1

    Args:
        page: Playwright Page 对象
        sport_id: 运动类型ID (29=足球, 4=篮球)
        period_num: 时段参数

    Returns:
        bool: 发送成功返回 True
    """
    try:
        # 打印调试信息
        print(f"🔍 [DEBUG] subscribe_live_euro_odds 参数:")
        # print(f"  sport_id: {sport_id} (type: {type(sport_id)})")
        # print(f"  period_num: {period_num} (type: {type(period_num)})")

        # 处理 None 值
        if sport_id is None:
            print(f"⚠️ [PIN888] sport_id 为 None,使用默认值 '29' (足球)")
            sport_id = '29'

        if period_num is None or period_num == 0:
            print(f"⚠️ [PIN888] period_num 为 None 或 0,使用默认值 '0'")
            period_num = '0'

        # 1. 检查 window.__pagestatus
        page_status = await page.evaluate("() => window.__pagestatus")

        # 2. 如果是 EVENTS_DETAIL_EURO,先取消订阅
        if page_status == 'EVENT_DETAILS_EURO_ODDS':
            print(f"🔄 [PIN888] 当前状态为 EVENTS_DETAIL_EURO,先取消订阅...")
            unsubscribe_message = {
                "type": "UNSUBSCRIBE",
                "destination": "EVENT_DETAILS_EURO_ODDS"
            }

            unsubscribe_success = await page.evaluate(f"""
                () => {{
                    if (window.__ws && window.__ws.readyState === 1) {{
                        window.__ws.send(JSON.stringify({unsubscribe_message}));
                        console.log('✅ 已取消 EVENTS_DETAIL_EURO 订阅');
                        return true;
                    }}
                    return false;
                }}
            """)

            if unsubscribe_success:
                print(f"✅ [PIN888] 已取消 EVENTS_DETAIL_EURO 订阅")
                await asyncio.sleep(0.2)  # 等待取消订阅生效
            else:
                print(f"⚠️ [PIN888] 取消 EVENTS_DETAIL_EURO 订阅失败")

        # 3. 清空旧数据,等待新数据更新
        await page.evaluate("""
            () => {
                window.__allEvents = null;
                window.__AllEvents = null;
                window.__parsedEvents = null;
                console.log('✅ 已清空旧数据: __allEvents, __AllEvents, __parsedEvents');
            }
        """)
        print(f"🧹 [PIN888] 已清空旧数据")

        # 4. 加载 JS 脚本
        js_code = load_js_file(
            file_name='Subscribe_live_euro_odds.js',
            platform_name='pin888'
        )

        if not js_code:
            print(f"❌ [PIN888] 加载 Subscribe_live_euro_odds.js 失败")
            return False

        # 5. 替换占位符 (确保转换为字符串)
        sport_id_str = str(sport_id)
        period_num_str = str(period_num)

        print(f"🔄 [DEBUG] 替换占位符:")
        print(f"  __SPORT_ID__ -> {sport_id_str}")
        print(f"  __PERIOD_NUM__ -> {period_num_str}")

        js_code = js_code.replace('__SPORT_ID__', sport_id_str)
        js_code = js_code.replace('__PERIOD_NUM__', period_num_str)

        # 6. 包装并执行
        wrapped_code = f"(() => {{ {js_code} }})()"

        result = await page.evaluate(wrapped_code)

        detail_start_time = time.time()
        all_events = None

        while time.time() - detail_start_time < 3:
            all_events = await get_all_events(page)
            # print(f"detail_full_odds: {detail_full_odds}")
            if all_events:
                print(f"✅ [PIN888] 获取 all_events 成功")
                # print(f"all_events: {all_events}")
                break
            await asyncio.sleep(0.1)
        
        return all_events

    except Exception as e:
        print(f"❌ [PIN888] 发送订阅请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def get_all_events(page):
        """
        获取 window.__AllEvents (完整的 odds 数据)

        Returns:
            dict: 包含 sportId, leagues 等的完整数据
        """
        try:
            data = await page.evaluate("() => window.__AllEvents")
            return data
        except Exception as e:
            print(f"❌ [PIN888] 获取 AllEvents 失败: {e}")
            return None