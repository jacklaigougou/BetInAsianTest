"""
PIN888 平台 - 取消 EVENTS_DETAIL_EURO 订阅
"""

import asyncio


async def unsubscribe_events_detail_euro(page, event_id=None):
    """
    取消 EVENTS_DETAIL_EURO 订阅

    Args:
        page: Playwright Page 对象
        event_id: 比赛事件ID (可选,用于日志输出)

    Returns:
        bool: 取消成功返回 True,失败返回 False
    """
    try:
        # 检查当前订阅状态
        page_status = await page.evaluate("() => window.__pagestatus")

        if page_status != 'EVENTS_DETAIL_EURO':
            # print(f"ℹ️ [PIN888] 当前不是 EVENTS_DETAIL_EURO 状态 (当前: {page_status}),无需取消订阅")
            return True

        # 发送取消订阅消息
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
                console.error('❌ WebSocket 未连接');
                return false;
            }}
        """)

        if unsubscribe_success:
            # 清空详情数据
            await page.evaluate("""
                () => {
                    window.___detailFullOdds = null;
                    window.__pagestatus = null;
                }
            """)

            event_log = f" (event_id: {event_id})" if event_id else ""
            print(f"✅ [PIN888] 已取消 EVENTS_DETAIL_EURO 订阅{event_log}")
            await asyncio.sleep(0.1)  # 短暂等待确保取消生效
            return True
        else:
            print(f"⚠️ [PIN888] 取消 EVENTS_DETAIL_EURO 订阅失败: WebSocket 未连接")
            return False

    except Exception as e:
        print(f"❌ [PIN888] 取消订阅异常: {e}")
        import traceback
        traceback.print_exc()
        return False
