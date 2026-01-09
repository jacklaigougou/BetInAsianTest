class Pin888POM:
    def __init__(self, page):
        self.page = page

    async def find_balance_element(self):
        """
        查找余额元素
        <span class="BalanceStyled-sc-1qwy9qm-2 jpMlCy">USD <span>2.31</span></span>

        Returns:
            Locator: 余额元素定位器
        """
        # 定位内部包含数值的 span 元素
        locator = self.page.locator('xpath=//span[contains(@class, "BalanceStyled-sc-")]//span')
        
        try:
            await locator.wait_for(timeout=30000)
            return locator
        except Exception as e:
            print(f"⚠️ [PIN888] 余额元素未找到: {e}")
            return None

    async def find_balance_by_request(self):
        """
        通过发送请求获取账户余额
        调用 Request_accountBalance.js 发送 GET 请求到 member-service API

        Returns:
            str: 余额数值,如 "2.31",失败返回 None
        """
        from utils.js_loader import get_js_loader
        import json
        import time

        try:
            # 加载 JS 文件
            js_code = get_js_loader(
                file_name='Request_accountBalance.js',
                platform_name='pin888'
            )

            if not js_code:
                print(f"❌ [PIN888] 加载 Request_accountBalance.js 失败")
                return None

            # 执行 JS 代码
            wrapped_code = f"(() => {{ {js_code} }})()"
            response = await self.page.evaluate(wrapped_code)
            # print(f"💰 [PIN888] 余额请求响应: {response}")
            # 检查响应
            if not response:
                print(f"❌ [PIN888] 余额请求返回空响应")
                return None

            if response.get('error'):
                print(f"❌ [PIN888] 余额请求失败: {response.get('error')}")
                return None

            if response.get('status') != 200:
                print(f"❌ [PIN888] 余额请求失败,状态码: {response.get('status')}")
                return None

            # 解析响应数据
            response_text = response.get('response')
            if response_text:
                data = json.loads(response_text)
                # API 返回格式: {"betCredit": 19.31, "currency": "USD", "success": true, ...}
                if data.get('success'):
                    balance = data.get('betCredit')
                    if balance is not None:
                        return str(balance)  # 转换为字符串返回
                    else:
                        print(f"❌ [PIN888] 响应中没有 betCredit 字段")
                        return None
                else:
                    print(f"❌ [PIN888] API 返回 success=false")
                    return None
            else:
                print(f"❌ [PIN888] 余额响应为空")
                return None

        except Exception as e:
            print(f"❌ [PIN888] 获取余额失败: {e}")
            return None


    async def find_Login_btn_element(self):
        # 在 div class 包含 RowIine 下的 Log in 按钮
        return self.page.locator('xpath=//div[contains(@class, "RowInline")]//span[text()="Log in"]/parent::button')

    async def find_Login_btn_element_2(self):
        # 在 div class 包含 ContentStyled 下的 Log in 按钮
        return self.page.locator('xpath=//div[contains(@class, "ContentStyled")]//span[text()="Log in"]/parent::button')

    async def find_username_input_element(self):
        # 在 div class 包含 ContentStyled 下的 username 输入框
        return self.page.locator('xpath=//div[contains(@class, "ContentStyled")]//input[@name="username"]')

    async def find_password_input_element(self):
        # 在 div class 包含 ContentStyled 下的 password 输入框
        return self.page.locator('xpath=//div[contains(@class, "ContentStyled")]//input[@name="password"]')

    async def find_deposit_link_element(self):
        # 匹配 a 标签,data-test-id 为 Button,文本严格为 Deposit
        return self.page.locator('xpath=//a[@data-test-id="Button" and text()="Deposit"]')