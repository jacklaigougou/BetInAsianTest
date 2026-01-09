# -*- coding: utf-8 -*-
"""
Pin888 准备工作
"""
from typing import Dict, Any
import logging
import asyncio
from utils import get_js_loader

logger = logging.getLogger(__name__)


async def prepare_work(
    self,
    **kwargs
) -> Dict[str, Any]:
    """
    准备工作: 检查登录状态、注入 WebSocket Hook、获取余额

    注意: 浏览器操作由 browser_controller 处理,此方法只负责业务逻辑

    Args:
        **kwargs: 额外参数

    Returns:
        {
            'success': bool,
            'message': str,
            'balance': str,
            'ws_status': str
        }
    """
    handler_name = self.handler_name

    try:
        # ========== Step 1: 检查页面状态 ==========
        logger.info(f"[{handler_name}] Step 1: 检查页面状态")

        if not self.page:
            return {'success': False, 'message': 'page 对象不存在'}

        logger.info(f"[{handler_name}] 当前页面 URL: {self.page.url}")
        logger.info(f"[{handler_name}] 页面是否关闭: {self.page.is_closed()}")

        # 等待页面加载完成
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
            logger.info(f"[{handler_name}] ✅ 页面加载完成")
        except Exception as e:
            logger.warning(f"[{handler_name}] ⚠️ 等待页面加载超时: {e}")

        await asyncio.sleep(15)  # 缓冲时间 (与原代码一致)

        # ========== Step 2: 检查登录状态 ==========
        logger.info(f"[{handler_name}] Step 2: 检查登录状态")

        deposit_link = await self.pom.find_deposit_link_element()
        deposit_count = await deposit_link.count()
        logger.info(f"[{handler_name}] Deposit 按钮数量: {deposit_count}")

        if deposit_count > 0:
            logger.info(f"[{handler_name}] ✅ 已登录,跳过登录流程")
        else:
            # ========== Step 3: 执行登录流程 ==========
            logger.info(f"[{handler_name}] Step 3: 执行登录流程")

            login_success = await _perform_login(self)

            if not login_success:
                return {'success': False, 'message': '登录失败'}

        # ========== Step 4: 注入 WebSocket Hook ==========
        logger.info(f"[{handler_name}] Step 4: 注入 WebSocket Hook")

        hook_success = await _inject_websocket_hook(self)

        if not hook_success:
            logger.warning(f"[{handler_name}] ⚠️ WebSocket Hook 注入失败")
            # 不返回失败,继续执行

        # ========== Step 5: 获取余额并发送 ==========
        logger.info(f"[{handler_name}] Step 5: 获取余额并发送")

        balance = await self.pom.find_balance_by_request()

        if balance:
            logger.info(f"[{handler_name}] 💰 当前余额: {balance}")

            # 保存到 handler_info
            from ..pin888_automation import Pin888Automation
            Pin888Automation.handler_info[handler_name]['balance'] = balance

            # 发送余额到 dispatch
            if self.ws_client:
                try:
                    await self.ws_client.send({
                        'from': 'automation',
                        'to': 'dispatch',
                        'type': 'balance_update',
                        'data': {
                            'handler_name': handler_name,
                            'balance': balance
                        }
                    })
                    logger.info(f"[{handler_name}] 📤 余额已发送")
                except Exception as e:
                    logger.warning(f"[{handler_name}] ⚠️ 发送余额失败: {e}")

        # ========== 返回成功 ==========
        logger.info(f"[{handler_name}] ✅ 初始化成功")
        return {
            'success': True,
            'message': '准备工作完成',
            'balance': balance,
            'ws_status': 'connected'
        }

    except Exception as e:
        logger.error(f"[{handler_name}] 准备工作失败: {e}", exc_info=True)
        return {
            'success': False,
            'message': f'准备工作异常: {str(e)}'
        }


