# -*- coding: utf-8 -*-
"""
BetInAsian Bet Type String Builder

Constructs BetInAsian bet_type strings from mapping dictionaries.

Bet Type Formats:
1. Simple format (Soccer 1X2): "for,{side}"
   Example: "for,h" (Home Win)

2. Custom formats (Soccer special cases):
   - Both Teams Score: "for,score,both" or "for,score,both,no"
   - Odd/Even: "for,odd" or "for,even"
   - Double Chance: "for,dc,{side1},{side2}" (e.g., "for,dc,h,d")

3. IR format (Soccer Asian Handicap, Over/Under): "for,ir,0,0,{market},{side},{line_id}"
   Example: "for,ir,0,0,ah,h,-2" (Asian Handicap -0.5 for Home)
   Special: Over/Under without side: "for,ir,0,0,ahover,10"

4. Standard format (Basketball, etc.): "for,{market},{side},{line_id}"
   Example: "for,ah,h,-22" (Asian Handicap -5.5 for Home)

5. Standard format without line: "for,{market},{side}"
   Example: "for,ml,h" (Money Line for Home)
"""

from typing import Dict, Any, Optional


def build(mapping: Dict[str, Any]) -> Optional[str]:
    """
    Build BetInAsian bet_type string from mapping dictionary

    Args:
        mapping: Mapping result from parse_spider_market()
            {
                "betinasian_market": "ah",     # Market type
                "betinasian_side": "h",        # Bet side
                "line_id": -22,                # Line ID (optional)
                "simple_format": True,         # Simple format flag (optional)
                "use_ir_format": True,         # IR format flag (optional)
                "description": "..."           # Description (ignored)
            }

    Returns:
        bet_type string or None if mapping is invalid

    Examples:
        >>> # Simple format (Soccer 1X2)
        >>> mapping = {"betinasian_side": "h", "simple_format": True}
        >>> build(mapping)
        "for,h"

        >>> # IR format with side (Soccer Asian Handicap)
        >>> mapping = {
        ...     "betinasian_market": "ah",
        ...     "betinasian_side": "h",
        ...     "line_id": -2,
        ...     "use_ir_format": True
        ... }
        >>> build(mapping)
        "for,ir,0,0,ah,h,-2"

        >>> # IR format without side (Soccer Over/Under)
        >>> mapping = {
        ...     "betinasian_market": "ahover",
        ...     "line_id": 10,
        ...     "use_ir_format": True
        ... }
        >>> build(mapping)
        "for,ir,0,0,ahover,10"

        >>> # Standard format with line (Basketball)
        >>> mapping = {
        ...     "betinasian_market": "ah",
        ...     "betinasian_side": "h",
        ...     "line_id": -22
        ... }
        >>> build(mapping)
        "for,ah,h,-22"

        >>> # Standard format without line (Basketball Money Line)
        >>> mapping = {
        ...     "betinasian_market": "ml",
        ...     "betinasian_side": "a"
        ... }
        >>> build(mapping)
        "for,ml,a"
    """
    if not mapping:
        return None

    # 1. Simple format (Soccer 1X2: "for,{side}")
    if mapping.get('simple_format'):
        side = mapping.get('betinasian_side')
        if not side:
            return None
        return f"for,{side}"

    # 2. Custom formats (Soccer special cases)
    custom_format = mapping.get('custom_format')

    if custom_format == 'score_both':
        # "for,score,both"
        return "for,score,both"

    elif custom_format == 'score_both_no':
        # "for,score,both,no"
        return "for,score,both,no"

    elif custom_format == 'odd_even_simple':
        # "for,odd" or "for,even"
        market = mapping.get('betinasian_market')
        if not market:
            return None
        return f"for,{market}"

    elif custom_format == 'dc_two_sides':
        # "for,dc,{side1},{side2}"
        market = mapping.get('betinasian_market')
        side1 = mapping.get('betinasian_side')
        side2 = mapping.get('betinasian_side2')
        if not market or not side1 or not side2:
            return None
        return f"for,{market},{side1},{side2}"

    # 3. IR format (Soccer Asian Handicap, Over/Under)
    if mapping.get('use_ir_format'):
        market = mapping.get('betinasian_market')
        side = mapping.get('betinasian_side')
        line_id = mapping.get('line_id')

        if not market:
            return None

        # Over/Under 特殊处理（无 side）
        if market in ['ahover', 'ahunder']:
            if line_id is None:
                return None
            return f"for,ir,0,0,{market},{line_id}"
        else:
            # Asian Handicap 等（有 side）
            if not side or line_id is None:
                return None
            return f"for,ir,0,0,{market},{side},{line_id}"

    # 4. Standard format (Basketball, etc.)
    market = mapping.get('betinasian_market')
    side = mapping.get('betinasian_side')

    # Validate required fields
    if not market or not side:
        return None

    # Extract optional line_id
    line_id = mapping.get('line_id')

    # Construct bet_type string
    if line_id is not None:
        # With line_id (Asian Handicap, Over/Under, etc.)
        return f"for,{market},{side},{line_id}"
    else:
        # Without line_id (Money Line, etc.)
        return f"for,{market},{side}"


def validate_mapping(mapping: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate mapping dictionary before building bet_type

    Args:
        mapping: Mapping dictionary to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, error_message) if invalid

    Examples:
        >>> mapping = {"betinasian_market": "ah", "betinasian_side": "h", "line_id": -22}
        >>> valid, error = validate_mapping(mapping)
        >>> valid
        True

        >>> mapping = {"betinasian_market": "ah"}  # Missing 'betinasian_side'
        >>> valid, error = validate_mapping(mapping)
        >>> error
        "Missing required field: betinasian_side"
    """
    if not mapping:
        return False, "Mapping is None or empty"

    # Check required fields
    if 'betinasian_market' not in mapping:
        return False, "Missing required field: betinasian_market"

    if 'betinasian_side' not in mapping:
        return False, "Missing required field: betinasian_side"

    market = mapping.get('betinasian_market')
    side = mapping.get('betinasian_side')

    # Validate values
    if not market or not isinstance(market, str):
        return False, "Invalid betinasian_market value"

    if not side or not isinstance(side, str):
        return False, "Invalid betinasian_side value"

    return True, None


def build_with_validation(mapping: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """
    Build bet_type with validation

    Args:
        mapping: Mapping dictionary

    Returns:
        Tuple of (bet_type, error_message)
        - (bet_type_string, None) if successful
        - (None, error_message) if failed

    Examples:
        >>> mapping = {"betinasian_market": "ah", "betinasian_side": "h", "line_id": -22}
        >>> bet_type, error = build_with_validation(mapping)
        >>> bet_type
        "for,ah,h,-22"
        >>> error
        None
    """
    # Validate first
    valid, error = validate_mapping(mapping)

    if not valid:
        return None, error

    # Build bet_type
    bet_type = build(mapping)

    if not bet_type:
        return None, "Failed to build bet_type from mapping"

    return bet_type, None
