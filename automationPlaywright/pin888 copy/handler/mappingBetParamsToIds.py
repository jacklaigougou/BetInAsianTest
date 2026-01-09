# -*- coding: utf-8 -*-
"""
Pin888 投注参数到ID的映射模块
将投注类型、脚本等映射为 _1a, _2b, _3c, _4d, _5e 参数
使用明确的输入输出参数,不依赖 msg 字典
"""


def transform_period_to_number(period: str) -> int | None:
    """
    转换时段名称为数字ID

    参数:
        period: 时段名称字符串

    返回:
        int: 时段数字ID
        None: 未知的时段名称
    """
    period_lower = period.lower()

    if period_lower in ['full time', 'hidden period', 'with ot']:
        return 0
    elif period_lower == '1st half':
        return 1
    elif period_lower == '2nd half':
        return 2
    elif period_lower in ['1st quarter', '1st qtr', '1rd qtr']:
        return 3
    elif period_lower in ['2nd quarter', '2nd qtr', '2rd qtr']:
        return 4
    elif period_lower in ['3rd quarter', '3rd qtr']:
        return 5
    elif period_lower in ['4th quarter', '4th qtr', '4rd qtr']:
        return 6
    else:
        print(f"❌ [PIN888] 未知的时段: {period}")
        return None


def map_1x2(
    period: str,
    handicap: str,
    line_id: int,
    market_group_id: int,
    **kwargs
) -> dict | None:
    """
    映射 1x2 投注类型(主胜/平局/客胜)

    返回: {'oddsID': str, 'oddsSelectionsType': str, 'selectionID': str} 或 None
    """
    period_lower = period.lower()
    if period_lower in ['full time', 'hidden period', 'with ot']:
        _1a = 0
    elif period_lower in ['1st half', '2nd half']:
        _1a = 1
    else:
        print(f"❌ [PIN888] 未知的投注时段: {period}")
        return None

    _2b = 1
    _4d = 0
    _5e = 0

    match handicap.lower():
        case "1":
            _3c = 0
            _6f = 0
        case "2":
            _3c = 1
            _6f = 1
        case "x":
            _3c = 2
            _6f = 2
        case _:
            print(f"❌ [PIN888] 未知的1x2盘口: {handicap}")
            return None

    return {
        'oddsID': f"{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}",
        'oddsSelectionsType': "NORMAL",
        'selectionID': f"{line_id}|{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{_6f}"
    }


def map_double_chance(
    line_id: int,
    market_group_id: int,
    specials_i: int = 0,
    **kwargs
) -> dict | None:
    """
    映射 Double Chance 投注类型(双重机会)
    携带了三个id

    返回: (oddsId, oddsSelectionsType, selectionId)
    """
    _1a = 0
    _2b = 99
    _3c = 10
    _4d = 0
    _5e = 0
    _6f = 0

    return {
        'oddsID': f"{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{specials_i}",
        'oddsSelectionsType': "OUTRIGHT",
        'selectionID': f"{line_id}|{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{specials_i}|{_6f}"
    }


def map_asian_handicap(
    sport_type: str,
    period: str,
    direction: str,
    handicap_param: str,
    line_id: int,
    market_group_id: int,
    is_alt: bool = False,
    **kwargs
) -> dict | None:
    """
    映射 Asian Handicap 投注类型(亚洲盘口)

    返回: (oddsId, oddsSelectionsType, selectionId) 或 None
    """
    if sport_type in ['basketball', 'soccer']:
        _1a = transform_period_to_number(period)
        if _1a is None:
            return None
    else:
        print(f"❌ [PIN888] 未知的运动类型: {sport_type}")
        return None

    _2b = 2

    match direction.lower():
        case 'home':
            _3c = 0
            _6f = 0
        case 'away':
            _3c = 1
            _6f = 1
        case _:
            print(f"❌ [PIN888] 未知的方向: {direction}")
            return None

    _4d = 1 if is_alt else 0

    _5e = float(handicap_param)
    if _5e == 0:
        _5e = str(int(0))
    elif _5e > 0:
        _5e = '+' + str(abs(_5e))

    return {
        'oddsID': f"{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}",
        'oddsSelectionsType': "NORMAL",
        'selectionID': f"{line_id}|{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{_6f}"
    }


