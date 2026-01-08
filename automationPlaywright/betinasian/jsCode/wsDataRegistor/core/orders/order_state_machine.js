/**
 * Order State Machine
 *
 * Order lifecycle: CREATED → OPEN → PLACED → FINISHED / EXPIRED_LOCAL
 *
 * State transition rules:
 * 1. CREATED: Initial state when order is first seen
 * 2. OPEN: Order is open and accepting bets (unplaced > 0)
 * 3. PLACED: All bets placed, waiting for matches (unplaced === 0, inprogress > 0)
 * 4. FINISHED: All bets matched or cancelled (isDone() === true)
 * 5. EXPIRED_LOCAL: Order timeout detected locally
 *
 * Special case: "order open + bet done"
 * - Order status = "OPEN"
 * - But isDone() returns true (all bets already matched)
 * - This is a valid state, don't transition to PLACED
 */

// ==================== State Machine ====================
class OrderStateMachine {
    constructor() {
        this.transitions = {
            'CREATED': ['OPEN', 'PLACED', 'FINISHED', 'EXPIRED_LOCAL'],
            'OPEN': ['PLACED', 'FINISHED', 'EXPIRED_LOCAL'],
            'PLACED': ['FINISHED', 'EXPIRED_LOCAL'],
            'FINISHED': [],  // Terminal state
            'EXPIRED_LOCAL': []  // Terminal state
        };
    }

    /**
     * Check if order is done (all bets matched or no more active bets)
     * @param {Object} order - Order data
     * @returns {boolean}
     */
    isDone(order) {
        const { success, inprogress, danger, unplaced } = order;

        // Calculate totals
        const successTotal = this._sumStakes(success);
        const inprogressTotal = this._sumStakes(inprogress);
        const dangerTotal = this._sumStakes(danger);
        const unplacedTotal = this._sumStakes(unplaced);
        const totalStake = successTotal + inprogressTotal + dangerTotal + unplacedTotal;

        // IMPORTANT: Must have some stake to be considered done
        // Otherwise "all zeros" would be treated as FINISHED
        if (totalStake === 0) {
            return false;
        }

        // Done if:
        // 1. All bets are in success (successTotal > 0 and others === 0)
        // 2. No active bets (inprogress === 0, unplaced === 0, danger === 0)
        if (successTotal > 0 && inprogressTotal === 0 && dangerTotal === 0 && unplacedTotal === 0) {
            return true;
        }

        if (inprogressTotal === 0 && unplacedTotal === 0 && dangerTotal === 0) {
            return true;
        }

        return false;
    }

    /**
     * Determine next state based on current state and bet bar
     * @param {Object} order - Order data
     * @returns {string} Next state
     */
    determineNextState(order) {
        const currentState = order.state || 'CREATED';

        // Terminal states cannot transition
        if (currentState === 'FINISHED' || currentState === 'EXPIRED_LOCAL') {
            return currentState;
        }

        // Check if done
        if (this.isDone(order)) {
            return 'FINISHED';
        }

        // Calculate bet bar
        const successTotal = this._sumStakes(order.success);
        const inprogressTotal = this._sumStakes(order.inprogress);
        const dangerTotal = this._sumStakes(order.danger);
        const unplacedTotal = this._sumStakes(order.unplaced);

        // State transition logic
        if (unplacedTotal > 0) {
            // Still has unplaced bets → OPEN
            return 'OPEN';
        } else if (inprogressTotal > 0 || dangerTotal > 0) {
            // All bets placed, some in progress → PLACED
            return 'PLACED';
        } else if (successTotal > 0) {
            // All bets matched → FINISHED
            return 'FINISHED';
        } else {
            // No bets at all → keep current state
            return currentState;
        }
    }

    /**
     * Check if transition is allowed
     * @param {string} from - Current state
     * @param {string} to - Next state
     * @returns {boolean}
     */
    canTransition(from, to) {
        if (from === to) return true;
        const allowed = this.transitions[from];
        return allowed && allowed.includes(to);
    }

    /**
     * Transition order state
     * @param {Object} order - Order data
     * @returns {Object} {changed: boolean, oldState: string, newState: string}
     */
    transition(order) {
        const currentState = order.state || 'CREATED';
        const nextState = this.determineNextState(order);

        if (currentState === nextState) {
            return {
                changed: false,
                oldState: currentState,
                newState: nextState
            };
        }

        if (!this.canTransition(currentState, nextState)) {
            console.warn(`[State Machine] Invalid transition: ${currentState} → ${nextState} for order ${order.order_id}`);
            return {
                changed: false,
                oldState: currentState,
                newState: currentState
            };
        }

        console.log(`[State Machine] Transition: ${currentState} → ${nextState} for order ${order.order_id}`);
        order.state = nextState;
        order.last_update = Date.now();

        return {
            changed: true,
            oldState: currentState,
            newState: nextState
        };
    }

    /**
     * Sum stakes from bet array
     * @param {Array} bets - Array of [bookie, stake] tuples
     * @returns {number}
     */
    _sumStakes(bets) {
        if (!bets || !Array.isArray(bets)) return 0;
        return bets.reduce((sum, bet) => sum + (bet[1] || 0), 0);
    }

    /**
     * Get state summary
     * @param {Object} order - Order data
     * @returns {Object}
     */
    getStateSummary(order) {
        const successTotal = this._sumStakes(order.success);
        const inprogressTotal = this._sumStakes(order.inprogress);
        const dangerTotal = this._sumStakes(order.danger);
        const unplacedTotal = this._sumStakes(order.unplaced);

        const totalStake = successTotal + inprogressTotal + dangerTotal + unplacedTotal;

        return {
            state: order.state,
            raw_status: order.raw_status,
            isDone: this.isDone(order),
            betBar: {
                success: successTotal,
                inprogress: inprogressTotal,
                danger: dangerTotal,
                unplaced: unplacedTotal,
                total: totalStake
            },
            nextState: this.determineNextState(order)
        };
    }
}

// ==================== Export ====================
const stateMachine = new OrderStateMachine();

window.orderStateMachine = stateMachine;

console.log('[Order State Machine] Initialized');
