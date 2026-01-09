// 从 cookies 中获取 dpMs1
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

// 构造订阅消息
const dpMs1 = getDpMs1FromCookies();
const sportId = '__SPORT_ID__';  // 将被 Python 替换
const periodNum = '__PERIOD_NUM__';  // 将被 Python 替换

const subscribeMessage = {
    type: 'SUBSCRIBE',
    destination: 'LIVE_EURO_ODDS',
    body: {
        sportId: sportId,
        isHlE: false,
        isLive: true,
        oddsType: 1,
        version: 0,
        eventType: 0,
        periodNum: periodNum,
        locale: 'en_US'
    }
};

// 如果找到 dpMs1，则添加到 body 中
if (dpMs1) {
    subscribeMessage.body.dpMs1 = dpMs1;
}

// 发送订阅消息
if (window.__ws && window.__ws.readyState === 1) {
    window.__ws.send(JSON.stringify(subscribeMessage));
    console.log('✅ 已发送 LIVE_EURO_ODDS 订阅:', subscribeMessage);
    return true;
} else {
    console.log('❌ WebSocket 未连接');
    return false;
}
