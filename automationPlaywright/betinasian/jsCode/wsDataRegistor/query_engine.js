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
        const eventKeys = window.__indexManager.getFromIndex('bySport', sportPeriod);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按 competition_id 查询事件
     * @param {number|string} competitionId
     * @returns {Array}
     */
    getEventsByCompetition(competitionId) {
        const eventKeys = window.__indexManager.getFromIndex('byCompetition', competitionId);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按日期查询事件
     * @param {string} date - 格式: "YYYY-MM-DD"
     * @returns {Array}
     */
    getEventsByDate(date) {
        const eventKeys = window.__indexManager.getFromIndex('byDate', date);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按 scope 查询事件
     * @param {string} scope - "MATCH" 或 "SEASON"
     * @returns {Array}
     */
    getEventsByScope(scope) {
        const eventKeys = window.__indexManager.getFromIndex('byScope', scope);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按 period 查询事件
     * @param {string} period - "FT", "HT", "Q1", etc.
     * @returns {Array}
     */
    getEventsByPeriod(period) {
        const eventKeys = window.__indexManager.getFromIndex('byPeriod', period);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按主队查询事件
     * @param {string} teamName
     * @returns {Array}
     */
    getEventsByHomeTeam(teamName) {
        const eventKeys = window.__indexManager.getFromIndex('byHomeTeam', teamName);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按客队查询事件
     * @param {string} teamName
     * @returns {Array}
     */
    getEventsByAwayTeam(teamName) {
        const eventKeys = window.__indexManager.getFromIndex('byAwayTeam', teamName);
        return this._resolveEvents(eventKeys);
    }

    /**
     * 按任意球队查询事件 (主队或客队)
     * @param {string} teamName
     * @returns {Array}
     */
    getEventsByTeam(teamName) {
        const homeKeys = window.__indexManager.getFromIndex('byHomeTeam', teamName);
        const awayKeys = window.__indexManager.getFromIndex('byAwayTeam', teamName);

        // 合并去重
        const allKeys = new Set([...homeKeys, ...awayKeys]);
        return this._resolveEvents(allKeys);
    }

    // ========== Market 查询 ==========

    /**
     * 通过 market_key 获取市场
     * @param {string} marketKey
     * @returns {Object|undefined}
     */
    getMarket(marketKey) {
        return window.__marketsStore.get(marketKey);
    }

    /**
     * 获取指定事件的所有市场
     * @param {string} eventKey
     * @returns {Array}
     */
    getMarketsByEvent(eventKey) {
        return window.__marketsStore.getByEventKey(eventKey);
    }

    /**
     * 获取指定事件的活跃市场
     * @param {string} eventKey
     * @returns {Array}
     */
    getActiveMarketsByEvent(eventKey) {
        const marketKeys = window.__indexManager.getFromIndex('activeLinesByEvent', eventKey);
        return this._resolveMarkets(marketKeys);
    }

    /**
     * 按 market_group 查询市场
     * @param {string} marketGroup - 例如: "ahou", "1x2"
     * @returns {Array}
     */
    getMarketsByGroup(marketGroup) {
        const marketKeys = window.__indexManager.getFromIndex('byMarketGroup', marketGroup);
        return this._resolveMarkets(marketKeys);
    }

    /**
     * 获取指定市场的赔率历史
     * @param {string} marketKey
     * @returns {Array}
     */
    getOddsHistory(marketKey) {
        const market = window.__marketsStore.get(marketKey);
        return market ? market.oddsHistory : [];
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
            candidateKeys = window.__indexManager.getFromIndex('bySport', conditions.sportPeriod);
        } else if (conditions.date) {
            candidateKeys = window.__indexManager.getFromIndex('byDate', conditions.date);
        } else if (conditions.competition_id) {
            candidateKeys = window.__indexManager.getFromIndex('byCompetition', conditions.competition_id);
        } else if (conditions.home) {
            candidateKeys = window.__indexManager.getFromIndex('byHomeTeam', conditions.home);
        } else if (conditions.scope) {
            candidateKeys = window.__indexManager.getFromIndex('byScope', conditions.scope);
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

    /**
     * 自定义过滤市场
     * @param {Function} filterFn - 过滤函数
     * @returns {Array}
     */
    filterMarkets(filterFn) {
        return Array.from(window.__marketsStore.marketsByKey.values()).filter(filterFn);
    }

    // ========== 统计信息 ==========

    /**
     * 获取统计信息
     * @returns {Object}
     */
    getStats() {
        return {
            totalEvents: window.__eventsStore.count(),
            totalMarkets: window.__marketsStore.count(),
            bySport: window.__indexManager.getIndexStats('bySport'),
            byScope: window.__indexManager.getIndexStats('byScope'),
            byPeriod: window.__indexManager.getIndexStats('byPeriod'),
            byCompetition: window.__indexManager.getIndexStats('byCompetition'),
            byMarketGroup: window.__indexManager.getIndexStats('byMarketGroup')
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
     * 解析 market_keys 为 market 对象数组
     * @private
     */
    _resolveMarkets(marketKeys) {
        const results = [];
        for (const key of marketKeys) {
            const market = window.__marketsStore.get(key);
            if (market) {
                results.push(market);
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
