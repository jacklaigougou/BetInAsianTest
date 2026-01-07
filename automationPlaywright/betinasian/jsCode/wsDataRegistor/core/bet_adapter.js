/**
 * Bet Data Adapter
 *
 * Normalize upstream bet data into store format
 *
 * Upstream format (from WebSocket):
 * {
 *   "bet_id": "1a2ab5f0-2d76-49fb-96d8-9fbb3d3e3ac2",
 *   "order_id": "a018ad32-c9a2-42b3-87f3-e2bde91bc002",
 *   "event_id": "2026-01-06,41236,40814",
 *   "betslip_id": "f7c79ab3-e01b-4e6a-84ea-a4bdb3e2a55a",
 *   "bookie": "bf",
 *   "status": {
 *     "code": "done",
 *     "message": null
 *   },
 *   "got_price": 1.009,
 *   "got_stake": 15.0,
 *   "unmatched_stake": 0.0,
 *   "placed_ts": "2026-01-06T16:08:05.421588+00:00",
 *   "matched_ts": "2026-01-06T16:08:05.459079+00:00"
 * }
 *
 * Store format (internal):
 * {
 *   "bet_id": "xxx",
 *   "order_id": "xxx",
 *   "event_id": "xxx",
 *   "betslip_id": "xxx",
 *   "bookie": "bf",
 *   "status": "done",              // Normalized to string
 *   "price": 1.009,                 // got_price or price
 *   "stake": 15.0,                  // got_stake or stake
 *   "matched_price": 1.009,
 *   "matched_stake": 15.0,
 *   "unmatched_stake": 0.0,
 *   "placed_ts": 1736168085.421,   // Unix timestamp (seconds)
 *   "matched_ts": 1736168085.459   // Unix timestamp (seconds)
 * }
 */

/**
 * Parse ISO timestamp to Unix timestamp (seconds)
 * @param {string} isoString - ISO 8601 timestamp
 * @returns {number} Unix timestamp in seconds
 */
function parseISOToUnixSeconds(isoString) {
    if (!isoString) return null;
    try {
        return new Date(isoString).getTime() / 1000;
    } catch (e) {
        console.warn('[Bet Adapter] Failed to parse ISO timestamp:', isoString);
        return null;
    }
}

/**
 * Normalize status to string
 * @param {Object|string} status - Status object or string
 * @returns {string} Normalized status code
 */
function normalizeStatus(status) {
    if (typeof status === 'string') {
        return status;
    }
    if (status && typeof status === 'object') {
        return status.code || status.status || 'unknown';
    }
    return 'unknown';
}

/**
 * Normalize upstream bet data to store format
 * @param {Object} upstreamData - Raw bet data from WebSocket
 * @returns {Object} Normalized bet data for store
 */
function normalizeBetData(upstreamData) {
    // Handle two possible formats:
    // 1. New format: { bet_id, order_id, status: { code: "done" }, got_price, got_stake, ... }
    // 2. Old format: { id, order_id, status: "MATCHED", price, stake, matched_price, ... }

    // IMPORTANT: Convert IDs to strings to match Order Store format
    const bet_id = String(upstreamData.bet_id || upstreamData.id);
    const order_id = String(upstreamData.order_id);

    // Normalize status
    const status = normalizeStatus(upstreamData.status);

    // Helper to extract numeric value from number or ["CCY", number] format
    function extractValue(val) {
        if (typeof val === 'number') {
            return val;
        }
        if (Array.isArray(val) && val.length === 2) {
            return val[1];  // ["USD", 2.0] → 2.0
        }
        return 0;
    }

    // Normalize price and stake
    const price = upstreamData.got_price !== undefined ? upstreamData.got_price : upstreamData.price;
    const stake = upstreamData.got_stake !== undefined ? extractValue(upstreamData.got_stake) : upstreamData.stake;
    const want_stake = upstreamData.want_stake !== undefined ? extractValue(upstreamData.want_stake) : stake;

    // Normalize matched fields
    const matched_price = upstreamData.got_price !== undefined ? upstreamData.got_price : upstreamData.matched_price;
    const matched_stake = stake;  // got_stake is already extracted
    const unmatched_stake = upstreamData.unmatched_stake !== undefined ? upstreamData.unmatched_stake : 0;

    // Parse timestamps
    let placed_ts = upstreamData.placed_ts;
    let matched_ts = upstreamData.matched_ts;

    // If timestamps are ISO strings, convert to Unix seconds
    if (typeof placed_ts === 'string') {
        placed_ts = parseISOToUnixSeconds(placed_ts);
    }
    if (typeof matched_ts === 'string') {
        matched_ts = parseISOToUnixSeconds(matched_ts);
    }

    return {
        bet_id: bet_id,
        order_id: order_id,
        event_id: upstreamData.event_id,
        betslip_id: upstreamData.betslip_id,
        bookie: upstreamData.bookie,
        status: status,
        price: price,
        stake: stake,
        matched_price: matched_price,
        matched_stake: matched_stake,
        unmatched_stake: unmatched_stake,
        placed_ts: placed_ts,
        matched_ts: matched_ts
    };
}

// ==================== Export ====================
window.betAdapter = {
    normalizeBetData: normalizeBetData,
    normalizeStatus: normalizeStatus,
    parseISOToUnixSeconds: parseISOToUnixSeconds
};

console.log('[Bet Adapter] Initialized');
