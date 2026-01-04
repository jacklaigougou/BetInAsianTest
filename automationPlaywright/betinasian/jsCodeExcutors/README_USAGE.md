# BetInAsian WebSocket Hook 使用说明

## 功能说明

本模块提供了完整的 WebSocket Hook 注入和管理功能,用于拦截和监控 BetInAsian 网站的 WebSocket 通信。

## 文件结构

```
automationPlaywright/betinasian/
├── jsCode/
│   └── _0websocket_hook.js          # WebSocket Hook 脚本
└── jsCodeExcutors/
    ├── __init__.py                   # 导出模块
    ├── inject_hook.py                # Hook 注入器
    └── README_USAGE.md               # 本文档
```

## 核心功能

### 1. 注入 WebSocket Hook

```python
from automationPlaywright.betinasian.jsCodeExcutors import inject_websocket_hook

# 注入 Hook
success = await inject_websocket_hook(page, handler_name="BetInAsian")

if success:
    print("Hook 注入成功!")
else:
    print("Hook 注入失败!")
```

**执行流程:**
1. 加载 `_0websocket_hook.js` 文件
2. 使用 `page.add_init_script()` 添加初始化脚本
3. 刷新页面使 Hook 生效
4. 手动执行 Hook 脚本(兼容 CDP 连接的浏览器)
5. 验证 Hook 是否成功安装

### 2. 检查 WebSocket 状态

```python
from automationPlaywright.betinasian.jsCodeExcutors import check_websocket_status

status = await check_websocket_status(page, handler_name="BetInAsian")
print(status)

# 输出示例:
# {
#     'state': 'OPEN',
#     'stateCode': 1,
#     'url': 'wss://example.com/websocket',
#     'totalWebSockets': 1
# }
```

**状态说明:**
- `CONNECTING` (0): 连接正在建立
- `OPEN` (1): 连接已建立,可以通信
- `CLOSING` (2): 连接正在关闭
- `CLOSED` (3): 连接已关闭

### 3. 获取 WebSocket 消息

```python
from automationPlaywright.betinasian.jsCodeExcutors import get_recent_ws_messages

# 获取最近 20 条消息
messages = await get_recent_ws_messages(page, count=20, handler_name="BetInAsian")

for msg in messages:
    print(f"消息 #{msg['count']}")
    print(f"时间戳: {msg['timestamp']}")
    print(f"数据: {msg['data']}")
```

**消息格式:**
```python
{
    'count': 1,                    # 消息序号
    'timestamp': 1704384000000,    # Unix 时间戳(毫秒)
    'data': {...}                  # JSON 解析后的消息数据
}
```

### 4. 发送 WebSocket 数据

```python
from automationPlaywright.betinasian.jsCodeExcutors import send_websocket_data

# 发送 JSON 数据
data = '{"type": "subscribe", "channel": "odds"}'
success = await send_websocket_data(page, data, handler_name="BetInAsian")

if success:
    print("数据发送成功!")
```

## 在 main.py 中的使用

```python
# -*- coding: utf-8 -*-
import asyncio
from fingerBrowser import FingerBrowser
from browserControler import BrowserControler
from automationPlaywright.betinasian.jsCodeExcutors import (
    inject_websocket_hook,
    check_websocket_status,
    get_recent_ws_messages
)

async def main():
    # 1. 启动浏览器并获取页面
    finger_browser = FingerBrowser(browser_type="ads")
    browser = await finger_browser.get_cdp_object(ws_url="...", tool="playwright")
    controller = BrowserControler(browser, tool="playwright")

    # 2. 打开或获取目标页面
    result = await controller.create_new_page("https://black.betinasia.com/sportsbook")
    page = result.get('page')

    # 3. 注入 WebSocket Hook
    hook_success = await inject_websocket_hook(page, handler_name="BetInAsian")

    if hook_success:
        # 4. 等待 WebSocket 连接建立
        await asyncio.sleep(3)

        # 5. 检查连接状态
        status = await check_websocket_status(page)
        print(f"WebSocket 状态: {status}")

        # 6. 定期获取消息
        while True:
            await asyncio.sleep(5)
            messages = await get_recent_ws_messages(page, count=5)
            for msg in messages:
                print(f"收到消息: {msg['data']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Hook 脚本提供的全局函数

注入成功后,页面中会有以下全局函数可用:

### JavaScript 端调用

```javascript
// 1. 发送数据
window.sendWebSocketData('{"type": "ping"}')

