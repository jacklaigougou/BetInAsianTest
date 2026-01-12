# -*- coding: utf-8 -*-
"""
Soccer Period to BetInAsian Sport Mapper

Maps spider_period values to BetInAsian sport types for soccer betting.

Spider Period Values:
- "Full Time": 全场
- "1st half": 上半场
- "2nd half": 下半场
- "Hidden period": 特殊时段(待确认)

BetInAsian Sport Types (Soccer):
- "fb": 全场
- "fb_ht": 半场
- "fb_et": 加时赛
- "fb_corn": 全场角球
- "fb_corn_ht": 半场角球

spider_period    + spider_market_id → betinasian_sport
"Full Time"      + 普通盘口         → "fb"
"Full Time"      + 角球盘口(49-52)  → "fb_corn"
"1st half"       + 普通盘口         → "fb_ht"
"1st half"       + 角球盘口         → "fb_corn_ht"
"2nd half"       + 普通盘口         → "fb_ht"
"""

# Spider period to base sport mapping
PERIOD_TO_BASE_SPORT = {
    "Full Time": "fb",
    "1st half": "fb_ht",
    "2nd half": "fb_ht",  # 注意: 2nd half 也映射到 fb_ht
    # "Hidden period": 待确认
}

# Corner markets (需要特殊处理)
CORNER_MARKET_IDS = ["49", "50", "51", "52"]


def map_period_to_sport(
    spider_period: str,
    spider_market_id: str = None
) -> str:
    """
    将 spider_period 映射到 BetInAsian sport 类型

    Args:
        spider_period: Spider 时段值
            - "Full Time": 全场
            - "1st half": 上半场
            - "2nd half": 下半场
            - "Hidden period": 特殊时段
        spider_market_id: Spider 市场ID (可选)
            - 用于判断是否为角球盘口 (49, 50, 51, 52)

    Returns:
        BetInAsian sport 类型:
            - "fb": 全场
            - "fb_ht": 半场
            - "fb_corn": 全场角球
            - "fb_corn_ht": 半场角球

    Examples:
        >>> # 全场盘口
        >>> map_period_to_sport("Full Time")
        "fb"

        >>> # 半场盘口
        >>> map_period_to_sport("1st half")
        "fb_ht"

        >>> # 全场角球
        >>> map_period_to_sport("Full Time", "49")
        "fb_corn"

        >>> # 半场角球
        >>> map_period_to_sport("1st half", "51")
        "fb_corn_ht"

        >>> # 未知时段,默认全场
        >>> map_period_to_sport("Unknown")
        "fb"
    """
    # 获取基础 sport 类型
    base_sport = PERIOD_TO_BASE_SPORT.get(spider_period, "fb")  # 默认全场

    # 检查是否为角球盘口
    if spider_market_id and str(spider_market_id) in CORNER_MARKET_IDS:
        # 角球盘口需要添加 _corn 后缀
        if base_sport == "fb":
            return "fb_corn"
        elif base_sport == "fb_ht":
            return "fb_corn_ht"
        else:
            # 其他情况默认全场角球
            return "fb_corn"

    return base_sport


def is_corner_market(spider_market_id: str) -> bool:
    """
    判断是否为角球盘口

    Args:
        spider_market_id: Spider 市场ID

    Returns:
        True if corner market, False otherwise

    Examples:
        >>> is_corner_market("49")
        True
        >>> is_corner_market("17")
        False
    """
    return str(spider_market_id) in CORNER_MARKET_IDS


def get_supported_periods() -> list:
    """
    获取支持的时段列表

    Returns:
        支持的时段列表

    Examples:
        >>> get_supported_periods()
        ['Full Time', '1st half', '2nd half']
    """
    return list(PERIOD_TO_BASE_SPORT.keys())


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
        >>> validate_period("Invalid")
        False
    """
    return spider_period in PERIOD_TO_BASE_SPORT
