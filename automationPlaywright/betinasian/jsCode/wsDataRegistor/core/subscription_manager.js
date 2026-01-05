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
        this.watchedHcaps = new Map();     // event_key -> true (已订阅)

        // 候选列表
        this.candidates = [];              // 待订阅的 event 列表

        // 时间记录
        this.firstEventTime = null;        // 第一个符合条件的event时间
        this.subscribeTimer = null;        // 订阅定时器

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

        // 过滤4: 避免重复订阅
        if (this.watchedHcaps.has(event.event_key)) {
            return;
        }

        // 过滤5: 避免重复添加到候选列表
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
     * 批量订阅候选列表中的事件
     * @returns {Object} {success, failed, total}
     */
    subscribeCandidates() {
        if (this.candidates.length === 0) {
            return { success: 0, failed: 0, total: 0 };
        }

        // 构造 watch_hcaps 请求
        // 格式: ["watch_hcaps", [[competition_id, sport, event_key], ...]]
        const watchList = this.candidates.map(event => [
            event.competition_id,
            event.sport,        // "basket" (不带period)
            event.event_key
        ]);

        const message = ["watch_hcaps", watchList];

        // 发送请求
        const sent = window.sendWebSocketData(JSON.stringify(message));

        if (sent) {
            // 标记已订阅
            this.candidates.forEach(event => {
                this.watchedHcaps.set(event.event_key, true);
                this.stats.subscribed++;
            });

            const count = this.candidates.length;
            this.candidates = [];

            return { success: count, failed: 0, total: count };
        } else {
            return { success: 0, failed: this.candidates.length, total: this.candidates.length };
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
        return this.watchedHcaps.has(eventKey) && this.watchedHcaps.get(eventKey);
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
