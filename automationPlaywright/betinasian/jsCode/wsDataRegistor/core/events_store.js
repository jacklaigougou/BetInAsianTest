// Event 主存储表
// 职责: 存储事件元数据,提供基本的 CRUD 操作

class EventsStore {
    constructor() {
        // 主存储: event_key -> EventMeta
        this.eventsByKey = new Map();
    }

    /**
     * 获取或创建事件
     * @param {string} eventKey - 事件唯一标识
     * @returns {Object} 事件对象
     */
    getOrCreate(eventKey) {
        if (!this.eventsByKey.has(eventKey)) {
            this.eventsByKey.set(eventKey, {
                event_key: eventKey,
                updateCount: 0,
                firstUpdate: Date.now(),
                lastUpdate: Date.now()
            });
        }
        return this.eventsByKey.get(eventKey);
    }

    /**
     * 更新事件数据
     * @param {string} eventKey - 事件唯一标识
     * @param {Object} updates - 要更新的字段
     * @returns {Object} 更新后的事件对象
     */
    update(eventKey, updates) {
        const event = this.getOrCreate(eventKey);

        // 合并更新数据
        Object.assign(event, updates);

        // 更新元数据
        event.updateCount++;
        event.lastUpdate = Date.now();

        return event;
    }

    /**
     * 获取单个事件
     * @param {string} eventKey - 事件唯一标识
     * @returns {Object|undefined} 事件对象
     */
    get(eventKey) {
        return this.eventsByKey.get(eventKey);
    }

    /**
     * 删除事件
     * @param {string} eventKey - 事件唯一标识
     * @returns {boolean} 是否删除成功
     */
    delete(eventKey) {
        return this.eventsByKey.delete(eventKey);
    }

    /**
     * 获取所有事件
     * @returns {Array} 事件数组
     */
    getAll() {
        return Array.from(this.eventsByKey.values());
    }

    /**
     * 获取事件总数
     * @returns {number}
     */
    count() {
        return this.eventsByKey.size;
    }

    /**
     * 清空所有事件
     */
    clear() {
        this.eventsByKey.clear();
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__eventsStore = new EventsStore();
}
