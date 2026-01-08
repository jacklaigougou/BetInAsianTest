// Watch Manager
// 职责: 管理 watch_event 订阅

class WatchManager {
    constructor() {
        // 已订阅的 event_keys
        this.watchedEvents = new Set();

        // 订阅历史
        this.watchHistory = [];
    }

    /**
     * 订阅 watch_event
     * @param {string} eventKey - 事件key
     * @param {string} sport - 运动类型 (如: "basket", "fb")
     * @param {number} competitionId - 联赛ID
     * @returns {boolean} 是否成功订阅
     */
    watch(eventKey, sport, competitionId) {
        // 检查是否已订阅
        if (this.watchedEvents.has(eventKey)) {
            console.log(`[WatchManager] 事件已订阅: ${eventKey}`);
            return false;
        }

        // 获取 WebSocket 实例
        const ws = window.getWebSocketInstance();
        if (!ws) {
            console.error('[WatchManager] WebSocket 实例未找到');
            return false;
        }

        // 构造 watch_event 消息
        const message = ["watch_event", [competitionId, sport, eventKey]];

        try {
            // 发送订阅消息
            ws.send(JSON.stringify(message));

            // 记录订阅
            this.watchedEvents.add(eventKey);
            this.watchHistory.push({
                eventKey,
                sport,
                competitionId,
                timestamp: Date.now()
            });

            console.log(`[WatchManager] 订阅成功: ${eventKey}`);
            return true;

        } catch (error) {
            console.error(`[WatchManager] 订阅失败: ${eventKey}`, error);
            return false;
        }
    }

    /**
     * 取消订阅 watch_event
     * @param {string} eventKey - 事件key
     * @param {string} sport - 运动类型
     * @param {number} competitionId - 联赛ID
     * @returns {boolean} 是否成功取消订阅
     */
    unwatch(eventKey, sport, competitionId) {
        // 检查是否已订阅
        if (!this.watchedEvents.has(eventKey)) {
            console.log(`[WatchManager] 事件未订阅: ${eventKey}`);
            return false;
        }

        // 获取 WebSocket 实例
        const ws = window.getWebSocketInstance();
        if (!ws) {
            console.error('[WatchManager] WebSocket 实例未找到');
            return false;
        }

        // 构造 unwatch_event 消息
        const message = ["unwatch_event", [competitionId, sport, eventKey]];

        try {
            // 发送取消订阅消息
            ws.send(JSON.stringify(message));

            // 移除订阅记录
            this.watchedEvents.delete(eventKey);

            console.log(`[WatchManager] 取消订阅成功: ${eventKey}`);
            return true;

        } catch (error) {
            console.error(`[WatchManager] 取消订阅失败: ${eventKey}`, error);
            return false;
        }
    }

    /**
     * 检查是否已订阅
     * @param {string} eventKey
     * @returns {boolean}
     */
    isWatched(eventKey) {
        return this.watchedEvents.has(eventKey);
    }

    /**
     * 获取所有已订阅的 event_keys
     * @returns {Array<string>}
     */
    getWatchedEvents() {
        return Array.from(this.watchedEvents);
    }

    /**
     * 获取订阅历史
     * @param {number} limit - 限制数量 (可选)
     * @returns {Array}
     */
    getWatchHistory(limit) {
        if (limit) {
            return this.watchHistory.slice(-limit);
        }
        return this.watchHistory;
    }

    /**
     * 获取统计信息
     * @returns {Object}
     */
    getStats() {
        return {
            currentWatched: this.watchedEvents.size,
            totalWatchHistory: this.watchHistory.length
        };
    }

    /**
     * 清空所有订阅
     */
    clear() {
        this.watchedEvents.clear();
        this.watchHistory = [];
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__watchManager = new WatchManager();
}
