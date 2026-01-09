def map_sport_base(sport_type: str) -> dict | None:
    """
    映射基础运动信息 (sportId 和 period_num)

    Args:
        sport_type: 运动类型 ('soccer', 'basketball')

    Returns:
        {
            'mapped_sportId': int,        # PIN888运动ID (29=足球, 4=篮球)
            'mapped_period_num': str      # PIN888订阅时段字符串
        }
        如果不支持该运动类型，返回 None
    """
    if not sport_type:
        print(f"❌ [PIN888 Mapping] sport_type 参数为空")
        return None

    sport_type = sport_type.lower().strip()

    if sport_type == 'soccer':
        return {
            'mapped_sportId': 29,
            'mapped_period_num': "0,8,39,3,4,5,6,7"
        }
    elif sport_type == 'basketball':
        return {
            'mapped_sportId': 4,
            'mapped_period_num': "0,2"
        }
    else:
        print(f"❌ [PIN888 Mapping] 不支持的球类: {sport_type}")
        return None


def map_handicap_full(
    sport_type: str,
    handicap: str,
    period: str,
    handicap_param: str,
    home_team: str = None,
    away_team: str = None
) -> dict | None:
    """
    映射盘口详细信息

    Args:
        sport_type: 运动类型 ('soccer', 'basketball')
        handicap: 盘口类型 ('Total Over(2.5)', 'Asian Handicap1(-1.5)', '1X', etc.)
        period: 时段 ('Full Time', '1st Half', '1st Quarter', etc.)
        handicap_param: 盘口参数值 ('2.5', '-1.5', etc.)
        home_team: 主队名称 (可选,某些盘口需要)
        away_team: 客队名称 (可选,某些盘口需要)

    Returns:
        {
            'mapped_market': str,              # 市场类型 ('normal', 'specials', 'corners')
            'mapped_handicap': str,            # PIN888盘口名称
            'mapped_handicap_param': str,      # 转换后的参数
            'mapped_direction': str,           # 方向 (可选)
            'mapped_match': str,               # 匹配类型 (可选)
            'mapped_period': str               # 具体时段
        }
        如果映射失败，返回 None
    """
    # 参数验证
    if not sport_type or not handicap or not period:
        print(f"❌ [PIN888 Mapping] 缺少必需参数")
        print(f"  sport_type: {sport_type}")
        print(f"  handicap: {handicap}")
        print(f"  period: {period}")
        return None

    # 标准化输入
    sport_type = sport_type.lower().strip()
    handicap = handicap.strip()
    period = period.strip()

    # 初始化返回字典
    result = {}

    # 根据运动类型进行映射
    match sport_type:
        case 'soccer':
            match handicap.lower():
                case "1" | "2" | "x":
                    result['mapped_market'] = 'normal'
                    result['mapped_handicap'] = 'moneyLine'

                    period_lower = period.lower()
                    if period_lower in ['full time', 'hidden period']:
                        result['mapped_period'] = '0'
                    elif period_lower in ['1st half', '2nd half']:
                        result['mapped_period'] = '1'
                    else:
                        return None

                    handicap_lower = handicap.lower()
                    if handicap_lower == '1':
                        result['mapped_match'] = 'homePrice'
                        result['mapped_handicap_param'] = 'homePrice'
                    elif handicap_lower == '2':
                        result['mapped_match'] = 'awayPrice'
                        result['mapped_handicap_param'] = 'awayPrice'
                    elif handicap_lower == 'x':
                        result['mapped_match'] = 'drawPrice'
                        result['mapped_handicap_param'] = 'drawPrice'
                    else:
                        print(f"❌ [PIN888 Mapping] 不支持的盘口: {handicap}")
                        return None

                case '1x' | "x2" | '12':
                    result['mapped_market'] = 'specials'

                    period_lower = period.lower()
                    if period_lower in ['full time', 'hidden period']:
                        result['mapped_handicap'] = 'Double Chance'
                    elif period_lower == '1st half':
                        result['mapped_handicap'] = 'Double Chance 1st Half'
                    elif period_lower == '2nd half':
                        result['mapped_handicap'] = 'Double Chance 2nd Half'
                    else:
                        return None

                    handicap_lower = handicap.lower()
                    if handicap_lower == '1x':
                        if not home_team:
                            print(f"❌ [PIN888 Mapping] 1X盘口需要home_team参数")
                            return None
                        result['mapped_handicap_param'] = home_team + ' or Draw'
                    elif handicap_lower == 'x2':
                        if not away_team:
                            print(f"❌ [PIN888 Mapping] X2盘口需要away_team参数")
                            return None
                        result['mapped_handicap_param'] = 'Draw or ' + away_team
                    elif handicap_lower == '12':
                        if not home_team or not away_team:
                            print(f"❌ [PIN888 Mapping] 12盘口需要home_team和away_team参数")
                            return None
                        result['mapped_handicap_param'] = home_team + ' or ' + away_team
                    else:
                        print(f"❌ [PIN888 Mapping] 不支持的盘口: {handicap}")
                        return None

                case "odd" | "even":
                    result['mapped_market'] = 'specials'

                    period_lower = period.lower()
                    if period_lower in ['full time', 'hidden period']:
                        result['mapped_handicap'] = "Total Goals Odd/Even"
                    elif period_lower == '1st half':
                        result['mapped_handicap'] = "Total Goals Odd/Even 1st Half"
                    elif period_lower == '2nd half':
                        result['mapped_handicap'] = "Total Goals Odd/Even 2nd Half"
                    else:
                        return None

                    handicap_lower = handicap.lower()
                    if handicap_lower == 'odd':
                        result['mapped_match'] = 'Odd'
                        result['mapped_handicap_param'] = 'Odd'
                    elif handicap_lower == 'even':
                        result['mapped_match'] = 'Even'
                        result['mapped_handicap_param'] = 'Even'
                    else:
                        return None

                case "both to score" | "one scoreless" | "both teams to score":
                    result['mapped_market'] = 'specials'

                    period_lower = period.lower()
                    if period_lower in ['full time', 'hidden period']:
                        result['mapped_handicap'] = "Both Teams To Score?"
                    elif period_lower == '1st half':
                        result['mapped_handicap'] = "Both Teams To Score? 1st Half"
                    elif period_lower == '2nd half':
                        result['mapped_handicap'] = "Both Teams To Score? 2nd Half"
                    else:
                        return None

                    handicap_lower = handicap.lower()
                    if handicap_lower == 'both to score':
                        result['mapped_match'] = 'n'
                        result['mapped_handicap_param'] = 'Yes'
                    elif handicap_lower == 'one scoreless':
                        result['mapped_match'] = 'n'
                        result['mapped_handicap_param'] = 'No'
                    else:
                        return None

                case "asian handicap1(0.0)/draw no bet" | "asian handicap2(0.0)/draw no bet":
                    result['mapped_market'] = 'specials'

                    period_lower = period.lower()
                    if period_lower in ['full time', 'hidden period']:
                        result['mapped_handicap'] = 'Draw No Bet'
                    elif period_lower == '1st half':
                        result['mapped_handicap'] = 'Draw No Bet 1st Half'
                    elif period_lower == '2nd half':
                        result['mapped_handicap'] = 'Draw No Bet 2nd Half'
                    else:
                        return None

                    handicap_lower = handicap.lower()
                    if handicap_lower == 'asian handicap1(0.0)/draw no bet':
                        if not home_team:
                            print(f"❌ [PIN888 Mapping] Draw No Bet需要home_team参数")
                            return None
                        result['mapped_match'] = 'n'
                        result['mapped_handicap_param'] = home_team
                    elif handicap_lower == 'asian handicap2(0.0)/draw no bet':
                        if not away_team:
                            print(f"❌ [PIN888 Mapping] Draw No Bet需要away_team参数")
                            return None
                        result['mapped_match'] = 'n'
                        result['mapped_handicap_param'] = away_team
                    else:
                        return None

                case "team1 win" | "team2 win":
                    result['mapped_market'] = 'normal'
                    result['mapped_handicap'] = 'moneyLine'

                    period_lower = period.lower()
                    if period_lower in ['full time', 'hidden period']:
                        result['mapped_period'] = '0'
                    elif period_lower in ['1st half', '2nd half']:
                        result['mapped_period'] = '1'
                    else:
                        print(period_lower)
                        return None

                    handicap_lower = handicap.lower()
                    if handicap_lower == 'team1 win':
                        result['mapped_direction'] = 'home'
                        result['mapped_handicap_param'] = 'homePrice'
                    elif handicap_lower == 'team2 win':
                        result['mapped_direction'] = 'away'
                        result['mapped_handicap_param'] = 'awayPrice'
                    else:
                        print(handicap_lower)
                        return None

                case _:
                    handicap_lower = handicap.lower()

                    # Total Over/Under 匹配
                    if (handicap_lower.startswith('total over(') or handicap_lower.startswith('total under(')) and ('corners' not in handicap_lower) and ('for' not in handicap_lower):
                        result['mapped_market'] = 'normal'
                        result['mapped_handicap'] = 'overUnder'
                        result['mapped_match'] = 'points'

                        period_lower = period.lower()
                        if period_lower in ['full time', 'hidden period']:
                            result['mapped_period'] = '0'
                        elif period_lower in ['1st half', '2nd half']:
                            result['mapped_period'] = '1'
                        else:
                            return None

                        if handicap_lower.startswith('total over('):
                            result['mapped_direction'] = 'Over'
                            result['mapped_handicap_param'] = format_pin888_remove_dot_zero(handicap_param)
                        elif handicap_lower.startswith('total under('):
                            result['mapped_direction'] = 'Under'
                            result['mapped_handicap_param'] = format_pin888_remove_dot_zero(handicap_param)
                        else:
                            return None

                    # Asian Handicap 匹配
                    elif (handicap_lower.startswith('asian handicap1(') or handicap_lower.startswith('asian handicap2(')) and ('corners' not in handicap_lower):
                        result['mapped_market'] = 'normal'
                        result['mapped_handicap'] = 'handicap'

                        period_lower = period.lower()
                        if period_lower in ['full time', 'hidden period']:
                            result['mapped_period'] = '0'
                        elif period_lower in ['1st half', '2nd half']:
                            result['mapped_period'] = '1'
                        else:
                            return None

                        if handicap_lower.startswith('asian handicap1('):
                            result['mapped_direction'] = 'Home'
                            result['mapped_match'] = 'homeSpread'
                            result['mapped_handicap_param'] = format_pin888_param(handicap_param)
                        elif handicap_lower.startswith('asian handicap2('):
                            result['mapped_direction'] = 'Away'
                            result['mapped_match'] = 'awaySpread'
                            result['mapped_handicap_param'] = format_pin888_param(handicap_param)
                        else:
                            return None

                    # Corners Total Over/Under 匹配
                    elif (handicap_lower.startswith('total over(') and '- corners' in handicap_lower) or \
                         (handicap_lower.startswith('total under(') and '- corners' in handicap_lower):
                        result['mapped_market'] = 'corners'
                        result['mapped_handicap'] = 'overUnder'

                        period_lower = period.lower()
                        if period_lower in ['full time', 'hidden period']:
                            result['mapped_period'] = '0'
                        elif period_lower in ['1st half', '2nd half']:
                            result['mapped_period'] = '1'
                        else:
                            return None

                        if handicap_lower.startswith('total over(') and '- corners' in handicap_lower:
                            result['mapped_direction'] = 'Over'
                            result['mapped_match'] = 'points'
                            result['mapped_handicap_param'] = str(handicap_param)
                        elif handicap_lower.startswith('total under(') and '- corners' in handicap_lower:
                            result['mapped_direction'] = 'Under'
                            result['mapped_match'] = 'points'
                            result['mapped_handicap_param'] = str(handicap_param)
                        else:
                            return None

                    # Corners Asian Handicap 匹配
                    elif (handicap_lower.startswith('asian handicap1(') and '- corners' in handicap_lower) or \
                         (handicap_lower.startswith('asian handicap2(') and '- corners' in handicap_lower):
                        result['mapped_market'] = 'corners'
                        result['mapped_handicap'] = 'handicap'

                        period_lower = period.lower()
                        if period_lower in ['full time', 'hidden period']:
                            result['mapped_period'] = '0'
                        elif period_lower in ['1st half', '2nd half']:
                            result['mapped_period'] = '1'
                        else:
                            return None

                        if handicap_lower.startswith('asian handicap1(') and '- corners' in handicap_lower:
                            result['mapped_direction'] = 'Home'
                            result['mapped_match'] = 'homeSpread'
                            result['mapped_handicap_param'] = str(handicap_param)
                        elif handicap_lower.startswith('asian handicap2(') and '- corners' in handicap_lower:
                            result['mapped_direction'] = 'Away'
                            result['mapped_match'] = 'awaySpread'
                            result['mapped_handicap_param'] = str(handicap_param)
                        else:
                            return None

                    # Team Totals 匹配
                    elif (handicap_lower.startswith('total over(') and 'for team' in handicap_lower) or \
                         (handicap_lower.startswith('total under(') and 'for team' in handicap_lower):
                        result['mapped_market'] = 'normal'
                        result['mapped_handicap'] = 'teamTotals'

                        period_lower = period.lower()
                        if period_lower in ['full time', 'hidden period']:
                            result['mapped_period'] = '0'
                        elif period_lower in ['1st half', '2nd half']:
                            result['mapped_period'] = '1'
                        else:
                            return None

                        if handicap_lower.startswith('total over(') and 'for team1' in handicap_lower:
                            result['mapped_direction'] = 'home'
                            result['mapped_match'] = 'over'
                            result['mapped_handicap_param'] = str(handicap_param)
                        elif handicap_lower.startswith('total under(') and 'for team1' in handicap_lower:
                            result['mapped_direction'] = 'home'
                            result['mapped_match'] = 'under'
                            result['mapped_handicap_param'] = str(handicap_param)
                        elif handicap_lower.startswith('total over(') and 'for team2' in handicap_lower:
                            result['mapped_direction'] = 'away'
                            result['mapped_match'] = 'over'
                            result['mapped_handicap_param'] = str(handicap_param)
                        elif handicap_lower.startswith('total under(') and 'for team2' in handicap_lower:
                            result['mapped_direction'] = 'away'
                            result['mapped_match'] = 'under'
                            result['mapped_handicap_param'] = str(handicap_param)
                        else:
                            return None

                    else:
                        return None

        case 'basketball':
            period_lower = period.lower()
            handicap_lower = handicap.lower()

            # 设置时段映射
            if period_lower in ['full time', 'hidden period', 'with ot']:
                result['mapped_period'] = '0'
            elif period_lower == '1st half':
                result['mapped_period'] = '1'
            elif period_lower == '2nd half':
                result['mapped_period'] = '2'
            elif period_lower in ['1st quarter', '1st qtr', '1rd qtr']:
                result['mapped_period'] = '3'
            elif period_lower in ['2nd quarter', '2nd qtr', '2rd qtr']:
                result['mapped_period'] = '4'
            elif period_lower in ['3rd quarter', '3rd qtr']:
                result['mapped_period'] = '5'
            elif period_lower in ['4th quarter', '4th qtr', '4rd qtr']:
                result['mapped_period'] = '6'
            else:
                return None

            # 盘口匹配
            if handicap_lower in ['1', '2', 'x']:
                print('[PIN888 Mapping] 没有 overTime,不做处理')
                return None

            elif handicap_lower in ['team1 win', 'team2 win']:
                result['mapped_market'] = 'normal'
                result['mapped_handicap'] = 'moneyLine'
                if handicap_lower == 'team1 win':
                    result['mapped_direction'] = 'home'
                    result['mapped_handicap_param'] = 'homePrice'
                elif handicap_lower == 'team2 win':
                    result['mapped_direction'] = 'away'
                    result['mapped_handicap_param'] = 'awayPrice'

            elif handicap_lower.startswith('asian handicap1(') or handicap_lower.startswith('asian handicap2('):
                result['mapped_market'] = 'normal'
                result['mapped_handicap'] = 'handicap'
                if handicap_lower.startswith('asian handicap1('):
                    result['mapped_direction'] = 'Home'
                    result['mapped_match'] = 'homeSpread'
                    result['mapped_handicap_param'] = str(handicap_param)
                elif handicap_lower.startswith('asian handicap2('):
                    result['mapped_direction'] = 'Away'
                    result['mapped_match'] = 'awaySpread'
                    result['mapped_handicap_param'] = str(handicap_param)

            elif handicap_lower.startswith('total over(') or handicap_lower.startswith('total under('):
                if 'for team' in handicap_lower:
                    result['mapped_market'] = 'normal'
                    result['mapped_handicap'] = 'teamTotals'
                    if 'team1' in handicap_lower:
                        result['mapped_direction'] = 'home'
                    else:
                        result['mapped_direction'] = 'away'

                    if 'total over' in handicap_lower:
                        result['mapped_match'] = 'over'
                    else:
                        result['mapped_match'] = 'under'
                    result['mapped_handicap_param'] = str(handicap_param)
                else:
                    result['mapped_market'] = 'normal'
                    result['mapped_handicap'] = 'overUnder'
                    if handicap_lower.startswith('total over('):
                        result['mapped_direction'] = 'Over'
                    else:
                        result['mapped_direction'] = 'Under'
                    result['mapped_match'] = 'points'
                    result['mapped_handicap_param'] = str(handicap_param)

            else:
                return None

        case _:
            print(f"❌ [PIN888 Mapping] 不支持的运动类型: {sport_type}")
            return None

    return result


