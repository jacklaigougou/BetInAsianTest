// 设置请求参数到 window.__requestParams
// 参数通过占位符注入：__ODDS_ID__, __ODDS_SELECTIONS_TYPE__, __SELECTION_ID__, __GROUP_ID__

(function() {
    try {
        // 创建参数对象
        window.__requestParams = {
            odds_id: __ODDS_ID__,
            odds_selections_type: __ODDS_SELECTIONS_TYPE__,
            selection_id: __SELECTION_ID__,
            group_id: __GROUP_ID__,
            timestamp: new Date().getTime()
        };

        console.log('[PIN888] Request params stored:', window.__requestParams);

        return {
            success: true,
            data: window.__requestParams
        };
    } catch (error) {
        console.error('[PIN888] Error storing request params:', error);
        return {
            success: false,
            error: error.message
        };
    }
})();
