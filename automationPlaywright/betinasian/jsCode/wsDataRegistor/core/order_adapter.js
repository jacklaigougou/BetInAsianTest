/**
 * Order Data Adapter
 *
 * Normalize upstream order data into store format
 *
 * Upstream format (from WebSocket):
 * {
 *   "order_id": "xxx",
 *   "event_id": "xxx",
 *   "betslip_id": "xxx",
 *   "status": "open",  // lowercase: open, reconciled, etc.
 *   "closed": false,
 *   "close_reason": null,
 *   "placement_time": "2026-01-06T16:08:05.266499+00:00",  // ISO string
 *   "expiry_time": "2026-01-06T16:08:15.266499+00:00",     // ISO string
 *   "bet_bar_values": {
 *     "success": 0,
 *     "inprogress": 15,
 *     "danger": 0,
 *     "unplaced": 0
 *   },
 *   "bookie": null,
 *   "price": null,
 *   "stake": null
 * }
 *
 * Store format (internal):
 * {
 *   "order_id": "xxx",
 *   "event_id": "xxx",
 *   "betslip_id": "xxx",
 *   "raw_status": "open",           // Original upstream status
 *   "state": "OPEN",                 // State machine state
 *   "closed": false,
 *   "close_reason": null,
 *   "created_at": 1736168085.266,   // Unix timestamp (seconds)
 *   "expires_at": 1736168097266,    // Unix timestamp (milliseconds)
 *   "duration": 10,                  // seconds (calculated)
 *   "success": [["bf", 0]],          // Array format for state machine
 *   "inprogress": [["bf", 15]],
 *   "danger": [],
 *   "unplaced": [],
 *   "bookie": null,
 *   "price": null,
 *   "stake": null
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
        console.warn('[Order Adapter] Failed to parse ISO timestamp:', isoString);
        return null;
    }
}

/**
 * Parse ISO timestamp to Unix timestamp (milliseconds)
 * @param {string} isoString - ISO 8601 timestamp
 * @returns {number} Unix timestamp in milliseconds
 */
function parseISOToUnixMs(isoString) {
    if (!isoString) return null;
    try {
        return new Date(isoString).getTime();
    } catch (e) {
        console.warn('[Order Adapter] Failed to parse ISO timestamp:', isoString);
        return null;
    }
}

/**
 * Convert bet_bar_values object to arrays
 * @param {Object} betBarValues - Two possible formats:
 *   1. { success: 0, inprogress: 15, danger: 0, unplaced: 0 }  (numbers)
 *   2. { success: ["USD", 0.0], inprogress: ["USD", 0.0], ... }  (arrays)
 * @param {string} bookie - Bookie name (optional)
 * @returns {Object} { success: [], inprogress: [["bf", 15]], danger: [], unplaced: [] }
 */
function convertBetBarToArrays(betBarValues, bookie = null) {
    const result = {
        success: [],
        inprogress: [],
        danger: [],
        unplaced: []
    };

    if (!betBarValues || typeof betBarValues !== 'object') {
        return result;
    }

    const bookieName = bookie || 'unknown';

    // Helper to extract value from either number or ["CCY", amount] array
    function extractValue(val) {
        if (typeof val === 'number') {
            return val;
        }
        if (Array.isArray(val) && val.length === 2) {
            return val[1];  // ["USD", 1.0] → 1.0
        }
        return 0;
    }

    const successVal = extractValue(betBarValues.success);
    const inprogressVal = extractValue(betBarValues.inprogress);
    const dangerVal = extractValue(betBarValues.danger);
    const unplacedVal = extractValue(betBarValues.unplaced);

    if (successVal > 0) {
        result.success.push([bookieName, successVal]);
    }
    if (inprogressVal > 0) {
        result.inprogress.push([bookieName, inprogressVal]);
    }
    if (dangerVal > 0) {
        result.danger.push([bookieName, dangerVal]);
    }
    if (unplacedVal > 0) {
        result.unplaced.push([bookieName, unplacedVal]);
    }

    return result;
}

/**
 * Normalize upstream order data to store format
 * @param {Object} upstreamData - Raw order data from WebSocket
 * @returns {Object} Normalized order data for store
 */
function normalizeOrderData(upstreamData) {
    // Handle two possible formats:
    // 1. New format: { order_id, placement_time, expiry_time, bet_bar_values, ... }
    // 2. Old format: { id, created_at, duration, success: [], inprogress: [], ... }

    const isNewFormat = upstreamData.order_id && upstreamData.placement_time;

    if (isNewFormat) {
        // New format: parse ISO timestamps
        const created_at = parseISOToUnixSeconds(upstreamData.placement_time);
        const expires_at = parseISOToUnixMs(upstreamData.expiry_time);

        // Calculate duration
        let duration = null;
        if (created_at && expires_at) {
            duration = Math.floor((expires_at / 1000) - created_at);
        }

        // Extract event_id from event_info or top level
        const event_id = upstreamData.event_info?.event_id || upstreamData.event_id;

        // Convert bet_bar_values to arrays
        const betBarArrays = convertBetBarToArrays(
            upstreamData.bet_bar_values,
            upstreamData.bookie
        );

        // Normalize order_id to string for consistent storage
        const order_id = String(upstreamData.order_id);

        return {
            order_id: order_id,
            event_id: event_id,
            betslip_id: upstreamData.betslip_id,
            raw_status: upstreamData.status,  // Keep original status
            closed: upstreamData.closed,
            close_reason: upstreamData.close_reason,
            created_at: created_at,
            expires_at: expires_at,
            duration: duration,
            bookie: upstreamData.bookie,
            price: upstreamData.price,
            stake: upstreamData.stake,
            success: betBarArrays.success,
            inprogress: betBarArrays.inprogress,
            danger: betBarArrays.danger,
            unplaced: betBarArrays.unplaced
        };
    } else {
        // Old format: already has created_at, duration, success/inprogress arrays
        return {
            order_id: upstreamData.id || upstreamData.order_id,
            event_id: upstreamData.event_id,
            betslip_id: upstreamData.betslip_id,
            raw_status: upstreamData.status,
            closed: upstreamData.closed,
            close_reason: upstreamData.close_reason,
            created_at: upstreamData.created_at,
            expires_at: upstreamData.expires_at,
            duration: upstreamData.duration,
            bookie: upstreamData.bookie,
            price: upstreamData.price,
            stake: upstreamData.stake,
            success: upstreamData.success || [],
            inprogress: upstreamData.inprogress || [],
            danger: upstreamData.danger || [],
            unplaced: upstreamData.unplaced || []
        };
    }
}

// ==================== Export ====================
window.orderAdapter = {
    normalizeOrderData: normalizeOrderData,
    parseISOToUnixSeconds: parseISOToUnixSeconds,
    parseISOToUnixMs: parseISOToUnixMs,
    convertBetBarToArrays: convertBetBarToArrays
};

console.log('[Order Adapter] Initialized');
