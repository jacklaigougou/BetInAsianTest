"""
Pin888 我的投注记录响应数据

此文件包含从 Pin888 平台获取的投注记录数据。
每个投注记录是一个包含多个字段的数组，已转换为字典格式以便于访问。
"""

# 原始数组格式的投注记录数据
my_bets_raw = [
    [
        687941788,  # wagerId: 投注ID
        0,  # 未知字段
        "Chicago Bulls-vs-San Antonio Spurs",  # 比赛名称
        None,  # 未知字段
        None,  # 未知字段
        1,  # 未知字段
        None,  # 未知字段
        "2025-11-10 22:34:39",  # 投注时间
        "2025-11-10",  # 日期
        "2.180",  # 赔率（字符串格式）
        1762823400000,  # 时间戳（毫秒）
        "OPEN",  # 投注状态
        1762828479000,  # 时间戳（毫秒）
        "Chicago Bulls",  # 主队名称
        "San Antonio Spurs",  # 客队名称
        "Chicago Bulls",  # 投注队伍
        0,  # 未知字段
        0.00,  # 金额
        2.180,  # 赔率（数字格式）
        1,  # 未知字段
        1,  # 未知字段
        "NBA",  # 联赛名称
        1.75,  # 投注金额
        4,  # 运动类型ID
        "Basketball",  # 运动类型名称
        1,  # 未知字段
        "USD",  # 货币
        0,  # 未知字段
        0,  # 未知字段
        "",  # 空字符串
        1,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        0,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        "Regular",  # 投注类型
        "RISK",  # 投注方式（RISK/WIN）
        2.0700000,  # 未知字段
        1.7500000,  # 投注金额
        "SB",  # 未知字段
        "",  # 空字符串
        "",  # 空字符串
        0,  # 未知字段
        "",  # 空字符串
        "",  # 空字符串
        2.18,  # 赔率
        None,  # 未知字段
        "",  # 空字符串
        None,  # 未知字段
        1,  # 未知字段
        None,  # 未知字段
        0,  # 未知字段
        0,  # 未知字段
        0,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        0,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        "EVENT",  # 投注类型
        99,  # 未知字段
        0,  # 未知字段
        "",  # 空字符串
        0,  # 未知字段
        "",  # 空字符串
        None,  # 未知字段
        "",  # 空字符串
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        "2025-11-10 21:10:00",  # 比赛开始时间
        "Sets",  # 未知字段
        None,  # 未知字段
        1,  # 未知字段
        1619465422,  # 事件ID
        0,  # 未知字段
        0,  # 未知字段
        "",  # 空字符串
        "San Antonio Spurs",  # 客队名称
        None,  # 未知字段
        None,  # 未知字段
        "Regular"  # 投注类型
    ],
    [
        687942192,  # wagerId: 投注ID
        0,  # 未知字段
        "Geelong United-vs-Perth Lynx",  # 比赛名称
        None,  # 未知字段
        None,  # 未知字段
        1,  # 未知字段
        None,  # 未知字段
        "2025-11-10 22:28:42",  # 投注时间
        "2025-11-11",  # 日期
        "1.900",  # 赔率（字符串格式）
        1762848000000,  # 时间戳（毫秒）
        "OPEN",  # 投注状态
        1762828122000,  # 时间戳（毫秒）
        "Geelong United",  # 主队名称
        "Perth Lynx",  # 客队名称
        "Geelong United",  # 投注队伍
        0,  # 未知字段
        3.50,  # 金额
        1.900,  # 赔率（数字格式）
        1,  # 未知字段
        2,  # 未知字段
        "Australia - WNBL",  # 联赛名称
        1.00,  # 投注金额
        4,  # 运动类型ID
        "Basketball",  # 运动类型名称
        1,  # 未知字段
        "USD",  # 货币
        0,  # 未知字段
        1,  # 未知字段
        "",  # 空字符串
        0,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        0,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        "Regular",  # 投注类型
        "RISK",  # 投注方式（RISK/WIN）
        0.9000000,  # 未知字段
        1.0000000,  # 投注金额
        "SB",  # 未知字段
        "",  # 空字符串
        "",  # 空字符串
        0,  # 未知字段
        "",  # 空字符串
        "",  # 空字符串
        1.9,  # 赔率
        None,  # 未知字段
        "",  # 空字符串
        None,  # 未知字段
        0,  # 未知字段
        None,  # 未知字段
        0,  # 未知字段
        0,  # 未知字段
        0,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        0,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        "EVENT",  # 投注类型
        99,  # 未知字段
        0,  # 未知字段
        "",  # 空字符串
        0,  # 未知字段
        "",  # 空字符串
        None,  # 未知字段
        "",  # 空字符串
        None,  # 未知字段
        None,  # 未知字段
        None,  # 未知字段
        "2025-11-11 04:00:00",  # 比赛开始时间
        "Games",  # 未知字段
        None,  # 未知字段
        0,  # 未知字段
        1618998061,  # 事件ID
        0,  # 未知字段
        0,  # 未知字段
        "",  # 空字符串
        "Geelong United",  # 客队名称
        None,  # 未知字段
        None,  # 未知字段
        "Regular"  # 投注类型
    ]
]


def parse_bet_record(record):
    """
    将原始数组格式的投注记录转换为字典格式
    
    Args:
        record: 原始数组格式的投注记录
        
    Returns:
        dict: 结构化的投注记录字典
    """
    if not record or len(record) < 90:
        return None
    
    return {
        "wagerId": record[0],
        "matchName": record[2],
        "betTime": record[7],
        "date": record[8],
        "odds": float(record[9]) if record[9] else None,
        "timestamp": record[10],
        "status": record[11],
        "timestamp2": record[12],
        "homeTeam": record[13],
        "awayTeam": record[14],
        "betTeam": record[15],
        "amount": record[16],
        "oddsDecimal": record[17],
        "leagueName": record[20],
        "stake": record[21],
        "sportId": record[22],
        "sportName": record[23],
        "currency": record[25],
        "betType": record[38],
        "betMode": record[39],  # RISK or WIN
        "stake2": record[41],
        "odds2": record[48],
        "betType2": record[64],
        "eventStartTime": record[75],
        "eventId": record[79],
        "awayTeam2": record[83]
    }


# 结构化的投注记录列表
my_bets = [parse_bet_record(record) for record in my_bets_raw]

# 为了向后兼容，保留原始变量名
a = my_bets_raw
