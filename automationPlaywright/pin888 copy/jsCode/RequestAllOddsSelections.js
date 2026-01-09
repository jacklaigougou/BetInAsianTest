// RequestAllOddsSelections.js - 获取所有赔率选项
// 通过同步XHR发送POST请求到pin888的member-betslip API

try {
    // 从Python传入的参数（通过模板替换）
    const timestamp = __TIMESTAMP__;
    const oddsId = __ODDS_ID__;
    const selectionId = __SELECTION_ID__;
    const oddsSelectionsType = __ODDS_SELECTIONS_TYPE__;

    // 构造请求URL
    const url = `https://www.pin880.com/member-betslip/v2/all-odds-selections?locale=en_US&_=${timestamp}&withCredentials=true`;

    // 构造POST数据
    const postData = {
        "oddsSelections": [
            {
                "oddsFormat": 1,
                "oddsId": oddsId,
                "oddsSelectionsType": oddsSelectionsType,
                "selectionId": selectionId
            }
        ]
    };

    // ✅ 从 Local Storage 获取请求头参数
    const vHucode = localStorage.getItem('v-hucode') || '';
    const xAppDataRaw = localStorage.getItem('x-app-data') || '';
    const tokenStr = localStorage.getItem('token') || '{}';

    // 处理 x-app-data (可能是字符串或 JSON 对象)
    let xAppData = '';
    if (xAppDataRaw) {
        // 尝试解析为 JSON（如果是对象格式）
        try {
            const parsed = JSON.parse(xAppDataRaw);
            // 如果解析成功且是对象，转换为分号分隔的字符串
            if (typeof parsed === 'object' && parsed !== null) {
                xAppData = Object.entries(parsed)
                    .map(([key, value]) => `${key}=${value}`)
                    .join(';');
            } else {
                xAppData = String(parsed);
            }
        } catch (e) {
            // 解析失败说明已经是字符串，直接使用
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
        timestamp: new Date().toISOString()
    };

} catch (error) {
    console.error('RequestAllOddsSelections错误:', error);
    return {
        error: error.message,
        status: 0,
        timestamp: new Date().toISOString()
    };
}