// RequestBuyV2.js - 发送buyV2下单请求
// 通过同步XHR发送POST请求到pin888的bet-placement API

try {
    // 从Python传入的参数
    const stake = __STAKE__;
    const odds = "__ODDS__";
    const oddsId = "__ODDS_ID__";
    const selectionId = "__SELECTION_ID__";

    // 验证必要字段是否存在
    if (!odds || !oddsId || !selectionId) {
        return {
            error: '订单信息缺少必要字段',
            status: 0,
            timestamp: new Date().toISOString()
        };
    }

    // 浏览器生成UUID和时间戳
    const uniqueRequestId = crypto.randomUUID();
    const selectionUuid = crypto.randomUUID();
    const timestamp = Date.now();

    // 构造请求URL
    const url = `https://www.pin880.com/bet-placement/buyV2?uniqueRequestId=${uniqueRequestId}&locale=en_US&_=${timestamp}&withCredentials=true`;

    // 构造POST数据
    const postData = {
        "acceptBetterOdds": true,
        "oddsFormat": 1,
        "selections": [
            {
                "odds": odds,
                "oddsId": oddsId,
                "selectionId": selectionId,
                "stake": stake,
                "winRiskStake": "RISK",
                "wagerType": "NORMAL",
                "uniqueRequestId": selectionUuid,
                "betLocationTracking": {
                    "mainPages": "SPORT",
                    "marketTab": "UNKNOWN",
                    "market": "UNKNOWN",
                    "view": "NEW_EUROPE_VIEW",
                    "navigation": "SPORTS",
                    "oddsContainerCategory": "MAIN",
                    "oddsContainerTitle": "UNKNOWN",
                    "marketType": "UNKNOWN",
                    "eventSorting": "UNKNOWN",
                    "pageType": "UNKNOWN",
                    "defaultPage": "UNKNOWN",
                    "reuseSelection": false,
                    "isLiveStreamPlaying": null,
                    "device": "DESKTOP",
                    "displayMode": "LIGHT",
                    "language": "en_US",
                    "timeZone": null
                }
            }
        ],
        "clientVersion": "master_2aea9aa3"
    };

    // ✅ 从 Local Storage 获取请求头参数
    const vHucode = localStorage.getItem('v-hucode') || '';
    const xAppDataRaw = localStorage.getItem('x-app-data') || '';
    const tokenStr = localStorage.getItem('token') || '{}';

    // 处理 x-app-data (可能是字符串或 JSON 对象)
    let xAppData = '';
    if (xAppDataRaw) {
        try {
            const parsed = JSON.parse(xAppDataRaw);
            if (typeof parsed === 'object' && parsed !== null) {
                xAppData = Object.entries(parsed)
                    .map(([key, value]) => `${key}=${value}`)
                    .join(';');
            } else {
                xAppData = String(parsed);
            }
        } catch (e) {
            xAppData = xAppDataRaw;
        }
    }

    // 解析 token JSON 对象
    let tokenObj = {};
    try {
        tokenObj = JSON.parse(tokenStr);
    } catch (e) {
        console.warn('⚠️ 解析 token 失败:', e);
    }

    // 提取 token 中的字段
    const xBrowserSessionId = tokenObj['X-Browser-Session-Id'] || '';
    const xCustid = tokenObj['X-Custid'] || '';
    const xLcu = tokenObj['X-Lcu'] || '';
    const xSlid = tokenObj['X-SLID'] || '';
    const xU = tokenObj['X-U'] || '';

    // 创建同步XHR请求
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url, false); // false = 同步请求
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');

    // ✅ 添加自定义请求头 (解决 400 错误的关键)
    if (vHucode) xhr.setRequestHeader('v-hucode', vHucode);
    if (xAppData) xhr.setRequestHeader('x-app-data', xAppData);
    if (xBrowserSessionId) xhr.setRequestHeader('x-browser-session-id', xBrowserSessionId);
    if (xCustid) xhr.setRequestHeader('x-custid', xCustid);
    if (xLcu) xhr.setRequestHeader('x-lcu', xLcu);
    if (xSlid) xhr.setRequestHeader('x-slid', xSlid);
    if (xU) xhr.setRequestHeader('x-u', xU);

    // 发送请求
    xhr.send(JSON.stringify(postData));

    // 返回响应结果
    return {
        status: xhr.status,
        statusText: xhr.statusText,
        response: xhr.responseText,
        headers: xhr.getAllResponseHeaders(),
        timestamp: new Date().toISOString(),
        requestData: {
            uniqueRequestId: uniqueRequestId,
            selectionUuid: selectionUuid,
            url: url,
            odds: odds,
            oddsId: oddsId,
            selectionId: selectionId,
            stake: stake
        }
    };

} catch (error) {
    console.error('RequestBuyV2错误:', error);
    return {
        error: error.message,
        status: 0,
        timestamp: new Date().toISOString()
    };
}
