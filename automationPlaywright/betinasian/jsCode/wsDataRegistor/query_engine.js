// 查询引擎
// 职责: 提供多维度查询接口,基于索引实现高效查询

class QueryEngine {
    // ========== Event 查询 ==========

    /**
     * 通过 event_key 获取事件
     * @param {string} eventKey
     * @returns {Object|undefined}
     */
    getEvent(eventKey) {
        return window.__eventsStore.get(eventKey);
    }

    /**
     * 按 sport_period 查询事件
     * @param {string} sportPeriod - 例如: "fb_ht", "basket_q1"
     * @returns {Array} 事件数组
     */
    getEventsBySport(sportPeriod) {
        const eventKeys = window.__eventsManager.getFromIndex('bySport', sportPeriod);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按 competition_id 查询事件
     * @param {number|string} competitionId
     * @returns {Array}
     */
    getEventsByCompetition(competitionId) {
        const eventKeys = window.__eventsManager.getFromIndex('byCompetition', competitionId);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按日期查询事件
     * @param {string} date - 格式: "YYYY-MM-DD"
     * @returns {Array}
     */
    getEventsByDate(date) {
        const eventKeys = window.__eventsManager.getFromIndex('byDate', date);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按 scope 查询事件
     * @param {string} scope - "MATCH" 或 "SEASON"
     * @returns {Array}
     */
    getEventsByScope(scope) {
        const eventKeys = window.__eventsManager.getFromIndex('byScope', scope);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按 period 查询事件
     * @param {string} period - "FT", "HT", "Q1", etc.
     * @returns {Array}
     */
    getEventsByPeriod(period) {
        const eventKeys = window.__eventsManager.getFromIndex('byPeriod', period);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按主队查询事件
     * @param {string} teamName
     * @returns {Array}
     */
    getEventsByHomeTeam(teamName) {
        const eventKeys = window.__eventsManager.getFromIndex('byHomeTeam', teamName);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按客队查询事件
     * @param {string} teamName
     * @returns {Array}
     */
    getEventsByAwayTeam(teamName) {
        const eventKeys = window.__eventsManager.getFromIndex('byAwayTeam', teamName);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按任意球队查询事件 (主队或客队)
     * @param {string} teamName
     * @returns {Array}
     */
    getEventsByTeam(teamName) {
        const homeKeys = window.__eventsManager.getFromIndex('byHomeTeam', teamName);
        const awayKeys = window.__eventsManager.getFromIndex('byAwayTeam', teamName);

        // 合并去重
        const allKeys = new Set([...homeKeys, ...awayKeys]);
        return this._resolveEvents(allKeys);
    }

    // ========== 新增: 比赛进行状态查询 ==========

    /**
     * 查询正在进行的比赛
     * @returns {Array}
     */
    getInRunningEvents() {
        const eventKeys = window.__eventsManager.getFromIndex('byInRunning', 'true');
        return this._resolveEvents(eventKeys);
    }

    /**
     * 查询未进行的比赛
     * @returns {Array}
     */
    getNotInRunningEvents() {
        const eventKeys = window.__eventsManager.getFromIndex('byInRunning', 'false');
        return this._resolveEvents(eventKeys);
    }

    // ========== 新增: 组合查询 ==========

    /**
     * 查询指定运动的正在进行的比赛
     * @param {string} sport - 例如: "basket", "fb"
     * @returns {Array}
     */
    getInRunningSportEvents(sport) {
        const key = `${sport}|true`;
        const eventKeys = window.__eventsManager.getFromIndex('bySportAndInRunning', key);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 查询指定运动的未进行的比赛
     * @param {string} sport - 例如: "basket", "fb"
     * @returns {Array}
     */
    getNotInRunningSportEvents(sport) {
        const key = `${sport}|false`;
        const eventKeys = window.__eventsManager.getFromIndex('bySportAndInRunning', key);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 查询指定运动+主队的比赛
     * @param {string} sport - 例如: "basket", "fb"
     * @param {string} homeTeam - 主队名称
     * @returns {Array}
     */
    getEventsBySportAndHome(sport, homeTeam) {
        const key = `${sport}|${homeTeam}`;
        const eventKeys = window.__eventsManager.getFromIndex('bySportAndHome', key);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 查询指定运动+客队的比赛
     * @param {string} sport - 例如: "basket", "fb"
     * @param {string} awayTeam - 客队名称
     * @returns {Array}
     */
    getEventsBySportAndAway(sport, awayTeam) {
        const key = `${sport}|${awayTeam}`;
        const eventKeys = window.__eventsManager.getFromIndex('bySportAndAway', key);
        return this._resolveEvents(eventKeys);
    }

    // ========== 组合查询 ==========

    /**
     * 多条件查询事件
     * @param {Object} conditions - 查询条件
     * @returns {Array}
     */
    queryEvents(conditions) {
        let candidateKeys = null;

        // 选择最小的索引作为起点
        if (conditions.sportPeriod) {
            candidateKeys = window.__eventsManager.getFromIndex('bySport', conditions.sportPeriod);
        } else if (conditions.date) {
            candidateKeys = window.__eventsManager.getFromIndex('byDate', conditions.date);
        } else if (conditions.competition_id) {
            candidateKeys = window.__eventsManager.getFromIndex('byCompetition', conditions.competition_id);
        } else if (conditions.home) {
            candidateKeys = window.__eventsManager.getFromIndex('byHomeTeam', conditions.home);
        } else if (conditions.scope) {
            candidateKeys = window.__eventsManager.getFromIndex('byScope', conditions.scope);
        } else {
            // 全表扫描
            return window.__eventsStore.getAll().filter(event => this._matchConditions(event, conditions));
        }

        // 过滤其他条件
        return this._resolveEvents(candidateKeys).filter(event => this._matchConditions(event, conditions));
    }

    /**
     * 自定义过滤事件
     * @param {Function} filterFn - 过滤函数
     * @returns {Array}
     */
    filterEvents(filterFn) {
        return window.__eventsStore.getAll().filter(filterFn);
    }

    // ========== 统计信息 ==========

    /**
     * 获取统计信息
     * @returns {Object}
     */
    getStats() {
        // 获取进行状态统计
        const inRunningStats = window.__eventsManager.getIndexStats('byInRunning');
        const inRunningCount = inRunningStats['true'] || 0;
        const notInRunningCount = inRunningStats['false'] || 0;

        return {
            totalEvents: window.__eventsStore.count(),
            totalOffers: window.__offersStore.count(),

            // 进行状态统计
            inRunningCount: inRunningCount,
            notInRunningCount: notInRunningCount,

            // 原有统计
            bySport: window.__eventsManager.getIndexStats('bySport'),
            byScope: window.__eventsManager.getIndexStats('byScope'),
            byPeriod: window.__eventsManager.getIndexStats('byPeriod'),
            byCompetition: window.__eventsManager.getIndexStats('byCompetition'),

            // 新增: 组合索引统计
            bySportAndInRunning: window.__eventsManager.getIndexStats('bySportAndInRunning')
        };
    }

    // ========== 内部辅助方法 ==========

    /**
     * 解析 event_keys 为 event 对象数组
     * @private
     */
    _resolveEvents(eventKeys) {
        const results = [];
        for (const key of eventKeys) {
            const event = window.__eventsStore.get(key);
            if (event) {
                results.push(event);
            }
        }
        return results;
    }

    /**
     * 检查 event 是否匹配所有条件
     * @private
     */
    _matchConditions(event, conditions) {
        for (const [key, value] of Object.entries(conditions)) {
            // 忽略特殊字段
            if (key === 'sportPeriod') continue;

            if (event[key] !== value) {
                return false;
            }
        }
        return true;
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__queryEngine = new QueryEngine();
}
