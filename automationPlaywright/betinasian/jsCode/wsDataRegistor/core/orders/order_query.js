/**
 * Order & Bet Query Functions
 *
 * Query interface for order and bet stores
 */

// ==================== Order Queries ====================

/**
 * Query order by ID
 * @param {string} order_id - Order ID
 * @returns {Object|null} Order data with bet_bar computed on demand
 */
function queryOrderById(order_id) {
    if (!window.orderStore) {
        return null;
    }

    const order = window.orderStore.store.get(order_id);
    if (!order) {
        return null;
    }

    // Compute bet_bar on demand
    const betBar = window.orderStore.getOrderBetBar(order_id);

    // Get state summary
    let stateSummary = null;
    if (window.orderStateMachine) {
        stateSummary = window.orderStateMachine.getStateSummary(order);
    }

    return {
        ...order,
        bet_bar: betBar,
        state_summary: stateSummary
    };
}

/**
 * Get orders by state
 * @param {string} state - Order state (CREATED, OPEN, PLACED, FINISHED, EXPIRED_LOCAL)
 * @returns {Array} Array of order data
 */
function getOrdersByStatus(state) {
    if (!window.orderStore || !window.orderStore.indexes.byState.has(state)) {
        return [];
    }

    const order_ids = window.orderStore.indexes.byState.get(state);
    const orders = [];

    for (const order_id of order_ids) {
        const order = queryOrderById(order_id);
        if (order) {
            orders.push(order);
        }
    }

    return orders;
}

/**
 * Get orders by event
 * @param {string} event_id - Event ID
 * @returns {Array} Array of order data
 */
function getOrdersByEvent(event_id) {
    if (!window.orderStore || !window.orderStore.indexes.byEvent.has(event_id)) {
        return [];
    }

    const order_ids = window.orderStore.indexes.byEvent.get(event_id);
    const orders = [];

    for (const order_id of order_ids) {
        const order = queryOrderById(order_id);
        if (order) {
            orders.push(order);
        }
    }

    return orders;
}

/**
 * Get orders by bookie
 * @param {string} bookie - Bookie name
 * @returns {Array} Array of order data
 */
function getOrdersByBookie(bookie) {
    if (!window.orderStore || !window.orderStore.indexes.byBookie.has(bookie)) {
        return [];
    }

    const order_ids = window.orderStore.indexes.byBookie.get(bookie);
    const orders = [];

    for (const order_id of order_ids) {
        const order = queryOrderById(order_id);
        if (order) {
            orders.push(order);
        }
    }

    return orders;
}

/**
 * Get all orders
 * @returns {Array} Array of order data
 */
function getAllOrders() {
    if (!window.orderStore) {
        return [];
    }

    const orders = [];
    for (const [order_id, order] of window.orderStore.store.entries()) {
        const orderData = queryOrderById(order_id);
        if (orderData) {
            orders.push(orderData);
        }
    }

    return orders;
}

// ==================== Bet Queries ====================

/**
 * Query bet by ID
 * @param {string} bet_id - Bet ID
 * @returns {Object|null} Bet data with slippage computed on demand
 */
function queryBetById(bet_id) {
    if (!window.betStore) {
        return null;
    }

    const bet = window.betStore.store.get(bet_id);
    if (!bet) {
        return null;
    }

    // Compute slippage if matched
    let slippage = null;
    if (bet.status === 'MATCHED') {
        slippage = window.betStore.calculateSlippage(bet_id);
    }

    return {
        ...bet,
        slippage: slippage
    };
}

/**
 * Get bets by order
 * @param {string} order_id - Order ID
 * @returns {Array} Array of bet data
 */
function getBetsByOrder(order_id) {
    if (!window.betStore) {
        return [];
    }

    const bets = window.betStore.getBetsByOrder(order_id);
    return bets.map(bet => queryBetById(bet.bet_id));
}

/**
 * Get bets by bookie
 * @param {string} bookie - Bookie name
 * @returns {Array} Array of bet data
 */
function getBetsByBookie(bookie) {
    if (!window.betStore || !window.betStore.indexes.byBookie.has(bookie)) {
        return [];
    }

    const bet_ids = window.betStore.indexes.byBookie.get(bookie);
    const bets = [];

    for (const bet_id of bet_ids) {
        const bet = queryBetById(bet_id);
        if (bet) {
            bets.push(bet);
        }
    }

    return bets;
}

