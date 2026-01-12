# -*- coding: utf-8 -*-
"""
Soccer Spider to BetInAsian Market Mapping

Spider Market Format:
{
    "1": "Team1 Win",                          # Full Time Money Line - Home
    "2": "Team2 Win",                          # Full Time Money Line - Away
    "3": "Asian Handicap1(0.0)/Draw No Bet",   # Draw No Bet - Home
    "4": "Asian Handicap2(0.0)/Draw No Bet",   # Draw No Bet - Away
    "5": "European Handicap1(%s)",             # European Handicap - Home
    "6": "European HandicapX(%s)",             # European Handicap - Draw
    "7": "European Handicap2(%s)",             # European Handicap - Away
    "8": "Both to score",                      # Both Teams to Score - Yes
    "9": "One scoreless",                      # Both Teams to Score - No
    "11": "1",                                 # 1X2 - Home
    "12": "X",                                 # 1X2 - Draw
    "13": "2",                                 # 1X2 - Away
    "14": "1X",                                # Double Chance - 1X
    "15": "X2",                                # Double Chance - X2
    "16": "12",                                # Double Chance - 12
    "17": "Asian Handicap1(%s)",               # Asian Handicap - Home
    "18": "Asian Handicap2(%s)",               # Asian Handicap - Away
    "19": "Total Over(%s)",                    # Over/Under - Over
    "20": "Total Under(%s)",                   # Over/Under - Under
    "21": "Total Over(%s) for Team1",          # Team1 Over/Under - Over
    "22": "Total Under(%s) for Team1",         # Team1 Over/Under - Under
    "23": "Total Over(%s) for Team2",          # Team2 Over/Under - Over
    "24": "Total Under(%s) for Team2",         # Team2 Over/Under - Under
    "25": "Odd",                               # Odd/Even - Odd
    "26": "Even",                              # Odd/Even - Even
    "49": "Asian Handicap1(%s) - Corners",     # Corners Asian Handicap - Home
    "50": "Asian Handicap2(%s) - Corners",     # Corners Asian Handicap - Away
    "51": "Total Over(%s) - Corners",          # Corners Over/Under - Over
    "52": "Total Under(%s) - Corners",         # Corners Over/Under - Under
    "165": "No goal"                           # No Goal
}

BetInAsian Market Types (Soccer):
- ml: Money Line (1X2 - 3-way)
- ah: Asian Handicap
- ahou: Asian Handicap Over/Under (Total Goals)
- dnb: Draw No Bet
- dc: Double Chance
- btts: Both Teams to Score
- oe: Odd/Even
- eh: European Handicap
- t1ahou: Team1 Over/Under
- t2ahou: Team2 Over/Under
- corners_ah: Corners Asian Handicap
- corners_ou: Corners Over/Under
"""

