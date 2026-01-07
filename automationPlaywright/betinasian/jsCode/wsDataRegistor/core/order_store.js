/**
 * Order Store
 *
 * Store structure + Indexes + Expiry Queue + State Machine Integration
 *
 * Features:
 * - Idempotent upsert (message replay safe)
 * - Minimal fact storage (no computed fields)
 * - State machine integration (raw_status → state)
 * - Timeout detection with grace period
 * - Closed order protection
 *
 * Field design:
 * - raw_status: Upstream status ("open", "reconciled", etc.)
 * - state: State machine state (CREATED, OPEN, PLACED, FINISHED, EXPIRED_LOCAL)
 * - closed: Upstream closed flag
 * - close_reason: Upstream close reason
 */

// ==================== Config ====================
const ORDER_TIMEOUT_GRACE_MS = 2000;  // 2 seconds grace period after duration expires

// ==================== Store ====================
const orderStore = new Map();  // order_id → OrderData

// ==================== Indexes ====================
const indexes = {
    byState: new Map(),        // state → Set(order_ids) [use state, not raw_status]
    byEvent: new Map(),        // event_id → Set(order_ids)
    byBookie: new Map(),       // bookie → Set(order_ids)
};

// ==================== Expiry Queue (Min-Heap) ====================
class ExpiryQueue {
    constructor() {
        this.heap = [];  // {expires_at, order_id, version}
        this.versionMap = new Map();  // order_id → version
    }

    push(order_id, expires_at) {
        // Increment version to identify old entries
        const version = (this.versionMap.get(order_id) || 0) + 1;
        this.versionMap.set(order_id, version);

        this.heap.push({ expires_at, order_id, version });
        this._bubbleUp(this.heap.length - 1);
    }

    cleanExpired(now) {
        const expired = [];

        while (this.heap.length > 0 && this.heap[0].expires_at < now) {
            const entry = this._extractMin();

            // Verify version to prevent deleting updated records
            const currentVersion = this.versionMap.get(entry.order_id);
            if (currentVersion !== entry.version) {
                continue;  // Old entry, skip
            }

            // Verify record is actually expired
            const order = orderStore.get(entry.order_id);
            if (order && order.expires_at === entry.expires_at) {
                // Mark as EXPIRED_LOCAL
                markOrderExpired(entry.order_id);
                expired.push(entry.order_id);
            }
        }

        return expired;
    }

    remove(order_id) {
        // Increment version to invalidate old entries
        const version = (this.versionMap.get(order_id) || 0) + 1;
        this.versionMap.set(order_id, version);
    }

    _bubbleUp(index) {
        while (index > 0) {
            const parent = Math.floor((index - 1) / 2);
            if (this.heap[parent].expires_at <= this.heap[index].expires_at) break;
            [this.heap[parent], this.heap[index]] = [this.heap[index], this.heap[parent]];
            index = parent;
        }
    }

    _extractMin() {
        const min = this.heap[0];
        const last = this.heap.pop();
        if (this.heap.length > 0) {
            this.heap[0] = last;
            this._sinkDown(0);
        }
        return min;
    }

    _sinkDown(index) {
        while (true) {
            const left = 2 * index + 1;
            const right = 2 * index + 2;
            let smallest = index;

            if (left < this.heap.length && this.heap[left].expires_at < this.heap[smallest].expires_at) {
                smallest = left;
            }
            if (right < this.heap.length && this.heap[right].expires_at < this.heap[smallest].expires_at) {
                smallest = right;
            }
            if (smallest === index) break;

            [this.heap[index], this.heap[smallest]] = [this.heap[smallest], this.heap[index]];
            index = smallest;
        }
    }
}

const expiryQueue = new ExpiryQueue();

