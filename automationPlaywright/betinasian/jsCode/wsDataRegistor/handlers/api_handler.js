// API 消息处理器
// 职责: 处理 api/pmm 等 API 类消息

class ApiHandler {
    constructor() {
        // 独立的 API 数据存储
        this.apiDataByType = new Map();
    }

    /**
     * 处理 API 消息
     * @param {Object} params
     * @param {string} params.type - 消息类型
     * @param {string} params.sportPeriod - sport_period
     * @param {string} params.eventKey - 事件key
     * @param {Object} params.data - 消息数据
     * @returns {boolean} 处理是否成功
     */
    handle({ type, sportPeriod, eventKey, data }) {
        try {
            // 提取 API 类型 (例如: api_pmm → pmm)
            const apiType = type.replace('api_', '').replace('api/', '');

            // 存储数据
            if (!this.apiDataByType.has(apiType)) {
                this.apiDataByType.set(apiType, new Map());
            }

            const typeStore = this.apiDataByType.get(apiType);
            typeStore.set(eventKey, {
                event_key: eventKey,
                api_type: apiType,
                data: data,
                timestamp: Date.now()
            });

            return true;

        } catch (error) {
            return false;
        }
    }

    /**
     * 获取指定类型的 API 数据
     * @param {string} apiType - API类型
     * @param {string} eventKey - 事件key (可选)
     * @returns {*}
     */
    getData(apiType, eventKey = null) {
        const typeStore = this.apiDataByType.get(apiType);
        if (!typeStore) {
            return null;
        }

        if (eventKey) {
            return typeStore.get(eventKey);
        }

        // 返回该类型的所有数据
        return Array.from(typeStore.values());
    }

    /**
     * 清空指定类型的数据
     * @param {string} apiType
     */
    clear(apiType) {
        this.apiDataByType.delete(apiType);
    }

    /**
     * 清空所有 API 数据
     */
    clearAll() {
        this.apiDataByType.clear();
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__apiHandler = new ApiHandler();
}
