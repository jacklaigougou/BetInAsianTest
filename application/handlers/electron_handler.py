import json
from typing import Any, Dict

from core.config import config


async def handle_electron_message(app: 'Application', message: Dict[str, Any]) -> None:
    """Handle messages coming from Electron/logWindow."""
    msg_type = message.get('type')

    if msg_type == 'onlineAccount':
        if app.settings.ENABLE_AUTO_MONITOR:
            added = await app.online_platform.update_accounts(message)
            accounts = app.online_platform.get_all_accounts()
            print(f"📋 当前调度账号总数: {len(accounts)} (本次新增 {added})")
        return

    if msg_type == 'set_automation_config':
        await _apply_automation_config(message)
        return

    print(f"⚠️ 未知的 electron 消息类型: {message}")


async def _apply_automation_config(message: Dict[str, Any]) -> None:
    """Apply automation configuration updates coming from Electron."""
    print(f"🧩 [配置更新] 收到配置: {message.get('data')}")
    data = message.get('data', {})

    acceptable_drop_rate = data.get('acceptableDropRate')
    if acceptable_drop_rate is not None:
        try:
            config.set_odds_drop_threshold(float(acceptable_drop_rate))
        except Exception as exc:  # noqa: BLE001
            print(f"? [配置错误] 设置 acceptableDropRate 失败: {exc}")

    first_retry_time = data.get('firstRetryTime')
    if first_retry_time is not None:
        try:
            config.set_supplementary_order_timeout(float(first_retry_time))
        except Exception as exc:  # noqa: BLE001
            print(f"? [配置错误] 设置 firstRetryTime 失败: {exc}")

    retry_count = data.get('retryCount')
    if retry_count is not None:
        try:
            config.set_max_retry_count(int(retry_count))
        except Exception as exc:  # noqa: BLE001
            print(f"? [配置错误] 设置 retryCount 失败: {exc}")

    print(f"? [配置完成] 当前配置: {config}")