// ==================== Index Management ====================
function attachIndexes(order) {
    const { order_id, state, event_id, bookie } = order;

    // byState - use state (not raw_status)
    if (!indexes.byState.has(state)) {
        indexes.byState.set(state, new Set());
    }
    indexes.byState.get(state).add(order_id);

    // byEvent
    if (!indexes.byEvent.has(event_id)) {
        indexes.byEvent.set(event_id, new Set());
    }
    indexes.byEvent.get(event_id).add(order_id);

    // byBookie
    if (bookie) {
        if (!indexes.byBookie.has(bookie)) {
            indexes.byBookie.set(bookie, new Set());
        }
        indexes.byBookie.get(bookie).add(order_id);
    }
}

function detachFromIndex(indexMap, key, order_id) {
    const indexSet = indexMap.get(key);
    if (indexSet) {
        indexSet.delete(order_id);
        if (indexSet.size === 0) {
            indexMap.delete(key);
        }
    }
}

function updateStateIndex(order_id, oldState, newState) {
    if (oldState) {
        detachFromIndex(indexes.byState, oldState, order_id);
    }
    if (newState) {
        if (!indexes.byState.has(newState)) {
            indexes.byState.set(newState, new Set());
        }
        indexes.byState.get(newState).add(order_id);
    }
}

function detachIndexes(order) {
    const { order_id, state, event_id, bookie } = order;

    detachFromIndex(indexes.byState, state, order_id);
    detachFromIndex(indexes.byEvent, event_id, order_id);
    if (bookie) {
        detachFromIndex(indexes.byBookie, bookie, order_id);
    }
}

// ==================== Extract Bet Bar (Derived from order data) ====================
function extractBetBar(orderData) {
    // Bet bar is derived from success/inprogress/danger/unplaced arrays
    const betBar = {
        success: 0,
        inprogress: 0,
        danger: 0,
        unplaced: 0
    };

    if (orderData.success && Array.isArray(orderData.success)) {
        betBar.success = orderData.success.reduce((sum, bet) => sum + (bet[1] || 0), 0);
    }
    if (orderData.inprogress && Array.isArray(orderData.inprogress)) {
        betBar.inprogress = orderData.inprogress.reduce((sum, bet) => sum + (bet[1] || 0), 0);
    }
    if (orderData.danger && Array.isArray(orderData.danger)) {
        betBar.danger = orderData.danger.reduce((sum, bet) => sum + (bet[1] || 0), 0);
    }
    if (orderData.unplaced && Array.isArray(orderData.unplaced)) {
        betBar.unplaced = orderData.unplaced.reduce((sum, bet) => sum + (bet[1] || 0), 0);
    }

    return betBar;
}

