// 订阅管理器
// 职责: 管理 WebSocket 订阅请求,自动订阅符合条件的事件

class SubscriptionManager {
    constructor(config = {}) {
        // 配置项
        this.config = {
            sports: config.sports || ['basket'],           // 要订阅的运动列表
            autoSubscribeDelay: config.autoSubscribeDelay || 10000,  // 延迟订阅时间(毫秒)
            onlyNormalEvents: true                         // 只处理 event_type === 'normal'
        };

        // 订阅状态表
        this.watchedHcaps = new Map();     // event_key -> event对象 (当前已订阅)
        this.lastSubscribed = new Set();   // 上一次订阅的 event_key 列表

        // 候选列表
        this.candidates = [];              // 待订阅的 event 列表

        // 时间记录
        this.firstEventTime = null;        // 第一个符合条件的event时间
        this.subscribeTimer = null;        // 订阅定时器
        this.periodicTimer = null;         // 周期性检查定时器

        // 统计信息
        this.stats = {
            totalReceived: 0,              // 收到的event总数
            filteredOut: 0,                // 被过滤掉的数量
            addedToCandidates: 0,          // 添加到候选列表的数量
            subscribed: 0                  // 已订阅数量
        };
    }

    /**
     * 当收到新的 event 时调用此方法
     * @param {Object} event - 事件对象
     * @param {string} sportPeriod - sport_period (例如: "basket" 或 "basket_ht")
     */
    onEventReceived(event, sportPeriod) {
        this.stats.totalReceived++;

        // 过滤1: 只处理 normal 事件
        if (event.event_type !== 'normal') {
            this.stats.filteredOut++;
            return;
        }

        // 过滤2: 只处理配置的 sport
        if (!this.config.sports.includes(event.sport)) {
            this.stats.filteredOut++;
            return;
        }

        // 过滤3: 只订阅全场 (sportPeriod 不含下划线)
        if (sportPeriod.includes('_')) {
            this.stats.filteredOut++;
            return;
        }

        // 过滤4: 只订阅正在进行的比赛 (isInRunning === true)
        if (!event.isInRunning) {
            this.stats.filteredOut++;
            return;
        }

        // 过滤5: 避免重复订阅
        if (this.watchedHcaps.has(event.event_key)) {
            return;
        }

        // 过滤6: 避免重复添加到候选列表
        if (this.candidates.some(e => e.event_key === event.event_key)) {
            return;
        }

        // 添加到候选列表
        this.candidates.push(event);
        this.stats.addedToCandidates++;

        // 启动定时器 (仅首次)
        if (!this.firstEventTime) {
            this.firstEventTime = Date.now();
            this.scheduleSubscribe();
        }
    }

    /**
     * 启动延迟订阅定时器
     */
    scheduleSubscribe() {
        if (this.subscribeTimer) {
            return; // 定时器已启动
        }

        this.subscribeTimer = setTimeout(() => {
            this.subscribeCandidates();
        }, this.config.autoSubscribeDelay);
    }

    /**
     * 批量订阅候选列表中的事件 (自动增量订阅,只增不减)
     * @returns {Object} {watched, unwatched, total}
     */
    subscribeCandidates() {
        // 1. 计算需要新增订阅的事件 (只订阅新的,不退订旧的)
        const toWatch = this.candidates.filter(event =>
            !this.watchedHcaps.has(event.event_key)
        );

        let watchedCount = 0;

        // 2. 发送 watch_hcaps (订阅新的事件)
        if (toWatch.length > 0) {
            const watchList = toWatch.map(event => [
                event.competition_id,
                event.sport,
                event.event_key
            ]);

            const watchMessage = ["watch_hcaps", watchList];
            const watchSent = window.sendWebSocketData(JSON.stringify(watchMessage));

            if (watchSent) {
                watchedCount = toWatch.length;
                // 标记已订阅
                toWatch.forEach(event => {
                    this.watchedHcaps.set(event.event_key, event);
                    this.lastSubscribed.add(event.event_key);
                    this.stats.subscribed++;
                });
            }
        }

        // 3. 清空候选列表
        this.candidates = [];

        // 4. 启动周期性检查 (每30秒检查一次比赛状态变化)
        this.startPeriodicCheck();

        return {
            watched: watchedCount,
            unwatched: 0,
            total: watchedCount
        };
    }