/**
 * Get bets by status
 * @param {string} status - Bet status
 * @returns {Array} Array of bet data
 */
function getBetsByStatus(status) {
    if (!window.betStore || !window.betStore.indexes.byStatus.has(status)) {
        return [];
    }

    const bet_ids = window.betStore.indexes.byStatus.get(status);
    const bets = [];

    for (const bet_id of bet_ids) {
        const bet = queryBetById(bet_id);
        if (bet) {
            bets.push(bet);
        }
    }

    return bets;
}

/**
 * Get bets by event
 * @param {string} event_id - Event ID
 * @returns {Array} Array of bet data
 */
function getBetsByEvent(event_id) {
    if (!window.betStore || !window.betStore.indexes.byEvent.has(event_id)) {
        return [];
    }

    const bet_ids = window.betStore.indexes.byEvent.get(event_id);
    const bets = [];

    for (const bet_id of bet_ids) {
        const bet = queryBetById(bet_id);
        if (bet) {
            bets.push(bet);
        }
    }

    return bets;
}

// ==================== Combined Queries ====================

/**
 * Get order with its bets
 * @param {string} order_id - Order ID
 * @returns {Object|null} {order: {...}, bets: [...]}
 */
function getOrderWithBets(order_id) {
    const order = queryOrderById(order_id);
    if (!order) {
        return null;
    }

    const bets = getBetsByOrder(order_id);

    return {
        order: order,
        bets: bets
    };
}

/**
 * Check slippage for all bets in an order
 * @param {string} order_id - Order ID
 * @returns {Object|null} {order_id, total_slippage, bets: [...]}
 */
function checkOrderSlippage(order_id) {
    const bets = getBetsByOrder(order_id);
    if (bets.length === 0) {
        return null;
    }

    let totalSlippage = 0;
    let betCount = 0;

    const betSlippages = [];

    for (const bet of bets) {
        if (bet.slippage) {
            totalSlippage += bet.slippage.slippage;
            betCount++;
            betSlippages.push({
                bet_id: bet.bet_id,
                bookie: bet.bookie,
                requested_price: bet.slippage.requested_price,
                matched_price: bet.slippage.matched_price,
                slippage: bet.slippage.slippage,
                slippage_pct: bet.slippage.slippage_pct
            });
        }
    }

    const avgSlippage = betCount > 0 ? totalSlippage / betCount : 0;

    return {
        order_id: order_id,
        total_slippage: totalSlippage,
        avg_slippage: avgSlippage,
        avg_slippage_pct: (avgSlippage * 100).toFixed(4) + '%',
        bet_count: betCount,
        bets: betSlippages
    };
}

/**
 * Get statistics
 * @returns {Object} Combined stats for orders and bets
 */
function getOrderBetStats() {
    const stats = {
        orders: window.orderStore ? window.orderStore.getStats() : {},
        bets: window.betStore ? window.betStore.getStats() : {},
        handlers: {
            order_handler: window.__orderHandler ? window.__orderHandler.getStats() : {},
            bet_handler: window.__betHandler ? window.__betHandler.getStats() : {}
        }
    };

    return stats;
}

// ==================== Export to window.queryData ====================
if (typeof window !== 'undefined') {
    // Preserve existing window.queryData
    const existingQueryData = window.queryData || {};

    window.queryData = {
        ...existingQueryData,

        // Order queries
        queryOrderById: queryOrderById,
        getOrdersByStatus: getOrdersByStatus,
        getOrdersByEvent: getOrdersByEvent,
        getOrdersByBookie: getOrdersByBookie,
        getAllOrders: getAllOrders,

        // Bet queries
        queryBetById: queryBetById,
        getBetsByOrder: getBetsByOrder,
        getBetsByBookie: getBetsByBookie,
        getBetsByStatus: getBetsByStatus,
        getBetsByEvent: getBetsByEvent,

        // Combined queries
        getOrderWithBets: getOrderWithBets,
        checkOrderSlippage: checkOrderSlippage,
        getOrderBetStats: getOrderBetStats
    };

    console.log('[Order Query] Initialized and exported to window.queryData');
}
