// Event 消息处理器
// 职责: 处理 event 消息,更新 events_store,建立索引

class EventHandler {
    /**
     * 处理 event 消息
     * @param {Object} params
     * @param {string} params.type - 消息类型
     * @param {string} params.sportPeriod - sport_period (例如: "fb_ht")
     * @param {string} params.eventKey - 事件唯一标识
     * @param {Object} params.data - 消息数据
     * @returns {boolean} 处理是否成功
     */
    handle({ type, sportPeriod, eventKey, data }) {
        try {
            // 1. 解析 sport 和 period
            const [sport, periodRaw] = sportPeriod.split('_');
            const period = periodRaw ? periodRaw.toUpperCase() : null;

            // 2. 提取日期 (从 event_key 或 start_ts)
            const date = this.extractDate(eventKey, data);

            // 3. 判断 scope (有 home/away 就是 MATCH,有 teams 列表就是 SEASON)
            const scope = this.determineScope(data);

            // 4. 提取队伍信息
            const { home, away } = this.extractTeams(data, scope);

            // 5. 判断比赛是否正在进行 (ir_status 存在且非空)
            const isInRunning = this.checkInRunning(data.ir_status);

            // 6. 构造 event 数据
            const eventData = {
                event_key: eventKey,
                sport,
                period,
                scope,
                date,
                competition_id: data.competition_id,
                competition_name: data.competition_name,
                home,
                away,
                start_ts: data.start_ts,
                end_ts: data.end_ts,
                event_type: data.event_type,
                teams: data.teams,  // 赛季盘保留完整队伍列表
                available_for_accas: data.available_for_accas,
                ir_status: data.ir_status,  // 保存原始 ir_status
                isInRunning: isInRunning    // 布尔标记: 是否正在进行
            };

            // 7. 完整重索引流程: 先移除旧索引,再建立新索引
            const oldEvent = window.__eventsStore.get(eventKey);
            const oldSportPeriod = oldEvent ? `${oldEvent.sport}${oldEvent.period ? '_' + oldEvent.period.toLowerCase() : ''}` : null;

            // 更新 store
            const event = window.__eventsStore.update(eventKey, eventData);

            // 移除旧索引 (如果存在)
            if (oldEvent && oldSportPeriod) {
                window.__eventsManager.removeEventIndexes(oldEvent, oldSportPeriod);
            }

            // 建立新索引 (基于最终合并后的数据)
            window.__eventsManager.indexEvent(event, sportPeriod);

            // 9. 通知订阅管理器
            if (window.__subscriptionManager) {
                window.__subscriptionManager.onEventReceived(event, sportPeriod);
            }

            return true;

        } catch (error) {
            return false;
        }
    }

    /**
     * 提取日期
     * @param {string} eventKey
     * @param {Object} data
     * @returns {string} 日期字符串 (YYYY-MM-DD)
     */
    extractDate(eventKey, data) {
        // 优先从 event_key 提取 (格式: "2026-01-04,31629,36428")
        const keyParts = eventKey.split(',');
        if (keyParts[0] && keyParts[0].match(/^\d{4}-\d{2}-\d{2}$/)) {
            return keyParts[0];
        }

        // 其次从 start_ts 提取
        if (data.start_ts) {
            return data.start_ts.split('T')[0];
        }

        return null;
    }

    /**
     * 判断 scope
     * @param {Object} data
     * @returns {string} "MATCH" 或 "SEASON"
     */
    determineScope(data) {
        // 判断依据:
        // - 有 home 和 away 对象 → MATCH
        // - event_type 是 multirunner/outright → SEASON
        // - 有 teams 数组且 > 2 → SEASON

        if (data.home && data.away) {
            return 'MATCH';
        }

        if (data.event_type === 'multirunner' || data.event_type === 'outright') {
            return 'SEASON';
        }

        if (data.teams && data.teams.length > 2) {
            return 'SEASON';
        }

        // 默认 MATCH
        return 'MATCH';
    }

    /**
     * 提取主客队信息
     * @param {Object} data
     * @param {string} scope
     * @returns {Object} {home, away}
     */
    extractTeams(data, scope) {
        if (scope === 'MATCH') {
            // 单场盘:有明确的主客队
            // 兼容多种数据格式:
            // 1. data.home 是字符串 (直接使用)
            // 2. data.home 是对象 (提取 name 属性)
            // 3. data.home_team 是字符串 (备选)
            let home = null;
            if (typeof data.home === 'string') {
                home = data.home;
            } else if (data.home && typeof data.home === 'object') {
                home = data.home.name || null;
            } else if (data.home_team) {
                home = data.home_team;
            }

            let away = null;
            if (typeof data.away === 'string') {
                away = data.away;
            } else if (data.away && typeof data.away === 'object') {
                away = data.away.name || null;
            } else if (data.away_team) {
                away = data.away_team;
            }

            return { home, away };
        } else {
            // 赛季盘:没有主客队概念
            return {
                home: null,
                away: null
            };
        }
    }

    /**
     * 判断比赛是否正在进行
     * @param {Object} ir_status - ir_status 字段
     * @returns {boolean} true = 正在进行, false = 未进行
     */
    checkInRunning(ir_status) {
        // ir_status 存在且非空 → IN_PLAY（正在进行）
        if (!ir_status) {
            return false;
        }

        // 检查是否为空对象
        if (typeof ir_status === 'object' && Object.keys(ir_status).length === 0) {
            return false;
        }

        return true;
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__eventHandler = new EventHandler();
}
