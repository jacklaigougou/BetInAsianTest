let pageStatus = window.__pagestatus;

// 判断 pageStatus 是否为 undefined 或 null
if (pageStatus === undefined || pageStatus === null) {
    return false;
} else {
    return pageStatus;
}