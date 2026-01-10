# -*- coding: utf-8 -*-
"""
Basketball Spider to BetInAsian Market Mapping

Spider Market Format:
{
    "1": "Team1 Win",                    # Full Time Money Line - Home
    "2": "Team2 Win",                    # Full Time Money Line - Away
    "11": "1",                           # Half Time Money Line - Home
    "12": "X",                           # Half Time Money Line - Draw
    "13": "2",                           # Half Time Money Line - Away
    "17": "Asian Handicap1(%s)",         # Asian Handicap - Home
    "18": "Asian Handicap2(%s)",         # Asian Handicap - Away
    "19": "Total Over(%s)",              # Over/Under - Over
    "20": "Total Under(%s)",             # Over/Under - Under
    "21": "Total Over(%s) for Team1",    # Team1 Over/Under - Over
    "22": "Total Under(%s) for Team1",   # Team1 Over/Under - Under
    "23": "Total Over(%s) for Team2",    # Team2 Over/Under - Over
    "24": "Total Under(%s) for Team2"    # Team2 Over/Under - Under
}

BetInAsian Market Types:
- ah: Asian Handicap
- ahou: Asian Handicap Over/Under
- ml: Money Line
- htah: Half Time Asian Handicap
- htahou: Half Time Asian Handicap Over/Under
- html: Half Time Money Line
- t1ahou: Team1 Over/Under
- t2ahou: Team2 Over/Under
"""

# Spider Market ID to BetInAsian Market Mapping
SPIDER_TO_BETINASIAN_MARKET = {
    # Full Time Money Line -> ml
    "1": {
        "betinasian_market": "ml",
        "betinasian_side": "h",  # home
        "description": "Money Line - Home"
    },
    "2": {
        "betinasian_market": "ml",
        "betinasian_side": "a",  # away
        "description": "Money Line - Away"
    },

    # Half Time Money Line -> html
    "11": {
        "betinasian_market": "html",
        "betinasian_side": "h",  # home
        "description": "Half Time Money Line - Home"
    },
    "12": {
        "betinasian_market": "html",
        "betinasian_side": "x",  # draw
        "description": "Half Time Money Line - Draw"
    },
    "13": {
        "betinasian_market": "html",
        "betinasian_side": "a",  # away
        "description": "Half Time Money Line - Away"
    },

    # Asian Handicap -> ah
    "17": {
        "betinasian_market": "ah",
        "betinasian_side": "h",  # home
        "description": "Asian Handicap - Home",
        "has_line": True  # has line value (e.g., -5.5)
    },
    "18": {
        "betinasian_market": "ah",
        "betinasian_side": "a",  # away
        "description": "Asian Handicap - Away",
        "has_line": True
    },

    # Over/Under (Full Time) -> ahou
    "19": {
        "betinasian_market": "ahou",
        "betinasian_side": "o",  # over
        "description": "Over/Under - Over",
        "has_line": True  # has line value (e.g., 170)
    },
    "20": {
        "betinasian_market": "ahou",
        "betinasian_side": "u",  # under
        "description": "Over/Under - Under",
        "has_line": True
    },

    # Team1 Over/Under -> t1ahou
    "21": {
        "betinasian_market": "t1ahou",
        "betinasian_side": "o",  # over
        "description": "Team1 Over/Under - Over",
        "has_line": True  # has line value (e.g., 85.5)
    },
    "22": {
        "betinasian_market": "t1ahou",
        "betinasian_side": "u",  # under
        "description": "Team1 Over/Under - Under",
        "has_line": True
    },

    # Team2 Over/Under -> t2ahou
    "23": {
        "betinasian_market": "t2ahou",
        "betinasian_side": "o",  # over
        "description": "Team2 Over/Under - Over",
        "has_line": True  # has line value (e.g., 82.5)
    },
    "24": {
        "betinasian_market": "t2ahou",
        "betinasian_side": "u",  # under
        "description": "Team2 Over/Under - Under",
        "has_line": True
    }
}


