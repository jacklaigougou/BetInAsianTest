// close_order.js - Close Order Request
// POST https://black.betinasia.com/v1/orders/{orderId}/close/
// Closes an existing order

/**
 * Close Order
 *
 * @param {number|string} orderId - Order ID to close (e.g., 1050357659)
 *
 * @returns {Object} Response object with status, data, and timestamp
 *
 * @example
 * // Close an order
 * closeOrder(1050357659)
 *
 * @example
 * // Close an order with string ID
 * closeOrder("1050357659")
 */
async function closeOrder(orderId) {
    try {
        // Validate input
        if (!orderId) {
            throw new Error('orderId is required');
        }

        // Convert to number if string
        const orderIdNum = typeof orderId === 'string' ? parseInt(orderId, 10) : orderId;

        if (isNaN(orderIdNum)) {
            throw new Error('orderId must be a valid number');
        }

        // Construct request URL
        const url = `https://black.betinasia.com/v1/orders/${orderIdNum}/close/`;

        // Prepare POST data
        const postData = {
            orderId: orderIdNum
        };

        // Get session from cookie
        const sessionMatch = document.cookie.match(/root-session=([^;]+)/);
        const sessionId = sessionMatch ? sessionMatch[1] : '';

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
        console.error('close_order error:', error);
        return {
            success: false,
            error: error.message,
            status: 0,
            timestamp: new Date().toISOString()
        };
    }
}

// Make function globally available
if (typeof window !== 'undefined') {
    window.closeOrder = closeOrder;
}

// Export for module usage (if applicable)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = closeOrder;
}
