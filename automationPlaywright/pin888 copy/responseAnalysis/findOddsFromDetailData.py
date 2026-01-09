"""
PIN888 平台 - 从详细赔率数据中查找特定赔率
使用独立参数替代 msg 字典的纯函数实现
"""


def find_odds_from_detail_data(
    sport_type: str,
    market_group: str,
    platform_handicap: str,
    platform_handicap_param: str,
    platform_direction: str,
    platform_match: str,
    period: str,
    detail_odds: dict
) -> dict | str | None:
    """
    从详细赔率数据中查找匹配的赔率

    参数:
        sport_type: 运动类型 ('soccer' 或 'basketball')
        market_group: 市场组 ('normal', 'specials', 'corners')
        platform_handicap: 盘口类型 ('handicap', 'overUnder', 'moneyLine' 等)
        platform_handicap_param: 盘口参数 (如 '2.5', '-0.25')
        platform_direction: 方向 ('home', 'away', 'over', 'under')
        platform_match: 匹配类型 ('over', 'under', 'even', 'odd' 等)
        period: 时间段 ('0' 全场, '1' 上半场)
        detail_odds: 详细赔率数据

    返回:
        dict: 包含 odd, lineID 等字段的字典
        str: 'need refresh' 表示需要刷新数据
        None: 匹配失败
    """
    try:
        match sport_type:
            case 'soccer':
                match market_group:
                    case 'normal':
                        if not detail_odds.get('normal'):
                            return 'need refresh'
                        return parse_soccer_normal(
                            platform_handicap,
                            platform_handicap_param,
                            platform_direction,
                            platform_match,
                            period,
                            detail_odds
                        )

                    case 'specials':
                        if not detail_odds.get('specials'):
                            return 'need refresh'
                        return parse_soccer_specials(
                            platform_handicap,
                            platform_handicap_param,
                            platform_match,
                            detail_odds
                        )

                    case 'corners':
                        if not detail_odds.get('corners'):
                            return 'need refresh'
                        return parse_soccer_corners(
                            platform_handicap,
                            platform_handicap_param,
                            platform_direction,
                            period,
                            detail_odds
                        )

                    case _:
                        print(f"pin888 不支持的market_groups: {market_group}")
                        return None

            case 'basketball':
                if not detail_odds.get('normal'):
                    print(f"❌ [PIN888] detailOdds['normal'] 为 None")
                    return 'need refresh'

                normal_data = detail_odds.get('normal')
                periods = normal_data.get('periods')
                if periods is None:
                    print(f"❌ [PIN888] detailOdds['normal']['periods'] 为 None")
                    return None

                data = periods.get(period, {})
                if not data:
                    print(f"⚠️ [PIN888] basketball 数据为空")
                    return None

                market_group_id = normal_data.get('id')
                return parse_basketball(
                    platform_handicap,
                    platform_handicap_param,
                    platform_direction,
                    platform_match,
                    data,
                    market_group_id
                )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    return None


