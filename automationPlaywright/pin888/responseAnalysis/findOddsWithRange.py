# -*- coding: utf-8 -*-
"""
PIN888 平台 - 使用区间条件从详细赔率数据中查找赔率
用于套利补单场景,支持区间匹配而非精确匹配
"""
from typing import Callable, Union, Optional


def find_odds_from_detail_data_with_range(
    sport_type: str,
    market_group: str,
    platform_handicap: str,
    platform_direction: str,
    platform_match: str,
    period: str,
    detail_odds: dict,
    range_condition: Callable
) -> Union[dict, str, None]:
    """
    使用区间条件从详细赔率数据中查找匹配的赔率

    参数:
        sport_type: 运动类型 ('soccer' 或 'basketball')
        market_group: 市场组 ('normal', 'specials', 'corners')
        platform_handicap: 盘口类型 ('overUnder', 'handicap', 'teamTotals')
        platform_direction: 方向 ('home', 'away', 'over', 'under')
        period: 时间段 ('0' 全场, '1' 上半场)
        detail_odds: 详细赔率数据
        range_condition: 区间条件函数 (如 lambda y: y >= 2.5)

    返回:
        dict: 包含 odd, lineID, market_group_id, isAlt 等字段
        str: 'need refresh' 表示需要刷新数据
        None: 未找到匹配

    示例:
        # 成功方 Over 2.5, 我方需要 Under Y (Y >= 2.5)
        condition = lambda y: y >= 2.5
        result = find_odds_from_detail_data_with_range(
            sport_type='soccer',
            market_group='normal',
            platform_handicap='overUnder',
            platform_direction='under',
            period='0',
            detail_odds=event_detail_data,
            range_condition=condition
        )
    """
    try:
        match sport_type:
            case 'soccer':
                match market_group:
                    case 'normal':
                        if not detail_odds.get('normal'):
                            return 'need refresh'
                        return parse_soccer_normal_with_range(
                            platform_handicap,
                            platform_match,
                            platform_direction,
                            period,
                            detail_odds,
                            range_condition
                        )

                    case 'corners':
                        if not detail_odds.get('corners'):
                            return 'need refresh'
                        return parse_soccer_corners_with_range(
                            platform_handicap,
                            platform_direction,
                            period,
                            detail_odds,
                            range_condition
                        )

                    case _:
                        print(f"⚠️ [PIN888 区间补单] 不支持的 market_group: {market_group}")
                        return None

            case 'basketball':
                if not detail_odds.get('normal'):
                    print(f"❌ [PIN888 区间补单] detailOdds['normal'] 为 None")
                    return 'need refresh'

                normal_data = detail_odds.get('normal')
                periods = normal_data.get('periods')
                if periods is None:
                    print(f"❌ [PIN888 区间补单] detailOdds['normal']['periods'] 为 None")
                    return None

                data = periods.get(period, {})
                if not data:
                    print(f"⚠️ [PIN888 区间补单] basketball 数据为空")
                    return None

                market_group_id = normal_data.get('id')
                return parse_basketball_with_range(
                    platform_handicap,
                    platform_match,
                    platform_direction,
                    data,
                    market_group_id,
                    range_condition
                )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

    return None


