// WebSocket 数据注册器 - 统一入口
// 职责: 初始化所有模块,提供全局 API

(function() {
    console.log('[DataRegistor] Initializing...');

    // 验证依赖是否加载
    const dependencies = [
        '__eventsStore',
        '__marketsStore',
        '__indexManager',
        '__eventHandler',
        '__offersHandler',
        '__apiHandler',
        '__messageRouter',
        '__queryEngine'
    ];

    for (const dep of dependencies) {
        if (!window[dep]) {
            console.error(`[DataRegistor] Dependency not loaded: ${dep}`);
            return;
        }
    }

    console.log('[DataRegistor] All dependencies loaded successfully');

    // ========== 全局 API: 注册消息 ==========

    /**
     * 注册单条消息
     * @param {Array} message - WebSocket 消息
     * @returns {boolean} 处理是否成功
     */
    window.registerMessage = function(message) {
        return window.__messageRouter.route(message);
    };

    /**
     * 批量注册消息
     * @param {Array} messages - 消息数组
     * @returns {Object} {total, success, failed}
     */
    window.registerMessages = function(messages) {
        if (!Array.isArray(messages)) {
            console.warn('[DataRegistor] registerMessages expects an array');
            return { total: 0, success: 0, failed: 0 };
        }

        let successCount = 0;
        let failedCount = 0;

        for (const message of messages) {
            const success = window.registerMessage(message);
            if (success) {
                successCount++;
            } else {
                failedCount++;
            }
        }

        return {
            total: messages.length,
            success: successCount,
            failed: failedCount
        };
    };

    // ========== 全局 API: 查询数据 ==========

    window.queryData = {
        // ===== Event 查询 =====

        // 按 ID
        event: (eventKey) => window.__queryEngine.getEvent(eventKey),

        // 按单个维度
        bySport: (sportPeriod) => window.__queryEngine.getEventsBySport(sportPeriod),
        byCompetition: (competitionId) => window.__queryEngine.getEventsByCompetition(competitionId),
        byDate: (date) => window.__queryEngine.getEventsByDate(date),
        byScope: (scope) => window.__queryEngine.getEventsByScope(scope),
        byPeriod: (period) => window.__queryEngine.getEventsByPeriod(period),
        byHomeTeam: (team) => window.__queryEngine.getEventsByHomeTeam(team),
        byAwayTeam: (team) => window.__queryEngine.getEventsByAwayTeam(team),
        byTeam: (team) => window.__queryEngine.getEventsByTeam(team),

        // 多条件查询
        query: (conditions) => window.__queryEngine.queryEvents(conditions),

        // 自定义过滤
        filterEvents: (fn) => window.__queryEngine.filterEvents(fn),

        // ===== Market 查询 =====

        // 按 market_key
        market: (marketKey) => window.__queryEngine.getMarket(marketKey),

        // 按 event 查询
        marketsByEvent: (eventKey) => window.__queryEngine.getMarketsByEvent(eventKey),
        activeMarketsByEvent: (eventKey) => window.__queryEngine.getActiveMarketsByEvent(eventKey),

        // 按 market_group
        marketsByGroup: (marketGroup) => window.__queryEngine.getMarketsByGroup(marketGroup),

        // 赔率历史
        oddsHistory: (marketKey) => window.__queryEngine.getOddsHistory(marketKey),

        // 自定义过滤
        filterMarkets: (fn) => window.__queryEngine.filterMarkets(fn),

        // ===== 统计信息 =====
        stats: () => window.__queryEngine.getStats()
    };

    // ========== 全局 API: 直接访问原始数据 ==========

    /**
     * 获取所有 event 数据 (Map对象)
     * @returns {Map}
     */
    window.getEventsData = function() {
        return window.__eventsStore.eventsByKey;
    };

    /**
     * 获取所有 market 数据 (Map对象)
     * @returns {Map}
     */
    window.getMarketsData = function() {
        return window.__marketsStore.marketsByKey;
    };

    /**
     * 获取所有索引
     * @returns {Object}
     */
    window.getIndexes = function() {
        return window.__indexManager.indexes;
    };

    /**
     * 获取路由统计信息
     * @returns {Object}
     */
    window.getRouterStats = function() {
        return window.__messageRouter.getStats();
    };

    // ========== 全局 API: 数据管理 ==========

    /**
     * 清空所有数据
     */
    window.clearAllData = function() {
        window.__eventsStore.clear();
        window.__marketsStore.clear();
        window.__indexManager.clearAll();
        window.__messageRouter.resetStats();
        window.__apiHandler.clearAll();

        console.log('[DataRegistor] All data cleared');
    };

    /**
     * 删除指定事件及其所有市场
     * @param {string} eventKey
     * @returns {Object} {eventDeleted, marketsDeleted}
     */
    window.deleteEvent = function(eventKey) {
        // 删除 event
        const eventDeleted = window.__eventsStore.delete(eventKey);

        // 删除相关 markets
        const marketsDeleted = window.__marketsStore.deleteByEventKey(eventKey);

        // TODO: 清理索引 (需要知道原始event的信息)

        return { eventDeleted, marketsDeleted };
    };

    // ========== 初始化完成 ==========

    console.log('[DataRegistor] ✅ Initialization complete!');
    console.log('[DataRegistor] Available functions:');
    console.log('  ========== 数据注册 ==========');
    console.log('  - window.registerMessage(message)');
    console.log('  - window.registerMessages(messages)');
    console.log('');
    console.log('  ========== Event 查询 ==========');
    console.log('  - window.queryData.event(eventKey)');
    console.log('  - window.queryData.bySport(sportPeriod)');
    console.log('  - window.queryData.byCompetition(competitionId)');
    console.log('  - window.queryData.byDate(date)');
    console.log('  - window.queryData.byScope(scope)');
    console.log('  - window.queryData.byPeriod(period)');
    console.log('  - window.queryData.byHomeTeam(team)');
    console.log('  - window.queryData.byAwayTeam(team)');
    console.log('  - window.queryData.byTeam(team)');
    console.log('  - window.queryData.query(conditions)');
    console.log('  - window.queryData.filterEvents(fn)');
    console.log('');
    console.log('  ========== Market 查询 ==========');
    console.log('  - window.queryData.market(marketKey)');
    console.log('  - window.queryData.marketsByEvent(eventKey)');
    console.log('  - window.queryData.activeMarketsByEvent(eventKey)');
    console.log('  - window.queryData.marketsByGroup(marketGroup)');
    console.log('  - window.queryData.oddsHistory(marketKey)');
    console.log('  - window.queryData.filterMarkets(fn)');
    console.log('');
    console.log('  ========== 统计与管理 ==========');
    console.log('  - window.queryData.stats()');
    console.log('  - window.getRouterStats()');
    console.log('  - window.getEventsData()');
    console.log('  - window.getMarketsData()');
    console.log('  - window.getIndexes()');
    console.log('  - window.clearAllData()');
    console.log('  - window.deleteEvent(eventKey)');

})();