# Spider Market ID to BetInAsian Market Mapping
SPIDER_TO_BETINASIAN_MARKET = {
    # Full Time Money Line (1X2) -> Simple format (same as 11/13)
    "1": {
        "betinasian_market": None,  # 简化格式不需要 market
        "betinasian_side": "h",  # home (1)
        "simple_format": True,  # 标记为简化格式
        "description": "1X2 - Home Win"
    },
    "2": {
        "betinasian_market": None,
        "betinasian_side": "a",  # away (2)
        "simple_format": True,
        "description": "1X2 - Away Win"
    },

    # Draw No Bet -> dnb
    "3": {
        "betinasian_market": "dnb",
        "betinasian_side": "h",  # home
        "description": "Draw No Bet - Home"
    },
    "4": {
        "betinasian_market": "dnb",
        "betinasian_side": "a",  # away
        "description": "Draw No Bet - Away"
    },

    # European Handicap -> eh
    "5": {
        "betinasian_market": "eh",
        "betinasian_side": "h",  # home
        "description": "European Handicap - Home",
        "has_line": True
    },
    "6": {
        "betinasian_market": "eh",
        "betinasian_side": "x",  # draw
        "description": "European Handicap - Draw",
        "has_line": True
    },
    "7": {
        "betinasian_market": "eh",
        "betinasian_side": "a",  # away
        "description": "European Handicap - Away",
        "has_line": True
    },

    # Both Teams to Score -> score,both format
    "8": {
        "betinasian_market": "score",
        "betinasian_side": "both",  # both teams score
        "custom_format": "score_both",  # 自定义格式标记
        "description": "Both Teams to Score - Yes"
    },
    "9": {
        "betinasian_market": "score",
        "betinasian_side": "both",
        "betinasian_extra": "no",  # 额外参数
        "custom_format": "score_both_no",  # 自定义格式标记
        "description": "Both Teams to Score - No"
    },

    # 1X2 (Simplified format: "for,{side}")
    "11": {
        "betinasian_market": None,  # 简化格式不需要 market
        "betinasian_side": "h",  # home (1)
        "simple_format": True,  # 标记为简化格式
        "description": "1X2 - Home Win"
    },
    "12": {
        "betinasian_market": None,
        "betinasian_side": "d",  # draw (X) - 改为 'd'
        "simple_format": True,
        "description": "1X2 - Draw"
    },
    "13": {
        "betinasian_market": None,
        "betinasian_side": "a",  # away (2)
        "simple_format": True,
        "description": "1X2 - Away Win"
    },

    # Double Chance -> dc (format: "for,dc,{side1},{side2}")
    "14": {
        "betinasian_market": "dc",
        "betinasian_side": "h",  # home
        "betinasian_side2": "d",  # draw
        "custom_format": "dc_two_sides",  # 双边格式
        "description": "Double Chance - 1X"
    },
    "15": {
        "betinasian_market": "dc",
        "betinasian_side": "a",  # away
        "betinasian_side2": "d",  # draw
        "custom_format": "dc_two_sides",
        "description": "Double Chance - X2"
    },
    "16": {
        "betinasian_market": "dc",
        "betinasian_side": "h",  # home
        "betinasian_side2": "a",  # away
        "custom_format": "dc_two_sides",
        "description": "Double Chance - 12"
    },

    # Asian Handicap -> ah (IR format: "for,ir,0,0,ah,{side},{line_id}")
    "17": {
        "betinasian_market": "ah",
        "betinasian_side": "h",  # home
        "description": "Asian Handicap - Home",
        "has_line": True,  # has line value (e.g., -0.5, -1.0)
        "use_ir_format": True  # 使用 IR 格式
    },
    "18": {
        "betinasian_market": "ah",
        "betinasian_side": "a",  # away
        "description": "Asian Handicap - Away",
        "has_line": True,
        "use_ir_format": True
    },

    # Over/Under (Total Goals) -> ahover/ahunder (IR format: "for,ir,0,0,{ahover|ahunder},{line_id}")
    "19": {
        "betinasian_market": "ahover",  # 改为 ahover
        "betinasian_side": None,  # Over/Under 不使用 side
        "description": "Over/Under - Over",
        "has_line": True,  # has line value (e.g., 2.5, 3.0)
        "use_ir_format": True  # 使用 IR 格式
    },
    "20": {
        "betinasian_market": "ahunder",  # 改为 ahunder
        "betinasian_side": None,  # Over/Under 不使用 side
        "description": "Over/Under - Under",
        "has_line": True,
        "use_ir_format": True
    },

    # Team1 Over/Under -> t1ahou
    "21": {
        "betinasian_market": "t1ahou",
        "betinasian_side": "o",  # over
        "description": "Team1 Over/Under - Over",
        "has_line": True  # has line value (e.g., 1.5)
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
        "has_line": True  # has line value (e.g., 1.5)
    },
    "24": {
        "betinasian_market": "t2ahou",
        "betinasian_side": "u",  # under
        "description": "Team2 Over/Under - Under",
        "has_line": True
    },

    # Odd/Even -> odd/even format (simple)
    "25": {
        "betinasian_market": "odd",
        "betinasian_side": None,  # no side needed
        "custom_format": "odd_even_simple",  # 简化格式
        "description": "Odd/Even - Odd"
    },
    "26": {
        "betinasian_market": "even",
        "betinasian_side": None,  # no side needed
        "custom_format": "odd_even_simple",
        "description": "Odd/Even - Even"
    },

    # Corners Asian Handicap -> ah (使用和普通盘口相同的市场名称)
    "49": {
        "betinasian_market": "ah",
        "betinasian_side": "h",  # home
        "description": "Corners Asian Handicap - Home",
        "has_line": True,  # has line value (e.g., -2.5)
        "use_ir_format": True  # 使用 IR 格式
    },
    "50": {
        "betinasian_market": "ah",
        "betinasian_side": "a",  # away
        "description": "Corners Asian Handicap - Away",
        "has_line": True,
        "use_ir_format": True  # 使用 IR 格式
    },

    # Corners Over/Under -> ahover/ahunder (使用和普通盘口相同的市场名称)
    "51": {
        "betinasian_market": "ahover",
        "betinasian_side": None,  # Over/Under 不需要 side
        "description": "Corners Over/Under - Over",
        "has_line": True,  # has line value (e.g., 10.5)
        "use_ir_format": True  # 使用 IR 格式
    },
    "52": {
        "betinasian_market": "ahunder",
        "betinasian_side": None,  # Over/Under 不需要 side
        "description": "Corners Over/Under - Under",
        "has_line": True,
        "use_ir_format": True  # 使用 IR 格式
    },

    # No Goal -> ng
    "165": {
        "betinasian_market": "ng",
        "betinasian_side": "y",  # yes (no goal)
        "description": "No Goal - Yes"
    }
}


