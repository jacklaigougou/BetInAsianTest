# -*- coding: utf-8 -*-
"""
BetInAsian Create Betslip

Create a new betslip by sending POST request to /v1/betslips/
"""
from typing import Dict, Any
import logging
import json
from utils.js_loader import get_js_loader

logger = logging.getLogger(__name__)


async def create_betslip(
    page,
    sport: str,
    event_id: str,
    bet_type: str,
    betslip_type: str = "normal",
    equivalent_bets: bool = True
) -> Dict[str, Any]:
    """
    Create a new betslip

    Args:
        page: Playwright Page object
        sport: Sport type
            - Basketball: "basket" (全场), "basket_ht" (半场),
                         "basket_q1" (第1节), "basket_q2" (第2节),
                         "basket_q3" (第3节), "basket_q4" (第4节)
            - Soccer: "fb" (全场), "fb_ht" (半场), "fb_et" (加时赛),
                     "fb_corn" (全场角球), "fb_corn_ht" (半场角球)
        event_id: Event ID (e.g., "2026-01-06,41024,40990")
        bet_type: Bet type (e.g., "for,ml,a" or "for,ah,h,-22")
        betslip_type: Betslip type (default: "normal")
        equivalent_bets: Include equivalent bets (default: True)

    Returns:
        {
            'success': True/False,
            'status': 200,
            'data': {...},  # Response data from API
            'error': 'error message'  # Only if success=False
        }

    Examples:
        >>> # Money Line bet
        >>> result = await create_betslip(
        ...     page,
        ...     sport="basket",
        ...     event_id="2026-01-06,41024,40990",
        ...     bet_type="for,ml,a"
        ... )

        >>> # Asian Handicap bet with line_id
        >>> result = await create_betslip(
        ...     page,
        ...     sport="basket",
        ...     event_id="2026-01-06,41024,40990",
        ...     bet_type="for,ah,h,-22"
        ... )
    """
    try:
        logger.info(f"Creating betslip: sport={sport}, event_id={event_id}, bet_type={bet_type}")

        # Load JS function from JSLoader
        js_loader = get_js_loader()
        js_code = js_loader.get_js_content("betinasian", "httpRequest/create_betslip.js")

        if not js_code:
            raise FileNotFoundError("create_betslip.js not found in JSLoader cache")

        # Prepare bet data
        bet_data = {
            "sport": sport,
            "event_id": event_id,
            "bet_type": bet_type,
            "betslip_type": betslip_type,
            "equivalent_bets": equivalent_bets
        }

        logger.info(f"Bet data: {json.dumps(bet_data, indent=2)}")

        # Use normal function (not arrow function) so 'arguments' is available
        wrapped_js = f"""
async function(betData) {{
{js_code}

    // Call the createBetslip function
    return await createBetslip(betData);
}}
"""

        # Execute request
        result = await page.evaluate(wrapped_js, bet_data)

        # Process result
        if result.get('success'):
            betslip_id = result.get('data', {}).get('betslip_id')
            logger.info(f"✅ Betslip created successfully: betslip_id={betslip_id}, status={result.get('status')}")

            return {
                'success': True,
                'status': result.get('status'),
                'data': result.get('data'),
                'timestamp': result.get('timestamp')
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ Failed to create betslip: {error_msg}")

            return {
                'success': False,
                'error': error_msg,
                'status': result.get('status', 0),
                'data': result.get('data'),
                'timestamp': result.get('timestamp')
            }

    except Exception as e:
        logger.error(f"❌ Exception in create_betslip: {e}")
        return {
            'success': False,
            'error': str(e),
            'status': 0
        }


async def create_betslip_from_mapping(
    page,
    event_id: str,
    mapping: Dict[str, Any],
    sport: str = "basket"
) -> Dict[str, Any]:
    """
    Create betslip using mapping result from MappingBetburgerToBetinisian

    Args:
        page: Playwright Page object
        event_id: Event ID
        mapping: Mapping result from parse_spider_market()
        sport: Sport type (default: "basket")

    Returns:
        Same as create_betslip()

    Examples:
        >>> from MappingBetburgerToBetinisian import parse_spider_market
        >>>
        >>> # Parse spider market
        >>> mapping = parse_spider_market("basket", "17", -5.5)
        >>> # mapping = {
        >>> #     "betinasian_market": "ah",
        >>> #     "betinasian_side": "h",
        >>> #     "line_id": -22,
        >>> #     "description": "Asian Handicap - Home"
        >>> # }
        >>>
        >>> # Create betslip
        >>> result = await create_betslip_from_mapping(
        ...     page,
        ...     event_id="2026-01-06,41024,40990",
        ...     mapping=mapping,
        ...     sport="basket"
        ... )
    """
    # Construct bet_type from mapping
    # Format: "for,{market},{side},{line_id}"
    # or "for,{market},{side}" (if no line_id)

    market = mapping.get('betinasian_market')
    side = mapping.get('betinasian_side')
    line_id = mapping.get('line_id')

    if line_id is not None:
        # With line_id (Asian Handicap, Over/Under, etc.)
        bet_type = f"for,{market},{side},{line_id}"
    else:
        # Without line_id (Money Line, BTTS, etc.)
        bet_type = f"for,{market},{side}"

    logger.info(f"Constructed bet_type from mapping: {bet_type}")
    logger.info(f"Mapping details: {mapping}")

    # Create betslip
    return await create_betslip(
        page=page,
        sport=sport,
        event_id=event_id,
        bet_type=bet_type
    )


def parse_bet_type_from_mapping(mapping: Dict[str, Any]) -> str:
    """
    Parse bet_type string from mapping result

    Args:
        mapping: Mapping result from parse_spider_market()

    Returns:
        Bet type string (e.g., "for,ah,h,-22")

    Examples:
        >>> mapping = {
        ...     "betinasian_market": "ah",
        ...     "betinasian_side": "h",
        ...     "line_id": -22
        ... }
        >>> parse_bet_type_from_mapping(mapping)
        "for,ah,h,-22"

        >>> mapping = {
        ...     "betinasian_market": "ml",
        ...     "betinasian_side": "h"
        ... }
        >>> parse_bet_type_from_mapping(mapping)
        "for,ml,h"
    """
    market = mapping.get('betinasian_market')
    side = mapping.get('betinasian_side')
    line_id = mapping.get('line_id')

    if line_id is not None:
        return f"for,{market},{side},{line_id}"
    else:
        return f"for,{market},{side}"