def map_total(
    sport_type: str,
    period: str,
    direction: str,
    handicap_param: str,
    line_id: int,
    market_group_id: int,
    is_alt: bool = False,
    **kwargs
) -> dict | None:
    """
    映射 Total 投注类型(总进球大小)

    返回: (oddsId, oddsSelectionsType, selectionId) 或 None
    """
    if sport_type in ['basketball', 'soccer']:
        _1a = transform_period_to_number(period)
        if _1a is None:
            return None
    else:
        print(f"❌ [PIN888] 未知的运动类型: {sport_type}")
        return None

    _2b = 3

    match direction.lower():
        case 'under':
            _3c = 4
            _6f = 1
        case 'over':
            _3c = 3
            _6f = 0
        case _:
            print(f"❌ [PIN888] 未知的方向: {direction}")
            return None

    _4d = 1 if is_alt else 0
    _5e = float(handicap_param)

    return {
        'oddsID': f"{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}",
        'oddsSelectionsType': "NORMAL",
        'selectionID': f"{line_id}|{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{_6f}"
    }


def map_odd_even(
    period: str,
    line_id: int,
    market_group_id: int,
    specials_i: int = 0,
    **kwargs
) -> dict | None:
    """
    映射 Odd/Even 投注类型(单双数)

    返回: (oddsId, oddsSelectionsType, selectionId)
    """
    period_lower = period.lower()
    if period_lower in ['full time', 'hidden period', '1st half', '2nd half']:
        _1a = 0
    else:
        print(f"❌ [PIN888] 未知的时段: {period}")
        return None

    _2b = 99
    _3c = 10
    _4d = 0
    _5e = 0
    _6f = 0

    return {
        'oddsID': f"{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{specials_i}",
        'oddsSelectionsType': "OUTRIGHT",
        'selectionID': f"{line_id}|{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{specials_i}|{_6f}"
    }


def map_both_teams_to_score(
    line_id: int,
    market_group_id: int,
    specials_i: int = 0,
    **kwargs
) -> dict | None:
    """
    映射 Both Teams to Score 投注类型(双方进球)

    返回: (oddsId, oddsSelectionsType, selectionId)
    """
    _1a = 0
    _2b = 99
    _3c = 10
    _4d = 0
    _5e = 0
    _6f = 0

    return {
        'oddsID': f"{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{specials_i}",
        'oddsSelectionsType': "OUTRIGHT",
        'selectionID': f"{line_id}|{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{specials_i}|{_6f}"
    }


def map_draw_no_bet(
    period: str,
    line_id: int,
    specials_i: int = 0,
    specials_event_id: int = 0,
    **kwargs
) -> dict | None:
    """
    映射 Draw No Bet 投注类型(平局退款)

    返回: (oddsId, oddsSelectionsType, selectionId)
    """
    period_lower = period.lower()
    if period_lower in ['full time', 'hidden period', 'with ot', '1st half', '2nd half']:
        _1a = 0
    else:
        print(f"❌ [PIN888] 未知的时段: {period}")
        return None

    _2b = 99
    _3c = 10
    _4d = 0
    _5e = 0
    _6f = 0

    return {
        'oddsID': f"{specials_event_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{specials_i}",
        'oddsSelectionsType': "OUTRIGHT",
        'selectionID': f"{line_id}|{specials_event_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{specials_i}|{_6f}"
    }


def map_corner_handicap(
    period: str,
    direction: str,
    handicap_param: str,
    line_id: int,
    market_group_id: int,
    is_alt: bool = False,
    **kwargs
) -> dict | None:
    """
    映射 Corner Handicap 投注类型(角球盘口)

    返回: (oddsId, oddsSelectionsType, selectionId) 或 None
    """
    period_lower = period.lower()
    if period_lower in ['full time', 'hidden period', 'with ot']:
        _1a = 0
    elif period_lower in ['1st half', '2nd half']:
        _1a = 1
    else:
        print(f"❌ [PIN888] 未知的时段: {period}")
        return None

    _2b = 2

    match direction.lower():
        case '1' | 'home':
            _3c = 0
            _6f = 0
        case '2' | 'away':
            _3c = 1
            _6f = 1
        case _:
            print(f"❌ [PIN888] 未知的方向: {direction}")
            return None

    _4d = 1 if is_alt else 0

    _5e = float(handicap_param)
    if _5e == 0:
        _5e = str(int(0))
    elif _5e > 0:
        _5e = '+' + str(abs(_5e))

    return {
        'oddsID': f"{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}",
        'oddsSelectionsType': "NORMAL",
        'selectionID': f"{line_id}|{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{_6f}"
    }


