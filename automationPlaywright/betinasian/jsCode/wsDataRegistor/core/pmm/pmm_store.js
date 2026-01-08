/**
 * PMM (Price Match Message) Store
 *
 * Store structure + Indexes + Expiry Queue
 *
 * Features:
 * - Out-of-order protection (timestamp-based)
 * - Index consistency management
 * - Efficient expiry cleanup (min-heap)
 * - Dirty flag batch recomputation
 */

// ==================== Config ====================
const PMM_EXPIRE_MS = 30000;  // 30 seconds
const MAX_PRICE_TIERS = 3;     // Keep max 3 price tiers

// ==================== Store ====================
const pmmStore = new Map();  // betslip_id → BetslipData

// ==================== Indexes ====================
const indexes = {
    byEvent: new Map(),        // event_id → Set(betslip_ids)
    byMarket: new Map(),       // "event_id|bet_type" → Set(betslip_ids)
    byBookie: new Map(),       // bookie → Set(betslip_ids)
    bySport: new Map()         // sport → Set(betslip_ids)
};

// ==================== Expiry Queue (Min-Heap) ====================
class ExpiryQueue {
    constructor() {
        this.heap = [];  // {expires_at, betslip_id, version}
        this.versionMap = new Map();  // betslip_id → version
    }

    push(betslip_id, expires_at) {
        // Increment version to identify old entries
        const version = (this.versionMap.get(betslip_id) || 0) + 1;
        this.versionMap.set(betslip_id, version);

        this.heap.push({ expires_at, betslip_id, version });
        this._bubbleUp(this.heap.length - 1);
    }

    cleanExpired(now) {
        const deleted = [];

        while (this.heap.length > 0 && this.heap[0].expires_at < now) {
            const entry = this._extractMin();

            // Verify version to prevent deleting updated records
            const currentVersion = this.versionMap.get(entry.betslip_id);
            if (currentVersion !== entry.version) {
                continue;  // Old entry, skip
            }

            // Verify record is actually expired
            const betslip = pmmStore.get(entry.betslip_id);
            if (betslip && betslip.expires_at === entry.expires_at) {
                deleteBetslip(entry.betslip_id);
                deleted.push(entry.betslip_id);
            }
        }

        return deleted;
    }

