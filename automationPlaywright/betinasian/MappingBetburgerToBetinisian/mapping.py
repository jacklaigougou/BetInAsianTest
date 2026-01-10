# -*- coding: utf-8 -*-
"""
Unified Market Mapping Interface

This module provides a unified interface for mapping spider markets to BetInAsian markets.
It automatically routes to the appropriate sport-specific mapping module.

Supported Sports:
- basket (basketball)
- soccer (football)
"""

from typing import Dict, Any, Optional
from . import basket
from . import soccer


# Sport type mapping
SPORT_MODULES = {
    "basket": basket,
    "basketball": basket,
    "fb": soccer,
    "soccer": soccer,
    "football": soccer
}


def parse_spider_market(
    sport_type: str,
    spider_market_id: str,
    handicap_value: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Parse spider market ID and return BetInAsian market info (unified interface)

    Args:
        sport_type: Sport type ("basket", "soccer", "fb", etc.)
        spider_market_id: Spider market ID (e.g., "17", "19")
        handicap_value: Handicap value (e.g., -5.5, 2.5), optional

    Returns:
        {
            "betinasian_market": "ah",     # BetInAsian market type
            "betinasian_side": "h",        # BetInAsian bet side
            "line_id": -22,                # Line ID (if applicable)
            "description": "Asian Handicap - Home"
        }
        or None (if cannot map or unsupported sport)

    Examples:
        >>> # Basketball
        >>> parse_spider_market("basket", "17", -5.5)
        {
            "betinasian_market": "ah",
            "betinasian_side": "h",
            "line_id": -22,
            "description": "Asian Handicap - Home"
        }

        >>> # Soccer
        >>> parse_spider_market("soccer", "17", -0.5)
        {
            "betinasian_market": "ah",
            "betinasian_side": "h",
            "line_id": -2,
            "description": "Asian Handicap - Home"
        }

        >>> # Soccer 1X2 (no handicap needed)
        >>> parse_spider_market("fb", "11")
        {
            "betinasian_market": "ml",
            "betinasian_side": "h",
            "description": "1X2 - Home Win"
        }
    """
    # Get sport module
    sport_module = SPORT_MODULES.get(sport_type.lower())

    if not sport_module:
        return None

    # Call sport-specific parse function
    return sport_module.parse_spider_market(spider_market_id, handicap_value)


def get_betinasian_market_type(
    sport_type: str,
    spider_market_id: str
) -> Optional[str]:
    """
    Quick get BetInAsian market type

    Args:
        sport_type: Sport type ("basket", "soccer", "fb", etc.)
        spider_market_id: Spider market ID

    Returns:
        BetInAsian market type (e.g., "ah", "ahou", "ml") or None

    Examples:
        >>> get_betinasian_market_type("basket", "17")
        "ah"
        >>> get_betinasian_market_type("soccer", "11")
        "ml"
    """
    sport_module = SPORT_MODULES.get(sport_type.lower())

    if not sport_module:
        return None

    return sport_module.get_betinasian_market_type(spider_market_id)


def get_betinasian_side(
    sport_type: str,
    spider_market_id: str
) -> Optional[str]:
    """
    Quick get BetInAsian bet side

    Args:
        sport_type: Sport type ("basket", "soccer", "fb", etc.)
        spider_market_id: Spider market ID

    Returns:
        BetInAsian bet side (e.g., "h", "a", "o", "u") or None

    Examples:
        >>> get_betinasian_side("basket", "17")
        "h"
        >>> get_betinasian_side("soccer", "12")
        "x"
    """
    sport_module = SPORT_MODULES.get(sport_type.lower())

    if not sport_module:
        return None

    return sport_module.get_betinasian_side(spider_market_id)


def needs_line_id(
    sport_type: str,
    spider_market_id: str
) -> bool:
    """
    Check if the market needs line_id

    Args:
        sport_type: Sport type ("basket", "soccer", "fb", etc.)
        spider_market_id: Spider market ID

    Returns:
        True if needs line_id, False otherwise

    Examples:
        >>> needs_line_id("basket", "17")  # Asian Handicap
        True
        >>> needs_line_id("soccer", "11")  # 1X2
        False
    """
    sport_module = SPORT_MODULES.get(sport_type.lower())

    if not sport_module:
        return False

    return sport_module.needs_line_id(spider_market_id)


def get_side_name(
    sport_type: str,
    side_code: str
) -> str:
    """
    Get readable name for bet side

    Args:
        sport_type: Sport type
        side_code: Side code (e.g., "h", "a", "o", "u")

    Returns:
        Readable name (e.g., "Home", "Away", "Over")

    Examples:
        >>> get_side_name("basket", "h")
        "Home"
        >>> get_side_name("soccer", "x")
        "Draw"
    """
    sport_module = SPORT_MODULES.get(sport_type.lower())

    if not sport_module:
        return side_code

    return sport_module.BETINASIAN_SIDE_NAMES.get(side_code, side_code)


def get_market_name(
    sport_type: str,
    market_code: str
) -> str:
    """
    Get readable name for market type

    Args:
        sport_type: Sport type
        market_code: Market code (e.g., "ah", "ahou", "ml")

    Returns:
        Readable name (e.g., "Asian Handicap", "Over/Under")

    Examples:
        >>> get_market_name("basket", "ah")
        "Asian Handicap"
        >>> get_market_name("soccer", "ml")
        "Money Line (1X2)"
    """
    sport_module = SPORT_MODULES.get(sport_type.lower())

    if not sport_module:
        return market_code

    return sport_module.BETINASIAN_MARKET_NAMES.get(market_code, market_code)


def get_supported_sports() -> list:
    """
    Get list of supported sport types

    Returns:
        List of supported sport type identifiers

    Examples:
        >>> get_supported_sports()
        ['basket', 'basketball', 'fb', 'soccer', 'football']
    """
    return list(SPORT_MODULES.keys())


def is_sport_supported(sport_type: str) -> bool:
    """
    Check if a sport type is supported

    Args:
        sport_type: Sport type to check

    Returns:
        True if supported, False otherwise

    Examples:
        >>> is_sport_supported("basket")
        True
        >>> is_sport_supported("tennis")
        False
    """
    return sport_type.lower() in SPORT_MODULES


class MarketMapper:
    """
    Object-oriented interface for market mapping

    Usage:
        mapper = MarketMapper("basket")
        mapping = mapper.parse("17", -5.5)
    """

    def __init__(self, sport_type: str):
        """
        Initialize mapper for specific sport

        Args:
            sport_type: Sport type ("basket", "soccer", etc.)

        Raises:
            ValueError: If sport type is not supported
        """
        self.sport_type = sport_type.lower()
        self.sport_module = SPORT_MODULES.get(self.sport_type)

        if not self.sport_module:
            raise ValueError(
                f"Unsupported sport type: {sport_type}. "
                f"Supported types: {', '.join(get_supported_sports())}"
            )

    def parse(
        self,
        spider_market_id: str,
        handicap_value: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Parse spider market ID

        Args:
            spider_market_id: Spider market ID
            handicap_value: Handicap value (optional)

        Returns:
            Mapping dict or None
        """
        return self.sport_module.parse_spider_market(spider_market_id, handicap_value)

    def get_market_type(self, spider_market_id: str) -> Optional[str]:
        """Get BetInAsian market type"""
        return self.sport_module.get_betinasian_market_type(spider_market_id)

    def get_side(self, spider_market_id: str) -> Optional[str]:
        """Get BetInAsian bet side"""
        return self.sport_module.get_betinasian_side(spider_market_id)

    def needs_line(self, spider_market_id: str) -> bool:
        """Check if market needs line_id"""
        return self.sport_module.needs_line_id(spider_market_id)

    def get_side_name(self, side_code: str) -> str:
        """Get readable name for side"""
        return self.sport_module.BETINASIAN_SIDE_NAMES.get(side_code, side_code)

    def get_market_name(self, market_code: str) -> str:
        """Get readable name for market"""
        return self.sport_module.BETINASIAN_MARKET_NAMES.get(market_code, market_code)


# Convenience functions for common use cases

def map_market(
    sport_type: str,
    spider_market_id: str,
    handicap_value: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Alias for parse_spider_market (more intuitive name)

    Args:
        sport_type: Sport type
        spider_market_id: Spider market ID
        handicap_value: Handicap value (optional)

    Returns:
        Mapping dict or None
    """
    return parse_spider_market(sport_type, spider_market_id, handicap_value)


def validate_mapping(
    sport_type: str,
    spider_market_id: str,
    handicap_value: Optional[float] = None
) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate and parse spider market with error message

    Args:
        sport_type: Sport type
        spider_market_id: Spider market ID
        handicap_value: Handicap value (optional)

    Returns:
        Tuple of (is_valid, mapping_dict, error_message)

    Examples:
        >>> valid, mapping, error = validate_mapping("basket", "17", -5.5)
        >>> if valid:
        >>>     print(mapping)
        >>> else:
        >>>     print(error)
    """
    # Check sport support
    if not is_sport_supported(sport_type):
        return False, None, f"Unsupported sport type: {sport_type}"

    # Check if market needs line_id
    if needs_line_id(sport_type, spider_market_id) and handicap_value is None:
        return False, None, f"Market {spider_market_id} requires handicap_value"

    # Parse mapping
    mapping = parse_spider_market(sport_type, spider_market_id, handicap_value)

    if not mapping:
        return False, None, f"Cannot map market ID: {spider_market_id}"

    return True, mapping, None


def build_bet_type_from_spider(
    sport_type: str,
    spider_market_id: str,
    handicap_value: Optional[float] = None,
    home_score: int = 0,
    away_score: int = 0
) -> Optional[str]:
    """
    Build BetInAsian bet_type string directly from spider market parameters

    This is a convenience function that combines parse_spider_market() and
    bet_type_builder.build() into a single call.

    Args:
        sport_type: Sport type ("basket", "soccer", "fb", etc.)
        spider_market_id: Spider market ID (e.g., "17", "1")
        handicap_value: Handicap value (e.g., -5.5, 170), optional
        home_score: Home team score for IR format (default: 0)
        away_score: Away team score for IR format (default: 0)

    Returns:
        BetInAsian bet_type string (e.g., "for,ah,h,-22" or "for,ml,h")
        or None if cannot map

    Examples:
        >>> # Basketball Asian Handicap
        >>> build_bet_type_from_spider("basket", "17", -5.5)
        "for,ah,h,-22"

        >>> # Basketball Money Line
        >>> build_bet_type_from_spider("basket", "1")
        "for,ml,h"

        >>> # Basketball Over/Under
        >>> build_bet_type_from_spider("basket", "19", 170)
        "for,ahou,o,680"

        >>> # Soccer Asian Handicap with score
        >>> build_bet_type_from_spider("soccer", "17", -0.5, home_score=1, away_score=2)
        "for,ir,1,2,ah,h,-2"

        >>> # Invalid sport
        >>> build_bet_type_from_spider("tennis", "17", -5.5)
        None
    """
    # Step 1: Parse spider market to get mapping
    mapping = parse_spider_market(sport_type, spider_market_id, handicap_value)

    if not mapping:
        return None

    # Step 2: Build bet_type string from mapping
    from .bet_type_builder import build

    bet_type = build(mapping, home_score, away_score)

    return bet_type
