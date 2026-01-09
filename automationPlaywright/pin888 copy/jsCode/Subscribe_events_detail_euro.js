// 从 cookies 获取 dpMs1 (可选)
function getDpMs1FromCookies() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'dpMs1') {
            return value;
        }
    }
    return null;
}

const dpMs1 = getDpMs1FromCookies();
const eventId = __EVENT_ID__;  // 将被 Python 替换为实际 eventId

// 构建订阅消息
const subscribeMessage = {
    type: 'SUBSCRIBE',
    destination: 'EVENT_DETAILS_EURO_ODDS',
    body: {
        eventId: eventId,
        oddsType: 1,
        version: 0,
        locale: 'en_US'
    }
};

// 如果有 dpMs1,添加到 body
if (dpMs1) {
    subscribeMessage.body.dpMs1 = dpMs1;
}

// 发送订阅请求
if (window.__ws && window.__ws.readyState === 1) {
    window.__ws.send(JSON.stringify(subscribeMessage));
    console.log('✅ [PIN888] 已发送 EVENTS_DETAIL_EURO 订阅:', subscribeMessage);
    return true;
} else {
    console.log('❌ [PIN888] WebSocket 未连接');
    return false;
}
