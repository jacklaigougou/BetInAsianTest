"""
OnlinePlatform - 在线平台账号管理单例
负责接收并存储 status="scheduling" 的账号数据
"""
from typing import Dict, Optional
from playwright.async_api import Page
import importlib
import sys
import os
import random
import time
import asyncio

# 添加 fingerBrowser 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from browserControler import BrowserControler
from fingerBrowser import FingerBrowser


class OnlinePlatform:
    """在线平台单例 - 管理调度中的账号"""

    _instance: Optional['OnlinePlatform'] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, platform_info: Dict[str, dict] = None, ws_client=None):
        """
        初始化 (只执行一次)

        Args:
            platform_info: 平台配置信息 (从 Settings.PLATFORM_INFO 传入)
            ws_client: WebSocket 客户端实例
        """
        if not OnlinePlatform._initialized:
            # 存储账号数据: {handler_name: account_data}
            # account_data 包含: 账号信息 + page 对象 + ac 对象
            self._accounts: Dict[str, dict] = {}
            # 存储平台配置信息
            self._platform_info: Dict[str, dict] = platform_info or {}
            # 存储 WebSocket 客户端
            self._ws_client = ws_client
            # 初始化 FingerBrowser 实例 (Linken Sphere)
            self._finger_browser = FingerBrowser(browser_type="linken_sphere")
            OnlinePlatform._initialized = True
            print("✅ OnlinePlatform 单例已初始化")
            print("✅ FingerBrowser (Linken Sphere) 已初始化")

    async def update_accounts(self, message: dict) -> int:
        """
        更新账号数据 (只记录 status="scheduling")
        自动合并 PLATFORM_INFO 中的配置信息
        创建 page 和 ActionChain 对象

        Args:
            message: WebSocket 消息 {"type": "onlineAccount", "data": [...]}

        Returns:
            新增的账号数量
        """
        if message.get('type') != 'onlineAccount':
            return 0
        # print(message)
        data = message.get('data', [])
        added_count = 0

        # === 调试日志开始 ===
        # print(f"\n{'='*60}")
        # print(f"🔍 [DEBUG] update_accounts 被调用")
        # print(f"📦 完整消息: {message}")
        # print(f"📊 data 数组长度: {len(data)}")
        # for idx, acc in enumerate(data):
        #     print(f"  [{idx+1}] handler_name={acc.get('handler_name')}, status='{acc.get('status')}', platform={acc.get('platform_name')}")
        # print(f"{'='*60}\n")
        # === 调试日志结束 ===

        for account in data:
            handler_name = account.get('handler_name')
            status = account.get('status')

            # 调试日志: 打印实际的 status 值
            # print(f"🔍 [调试] handler_name={handler_name}, status='{status}', type={type(status)}")

            # 1. 只记录 status="scheduling"
            if status != 'scheduling':
                # 如果之前存在且是 scheduling,现在不是了 → 删除
                if handler_name and handler_name in self._accounts:
                    print(f"⚠️ [DEBUG] 准备删除账号: {handler_name} (原因: status='{status}' != 'scheduling')")
                    self.remove_account(handler_name)
                else:
                    # print(f"ℹ️ [调试] status != 'scheduling', 但账号不在列表中,跳过")
                    pass
                continue

            platform_name = account.get('platform_name')

            if not handler_name or not platform_name:
                continue

            # 2. 如果账号已存在,检查关键字段是否变化
            if handler_name in self._accounts:
                existing_account = self._accounts[handler_name]

                # ⚠️ 重要: WebSocket 消息不包含 port/ws_url,不应该用来判断连接是否变化
                # 只有当 WebSocket 消息明确提供了新的 port/ws 时才检查变化
                port_changed = False
                ws_changed = False

                if account.get('port') is not None:
                    port_changed = account.get('port') != existing_account.get('port')
                if account.get('ws') is not None:
                    ws_changed = account.get('ws') != existing_account.get('ws')

                # 检查 page 对象是否已关闭
                page = existing_account.get('page')
                page_closed = False
                if page:
                    try:
                        page_closed = page.is_closed()
                    except Exception:
                        page_closed = True  # 如果检查失败,认为已关闭

                # 如果 CDP 连接变化或 page 已关闭,需要重建
                need_reconnect = port_changed or ws_changed or page_closed

                if need_reconnect:
                    print(f"🔄 [{handler_name}] 检测到 CDP 连接变化,重建 page:")
                    if port_changed:
                        print(f"   - port: {existing_account.get('port')} → {account.get('port')}")
                    if ws_changed:
                        print(f"   - ws: {existing_account.get('ws')} → {account.get('ws')}")
                    if page_closed:
                        print(f"   - page 已关闭")

                    # ⚠️ 关键修复: 只更新非 None 的字段,保留已获取的 port/ws_url
                    for key, value in account.items():
                        if value is not None:
                            existing_account[key] = value

                    # 重建 page 和 ac
                    try:
                        await self._create_page_and_ac(handler_name)
                        print(f"✅ [{handler_name}] page 重建成功")
                    except Exception as e:
                        print(f"❌ [{handler_name}] page 重建失败: {e}")
                else:
                    # 只更新动态字段,不覆盖 port/ws_url/page/ac
                    # ⚠️ 关键修复: 只更新非 None 且非关键字段的值
                    for key, value in account.items():
                        if value is not None and key not in ['page', 'ac', 'port', 'ws_url']:
                            existing_account[key] = value
                    # print(f"🔄 更新账号信息: {handler_name} (balance: {account.get('balance')})")

                    # ✅ 定期查询余额并发送给 dispatch
                    try:
                        current_time = time.time()
                        last_check = existing_account.get('last_balance_check', 0)
                        check_interval = existing_account.get('next_balance_check_interval', 0)

                        # 判断是否需要查询余额
                        should_check = False
                        is_first_check = False

                        if last_check == 0:
                            # 第一次查询,立即执行
                            should_check = True
                            is_first_check = True
                        elif (current_time - last_check) >= check_interval:
                            # 超过间隔时间,执行查询
                            should_check = True

                        if should_check:
                            # 获取 ac 对象
                            ac = existing_account.get('ac')
                            if ac and hasattr(ac, 'GetBalanceByRequest'):
                                # 随机延迟 1-2 秒
                                delay = random.uniform(1, 2)
                                # print(f"💤 [{handler_name}] 延迟 {delay:.2f}秒后查询余额...")
                                await asyncio.sleep(delay)

                                # 查询余额
                                balance = await ac.GetBalanceByRequest()

                                if balance is not None:
                                    # 更新本地余额
                                    existing_account['balance'] = balance
                                    # print(f"💰 [{handler_name}] 余额查询成功: {balance}")

                                    # 发送余额到 dispatch
                                    if self._ws_client:
                                        try:
                                            await self._ws_client.send({
                                                'from': 'automation',
                                                'to': 'dispatch',
                                                'type': 'balance_update',
                                                'data': {
                                                    'handler_name': handler_name,
                                                    'balance': balance
                                                }
                                            })
                                            if is_first_check:
                                                print(f"📤 [{handler_name}] 首次余额已发送: {balance}")
                                            # else:
                                            #     print(f"📤 [{handler_name}] 余额已更新并发送: {balance}")
                                        except Exception as e:
                                            print(f"⚠️ [{handler_name}] 发送余额失败: {e}")
                                # else:
                                    # print(f"⚠️ [{handler_name}] 余额查询失败")

                                # 更新查询时间和下次间隔 (无论成功与否)
                                existing_account['last_balance_check'] = current_time
                                existing_account['next_balance_check_interval'] = random.uniform(60, 120)
                            # else:
                                # print(f"⚠️ [{handler_name}] ac 对象不存在或没有 GetBalanceByRequest 方法")
                    except Exception as e:
                        print(f"❌ [{handler_name}] 余额查询异常: {e}")

                continue  # 不重复创建

            # 3. 合并平台配置信息
            enhanced_account = account.copy()
            if platform_name in self._platform_info:
                platform_config = self._platform_info[platform_name]
                enhanced_account.update({
                    'start_url': platform_config.get('start_url'),
                    'match_url': platform_config.get('match_url'),
                    'folder_addr': platform_config.get('folder_addr'),
                    'file_name': platform_config.get('file_name'),
                    'class_name': platform_config.get('class_name'),
                    'js_base_path': platform_config.get('js_base_path'),
                })

            # 4. 添加新账号
            self._accounts[handler_name] = enhanced_account
            added_count += 1
            # print(f"📝 新增调度账号: {handler_name} (平台: {platform_name})")

            # 5. 创建 page 和 ActionChain 对象 (直接修改 _accounts 中的引用)
            try:
                await self._create_page_and_ac(handler_name)
            except Exception as e:
                print(f"❌ 创建 page/ac 失败 ({handler_name}): {e}")

        # 打印所有账号及其 balance
        print(f"\n📋 [DEBUG] 当前所有账号: {list(self._accounts.keys())}")
        if self._accounts:
            # print(f"\n📊 当前所有调度账号 (共 {len(self._accounts)} 个):")
            for name, acc in self._accounts.items():
                balance = acc.get('balance', 'N/A')
                platform = acc.get('platform_name', 'N/A')
                status = acc.get('status', 'N/A')
                # print(f"  • {name}: balance={balance}, platform={platform}, status={status}")
            # print()

        return added_count

    async def _create_page_and_ac(self, handler_name: str):
        """创建 page 和 ActionChain。"""
        account = self._accounts.get(handler_name)
        if not account:
            print(f"❌ 账号 {handler_name} 不存在")
            return

        if account.get('page') and account.get('ac'):
            return

        port = account.get('port')
        folder_addr = account.get('folder_addr')
        file_name = account.get('file_name')
        class_name = account.get('class_name')
        browser_id = account.get('ads_id')

        if not browser_id:
            print(f"⚠️ 账号 {handler_name} 缺少 browser_id (ads_id),跳过创建 page")
            print("   提示: 请在 WebSocket 消息中添加 'ads_id' 字段")
            return

        if not port:
            print(f"🔍 [{handler_name}] port 不存在或首次初始化,尝试从 FingerBrowser 获取...")
            try:
                browser_info = await self._finger_browser.get_single_browser_info(
                    browser_id=browser_id,
                    auto_launch=True
                )
            except Exception as exc:
                print(f"❌ [{handler_name}] 获取浏览器信息失败: {exc}")
                return

            account['port'] = browser_info.get('debug_port')
            account['ws_url'] = browser_info.get('ws_url')
            port = account['port']

        if not port:
            print(f"⚠️ 账号 {handler_name} 仍没有有效 port,跳过创建 page")
            return

        ws_url = account.get('ws_url')
        connect_model = 'ws_url' if ws_url else 'port'

        try:
            browser_object = await self._finger_browser.get_cdp_object(
                ws_url=ws_url,
                port=port,
                tool='playwright',
                model=connect_model
            )
            browser_controller = BrowserControler(browser_object, tool='playwright')
        except Exception as exc:
            print(f"❌ [{handler_name}] 连接浏览器失败: {exc}")
            return

        match_url = account.get('match_url')
        page = None

        if match_url:
            try:
                result = await browser_controller.check_url_exists(match_url)
                if result.get('exists'):
                    page = result.get('page')
                    print(f"✅ 已找到匹配页面: {handler_name} (url: {result.get('url')})")
            except Exception as exc:
                print(f"⚠️ [{handler_name}] 检查页面失败: {exc}")

        if not page:
            start_url = account.get('start_url')
            if not start_url:
                print(f"⚠️ 账号 {handler_name} 缺少 start_url,无法创建 page")
                return

            try:
                create_result = await browser_controller.create_new_page(
                    start_url,
                    wait_until='domcontentloaded',
                    timeout=30000
                )
            except Exception as exc:
                print(f"❌ [{handler_name}] 创建页面失败: {exc}")
                return

            if not create_result.get('success'):
                print(f"⚠️ [{handler_name}] 创建页面失败: {create_result.get('message')}")
                return

            page = create_result.get('page')
            print(f"✅ [{handler_name}] 成功导航到 {create_result.get('url')}")

        account['browser_controller'] = browser_controller
        account['page'] = page

        if not all([folder_addr, file_name, class_name]):
            print(f"⚠️ 账号 {handler_name} 缺少 ActionChain 配置,跳过创建 ac")
            return

        try:
            module = importlib.import_module(f"{folder_addr}.{file_name}")
            ActionChainClass = getattr(module, class_name)
            ac = ActionChainClass(
                browser_controller=browser_controller,
                page=page,
                config=account,
                ws_client=self._ws_client,
                online_platform=account
            )
            account['ac'] = ac
            print(f"🔍 [{handler_name}] ac: {ac}")

            if hasattr(ac, 'prepare_work'):
                try:
                    print(f"🛠 [{handler_name}] 开始执行 prepare_work")
                    result = await ac.prepare_work()
                    if not result:
                        print(f"⚠️ [{handler_name}] prepare_work 未返回数据")
                except Exception as exc:
                    print(f"⚠️ [{handler_name}] prepare_work 异常: {exc}")
        except Exception as exc:
            print(f"❌ 创建 ActionChain 失败 ({handler_name}): {exc}")
    
    
    def get_account(self, handler_name: str) -> Optional[dict]:
        """获取指定账号 (包含 page 和 ac)"""
        return self._accounts.get(handler_name)

    def get_page(self, handler_name: str) -> Optional[Page]:
        """获取指定账号的 page 对象"""
        account = self._accounts.get(handler_name)
        return account.get('page') if account else None

    def get_action_chain(self, handler_name: str):
        """获取指定账号的 ActionChain 对象"""
        account = self._accounts.get(handler_name)
        return account.get('ac') if account else None

    def get_all_accounts(self) -> Dict[str, dict]:
        """获取所有调度账号"""
        return self._accounts.copy()

    def get_accounts_by_platform(self, platform_name: str) -> Dict[str, dict]:
        """获取指定平台的所有账号"""
        return {
            name: data
            for name, data in self._accounts.items()
            if data.get('platform_name') == platform_name
        }

    def remove_account(self, handler_name: str) -> bool:
        """
        移除账号（状态变为非 scheduling 时调用）
        清理 page 和 ac 对象
        """
        if handler_name not in self._accounts:
            return False

        account = self._accounts[handler_name]

        # 清理 page 对象
        page = account.get('page')
        if page:
            try:
                # 注意: 这是同步方法,不能 await page.close()
                # page 会在浏览器关闭时自动清理
                print(f"🧹 清理 {handler_name} 的 page 对象")
            except Exception as e:
                print(f"⚠️ 清理 page 失败: {e}")

        # 清理 ac 对象
        ac = account.get('ac')
        if ac:
            try:
                # ac 对象通常不需要特殊清理
                print(f"🧹 清理 {handler_name} 的 ac 对象")
            except Exception as e:
                print(f"⚠️ 清理 ac 失败: {e}")

        # 从字典中删除
        del self._accounts[handler_name]
        print(f"🗑️ 移除账号: {handler_name} (状态变为非 scheduling)")
        return True

    def clear(self):
        """清空所有账号"""
        count = len(self._accounts)
        self._accounts.clear()
        print(f"🧹 已清空 {count} 个账号")

    def count(self) -> int:
        """获取账号总数"""
        return len(self._accounts)

    async def cleanup(self):
        """
        清理 FingerBrowser 资源
        在应用退出时调用,关闭 HTTP 会话
        """
        try:
            await self._finger_browser.close_session()
            print("✅ FingerBrowser 资源已清理")
        except Exception as e:
            print(f"⚠️ 清理 FingerBrowser 资源失败: {e}")

    def __repr__(self):
        return f"<OnlinePlatform: {len(self._accounts)} accounts>"