// ==================== Store Order (Idempotent Upsert with State Machine) ====================
function storeOrder(rawOrderData) {
    // Step 1: Normalize data using adapter
    let normalizedData;
    if (window.orderAdapter && typeof window.orderAdapter.normalizeOrderData === 'function') {
        normalizedData = window.orderAdapter.normalizeOrderData(rawOrderData);
    } else {
        // Fallback: use raw data directly
        console.warn('[Order Store] Adapter not available, using raw data');
        normalizedData = rawOrderData;
        // Ensure order_id exists
        normalizedData.order_id = rawOrderData.order_id || rawOrderData.id;
    }

    const {
        order_id,
        event_id,
        betslip_id,
        raw_status,
        closed,
        close_reason,
        created_at,
        expires_at,
        duration,
        bookie,
        price,
        stake,
        success,
        inprogress,
        danger,
        unplaced
    } = normalizedData;

    // 🔍 DEBUG: 打印 normalized data
    console.log('[DEBUG storeOrder]', {
        order_id: normalizedData.order_id,
        event_id: normalizedData.event_id,
        raw_status: normalizedData.raw_status,
        closed: normalizedData.closed,
        has_adapter: !!window.orderAdapter
    });

    // Validate required fields
    if (!order_id || !event_id) {
        console.warn('[Order Store] ❌ Missing required fields!');
        console.warn('[Order Store] Normalized:', { order_id, event_id, raw_status: normalizedData.raw_status });
        console.warn('[Order Store] Raw data:', rawOrderData);
        return null;
    }

    // Check if order exists
    const existing = orderStore.get(order_id);

    if (existing) {
        // Idempotent update
        const oldState = existing.state;

        // Update minimal facts
        existing.raw_status = raw_status;
        existing.closed = closed;
        existing.close_reason = close_reason;
        existing.duration = duration;
        existing.bookie = bookie;
        existing.price = price;
        existing.stake = stake;
        existing.success = success;
        existing.inprogress = inprogress;
        existing.danger = danger;
        existing.unplaced = unplaced;
        existing.last_update = Date.now();

        // Update expiry if provided
        if (expires_at !== undefined && expires_at !== null) {
            if (expires_at !== existing.expires_at) {
                existing.expires_at = expires_at;
                expiryQueue.push(order_id, expires_at);
            }
        }

        // Step 2: Apply state machine transition
        if (window.orderStateMachine) {
            const transitionResult = window.orderStateMachine.transition(existing);

            if (transitionResult.changed) {
                // Update state index
                updateStateIndex(order_id, oldState, transitionResult.newState);
                console.log(`[Order Store] State transition: ${oldState} → ${transitionResult.newState} for order ${order_id}`);
            }
        } else {
            console.warn('[Order Store] State machine not available');
        }

        return existing;
    } else {
        // Create new order
        const order = {
            order_id: order_id,
            event_id: event_id,
            betslip_id: betslip_id,
            raw_status: raw_status,
            state: 'CREATED',  // Initial state
            closed: closed,
            close_reason: close_reason,
            created_at: created_at,
            expires_at: expires_at,
            duration: duration,
            bookie: bookie,
            price: price,
            stake: stake,
            success: success || [],
            inprogress: inprogress || [],
            danger: danger || [],
            unplaced: unplaced || [],
            first_seen: Date.now(),
            last_update: Date.now()
        };

        // Step 2: Apply state machine transition
        if (window.orderStateMachine) {
            const transitionResult = window.orderStateMachine.transition(order);
            console.log(`[Order Store] New order: ${order_id}, initial state=${order.state}, event=${event_id}`);
        } else {
            console.warn('[Order Store] State machine not available');
            console.log(`[Order Store] New order: ${order_id}, state=CREATED, event=${event_id}`);
        }

        orderStore.set(order_id, order);
        attachIndexes(order);

        // Push to expiry queue if expires_at is valid
        if (expires_at !== undefined && expires_at !== null) {
            expiryQueue.push(order_id, expires_at);
        }

        return order;
    }
}

// ==================== Mark Order as Expired ====================
function markOrderExpired(order_id) {
    const order = orderStore.get(order_id);
    if (!order) return;

    // Protection: Don't mark if upstream says closed
    if (order.closed === true) {
        console.log(`[Order Store] Order ${order_id} already closed by upstream, skip local expiry`);
        return;
    }

    // Protection: Don't mark if already in terminal state
    if (order.state === 'FINISHED' || order.state === 'EXPIRED_LOCAL') {
        return;
    }

    const oldState = order.state;
    order.state = 'EXPIRED_LOCAL';
    order.last_update = Date.now();

    updateStateIndex(order_id, oldState, 'EXPIRED_LOCAL');

    console.log(`[Order Store] Order expired locally: ${order_id}`);
}

// ==================== Delete Order ====================
function deleteOrder(order_id) {
    const order = orderStore.get(order_id);
    if (!order) return;

    detachIndexes(order);
    orderStore.delete(order_id);
    expiryQueue.remove(order_id);
}

// ==================== Get Bet Bar (Computed on demand) ====================
function getOrderBetBar(order_id) {
    const order = orderStore.get(order_id);
    if (!order) return null;

    return extractBetBar(order);
}

// ==================== Apply Bets to Order (Bet → Order Aggregation) ====================
/**
 * Aggregate bets from betStore and update order's bet_bar
 * This is the key function for "bet drives order state"
 *
 * @param {string} order_id - Order ID
 * @returns {boolean} Whether order was updated
 */
