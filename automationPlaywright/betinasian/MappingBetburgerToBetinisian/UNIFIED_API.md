# Unified Market Mapping API Guide

## Overview

`mapping.py` provides a unified interface for mapping spider markets to BetInAsian markets across different sports.

## Key Features

✅ **Automatic Sport Routing** - Automatically route to the correct sport module
✅ **Consistent API** - Same function signatures for all sports
✅ **Type Safety** - Full type hints for better IDE support
✅ **Validation** - Built-in validation with error messages
✅ **OOP Interface** - Object-oriented alternative available

## Quick Start

### Basic Usage (Function-based)

```python
from MappingBetburgerToBetinisian import parse_spider_market

# Basketball: Asian Handicap1(-5.5)
mapping = parse_spider_market("basket", "17", -5.5)
print(mapping)
# {
#     "betinasian_market": "ah",
#     "betinasian_side": "h",
#     "line_id": -22,
#     "description": "Asian Handicap - Home"
# }

# Soccer: 1X2 Home Win
mapping = parse_spider_market("soccer", "11")
print(mapping)
# {
#     "betinasian_market": "ml",
#     "betinasian_side": "h",
#     "description": "1X2 - Home Win"
# }

# Soccer: Asian Handicap1(-0.5)
mapping = parse_spider_market("fb", "17", -0.5)
print(mapping)
# {
#     "betinasian_market": "ah",
#     "betinasian_side": "h",
#     "line_id": -2,
#     "description": "Asian Handicap - Home"
# }
```

### Object-Oriented Usage

```python
from MappingBetburgerToBetinisian import MarketMapper

# Create mapper for basketball
basket_mapper = MarketMapper("basket")

# Parse markets
mapping1 = basket_mapper.parse("17", -5.5)
mapping2 = basket_mapper.parse("19", 170)

# Quick queries
market_type = basket_mapper.get_market_type("17")  # "ah"
side = basket_mapper.get_side("17")                # "h"
needs_line = basket_mapper.needs_line("17")        # True

# Get readable names
side_name = basket_mapper.get_side_name("h")       # "Home"
market_name = basket_mapper.get_market_name("ah")  # "Asian Handicap"
```

## API Reference

### Core Functions

#### `parse_spider_market(sport_type, spider_market_id, handicap_value=None)`

Parse spider market and return BetInAsian mapping.

**Parameters:**
- `sport_type` (str): Sport type identifier
  - Basketball: `"basket"`, `"basketball"`
  - Soccer: `"soccer"`, `"fb"`, `"football"`
- `spider_market_id` (str): Spider market ID (e.g., `"17"`, `"19"`)
- `handicap_value` (float, optional): Handicap value (e.g., `-5.5`, `2.5`)

**Returns:**
- `dict` or `None`: Mapping dictionary containing:
  - `betinasian_market`: BetInAsian market type
  - `betinasian_side`: Bet side code
  - `line_id`: Converted line ID (if applicable)
  - `description`: Human-readable description

**Example:**
```python
mapping = parse_spider_market("basket", "17", -5.5)
```

---

#### `get_betinasian_market_type(sport_type, spider_market_id)`

Quick get BetInAsian market type.

**Returns:** `str` or `None` (e.g., `"ah"`, `"ahou"`, `"ml"`)

**Example:**
```python
market = get_betinasian_market_type("soccer", "17")  # "ah"
```

---

#### `get_betinasian_side(sport_type, spider_market_id)`

Quick get BetInAsian bet side.

**Returns:** `str` or `None` (e.g., `"h"`, `"a"`, `"o"`, `"u"`, `"x"`)

**Example:**
```python
side = get_betinasian_side("soccer", "12")  # "x" (Draw)
```

---

#### `needs_line_id(sport_type, spider_market_id)`

Check if market requires handicap_value/line_id.

**Returns:** `bool`

**Example:**
```python
needs_line_id("basket", "17")  # True (Asian Handicap needs line)
needs_line_id("soccer", "11")  # False (1X2 doesn't need line)
```

---

#### `validate_mapping(sport_type, spider_market_id, handicap_value=None)`

Validate mapping with detailed error messages.

