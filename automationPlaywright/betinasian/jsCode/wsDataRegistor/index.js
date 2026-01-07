// WebSocket 数据注册器 - 统一入口
// 职责: 初始化所有模块,提供全局 API

(function() {
    // 验证依赖是否加载
    const dependencies = [
        '__eventsStore',
        '__offersHcapStore',
        '__offersEventStore',
        '__eventsManager',
        '__offersHcapManager',
        '__offersEventManager',
        '__watchManager',
        '__subscriptionManager',
        '__eventHandler',
        '__offersHandler',
        '__apiHandler',
        '__messageRouter',
        '__queryEngine'
    ];

    for (const dep of dependencies) {
        if (!window[dep]) {
            return;
        }
    }

    // PMM module dependencies (optional, will be added later)
    const pmmDependencies = [
        'pmmStore',
        '__pmmHandler'
    ];

    let pmmAvailable = true;
    for (const dep of pmmDependencies) {
        if (!window[dep]) {
            pmmAvailable = false;
            break;
        }
    }

    if (pmmAvailable) {
        console.log('[DataRegistor] PMM module available');
    } else {
        console.warn('[DataRegistor] PMM module not available (will be loaded separately)');
    }

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

    // 保留已存在的 PMM 函数 (如果已经加载了 pmm_query.js)
    const existingPmmFunctions = window.queryData || {};

    window.queryData = {
        // 保留之前加载的 PMM 函数
        ...existingPmmFunctions,

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

        // ========== 新增: 比赛进行状态查询 ==========
        inRunning: () => window.__queryEngine.getInRunningEvents(),
        notInRunning: () => window.__queryEngine.getNotInRunningEvents(),

        // ========== 新增: 组合查询 ==========
        inRunningSport: (sport) => window.__queryEngine.getInRunningSportEvents(sport),
        notInRunningSport: (sport) => window.__queryEngine.getNotInRunningSportEvents(sport),
        bySportAndHome: (sport, home) => window.__queryEngine.getEventsBySportAndHome(sport, home),
        bySportAndAway: (sport, away) => window.__queryEngine.getEventsBySportAndAway(sport, away),

        // 多条件查询
        query: (conditions) => window.__queryEngine.queryEvents(conditions),

        // 自定义过滤
        filterEvents: (fn) => window.__queryEngine.filterEvents(fn),

        // ===== Offers Hcap 查询 =====

        // 获取某个 event 的所有 offers (hcap)
        offers: (eventKey) => window.__offersHcapManager.getOffers(eventKey),

        // 获取某个 event 的特定 offer (hcap)
        offer: (eventKey, offerType) => window.__offersHcapManager.getOffer(eventKey, offerType),

        // 解析赔率为字典格式 (hcap)
        parseOdds: (eventKey, offerType) => window.__offersHcapManager.parseOdds(eventKey, offerType),

        // 按 offer_type 查询所有相关 events (hcap)
        eventsByOfferType: (offerType) => window.__offersHcapManager.getEventsByOfferType(offerType),

        // ===== Offers Event 查询 =====

        // 获取某个 event 的所有 offers_event
        offersEvent: (eventKey) => window.__offersEventManager.getOffersEvent(eventKey),

        // 获取某个 event 的特定 offer_type 的所有 lines
        offerEventLines: (eventKey, offerType) => window.__offersEventManager.getOfferEventLines(eventKey, offerType),

        // 获取某个 event 的特定 line
        offerEventLine: (eventKey, offerType, lineId) => window.__offersEventManager.getOfferEventLine(eventKey, offerType, lineId),

        // 解析所有 lines 为字典格式
        parseAllOfferEventLines: (eventKey, offerType) => window.__offersEventManager.parseAllOfferEventLines(eventKey, offerType),

        // 解析特定 line 为字典格式
        parseOfferEventLine: (eventKey, offerType, lineId) => window.__offersEventManager.parseOfferEventLine(eventKey, offerType, lineId),

        // ===== Watch 管理 =====

        // 订阅 watch_event
        watch: (eventKey, sport, competitionId) => window.__watchManager.watch(eventKey, sport, competitionId),

        // 取消订阅
        unwatch: (eventKey, sport, competitionId) => window.__watchManager.unwatch(eventKey, sport, competitionId),

        // 检查是否已订阅
        isWatched: (eventKey) => window.__watchManager.isWatched(eventKey),

        // 获取所有已订阅事件
        getWatchedEvents: () => window.__watchManager.getWatchedEvents(),

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
     * 获取所有 offers_hcap 数据 (Map对象)
     * @returns {Map}
     */
    window.getOffersHcapData = function() {
        return window.__offersHcapStore.offersByEvent;
    };

    /**
     * 获取所有 offers_event 数据 (Map对象)
     * @returns {Map}
     */
    window.getOffersEventData = function() {
        return window.__offersEventStore.offersByEvent;
    };

    /**
     * 获取所有 offers 数据 (兼容旧版,返回 hcap)
     * @deprecated 请使用 getOffersHcapData 或 getOffersEventData
     * @returns {Map}
     */
    window.getOffersData = function() {
        return window.__offersHcapStore.offersByEvent;
    };

    /**
     * 获取所有 Events 索引
     * @returns {Object}
     */
    window.getEventsIndexes = function() {
        return window.__eventsManager.indexes;
    };

    /**
     * 获取所有 Offers Hcap 索引
     * @returns {Object}
     */
    window.getOffersHcapIndexes = function() {
        return window.__offersHcapManager.indexes;
    };

    /**
     * 获取所有 Offers Event 索引
     * @returns {Object}
     */
    window.getOffersEventIndexes = function() {
        return window.__offersEventManager.indexes;
    };

    /**
     * 获取所有 Offers 索引 (兼容旧版,返回 hcap)
     * @deprecated 请使用 getOffersHcapIndexes 或 getOffersEventIndexes
     * @returns {Object}
     */
    window.getOffersIndexes = function() {
        return window.__offersHcapManager.indexes;
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
        window.__offersHcapStore.clear();
        window.__offersEventStore.clear();
        window.__eventsManager.clear();
        window.__offersHcapManager.clear();
        window.__offersEventManager.clear();
        window.__watchManager.clear();
        window.__messageRouter.resetStats();
        window.__apiHandler.clearAll();
        window.__subscriptionManager.clearAll();
    };

    /**
     * 删除指定事件及其所有 offers
     * @param {string} eventKey
     * @returns {Object} {eventDeleted, offersHcapDeleted, offersEventDeleted}
     */
    window.deleteEvent = function(eventKey) {
        // 删除 event
        const eventDeleted = window.__eventsStore.delete(eventKey);

        // 删除相关 offers (两个存储)
        const offersHcapDeleted = window.__offersHcapStore.delete(eventKey);
        const offersEventDeleted = window.__offersEventStore.delete(eventKey);

        // TODO: 清理索引 (需要知道原始event的信息)

        return { eventDeleted, offersHcapDeleted, offersEventDeleted };
    };

    // ========== 全局 API: 订阅管理 ==========

    /**
     * 配置订阅策略
     * @param {Object} config - {sports: ['basket', 'fb'], autoSubscribeDelay: 10000}
     */
    window.configureSubscription = function(config) {
        if (window.__subscriptionManager) {
            window.__subscriptionManager.updateConfig(config);
            return true;
        }
        return false;
    };

    /**
     * 获取订阅统计信息
     */
    window.getSubscriptionStats = function() {
        return window.__subscriptionManager.getStats();
    };

    /**
     * 手动触发订阅
     */
    window.manualSubscribe = function() {
        return window.__subscriptionManager.subscribeCandidates();
    };

    /**
     * 检查事件是否已订阅
     */
    window.isWatched = function(eventKey) {
        return window.__subscriptionManager.isWatched(eventKey);
    };

})();
