"""
PIN888 平台 - EVENTS_DETAIL_EURO 订阅相关的 JS 代码执行器
"""

import asyncio
import json
from utils import get_js_loader
import time

async def subscribe_events_detail_euro(page, event_id):
    """
    发送 EVENTS_DETAIL_EURO 订阅请求
    如果当前状态是 LIVE_EURO_ODDS,先取消订阅
    自动从 cookies 获取 dpMs1

    Args:
        page: Playwright Page 对象
        event_id: 比赛事件ID

    Returns:
        bool: 发送成功返回 True
    """
    try:
        # 1. 检查 window.__pagestatus
        page_status = await page.evaluate("() => window.__pagestatus")

        # 2. 如果是 LIVE_EURO_ODDS,先取消订阅
        if page_status == 'LIVE_EURO_ODDS':
            print(f"🔄 [PIN888] 当前状态为 LIVE_EURO_ODDS,先取消订阅...")
            unsubscribe_message = {
                "type": "UNSUBSCRIBE",
                "destination": "EVENT_DETAILS_EURO_ODDS"
            }

            unsubscribe_success = await page.evaluate(f"""
                () => {{
                    if (window.__ws && window.__ws.readyState === 1) {{
                        window.__ws.send(JSON.stringify({unsubscribe_message}));
                        console.log('✅ 已取消 LIVE_EURO_ODDS 订阅');
                        return true;
                    }}
                    return false;
                }}
            """)

            if unsubscribe_success:
                print(f"✅ [PIN888] 已取消 LIVE_EURO_ODDS 订阅")
                await asyncio.sleep(0.2)  # 等待取消订阅生效
            else:
                print(f"⚠️ [PIN888] 取消 LIVE_EURO_ODDS 订阅失败")

        # 3. 清空旧的详情数据
        await page.evaluate("""
            () => {
                window.___detailFullOdds = null;
                console.log('✅ 已清空旧数据: ___detailFullOdds');
            }
        """)
        print(f"🧹 [PIN888] 已清空旧详情数据")

        # 4. 加载 EVENTS_DETAIL_EURO 订阅脚本
        js_loader = get_js_loader()
        js_code = js_loader.get_js_content(
            'pin888',
            'Subscribe_events_detail_euro.js'
        )


        if not js_code:
            print(f"❌ [PIN888] 加载 Subscribe_events_detail_euro.js 失败")
            return False

        # 5. 验证并替换 event_id 占位符
        if event_id is None or event_id == '':
            print(f"❌ [PIN888] event_id 无效: {event_id}")
            return False

        # 使用 json.dumps 确保生成有效的 JavaScript 字面量
        # None → null, 123 → 123, "abc" → "abc"
        js_code = js_code.replace('__EVENT_ID__', json.dumps(event_id))

        # 6. 包装并执行
        wrapped_code = f"(() => {{ {js_code} }})()"

        result = await page.evaluate(wrapped_code)
        
        detail_start_time = time.time()
        detail_full_odds = None

        while time.time() - detail_start_time < 3:
            detail_full_odds = await get_detail_full_odds(page)
            # print(f"detail_full_odds: {detail_full_odds}")
            if detail_full_odds:
                break
            await asyncio.sleep(0.1)

        # 验证数据完整性
        if not detail_full_odds:
            print(f'❌ [PIN888] 未获取到 detail_full_odds 数据')
            return None

        # 数据结构: {eventId, info, normal, ...}
        # info 和 normal 直接在顶层，没有 odds 这一层
        info = detail_full_odds.get('info')
        if not info:
            print(f'❌ [PIN888] detail_full_odds 中缺少 info 字段')
            print(f'收到的数据: {detail_full_odds}')
            return None

        normal = detail_full_odds.get('normal')
        if not normal:
            print(f'⚠️ [PIN888] detail_full_odds 中缺少 normal 字段')
            # normal 可能为空，但不是致命错误

        print(f'✅ [PIN888] 成功获取详情数据: eventId={detail_full_odds.get("eventId")}')

        return detail_full_odds

    except Exception as e:
        print(f"❌ [PIN888] 发送 EVENTS_DETAIL_EURO 订阅失败: {e}")
        return False


async def get_detail_full_odds(page):
        """
        获取 window.___detailFullOdds (比赛详情数据)

        Returns:
            dict: 包含 eventId, info, normal, specials 等的详情数据
        """
        try:
            data = await page.evaluate("() => window.___detailFullOdds")
            return data
        except Exception as e:
            print(f"❌ [PIN888] 获取 detailFullOdds 失败: {e}")
            return None
