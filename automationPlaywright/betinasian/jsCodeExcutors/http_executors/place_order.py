# -*- coding: utf-8 -*-
"""
BetInAsian Place Order Executor

Place a betting order on a betslip with specified price and stake
"""
from typing import Dict, Any
import logging
import json
from utils import get_js_loader

logger = logging.getLogger(__name__)


async def place_order(
    page,
    betslip_id: str,
    price: float,
    stake: float,
    currency: str = "USD",
    duration: int = 10,
    keep_open_ir: bool = False,
    exchange_mode: str = "make_and_take",
    adaptive_bookies: list = None,
    accounts: list = None,
    request_uuid: str = None
) -> Dict[str, Any]:
    """
    Place a betting order

    Args:
        page: Playwright Page object
        betslip_id: Betslip ID from create_betslip response
        price: Target price/odds (must be > 1.0)
        stake: Stake amount in base currency (must be > 0)
        currency: Currency code (default: "USD")
        duration: Order duration in seconds (default: 10)
        keep_open_ir: Keep open in-running (default: False)
        exchange_mode: Exchange mode (default: "make_and_take")
        adaptive_bookies: Adaptive bookies list (default: [])
        accounts: Specific accounts list (default: [])
        request_uuid: Request UUID (auto-generated if not provided)

    Returns:
        {
            'success': True/False,
            'status': HTTP status code,
            'data': Response data from server,
            'timestamp': ISO timestamp
        }

    Examples:
        >>> # Place order with minimum parameters
        >>> result = await place_order(
        ...     page=page,
        ...     betslip_id="fe7d055dee2742cab7253a1b6937cfad",
        ...     price=1.14,
        ...     stake=1
        ... )

        >>> # Place order with custom parameters
        >>> result = await place_order(
        ...     page=page,
        ...     betslip_id="fe7d055dee2742cab7253a1b6937cfad",
        ...     price=1.20,
        ...     stake=10,
        ...     currency="GBP",
        ...     duration=15
        ... )
    """
    try:
        logger.info(f"Placing order: betslip_id={betslip_id}, price={price}, stake={stake} {currency}")

        # Load JS code
        js_loader = get_js_loader()
        js_code = js_loader.get_js_content(
            platform_name='betinasian',
            relative_path='httpRequest/place_order.js'
        )

        if not js_code:
            logger.error("Failed to load place_order.js")
            return {
                'success': False,
                'error': 'Failed to load place_order.js',
                'status': 0
            }

        # Prepare order data
        order_data = {
            'betslip_id': betslip_id,
            'price': price,
            'stake': stake,
            'currency': currency,
            'duration': duration,
            'keep_open_ir': keep_open_ir,
            'exchange_mode': exchange_mode,
            'adaptive_bookies': adaptive_bookies if adaptive_bookies is not None else [],
            'accounts': accounts if accounts is not None else []
        }

        if request_uuid:
            order_data['request_uuid'] = request_uuid

        logger.info(f"Order data: {json.dumps(order_data, indent=2)}")

        # Wrap JS code in normal function (not arrow function)
        wrapped_js = f"""
async function(orderData) {{
{js_code}

    // Call the placeOrder function
    return await placeOrder(orderData);
}}
"""

        # Execute request
        result = await page.evaluate(wrapped_js, order_data)

        # Process result
        if result.get('success'):
            logger.info(f"✅ Order placed successfully: status={result.get('status')}")
            logger.info(f"Response data: {json.dumps(result.get('data'), indent=2)}")

            return {
                'success': True,
                'status': result.get('status'),
                'data': result.get('data'),
                'timestamp': result.get('timestamp')
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            status = result.get('status', 0)
            response_data = result.get('data')

            logger.error(f"❌ Failed to place order: {error_msg}")
            logger.error(f"   Status: {status}")
            logger.error(f"   Response data: {json.dumps(response_data, indent=2) if response_data else 'None'}")

            return {
                'success': False,
                'error': error_msg,
                'status': status,
                'data': response_data,
                'timestamp': result.get('timestamp')
            }

    except Exception as e:
        logger.error(f"❌ Exception in place_order: {e}")
        return {
            'success': False,
            'error': str(e),
            'status': 0
        }
