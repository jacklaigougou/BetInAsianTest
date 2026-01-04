# WebSocket 数据注册器使用文档

## 概述

这是一个完整的 WebSocket 实时数据管理系统,采用**扁平主键 + 多维索引**架构,支持高效的数据存储、更新和查询。

## 核心设计

### 数据结构

```
eventsByKey (Map)      ← Event 主表 (扁平)
marketsByKey (Map)     ← Market 主表 (扁平)
indexes (Object)       ← 多维索引
```

### 索引维度

- `bySport`: 按 sport_period (例如: "fb_ht")
- `byCompetition`: 按 competition_id
- `byDate`: 按日期 ("YYYY-MM-DD")
- `byScope`: 按 MATCH/SEASON
- `byPeriod`: 按 FT/HT/Q1 等
- `byHomeTeam`: 按主队名称
- `byAwayTeam`: 按客队名称
- `activeLinesByEvent`: 按 event 聚合活跃盘口
- `byMarketGroup`: 按 market_group (例如: "ahou")

## JavaScript 端使用

### 1. 查询 Event

```javascript
// 按 event_key 查询
const event = window.queryData.event("2026-01-04,31629,36428");

// 按 sport_period 查询
const fbHtEvents = window.queryData.bySport("fb_ht");

// 按 competition 查询
const plEvents = window.queryData.byCompetition(416);

// 按日期查询
const todayEvents = window.queryData.byDate("2026-01-04");

// 按主队查询
const arsenalMatches = window.queryData.byHomeTeam("Arsenal");

// 按任意球队查询 (主队或客队)
const chelseaMatches = window.queryData.byTeam("Chelsea");

// 多条件查询
const results = window.queryData.query({
    sport: "fb",
    scope: "MATCH",
    period: "HT",
    competition_id: 416,
    date: "2026-01-04"
});

// 自定义过滤
const liveMatches = window.queryData.filterEvents(
    event => event.liveScore && event.liveScore.status === 'live'
);
```

### 2. 查询 Market

```javascript
// 查询指定事件的所有市场
const markets = window.queryData.marketsByEvent("2026-01-04,31629,36428");

// 查询指定事件的活跃市场
const activeMarkets = window.queryData.activeMarketsByEvent("2026-01-04,31629,36428");

// 查询赔率历史
const history = window.queryData.oddsHistory("market_key_here");

// 按 market_group 查询
const ahouMarkets = window.queryData.marketsByGroup("ahou");

// 自定义过滤
const highOdds = window.queryData.filterMarkets(
    market => market.odds && market.odds.home > 2.0
);
```

### 3. 统计信息

```javascript
// 获取数据统计
const stats = window.queryData.stats();
console.log(stats);
// {
//   totalEvents: 500,
//   totalMarkets: 2500,
//   bySport: { fb_ht: 200, fb_ft: 180, ... },
//   byScope: { MATCH: 450, SEASON: 50 },
//   byPeriod: { FT: 300, HT: 200 },
//   byCompetition: { 416: 80, ... },
//   byMarketGroup: { ahou: 1200, 1x2: 800 }
// }

// 获取路由统计
const routerStats = window.getRouterStats();
console.log(routerStats);
// {
//   totalMessages: 10000,
//   successCount: 9950,
//   errorCount: 50,
//   successRate: "99.50%",
//   byType: {
//     event: 500,
//     offers_hcaps: 8500,
//     offers_event: 950,
//     api_pmm: 50
//   }
// }
```

### 4. 数据管理

```javascript
// 直接访问原始数据
const eventsMap = window.getEventsData();  // Map<event_key, event>
const marketsMap = window.getMarketsData();  // Map<market_key, market>
const indexes = window.getIndexes();

// 清空所有数据
window.clearAllData();

// 删除指定事件
const result = window.deleteEvent("2026-01-04,31629,36428");
// { eventDeleted: true, marketsDeleted: 15 }
```

## Python 端使用

### 1. 初始化

```python
from automationPlaywright.betinasian.jsCodeExcutors import (
    inject_websocket_hook,
    inject_data_registors,
    get_registor_stats,
    get_router_stats
)

# 1. 先注入 WebSocket Hook
await inject_websocket_hook(page, handler_name="BetInAsian")

# 2. 再注入数据注册器系统
await inject_data_registors(page, handler_name="BetInAsian")

# 3. 等待数据收集
await asyncio.sleep(5)

# 4. 查看统计
await get_registor_stats(page)
await get_router_stats(page)
```

### 2. 查询数据

