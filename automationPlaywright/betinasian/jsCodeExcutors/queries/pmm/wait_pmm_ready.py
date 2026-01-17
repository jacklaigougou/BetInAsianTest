# -*- coding: utf-8 -*-
"""
BetInAsian Wait for PMM Ready

Wait for PMM data to be stable and ready for execution
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


async def wait_for_pmm_ready(
    page,
    betslip_id: str,
    required_amount: float = 10.0,
    required_currency: str = "GBP",
    poll_interval: int = 50,
    stable_ms: int = 300,
    total_timeout: int = 4000,
    min_updates: int = 1
) -> Dict[str, Any]:
    """
    Wait for PMM data to be ready and stable

    This function waits until PMM data meets the following conditions:
    1. best_executable exists (not null)
    2. Currency matches required_currency
    3. Available amount >= required_amount
    4. Data is stable (no changes for stable_ms milliseconds)

    Args:
        page: Playwright Page object
        betslip_id: Betslip ID from CreateBetslip response
        required_amount: Required stake amount (default: 10.0)
        required_currency: Required currency (default: "GBP")
        poll_interval: Polling interval in ms (default: 50)
        stable_ms: Stable duration in ms (default: 300)
        total_timeout: Total timeout in ms (default: 4000)
        min_updates: Minimum update count (default: 1)

    Returns:
        {
            'ready': True/False,
            'elapsed': 850,              # Actual wait time (ms)
            'update_count': 3,           # Number of updates
            'stable_duration': 420,      # Stable duration (ms)
            'has_executable': True,      # Has executable price
            'has_odds': True,            # Has odds data
            'best_price': 1.95,          # Best price (only if ready=True)
            'best_bookie': 'bf',         # Best bookie (only if ready=True)
            'best_amount': 50.0,         # Best amount (only if ready=True)
            'reason': 'timeout'          # Failure reason (only if ready=False)
        }

    Examples:
        >>> # Wait for PMM data with default parameters
        >>> result = await wait_for_pmm_ready(
        ...     page,
        ...     betslip_id="xxx"
        ... )
        >>> if result['ready']:
        ...     print(f"Ready! Best price: {result['best_price']}")
        ... else:
        ...     print(f"Not ready: {result['reason']}")

        >>> # Wait with custom parameters (faster, less stable)
        >>> result = await wait_for_pmm_ready(
        ...     page,
        ...     betslip_id="xxx",
        ...     required_amount=20.0,
        ...     stable_ms=100,  # Wait only 100ms for stability
        ...     total_timeout=2000  # 2 second timeout
        ... )
    """
    try:
        logger.info(f"⏳ Waiting for PMM data: betslip_id={betslip_id}, "
                   f"amount={required_amount} {required_currency}")

        # Call window.queryData.waitForPMMReady()
        result = await page.evaluate(
            """
            (params) => {
                if (!window.queryData || !window.queryData.waitForPMMReady) {
                    return {
                        ready: false,
                        reason: 'wait_function_not_available',
                        elapsed: 0,
                        update_count: 0
                    };
                }

                return window.queryData.waitForPMMReady(
                    params.betslip_id,
                    params.required_amount,
                    params.required_currency,
                    {
                        pollInterval: params.poll_interval,
                        stableMs: params.stable_ms,
                        totalTimeout: params.total_timeout,
                        minUpdates: params.min_updates
                    }
                );
            }
            """,
            {
                "betslip_id": betslip_id,
                "required_amount": required_amount,
                "required_currency": required_currency,
                "poll_interval": poll_interval,
                "stable_ms": stable_ms,
                "total_timeout": total_timeout,
                "min_updates": min_updates
            }
        )

        # Log result
        if result.get('ready'):
            logger.info(f"✅ PMM data ready:")
            # logger.info(f"  - Elapsed: {result.get('elapsed')}ms")
            # logger.info(f"  - Updates: {result.get('update_count')}")
            # logger.info(f"  - Stable duration: {result.get('stable_duration')}ms")
            # logger.info(f"  - Best price: {result.get('best_price')}")
            # logger.info(f"  - Best bookie: {result.get('best_bookie')}")
            # logger.info(f"  - Best amount: {result.get('best_amount')}")
        else:
            logger.warning(f"⚠️ PMM data not ready:")
            # logger.warning(f"  - Reason: {result.get('reason')}")
            # logger.warning(f"  - Elapsed: {result.get('elapsed')}ms")
            # logger.warning(f"  - Updates: {result.get('update_count')}")

        return result

    except Exception as e:
        logger.error(f"❌ Exception in wait_for_pmm_ready: {e}")
        return {
            'ready': False,
            'reason': 'exception',
            'error': str(e),
            'elapsed': 0,
            'update_count': 0
        }
