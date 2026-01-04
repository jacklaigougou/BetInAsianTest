// Market 主存储表
// 职责: 存储盘口/赔率数据,支持直接覆盖更新

class MarketsStore {
    constructor() {
        // 主存储: market_key -> MarketState
        // market_key 格式: "event_key|market_group|line_id"
        this.marketsByKey = new Map();

        // 配置项
        this.config = {
            keepHistory: true,           // 是否保留赔率历史
            maxHistoryLength: 20         // 最大历史记录数
        };
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
                oddsHistory: [],
                updateCount: 0,
                firstUpdate: Date.now(),
                lastUpdate: Date.now()
            });
        }

        return this.marketsByKey.get(marketKey);
    }

    /**
     * 更新市场数据 (直接覆盖)
     * @param {string} eventKey
     * @param {string} marketGroup
     * @param {string} lineId
     * @param {Object} updates - 要更新的数据
     * @returns {Object} 更新后的市场对象
     */
    update(eventKey, marketGroup, lineId, updates) {
        const market = this.getOrCreate(eventKey, marketGroup, lineId);

        // 保存赔率历史 (可选)
        if (this.config.keepHistory && updates.odds && market.odds) {
            market.oddsHistory.push({
                timestamp: market.lastUpdate,
                odds: JSON.parse(JSON.stringify(market.odds))  // 深拷贝
            });

            // 限制历史记录长度
            if (market.oddsHistory.length > this.config.maxHistoryLength) {
                market.oddsHistory.shift();
            }
        }

        // 直接覆盖更新 (关键设计!)
        Object.assign(market, updates);

        // 更新元数据
        market.updateCount++;
        market.lastUpdate = Date.now();

        return market;
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
