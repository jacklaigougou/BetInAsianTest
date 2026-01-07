// Offers Event 索引管理器
// 职责: 管理 Offers Event 的索引,提供查询接口

class OffersEventManager {
    constructor() {
        // 索引结构
        this.indexes = {
            // event_key|offer_type|line_id -> event_key
            byEventOfferLine: new Map(),

            // offer_type -> Set(event_keys)
            byOfferType: new Map(),

            // event_key|offer_type -> Set(line_ids)
            byEventOffer: new Map()
        };
    }

    /**
     * 为某个 event 的 offers_event 建立索引
     * @param {string} eventKey - 事件key
     * @param {Object} offersData - offers_event 数据对象
     */
    indexOffersEvent(eventKey, offersData) {
        // 防御: 检查 offersData 是否为有效对象
        if (!offersData || typeof offersData !== 'object') {
            console.warn('[OffersEventManager] indexOffersEvent: invalid offersData', { eventKey, offersData });
            return;
        }

        for (const [offerType, lines] of Object.entries(offersData)) {
            // 防御: 检查 lines 是否为数组
            if (!Array.isArray(lines)) {
                console.warn('[OffersEventManager] indexOffersEvent: lines is not an array', { eventKey, offerType, lines });
                continue;
            }

            // 索引1: byOfferType
            if (!this.indexes.byOfferType.has(offerType)) {
                this.indexes.byOfferType.set(offerType, new Set());
            }
            this.indexes.byOfferType.get(offerType).add(eventKey);

            // 索引2: byEventOffer (存储 line_ids)
            const eventOfferKey = `${eventKey}|${offerType}`;
            if (!this.indexes.byEventOffer.has(eventOfferKey)) {
                this.indexes.byEventOffer.set(eventOfferKey, new Set());
            }

            // 索引3: byEventOfferLine (每个 line_id)
            for (const [lineId, oddsArray] of lines) {
                // 防御: 检查 oddsArray 是否为数组
                if (!Array.isArray(oddsArray)) {
                    console.warn('[OffersEventManager] indexOffersEvent: oddsArray is not an array', { eventKey, offerType, lineId, oddsArray });
                    continue;
                }

                const indexKey = `${eventKey}|${offerType}|${lineId}`;
                this.indexes.byEventOfferLine.set(indexKey, eventKey);
                this.indexes.byEventOffer.get(eventOfferKey).add(lineId);
            }
        }
    }

    /**
     * 获取某个 event 的所有 offers_event (原始格式)
     * @param {string} eventKey
     * @returns {Object|null} offers_event 数据对象,例如: {"ah": [[20, [...]], [22, [...]]], ...}
     */
    getOffersEvent(eventKey) {
        const data = window.__offersEventStore.get(eventKey);
        return data ? data.raw_data : null;
    }

    /**
     * 获取某个 event 的特定 offer_type 的所有 lines
     * @param {string} eventKey
     * @param {string} offerType - 例如: "ah", "ahou", "ml"
     * @returns {Array|null} [[line_id, odds_array], ...],例如: [[20, [["a", 1.877]]], [22, [["a", 1.888]]]]
     */
    getOfferEventLines(eventKey, offerType) {
        const offers = this.getOffersEvent(eventKey);
        return offers ? offers[offerType] : null;
    }

    /**
     * 获取某个 event 的特定 offer_type 的特定 line
     * @param {string} eventKey
     * @param {string} offerType
     * @param {number} lineId
     * @returns {Array|null} odds_array,例如: [["a", 1.877], ["h", 1.862]]
     */
    getOfferEventLine(eventKey, offerType, lineId) {
        const lines = this.getOfferEventLines(eventKey, offerType);
        if (!lines) return null;

        for (const [id, oddsArray] of lines) {
            if (id === lineId) {
                return oddsArray;
            }
        }
        return null;
    }

    /**
     * 解析所有 lines 为字典格式
     * @param {string} eventKey
     * @param {string} offerType
     * @returns {Array|null} [{ line_id: 20, odds: { "a": 1.877, "h": 1.862 } }, ...]
     */
    parseAllOfferEventLines(eventKey, offerType) {
        const lines = this.getOfferEventLines(eventKey, offerType);
        if (!lines) return null;

        const result = [];
        for (const [lineId, oddsArray] of lines) {
            const oddsDict = {};
            for (const [side, value] of oddsArray) {
                oddsDict[side] = value;
            }
            result.push({
                line_id: lineId,
                odds: oddsDict
            });
        }
        return result;
    }