def parse_spider_market(spider_market_id: str, handicap_value: float = None):
    """
    Parse spider market ID and return BetInAsian market info

    Args:
        spider_market_id: Spider market ID (e.g., "17", "19")
        handicap_value: Handicap value (e.g., -5.5, 170)

    Returns:
        {
            "betinasian_market": "ah",     # BetInAsian market type
            "betinasian_side": "h",        # BetInAsian bet side
            "line_id": -22,                # Line ID (converted to int, -5.5 -> -22)
            "description": "Asian Handicap - Home"
        }
        or None (if cannot map)

    Examples:
        >>> parse_spider_market("17", -5.5)
        {
            "betinasian_market": "ah",
            "betinasian_side": "h",
            "line_id": -22,
            "description": "Asian Handicap - Home"
        }

        >>> parse_spider_market("19", 170)
        {
            "betinasian_market": "ahou",
            "betinasian_side": "o",
            "line_id": 680,
            "description": "Over/Under - Over"
        }
    """
    # 确保 spider_market_id 是字符串类型
    spider_market_id = str(spider_market_id)

    if spider_market_id not in SPIDER_TO_BETINASIAN_MARKET:
        return None

    mapping = SPIDER_TO_BETINASIAN_MARKET[spider_market_id].copy()
    


    # Convert handicap value to line_id if needed
    if mapping.get("has_line") and handicap_value is not None:
        # Convert to integer (BetInAsian line_id format)
        # e.g., -5.5 -> -22, 170 -> 680, 165.5 -> 662
        mapping["line_id"] = int(float(handicap_value) * 4)

    # Remove internal flag
    mapping.pop("has_line", None)

    return mapping


def get_betinasian_market_type(spider_market_id: str) -> str:
    """
    Quick get BetInAsian market type

    Args:
        spider_market_id: Spider market ID

    Returns:
        BetInAsian market type (e.g., "ah", "ahou", "ml") or None

    Examples:
        >>> get_betinasian_market_type("17")
        "ah"
        >>> get_betinasian_market_type("19")
        "ahou"
    """
    mapping = SPIDER_TO_BETINASIAN_MARKET.get(spider_market_id)
    return mapping["betinasian_market"] if mapping else None


def get_betinasian_side(spider_market_id: str) -> str:
    """
    Quick get BetInAsian bet side

    Args:
        spider_market_id: Spider market ID

    Returns:
        BetInAsian bet side (e.g., "h", "a", "o", "u") or None

    Examples:
        >>> get_betinasian_side("17")
        "h"
        >>> get_betinasian_side("19")
        "o"
    """
    mapping = SPIDER_TO_BETINASIAN_MARKET.get(spider_market_id)
    return mapping["betinasian_side"] if mapping else None


def needs_line_id(spider_market_id: str) -> bool:
    """
    Check if the market needs line_id

    Args:
        spider_market_id: Spider market ID

    Returns:
        True if needs line_id, False otherwise

    Examples:
        >>> needs_line_id("17")  # Asian Handicap
        True
        >>> needs_line_id("1")   # Money Line
        False
    """
    mapping = SPIDER_TO_BETINASIAN_MARKET.get(spider_market_id)
    return mapping.get("has_line", False) if mapping else False


# BetInAsian bet side readable names
BETINASIAN_SIDE_NAMES = {
    "h": "Home",
    "a": "Away",
    "o": "Over",
    "u": "Under",
    "x": "Draw"
}


# BetInAsian market type readable names
BETINASIAN_MARKET_NAMES = {
    "ah": "Asian Handicap",
    "ahou": "Over/Under",
    "ml": "Money Line",
    "html": "Half Time Money Line",
    "htah": "Half Time Asian Handicap",
    "htahou": "Half Time Over/Under",
    "t1ahou": "Team1 Over/Under",
    "t2ahou": "Team2 Over/Under"
}
