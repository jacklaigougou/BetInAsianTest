let orderInfo = window.__orderInfo;

// 判断 a 是否为 undefined 或 null
if (orderInfo === undefined || orderInfo === null) {
    return false;
} else {
    return orderInfo;
}