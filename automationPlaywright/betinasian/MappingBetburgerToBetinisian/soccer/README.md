# Soccer (Football) Market Mapping Guide

## Overview

Complete mapping between Spider soccer markets and BetInAsian soccer markets.

## Soccer Market Mapping Table

| Spider ID | Spider Market | BetInAsian Market | Side | Line ID | Example |
|-----------|---------------|-------------------|------|---------|---------|
| **1X2 (Money Line)** |
| 1 | Team1 Win | ml | h | - | Home Win @ 2.50 |
| 2 | Team2 Win | ml | a | - | Away Win @ 3.20 |
| 11 | 1 | ml | h | - | Same as ID 1 |
| 12 | X | ml | x | - | Draw @ 3.00 |
| 13 | 2 | ml | a | - | Same as ID 2 |
| **Asian Handicap** |
| 17 | Asian Handicap1(%s) | ah | h | ×4 | -0.5 → -2 |
| 18 | Asian Handicap2(%s) | ah | a | ×4 | +0.5 → 2 |
| **Over/Under (Total Goals)** |
| 19 | Total Over(%s) | ahou | o | ×4 | 2.5 → 10 |
| 20 | Total Under(%s) | ahou | u | ×4 | 2.5 → 10 |
| **Draw No Bet** |
| 3 | Asian Handicap1(0.0) | dnb | h | - | Draw No Bet Home |
| 4 | Asian Handicap2(0.0) | dnb | a | - | Draw No Bet Away |
| **Double Chance** |
| 14 | 1X | dc | 1x | - | Home or Draw |
| 15 | X2 | dc | x2 | - | Draw or Away |
| 16 | 12 | dc | 12 | - | Home or Away |
| **Both Teams to Score** |
| 8 | Both to score | btts | y | - | Both Teams Score - Yes |
| 9 | One scoreless | btts | n | - | Both Teams Score - No |
| **Odd/Even** |
| 25 | Odd | oe | o | - | Total Goals Odd |
| 26 | Even | oe | e | - | Total Goals Even |
| **European Handicap** |
| 5 | European Handicap1(%s) | eh | h | ×4 | -1 → -4 |
| 6 | European HandicapX(%s) | eh | x | ×4 | 0 → 0 |
| 7 | European Handicap2(%s) | eh | a | ×4 | +1 → 4 |
| **Team Totals** |
| 21 | Total Over(%s) Team1 | t1ahou | o | ×4 | 1.5 → 6 |
| 22 | Total Under(%s) Team1 | t1ahou | u | ×4 | 1.5 → 6 |
| 23 | Total Over(%s) Team2 | t2ahou | o | ×4 | 1.5 → 6 |
| 24 | Total Under(%s) Team2 | t2ahou | u | ×4 | 1.5 → 6 |
| **Corners** |
| 49 | Asian Handicap1(%s) Corners | corners_ah | h | ×4 | -2.5 → -10 |
| 50 | Asian Handicap2(%s) Corners | corners_ah | a | ×4 | +2.5 → 10 |
| 51 | Total Over(%s) Corners | corners_ou | o | ×4 | 10.5 → 42 |
| 52 | Total Under(%s) Corners | corners_ou | u | ×4 | 10.5 → 42 |
| **Special** |
| 165 | No goal | ng | y | - | No Goal - Yes |

## Line ID Conversion Rules

Soccer uses **0.25 increments**, multiply by **4**:

| Handicap | Calculation | Line ID |
|----------|-------------|---------|
| -1.0 | -1.0 × 4 | -4 |
| -0.75 | -0.75 × 4 | -3 |
| -0.5 | -0.5 × 4 | -2 |
| -0.25 | -0.25 × 4 | -1 |
| 0.0 | 0.0 × 4 | 0 |
| +0.25 | +0.25 × 4 | 1 |
| +0.5 | +0.5 × 4 | 2 |
| 2.5 (O/U) | 2.5 × 4 | 10 |
| 3.0 (O/U) | 3.0 × 4 | 12 |

## Usage Examples

### Example 1: Asian Handicap

```python
from MappingBetburgerToBetinisian.soccer import parse_spider_market

# Spider data: Asian Handicap1(-0.5)
spider_data = {
    "market_id": "17",
    "handicap": -0.5,
    "odds": 1.95
}

# Parse mapping
mapping = parse_spider_market("17", -0.5)
print(mapping)
# {
#     "betinasian_market": "ah",
#     "betinasian_side": "h",
#     "line_id": -2,
#     "description": "Asian Handicap - Home"
# }

# Query BetInAsian
ah_line = await page.evaluate(f'''
    window.queryData.parseOfferEventLine(
        "{event_key}",
        "ah",
        -2
    )
''')

# Get odds
betinasian_odds = ah_line['odds']['h']  # 1.90
```

