# 爬虫数据到 BetInAsian 盘口映射

## 功能说明

将爬虫采集的篮球盘口数据映射到 BetInAsian 的盘口类型和投注方向。

## 映射关系

### 篮球盘口映射表

| 爬虫ID | 爬虫描述 | BetInAsian 盘口 | BetInAsian 方向 | 需要盘口值 |
|--------|----------|-----------------|-----------------|------------|
| 1 | Team1 Win | ml (独赢) | h (主队) | ❌ |
| 2 | Team2 Win | ml (独赢) | a (客队) | ❌ |
| 11 | 1 (半场) | html (半场独赢) | h (主队) | ❌ |
| 12 | X (半场) | html (半场独赢) | x (平局) | ❌ |
| 13 | 2 (半场) | html (半场独赢) | a (客队) | ❌ |
| 17 | Asian Handicap1 | ah (让分盘) | h (主队) | ✅ |
| 18 | Asian Handicap2 | ah (让分盘) | a (客队) | ✅ |
| 19 | Total Over | ahou (大小分) | o (大) | ✅ |
| 20 | Total Under | ahou (大小分) | u (小) | ✅ |
| 21 | Total Over for Team1 | t1ahou (主队大小分) | o (大) | ✅ |
| 22 | Total Under for Team1 | t1ahou (主队大小分) | u (小) | ✅ |
| 23 | Total Over for Team2 | t2ahou (客队大小分) | o (大) | ✅ |
| 24 | Total Under for Team2 | t2ahou (客队大小分) | u (小) | ✅ |

## 使用示例

### 1. 解析完整盘口信息

```python
from BetburgerToBetinisian.basket import parse_spider_market

# 示例1: 让分盘 Asian Handicap1(-5.5)
result = parse_spider_market("17", -5.5)
print(result)
# 输出:
# {
#     "betinasian_market": "ah",
#     "betinasian_side": "h",
#     "line_id": -55,
#     "description": "让分盘-主队"
# }

# 示例2: 大小分 Total Over(170)
result = parse_spider_market("19", 170)
print(result)
# 输出:
# {
#     "betinasian_market": "ahou",
#     "betinasian_side": "o",
#     "line_id": 1700,
#     "description": "大小分-大"
# }

# 示例3: 主队大小分 Total Over(85.5) for Team1
result = parse_spider_market("21", 85.5)
print(result)
# 输出:
# {
#     "betinasian_market": "t1ahou",
#     "betinasian_side": "o",
#     "line_id": 855,
#     "description": "主队大小分-大"
# }

# 示例4: 独赢(不需要盘口值)
result = parse_spider_market("1")
print(result)
# 输出:
# {
#     "betinasian_market": "ml",
#     "betinasian_side": "h",
#     "description": "独赢-主队"
# }
```

### 2. 快速获取盘口类型

```python
from BetburgerToBetinisian.basket import get_betinasian_market_type

market_type = get_betinasian_market_type("17")
print(market_type)  # "ah"

market_type = get_betinasian_market_type("19")
print(market_type)  # "ahou"
```

### 3. 快速获取投注方向

```python
from BetburgerToBetinisian.basket import get_betinasian_side

side = get_betinasian_side("17")
print(side)  # "h" (主队)

side = get_betinasian_side("19")
print(side)  # "o" (大)
```

### 4. 判断是否需要盘口值

```python
from BetburgerToBetinisian.basket import needs_line_id

# 让分盘需要盘口值
print(needs_line_id("17"))  # True

# 独赢不需要盘口值
print(needs_line_id("1"))   # False
```

### 5. 完整使用流程

```python
from BetburgerToBetinisian.basket import (
    parse_spider_market,
    needs_line_id,
    BETINASIAN_MARKET_NAMES,
    BETINASIAN_SIDE_NAMES
)

# 爬虫数据
spider_data = {
    "market_id": "17",           # Asian Handicap1
    "handicap": -5.5,            # -5.5 盘口
    "odds": 1.95                 # 赔率 1.95
}

# 1. 解析映射
mapping = parse_spider_market(spider_data["market_id"], spider_data["handicap"])

if mapping:
    print(f"盘口类型: {BETINASIAN_MARKET_NAMES[mapping['betinasian_market']]}")
    print(f"投注方向: {BETINASIAN_SIDE_NAMES[mapping['betinasian_side']]}")

    if 'line_id' in mapping:
        print(f"盘口值: {mapping['line_id']}")

    # 2. 构造查询条件
    query_params = {
        "event_key": "2026-01-06,42495,47395",
        "offer_type": mapping["betinasian_market"],  # "ah"
        "line_id": mapping.get("line_id"),           # -55
        "side": mapping["betinasian_side"]           # "h"
    }

    print(f"\n查询参数: {query_params}")

    # 3. 使用 parseOfferEventLine 查询
    # result = await page.evaluate(f'''
    #     window.queryData.parseOfferEventLine(
    #         "{query_params['event_key']}",
    #         "{query_params['offer_type']}",
    #         {query_params['line_id']}
    #     )
    # ''')
    #
    # if result:
    #     betinasian_odds = result['odds'][query_params['side']]
    #     print(f"BetInAsian 赔率: {betinasian_odds}")
else:
    print("无法映射该盘口")
```

## 盘口值转换规则

BetInAsian 的 `line_id` 使用整数表示,转换规则:

- **让分盘**: `line_id = handicap × 10`
  - `-5.5` → `-55`
  - `3.0` → `30`
  - `-10.5` → `-105`

- **大小分**: `line_id = total × 10`
  - `170` → `1700`
  - `165.5` → `1655`
  - `180.0` → `1800`

## 集成到 GetOdd.py

```python
from BetburgerToBetinisian.basket import parse_spider_market

async def GetOdd(self, dispatch_message, **kwargs):
    # ... 获取 event_key ...

    # 1. 解析爬虫盘口
    spider_market_id = dispatch_message.get('market_id')
    handicap_value = dispatch_message.get('handicap')

    mapping = parse_spider_market(spider_market_id, handicap_value)

    if not mapping:
        return {'success': False, 'message': f'无法映射盘口: {spider_market_id}'}

    # 2. 订阅 watch_event
    # ... (watch_event 代码) ...

    # 3. 查询对应的 line
    if 'line_id' in mapping:
        # 有盘口值,查询特定 line
        line_data = await self.page.evaluate(f'''
            window.queryData.parseOfferEventLine(
                "{event_key}",
                "{mapping['betinasian_market']}",
                {mapping['line_id']}
            )
        ''')
    else:
        # 无盘口值(如独赢),查询整个 offer
        line_data = await self.page.evaluate(f'''
            window.queryData.parseOdds(
                "{event_key}",
                "{mapping['betinasian_market']}"
            )
        ''')

    if not line_data:
        return {'success': False, 'message': '未找到对应盘口'}

    # 4. 提取赔率
    odds = line_data['odds'][mapping['betinasian_side']]

    return {
        'success': True,
        'odds': odds,
        'market_info': mapping
    }
```

## 注意事项

1. **盘口值单位**: 爬虫数据的盘口值可能是整数(如 170)或小数(如 165.5),统一转换为整数 line_id
2. **投注方向**: 确保使用正确的方向代码 (`h`, `a`, `o`, `u`, `x`)
3. **盘口类型**: BetInAsian 可能不支持所有爬虫盘口,需要检查返回值
4. **数据时效**: offers_event 需要先订阅 watch_event 才能获取详细数据
