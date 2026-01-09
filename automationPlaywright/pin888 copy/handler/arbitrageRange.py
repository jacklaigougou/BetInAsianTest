# -*- coding: utf-8 -*-
"""
PIN888 平台套利补单区间计算
根据成功平台的盘口参数,计算 PIN888 可补单的区间条件
"""
from typing import Callable, Optional


def calculate_arbitrage_range(
    success_platform_handicap: str,
    success_platform_handicap_param: str
) -> Optional[Callable]:
    """
    根据成功平台的盘口参数,计算 PIN888 补单的区间条件函数

    参数:
        success_platform_handicap: 成功平台盘口类型 (如 "Total Over(%s)", "Asian Handicap1(%s)")
        success_platform_handicap_param: 成功平台盘口参数 (如 "2.5", "-1.5")

    返回:
        callable: lambda 函数,用于判断某个值是否在补单区间内
                  例如: lambda y: y >= 2.5 (对手方 Over 2.5,我方需要 Under Y, Y >= 2.5)
        None: 不支持的盘口类型

    示例:
        # 成功方 Over 2.5 → 我方找 Under Y (Y >= 2.5)
        condition = calculate_arbitrage_range("Total Over(%s)", "2.5")
        condition(2.5)  # True
        condition(2.75) # True
        condition(2.25) # False

        # 成功方 Handicap1(-1.5) → 我方找 Handicap2 Y (-1.5 <= Y <= 0)
        condition = calculate_arbitrage_range("Asian Handicap1(%s)", "-1.5")
        condition(-1.0) # True
        condition(-0.5) # True
        condition(0.5)  # False
    """
    print(f"📊 [PIN888 套利区间] 计算补单区间:")
    print(f"  成功方盘口: {success_platform_handicap}")
    print(f"  成功方参数: {success_platform_handicap_param}")

    # 步骤1: 判断盘口类型
    success_platform_handicap_lower = success_platform_handicap.lower()

    is_total = "total" in success_platform_handicap_lower
    is_handicap = "handicap" in success_platform_handicap_lower

    if not is_total and not is_handicap:
        print(f"⚠️ [PIN888 套利区间] 当前只支持 Total 类和 Handicap 类套利")
        return None

    # 步骤2: 转换数值为 float
    try:
        success_value = float(success_platform_handicap_param)
    except (ValueError, TypeError) as e:
        print(f"❌ [PIN888 套利区间] 无法解析数值: {success_platform_handicap_param}, 错误: {e}")
        return None

    # 步骤3: 确定反向盘口类型和区间条件
    if is_total:
        if "over" in success_platform_handicap_lower:
            # 对手: Over X → 我方: Under Y (Y >= X)
            condition = lambda y: y >= success_value
            description = f"Under Y (Y >= {success_value})"

            print(f"📊 [PIN888 套利区间] 成功方: Over {success_value}")
            print(f"📊 [PIN888 套利区间] 补单区间: {description}")
            return condition

        elif "under" in success_platform_handicap_lower:
            # 对手: Under X → 我方: Over Y (Y <= X)
            condition = lambda y: y <= success_value
            description = f"Over Y (Y <= {success_value})"

            print(f"📊 [PIN888 套利区间] 成功方: Under {success_value}")
            print(f"📊 [PIN888 套利区间] 补单区间: {description}")
            return condition

        else:
            print(f"❌ [PIN888 套利区间] 无法识别的 Total 类型: {success_platform_handicap}")
            return None

    elif is_handicap:
        if "handicap1" in success_platform_handicap_lower:
            # 对手: Handicap1(X)
            if success_value < 0:
               
                condition = lambda y: y <= -success_value
                description = f"Handicap2 Y <= {-success_value}"
            else:
                
                condition = lambda y: y >= -success_value
                description = f"Handicap2 Y >= {-success_value}"

            print(f"📊 [PIN888 套利区间] 成功方: Handicap1({success_value})")
            print(f"📊 [PIN888 套利区间] 补单区间: {description}")
            return condition

        elif "handicap2" in success_platform_handicap_lower:
            # 对手: Handicap2(X)
            if success_value < 0:
                # X < 0 → 我方: Handicap1 Y (Y >= X)
                condition = lambda y: y <= -success_value
                description = f"Handicap1 Y <= {-success_value}"
            else:
                # X > 0 → 我方: Handicap1 Y (Y <= X)
                condition = lambda y: y >= -success_value
                description = f"Handicap1 Y >= {-success_value}"

            print(f"📊 [PIN888 套利区间] 成功方: Handicap2({success_value})")
            print(f"📊 [PIN888 套利区间] 补单区间: {description}")
            return condition

        else:
            print(f"❌ [PIN888 套利区间] 无法识别的 Handicap 类型: {success_platform_handicap}")
            return None

    return None
