# -*- coding: utf-8 -*-
"""
BetInAsian Bet Type String Builder

Constructs BetInAsian bet_type strings from mapping dictionaries.

Bet Type Format:
- With line_id: "for,{market},{side},{line_id}"
  Example: "for,ah,h,-22" (Asian Handicap -5.5 for Home)

- Without line_id: "for,{market},{side}"
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
                "description": "..."           # Description (ignored)
            }

    Returns:
        bet_type string (e.g., "for,ah,h,-22" or "for,ml,h")
        or None if mapping is invalid

    Examples:
        >>> # Asian Handicap with line
        >>> mapping = {
        ...     "betinasian_market": "ah",
        ...     "betinasian_side": "h",
        ...     "line_id": -22
        ... }
        >>> build(mapping)
        "for,ah,h,-22"

        >>> # Money Line without line
        >>> mapping = {
        ...     "betinasian_market": "ml",
        ...     "betinasian_side": "a"
        ... }
        >>> build(mapping)
        "for,ml,a"

        >>> # Over/Under with line
        >>> mapping = {
        ...     "betinasian_market": "ahou",
        ...     "betinasian_side": "o",
        ...     "line_id": 680
        ... }
        >>> build(mapping)
        "for,ahou,o,680"
    """
    if not mapping:
        return None

    # Extract required fields
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
