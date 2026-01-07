// 消息路由器
// 职责: 解析消息格式,根据消息类型分发到对应的 handler

class MessageRouter {
    constructor() {
        // 注册所有 handler
        this.handlers = {
            'event': window.__eventHandler,
            'offers_event': window.__offersHandler,
            'offers_hcap': window.__offersHandler,
            'offers_odds': window.__offersHandler,
            'api_pmm': window.__apiHandler,
            'api': window.__apiHandler
        };

        // 消息计数
        this.stats = {
            totalMessages: 0,
            successCount: 0,
            errorCount: 0,
            byType: {}
        };
    }

    /**
     * 路由消息到对应的 handler
     * @param {Array} message - WebSocket 消息
     * @returns {boolean} 处理是否成功
     */
    route(message) {
        this.stats.totalMessages++;

        try {
            // ========== 特殊处理: API 消息 (包含 order/bet) ==========
            // API 消息格式: ["api", {ts: ..., data: [["order", {...}], ["bet", {...}]]}]
            if (Array.isArray(message) && message.length >= 2 && message[0] === 'api') {
                const [messageType, apiData] = message;

                // 统计
                if (!this.stats.byType[messageType]) {
                    this.stats.byType[messageType] = 0;
                }
                this.stats.byType[messageType]++;

                // 获取 API handler
                const handler = this.getHandler(messageType);
                if (!handler) {
                    this.stats.errorCount++;
                    return false;
                }

                // 直接传递 API 数据给 handler (handler 会自己解包)
                const success = handler.handle({
                    type: messageType,
                    sportPeriod: null,
                    eventKey: null,
                    data: apiData,
                    competitionId: null
                });

                if (success) {
                    this.stats.successCount++;
                } else {
                    this.stats.errorCount++;
                }

                return success;
            }

            // ========== 常规消息处理 ==========
            // 1. 验证消息格式
            if (!this.validateMessage(message)) {
                this.stats.errorCount++;
                return false;
            }

            // 2. 解析消息 (适配两种格式)
            const [messageType, identifier, data] = message;

            let sportPeriod, eventKey, competitionId;

            // 判断 identifier 格式
            if (identifier.length === 3) {
                // offers 类消息格式: [competition_id, sport, event_key]
                competitionId = identifier[0];
                const sport = identifier[1];
                eventKey = identifier[2];
                sportPeriod = sport;  // 使用 sport 作为 sportPeriod
            } else if (identifier.length === 2) {
                // event 类消息格式: [sport_period, event_key]
                sportPeriod = identifier[0];
                eventKey = identifier[1];
            } else {
                // 未知格式
                this.stats.errorCount++;
                return false;
            }

            // 3. 统计
            if (!this.stats.byType[messageType]) {
                this.stats.byType[messageType] = 0;
            }
            this.stats.byType[messageType]++;

            // 4. 获取对应的 handler
            const handler = this.getHandler(messageType);
            if (!handler) {
                // 未注册的消息类型 (例如 watch_*)
                return false;
            }

            // 5. 调用 handler 处理
            const success = handler.handle({
                type: messageType,
                sportPeriod,
                eventKey,
                data,
                competitionId  // 传递 competition_id (仅 offers 类消息有)
            });

            if (success) {
                this.stats.successCount++;
            } else {
                this.stats.errorCount++;
            }

            return success;

        } catch (error) {
            console.error('[Message Router] Error:', error);
            this.stats.errorCount++;
            return false;
        }
    }

    /**
     * 验证消息格式
     * @param {*} message
     * @returns {boolean}
     */
    validateMessage(message) {
        // 消息格式: [type, [sport_period, event_key], data]
        if (!Array.isArray(message)) {
            return false;
        }

        if (message.length < 3) {
            return false;
        }

        const [type, identifier, data] = message;

        if (typeof type !== 'string') {
            return false;
        }

        if (!Array.isArray(identifier) || identifier.length < 2) {
            return false;
        }

        if (typeof data !== 'object') {
            return false;
        }

        return true;
    }

    /**
     * 获取对应的 handler
     * @param {string} messageType
     * @returns {Object|null}
     */
    getHandler(messageType) {
        // 精确匹配
        if (this.handlers[messageType]) {
            return this.handlers[messageType];
        }

        // 前缀匹配 (例如: api_xxx → api)
        for (const [key, handler] of Object.entries(this.handlers)) {
            if (messageType.startsWith(key + '_') || messageType.startsWith(key + '/')) {
                return handler;
            }
        }

        return null;
    }

    /**
     * 注册新的 handler
     * @param {string} messageType
     * @param {Object} handler
     */
    registerHandler(messageType, handler) {
        this.handlers[messageType] = handler;
    }

    /**
     * 获取统计信息
     * @returns {Object}
     */
    getStats() {
        return {
            ...this.stats,
            successRate: this.stats.totalMessages > 0
                ? (this.stats.successCount / this.stats.totalMessages * 100).toFixed(2) + '%'
                : '0%'
        };
    }

    /**
     * 重置统计信息
     */
    resetStats() {
        this.stats = {
            totalMessages: 0,
            successCount: 0,
            errorCount: 0,
            byType: {}
        };
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__messageRouter = new MessageRouter();
}