// 2. 获取状态
const status = window.getWebSocketStatus()
console.log(status)

// 3. 获取最近消息
const messages = window.getRecentMessages(10)
console.log(messages)

// 4. 清空消息历史
window.clearMessageHistory()
```

### Python 端调用(通过 page.evaluate)

```python
# 1. 执行 JavaScript 获取状态
status = await page.evaluate("window.getWebSocketStatus()")

# 2. 获取消息
messages = await page.evaluate("window.getRecentMessages(10)")

# 3. 清空历史
await page.evaluate("window.clearMessageHistory()")
```

## 全局变量

Hook 注入后会在页面中创建以下全局变量:

- `window.__ws` - 最新创建的 WebSocket 实例
- `window.__allWebSockets` - 所有 WebSocket 实例数组
- `window.__wsMessages` - 消息历史(最多保留 100 条)

## 注意事项

1. **注入时机**: Hook 必须在 WebSocket 创建之前注入,因此使用 `add_init_script()` + 页面刷新
2. **CDP 兼容**: 对于 CDP 连接的浏览器,`add_init_script()` 可能不生效,所以额外手动执行了一次
3. **消息限制**: 自动保留最近 100 条消息,防止内存溢出
4. **异步操作**: 所有函数都是异步的,需要使用 `await`

## 调试技巧

### 检查 Hook 是否生效

```python
# 方法 1: 检查函数是否存在
hook_check = await page.evaluate("typeof window.getWebSocketStatus")
print(f"Hook 状态: {hook_check}")  # 应该输出 'function'

# 方法 2: 直接调用状态函数
status = await page.evaluate("window.getWebSocketStatus()")
if status == 'No WebSocket instance':
    print("Hook 已安装,但页面还没有创建 WebSocket")
else:
    print(f"WebSocket 已连接: {status}")
```

### 查看浏览器控制台日志

Hook 脚本会输出详细的控制台日志:

```
[BetInAsian Hook] Hook script started
[BetInAsian Hook] New WebSocket connection: wss://...
[BetInAsian Hook] WebSocket connected: wss://...
[BetInAsian Hook] WebSocket message #1: {...}
```

在 Playwright 中监听控制台:

```python
page.on("console", lambda msg: print(f"浏览器控制台: {msg.text()}"))
```

## 故障排除

### 问题 1: Hook 注入后不生效

**原因**: 页面在 Hook 注入前就已经创建了 WebSocket

**解决**:
```python
# 注入后刷新页面
await page.reload()
```

### 问题 2: CDP 浏览器中 add_init_script 不生效

**原因**: 通过 CDP 连接的浏览器可能不支持 init_script

**解决**: 使用 `inject_websocket_hook()` 函数,它会自动手动执行 Hook 脚本

### 问题 3: 获取不到消息

**原因**: WebSocket 还没有收到消息,或者消息被覆盖

**解决**:
1. 等待足够的时间让 WebSocket 接收消息
2. 增加消息缓冲区大小(修改 Hook 脚本中的 100)
3. 及时读取消息避免被覆盖

## 扩展开发

如果需要自定义 Hook 行为,可以修改 `_0websocket_hook.js`:

```javascript
// 在消息监听器中添加自定义逻辑
ws.addEventListener('message', function (event) {
    const data = JSON.parse(event.data);

    // 自定义处理: 例如只保存特定类型的消息
    if (data.type === 'odds_update') {
        window.__oddsUpdates = window.__oddsUpdates || [];
        window.__oddsUpdates.push(data);
    }
});
```

## 安全说明

此 Hook 工具仅用于**自动化测试和开发调试**,请勿用于:
- 未授权的数据采集
- 破坏网站正常运行
- 任何违反服务条款的行为