def parse_soccer_normal_with_range(
    platform_handicap: str,
    platform_match: str,
    platform_direction: str,
    period: str,
    detail_odds: dict,
    range_condition: Callable
) -> Optional[dict]:
    """解析足球正常盘口数据 - 区间匹配"""
    try:
        market_group_id = detail_odds.get('normal', {}).get('id', 0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(detail_odds)
        return None

    if period == '0':
        data = detail_odds['normal']['periods']['0']
    elif period == '1':
        data = detail_odds['normal']['periods']['1']
    else:
        return None

    match platform_handicap:
        case 'overUnder':
            data = data['overUnder']
            matched_lines = []

            # 收集所有满足区间条件的盘口
            for line in data:
                points = float(line['points'])
                if range_condition(points):
                    matched_lines.append(line)

            if not matched_lines:
                print(f"⚠️ [PIN888 区间补单] overUnder 未找到满足区间条件的盘口")
                
                print(f"📋 [PIN888 区间补单] 所有可用盘口 (共 {len(data)} 个):")
                for idx, line in enumerate(data, 1):
                    print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, "
                          f"lineId={line['lineId']}, offline={line['offline']}, unavailable={line['unavailable']}")
                return None

            # 选择最优盘口 (赔率最高的)
            best_line = None
            best_odds = 0.0

            for line in matched_lines:
                if platform_direction.lower() == 'over':
                    current_odds = float(line['overOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line
                elif platform_direction.lower() == 'under':
                    current_odds = float(line['underOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line

            if not best_line:
                print(f"⚠️ [PIN888 区间补单] 未找到有效赔率")
                return None

            print(f"✅ [PIN888 区间补单] 找到最优盘口: points={best_line['points']}, {platform_direction}={best_odds}")

            if platform_direction.lower() == 'over':
                return {
                    'odd': best_line['overOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['points']  # 返回匹配到的参数值
                }
            elif platform_direction.lower() == 'under':
                return {
                    'odd': best_line['underOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['points']
                }
            else:
                return None

        case 'handicap':
            data = data['handicap']
            matched_lines = []

            # 收集所有满足区间条件的盘口
            for line in data:
                if platform_direction.lower() == 'home':
                    spread = float(line['homeSpread'])
                    if range_condition(spread):
                        matched_lines.append(line)
                elif platform_direction.lower() == 'away':
                    spread = float(line['awaySpread'])
                    if range_condition(spread):
                        matched_lines.append(line)

            if not matched_lines:
                print(f"⚠️ [PIN888 区间补单] handicap 未找到满足区间条件的盘口")
                print(f"🔍 [PIN888 区间补单] 方向: {platform_direction}")
                print(f"📋 [PIN888 区间补单] 所有可用盘口 (共 {len(data)} 个):")
                for idx, line in enumerate(data, 1):
                    print(f"  [{idx}] homeSpread={line['homeSpread']}, awaySpread={line['awaySpread']}, homeOdds={line['homeOdds']}, awayOdds={line['awayOdds']}")
                return None

            # 选择最优盘口 (赔率最高的)
            best_line = None
            best_odds = 0.0

            for line in matched_lines:
                if platform_direction.lower() == 'home':
                    current_odds = float(line['homeOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line
                elif platform_direction.lower() == 'away':
                    current_odds = float(line['awayOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line

            if not best_line:
                print(f"⚠️ [PIN888 区间补单] 未找到有效赔率")
                return None

            if platform_direction.lower() == 'home':
                print(f"✅ [PIN888 区间补单] 找到最优盘口: homeSpread={best_line['homeSpread']}, homeOdds={best_odds}")
                return {
                    'odd': best_line['homeOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['homeSpread']
                }
            elif platform_direction.lower() == 'away':
                print(f"✅ [PIN888 区间补单] 找到最优盘口: awaySpread={best_line['awaySpread']}, awayOdds={best_odds}")
                return {
                    'odd': best_line['awayOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['awaySpread']
                }
            else:
                return None

        case 'teamTotals':
            data = data['teamTotals']
            team_type = 'awayLines' if platform_direction.lower() == 'away' else 'homeLines'
            data = data[team_type]

            matched_lines = []
            if not data:
                print(f"⚠️ [PIN888 区间补单] teamTotals 数据为空，也就是说，盘口全部都关闭了")
                return None
    

            # 收集所有满足区间条件的盘口
            for line in data:
                points = float(line['points'])
                if range_condition(points):
                    matched_lines.append(line)

            if not matched_lines:
                print(f"⚠️ [PIN888 区间补单] teamTotals 未找到满足区间条件的盘口")
                print(f"🔍 [PIN888 区间补单] {team_type}")
                print(f"📋 [PIN888 区间补单] 所有可用盘口 (共 {len(data)} 个):")
                for idx, line in enumerate(data, 1):
                    print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}")
                         
                return None

            # 选择最优盘口 (赔率最高的)
            best_line = None
            best_odds = 0.0

            for line in matched_lines:
                if platform_match.lower() == 'over':
                    current_odds = float(line['overOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds 
                        best_line = line
                elif platform_match.lower() == 'under':
                    current_odds = float(line['underOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line

            if not best_line:
                print(f"⚠️ [PIN888 区间补单] teamTotals 未找到有效赔率")
                return None

            print(f"✅ [PIN888 区间补单] 找到最优盘口: points={best_line['points']}, {platform_match}={best_odds}")

            if platform_match.lower() == 'over':
                return {
                    'odd': best_line['overOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['points']
                }
            elif platform_match.lower() == 'under':
                return {
                    'odd': best_line['underOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['points']
                }
            else:
                return None

        case _:
            print(f"⚠️ [PIN888 区间补单] 不支持的盘口类型: {platform_handicap}")
            return None


def parse_soccer_corners_with_range(
    platform_handicap: str,
    platform_direction: str,
    period: str,
    detail_odds: dict,
    range_condition: Callable
) -> Optional[dict]:
    """解析足球角球盘口数据 - 区间匹配"""
    try:
        data = detail_odds.get('corners', {})
        market_group_id = data['id']
        if not data:
            print(f"⚠️ [PIN888 区间补单] corners 数据为空")
            return None
        data = data['periods'].get(period, {})
        if not data:
            print(f"⚠️ [PIN888 区间补单] corners 数据为空")
            return None

        match platform_handicap.lower():
            case 'handicap':
                data = data.get('handicap', [])
                matched_lines = []

                for line in data:
                    if platform_direction.lower() == 'home':
                        spread = float(line['homeSpread'])
                        if range_condition(spread):
                            matched_lines.append(line)
                    elif platform_direction.lower() == 'away':
                        spread = float(line['awaySpread'])
                        if range_condition(spread):
                            matched_lines.append(line)

                if not matched_lines:
                    print(f"⚠️ [PIN888 区间补单] corners handicap 未找到满足区间条件的盘口")
                    return None

                # 选择最优盘口
                best_line = None
                best_odds = 0.0

                for line in matched_lines:
                    if platform_direction.lower() == 'home':
                        current_odds = float(line['homeOdds'])
                        if current_odds > best_odds:
                            best_odds = current_odds
                            best_line = line
                    elif platform_direction.lower() == 'away':
                        current_odds = float(line['awayOdds'])
                        if current_odds > best_odds:
                            best_odds = current_odds
                            best_line = line

                if not best_line:
                    return None

                if platform_direction.lower() == 'home':
                    return {
                        'odd': best_line['homeOdds'],
                        'lineID': best_line['lineId'],
                        'isAlt': best_line['isAlt'],
                        'market_group_id': market_group_id,
                        'matched_param': best_line['homeSpread']
                    }
                elif platform_direction.lower() == 'away':
                    return {
                        'odd': best_line['awayOdds'],
                        'lineID': best_line['lineId'],
                        'isAlt': best_line['isAlt'],
                        'market_group_id': market_group_id,
                        'matched_param': best_line['awaySpread']
                    }

            case 'overunder':
                data = data.get('overUnder', [])
                matched_lines = []

                for line in data:
                    points = float(line['points'])
                    if range_condition(points):
                        matched_lines.append(line)

                if not matched_lines:
                    print(f"⚠️ [PIN888 区间补单] corners overUnder 未找到满足区间条件的盘口")
                    return None

                # 选择最优盘口
                best_line = None
                best_odds = 0.0

                for line in matched_lines:
                    if platform_direction.lower() == 'over':
                        current_odds = float(line['overOdds'])
                        if current_odds > best_odds:
                            best_odds = current_odds
                            best_line = line
                    elif platform_direction.lower() == 'under':
                        current_odds = float(line['underOdds'])
                        if current_odds > best_odds:
                            best_odds = current_odds
                            best_line = line

                if not best_line:
                    return None

                if platform_direction.lower() == 'over':
                    return {
                        'odd': best_line['overOdds'],
                        'lineID': best_line['lineId'],
                        'isAlt': best_line['isAlt'],
                        'market_group_id': market_group_id,
                        'matched_param': best_line['points']
                    }
                elif platform_direction.lower() == 'under':
                    return {
                        'odd': best_line['underOdds'],
                        'lineID': best_line['lineId'],
                        'isAlt': best_line['isAlt'],
                        'market_group_id': market_group_id,
                        'matched_param': best_line['points']
                    }

            case _:
                print(f"⚠️ [PIN888 区间补单] corners 不支持的盘口类型: {platform_handicap}")
                return None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

    return None


def parse_basketball_with_range(
    platform_handicap: str,
    platform_match: str,
    platform_direction: str,
    detail_odds: dict,
    market_group_id: int,
    range_condition: Callable
) -> Optional[dict]:
    """解析篮球盘口数据 - 区间匹配"""
    match platform_handicap.lower():
        case 'handicap':
            data = detail_odds.get('handicap')
            if not data:
                print(f"⚠️ [PIN888 区间补单] basketball handicap 数据为空")
                return None

            matched_lines = []

            for line in data:
                if platform_direction.lower() == 'home':
                    spread = float(line['homeSpread'])
                    if range_condition(spread):
                        matched_lines.append(line)
                elif platform_direction.lower() == 'away':
                    spread = float(line['awaySpread'])
                    if range_condition(spread):
                        matched_lines.append(line)

            if not matched_lines:
                print(f"⚠️ [PIN888 区间补单] basketball handicap 未找到满足区间条件的盘口")
                print(f"🔍 [PIN888 区间补单] 方向: {platform_direction}")
                print(f"📋 [PIN888 区间补单] 所有可用盘口 (共 {len(data)} 个):")
                for idx, line in enumerate(data, 1):
                    print(f"  [{idx}] homeSpread={line['homeSpread']}, awaySpread={line['awaySpread']}, homeOdds={line['homeOdds']}, awayOdds={line['awayOdds']}")
                return None

            # 选择最优盘口
            best_line = None
            best_odds = 0.0

            for line in matched_lines:
                if platform_direction.lower() == 'home':
                    current_odds = float(line['homeOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line
                elif platform_direction.lower() == 'away':
                    current_odds = float(line['awayOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line
            

            if not best_line:
                return None

            if platform_direction.lower() == 'home':
                return {
                    'odd': best_line['homeOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['homeSpread']
                }
            elif platform_direction.lower() == 'away':
                return {
                    'odd': best_line['awayOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['awaySpread']
                }

        case 'overunder':
            data = detail_odds.get('overUnder')
            if not data:
                print(f"⚠️ [PIN888 区间补单] basketball overUnder 数据为空")
                return None

            matched_lines = []

            for line in data:
                points = float(line['points'])
                if range_condition(points):
                    matched_lines.append(line)

            if not matched_lines:
                print(f"⚠️ [PIN888 区间补单] basketball overUnder 未找到满足区间条件的盘口")
                print(f"🔍 [PIN888 区间补单] 方向: {platform_direction}")
                print(f"📋 [PIN888 区间补单] 所有可用盘口 (共 {len(data)} 个):")
                for idx, line in enumerate(data, 1):
                    print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}")
                return None

            # 选择最优盘口
            best_line = None
            best_odds = 0.0

            for line in matched_lines:
                if platform_direction.lower() == 'over':
                    current_odds = float(line['overOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line
                elif platform_direction.lower() == 'under':
                    current_odds = float(line['underOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line

            if not best_line:
                return None

            if platform_direction.lower() == 'over':
                return {
                    'odd': best_line['overOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['points']
                }
            elif platform_direction.lower() == 'under':
                return {
                    'odd': best_line['underOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['points']
                }

        case 'teamtotals':
            teamTotalsData = detail_odds.get('teamTotals')
            if not teamTotalsData:
                print(f"⚠️ [PIN888 区间补单] basketball teamTotals 数据为空")
                return None

            if platform_direction.lower() == 'home':
                data = teamTotalsData.get('homeLines', {})
            elif platform_direction.lower() == 'away':
                data = teamTotalsData.get('awayLines', {})
            else:
                return None

            if not data:
                print(f"⚠️ [PIN888 区间补单] basketball teamTotals 数据为空，也就是说，盘口全部都关闭了")
                return None

            matched_lines = []

            for line in data:
                points = float(line['points'])
                if range_condition(points):
                    matched_lines.append(line)

            if not matched_lines:
                print(f"⚠️ [PIN888 区间补单] basketball teamTotals 未找到满足区间条件的盘口")
                print(f"🔍 [PIN888 区间补单] 方向: {platform_direction}")
                print(f"📋 [PIN888 区间补单] 所有可用盘口 (共 {len(data)} 个):")
                for idx, line in enumerate(data, 1):
                    print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}")
                return None

            # 选择最优盘口 (赔率最高的)
            best_line = None
            best_odds = 0.0

            for line in matched_lines:
                if platform_match.lower() == 'over':
                    current_odds = float(line['overOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line
                elif platform_match.lower() == 'under':
                    current_odds = float(line['underOdds'])
                    if current_odds > best_odds:
                        best_odds = current_odds
                        best_line = line

            if not best_line:
                print(f"⚠️ [PIN888 区间补单] basketball teamTotals 未找到有效赔率")
                return None

            print(f"✅ [PIN888 区间补单] 找到最优盘口: points={best_line['points']}, {platform_match}={best_odds}")

            if platform_match.lower() == 'over':
                return {
                    'odd': best_line['overOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['points']
                }
            elif platform_match.lower() == 'under':
                return {
                    'odd': best_line['underOdds'],
                    'lineID': best_line['lineId'],
                    'isAlt': best_line['isAlt'],
                    'market_group_id': market_group_id,
                    'matched_param': best_line['points']
                }
            else:
                return None

        case _:
            print(f"⚠️ [PIN888 区间补单] basketball 不支持的盘口类型: {platform_handicap}")
            return None

    return None
