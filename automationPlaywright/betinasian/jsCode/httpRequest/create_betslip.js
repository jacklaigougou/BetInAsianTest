// create_betslip.js - Create Betslip Request
// POST https://black.betinasia.com/v1/betslips/
// Creates a new betslip for betting

/**
 * Create Betslip
 *
 * @param {Object} betData - Bet data object
 * @param {string} betData.sport - Sport type (e.g., "basket", "fb")
 * @param {string} betData.event_id - Event ID (e.g., "2026-01-06,41024,40990")
 * @param {string} betData.bet_type - Bet type (e.g., "for,ml,a" or "for,ah,h,-22")
 * @param {string} betData.betslip_type - Betslip type (default: "normal")
 * @param {boolean} betData.equivalent_bets - Whether to include equivalent bets (default: true)
 *
 * @returns {Object} Response object with status, data, and timestamp
 *
 * @example
 * // Money Line bet
 * createBetslip({
 *     sport: "basket",
 *     event_id: "2026-01-06,41024,40990",
 *     bet_type: "for,ml,a",
 *     betslip_type: "normal",
 *     equivalent_bets: true
 * })
 *
 * @example
 * // Asian Handicap bet with line_id
 * createBetslip({
 *     sport: "basket",
 *     event_id: "2026-01-06,41024,40990",
 *     bet_type: "for,ah,h,-22",
 *     betslip_type: "normal",
 *     equivalent_bets: true
 * })
 */
async function createBetslip(betData) {
    try {
        // Validate input
        if (!betData || typeof betData !== 'object') {
            throw new Error('betData must be an object');
        }

        if (!betData.sport) {
            throw new Error('sport is required');
        }

        if (!betData.event_id) {
            throw new Error('event_id is required');
        }

        if (!betData.bet_type) {
            throw new Error('bet_type is required');
        }

        // Construct request URL
        const url = 'https://black.betinasia.com/v1/betslips/';

        // Prepare POST data
        const postData = {
            sport: betData.sport,
            event_id: betData.event_id,
            bet_type: betData.bet_type,
            betslip_type: betData.betslip_type || 'normal',
            equivalent_bets: betData.equivalent_bets !== undefined ? betData.equivalent_bets : true
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
                'x-molly-client-version': '2.5.4'
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
        console.error('create_betslip error:', error);
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
    window.createBetslip = createBetslip;
}

// Export for module usage (if applicable)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = createBetslip;
}
