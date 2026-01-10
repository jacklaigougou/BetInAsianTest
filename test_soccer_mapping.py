# -*- coding: utf-8 -*-
"""
测试足球（Soccer）映射规则修改
"""

import sys
sys.path.insert(0, r'c:\Users\Administrator\Desktop\PyPJT\发给亨亨\重要\BetInAsian')

from automationPlaywright.betinasian.MappingBetburgerToBetinisian import build_bet_type_from_spider

def test_soccer_mappings():
    """测试所有修改的足球映射规则"""

    print("=" * 80)
    print("测试足球（Soccer）映射规则")
    print("=" * 80)

    test_cases = [
        # 1X2 市场 - 简化格式
        {
            "name": "1X2 - Home Win",
            "sport": "soccer",
            "market_id": "11",
            "handicap": None,
            "expected": "for,h"
        },
        {
            "name": "1X2 - Draw",
            "sport": "soccer",
            "market_id": "12",
            "handicap": None,
            "expected": "for,d"
        },
        {
            "name": "1X2 - Away Win",
            "sport": "soccer",
            "market_id": "13",
            "handicap": None,
            "expected": "for,a"
        },

        # Money Line (与 11/13 保持一致)
        {
            "name": "Money Line - Home Win (ID: 1)",
            "sport": "soccer",
            "market_id": "1",
            "handicap": None,
            "expected": "for,h"
        },
        {
            "name": "Money Line - Away Win (ID: 2)",
            "sport": "soccer",
            "market_id": "2",
            "handicap": None,
            "expected": "for,a"
        },

        # Both Teams to Score
        {
            "name": "Both Teams to Score - Yes",
            "sport": "soccer",
            "market_id": "8",
            "handicap": None,
            "expected": "for,score,both"
        },
        {
            "name": "Both Teams to Score - No",
            "sport": "soccer",
            "market_id": "9",
            "handicap": None,
            "expected": "for,score,both,no"
        },

        # Odd/Even
        {
            "name": "Odd/Even - Odd",
            "sport": "soccer",
            "market_id": "25",
            "handicap": None,
            "expected": "for,odd"
        },
        {
            "name": "Odd/Even - Even",
            "sport": "soccer",
            "market_id": "26",
            "handicap": None,
            "expected": "for,even"
        },

        # Double Chance
        {
            "name": "Double Chance - 1X (Home or Draw)",
            "sport": "soccer",
            "market_id": "14",
            "handicap": None,
            "expected": "for,dc,h,d"
        },
        {
            "name": "Double Chance - X2 (Draw or Away)",
            "sport": "soccer",
            "market_id": "15",
            "handicap": None,
            "expected": "for,dc,a,d"
        },
        {
            "name": "Double Chance - 12 (Home or Away)",
            "sport": "soccer",
            "market_id": "16",
            "handicap": None,
            "expected": "for,dc,h,a"
        },

        # Asian Handicap - IR 格式
        {
            "name": "Asian Handicap - Home (-0.25)",
            "sport": "soccer",
            "market_id": "17",
            "handicap": -0.25,
            "expected": "for,ir,0,0,ah,h,-1"
        },
        {
            "name": "Asian Handicap - Home (-0.5)",
            "sport": "soccer",
            "market_id": "17",
            "handicap": -0.5,
            "expected": "for,ir,0,0,ah,h,-2"
        },
        {
            "name": "Asian Handicap - Away (0.5)",
            "sport": "soccer",
            "market_id": "18",
            "handicap": 0.5,
            "expected": "for,ir,0,0,ah,a,2"
        },
        {
            "name": "Asian Handicap - Away (1.0)",
            "sport": "soccer",
            "market_id": "18",
            "handicap": 1.0,
            "expected": "for,ir,0,0,ah,a,4"
        },

        # Over/Under - IR 格式（无 side）
        {
            "name": "Over/Under - Over (2.5)",
            "sport": "soccer",
            "market_id": "19",
            "handicap": 2.5,
            "expected": "for,ir,0,0,ahover,10"
        },
        {
            "name": "Over/Under - Over (3.0)",
            "sport": "soccer",
            "market_id": "19",
            "handicap": 3.0,
            "expected": "for,ir,0,0,ahover,12"
        },
        {
            "name": "Over/Under - Under (2.5)",
            "sport": "soccer",
            "market_id": "20",
            "handicap": 2.5,
            "expected": "for,ir,0,0,ahunder,10"
        },
        {
            "name": "Over/Under - Under (1.5)",
            "sport": "soccer",
            "market_id": "20",
            "handicap": 1.5,
            "expected": "for,ir,0,0,ahunder,6"
        },
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\n[测试 {i}/{len(test_cases)}] {test['name']}")
        print(f"  输入: sport={test['sport']}, market_id={test['market_id']}, handicap={test['handicap']}")

        result = build_bet_type_from_spider(
            sport_type=test['sport'],
            spider_market_id=test['market_id'],
            handicap_value=test['handicap']
        )

        print(f"  期望输出: {test['expected']}")
        print(f"  实际输出: {result}")

        if result == test['expected']:
            print(f"  ✅ 通过")
            passed += 1
        else:
            print(f"  ❌ 失败")
            failed += 1

    print("\n" + "=" * 80)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 80)

    return failed == 0


def test_basketball_compatibility():
    """测试篮球映射规则是否保持兼容"""

    print("\n" + "=" * 80)
    print("测试篮球（Basketball）映射规则兼容性")
    print("=" * 80)

    test_cases = [
        {
            "name": "Basketball Money Line - Home",
            "sport": "basket",
            "market_id": "1",
            "handicap": None,
            "expected": "for,ml,h"
        },
        {
            "name": "Basketball Asian Handicap - Home (-5.5)",
            "sport": "basket",
            "market_id": "17",
            "handicap": -5.5,
            "expected": "for,ah,h,-22"
        },
        {
            "name": "Basketball Over/Under - Over (170)",
            "sport": "basket",
            "market_id": "19",
            "handicap": 170,
            "expected": "for,ahou,o,680"
        },
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\n[测试 {i}/{len(test_cases)}] {test['name']}")
        print(f"  输入: sport={test['sport']}, market_id={test['market_id']}, handicap={test['handicap']}")

        result = build_bet_type_from_spider(
            sport_type=test['sport'],
            spider_market_id=test['market_id'],
            handicap_value=test['handicap']
        )

        print(f"  期望输出: {test['expected']}")
        print(f"  实际输出: {result}")

        if result == test['expected']:
            print(f"  ✅ 通过")
            passed += 1
        else:
            print(f"  ❌ 失败")
            failed += 1

    print("\n" + "=" * 80)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    soccer_ok = test_soccer_mappings()
    basketball_ok = test_basketball_compatibility()

    print("\n" + "=" * 80)
    print("总体测试结果")
    print("=" * 80)
    print(f"足球映射: {'✅ 通过' if soccer_ok else '❌ 失败'}")
    print(f"篮球兼容性: {'✅ 通过' if basketball_ok else '❌ 失败'}")
    print("=" * 80)

    sys.exit(0 if (soccer_ok and basketball_ok) else 1)
