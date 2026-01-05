// Offers 索引管理器
// 职责: 管理 Offers 的索引,提供查询接口

class OffersManager {
    constructor() {
        // 索引结构
        this.indexes = {
            // event_key|offer_type -> event_key
            byEventOffer: new Map(),

            // offer_type -> Set(event_keys)
            byOfferType: new Map()
        };
    }

    /**
     * 为某个 event 的 offers 建立索引
     * @param {string} eventKey - 事件key
     * @param {Object} offersData - offers 数据对象
     */
    indexOffers(eventKey, offersData) {
        for (const offerType of Object.keys(offersData)) {
            // 索引1: byEventOffer
            const indexKey = `${eventKey}|${offerType}`;
            this.indexes.byEventOffer.set(indexKey, eventKey);

            // 索引2: byOfferType
            if (!this.indexes.byOfferType.has(offerType)) {
                this.indexes.byOfferType.set(offerType, new Set());
            }
            this.indexes.byOfferType.get(offerType).add(eventKey);
        }
    }

    /**
     * 获取某个 event 的所有 offers (原始格式)
     * @param {string} eventKey
     * @returns {Object|null} offers 数据对象,例如: {"ah": [20, [...]], "ahou": [632, [...]]}
     */
    getOffers(eventKey) {
        const data = window.__offersStore.get(eventKey);
        return data ? data.raw_data : null;
    }

    /**
     * 获取某个 event 的特定 offer
     * @param {string} eventKey
     * @param {string} offerType - 例如: "ah", "ahou", "ml"
     * @returns {Array|null} [line_id, odds_array],例如: [20, [["a", 1.877], ["h", 1.862]]]
     */
    getOffer(eventKey, offerType) {
        const offers = this.getOffers(eventKey);
        return offers ? offers[offerType] : null;
    }

    /**
     * 解析赔率为字典格式
     * @param {string} eventKey
     * @param {string} offerType
     * @returns {Object|null} { line_id: 20, odds: { "a": 1.877, "h": 1.862 } }
     */
    parseOdds(eventKey, offerType) {
        const offer = this.getOffer(eventKey, offerType);
        if (!offer) return null;

        const [lineId, oddsArray] = offer;
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
     * 检查某个 event 是否有特定 offer
     * @param {string} eventKey
     * @param {string} offerType
     * @returns {boolean}
     */
    hasOffer(eventKey, offerType) {
        const indexKey = `${eventKey}|${offerType}`;
        return this.indexes.byEventOffer.has(indexKey);
    }

    /**
     * 获取统计信息
     * @returns {Object}
     */
    getStats() {
        const stats = {
            totalEvents: window.__offersStore.count(),
            byOfferType: {}
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
        for (const offerType of Object.keys(offersData)) {
            const indexKey = `${eventKey}|${offerType}`;
            this.indexes.byEventOffer.delete(indexKey);

            if (this.indexes.byOfferType.has(offerType)) {
                this.indexes.byOfferType.get(offerType).delete(eventKey);
                if (this.indexes.byOfferType.get(offerType).size === 0) {
                    this.indexes.byOfferType.delete(offerType);
                }
            }
        }
    }

    /**
     * 清空所有索引
     */
    clear() {
        this.indexes.byEventOffer.clear();
        this.indexes.byOfferType.clear();
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__offersManager = new OffersManager();
}
