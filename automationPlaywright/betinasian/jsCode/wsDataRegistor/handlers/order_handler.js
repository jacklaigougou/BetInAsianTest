/**
 * Order Handler
 *
 * Listen to WebSocket ["order", {...}] messages and store order data
 *
 * Message format:
 * [["order", {
 *     "id": "a018ad32-c9a2-42b3-87f3-e2bde91bc002",
 *     "event_id": "2026-01-06,41236,40814",
 *     "betslip_id": "f7c79ab3-e01b-4e6a-84ea-a4bdb3e2a55a",
 *     "status": "OPEN",
 *     "duration": 10,
 *     "created_at": 1736168085.2664988,
 *     "bookie": null,
 *     "price": null,
 *     "stake": null,
 *     "success": [],
 *     "inprogress": [["bf", 15]],
 *     "danger": [],
 *     "unplaced": []
 * }]]
 */

// Order message handler
class OrderHandler {
    constructor() {
        this.messageCount = 0;
        this.orderCount = 0;
        this.recentMessages = [];  // Keep recent 10 messages for debugging
    }

    handleMessage(message) {
        try {
            // Check message format: [["order", {...}]]
            if (!Array.isArray(message) || message.length === 0) {
                return;
            }

            const [msgType, msgData] = message[0];

            // Only handle "order" messages
            if (msgType !== 'order' || !msgData) {
                return;
            }

            this.messageCount++;
            this.processOrder(msgData);

        } catch (error) {
            console.error('[Order Handler] Error processing message:', error);
        }
    }

    processOrder(orderData) {
        // Validate required fields
        if (!orderData.id || !orderData.event_id) {
            console.warn('[Order Handler] Missing required fields:', orderData);
            return;
        }

        // Store to orderStore (state machine is called inside storeOrder)
        if (window.orderStore && typeof window.orderStore.storeOrder === 'function') {
            const order = window.orderStore.storeOrder(orderData);

            if (order) {
                this.orderCount++;

                // Keep recent messages for debugging
                this.recentMessages.push({
                    ts: Date.now(),
                    order_id: order.order_id,
                    status: order.status,
                    message: orderData
                });

                if (this.recentMessages.length > 10) {
                    this.recentMessages.shift();
                }
            }
        } else {
            console.error('[Order Handler] orderStore not available');
        }
    }

    getStats() {
        return {
            message_count: this.messageCount,
            order_count: this.orderCount,
            recent_messages: this.recentMessages.length
        };
    }
}

// Create handler instance
const orderHandler = new OrderHandler();

// Register to message router
if (window.__messageRouter) {
    window.__messageRouter.registerHandler('order', (message) => {
        orderHandler.handleMessage(message);
    });
    console.log('[Order Handler] Registered to message router');
} else {
    console.warn('[Order Handler] Message router not available, registering to global handler');

    // Fallback: listen to WebSocket messages directly
    if (window.__ws) {
        const originalOnMessage = window.__ws.onmessage;
        window.__ws.onmessage = function(event) {
            try {
                const message = JSON.parse(event.data);
                orderHandler.handleMessage(message);
            } catch (e) {
                // Ignore parse errors
            }

            // Call original handler
            if (originalOnMessage) {
                originalOnMessage.call(window.__ws, event);
            }
        };
        console.log('[Order Handler] Listening to WebSocket messages');
    }
}

// Export
window.__orderHandler = orderHandler;

console.log('[Order Handler] Initialized');
