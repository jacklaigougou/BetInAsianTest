// Offers 消息处理器
// 职责: 处理 offers 消息,原样存储到 offers_store

class OffersHandler {
    constructor() {
        // 保存最近的消息样本用于调试
        this.recentMessages = [];
        this.maxSamples = 20;
    }

    /**
     * 处理 offers 消息
     * @param {Object} params
     * @param {string} params.type - 消息类型
     * @param {string} params.sportPeriod - sport_period
     * @param {string} params.eventKey - 事件key
     * @param {Object} params.data - 消息数据(原始格式)
     * @returns {boolean} 处理是否成功
     */
    handle({ type, sportPeriod, eventKey, data }) {
        try {
            // 1. 记录消息样本(调试用)
            this.recentMessages.push({
                type,
                sportPeriod,
                eventKey,
                data_keys: Object.keys(data),
                data: JSON.parse(JSON.stringify(data))  // 深拷贝
            });
            if (this.recentMessages.length > this.maxSamples) {
                this.recentMessages.shift();
            }

            // 2. 根据消息类型路由到不同的存储
            if (type === 'offers_event') {
                // offers_event → offers_event_store
                window.__offersEventStore.update(eventKey, data);
                window.__offersEventManager.indexOffersEvent(eventKey, data);
            } else {
                // offers_hcap / offers_odds → offers_hcap_store
                window.__offersHcapStore.update(eventKey, data);
                window.__offersHcapManager.indexOffers(eventKey, data);
            }

            return true;

        } catch (error) {
            return false;
        }
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__offersHandler = new OffersHandler();
}
