# Market Mapping Module

Spider to BetInAsian market mapping for multiple sports.

## Directory Structure

```
MappingBetburgerToBetinisian/
├── basket/                    # Basketball mapping module
│   ├── __init__.py
│   ├── basket.py             # Basketball mapping logic
│   └── README.md             # Basketball usage guide
│
├── soccer/                    # Soccer mapping module
│   ├── __init__.py
│   ├── soccer.py             # Soccer mapping logic
│   └── README.md             # Soccer usage guide
│
├── mapping.py                 # Unified interface (auto-routing)
├── UNIFIED_API.md            # Unified interface documentation
├── __init__.py               # Package entry point
└── README.md                 # This file
```

## Quick Start

### Option 1: Unified Interface (Recommended)

Auto-routes to the correct sport module:

```python
from MappingBetburgerToBetinisian import parse_spider_market

# Basketball
mapping = parse_spider_market("basket", "17", -5.5)
# Returns: {"betinasian_market": "ah", "betinasian_side": "h", "line_id": -22, ...}

# Soccer
mapping = parse_spider_market("soccer", "11")
# Returns: {"betinasian_market": "ml", "betinasian_side": "h", ...}
```

### Option 2: Direct Module Access

Import specific sport module:

```python
from MappingBetburgerToBetinisian import basket, soccer

# Basketball
basket_mapping = basket.parse_spider_market("17", -5.5)

# Soccer
soccer_mapping = soccer.parse_spider_market("17", -0.5)
```

### Option 3: Object-Oriented

Create a mapper for specific sport:

```python
from MappingBetburgerToBetinisian import MarketMapper

# Create basketball mapper
basket_mapper = MarketMapper("basket")

# Parse multiple markets
mapping1 = basket_mapper.parse("17", -5.5)
mapping2 = basket_mapper.parse("19", 170)
```

## Supported Sports

| Sport | Aliases | Module |
|-------|---------|--------|
| Basketball | `"basket"`, `"basketball"` | `basket/` |
| Soccer | `"soccer"`, `"fb"`, `"football"` | `soccer/` |

## Key Conversion Rule

All sports use the same conversion rule:

**line_id = handicap_value × 4**

### Examples

**Basketball:**
```python
-5.5 × 4 = -22    # Asian Handicap -5.5
170  × 4 = 680    # Over/Under 170
```

**Soccer:**
```python
-0.5 × 4 = -2     # Asian Handicap -0.5
2.5  × 4 = 10     # Over/Under 2.5
```

## Common Functions

All available from unified interface:

```python
from MappingBetburgerToBetinisian import (
    parse_spider_market,        # Full parsing
    get_betinasian_market_type, # Quick get market type
    get_betinasian_side,        # Quick get bet side
    needs_line_id,              # Check if needs handicap
    validate_mapping,           # Validate with error message
    get_supported_sports,       # List supported sports
    is_sport_supported,         # Check if sport is supported
)

# Usage examples
market_type = get_betinasian_market_type("basket", "17")  # "ah"
side = get_betinasian_side("basket", "17")                 # "h"
needs_hcp = needs_line_id("basket", "17")                  # True

# Validation
valid, mapping, error = validate_mapping("basket", "17", -5.5)
if valid:
    print(mapping)
else:
    print(f"Error: {error}")
```

## Documentation

- **Basketball Guide**: See `basket/README.md`
- **Soccer Guide**: See `soccer/README.md`
- **Unified API Guide**: See `UNIFIED_API.md`

## Integration Example

```python
from MappingBetburgerToBetinisian import parse_spider_market, validate_mapping

async def GetOdd(self, dispatch_message, **kwargs):
    # Extract spider data
    sport_type = dispatch_message.get('spider_sport_type')  # "basket" or "fb"
    market_id = dispatch_message.get('market_id')           # "17"
    handicap = dispatch_message.get('handicap')             # -5.5

    # Validate and parse
    valid, mapping, error = validate_mapping(sport_type, market_id, handicap)

    if not valid:
        return {'success': False, 'message': error}

    # Use mapping to query BetInAsian
    # mapping = {
    #     "betinasian_market": "ah",
    #     "betinasian_side": "h",
    #     "line_id": -22,
    #     "description": "Asian Handicap - Home"
    # }

    # ... rest of your code ...
```

## Adding New Sports

To add a new sport (e.g., tennis):

1. Create directory: `tennis/`
2. Create mapping file: `tennis/tennis.py`
3. Create init file: `tennis/__init__.py`
4. Update `mapping.py` SPORT_MODULES dict:
   ```python
   SPORT_MODULES = {
       ...
       "tennis": tennis
   }
   ```

## Notes

- All mapping functions return `None` if market cannot be mapped
- Use `validate_mapping()` for detailed error messages
- Markets without handicap (like 1X2) don't need `handicap_value` parameter
- Same market ID may map differently in different sports
