/**
 * PMM (Price Match Message) Handler
 *
 * Listen to WebSocket ["api", {...}] messages and extract pmm data
 *
 * Message format:
 * [["api", {
 *     "ts": 1767732155.791977,
 *     "data": [
 *         ["pmm", {
 *             "betslip_id": "xxx",
 *             "sport": "basket",
 *             "event_id": "2026-01-06,41236,40814",
 *             "bookie": "bf",
 *             "username": "_xxx_",
 *             "bet_type": "for,ml,a",
 *             "status": {"code": "success"},
 *             "price_list": [...]
 *         }],
 *         ["pmm", {...}],
 *         ...
 *     ]
 * }]]
 */

// PMM message handler
class PMMHandler {
    constructor() {
        this.messageCount = 0;
        this.pmmCount = 0;
        this.recentMessages = [];  // Keep recent 10 messages for debugging
    }

    handleMessage(message) {
        try {
            // Check message format: [["api", {...}]]
            if (!Array.isArray(message) || message.length === 0) {
                return;
            }

            const [msgType, msgData] = message[0];

            // Only handle "api" messages
            if (msgType !== 'api' || !msgData || !msgData.data) {
                return;
            }

            this.messageCount++;

            // Extract timestamp
            const ts = msgData.ts || (Date.now() / 1000);

            // Process each item in data array
            const { data } = msgData;
            let pmmCountInThisMessage = 0;

            for (const item of data) {
                if (!Array.isArray(item) || item.length < 2) continue;

                const [itemType, itemData] = item;

                // Only handle "pmm" items
                if (itemType === 'pmm' && itemData) {
                    this.processPMM(itemData, ts);
                    pmmCountInThisMessage++;
                    this.pmmCount++;
                }
            }

            if (pmmCountInThisMessage > 0) {
                // Keep recent messages for debugging
                this.recentMessages.push({
                    ts: ts,
                    pmm_count: pmmCountInThisMessage,
                    message: message
                });

                if (this.recentMessages.length > 10) {
                    this.recentMessages.shift();
                }

                console.log(`[PMM Handler] Processed ${pmmCountInThisMessage} pmm records (total: ${this.pmmCount})`);
            }

        } catch (error) {
            console.error('[PMM Handler] Error processing message:', error);
        }
    }

    processPMM(pmmData, ts) {
        // Add timestamp to pmmData
        pmmData.ts = ts;

        // Validate required fields
        if (!pmmData.betslip_id || !pmmData.bookie || !pmmData.event_id || !pmmData.bet_type) {
            console.warn('[PMM Handler] Missing required fields:', pmmData);
            return;
        }

        // Store to pmmStore
        if (window.pmmStore && typeof window.pmmStore.storePMM === 'function') {
            window.pmmStore.storePMM(pmmData);
        } else {
            console.error('[PMM Handler] pmmStore not available');
        }
    }

    getStats() {
        return {
            message_count: this.messageCount,
            pmm_count: this.pmmCount,
            recent_messages: this.recentMessages.length
        };
    }
}

// Create handler instance
const pmmHandler = new PMMHandler();

// Register to message router
if (window.__messageRouter) {
    window.__messageRouter.registerHandler('pmm', (message) => {
        pmmHandler.handleMessage(message);
    });
    console.log('[PMM Handler] Registered to message router');
} else {
    console.warn('[PMM Handler] Message router not available, registering to global handler');

    // Fallback: listen to WebSocket messages directly
    if (window.__ws) {
        const originalOnMessage = window.__ws.onmessage;
        window.__ws.onmessage = function(event) {
            try {
                const message = JSON.parse(event.data);
                pmmHandler.handleMessage(message);
            } catch (e) {
                // Ignore parse errors
            }

            // Call original handler
            if (originalOnMessage) {
                originalOnMessage.call(window.__ws, event);
            }
        };
        console.log('[PMM Handler] Listening to WebSocket messages');
    }
}

// Export
window.__pmmHandler = pmmHandler;

console.log('[PMM Handler] Initialized');