### Example 2: Over/Under

```python
# Spider data: Total Over(2.5)
mapping = parse_spider_market("19", 2.5)
# {
#     "betinasian_market": "ahou",
#     "betinasian_side": "o",
#     "line_id": 10,
#     "description": "Over/Under - Over"
# }
```

### Example 3: 1X2 (No Line ID)

```python
# Spider data: Team1 Win (1X2)
mapping = parse_spider_market("11")
# {
#     "betinasian_market": "ml",
#     "betinasian_side": "h",
#     "description": "1X2 - Home Win"
# }

# Query BetInAsian (no line_id needed)
ml_data = await page.evaluate(f'''
    window.queryData.parseOfferEventLine(
        "{event_key}",
        "ml",
        0
    )
''')

betinasian_odds = ml_data['odds']['h']
```

### Example 4: Both Teams to Score

```python
# Spider data: Both to score
mapping = parse_spider_market("8")
# {
#     "betinasian_market": "btts",
#     "betinasian_side": "y",
#     "description": "Both Teams to Score - Yes"
# }
```

### Example 5: Corners

```python
# Spider data: Corners Asian Handicap1(-2.5)
mapping = parse_spider_market("49", -2.5)
# {
#     "betinasian_market": "corners_ah",
#     "betinasian_side": "h",
#     "line_id": -10,
#     "description": "Corners Asian Handicap - Home"
# }
```

## Integrated Usage in GetOdd.py

```python
from MappingBetburgerToBetinisian.soccer import parse_spider_market

async def GetOdd(self, dispatch_message, **kwargs):
    # Get event_key
    match_result = await get_event_key_by_team_name(self, dispatch_message, **kwargs)
    event_key = match_result.get('event_key')

    # Parse spider market
    spider_market_id = dispatch_message.get('market_id')
    handicap_value = dispatch_message.get('handicap')

    mapping = parse_spider_market(spider_market_id, handicap_value)

    if not mapping:
        return {'success': False, 'message': 'Cannot map market'}

    # Subscribe watch_event
    await page.evaluate(f'''
        window.__watchManager.watch("{event_key}", "fb", {competition_id})
    ''')
    await asyncio.sleep(2)

    # Query corresponding line
    if 'line_id' in mapping:
        # Has line_id (Asian Handicap, Over/Under, etc.)
        line_data = await page.evaluate(f'''
            window.queryData.parseOfferEventLine(
                "{event_key}",
                "{mapping['betinasian_market']}",
                {mapping['line_id']}
            )
        ''')
    else:
        # No line_id (1X2, BTTS, etc.)
        # Use line_id=0 or query all lines
        line_data = await page.evaluate(f'''
            window.queryData.parseOfferEventLine(
                "{event_key}",
                "{mapping['betinasian_market']}",
                0
            )
        ''')

    if not line_data:
        return {'success': False, 'message': 'Line not found'}

    # Extract odds
    betinasian_odds = line_data['odds'][mapping['betinasian_side']]

    return {
        'success': True,
        'odds': betinasian_odds,
        'market_info': mapping
    }
```

## Market Type Priority

When multiple spider IDs map to the same BetInAsian market:

1. **ID 1, 2** vs **ID 11, 13**: Both map to `ml`, use either (they're identical)
2. **Asian Handicap vs Draw No Bet**:
   - AH(0.0) = Draw No Bet
   - Both are valid, but `dnb` is more explicit

## Common Pitfalls

1. **1X2 Draw**: Use `side="x"` not `side="d"`
2. **Double Chance**: Use `side="1x"`, `side="x2"`, `side="12"` (lowercase)
3. **Odd/Even**: `side="o"` for Odd, `side="e"` for Even
4. **Line ID**: Always multiply by 4 for soccer
5. **Corners**: Different market types (`corners_ah`, `corners_ou`)

## BetInAsian Market Availability

Not all BetInAsian events have all markets:
- **Always Available**: ml (1X2), ah, ahou
- **Often Available**: dnb, dc, btts, oe
- **Sometimes Available**: eh, t1ahou, t2ahou, corners_*
- **Rarely Available**: ng

Always check if the market exists before querying.
