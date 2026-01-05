// Offers 数据存储
// 职责: 按 event_key 存储原始 offers 数据,支持智能更新

class OffersStore {
    constructor() {
        // 按 event_key 存储原始 offers 数据
        // event_key -> { event_key, raw_data, updateCount, firstUpdate, lastUpdate }
        this.offersByEvent = new Map();
    }

    /**
     * 更新/添加 offers 数据
     * @param {string} eventKey - 事件key
     * @param {Object} offersData - 原始 offers 数据对象
     * @returns {Object} 更新后的 offers 对象
     */
    update(eventKey, offersData) {
        const existing = this.offersByEvent.get(eventKey);

        if (existing) {
            // 获取新旧数据的键
            const oldKeys = Object.keys(existing.raw_data);
            const newKeys = Object.keys(offersData);

            // 比较键是否一致
            if (this.compareKeys(oldKeys, newKeys)) {
                // 键一致 → 整个替换(旧数据作废)
                existing.raw_data = offersData;
            } else {
                // 键不一致 → 合并(保留所有字段)
                Object.assign(existing.raw_data, offersData);
            }

            // 更新元数据
            existing.updateCount++;
            existing.lastUpdate = Date.now();
        } else {
            // 新建
            this.offersByEvent.set(eventKey, {
                event_key: eventKey,
                raw_data: offersData,  // 原始格式,不做转换
                updateCount: 1,
                firstUpdate: Date.now(),
                lastUpdate: Date.now()
            });
        }

        return this.offersByEvent.get(eventKey);
    }

    /**
     * 比较两组键是否一致
     * @param {Array} keys1
     * @param {Array} keys2
     * @returns {boolean}
     */
    compareKeys(keys1, keys2) {
        if (keys1.length !== keys2.length) return false;
        const set1 = new Set(keys1);
        const set2 = new Set(keys2);
        for (const key of set1) {
            if (!set2.has(key)) return false;
        }
        return true;
    }

    /**
     * 获取某个 event 的 offers 数据
     * @param {string} eventKey
     * @returns {Object|undefined}
     */
    get(eventKey) {
        return this.offersByEvent.get(eventKey);
    }

    /**
     * 获取所有 offers 数据
     * @returns {Array}
     */
    getAll() {
        return Array.from(this.offersByEvent.values());
    }

    /**
     * 删除某个 event 的 offers 数据
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
    window.__offersStore = new OffersStore();
}
