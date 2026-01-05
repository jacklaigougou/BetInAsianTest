// Offers 消息处理器
// 职责: 处理 offers_hcaps, offers_event 等盘口消息,直接覆盖更新 markets_store

class OffersHandler {
    /**
     * 处理 offers 消息
     * @param {Object} params
     * @param {string} params.type - 消息类型
     * @param {string} params.sportPeriod - sport_period
     * @param {string} params.eventKey - 事件key
     * @param {Object} params.data - 消息数据
     * @returns {boolean} 处理是否成功
     */
    handle({ type, sportPeriod, eventKey, data }) {
        try {
            // 1. 提取市场信息
            const marketGroup = data.market_group || data.market_type || 'unknown';
            const lineId = data.line_id || data.line || 'main';

            // 2. 构造 market 数据
            const marketData = {
                market_key: null,  // 由 store 自动生成
                event_key: eventKey,
                market_group: marketGroup,
                line_id: lineId,
                odds: data.odds || data.prices,
                status: data.status || 'open',
                handicap: data.handicap,
                line_value: data.line_value || data.line,
                total: data.total,
                period: this.extractPeriod(sportPeriod, data),
                market_type: data.market_type
            };

            // 3. 直接覆盖更新 markets_store
            const market = window.__marketsStore.update(
                eventKey,
                marketGroup,
                lineId,
                marketData
            );

            // 4. 建立索引
            window.__indexManager.indexMarket(market);

            return true;

        } catch (error) {
            return false;
        }
    }

    /**
     * 从 sport_period 或 data 中提取 period
     * @param {string} sportPeriod
     * @param {Object} data
     * @returns {string|null}
     */
    extractPeriod(sportPeriod, data) {
        // 优先从 data 中获取
        if (data.period) {
            return data.period.toUpperCase();
        }

        // 其次从 sport_period 推导
        const parts = sportPeriod.split('_');
        if (parts.length > 1) {
            return parts[1].toUpperCase();
        }

        return null;
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__offersHandler = new OffersHandler();
}
