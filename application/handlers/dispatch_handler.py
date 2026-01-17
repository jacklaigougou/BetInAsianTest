from typing import Any, Dict


def _build_task(task_builder, method_name: str, message: Dict[str, Any]) -> None:
    method = getattr(task_builder, method_name)
    method(message)


async def handle_dispatch_message(app, message: Dict[str, Any]) -> None:
    """Handle messages coming from dispatch."""
    msg_type = message.get('type')

    match msg_type:
        case 'betting_order' | 'betting':
            print(f'收到 dispatch --> betting_order: {message}')
            app.task_builder.build_betting_order_task(message)
        case 'new_order':
            # print('收到 dispatch --> new_order: ',message)
            app.task_builder.build_new_order_task(message)
        case 'stop_pin888_cycle':
            _handle_stop_cycle(app, message)
        case 'request_balance':
            app.task_builder.build_request_balance_task(message)
        case 'single_side_success':
            app.task_builder.build_single_side_success_task(message)
        case 'onlineAccount':
            # print('收到 dispatch --> onlineAccount: ',message)
            await _filter_and_update_accounts(app, message)
        case 'single_side_failure':
            app.task_builder.build_single_side_failure_task(message)
        case 'cancel_order':
            print(f'收到 dispatch --> cancel_order: {message}')
            app.task_builder.build_cancel_order_task(message)
        case _:
            print(f"⚠️ 未知的 dispatch 消息类型: {msg_type}")


def _handle_stop_cycle(app, message: Dict[str, Any]) -> None:
    data = message.get('data', {})
    handler_name = data.get('handler_name')

    if not handler_name:
        print("⚠️ stop_pin888_cycle 消息缺少 handler_name")
        return

    account = app.online_platform.get_account(handler_name)
    if not account:
        print(f"⚠️ 未找到账号: {handler_name}")
        return

    account['PIN888_CYCLEING'] = False
    print(f"? [{handler_name}] 已设置 PIN888_CYCLEING = False, 补单循环将在下次迭代时退出")


async def _filter_and_update_accounts(app, message: Dict[str, Any]) -> None:
    """
    过滤并更新账号列表（跳过已废弃的平台）

    Args:
        app: Application 实例
        message: onlineAccount 消息
    """
    data = message.get('data', [])

    if not isinstance(data, list):
        print("⚠️ onlineAccount 消息的 data 不是列表")
        await app.online_platform.update_accounts(message)
        return

    # 过滤掉 sportsbet 平台（已废弃）
    filtered_data = [
        account for account in data
        if account.get('platform_name') != 'sportsbet'
    ]

    # 统计过滤结果
    original_count = len(data)
    filtered_count = len(filtered_data)
    skipped_count = original_count - filtered_count

    if skipped_count > 0:
        print(f"⏭️ 已跳过 {skipped_count} 个 sportsbet 账号（平台已废弃）")

    # 更新消息数据
    filtered_message = {
        **message,
        'data': filtered_data
    }

    # 调用原有的更新逻辑
    await app.online_platform.update_accounts(filtered_message)
