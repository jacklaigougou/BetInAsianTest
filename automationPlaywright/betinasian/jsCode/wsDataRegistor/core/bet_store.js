/**
 * Bet Store
 *
 * Store structure + Indexes
 *
 * Features:
 * - Idempotent upsert (message replay safe)
 * - Minimal fact storage
 * - Links to order updates via bet_bar
 */

// ==================== Store ====================
const betStore = new Map();  // bet_id → BetData

// ==================== Indexes ====================
const indexes = {
    byOrder: new Map(),        // order_id → Set(bet_ids)
    byBookie: new Map(),       // bookie → Set(bet_ids)
    byStatus: new Map(),       // status → Set(bet_ids)
    byEvent: new Map()         // event_id → Set(bet_ids)
};

// ==================== Index Management ====================
function attachIndexes(bet) {
    const { bet_id, order_id, bookie, status, event_id } = bet;

    // byOrder
    if (!indexes.byOrder.has(order_id)) {
        indexes.byOrder.set(order_id, new Set());
    }
    indexes.byOrder.get(order_id).add(bet_id);

    // byBookie
    if (bookie) {
        if (!indexes.byBookie.has(bookie)) {
            indexes.byBookie.set(bookie, new Set());
        }
        indexes.byBookie.get(bookie).add(bet_id);
    }

    // byStatus
    if (status) {
        if (!indexes.byStatus.has(status)) {
            indexes.byStatus.set(status, new Set());
        }
        indexes.byStatus.get(status).add(bet_id);
    }

    // byEvent
    if (event_id) {
        if (!indexes.byEvent.has(event_id)) {
            indexes.byEvent.set(event_id, new Set());
        }
        indexes.byEvent.get(event_id).add(bet_id);
    }
}

function detachFromIndex(indexMap, key, bet_id) {
    const indexSet = indexMap.get(key);
    if (indexSet) {
        indexSet.delete(bet_id);
        if (indexSet.size === 0) {
            indexMap.delete(key);
        }
    }
}

function updateStatusIndex(bet_id, oldStatus, newStatus) {
    if (oldStatus) {
        detachFromIndex(indexes.byStatus, oldStatus, bet_id);
    }
    if (newStatus) {
        if (!indexes.byStatus.has(newStatus)) {
            indexes.byStatus.set(newStatus, new Set());
        }
        indexes.byStatus.get(newStatus).add(bet_id);
    }
}

function detachIndexes(bet) {
    const { bet_id, order_id, bookie, status, event_id } = bet;

    detachFromIndex(indexes.byOrder, order_id, bet_id);
    if (bookie) {
        detachFromIndex(indexes.byBookie, bookie, bet_id);
    }
    if (status) {
        detachFromIndex(indexes.byStatus, status, bet_id);
    }
    if (event_id) {
        detachFromIndex(indexes.byEvent, event_id, bet_id);
    }
}

// ==================== Store Bet (Idempotent Upsert with Adapter) ====================
function storeBet(rawBetData) {
    // Step 1: Normalize data using adapter
    let normalizedData;
    if (window.betAdapter && typeof window.betAdapter.normalizeBetData === 'function') {
        normalizedData = window.betAdapter.normalizeBetData(rawBetData);
    } else {
        // Fallback: use raw data directly
        console.warn('[Bet Store] Adapter not available, using raw data');
        normalizedData = rawBetData;
        // Ensure bet_id exists
        normalizedData.bet_id = rawBetData.bet_id || rawBetData.id;
    }

    const {
        bet_id,
        order_id,
        event_id,
        betslip_id,
        bookie,
        status,
        price,
        stake,
        placed_ts,
        matched_ts,
        matched_price,
        matched_stake,
        unmatched_stake
    } = normalizedData;

    // Validate required fields
    if (!bet_id || !order_id) {
        console.warn('[Bet Store] Missing required fields:', normalizedData);
        return null;
    }

    // Check if bet exists
    const existing = betStore.get(bet_id);

    if (existing) {
        // Idempotent update: only update if data changed
        const oldStatus = existing.status;

        // Update minimal facts
        existing.status = status;
        existing.price = price;
        existing.stake = stake;
        existing.placed_ts = placed_ts;
        existing.matched_ts = matched_ts;
        existing.matched_price = matched_price;
        existing.matched_stake = matched_stake;
        existing.unmatched_stake = unmatched_stake;
        existing.last_update = Date.now();

        // Update status index if status changed
        if (status && status !== oldStatus) {
            updateStatusIndex(bet_id, oldStatus, status);
        }

        return existing;
    } else {
        // Create new bet
        const bet = {
            bet_id: bet_id,
            order_id: order_id,
            event_id: event_id,
            betslip_id: betslip_id,
            bookie: bookie,
            status: status,
            price: price,
            stake: stake,
            placed_ts: placed_ts,
            matched_ts: matched_ts,
            matched_price: matched_price,
            matched_stake: matched_stake,
            unmatched_stake: unmatched_stake,
            first_seen: Date.now(),
            last_update: Date.now()
        };

        betStore.set(bet_id, bet);
        attachIndexes(bet);

        console.log(`[Bet Store] New bet: ${bet_id}, order=${order_id}, bookie=${bookie}, status=${status}`);
        return bet;
    }
}

// ==================== Delete Bet ====================
function deleteBet(bet_id) {
    const bet = betStore.get(bet_id);
    if (!bet) return;

    detachIndexes(bet);
    betStore.delete(bet_id);
}

// ==================== Get Bets by Order ====================
function getBetsByOrder(order_id) {
    const bet_ids = indexes.byOrder.get(order_id);
    if (!bet_ids) return [];

    const bets = [];
    for (const bet_id of bet_ids) {
        const bet = betStore.get(bet_id);
        if (bet) {
            bets.push(bet);
        }
    }

    return bets;
}

// ==================== Calculate Slippage ====================
function calculateSlippage(bet_id) {
    const bet = betStore.get(bet_id);
    if (!bet) return null;

    const { price, matched_price } = bet;

    if (!price || !matched_price) {
        return null;
    }

    // Slippage = (matched_price - requested_price) / requested_price
    const slippage = (matched_price - price) / price;

    return {
        bet_id: bet_id,
        requested_price: price,
        matched_price: matched_price,
        slippage: slippage,
        slippage_pct: (slippage * 100).toFixed(4) + '%'
    };
}

// ==================== Export ====================
window.betStore = {
    // Store
    store: betStore,
    indexes: indexes,

    // Functions
    storeBet: storeBet,
    deleteBet: deleteBet,
    getBetsByOrder: getBetsByOrder,
    calculateSlippage: calculateSlippage,

    // Stats
    getStats: function() {
        return {
            total_bets: betStore.size,
            total_orders: indexes.byOrder.size,
            total_bookies: indexes.byBookie.size,
            total_events: indexes.byEvent.size,
            by_status: Array.from(indexes.byStatus.entries()).map(([status, set]) => ({
                status,
                count: set.size
            }))
        };
    }
};

console.log('[Bet Store] Initialized');