    /**
     * 解析特定 line 为字典格式
     * @param {string} eventKey
     * @param {string} offerType
     * @param {number} lineId
     * @returns {Object|null} { line_id: 20, odds: { "a": 1.877, "h": 1.862 } }
     */
    parseOfferEventLine(eventKey, offerType, lineId) {
        const oddsArray = this.getOfferEventLine(eventKey, offerType, lineId);
        if (!oddsArray) return null;

        const oddsDict = {};
        for (const [side, value] of oddsArray) {
            oddsDict[side] = value;
        }

        return {
            line_id: lineId,
            odds: oddsDict
        };
    }

    /**
     * 按 offer_type 查询所有相关的 events
     * @param {string} offerType
     * @returns {Array<string>} event_keys 数组
     */
    getEventsByOfferType(offerType) {
        const eventKeys = this.indexes.byOfferType.get(offerType);
        return eventKeys ? Array.from(eventKeys) : [];
    }

    /**
     * 检查某个 event 是否有特定 offer_type
     * @param {string} eventKey
     * @param {string} offerType
     * @returns {boolean}
     */
    hasOfferType(eventKey, offerType) {
        const eventOfferKey = `${eventKey}|${offerType}`;
        return this.indexes.byEventOffer.has(eventOfferKey);
    }

    /**
     * 检查某个 event 的特定 offer_type 是否有特定 line_id
     * @param {string} eventKey
     * @param {string} offerType
     * @param {number} lineId
     * @returns {boolean}
     */
    hasLine(eventKey, offerType, lineId) {
        const indexKey = `${eventKey}|${offerType}|${lineId}`;
        return this.indexes.byEventOfferLine.has(indexKey);
    }

    /**
     * 获取某个 event 的特定 offer_type 的所有 line_ids
     * @param {string} eventKey
     * @param {string} offerType
     * @returns {Array<number>} line_ids 数组
     */
    getLineIds(eventKey, offerType) {
        const eventOfferKey = `${eventKey}|${offerType}`;
        const lineIds = this.indexes.byEventOffer.get(eventOfferKey);
        return lineIds ? Array.from(lineIds) : [];
    }

    /**
     * 获取统计信息
     * @returns {Object}
     */
    getStats() {
        const stats = {
            totalEvents: window.__offersEventStore.count(),
            byOfferType: {},
            totalLines: this.indexes.byEventOfferLine.size
        };

        for (const [offerType, eventKeys] of this.indexes.byOfferType) {
            stats.byOfferType[offerType] = eventKeys.size;
        }

        return stats;
    }

    /**
     * 移除某个 event 的索引
     * @param {string} eventKey
     * @param {Object} offersData
     */
    removeIndexes(eventKey, offersData) {
        // 防御: 检查 offersData 是否为有效对象
        if (!offersData || typeof offersData !== 'object') {
            console.warn('[OffersEventManager] removeIndexes: invalid offersData', { eventKey, offersData });
            return;
        }

        for (const [offerType, lines] of Object.entries(offersData)) {
            // 防御: 检查 lines 是否为数组
            if (!Array.isArray(lines)) {
                console.warn('[OffersEventManager] removeIndexes: lines is not an array', { eventKey, offerType, lines });
                continue;
            }

            // 移除 byOfferType
            if (this.indexes.byOfferType.has(offerType)) {
                this.indexes.byOfferType.get(offerType).delete(eventKey);
                if (this.indexes.byOfferType.get(offerType).size === 0) {
                    this.indexes.byOfferType.delete(offerType);
                }
            }

            // 移除 byEventOffer
            const eventOfferKey = `${eventKey}|${offerType}`;
            this.indexes.byEventOffer.delete(eventOfferKey);

            // 移除 byEventOfferLine
            for (const [lineId, oddsArray] of lines) {
                const indexKey = `${eventKey}|${offerType}|${lineId}`;
                this.indexes.byEventOfferLine.delete(indexKey);
            }
        }
    }

    /**
     * 清空所有索引
     */
    clear() {
        this.indexes.byEventOfferLine.clear();
        this.indexes.byOfferType.clear();
        this.indexes.byEventOffer.clear();
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__offersEventManager = new OffersEventManager();
}