def parse_soccer_normal(
    platform_handicap: str,
    platform_handicap_param: str,
    platform_direction: str,
    platform_match: str,
    period: str,
    detail_odds: dict
) -> dict | None:
    """解析足球正常盘口数据"""
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
        case 'moneyLine':
            data = data['moneyLine']
            _match = platform_handicap_param
            odd = data[_match]
            lineID = data['lineId']
            return {
                'odd': odd,
                'lineID': lineID,
                'market_group_id': market_group_id
            }

        case 'overUnder':
            data = data['overUnder']
            for line in data:
                if float(platform_handicap_param) == float(line['points']):
                    if platform_direction.lower() == 'over':
                        return {
                            'odd': line['overOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt'],
                            'market_group_id': market_group_id
                        }
                    elif platform_direction.lower() == 'under':
                        return {
                            'odd': line['underOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt'],
                            'market_group_id': market_group_id
                        }
                    else:
                        return None
                else:
                    continue

            # 未匹配成功,打印所有可用盘口
            print(f"⚠️ [PIN888] overUnder 未匹配成功")
            print(f"🔍 [PIN888] 寻找参数: points={platform_handicap_param}, direction={platform_direction}")
            print(f"[PIN888] 📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, "
                      f"lineId={line['lineId']}, offline={line['offline']}, unavailable={line['unavailable']}")
            return None

        case 'handicap':
            data = data['handicap']
            for line in data:
                if platform_direction.lower() == 'home':
                    if float(line['homeSpread']) == float(platform_handicap_param):
                        return {
                            'odd': line['homeOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt'],
                            'market_group_id': market_group_id
                        }
                elif platform_direction.lower() == 'away':
                    if float(line['awaySpread']) == float(platform_handicap_param):
                        return {
                            'odd': line['awayOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt'],
                            'market_group_id': market_group_id
                        }
                else:
                    continue

            # 未匹配成功,打印所有可用盘口
            print(f"⚠️ [PIN888] handicap 未匹配成功")
            print(f"🔍 寻找参数: {platform_direction}Spread={platform_handicap_param}")
            print(f"📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] homeSpread={line['homeSpread']}, awaySpread={line['awaySpread']}, "
                      f"homeOdds={line['homeOdds']}, awayOdds={line['awayOdds']}, "
                      f"lineId={line['lineId']}, offline={line['offline']}, unavailable={line['unavailable']}")
            return None

        case 'teamTotals':
            data = data['teamTotals']
            if not data:
                print(f"⚠️ [PIN888] teamTotals 数据为空，也就是说，盘口全部都关闭了1")
                return None
            team_type = 'awayLines' if platform_direction.lower() == 'away' else 'homeLines'
            data = data[team_type]

            if not data:
                print(f"⚠️ [PIN888] teamTotals 数据为空，也就是说，盘口全部都关闭了2")
                return None


            for line in data:
                if platform_match.lower() == 'over':
                    if float(line['points']) == float(platform_handicap_param):
                        return {
                            'odd': line['overOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt'],
                            'market_group_id': market_group_id
                        }
                elif platform_match.lower() == 'under':
                    if float(line['points']) == float(platform_handicap_param):
                        return {
                            'odd': line['underOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt'],
                            'market_group_id': market_group_id
                        }
                else:
                    continue

            # 未匹配成功,打印所有可用盘口
            print(f"⚠️ [PIN888] teamTotals 未匹配成功")
            print(f"🔍 寻找参数: {team_type}, points={platform_handicap_param}, match={platform_match}")
            print(f"📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, "
                      f"lineId={line['lineId']}, offline={line['offline']}, unavailable={line['unavailable']}")
            return None


def parse_soccer_specials(
    platform_handicap: str,
    platform_handicap_param: str,
    platform_match: str,
    detail_odds: dict
) -> dict | None:
    """解析足球特殊盘口数据"""
    try:
        data = detail_odds['specials'][0]['events']

        for line in data:
            market_group_id = line['id']
            match platform_handicap.lower():
                case 'total goals odd/even' | 'total goals odd/even 1st half' | 'total goals odd/even 2nd half':
                    if line['name'].lower() == platform_handicap.lower():
                        contestants = line['contestants']
                        for contestant in contestants:
                            if platform_match.lower() == contestant['n'].lower():
                                return {
                                    'odd': contestant['p'],
                                    'lineID': contestant['l'],
                                    'market_group_id': market_group_id,
                                    'specials_i': contestant['i']
                                }
                            else:
                                continue

                case 'both teams to score?' | 'both teams to score? 1st half' | 'both teams to score? 2nd half' | 'both to score' | 'both to score? 1st half' | 'both to score? 2nd half':
                    if line['name'].lower() == platform_handicap.lower():
                        contestants = line['contestants']
                        for contestant in contestants:
                            if platform_handicap_param.lower() == contestant['n'].lower():
                                return {
                                    'odd': contestant['p'],
                                    'lineID': contestant['l'],
                                    'market_group_id': market_group_id,
                                    'specials_i': contestant['i']
                                }
                            else:
                                continue

                case 'double chance' | 'double chance 1st half' | 'double chance 2nd half':
                    if line['name'].lower() == platform_handicap.lower():
                        contestants = line['contestants']
                        for contestant in contestants:
                            if platform_handicap_param.lower() == contestant['n'].lower():
                                return {
                                    'odd': contestant['p'],
                                    'lineID': contestant['l'],
                                    'market_group_id': market_group_id,
                                    'specials_i': contestant['i']
                                }
                            else:
                                continue

                case 'draw no bet' | 'draw no bet 1st half' | 'draw no bet 2nd half':
                    if line['name'].lower() == platform_handicap.lower():
                        contestants = line['contestants']
                        for contestant in contestants:
                            if platform_handicap_param.lower() == contestant['n'].lower():
                                return {
                                    'odd': contestant['p'],
                                    'lineID': contestant['l'],
                                    'market_group_id': market_group_id,
                                    'specials_i': contestant['i'],
                                    'specials_event_id': market_group_id
                                }
                            else:
                                continue

                case _:
                    print(f"pin888 不支持的盘口: {platform_handicap}")
                    return None

    except Exception as e:
        import traceback
        traceback.print_exc()
        print('返回的数据中没有 specials 项, 说明盘口没有开')
        return None