def pin888(
    sport_type: str,
    handicap: str,
    period: str,
    handicap_param: str,
    home_team: str = None,
    away_team: str = None
) -> dict | None:
    """
    将标准盘口参数映射为 PIN888 平台格式 (主函数)

    Args:
        sport_type: 运动类型 ('soccer', 'basketball')
        handicap: 盘口类型 ('Total Over(2.5)', 'Asian Handicap1(-1.5)', '1X', etc.)
        period: 时段 ('Full Time', '1st Half', '1st Quarter', etc.)
        handicap_param: 盘口参数值 ('2.5', '-1.5', etc.)
        home_team: 主队名称 (可选,某些盘口需要)
        away_team: 客队名称 (可选,某些盘口需要)

    Returns:
        完整的映射结果字典，包含以下字段:
        {
            'mapped_sportId': int,
            'mapped_period_num': str,
            'mapped_market': str,
            'mapped_handicap': str,
            'mapped_handicap_param': str,
            'mapped_direction': str,
            'mapped_match': str,
            'mapped_period': str
        }
        如果映射失败，返回 None
    """
    # 步骤1: 映射基础运动信息
    base_info = map_sport_base(sport_type)
    if not base_info:
        return None

    # 步骤2: 映射盘口详细信息
    handicap_info = map_handicap_full(
        sport_type=sport_type,
        handicap=handicap,
        period=period,
        handicap_param=handicap_param,
        home_team=home_team,
        away_team=away_team
    )
    if not handicap_info:
        return None

    # 步骤3: 合并结果
    return {**base_info, **handicap_info}