**Returns:** `tuple[bool, dict|None, str|None]`
- `is_valid`: Whether mapping is valid
- `mapping`: Mapping dict (if valid)
- `error_message`: Error message (if invalid)

**Example:**
```python
valid, mapping, error = validate_mapping("basket", "17", -5.5)

if valid:
    print(f"Mapping: {mapping}")
else:
    print(f"Error: {error}")
```

### Utility Functions

#### `get_supported_sports()`

Get list of supported sport types.

**Returns:** `list` of sport type identifiers

**Example:**
```python
sports = get_supported_sports()
# ['basket', 'basketball', 'fb', 'soccer', 'football']
```

---

#### `is_sport_supported(sport_type)`

Check if sport type is supported.

**Example:**
```python
is_sport_supported("basket")  # True
is_sport_supported("tennis")  # False
```

---

#### `get_side_name(sport_type, side_code)`

Get readable name for bet side.

**Example:**
```python
get_side_name("basket", "h")   # "Home"
get_side_name("soccer", "x")   # "Draw"
```

---

#### `get_market_name(sport_type, market_code)`

Get readable name for market type.

**Example:**
```python
get_market_name("basket", "ah")      # "Asian Handicap"
get_market_name("soccer", "ml")      # "Money Line (1X2)"
```

## Sport Type Aliases

Multiple aliases are supported for convenience:

| Sport | Supported Aliases |
|-------|-------------------|
| Basketball | `"basket"`, `"basketball"` |
| Soccer | `"soccer"`, `"fb"`, `"football"` |

## Complete Integration Example

### In GetOdd.py

```python
from MappingBetburgerToBetinisian import parse_spider_market, validate_mapping

async def GetOdd(self, dispatch_message, **kwargs):
    # Extract spider data
    sport_type = dispatch_message.get('spider_sport_type')  # "basket" or "fb"
    spider_market_id = dispatch_message.get('market_id')    # "17"
    handicap_value = dispatch_message.get('handicap')       # -5.5

    # Step 1: Validate mapping
    valid, mapping, error = validate_mapping(
        sport_type,
        spider_market_id,
        handicap_value
    )

    if not valid:
        return {
            'success': False,
            'message': f'Mapping error: {error}'
        }

    # Step 2: Get event_key
    match_result = await get_event_key_by_team_name(self, dispatch_message, **kwargs)
    if not match_result.get('success'):
        return match_result

    event = match_result.get('event')
    event_key = match_result.get('event_key')
    competition_id = event.get('competition_id')

    # Step 3: Subscribe watch_event
    await self.page.evaluate(f'''
        window.__watchManager.watch(
            "{event_key}",
            "{sport_type}",
            {competition_id}
        )
    ''')
    await asyncio.sleep(2)

    # Step 4: Query BetInAsian data
    if 'line_id' in mapping:
        # Market with line_id (Asian Handicap, Over/Under, etc.)
        line_data = await self.page.evaluate(f'''
            window.queryData.parseOfferEventLine(
                "{event_key}",
                "{mapping['betinasian_market']}",
                {mapping['line_id']}
            )
        ''')
    else:
        # Market without line_id (1X2, BTTS, etc.)
        # Query with line_id=0 or get first available line
        all_lines = await self.page.evaluate(f'''
            window.queryData.parseAllOfferEventLines(
                "{event_key}",
                "{mapping['betinasian_market']}"
            )
        ''')
        line_data = all_lines[0] if all_lines else None

    if not line_data:
        return {
            'success': False,
            'message': f'BetInAsian line not found: {mapping["description"]}'
        }

    # Step 5: Extract odds
    betinasian_odds = line_data['odds'][mapping['betinasian_side']]

    # Step 6: Return result
    return {
        'success': True,
        'event_key': event_key,
        'spider_odds': dispatch_message.get('odds'),
        'betinasian_odds': betinasian_odds,
        'odds_diff': dispatch_message.get('odds') - betinasian_odds,
        'market_info': {
            'spider_market_id': spider_market_id,
            'betinasian_market': mapping['betinasian_market'],
            'betinasian_side': mapping['betinasian_side'],
            'line_id': mapping.get('line_id'),
            'description': mapping['description']
        }
    }
```

