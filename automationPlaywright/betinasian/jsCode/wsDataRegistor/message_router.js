// 消息路由器
// 职责: 解析消息格式,根据消息类型分发到对应的 handler

class MessageRouter {
    constructor() {
        // 注册所有 handler
        this.handlers = {
            'event': window.__eventHandler,
            'offers_event': window.__offersHandler,
            'offers_hcaps': window.__offersHandler,
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
            // 1. 验证消息格式
            if (!this.validateMessage(message)) {
                console.warn('[Router] Invalid message format:', message);
                this.stats.errorCount++;
                return false;
            }

            // 2. 解析消息
            const [messageType, identifier, data] = message;
            const [sportPeriod, eventKey] = identifier;

            // 3. 统计
            if (!this.stats.byType[messageType]) {
                this.stats.byType[messageType] = 0;
            }
            this.stats.byType[messageType]++;

            // 4. 获取对应的 handler
            const handler = this.getHandler(messageType);
            if (!handler) {
                // 未注册的消息类型 (例如 watch_*)
                console.log(`[Router] No handler for type: ${messageType}`);
                return false;
            }

            // 5. 调用 handler 处理
            const success = handler.handle({
                type: messageType,
                sportPeriod,
                eventKey,
                data
            });

            if (success) {
                this.stats.successCount++;
            } else {
                this.stats.errorCount++;
            }

            return success;

        } catch (error) {
            console.error('[Router] Error routing message:', error, message);
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
