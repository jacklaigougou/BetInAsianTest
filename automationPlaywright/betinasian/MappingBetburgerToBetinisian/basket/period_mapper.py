# -*- coding: utf-8 -*-
"""
Basketball Period to BetInAsian Sport Mapper

Maps spider_period values to BetInAsian sport types for basketball betting.

Spider Period Values:
- "Full Time": 全场
- "1st half": 上半场
- "2nd half": 下半场
- "1st qtr": 第1节
- "2nd qtr": 第2节
- "3rd qtr": 第3节
- "4th qtr": 第4节

BetInAsian Sport Types (Basketball):
- "basket": 全场
- "basket_ht": 半场
- "basket_q1": 第1节
- "basket_q2": 第2节
- "basket_q3": 第3节
- "basket_q4": 第4节


"Full Time" → "basket" (全场)
"1st half" → "basket_ht" (上半场)
"2nd half" → "basket" (全场)
"1st qtr" → "basket_q1" (第1节)
"2nd qtr" → "basket_q2" (第2节)
"3rd qtr" → "basket_q3" (第3节)
"4th qtr" → "basket_q4" (第4节)
"""

# Spider period to sport mapping
PERIOD_TO_SPORT = {
    "Full Time": "basket",
    "1st half": "basket_ht",
    "2nd half": "basket",  # 注意: 2nd half 映射到 basket (全场)

    # 第1节 - 支持正确和错误拼写
    "1st qtr": "basket_q1",
    "1rd qtr": "basket_q1",  # 容错：1rd → 1st
    "1th qtr": "basket_q1",  # 容错：1th → 1st

    # 第2节 - 支持正确和错误拼写
    "2nd qtr": "basket_q2",
    "2rd qtr": "basket_q2",  # 容错：2rd → 2nd
    "2th qtr": "basket_q2",  # 容错：2th → 2nd

    # 第3节 - 支持正确和错误拼写
    "3rd qtr": "basket_q3",
    "3nd qtr": "basket_q3",  # 容错：3nd → 3rd
    "3th qtr": "basket_q3",  # 容错：3th → 3rd

    # 第4节 - 支持正确和错误拼写
    "4th qtr": "basket_q4",
    "4rd qtr": "basket_q4",  # 容错：4rd → 4th
    "4nd qtr": "basket_q4"   # 容错：4nd → 4th
}


def map_period_to_sport(spider_period: str) -> str:
    """
    将 spider_period 映射到 BetInAsian sport 类型

    Args:
        spider_period: Spider 时段值
            - "Full Time": 全场
            - "1st half": 上半场
            - "2nd half": 下半场
            - "1st qtr": 第1节
            - "2nd qtr": 第2节
            - "3rd qtr": 第3节
            - "4th qtr": 第4节

    Returns:
        BetInAsian sport 类型:
            - "basket": 全场
            - "basket_ht": 半场
            - "basket_q1": 第1节
            - "basket_q2": 第2节
            - "basket_q3": 第3节
            - "basket_q4": 第4节

    Examples:
        >>> # 全场盘口
        >>> map_period_to_sport("Full Time")
        "basket"

        >>> # 半场盘口
        >>> map_period_to_sport("1st half")
        "basket_ht"

        >>> # 第1节
        >>> map_period_to_sport("1st qtr")
        "basket_q1"

        >>> # 第4节
        >>> map_period_to_sport("4th qtr")
        "basket_q4"

        >>> # 未知时段,默认全场
        >>> map_period_to_sport("Unknown")
        "basket"
    """
    return PERIOD_TO_SPORT.get(spider_period, "basket")  # 默认全场


def get_supported_periods() -> list:
    """
    获取支持的时段列表

    Returns:
        支持的时段列表

    Examples:
        >>> get_supported_periods()
        ['Full Time', '1st half', '2nd half', '1st qtr', '2nd qtr', '3rd qtr', '4th qtr']
    """
    return list(PERIOD_TO_SPORT.keys())


def validate_period(spider_period: str) -> bool:
    """
    验证时段是否有效

    Args:
        spider_period: Spider 时段值

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_period("Full Time")
        True
        >>> validate_period("1st qtr")
        True
        >>> validate_period("Invalid")
        False
    """
    return spider_period in PERIOD_TO_SPORT