function applyBetsToOrder(order_id) {
    const order = orderStore.get(order_id);
    if (!order) {
        console.warn('[Order Store] applyBetsToOrder: Order not found:', order_id);
        return false;
    }

    // Get all bets for this order from betStore
    if (!window.betStore || !window.betStore.getBetsByOrder) {
        console.warn('[Order Store] betStore not available');
        return false;
    }

    const bets = window.betStore.getBetsByOrder(order_id);
    if (!bets || bets.length === 0) {
        // No bets yet, keep existing bet_bar
        return false;
    }

    // Aggregate bets into success/inprogress/danger/unplaced arrays
    const aggregated = {
        success: [],
        inprogress: [],
        danger: [],
        unplaced: []
    };

    // Map to track stake by bookie
    const bookieStakes = {
        success: new Map(),
        inprogress: new Map(),
        danger: new Map(),
        unplaced: new Map()
    };

    for (const bet of bets) {
        const { bookie, status, stake, unmatched_stake } = bet;

        // Categorize bet by status
        let category = 'inprogress';  // Default

        if (status === 'done' || status === 'settled' || status === 'MATCHED') {
            category = 'success';
        } else if (status === 'cancelled' || status === 'rejected') {
            category = 'danger';
        } else if (status === 'pending' || status === 'unplaced') {
            category = 'unplaced';
        } else if (status === 'inprogress' || status === 'placing') {
            category = 'inprogress';
        }

        // Aggregate stake by bookie
        const currentStake = bookieStakes[category].get(bookie) || 0;
        bookieStakes[category].set(bookie, currentStake + (stake || 0));
    }

    // Convert Maps to arrays
    for (const [bookie, stake] of bookieStakes.success) {
        aggregated.success.push([bookie, stake]);
    }
    for (const [bookie, stake] of bookieStakes.inprogress) {
        aggregated.inprogress.push([bookie, stake]);
    }
    for (const [bookie, stake] of bookieStakes.danger) {
        aggregated.danger.push([bookie, stake]);
    }
    for (const [bookie, stake] of bookieStakes.unplaced) {
        aggregated.unplaced.push([bookie, stake]);
    }

    // Update order's bet_bar arrays
    const oldState = order.state;
    order.success = aggregated.success;
    order.inprogress = aggregated.inprogress;
    order.danger = aggregated.danger;
    order.unplaced = aggregated.unplaced;
    order.last_update = Date.now();

    // Apply state machine transition
    if (window.orderStateMachine) {
        const transitionResult = window.orderStateMachine.transition(order);

        if (transitionResult.changed) {
            // Update state index
            updateStateIndex(order_id, oldState, transitionResult.newState);
            console.log(`[Order Store] Bet-driven transition: ${oldState} → ${transitionResult.newState} for order ${order_id}`);
        }
    }

    return true;
}

// ==================== Periodic Cleanup ====================
setInterval(() => {
    const expired = expiryQueue.cleanExpired(Date.now());
    if (expired.length > 0) {
        console.log(`[Order Store] Marked ${expired.length} orders as expired locally`);
    }
}, 5000);  // Every 5 seconds

// ==================== Export ====================
window.orderStore = {
    // Store
    store: orderStore,
    indexes: indexes,

    // Functions
    storeOrder: storeOrder,
    deleteOrder: deleteOrder,
    getOrderBetBar: getOrderBetBar,
    applyBetsToOrder: applyBetsToOrder,
    markOrderExpired: markOrderExpired,

    // Stats
    getStats: function() {
        return {
            total_orders: orderStore.size,
            total_events: indexes.byEvent.size,
            total_bookies: indexes.byBookie.size,
            by_state: Array.from(indexes.byState.entries()).map(([state, set]) => ({
                state,
                count: set.size
            })),
            heap_size: expiryQueue.heap.length
        };
    }
};

console.log('[Order Store] Initialized');
