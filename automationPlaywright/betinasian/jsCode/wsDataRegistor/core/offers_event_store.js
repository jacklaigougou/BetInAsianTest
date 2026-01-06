// Offers Event 数据存储
// 职责: 按 event_key 存储 offers_event 原始数据,支持深度合并

class OffersEventStore {
    constructor() {
        // 按 event_key 存储原始 offers_event 数据
        // event_key -> { event_key, raw_data, updateCount, firstUpdate, lastUpdate }
        this.offersByEvent = new Map();
    }

    /**
     * 更新/添加 offers_event 数据
     * @param {string} eventKey - 事件key
     * @param {Object} offersData - 原始 offers_event 数据对象
     * @returns {Object} 更新后的 offers 对象
     */
    update(eventKey, offersData) {
        const existing = this.offersByEvent.get(eventKey);

        if (!existing) {
            // 新建
            this.offersByEvent.set(eventKey, {
                event_key: eventKey,
                raw_data: offersData,  // 原始格式,不做转换
                updateCount: 1,
                firstUpdate: Date.now(),
                lastUpdate: Date.now()
            });
            return this.offersByEvent.get(eventKey);
        }

        // 深度合并每个 offer_type
        for (const [offerType, newLines] of Object.entries(offersData)) {
            const oldLines = existing.raw_data[offerType];

            if (!oldLines) {
                // 新的 offer_type,直接添加
                existing.raw_data[offerType] = newLines;
            } else {
                // 已有的 offer_type,深度合并 line_id 和 odds
                existing.raw_data[offerType] = this.mergeLines(oldLines, newLines);
            }
        }

        // 更新元数据
        existing.updateCount++;
        existing.lastUpdate = Date.now();

        return existing;
    }

    /**
     * 合并 lines (line_id 级别)
     * @param {Array} oldLines - 旧的 lines 数据: [[line_id, odds_array], ...]
     * @param {Array} newLines - 新的 lines 数据: [[line_id, odds_array], ...]
     * @returns {Array} 合并后的 lines
     */
    mergeLines(oldLines, newLines) {
        // 使用 Map 管理 line_id
        const lineMap = new Map();

        // 添加所有旧的 line_id
        for (const [lineId, oddsArray] of oldLines) {
            lineMap.set(lineId, oddsArray);
        }

        // 更新/添加新的 line_id (深度合并 odds)
        for (const [lineId, newOddsArray] of newLines) {
            if (lineMap.has(lineId)) {
                // line_id 已存在,深度合并 odds
                const oldOddsArray = lineMap.get(lineId);
                const mergedOdds = this.mergeOdds(oldOddsArray, newOddsArray);
                lineMap.set(lineId, mergedOdds);
            } else {
                // 新的 line_id,直接添加
                lineMap.set(lineId, newOddsArray);
            }
        }

        // 转换回数组格式
        return Array.from(lineMap);
    }

    /**
     * 合并 odds (odds 级别)
     * @param {Array} oldOdds - 旧的 odds: [["a", 1.877], ["h", 1.862], ...]
     * @param {Array} newOdds - 新的 odds: [["a", 1.888], ...]
     * @returns {Array} 合并后的 odds
     */
    mergeOdds(oldOdds, newOdds) {
        // 使用 Map 管理 odds
        const oddsMap = new Map(oldOdds);

        // 更新/添加新的 odds (新值覆盖旧值)
        for (const [side, value] of newOdds) {
            oddsMap.set(side, value);
        }

        // 转换回数组格式
        return Array.from(oddsMap);
    }

    /**
     * 获取某个 event 的 offers_event 数据
     * @param {string} eventKey
     * @returns {Object|undefined}
     */
    get(eventKey) {
        return this.offersByEvent.get(eventKey);
    }

    /**
     * 获取所有 offers_event 数据
     * @returns {Array}
     */
    getAll() {
        return Array.from(this.offersByEvent.values());
    }

    /**
     * 删除某个 event 的 offers_event 数据
     * @param {string} eventKey
     * @returns {boolean}
     */
    delete(eventKey) {
        return this.offersByEvent.delete(eventKey);
    }

    /**
     * 获取总数
     * @returns {number}
     */
    count() {
        return this.offersByEvent.size;
    }

    /**
     * 清空所有数据
     */
    clear() {
        this.offersByEvent.clear();
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__offersEventStore = new OffersEventStore();
}
