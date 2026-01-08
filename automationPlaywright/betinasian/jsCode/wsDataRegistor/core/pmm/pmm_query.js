/**
 * PMM (Price Match Message) Query Interface
 *
 * Query functions for PMM data
 */

// Bookie priority for tie-breaking
const BOOKIE_PRIORITY = {
    'bf': 3,      // Betfair (sharp book)
    'bdaq': 2,    // Betdaq
    'mbook': 1    // Matchbook
};

/**
 * Query betslip by ID
 *
 * @param {string} betslip_id - Betslip ID
 * @returns {Object|null} Betslip object or null
 */
function queryBetslipById(betslip_id) {
    if (!window.pmmStore) {
        console.error('[PMM Query] pmmStore not available');
        return null;
    }

    return window.pmmStore.store.get(betslip_id) || null;
}

/**
 * Query all betslips for a market
 *
 * @param {string} event_id - Event ID
 * @param {string} bet_type - Bet type (e.g., "for,ml,a")
 * @returns {Array} Array of betslip objects
 */
function queryMarket(event_id, bet_type) {
    if (!window.pmmStore) {
        console.error('[PMM Query] pmmStore not available');
        return [];
    }

    const market_key = `${event_id}|${bet_type}`;
    const betslip_ids = window.pmmStore.indexes.byMarket.get(market_key);

    if (!betslip_ids || betslip_ids.size === 0) {
        return [];
    }

    return Array.from(betslip_ids)
        .map(id => window.pmmStore.store.get(id))
        .filter(b => b !== undefined);
}

/**
 * Get best executable price with tie-breaking
 *
 * @param {string} event_id - Event ID
 * @param {string} bet_type - Bet type
 * @param {number} requiredAmount - Required stake amount (default: 10)
 * @param {string} requiredCurrency - Required currency (default: "GBP")
 * @returns {Object} Result object
 */
function getBestExecutablePrice(event_id, bet_type, requiredAmount = 10, requiredCurrency = 'GBP') {
    const betslips = queryMarket(event_id, bet_type);

    if (betslips.length === 0) {
        return {
            success: false,
            reason: "no_betslip",
            event_id: event_id,
            bet_type: bet_type
        };
    }

    // Find all executable betslips
    const executables = betslips
        .filter(b => b.best_executable !== null)
        .sort((a, b) => {
            // Tie-breaker rules:
            // 1. Price (higher is better)
            if (b.best_executable.price !== a.best_executable.price) {
                return b.best_executable.price - a.best_executable.price;
            }
            // 2. Available amount (larger is better)
            if (b.best_executable.available.amount !== a.best_executable.available.amount) {
                return b.best_executable.available.amount - a.best_executable.available.amount;
            }
            // 3. Updated time (more recent is better)
            if (b.best_executable.updated_at !== a.best_executable.updated_at) {
                return b.best_executable.updated_at - a.best_executable.updated_at;
            }
            // 4. Bookie priority
            const priorityA = BOOKIE_PRIORITY[a.best_executable.bookie] || 0;
            const priorityB = BOOKIE_PRIORITY[b.best_executable.bookie] || 0;
            return priorityB - priorityA;
        });

    if (executables.length > 0) {
        const best = executables[0];
        return {
            success: true,
            betslip_id: best.betslip_id,
            event_id: best.event_id,
            bet_type: best.bet_type,
            bookie: best.best_executable.bookie,
            price: best.best_executable.price,
            available: best.best_executable.available,
            updated_at: best.best_executable.updated_at
        };
    }

    // Fallback: no executable price, return best odds + reason
    const best_odds_betslip = betslips
        .filter(b => b.best_odds !== null)
        .sort((a, b) => b.best_odds.price - a.best_odds.price)[0];

    if (best_odds_betslip) {
        return {
            success: false,
            reason: best_odds_betslip.best_executable_reason || "not_executable",
            event_id: best_odds_betslip.event_id,
            bet_type: best_odds_betslip.bet_type,
            best_odds: best_odds_betslip.best_odds,
            filtered_reasons: best_odds_betslip.filtered_reasons
        };
    }

    return {
        success: false,
        reason: "no_price",
        event_id: event_id,
        bet_type: bet_type
    };
}

/**
 * Get all prices for a market (all bookies)
 *
 * @param {string} event_id - Event ID
 * @param {string} bet_type - Bet type
 * @returns {Object} Result object with all bookie prices
 */