```python
# 查询单个 event
event = await page.evaluate('window.queryData.event("2026-01-04,31629,36428")')

# 查询今天的足球半场赛事
fb_ht_events = await page.evaluate('window.queryData.bySport("fb_ht")')

# 查询英超所有赛事
pl_events = await page.evaluate('window.queryData.byCompetition(416)')

# 查询 Arsenal 的比赛
arsenal_matches = await page.evaluate('window.queryData.byTeam("Arsenal")')

# 多条件查询
results = await page.evaluate('''
    window.queryData.query({
        sport: "fb",
        scope: "MATCH",
        period: "HT",
        date: "2026-01-04"
    })
''')

# 自定义过滤
live_matches = await page.evaluate('''
    window.queryData.filterEvents(
        event => event.liveScore && event.liveScore.status === 'live'
    )
''')
```

### 3. 查询 Market

```python
# 查询某场比赛的所有市场
markets = await page.evaluate('''
    window.queryData.marketsByEvent("2026-01-04,31629,36428")
''')

# 查询活跃市场
active_markets = await page.evaluate('''
    window.queryData.activeMarketsByEvent("2026-01-04,31629,36428")
''')

# 查询赔率历史
history = await page.evaluate('''
    window.queryData.oddsHistory("market_key_here")
''')
```

## 数据流转过程

```
WebSocket Message
    ↓
Hook 拦截
    ↓
window.registerMessage(message)
    ↓
MessageRouter.route()
    ↓
根据消息类型分发:
    ├─ event → EventHandler
    ├─ offers_hcaps → OffersHandler
    ├─ offers_event → OffersHandler
    └─ api_pmm → ApiHandler
    ↓
Handler 处理:
    ├─ 更新主表 (eventsStore / marketsStore)
    └─ 更新索引 (indexManager)
    ↓
数据可查询
```

## 文件结构

```
wsDataRegistor/
├── core/
│   ├── events_store.js          # Event 主表
│   ├── markets_store.js         # Market 主表
│   └── index_manager.js         # 索引管理器
├── handlers/
│   ├── event_handler.js         # Event 消息处理
│   ├── offers_handler.js        # Offers 消息处理
│   └── api_handler.js           # API 消息处理
├── message_router.js            # 消息路由器
├── query_engine.js              # 查询引擎
└── index.js                     # 统一入口
```

## 性能特点

✅ **O(1) 查询**: 通过 event_key 或 market_key 直接访问
✅ **索引优化**: 多维索引支持快速筛选
✅ **直接覆盖**: offers 消息直接覆盖,无需 merge
✅ **内存高效**: 扁平存储,无深层嵌套
✅ **实时更新**: 同一对象持续更新,保持数据一致性

## 注意事项

1. **加载顺序**: 必须先注入 Hook,再注入数据注册器
2. **消息格式**: 消息必须是 `[type, [sport_period, event_key], data]` 格式
3. **批量消息**: 自动处理批量消息 (数组的数组)
4. **历史记录**: 赔率历史默认保留最近 20 条

## 调试技巧

```javascript
// 1. 查看路由统计
console.log(window.getRouterStats());

// 2. 查看数据统计
console.log(window.queryData.stats());

// 3. 查看索引内容
console.log(window.getIndexes());

// 4. 查看原始数据
console.log(window.getEventsData());
console.log(window.getMarketsData());

// 5. 手动注册消息 (测试)
window.registerMessage([
    "event",
    ["fb_ht", "2026-01-04,31629,36428"],
    {
        competition_id: 416,
        competition_name: "England Premier League",
        home: { name: "Arsenal" },
        away: { name: "Chelsea" }
    }
]);
```

## 扩展开发

### 添加新的索引

编辑 `core/index_manager.js`:

```javascript
this.indexes = {
    // ... 现有索引
    byVenue: new Map(),  // 新增: 按场地索引
};

// 在 indexEvent 中添加
if (event.venue) {
    this.addToIndex('byVenue', event.venue, eventKey);
}
```

### 添加新的消息类型

1. 在 `handlers/` 创建新的 handler
2. 在 `message_router.js` 注册 handler
3. 更新 `index.js` 加载顺序

## 常见问题

**Q: 为什么我的消息没有被处理?**
A: 检查 `window.getRouterStats()`,查看 `byType` 中是否有该消息类型

**Q: 如何清空所有数据重新开始?**
A: 调用 `window.clearAllData()`

**Q: 赔率历史只保留20条够吗?**
A: 可以修改 `markets_store.js` 中的 `maxHistoryLength` 配置

**Q: 如何查看某个 event 的所有更新历史?**
A: Event 本身不保留历史,只有 Market 的赔率有历史记录
