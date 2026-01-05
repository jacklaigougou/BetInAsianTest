// Market 主存储表
// 职责: 存储盘口/赔率数据,支持直接覆盖更新

class MarketsStore {
    constructor() {
        // 主存储: market_key -> MarketState
        // market_key 格式: "event_key|market_group|line_id"
        this.marketsByKey = new Map();
    }

    /**
     * 构建 market_key
     * @param {string} eventKey - 事件key
     * @param {string} marketGroup - 市场分组
     * @param {string} lineId - 盘口ID
     * @returns {string} market_key
     */
    buildKey(eventKey, marketGroup, lineId) {
        return `${eventKey}|${marketGroup}|${lineId}`;
    }

    /**
     * 解析 market_key
     * @param {string} marketKey
     * @returns {Object} {eventKey, marketGroup, lineId}
     */
    parseKey(marketKey) {
        const [eventKey, marketGroup, lineId] = marketKey.split('|');
        return { eventKey, marketGroup, lineId };
    }

    /**
     * 获取或创建市场
     * @param {string} eventKey
     * @param {string} marketGroup
     * @param {string} lineId
     * @returns {Object} 市场对象
     */
    getOrCreate(eventKey, marketGroup, lineId) {
        const marketKey = this.buildKey(eventKey, marketGroup, lineId);

        if (!this.marketsByKey.has(marketKey)) {
            this.marketsByKey.set(marketKey, {
                market_key: marketKey,
                event_key: eventKey,
                market_group: marketGroup,
                line_id: lineId,
                odds: null,
                updateCount: 0,
                firstUpdate: Date.now(),
                lastUpdate: Date.now()
            });
        }

        return this.marketsByKey.get(marketKey);
    }

    /**
     * 更新市场数据 (智能合并策略)
     * @param {string} eventKey
     * @param {string} marketGroup
     * @param {string} lineId
     * @param {Object} updates - 要更新的数据
     * @returns {Object} 更新后的市场对象
     */
    update(eventKey, marketGroup, lineId, updates) {
        const market = this.getOrCreate(eventKey, marketGroup, lineId);

        // 获取新旧数据的有效字段(排除 null/undefined)
        const oldKeys = this.getValidKeys(market);
        const newKeys = this.getValidKeys(updates);

        // 检查数据项是否一致
        const keysMatch = this.compareKeys(oldKeys, newKeys);

        if (keysMatch) {
            // 数据项一致 → 直接替换,旧数据作废
            Object.assign(market, updates);
        } else {
            // 数据项不一致 → 合并,保留所有字段
            for (const [key, value] of Object.entries(updates)) {
                if (value !== null && value !== undefined) {
                    market[key] = value;
                }
            }
        }

        // 更新元数据
        market.updateCount++;
        market.lastUpdate = Date.now();

        return market;
    }

    /**
     * 获取对象中的有效键(值不为 null/undefined)
     * @param {Object} obj
     * @returns {Set<string>}
     */
    getValidKeys(obj) {
        const keys = new Set();
        for (const [key, value] of Object.entries(obj)) {
            // 跳过元数据字段
            if (['market_key', 'event_key', 'market_group', 'line_id',
                 'updateCount', 'firstUpdate', 'lastUpdate'].includes(key)) {
                continue;
            }
            // 只记录有效值
            if (value !== null && value !== undefined) {
                keys.add(key);
            }
        }
        return keys;
    }

    /**
     * 比较两组键是否一致
     * @param {Set<string>} keys1
     * @param {Set<string>} keys2
     * @returns {boolean}
     */
    compareKeys(keys1, keys2) {
        if (keys1.size !== keys2.size) return false;
        for (const key of keys1) {
            if (!keys2.has(key)) return false;
        }
        return true;
    }

    /**
     * 通过 market_key 获取市场
     * @param {string} marketKey
     * @returns {Object|undefined}
     */
    get(marketKey) {
        return this.marketsByKey.get(marketKey);
    }

    /**
     * 获取某个事件的所有市场
     * @param {string} eventKey
     * @returns {Array} 市场数组
     */
    getByEventKey(eventKey) {
        const results = [];
        for (const [key, market] of this.marketsByKey) {
            if (market.event_key === eventKey) {
                results.push(market);
            }
        }
        return results;
    }

    /**
     * 删除市场
     * @param {string} marketKey
     * @returns {boolean}
     */
    delete(marketKey) {
        return this.marketsByKey.delete(marketKey);
    }

    /**
     * 删除某个事件的所有市场
     * @param {string} eventKey
     * @returns {number} 删除的数量
     */
    deleteByEventKey(eventKey) {
        let count = 0;
        for (const [key, market] of this.marketsByKey) {
            if (market.event_key === eventKey) {
                this.marketsByKey.delete(key);
                count++;
            }
        }
        return count;
    }

    /**
     * 获取市场总数
     * @returns {number}
     */
    count() {
        return this.marketsByKey.size;
    }

    /**
     * 清空所有市场
     */
    clear() {
        this.marketsByKey.clear();
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__marketsStore = new MarketsStore();
}
