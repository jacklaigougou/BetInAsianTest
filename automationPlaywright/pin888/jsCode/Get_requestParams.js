// 获取 window.__requestParams
(function() {
    if (window.__requestParams) {
        return window.__requestParams;
    } else {
        console.warn('[PIN888] window.__requestParams not found');
        return null;
    }
})();