def map_total_corners(
    period: str,
    direction: str,
    handicap_param: str,
    line_id: int,
    market_group_id: int,
    is_alt: bool = False,
    **kwargs
) -> dict | None:
    """
    映射 Total Corners 投注类型(总角球数)

    返回: (oddsId, oddsSelectionsType, selectionId) 或 None
    """
    period_lower = period.lower()
    if period_lower in ['full time', 'hidden period', 'with ot']:
        _1a = 0
    elif period_lower in ['1st half', '2nd half']:
        _1a = 1
    else:
        print(f"❌ [PIN888] 未知的时段: {period}")
        return None

    _2b = 3

    match direction.lower():
        case 'over':
            _3c = 3
            _6f = 0
        case 'under':
            _3c = 4
            _6f = 1
        case _:
            print(f"❌ [PIN888] 未知的方向: {direction}")
            return None

    _4d = 1 if is_alt else 0
    _5e = handicap_param

    return {
        'oddsID': f"{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}",
        'oddsSelectionsType': "NORMAL",
        'selectionID': f"{line_id}|{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{_6f}"
    }


def map_total_for_team(
    sport_type: str,
    period: str,
    direction: str,
    match: str,
    handicap_param: str,
    line_id: int,
    market_group_id: int,
    is_alt: bool = False,
    **kwargs
) -> dict | None:
    """
    映射 Total for Team 投注类型(球队总分)

    返回: (oddsId, oddsSelectionsType, selectionId) 或 None
    """
    # 根据运动类型选择不同的时段映射逻辑
    if sport_type == 'basketball':
        _1a = transform_period_to_number(period)
        if _1a is None:
            return None
    else:
        # 足球等其他运动的时段映射
        period_lower = period.lower()
        if period_lower in ['full time', 'hidden period', 'with ot']:
            _1a = 0
        elif period_lower in ['1st half', '2nd half']:
            _1a = 1
        else:
            print(f"❌ [PIN888] 未知的时段: {period}")
            return None

    match direction.lower():
        case 'home':
            if match.lower() == 'over':
                _2b = 4
                _3c = 5
                _6f = 0
            elif match.lower() == 'under':
                _2b = 4
                _3c = 6
                _6f = 0
            else:
                print(f"❌ [PIN888] 未知的匹配类型: {match}")
                return None

        case 'away':
            if match.lower() == 'over':
                _2b = 5
                _3c = 7
                _6f = 1
            elif match.lower() == 'under':
                _2b = 5
                _3c = 8
                _6f = 1
            else:
                print(f"❌ [PIN888] 未知的匹配类型: {match}")
                return None
        case _:
            print(f"❌ [PIN888] 未知的方向: {direction}")
            return None

    _4d = 1 if is_alt else 0
    _5e = handicap_param

    return {
        'oddsID': f"{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}",
        'oddsSelectionsType': "NORMAL",
        'selectionID': f"{line_id}|{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{_6f}"
    }


def map_basketball_team_win(
    period: str,
    direction: str,
    line_id: int,
    market_group_id: int,
    handicap: str = '',
    **kwargs
) -> dict | None:
    """
    映射 Basketball Team Win 投注类型(篮球球队获胜)

    返回: (oddsId, oddsSelectionsType, selectionId) 或 None
    """
    _1a = transform_period_to_number(period)
    if _1a is None:
        return None

    _2b = 1
    _4d = 0
    _5e = 0

    match direction.lower():
        case 'home':
            _3c = 0
            _6f = 0
        case 'away':
            _3c = 1
            _6f = 1
        case _:
            print(f"❌ [PIN888] 未知的方向: {direction}")
            return None

    return {
        'oddsID': f"{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}",
        'oddsSelectionsType': "NORMAL",
        'selectionID': f"{line_id}|{market_group_id}|{_1a}|{_2b}|{_3c}|{_4d}|{_5e}|{_6f}"
    }


