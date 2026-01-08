// Events 索引管理器
// 职责: 管理 Events 的索引

class EventsManager {
    constructor() {
        // 所有索引都用 Map<key, Set<id>> 结构
        this.indexes = {
            // ========== Event 单维度索引 ==========

            // 按 sport_period 分组 (例如: "fb_ht", "basket_q1")
            bySport: new Map(),

            // 按 competition_id 分组
            byCompetition: new Map(),

            // 按日期分组 (例如: "2026-01-04")
            byDate: new Map(),

            // 按 scope 分组 ("MATCH", "SEASON")
            byScope: new Map(),

            // 按 period 分组 ("FT", "HT", "Q1", etc.)
            byPeriod: new Map(),

            // 按主队名称分组
            byHomeTeam: new Map(),

            // 按客队名称分组
            byAwayTeam: new Map(),

            // 按比赛进行状态分组 (true/false)
            byInRunning: new Map(),

            // ========== Event 组合索引 ==========

            // 组合索引: sport + inRunning (例如: "basket|true")
            bySportAndInRunning: new Map(),

            // 组合索引: sport + homeTeam (例如: "basket|Arsenal")
            bySportAndHome: new Map(),

            // 组合索引: sport + awayTeam (例如: "basket|Lakers")
            bySportAndAway: new Map()
        };
    }

    /**
     * 添加到指定索引
     * @param {string} indexName - 索引名称
     * @param {string} key - 索引键
     * @param {string} value - 要添加的值 (event_key 或 market_key)
     */
    addToIndex(indexName, key, value) {
        if (!this.indexes[indexName]) {
            console.warn(`[IndexManager] Unknown index: ${indexName}`);
            return;
        }

        if (!this.indexes[indexName].has(key)) {
            this.indexes[indexName].set(key, new Set());
        }

        this.indexes[indexName].get(key).add(value);
    }

    /**
     * 从指定索引移除
     * @param {string} indexName - 索引名称
     * @param {string} key - 索引键
     * @param {string} value - 要移除的值
     */
    removeFromIndex(indexName, key, value) {
        if (!this.indexes[indexName]) {
            return;
        }

        if (this.indexes[indexName].has(key)) {
            this.indexes[indexName].get(key).delete(value);

            // 如果 Set 为空,删除这个 key
            if (this.indexes[indexName].get(key).size === 0) {
                this.indexes[indexName].delete(key);
            }
        }
    }

    /**
     * 从指定索引获取值集合
     * @param {string} indexName - 索引名称
     * @param {string} key - 索引键
     * @returns {Set} 值集合
     */
    getFromIndex(indexName, key) {
        if (!this.indexes[indexName]) {
            return new Set();
        }
        return this.indexes[indexName].get(key) || new Set();
    }

    /**
     * 为 event 建立索引
     * @param {Object} event - 事件对象
     * @param {string} sportPeriod - sport_period 字符串 (例如: "fb_ht")
     */
    indexEvent(event, sportPeriod) {
        const eventKey = event.event_key;

        // 索引1: bySport (使用完整的 sport_period)
        if (sportPeriod) {
            this.addToIndex('bySport', String(sportPeriod), eventKey);
        }

        // 索引2: byCompetition (统一转为字符串)
        if (event.competition_id !== null && event.competition_id !== undefined) {
            this.addToIndex('byCompetition', String(event.competition_id), eventKey);
        }

        // 索引3: byDate (保持字符串)
        if (event.date) {
            this.addToIndex('byDate', String(event.date), eventKey);
        }

        // 索引4: byScope
        if (event.scope) {
            this.addToIndex('byScope', event.scope, eventKey);
        }

        // 索引5: byPeriod
        if (event.period) {
            this.addToIndex('byPeriod', event.period, eventKey);
        }

        // 索引6: byHomeTeam
        if (event.home) {
            this.addToIndex('byHomeTeam', event.home, eventKey);
        }

        // 索引7: byAwayTeam
        if (event.away) {
            this.addToIndex('byAwayTeam', event.away, eventKey);
        }

        // ========== 新增索引 ==========

        // 索引8: byInRunning
        if (event.isInRunning !== undefined) {
            this.addToIndex('byInRunning', event.isInRunning.toString(), eventKey);
        }

        // 索引9: bySportAndInRunning (sport + isInRunning)
        if (event.sport && event.isInRunning !== undefined) {
            const key = `${event.sport}|${event.isInRunning}`;
            this.addToIndex('bySportAndInRunning', key, eventKey);
        }

        // 索引10: bySportAndHome (sport + homeTeam)
        if (event.sport && event.home) {
            const key = `${event.sport}|${event.home}`;
            this.addToIndex('bySportAndHome', key, eventKey);
        }

        // 索引11: bySportAndAway (sport + awayTeam)
        if (event.sport && event.away) {
            const key = `${event.sport}|${event.away}`;
            this.addToIndex('bySportAndAway', key, eventKey);
        }
    }

    /**
     * 删除 event 的所有索引
     * @param {Object} event - 事件对象
     * @param {string} sportPeriod - sport_period 字符串
     */
    removeEventIndexes(event, sportPeriod) {
        const eventKey = event.event_key;

        if (sportPeriod) {
            this.removeFromIndex('bySport', String(sportPeriod), eventKey);
        }
        if (event.competition_id !== null && event.competition_id !== undefined) {
            this.removeFromIndex('byCompetition', String(event.competition_id), eventKey);
        }
        if (event.date) {
            this.removeFromIndex('byDate', String(event.date), eventKey);
        }
        if (event.scope) {
            this.removeFromIndex('byScope', event.scope, eventKey);
        }
        if (event.period) {
            this.removeFromIndex('byPeriod', event.period, eventKey);
        }
        if (event.home) {
            this.removeFromIndex('byHomeTeam', event.home, eventKey);
        }
        if (event.away) {
            this.removeFromIndex('byAwayTeam', event.away, eventKey);
        }

        // ========== 移除新增索引 ==========

        if (event.isInRunning !== undefined) {
            this.removeFromIndex('byInRunning', event.isInRunning.toString(), eventKey);
        }

        if (event.sport && event.isInRunning !== undefined) {
            const key = `${event.sport}|${event.isInRunning}`;
            this.removeFromIndex('bySportAndInRunning', key, eventKey);
        }

        if (event.sport && event.home) {
            const key = `${event.sport}|${event.home}`;
            this.removeFromIndex('bySportAndHome', key, eventKey);
        }

        if (event.sport && event.away) {
            const key = `${event.sport}|${event.away}`;
            this.removeFromIndex('bySportAndAway', key, eventKey);
        }
    }


    /**
     * 获取索引统计信息
     * @param {string} indexName - 索引名称
     * @returns {Object} 统计信息 {key: count}
     */
    getIndexStats(indexName) {
        const stats = {};
        if (this.indexes[indexName]) {
            for (const [key, set] of this.indexes[indexName]) {
                stats[key] = set.size;
            }
        }
        return stats;
    }

    /**
     * 清空所有索引
     */
    clearAll() {
        for (const indexMap of Object.values(this.indexes)) {
            indexMap.clear();
        }
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__eventsManager = new EventsManager();
}