### With Error Handling

```python
from MappingBetburgerToBetinisian import (
    parse_spider_market,
    is_sport_supported,
    needs_line_id
)

async def GetOdd(self, dispatch_message, **kwargs):
    sport_type = dispatch_message.get('spider_sport_type')
    spider_market_id = dispatch_message.get('market_id')
    handicap_value = dispatch_message.get('handicap')

    # Check 1: Sport supported?
    if not is_sport_supported(sport_type):
        return {
            'success': False,
            'message': f'Unsupported sport: {sport_type}'
        }

    # Check 2: Handicap required?
    if needs_line_id(sport_type, spider_market_id) and handicap_value is None:
        return {
            'success': False,
            'message': f'Market {spider_market_id} requires handicap value'
        }

    # Check 3: Can map?
    mapping = parse_spider_market(sport_type, spider_market_id, handicap_value)
    if not mapping:
        return {
            'success': False,
            'message': f'Cannot map market: {spider_market_id}'
        }

    # Continue with query...
    # ...
```

## MarketMapper Class

For cleaner code when processing multiple markets from the same sport:

```python
from MappingBetburgerToBetinisian import MarketMapper

# Create mapper once
try:
    mapper = MarketMapper("basket")
except ValueError as e:
    print(f"Error: {e}")
    return

# Use for multiple markets
markets = [
    ("17", -5.5),   # Asian Handicap
    ("19", 170),    # Over/Under
    ("21", 85.5)    # Team1 Over
]

for market_id, handicap in markets:
    mapping = mapper.parse(market_id, handicap)
    if mapping:
        print(f"{mapping['description']}: line_id={mapping.get('line_id')}")
```

## Performance Tips

1. **Cache MapperMapper instances** - Create once, reuse many times
2. **Validate early** - Use `validate_mapping()` before expensive operations
3. **Use quick queries** - `get_betinasian_market_type()` is faster than full parse

## Common Patterns

### Pattern 1: Quick Lookup

```python
from MappingBetburgerToBetinisian import (
    get_betinasian_market_type,
    get_betinasian_side
)

market = get_betinasian_market_type("basket", "17")  # "ah"
side = get_betinasian_side("basket", "17")           # "h"

# Now query directly
line_data = await page.evaluate(f'''
    window.queryData.parseOfferEventLine("{event_key}", "{market}", {line_id})
''')
odds = line_data['odds'][side]
```

### Pattern 2: Batch Processing

```python
from MappingBetburgerToBetinisian import MarketMapper

mapper = MarketMapper("basket")

spider_markets = [
    {"id": "17", "handicap": -5.5, "odds": 1.95},
    {"id": "19", "handicap": 170, "odds": 1.88},
    {"id": "1", "handicap": None, "odds": 2.50}
]

for spider_market in spider_markets:
    mapping = mapper.parse(
        spider_market["id"],
        spider_market.get("handicap")
    )

    if mapping:
        # Process mapping...
        pass
```

### Pattern 3: Dynamic Sport Selection

```python
from MappingBetburgerToBetinisian import parse_spider_market

def process_market(sport, market_id, handicap=None):
    """Process market for any sport"""
    mapping = parse_spider_market(sport, market_id, handicap)

    if not mapping:
        return None

    # Same code works for all sports!
    return {
        'market': mapping['betinasian_market'],
        'side': mapping['betinasian_side'],
        'line': mapping.get('line_id')
    }

# Works for any sport
result1 = process_market("basket", "17", -5.5)
result2 = process_market("soccer", "17", -0.5)
result3 = process_market("fb", "11")
```

## Troubleshooting

**Q: `parse_spider_market` returns `None`**
- Check if sport type is correct (use `is_sport_supported()`)
- Check if market_id exists in that sport's mapping
- Check if handicap_value is required (use `needs_line_id()`)

**Q: MarketMapper raises `ValueError`**
- Sport type not supported
- Check spelling: `"basket"` not `"baskeball"`
- Use `get_supported_sports()` to see valid options

**Q: Different line_id for same handicap in different sports**
- This is expected! Basketball and soccer use same formula (×4) but different typical values
- Basketball: -5.5 → -22
- Soccer: -0.5 → -2
