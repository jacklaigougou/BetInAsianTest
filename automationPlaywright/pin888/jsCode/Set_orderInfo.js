// 接收 Python 传入的订单数据并存储到 window.__orderInfo
window.__orderInfo = JSON.parse(arguments[0]);
return true;
