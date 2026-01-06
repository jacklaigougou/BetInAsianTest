#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify all imports work correctly
"""

print("Testing MappingBetburgerToBetinisian imports...\n")

# Test 1: Unified interface
print("=" * 60)
print("Test 1: Unified Interface")
print("=" * 60)

from MappingBetburgerToBetinisian import parse_spider_market

# Basketball
basket_mapping = parse_spider_market("basket", "17", -5.5)
print(f"Basketball AH(-5.5): {basket_mapping}")

# Soccer
soccer_mapping = parse_spider_market("soccer", "11")
print(f"Soccer 1X2: {soccer_mapping}")

print("✅ Unified interface works!\n")

# Test 2: Direct module access
print("=" * 60)
print("Test 2: Direct Module Access")
print("=" * 60)

from MappingBetburgerToBetinisian import basket, soccer

basket_direct = basket.parse_spider_market("19", 170)
print(f"Basketball O/U(170): {basket_direct}")

soccer_direct = soccer.parse_spider_market("17", -0.5)
print(f"Soccer AH(-0.5): {soccer_direct}")

print("✅ Direct module access works!\n")

# Test 3: Object-oriented interface
print("=" * 60)
print("Test 3: Object-Oriented Interface")
print("=" * 60)

from MappingBetburgerToBetinisian import MarketMapper

basket_mapper = MarketMapper("basket")
mapping1 = basket_mapper.parse("17", -5.5)
mapping2 = basket_mapper.parse("19", 170)

print(f"Basket Mapper Test 1: {mapping1}")
print(f"Basket Mapper Test 2: {mapping2}")

print("✅ Object-oriented interface works!\n")

# Test 4: Utility functions
print("=" * 60)
print("Test 4: Utility Functions")
print("=" * 60)

from MappingBetburgerToBetinisian import (
    get_betinasian_market_type,
    get_betinasian_side,
    needs_line_id,
    get_supported_sports,
    is_sport_supported,
    validate_mapping
)

print(f"Supported sports: {get_supported_sports()}")
print(f"Is 'basket' supported? {is_sport_supported('basket')}")
print(f"Is 'tennis' supported? {is_sport_supported('tennis')}")

market_type = get_betinasian_market_type("basket", "17")
side = get_betinasian_side("basket", "17")
needs_hcp = needs_line_id("basket", "17")

print(f"Market type for basket/17: {market_type}")
print(f"Side for basket/17: {side}")
print(f"Needs line_id for basket/17? {needs_hcp}")

# Validation
valid, mapping, error = validate_mapping("basket", "17", -5.5)
print(f"Validation result: valid={valid}, error={error}")

print("✅ Utility functions work!\n")

# Test 5: Line ID conversion
print("=" * 60)
print("Test 5: Line ID Conversion")
print("=" * 60)

test_cases = [
    ("basket", "17", -5.5, -22),    # Basketball AH
    ("basket", "19", 170, 680),     # Basketball O/U
    ("soccer", "17", -0.5, -2),     # Soccer AH
    ("soccer", "19", 2.5, 10),      # Soccer O/U
]

all_correct = True
for sport, market_id, handicap, expected_line_id in test_cases:
    mapping = parse_spider_market(sport, market_id, handicap)
    actual_line_id = mapping.get('line_id')

    status = "✅" if actual_line_id == expected_line_id else "❌"
    print(f"{status} {sport}/{market_id}({handicap}): "
          f"expected {expected_line_id}, got {actual_line_id}")

    if actual_line_id != expected_line_id:
        all_correct = False

if all_correct:
    print("✅ All line_id conversions correct!\n")
else:
    print("❌ Some line_id conversions failed!\n")

# Test 6: Sport aliases
print("=" * 60)
print("Test 6: Sport Aliases")
print("=" * 60)

aliases_test = [
    ("basket", "17", -5.5),
    ("basketball", "17", -5.5),
    ("soccer", "11", None),
    ("fb", "11", None),
    ("football", "11", None),
]

for sport, market_id, handicap in aliases_test:
    mapping = parse_spider_market(sport, market_id, handicap)
    if mapping:
        print(f"✅ {sport}: {mapping['betinasian_market']}")
    else:
        print(f"❌ {sport}: Failed")

print()
print("=" * 60)
print("All Tests Completed!")
print("=" * 60)