async def _inject_websocket_hook(self) -> bool:
    """
    注入 WebSocket Hook (内部辅助方法)

    参考: actionChain.py hookWebSocket() 方法

    Returns:
        bool: 注入成功返回 True
    """
    handler_name = self.handler_name

    try:
        logger.info(f"[{handler_name}] 🔧 开始注入 WebSocket Hook...")

        # 1. 加载 Hook 脚本 (使用 JSLoader)
        js_loader = get_js_loader()
        hook_code = js_loader.get_js_content('pin888', '_0websocket_hook.js')

        if not hook_code:
            logger.error(f"[{handler_name}] ❌ 加载 _0websocket_hook.js 失败")
            return False

        # 2. 使用 add_init_script 注入
        try:
            await self.page.add_init_script(hook_code)
            logger.info(f"[{handler_name}] ✅ Hook 脚本已添加到页面初始化脚本")
        except Exception as e:
            logger.error(f"[{handler_name}] ❌ 添加 init_script 失败: {e}")
            return False

        # 3. 刷新页面,使 Hook 生效
        logger.info(f"[{handler_name}] 🔄 刷新页面以激活 Hook...")
        try:
            await self.page.reload(wait_until='domcontentloaded', timeout=15000)
            logger.info(f"[{handler_name}] ✅ 页面刷新完成")
        except Exception as e:
            logger.warning(f"[{handler_name}] ⚠️ 页面刷新超时,但可能已加载: {e}")

        # 4. 手动执行 Hook (兼容 CDP 浏览器)
        logger.info(f"[{handler_name}] 🔧 手动执行 Hook 脚本...")
        try:
            await self.page.evaluate(hook_code)
            logger.info(f"[{handler_name}] ✅ Hook 脚本手动执行完成")
        except Exception as e:
            logger.error(f"[{handler_name}] ❌ 手动执行 Hook 失败: {e}")
            return False

        # 5. 验证 Hook 是否生效
        try:
            hook_check = await self.page.evaluate("typeof window.getWebSocketStatus")
            logger.info(f"[{handler_name}] 🔍 Hook 检查: window.getWebSocketStatus = {hook_check}")

            if hook_check == 'function':
                logger.info(f"[{handler_name}] ✅ WebSocket Hook 注入成功!")
                return True
            else:
                logger.warning(f"[{handler_name}] ⚠️ Hook 可能未生效")
                return False
        except Exception as e:
            logger.warning(f"[{handler_name}] ⚠️ Hook 验证失败: {e}")
            return False

    except Exception as e:
        logger.error(f"[{handler_name}] Hook 注入异常: {e}", exc_info=True)
        return False


async def _perform_login(self) -> bool:
    """
    执行登录流程 (内部辅助方法)

    参考: actionChain.py prepare_work() 方法 (第1389-1456行)

    Returns:
        bool: 登录成功返回 True
    """
    handler_name = self.handler_name

    try:
        logger.info(f"[{handler_name}] 🔐 开始登录流程...")

        # 1. 点击登录按钮
        login_btn = await self.pom.find_Login_btn_element()
        login_btn_count = await login_btn.count()
        logger.info(f"[{handler_name}] Login 按钮数量: {login_btn_count}")

        if login_btn_count == 0:
            logger.error(f"[{handler_name}] ❌ 登录按钮不存在")
            return False

        try:
            await login_btn.click()
        except Exception as e:
            logger.error(f"[{handler_name}] ⚠️ 点击登录按钮失败: {e}")
            return False

        await asyncio.sleep(3)

        # 2. 填写用户名密码
        login_btn_2 = await self.pom.find_Login_btn_element_2()
        if await login_btn_2.count() == 0:
            logger.error(f"[{handler_name}] ❌ 登录按钮2不存在")
            return False

        username_input = await self.pom.find_username_input_element()
        password_input = await self.pom.find_password_input_element()

        if await username_input.count() == 0:
            logger.error(f"[{handler_name}] ❌ 输入框不存在")
            return False

        # 检查输入框是否已有内容
        username_value = await username_input.input_value()
        password_value = await password_input.input_value()

        if not username_value or not password_value:
            # ========== 通过 Backend 模块获取账号信息 ==========
            logger.info(f"[{handler_name}] 输入框为空,通过 Backend 获取账号信息...")

            # 从 config 获取 ads_id
            ads_id = self.config.get('ads_id')

            if not ads_id:
                logger.error(f"[{handler_name}] ❌ 配置中缺少 ads_id")
                return False

            # ✅ 调用 Backend 模块获取账号信息
            from backend import get_account_info

            account_result = await get_account_info(
                ads_id=ads_id,
                platform='pin888'
            )

            # 检查结果
            if not account_result['success']:
                logger.error(f"[{handler_name}] ❌ 获取账号信息失败: {account_result['message']}")
                return False

            username = account_result['username']
            password = account_result['password']

            logger.info(f"[{handler_name}] ✅ 成功获取账号信息")

            # 填充输入框
            await username_input.fill(username)
            await password_input.fill(password)
            await asyncio.sleep(0.5)

        # 3. 提交登录
        await login_btn_2.click()
        await asyncio.sleep(3)

        # 4. 验证登录成功
        deposit_link = await self.pom.find_deposit_link_element()
        if await deposit_link.count() > 0:
            logger.info(f"[{handler_name}] ✅ 登录成功")
            return True
        else:
            logger.error(f"[{handler_name}] ❌ 登录失败")
            return False

    except Exception as e:
        logger.error(f"[{handler_name}] 登录异常: {e}", exc_info=True)
        return False
