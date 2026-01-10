# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'c:\Users\Administrator\Desktop\PyPJT\发给亨亨\重要\BetInAsian')

from automationPlaywright.betinasian.MappingBetburgerToBetinisian import build_bet_type_from_spider

print("=" * 60)
print("Quick Test - New Soccer Mappings")
print("=" * 60)

tests = [
    ("1", None, "for,h", "Money Line - Home"),
    ("2", None, "for,a", "Money Line - Away"),
    ("8", None, "for,score,both", "Both Teams Score - Yes"),
    ("9", None, "for,score,both,no", "Both Teams Score - No"),
    ("14", None, "for,dc,h,d", "Double Chance - 1X"),
    ("15", None, "for,dc,a,d", "Double Chance - X2"),
    ("16", None, "for,dc,h,a", "Double Chance - 12"),
    ("25", None, "for,odd", "Odd/Even - Odd"),
    ("26", None, "for,even", "Odd/Even - Even"),
]

passed = 0
failed = 0

for market_id, handicap, expected, name in tests:
    result = build_bet_type_from_spider("soccer", market_id, handicap)
    status = "✓" if result == expected else "✗"
    if result == expected:
        passed += 1
    else:
        failed += 1
    print(f"{status} [{market_id}] {name}")
    print(f"  Expected: {expected}")
    print(f"  Got:      {result}")
    print()

print("=" * 60)
print(f"Result: {passed} passed, {failed} failed")
print("=" * 60)