def parse_soccer_corners(
    platform_handicap: str,
    platform_handicap_param: str,
    platform_direction: str,
    period: str,
    detail_odds: dict
) -> dict | None:
    """解析足球角球盘口数据"""
    try:
        data = detail_odds.get('corners', {})
        market_group_id = data['id']
        if not data:
            print(f"⚠️ [PIN888] corners 数据为空")
            return None
        data = data['periods'].get(period, {})
        if not data:
            print(f"⚠️ [PIN888] corners 数据为空")
            return None

        match platform_handicap.lower():
            case 'handicap':
                data = data.get('handicap', [])
                for line in data:
                    if platform_direction.lower() == 'home':
                        if float(line['homeSpread']) == float(platform_handicap_param):
                            return {
                                'odd': line['homeOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id': market_group_id
                            }
                    elif platform_direction.lower() == 'away':
                        if float(line['awaySpread']) == float(platform_handicap_param):
                            return {
                                'odd': line['awayOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id': market_group_id
                            }
                    else:
                        continue

                # 未匹配成功,打印所有可用盘口
                print(f"⚠️ [PIN888] corners handicap 未匹配成功")
                print(f"🔍 寻找参数: {platform_direction}Spread={platform_handicap_param}")
                print(f"📋 所有可用盘口 (共 {len(data)} 个):")
                for idx, line in enumerate(data, 1):
                    print(f"  [{idx}] homeSpread={line['homeSpread']}, awaySpread={line['awaySpread']}, "
                          f"homeOdds={line['homeOdds']}, awayOdds={line['awayOdds']}, lineId={line['lineId']}")
                return None

            case 'overunder':
                data = data.get('overUnder', [])
                print(data)
                for line in data:
                    if platform_direction.lower() == 'over':
                        if float(line['points']) == float(platform_handicap_param):
                            return {
                                'odd': line['overOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id': market_group_id
                            }
                    elif platform_direction.lower() == 'under':
                        if float(line['points']) == float(platform_handicap_param):
                            return {
                                'odd': line['underOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id': market_group_id
                            }
                    else:
                        continue

                # 未匹配成功,打印所有可用盘口
                print(f"⚠️ [PIN888] corners overUnder 未匹配成功")
                print(f"🔍 寻找参数: points={platform_handicap_param}, direction={platform_direction}")
                print(f"📋 所有可用盘口 (共 {len(data)} 个):")
                for idx, line in enumerate(data, 1):
                    print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, lineId={line['lineId']}")
                return None

            case _:
                print(f"pin888 不支持的盘口: {platform_handicap}")
                return None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    return None


def parse_basketball(
    platform_handicap: str,
    platform_handicap_param: str,
    platform_direction: str,
    platform_match: str,
    detail_odds: dict,
    market_group_id: int
) -> dict | None:
    """解析篮球盘口数据"""
    match platform_handicap.lower():
        case 'handicap':
            data = detail_odds.get('handicap')

            if not data:
                print(f"⚠️ [PIN888] basketball handicap 数据为空")
                return None
            for line in data:
                if platform_direction.lower() == 'home':
                    if float(line['homeSpread']) == float(platform_handicap_param):
                        return {
                            'odd': line['homeOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt'],
                            'market_group_id': market_group_id
                        }

                elif platform_direction.lower() == 'away':
                    if float(line['awaySpread']) == float(platform_handicap_param):
                        return {
                            'odd': line['awayOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt'],
                            'market_group_id': market_group_id
                        }

            print(f"⚠️ [PIN888] basketball handicap 未匹配成功")
            print(f"🔍 寻找参数: {platform_direction}Spread={platform_handicap_param}")
            print(f"📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] homeSpread={line['homeSpread']}, awaySpread={line['awaySpread']}, "
                      f"homeOdds={line['homeOdds']}, awayOdds={line['awayOdds']}, "
                      f"lineId={line['lineId']}, offline={line['offline']}, unavailable={line['unavailable']}")
            return None

        case 'overunder':
            data = detail_odds.get('overUnder')
            if not data:
                print(f"⚠️ [PIN888] basketball overUnder 数据为空")
                return None
            for line in data:
                if platform_direction.lower() == 'over':
                    if float(line['points']) == float(platform_handicap_param):
                        return {
                            'odd': line['overOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt'],
                            'market_group_id': market_group_id
                        }
                elif platform_direction.lower() == 'under':
                    if float(line['points']) == float(platform_handicap_param):
                        return {
                            'odd': line['underOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt'],
                            'market_group_id': market_group_id
                        }
                else:
                    continue

            print(f"⚠️ [PIN888] basketball overUnder 未匹配成功")
            print(f"🔍 寻找参数: points={platform_handicap_param}")
            print(f"📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, lineId={line['lineId']}")
            return None

        case 'moneyline':
            data = detail_odds.get('moneyLine')
            if not data:
                print(f"⚠️ [PIN888] basketball moneyLine 数据为空")
                return None

            if platform_direction.lower() == 'home':
                return {
                    'odd': data.get('homePrice', ''),
                    'lineID': data.get('lineId', ''),
                    'market_group_id': market_group_id
                }
            elif platform_direction.lower() == 'away':
                return {
                    'odd': data.get('awayPrice', ''),
                    'lineID': data.get('lineId', ''),
                    'market_group_id': market_group_id
                }

            print(f"⚠️ [PIN888] basketball moneyLine 未匹配成功")
            print(f"🔍 寻找参数: {platform_direction}")
            print(f"📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] homePrice={line['homePrice']}, awayPrice={line['awayPrice']}, lineId={line['lineId']}")
            return None

        case 'teamtotals':
            teamTotalsData = detail_odds.get('teamTotals')

            if not teamTotalsData:
                print(f"⚠️ [PIN888] basketball teamTotals 数据为空，也就是说，盘口全部都关闭了3")
                return None

            if platform_direction.lower() == 'home':
                data = teamTotalsData.get('homeLines', {})
                for line in data:
                    if platform_match.lower() == 'over':
                        if float(line['points']) == float(platform_handicap_param):
                            return {
                                'odd': line['overOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id': market_group_id
                            }
                    elif platform_match.lower() == 'under':
                        if float(line['points']) == float(platform_handicap_param):
                            return {
                                'odd': line['underOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id': market_group_id
                            }
                    else:
                        continue
                    
            elif platform_direction.lower() == 'away':
                data = teamTotalsData.get('awayLines', {})
                for line in data:
                    if platform_match.lower() == 'over':
                        if float(line['points']) == float(platform_handicap_param):
                            return {
                                'odd': line['overOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id': market_group_id
                            }
                    elif platform_match.lower() == 'under':
                        if float(line['points']) == float(platform_handicap_param):
                            return {
                                'odd': line['underOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id': market_group_id
                            }
                    else:
                        continue

            print(f"⚠️ [PIN888] basketball teamTotals 未匹配成功")
            print(f"🔍 寻找参数: {platform_direction}, points={platform_handicap_param}, match={platform_match}")

            # 根据 platform_direction 选择对应的盘口数据
            if platform_direction.lower() == 'home':
                lines = teamTotalsData.get('homeLines', [])
                team_label = "主队"
            elif platform_direction.lower() == 'away':
                print(teamTotalsData)
                lines = teamTotalsData.get('awayLines', [])
                team_label = "客队"
            else:
                lines = []
                team_label = "未知"

            if lines:
                print(f"📋 {team_label}盘口 (共 {len(lines)} 个):")
                for idx, line in enumerate(lines, 1):
                    print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, "
                          f"lineId={line['lineId']}, isAlt={line.get('isAlt', False)}")
            else:
                print(f"📋 未找到 {team_label} 盘口数据")

            return None