    /**
     * 主动重新订阅指定的事件列表 (先退订所有,再订阅新的)
     * @param {Array} events - 要订阅的事件对象数组
     * @returns {Object} {watched, unwatched, total}
     */
    resubscribe(events) {
        let watchedCount = 0;
        let unwatchedCount = 0;

        // 1. 先退订所有当前订阅
        if (this.watchedHcaps.size > 0) {
            const unwatchList = Array.from(this.watchedHcaps.values()).map(event => [
                event.competition_id,
                event.sport,
                event.event_key
            ]);

            const unwatchMessage = ["unwatch_hcaps", unwatchList];
            const unwatchSent = window.sendWebSocketData(JSON.stringify(unwatchMessage));

            if (unwatchSent) {
                unwatchedCount = this.watchedHcaps.size;
                // 清空所有订阅记录
                this.watchedHcaps.clear();
                this.lastSubscribed.clear();
            }
        }

        // 2. 订阅新的事件列表
        if (events && events.length > 0) {
            const watchList = events.map(event => [
                event.competition_id,
                event.sport,
                event.event_key
            ]);

            const watchMessage = ["watch_hcaps", watchList];
            const watchSent = window.sendWebSocketData(JSON.stringify(watchMessage));

            if (watchSent) {
                watchedCount = events.length;
                // 标记已订阅
                events.forEach(event => {
                    this.watchedHcaps.set(event.event_key, event);
                    this.lastSubscribed.add(event.event_key);
                    this.stats.subscribed++;
                });
            }
        }

        return {
            watched: watchedCount,
            unwatched: unwatchedCount,
            total: watchedCount + unwatchedCount
        };
    }

    /**
     * 启动周期性检查 (检查比赛状态变化)
     */
    startPeriodicCheck() {
        // 如果已经有定时器在运行,不重复启动
        if (this.periodicTimer) {
            return;
        }

        this.periodicTimer = setInterval(() => {
            this.checkAndUpdateSubscriptions();
        }, 30000); // 每30秒检查一次
    }

    /**
     * 检查并更新订阅 (只检测新加入的正在进行的比赛)
     */
    checkAndUpdateSubscriptions() {
        // 从 eventsStore 中重新查询正在进行的篮球比赛
        const inRunningEvents = window.queryData.inRunningSport('basket');

        // 清空候选列表
        this.candidates = [];

        // 只添加尚未订阅的新比赛到候选列表
        inRunningEvents.forEach(event => {
            // 检查是否是全场盘 (不含下划线)
            if (event.period === null) {
                // 只添加尚未订阅的事件
                if (!this.watchedHcaps.has(event.event_key)) {
                    this.candidates.push(event);
                }
            }
        });

        // 如果有新比赛,执行增量订阅
        if (this.candidates.length > 0) {
            this.subscribeCandidates();
        }
    }

    /**
     * 更新配置 (供 Python 调用)
     * @param {Object} newConfig
     */
    updateConfig(newConfig) {
        Object.assign(this.config, newConfig);
    }

    /**
     * 检查事件是否已订阅
     * @param {string} eventKey
     * @returns {boolean}
     */
    isWatched(eventKey) {
        return this.watchedHcaps.has(eventKey);
    }

    /**
     * 获取统计信息
     * @returns {Object}
     */
    getStats() {
        return {
            ...this.stats,
            pendingCandidates: this.candidates.length,
            watchedCount: this.watchedHcaps.size,
            firstEventTime: this.firstEventTime ? new Date(this.firstEventTime).toISOString() : null,
            configuredSports: this.config.sports,
            autoSubscribeDelay: this.config.autoSubscribeDelay
        };
    }

    /**
     * 重置统计信息
     */
    resetStats() {
        this.stats = {
            totalReceived: 0,
            filteredOut: 0,
            addedToCandidates: 0,
            subscribed: 0
        };
    }

    /**
     * 清空所有订阅状态
     */
    clearAll() {
        this.watchedHcaps.clear();
        this.lastSubscribed.clear();
        this.candidates = [];
        this.firstEventTime = null;
        if (this.subscribeTimer) {
            clearTimeout(this.subscribeTimer);
            this.subscribeTimer = null;
        }
        this.resetStats();
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__subscriptionManager = new SubscriptionManager();
}
