// Request_myBets.js - 获取我的投注记录
// 通过同步XHR发送GET请求到pin888的member-service API

try {
    // 浏览器生成时间戳
    const timestamp = Date.now();

    // 构造请求URL
    const url = `https://www.pin880.com/member-service/v2/my-bets?locale=en_US&_=${timestamp}&withCredentials=true`;

    // ✅ 从 Local Storage 获取请求头参数
    const vHucode = localStorage.getItem('v-hucode') || '';
    const xAppDataRaw = localStorage.getItem('x-app-data') || '';
    const tokenStr = localStorage.getItem('token') || '{}';

    // 处理 x-app-data
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

    // 解析 token
    let tokenObj = {};
    try {
        tokenObj = JSON.parse(tokenStr);
    } catch (e) {
        console.warn('⚠️ 解析 token 失败:', e);
    }

    const xBrowserSessionId = tokenObj['X-Browser-Session-Id'] || '';
    const xCustid = tokenObj['X-Custid'] || '';
    const xLcu = tokenObj['X-Lcu'] || '';
    const xSlid = tokenObj['X-SLID'] || '';
    const xU = tokenObj['X-U'] || '';

    // 创建同步XHR请求
    const xhr = new XMLHttpRequest();
    xhr.open('GET', url, false); // false = 同步请求

    // ✅ 添加自定义请求头
    if (vHucode) xhr.setRequestHeader('v-hucode', vHucode);
    if (xAppData) xhr.setRequestHeader('x-app-data', xAppData);
    if (xBrowserSessionId) xhr.setRequestHeader('x-browser-session-id', xBrowserSessionId);
    if (xCustid) xhr.setRequestHeader('x-custid', xCustid);
    if (xLcu) xhr.setRequestHeader('x-lcu', xLcu);
    if (xSlid) xhr.setRequestHeader('x-slid', xSlid);
    if (xU) xhr.setRequestHeader('x-u', xU);

    // 发送请求
    xhr.send();

    // 返回响应结果
    return {
        status: xhr.status,
        statusText: xhr.statusText,
        response: xhr.responseText,
        headers: xhr.getAllResponseHeaders(),
        timestamp: new Date().toISOString()
    };

} catch (error) {
    console.error('Request_myBets错误:', error);
    return {
        error: error.message,
        status: 0,
        timestamp: new Date().toISOString()
    };
}

