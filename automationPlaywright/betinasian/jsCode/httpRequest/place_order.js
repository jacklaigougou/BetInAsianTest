// place_order.js - Place Order Request
// POST https://black.betinasia.com/v1/orders/
// Places a betting order on a betslip

/**
 * Generate a random UUID v4
 * @returns {string} UUID string
 */
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * Place Order
 *
 * @param {Object} orderData - Order data object
 * @param {string} orderData.betslip_id - Betslip ID from create_betslip response
 * @param {number} orderData.price - Target price/odds (e.g., 1.14)
 * @param {number} orderData.stake - Stake amount in base currency (e.g., 1)
 * @param {string} orderData.currency - Currency code (default: "USD")
 * @param {number} orderData.duration - Order duration in seconds (default: 10)
 * @param {boolean} orderData.keep_open_ir - Keep open in-running (default: false)
 * @param {string} orderData.exchange_mode - Exchange mode (default: "make_and_take")
 * @param {Array} orderData.adaptive_bookies - Adaptive bookies list (default: [])
 * @param {Array} orderData.accounts - Specific accounts list (default: [])
 * @param {string} orderData.request_uuid - Request UUID (auto-generated if not provided)
 *
 * @returns {Object} Response object with status, data, and timestamp
 *
 * @example
 * // Place order with minimum parameters
 * placeOrder({
 *     betslip_id: "fe7d055dee2742cab7253a1b6937cfad",
 *     price: 1.14,
 *     stake: 1
 * })
 *
 * @example
 * // Place order with all parameters
 * placeOrder({
 *     betslip_id: "fe7d055dee2742cab7253a1b6937cfad",
 *     price: 1.14,
 *     stake: 10,
 *     currency: "GBP",
 *     duration: 15,
 *     keep_open_ir: true,
 *     exchange_mode: "make_and_take",
 *     adaptive_bookies: [],
 *     accounts: []
 * })
 */
async function placeOrder(orderData) {
    try {
        // Validate input
        if (!orderData || typeof orderData !== 'object') {
            throw new Error('orderData must be an object');
        }

        if (!orderData.betslip_id) {
            throw new Error('betslip_id is required');
        }

        if (orderData.price === undefined || orderData.price === null) {
            throw new Error('price is required');
        }

        if (orderData.stake === undefined || orderData.stake === null) {
            throw new Error('stake is required');
        }

        // Validate price
        if (typeof orderData.price !== 'number' || orderData.price <= 1.0) {
            throw new Error('price must be a number greater than 1.0');
        }

        // Validate stake
        if (typeof orderData.stake !== 'number' || orderData.stake <= 0) {
            throw new Error('stake must be a positive number');
        }

        // Construct request URL
        const url = 'https://black.betinasia.com/v1/orders/';

        // Prepare POST data
        const postData = {
            betslip_id: orderData.betslip_id,
            price: orderData.price,
            stake: [
                orderData.currency || 'USD',
                orderData.stake
            ],
            duration: orderData.duration !== undefined ? orderData.duration : 10,
            keep_open_ir: orderData.keep_open_ir !== undefined ? orderData.keep_open_ir : false,
            adaptive_bookies: orderData.adaptive_bookies || [],
            accounts: orderData.accounts || [],
            exchange_mode: orderData.exchange_mode || 'make_and_take',
            request_uuid: orderData.request_uuid || generateUUID()
        };

        // Get session from cookie
        const sessionMatch = document.cookie.match(/root-session=([^;]+)/);
        const sessionId = sessionMatch ? sessionMatch[1] : '';

        if (!sessionId) {
            throw new Error('Session not found in cookies');
        }

        // Log request details for debugging
        console.log('[PlaceOrder] 🚀 Sending order request:', {
            url: url,
            method: 'POST',
            body: postData
        });

        // Use fetch API with required headers
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
                'session': sessionId,
                'x-molly-client-name': 'sonic',
                'x-molly-client-version': '2.5.15'
            },
            body: JSON.stringify(postData),
            credentials: 'include'
        });

        console.log('[PlaceOrder] 📥 Response received:', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok
        });

        const responseData = await response.json();

        // Return response
        return {
            success: response.ok,
            status: response.status,
            statusText: response.statusText,
            data: responseData,
            timestamp: new Date().toISOString(),
            request: {
                url: url,
                method: 'POST',
                body: postData
            }
        };

    } catch (error) {
        console.error('place_order error:', error);
        return {
            success: false,
            error: error.message,
            status: 0,
            timestamp: new Date().toISOString()
        };
    }
}

// Make function globally available
