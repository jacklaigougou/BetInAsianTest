"""
PIN888 平台区间补单(套利匹配)逻辑
"""

import re


def find_handicap_for_arbitrage(bet_data, detail_full_odds, success_platform_handicap, success_platform_handicap_param):
    """
    为 PIN888 套利补单场景匹配盘口

    匹配逻辑:
    1. 确定反向盘口类型 (Over → Under, Handicap1 → Handicap2)
    2. 确定数值区间 (Over X → Under Y where Y >= X)
    3. 在符合条件的盘口中选择赔率最高的

    Args:
        bet_data: 原始下注数据
        detail_full_odds: PIN888 的盘口详情数据 (window.___detailFullOdds)
        success_platform_handicap: 对手成功盘口类型,如 "Total Over(%s)"
        success_platform_handicap_param: 对手成功参数,如 "5.5"

    Returns:
        {
            'odds': 2.1,
            'selection': {...},
            'market': {...},
            'matched_value': 5.5,
            'gap': 0.5
        }
        或 None (未找到符合条件的盘口)
    """

    print(f"📊 [PIN888 套利匹配] 接收到对手盘口信息:")
    print(f"  对手盘口: {success_platform_handicap}")
    print(f"  对手参数: {success_platform_handicap_param}")

    # 步骤1: 判断盘口类型
    success_platform_handicap_lower = success_platform_handicap.lower()

    is_total = "total" in success_platform_handicap_lower
    is_handicap = "handicap" in success_platform_handicap_lower

    if not is_total and not is_handicap:
        print(f"⚠️ [PIN888 套利匹配] 当前只支持 Total 类和 Handicap 类套利")
        return None

    # 步骤2: 转换数值为 float
    try:
        success_value = float(success_platform_handicap_param)
    except (ValueError, TypeError) as e:
        print(f"❌ [PIN888 套利匹配] 无法解析数值: {success_platform_handicap_param}, 错误: {e}")
        return None

    # 步骤3: 确定反向盘口类型和区间条件
    if is_total:
        if "over" in success_platform_handicap_lower:
            # 对手: Over X → 我方: Under Y (Y >= X)
            target_direction = "under"
            condition = lambda y: y >= success_value
            description = f"寻找 Under Y (Y >= {success_value})"

            print(f"📊 [PIN888 套利匹配] 对手盘口: Over {success_value}")
            print(f"📊 [PIN888 套利匹配] 匹配条件: {description}")

        elif "under" in success_platform_handicap_lower:
            # 对手: Under X → 我方: Over Y (Y <= X)
            target_direction = "over"
            condition = lambda y: y <= success_value
            description = f"寻找 Over Y (Y <= {success_value})"

            print(f"📊 [PIN888 套利匹配] 对手盘口: Under {success_value}")
            print(f"📊 [PIN888 套利匹配] 匹配条件: {description}")
        else:
            print(f"❌ [PIN888 套利匹配] 无法识别的 Total 类型: {success_platform_handicap}")
            return None

    elif is_handicap:
        if "handicap1" in success_platform_handicap_lower:
            target_direction = "handicap2"
            if success_value < 0:
                condition = lambda y: success_value <= y <= 0
                description = f"寻找 Handicap2 Y ({success_value} <= Y <= 0)"
            else:
                condition = lambda y: -success_value <= y <= 0
                description = f"寻找 Handicap2 Y ({-success_value} <= Y <= 0)"

            print(f"📊 [PIN888 套利匹配] 对手盘口: Handicap1({success_value})")
            print(f"📊 [PIN888 套利匹配] 匹配条件: {description}")

        elif "handicap2" in success_platform_handicap_lower:
            target_direction = "handicap1"
            if success_value < 0:
                condition = lambda y: success_value <= y <= 0
                description = f"寻找 Handicap1 Y ({success_value} <= Y <= 0)"
            else:
                condition = lambda y: -success_value <= y <= 0
                description = f"寻找 Handicap1 Y ({-success_value} <= Y <= 0)"

            print(f"📊 [PIN888 套利匹配] 对手盘口: Handicap2({success_value})")
            print(f"📊 [PIN888 套利匹配] 匹配条件: {description}")
        else:
            print(f"❌ [PIN888 套利匹配] 无法识别的 Handicap 类型: {success_platform_handicap}")
            return None

    # 步骤4: 从 detail_full_odds 中筛选符合条件的盘口
    candidates = []

    normal_markets = detail_full_odds.get('normal', [])
    if not normal_markets:
        print(f"❌ [PIN888 套利匹配] detail_full_odds 中没有 normal 数据")
        return None

    print(f"\n📊 [PIN888 套利匹配] 开始在 {len(normal_markets)} 个盘口中查找...")

    for market in normal_markets:
        market_name = market.get('name', '').lower()

        # 跳过不相关的盘口类型
        if is_total and 'total' not in market_name:
            continue
        if is_handicap and 'handicap' not in market_name:
            continue

        selections = market.get('selections', [])

        for selection in selections:
            selection_name = selection.get('name', '')
            selection_name_lower = selection_name.lower()

            # 检查方向是否匹配
            if target_direction not in selection_name_lower:
                continue

            # 提取数值
            try:
                # 格式: "Over 5.5" 或 "Under 2.75" 或 "Handicap2(-1.5)"
                if is_total:
                    # Total 类: "Over 5.5" → ["Over", "5.5"]
                    parts = selection_name.split()
                    if len(parts) >= 2:
                        selection_value = float(parts[1])
                    else:
                        continue
                elif is_handicap:
                    # Handicap 类: "Handicap2(-1.5)" → 提取括号中的值
                    match = re.search(r'\(([-+]?\d+\.?\d*)\)', selection_name)
                    if match:
                        selection_value = float(match.group(1))
                    else:
                        continue
            except (ValueError, IndexError):
                continue

            # 检查是否符合区间条件
            if not condition(selection_value):
                print(f"      ✗ 跳过: {selection_name} (数值: {selection_value}) - 不符合条件")
                continue
            else:
                print(f"      ✓ 符合: {selection_name} (数值: {selection_value}, 赔率: {selection.get('odds')})")

            # 符合条件,加入候选列表
            candidates.append({
                'odds': selection.get('odds'),
                'selection': selection,
                'selection_value': selection_value,
                'market': market,
                'gap': abs(selection_value - success_value)
            })

    # 步骤5: 选择赔率最高的候选项
    if not candidates:
        print(f"❌ [PIN888 套利匹配] 未找到符合条件的盘口")
        return None

    # 按赔率排序,选择最高的
    best = max(candidates, key=lambda x: x['odds'])

    print(f"\n✅ [PIN888 套利匹配] 找到 {len(candidates)} 个候选项,选择赔率最高的:")
    print(f"  选项: {best['selection'].get('name')}")
    print(f"  赔率: {best['odds']}")
    print(f"  数值: {best['selection_value']}")
    print(f"  区间: {best['gap']}")

    # 返回格式与 find_handicap() 相同
    return {
        'odds': best['odds'],
        'selection': best['selection'],
        'market': best['market'],
        'matched_value': best['selection_value'],
        'gap': best['gap']
    }