def format_pin888_param(value):
    """
    格式化 PIN888 的参数值 (带符号)
    - 正数前面加 +
    - 负数保持 -
    - 整数加 .0 (如 2 → +2.0, -1 → -1.0)
    - 小数保持不变 (如 2.5 → +2.5)

    Args:
        value: 数值参数 (可以是 str, int, float)

    Returns:
        str: 格式化后的字符串 (如 "+2.0", "+2.5", "-1.0", "-1.5")
    """
    try:
        num = float(value)

        # 判断是否为整数
        if num == int(num):
            # 整数格式: +2.0 或 -1.0
            if num >= 0:
                return f"+{int(num)}.0"
            else:
                return f"{int(num)}.0"
        else:
            # 小数格式: +2.5 或 -1.5
            if num >= 0:
                return f"+{value}"
            else:
                return str(value)
    except:
        # 如果无法转换为数字,直接返回原值
        return str(value)


def format_pin888_param_no_sign(value):
    """
    格式化 PIN888 的参数值 (不带符号)
    - 整数加 .0 (如 2 → 2.0, -1 → -1.0)
    - 小数保持不变 (如 2.5 → 2.5)

    Args:
        value: 数值参数 (可以是 str, int, float)

    Returns:
        str: 格式化后的字符串 (如 "2.0", "2.5", "-1.0", "-1.5")
    """
    try:
        num = float(value)

        # 判断是否为整数
        if num == int(num):
            # 整数格式: 2.0 或 -1.0
            return f"{int(num)}.0"
        else:
            # 小数格式: 2.5 或 -1.5
            return str(value)
    except:
        # 如果无法转换为数字,直接返回原值
        return str(value)


def format_pin888_remove_dot_zero(value):
    """
    格式化 PIN888 的参数值 (移除 .0)
    - 如果是整数 (如 2.0),去掉 .0 变成 2
    - 小数保持不变 (如 2.5 → 2.5)

    Args:
        value: 数值参数 (可以是 str, int, float)

    Returns:
        str: 格式化后的字符串 (如 "2", "2.5", "-1", "-1.5")
    """
    try:
        num = float(value)

        # 判断是否为整数
        if num == int(num):
            # 整数格式: 去掉 .0
            return str(int(num))
        else:
            # 小数格式: 保持不变
            return str(value)
    except:
        # 如果无法转换为数字,直接返回原值
        return str(value)



def normalize_period_name(period):
    """标准化时段名称,将拼写变体转换为标准形式"""
    period_lower = period.lower()
    # 标准化映射
    normalize_map = {
        '1st half': '1st Half',
        '2nd half': '2nd Half',
        '1rd qtr': '1st Quarter',
        '2rd qtr': '2nd Quarter',
        '3rd qtr': '3rd Quarter',
        '4rd qtr': '4th Quarter',
        'with ot': 'with OT',
    }
    return normalize_map.get(period_lower, period)