def parse_spider_market(spider_market_id: str, handicap_value: float = None):
    """
    Parse spider market ID and return BetInAsian market info

    Args:
        spider_market_id: Spider market ID (e.g., "17", "19")
        handicap_value: Handicap value (e.g., -0.5, 2.5)

    Returns:
        {
            "betinasian_market": "ah",     # BetInAsian market type
            "betinasian_side": "h",        # BetInAsian bet side
            "line_id": -2,                 # Line ID (converted to int, -0.5 -> -2)
            "description": "Asian Handicap - Home"
        }
        or None (if cannot map)

    Examples:
        >>> parse_spider_market("17", -0.5)
        {
            "betinasian_market": "ah",
            "betinasian_side": "h",
            "line_id": -2,
            "description": "Asian Handicap - Home"
        }

        >>> parse_spider_market("19", 2.5)
        {
            "betinasian_market": "ahou",
            "betinasian_side": "o",
            "line_id": 10,
            "description": "Over/Under - Over"
        }

        >>> parse_spider_market("11")
        {
            "betinasian_market": "ml",
            "betinasian_side": "h",
            "description": "1X2 - Home Win"
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
        # Soccer uses 0.25 increments, multiply by 4
        # e.g., -0.5 -> -2, 2.5 -> 10, 1.75 -> 7
        mapping["line_id"] = int(handicap_value * 4)

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
        >>> get_betinasian_market_type("11")
        "ml"
    """
    mapping = SPIDER_TO_BETINASIAN_MARKET.get(spider_market_id)
    return mapping["betinasian_market"] if mapping else None


def get_betinasian_side(spider_market_id: str) -> str:
    """
    Quick get BetInAsian bet side

    Args:
        spider_market_id: Spider market ID

    Returns:
        BetInAsian bet side (e.g., "h", "a", "o", "u", "x") or None

    Examples:
        >>> get_betinasian_side("17")
        "h"
        >>> get_betinasian_side("12")
        "x"
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
        >>> needs_line_id("11")   # 1X2
        False
    """
    mapping = SPIDER_TO_BETINASIAN_MARKET.get(spider_market_id)
    return mapping.get("has_line", False) if mapping else False


# BetInAsian bet side readable names
BETINASIAN_SIDE_NAMES = {
    "h": "Home",
    "a": "Away",
    "x": "Draw",
    "o": "Over / Odd",
    "u": "Under",
    "e": "Even",
    "y": "Yes",
    "n": "No",
    "1x": "Home or Draw",
    "x2": "Draw or Away",
    "12": "Home or Away"
}


# BetInAsian market type readable names
BETINASIAN_MARKET_NAMES = {
    "ml": "Money Line (1X2)",
    "ah": "Asian Handicap",
    "ahou": "Over/Under (Total Goals)",
    "dnb": "Draw No Bet",
    "dc": "Double Chance",
    "btts": "Both Teams to Score",
    "oe": "Odd/Even",
    "eh": "European Handicap",
    "t1ahou": "Team1 Over/Under",
    "t2ahou": "Team2 Over/Under",
    "corners_ah": "Corners Asian Handicap",
    "corners_ou": "Corners Over/Under",
    "ng": "No Goal"
}
