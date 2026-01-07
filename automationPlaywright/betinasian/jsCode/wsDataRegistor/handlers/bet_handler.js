/**
 * Bet Handler
 *
 * Listen to WebSocket ["bet", {...}] messages and store bet data
 *
 * Message format:
 * [["bet", {
 *     "id": "1a2ab5f0-2d76-49fb-96d8-9fbb3d3e3ac2",
 *     "order_id": "a018ad32-c9a2-42b3-87f3-e2bde91bc002",
 *     "event_id": "2026-01-06,41236,40814",
 *     "betslip_id": "f7c79ab3-e01b-4e6a-84ea-a4bdb3e2a55a",
 *     "bookie": "bf",
 *     "status": "MATCHED",
 *     "price": 1.009,
 *     "stake": 15,
 *     "placed_ts": 1736168085.421588,
 *     "matched_ts": 1736168085.459079,
 *     "matched_price": 1.009,
 *     "matched_stake": 15.0,
 *     "unmatched_stake": 0.0
 * }]]
 */

// Bet message handler
class BetHandler {
    constructor() {
        this.messageCount = 0;
        this.betCount = 0;
        this.recentMessages = [];  // Keep recent 10 messages for debugging
    }

    handleMessage(message) {
        try {
            // Check message format: [["bet", {...}]]
            if (!Array.isArray(message) || message.length === 0) {
                return;
            }

            const [msgType, msgData] = message[0];

            // Only handle "bet" messages
            if (msgType !== 'bet' || !msgData) {
                return;
            }

            this.messageCount++;
            this.processBet(msgData);

        } catch (error) {
            console.error('[Bet Handler] Error processing message:', error);
        }
    }

    processBet(betData) {
        // Validate required fields (handle both bet_id and id)
        const bet_id = betData.bet_id || betData.id;
        const order_id = betData.order_id;

        if (!bet_id || !order_id) {
            console.warn('[Bet Handler] Missing required fields:', betData);
            return null;
        }

        // Store to betStore (adapter is called inside)
        if (window.betStore && typeof window.betStore.storeBet === 'function') {
            const bet = window.betStore.storeBet(betData);

            if (bet) {
                this.betCount++;

                // KEY: Trigger bet → order aggregation
                // This is where "bet drives order state"
                this.updateRelatedOrder(bet.order_id);

                // Calculate slippage if matched
                const matchedStatuses = ['done', 'settled', 'MATCHED'];
                if (matchedStatuses.includes(bet.status) && bet.price && bet.matched_price) {
                    const slippage = window.betStore.calculateSlippage(bet.bet_id);
                    if (slippage && Math.abs(slippage.slippage) > 0.001) {
                        console.log(`[Bet Handler] Slippage detected: ${slippage.slippage_pct} for bet ${bet.bet_id}`);
                    }
                }

                // Keep recent messages for debugging
                this.recentMessages.push({
                    ts: Date.now(),
                    bet_id: bet.bet_id,
                    order_id: bet.order_id,
                    bookie: bet.bookie,
                    status: bet.status,
                    message: betData
                });

                if (this.recentMessages.length > 10) {
                    this.recentMessages.shift();
                }

                return bet;
            }
        } else {
            console.error('[Bet Handler] betStore not available');
        }

        return null;
    }

    updateRelatedOrder(order_id) {
        // KEY CHANGE: Use applyBetsToOrder instead of state machine directly
        // This aggregates all bets and then triggers state machine
        if (window.orderStore && typeof window.orderStore.applyBetsToOrder === 'function') {
            const updated = window.orderStore.applyBetsToOrder(order_id);
            if (updated) {
                console.log(`[Bet Handler] Order ${order_id} updated from bet aggregation`);
            }
        } else if (window.orderStore && window.orderStore.store.has(order_id)) {
            const order = window.orderStore.store.get(order_id);

            // Apply state machine transition
            if (window.orderStateMachine) {
                const result = window.orderStateMachine.transition(order);

                if (result.changed) {
                    console.log(`[Bet Handler] Order ${order_id}: ${result.oldState} → ${result.newState} (triggered by bet)`);
                }
            }
        }
    }

    getStats() {
        return {
            message_count: this.messageCount,
            bet_count: this.betCount,
            recent_messages: this.recentMessages.length
        };
    }
}

// Create handler instance
const betHandler = new BetHandler();

// Register to message router
if (window.__messageRouter) {
    window.__messageRouter.registerHandler('bet', (message) => {
        betHandler.handleMessage(message);
    });
    console.log('[Bet Handler] Registered to message router');
} else {
    console.warn('[Bet Handler] Message router not available, registering to global handler');

    // Fallback: listen to WebSocket messages directly
    if (window.__ws) {
        const originalOnMessage = window.__ws.onmessage;
        window.__ws.onmessage = function(event) {
            try {
                const message = JSON.parse(event.data);
                betHandler.handleMessage(message);
            } catch (e) {
                // Ignore parse errors
            }

            // Call original handler
            if (originalOnMessage) {
                originalOnMessage.call(window.__ws, event);
            }
        };
        console.log('[Bet Handler] Listening to WebSocket messages');
    }
}

// Export
window.__betHandler = betHandler;

console.log('[Bet Handler] Initialized');