function getAllPrices(event_id, bet_type) {
    const betslips = queryMarket(event_id, bet_type);

    if (betslips.length === 0) {
        return {
            success: false,
            reason: "no_betslip",
            event_id: event_id,
            bet_type: bet_type
        };
    }

    // Collect all bookie prices from all betslips
    const allBookies = new Map();

    for (const betslip of betslips) {
        for (const [bookie, data] of betslip.bookies.entries()) {
            if (!allBookies.has(bookie) || data.top_price > allBookies.get(bookie).top_price) {
                allBookies.set(bookie, {
                    bookie: bookie,
                    betslip_id: betslip.betslip_id,
                    price: data.top_price,
                    available: data.top_available,
                    status: data.status,
                    updated_at: data.last_update
                });
            }
        }
    }

    // Get best executable from first betslip (already computed)
    const best_executable = betslips[0].best_executable;
    const best_odds = betslips[0].best_odds;

    return {
        success: true,
        event_id: event_id,
        bet_type: bet_type,
        best_executable: best_executable,
        best_odds: best_odds,
        bookies: Array.from(allBookies.values()).sort((a, b) => b.price - a.price)
    };
}

/**
 * Query betslips by event
 *
 * @param {string} event_id - Event ID
 * @returns {Array} Array of betslip objects
 */
function queryByEvent(event_id) {
    if (!window.pmmStore) {
        return [];
    }

    const betslip_ids = window.pmmStore.indexes.byEvent.get(event_id);

    if (!betslip_ids || betslip_ids.size === 0) {
        return [];
    }

    return Array.from(betslip_ids)
        .map(id => window.pmmStore.store.get(id))
        .filter(b => b !== undefined);
}

/**
 * Query betslips by bookie
 *
 * @param {string} bookie - Bookie name (e.g., "bf", "mbook")
 * @returns {Array} Array of betslip objects
 */
function queryByBookie(bookie) {
    if (!window.pmmStore) {
        return [];
    }

    const betslip_ids = window.pmmStore.indexes.byBookie.get(bookie);

    if (!betslip_ids || betslip_ids.size === 0) {
        return [];
    }

    return Array.from(betslip_ids)
        .map(id => window.pmmStore.store.get(id))
        .filter(b => b !== undefined);
}

/**
 * Get total available amount at or above target price
 *
 * @param {string} event_id - Event ID
 * @param {string} bet_type - Bet type
 * @param {number} targetPrice - Target price (e.g., 1.5)
 * @param {string} requiredCurrency - Currency (default: "GBP")
 * @returns {Object} Result with total amount and breakdown by bookie
 */
function getTotalAmountAtPrice(event_id, bet_type, targetPrice, requiredCurrency = 'GBP') {
    const betslips = queryMarket(event_id, bet_type);

    if (betslips.length === 0) {
        return {
            success: false,
            reason: "no_betslip",
            event_id: event_id,
            bet_type: bet_type,
            target_price: targetPrice
        };
    }

    const now = Date.now();
    const EXPIRE_MS = 30000;

    let totalAmount = 0;
    const bookieBreakdown = [];

    // Collect all tiers from all betslips
    for (const betslip of betslips) {
        for (const [bookie, data] of betslip.bookies.entries()) {
            const { status, price_tiers, last_update, top_available } = data;

            // Filter checks (same as best_executable)
            // 1. Status check
            if (status?.code !== "success") {
                continue;
            }

            // 2. Expiry check
            if (now - last_update > EXPIRE_MS) {
                continue;
            }

            // 3. Currency check
            if (top_available?.currency !== requiredCurrency) {
                continue;
            }

            // Process price tiers
            if (price_tiers && price_tiers.length > 0) {
                let bookieTotal = 0;
                const validTiers = [];

                for (const tier of price_tiers) {
                    // Only include tiers with price >= targetPrice
                    if (tier.price >= targetPrice && tier.price > 1.0) {
                        // Add the max amount from this tier
                        bookieTotal += tier.max;
                        validTiers.push({
                            price: tier.price,
                            amount: tier.max,
                            min: tier.min
                        });
                    }
                }

                if (bookieTotal > 0) {
                    totalAmount += bookieTotal;
                    bookieBreakdown.push({
                        bookie: bookie,
                        betslip_id: betslip.betslip_id,
                        total_amount: bookieTotal,
                        tiers: validTiers,
                        currency: requiredCurrency
                    });
                }
            }
        }
    }

    // Sort breakdown by total amount descending
    bookieBreakdown.sort((a, b) => b.total_amount - a.total_amount);

    return {
        success: totalAmount > 0,
        event_id: event_id,
        bet_type: bet_type,
        target_price: targetPrice,
        currency: requiredCurrency,
        total_amount: totalAmount,
        bookie_count: bookieBreakdown.length,
        bookies: bookieBreakdown
    };
}

// ==================== Mount to window.queryData ====================
if (!window.queryData) {
    window.queryData = {};
}

// PMM Query Functions
window.queryData.queryBetslipById = queryBetslipById;  // Main query by ID
window.queryData.pmmBetslipById = queryBetslipById;    // Alias for compatibility
window.queryData.pmmMarket = queryMarket;
window.queryData.getBestPrice = getBestExecutablePrice;
window.queryData.getAllPrices = getAllPrices;
window.queryData.getTotalAmountAtPrice = getTotalAmountAtPrice;
window.queryData.pmmByEvent = queryByEvent;
window.queryData.pmmByBookie = queryByBookie;

console.log('[PMM Query] Initialized and mounted to window.queryData');