    remove(betslip_id) {
        // Increment version to invalidate old entries
        const version = (this.versionMap.get(betslip_id) || 0) + 1;
        this.versionMap.set(betslip_id, version);
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

// ==================== Dirty Flag Batch Recomputation ====================
const dirtyBetslips = new Set();
let recomputeScheduled = false;

function markDirty(betslip_id) {
    dirtyBetslips.add(betslip_id);

    // Schedule batch recomputation
    if (!recomputeScheduled) {
        recomputeScheduled = true;
        Promise.resolve().then(() => {
            recomputeAllDirty();
            recomputeScheduled = false;
        });
    }
}

function recomputeAllDirty() {
    for (const betslip_id of dirtyBetslips) {
        const betslip = pmmStore.get(betslip_id);
        if (!betslip) continue;

        const result = calculateBestPrice(betslip.bookies);
        betslip.best_odds = result.best_odds;
        betslip.best_executable = result.best_executable;
        betslip.best_executable_reason = result.best_executable_reason;
        betslip.filtered_reasons = result.filtered_reasons;
        betslip.updated_at = Date.now();
    }

    dirtyBetslips.clear();
}

// ==================== Index Management ====================
function attachIndexes(betslip) {
    const { betslip_id, event_id, bet_type, market_key, sport } = betslip;

    // byEvent
    if (!indexes.byEvent.has(event_id)) {
        indexes.byEvent.set(event_id, new Set());
    }
    indexes.byEvent.get(event_id).add(betslip_id);

    // byMarket
    if (!indexes.byMarket.has(market_key)) {
        indexes.byMarket.set(market_key, new Set());
    }
    indexes.byMarket.get(market_key).add(betslip_id);

    // bySport
    if (!indexes.bySport.has(sport)) {
        indexes.bySport.set(sport, new Set());
    }
    indexes.bySport.get(sport).add(betslip_id);

    // byBookie - will be updated when bookies are added
    for (const bookie of betslip.bookies.keys()) {
        if (!indexes.byBookie.has(bookie)) {
            indexes.byBookie.set(bookie, new Set());
        }
        indexes.byBookie.get(bookie).add(betslip_id);
    }
}

function detachIndexes(betslip) {
    const { betslip_id, event_id, market_key, sport } = betslip;

    // byEvent
    const eventSet = indexes.byEvent.get(event_id);
    if (eventSet) {
        eventSet.delete(betslip_id);
        // Delete key if Set is empty to prevent Map bloat
        if (eventSet.size === 0) {
            indexes.byEvent.delete(event_id);
        }
    }

    // byMarket
    const marketSet = indexes.byMarket.get(market_key);
    if (marketSet) {
        marketSet.delete(betslip_id);
        if (marketSet.size === 0) {
            indexes.byMarket.delete(market_key);
        }
    }

    // bySport
    const sportSet = indexes.bySport.get(sport);
    if (sportSet) {
        sportSet.delete(betslip_id);
        if (sportSet.size === 0) {
            indexes.bySport.delete(sport);
        }
    }

    // byBookie
    for (const bookie of betslip.bookies.keys()) {
        const bookieSet = indexes.byBookie.get(bookie);
        if (bookieSet) {
            bookieSet.delete(betslip_id);
            if (bookieSet.size === 0) {
                indexes.byBookie.delete(bookie);
            }
        }
    }
}

function deleteBetslip(betslip_id) {
    const betslip = pmmStore.get(betslip_id);
    if (!betslip) return;

    // Fixed entry point: detach indexes → delete from store → remove from queue
    detachIndexes(betslip);
    pmmStore.delete(betslip_id);
    expiryQueue.remove(betslip_id);
}

// ==================== Price Tiers Extraction (O(n)) ====================
function extractTop3Tiers(price_list) {
    if (!price_list || price_list.length === 0) return [];

    // Extract top 3 tiers in O(n) using insertion sort
    const top3 = [];

    for (const item of price_list) {
        const tier = {
            price: item.effective?.price || 0,
            min: item.effective?.min?.[1] || 0,
            max: item.effective?.max?.[1] || 0
        };

        if (tier.price <= 1.0) continue;

        // Insert into sorted top3
        let inserted = false;
        for (let i = 0; i < top3.length; i++) {
            if (tier.price > top3[i].price) {
                top3.splice(i, 0, tier);
                inserted = true;
                break;
            }
        }
        if (!inserted && top3.length < MAX_PRICE_TIERS) {
            top3.push(tier);
        }

        // Keep max 3
        if (top3.length > MAX_PRICE_TIERS) {
            top3.length = MAX_PRICE_TIERS;
        }
    }

    return top3;
}

// ==================== Store Bookie Data ====================
function storePMMBookie(betslip, bookie, pmmData) {
    // Use upstream timestamp for out-of-order protection
    const incoming_ts = (pmmData.ts * 1000) || pmmData.updated_at || Date.now();

    // Out-of-order protection: drop if older than existing
    const existing = betslip.bookies.get(bookie);
    if (existing && incoming_ts <= existing.last_update) {
        console.warn(`[PMM] Dropping old packet: ${bookie}, incoming=${incoming_ts}, existing=${existing.last_update}`);
        return false;  // Not updated
    }

    // Extract price info (slimmed down)
    const { price_list, status } = pmmData;

    let top_price = null;
    let top_available = null;
    let price_tiers = [];

    if (price_list && price_list.length > 0) {
        // Extract top 3 tiers
        price_tiers = extractTop3Tiers(price_list);

        if (price_tiers.length > 0) {
            const best = price_tiers[0];
            top_price = best.price;
            top_available = {
                currency: 'GBP',  // Assume GBP for now (can be extracted from price_list)
                amount: best.max
            };
        }
    }

    betslip.bookies.set(bookie, {
        username: pmmData.username,
        status: status,
        top_price: top_price,
        top_available: top_available,
        price_tiers: price_tiers,
        last_update: incoming_ts
    });

    // Update byBookie index
    if (!indexes.byBookie.has(bookie)) {
        indexes.byBookie.set(bookie, new Set());
    }
    indexes.byBookie.get(bookie).add(betslip.betslip_id);

    return true;  // Updated
}

// ==================== Calculate Best Price ====================
function calculateBestPrice(bookies, requiredAmount = 10, requiredCurrency = 'GBP') {
    const now = Date.now();

    let best_odds = null;
    let best_executable = null;
    const filtered_reasons = {};

    for (const [bookie, data] of bookies.entries()) {
        const { status, top_price, top_available, price_tiers, last_update } = data;

        // Check if price exists
        if (!top_price || top_price <= 1.0) {
            filtered_reasons[bookie] = "no_price";
            continue;
        }

        // Update best_odds (no executability check, only price)
        if (!best_odds || top_price > best_odds.price) {
            best_odds = {
                bookie: bookie,
                price: top_price,
                available: top_available,
                updated_at: last_update
            };
        }

        // ===== Executability Filters =====

        // 1. Status check
        if (status?.code !== "success") {
            filtered_reasons[bookie] = `status_${status?.code || 'unknown'}`;
            continue;
        }

        // 2. Expiry check
        if (now - last_update > PMM_EXPIRE_MS) {
            filtered_reasons[bookie] = "expired";
            continue;
        }

        // 3. Liquidity check
        if (!top_available || top_available.amount <= 0) {
            filtered_reasons[bookie] = "no_liquidity";
            continue;
        }

        // 4. Currency check
        if (top_available.currency !== requiredCurrency) {
            filtered_reasons[bookie] = `currency_mismatch_${top_available.currency}`;
            continue;
        }

        // 5. Min stake check (from tiers)
        let canStake = false;
        if (price_tiers && price_tiers.length > 0) {
            for (const tier of price_tiers) {
                if (tier.price === top_price && tier.min <= requiredAmount && tier.max >= requiredAmount) {
                    canStake = true;
                    break;
                }
            }
        } else if (top_available.amount >= requiredAmount) {
            canStake = true;
        }

        if (!canStake) {
            filtered_reasons[bookie] = `min_stake_${requiredAmount}`;
            continue;
        }

        // Passed all filters, compare price
        if (!best_executable || top_price > best_executable.price) {
            best_executable = {
                bookie: bookie,
                price: top_price,
                available: top_available,
                updated_at: last_update
            };
        }
    }

    // Generate summary reason
    let best_executable_reason = null;
    if (!best_executable) {
        const reasons = Object.values(filtered_reasons);
        if (reasons.every(r => r.startsWith('status_'))) {
            best_executable_reason = "all_suspended";
        } else if (reasons.every(r => r === 'expired')) {
            best_executable_reason = "all_expired";
        } else if (reasons.every(r => r === 'no_liquidity')) {
            best_executable_reason = "no_liquidity";
        } else {
            best_executable_reason = "mixed_issues";
        }
    }

    return {
        best_odds,
        best_executable,
        best_executable_reason,
        filtered_reasons: Object.keys(filtered_reasons).length > 0 ? filtered_reasons : undefined
    };
}

// ==================== Update Betslip Expiry ====================
function updateBetslipExpiry(betslip) {
    const now = Date.now();
    betslip.expires_at = now + PMM_EXPIRE_MS;
    expiryQueue.push(betslip.betslip_id, betslip.expires_at);
}

// ==================== Store PMM ====================
function storePMM(pmmData) {
    const { betslip_id, bookie, event_id, bet_type, sport } = pmmData;
    const market_key = `${event_id}|${bet_type}`;

    // Get or create betslip
    if (!pmmStore.has(betslip_id)) {
        const betslip = {
            betslip_id: betslip_id,
            sport: sport,
            event_id: event_id,
            bet_type: bet_type,
            market_key: market_key,
            bookies: new Map(),
            best_odds: null,
            best_executable: null,
            best_executable_reason: null,
            filtered_reasons: undefined,
            created_at: Date.now(),
            updated_at: Date.now(),
            expires_at: Date.now() + PMM_EXPIRE_MS
        };

        pmmStore.set(betslip_id, betslip);
        attachIndexes(betslip);
        expiryQueue.push(betslip_id, betslip.expires_at);
    }

    const betslip = pmmStore.get(betslip_id);

    // Store bookie data (with out-of-order protection)
    const updated = storePMMBookie(betslip, bookie, pmmData);

    if (updated) {
        // Update expiry
        updateBetslipExpiry(betslip);

        // Mark dirty for batch recomputation
        markDirty(betslip_id);
    }
}

// ==================== Periodic Cleanup ====================
setInterval(() => {
    const deleted = expiryQueue.cleanExpired(Date.now());
    if (deleted.length > 0) {
        console.log(`[PMM] Cleaned ${deleted.length} expired betslips`);
    }
}, 5000);  // Every 5 seconds

// ==================== Export ====================
window.pmmStore = {
    // Store
    store: pmmStore,
    indexes: indexes,

    // Functions
    storePMM: storePMM,
    deleteBetslip: deleteBetslip,

    // Stats
    getStats: function() {
        return {
            total_betslips: pmmStore.size,
            total_events: indexes.byEvent.size,
            total_markets: indexes.byMarket.size,
            total_bookies: indexes.byBookie.size,
            dirty_count: dirtyBetslips.size,
            heap_size: expiryQueue.heap.length
        };
    }
};

console.log('[PMM Store] Initialized');