def map_bet_params_to_ids(
    sport_type: str,              # 'soccer' 或 'basketball' (必需)
    handicap: str,                # 盘口类型 (必需)
    period: str,                  # 时段 (必需)
    direction: str = '',          # 方向 (可选,允许空值)
    match: str = '',              # 匹配类型 (可选,允许空值)
    handicap_param: str = '',     # 盘口参数 (可选,允许空值)
    line_id: int = 0,             # lineID (可选,默认0)
    market_group_id: int = 0,     # market_group_id (可选,默认0)
    is_alt: bool = False,         # 是否备用盘口 (可选,默认False)
    specials_i: int = 0,          # 特殊盘口 i (可选,默认0)
    specials_event_id: int = 0    # 特殊盘口 event_id (可选,默认0)
) -> dict | None:
    """
    将投注参数映射为Pin888所需的ID格式(主函数)

    使用明确的输入参数,不依赖 msg 字典

    参数:
        sport_type: 运动类型 ('soccer', 'basketball')
        handicap: 盘口类型
        period: 时段
        direction: 方向 (home/away/over/under, 可选)
        match: 匹配类型 (over/under/even/odd, 可选)
        handicap_param: 盘口参数 (可选)
        line_id: lineID
        market_group_id: market_group_id
        is_alt: 是否为备用盘口
        specials_i: 特殊盘口 i
        specials_event_id: 特殊盘口 event_id

    返回:
        dict: {'oddsID': str, 'oddsSelectionsType': str, 'selectionID': str}
        None: 如果映射失败
    """
    # 构造参数字典,传递给各个映射函数
    params = {
        'sport_type': sport_type,
        'handicap': handicap,
        'period': period,
        'direction': direction,
        'match': match,
        'handicap_param': handicap_param,
        'line_id': line_id,
        'market_group_id': market_group_id,
        'is_alt': is_alt,
        'specials_i': specials_i,
        'specials_event_id': specials_event_id
    }

    # 根据投注类型调用对应的映射函数
    handicap_lower = handicap.lower()
    print(f"handicap_lower {handicap_lower}")

    if handicap_lower in ["1x2", "1", "2", "x"]:
        return map_1x2(**params)

    elif handicap_lower in ["double chance", "1x", "x2", "12"]:
        return map_double_chance(**params)

    elif (handicap_lower == "asian handicap" or
          handicap_lower.startswith("asian handicap1(") or
          handicap_lower.startswith("asian handicap2(")) and \
         (handicap_lower not in ["asian handicap2(0.0)/draw no bet", "asian handicap1(0.0)/draw no bet"]):
        return map_asian_handicap(**params)

    elif (handicap_lower == "total" or
          handicap_lower.startswith("total over(") or
          handicap_lower.startswith("total under(")) and \
         ('corners' not in handicap_lower):
        # 检查是否是 for team1/team2
        if 'for team' in handicap_lower:
            return map_total_for_team(**params)
        else:
            return map_total(**params)

    elif handicap_lower in ["odd/even", "odd", "even"]:
        return map_odd_even(**params)

    elif handicap_lower in ["both teams to score", "one scoreless", "both to score"]:
        return map_both_teams_to_score(**params)

    elif handicap_lower in ["draw no bet", "asian handicap1(0.0)/draw no bet",
                            "asian handicap2(0.0)/draw no bet",
                            "draw no bet 1", "draw no bet 2"]:
        return map_draw_no_bet(**params)

    elif handicap_lower == "corner handicap" or handicap_lower.endswith("- corners"):
        if handicap_lower.startswith("asian handicap"):
            return map_corner_handicap(**params)
        elif handicap_lower.startswith("total"):
            return map_total_corners(**params)
        else:
            print(f"❌ [PIN888] mappingBetParamsToIds 未知的角球盘口类型: {handicap}")
            return None

    elif handicap_lower in ['team1 win', 'team2 win']:
        if sport_type in ['basketball', 'soccer']:
            return map_basketball_team_win(**params)
        else:
            print(f"❌ [PIN888] 未知的运动类型: {sport_type}")
            return None

    else:
        print(f"❌ [PIN888] mappingBetParamsToIds 未知的投注类型: {handicap}")
        return None
