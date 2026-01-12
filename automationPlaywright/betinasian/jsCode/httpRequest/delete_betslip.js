// delete_betslip.js - Delete Betslip Request
// DELETE https://black.betinasia.com/v1/betslips/{betslip_id}/
// Deletes an existing betslip

/**
 * Delete Betslip
 *
 * @param {string} betslipId - Betslip ID to delete (e.g., "5b0c08d6be3d44d2abe468e2a26755a5")
 *
 * @returns {Object} Response object with status, data, and timestamp
 *
 * @example
 * deleteBetslip("5b0c08d6be3d44d2abe468e2a26755a5")
 */
async function deleteBetslip(betslipId) {
    try {
        // Validate input
        if (!betslipId || typeof betslipId !== 'string') {
            throw new Error('betslipId must be a non-empty string');
        }

        // Construct request URL
        const url = `https://black.betinasia.com/v1/betslips/${betslipId}/`;

        // Get session from cookie
        const sessionMatch = document.cookie.match(/root-session=([^;]+)/);
        const sessionId = sessionMatch ? sessionMatch[1] : '';

        if (!sessionId) {
            throw new Error('Session not found in cookies');
        }

        console.log('[DeleteBetslip] 🗑️ Deleting betslip:', {
            betslipId: betslipId,
            url: url
        });

        // Use fetch API with required headers
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://black.betinasia.com',
                'Referer': 'https://black.betinasia.com/sportsbook',
                'session': sessionId,
                'x-molly-client-name': 'sonic',
                'x-molly-client-version': '2.5.9'
            },
            credentials: 'include'
        });

        console.log('[DeleteBetslip] 📥 Response received:', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok
        });

        // Parse response (may be empty for DELETE)
        let responseData = null;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            try {
                responseData = await response.json();
            } catch (e) {
                // Response may be empty, which is fine for DELETE
                console.log('[DeleteBetslip] No JSON response body (expected for DELETE)');
            }
        }

        // Return response
        return {
            success: response.ok,
            status: response.status,
            statusText: response.statusText,
            data: responseData,
            timestamp: new Date().toISOString(),
            request: {
                url: url,
                method: 'DELETE',
                betslipId: betslipId
            }
        };

    } catch (error) {
        console.error('[DeleteBetslip] ❌ Error:', error);
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
    window.deleteBetslip = deleteBetslip;
}

// Export for module usage (if applicable)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = deleteBetslip;
}
