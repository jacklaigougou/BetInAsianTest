// WebSocket Hook Script


(function () {

    // Save original WebSocket constructor
    const OriginalWebSocket = window.WebSocket;
    console.log('hook start');
    // Override WebSocket constructor
    window.WebSocket = function (...args) {
        console.log('新建ws连接:', args[0]);

        // Create original WebSocket instance
        const ws = new OriginalWebSocket(...args);

        // Save to window.__ws
        window.__ws = ws;

        // Also save all WebSockets to an array
        window.__allWebSockets = window.__allWebSockets || [];
        window.__allWebSockets.push(ws);

        console.log('ws连接保存到window.__ws');

        // Add event listeners for debugging
        ws.addEventListener('open', function (event) {
            console.log('WebSocket connected:', ws.url);
        });

        ws.addEventListener('close', function (event) {
            console.log('WebSocket closed:', event.code, event.reason);
        });

        ws.addEventListener('error', function (event) {
            console.log('WebSocket error:', event);
        });

        // 添加消息计数器
        let messageCount = 0;
        ws.addEventListener('message', function (event) {
            messageCount++;

            try {
                const data = JSON.parse(event.data);
                // console.log(`收到WebSocket消息: ${messageCount} - type: ${data.type}, destination: ${data.destination}`);
                window.__pagestatus = 'LIVE_EURO_ODDS';
               
                // 根据destination设置页面状态
                if (data.destination) {
                    if (data.destination === 'LIVE_EURO_ODDS') {
                        window.__pagestatus = 'LIVE_EURO_ODDS';

                        if (data.type === 'FULL_ODDS') {
                            // 保存完整的 FULL_ODDS 数据
                            // window.__allEvents = data;
                            // 保存 odds 部分到 window.__AllEvents
                            window.__AllEvents = data.odds;

                            // 解析联赛和比赛数据
                            console.log('开始解析FULL_ODDS数据...');
                            window.__parsedEvents = {};

                            // 兼容不同的数据结构
                            const leagues = (data.odds && data.odds.leagues) ? data.odds.leagues : [];
                            console.log('找到', leagues.length, '个联赛');

                            leagues.forEach(league => {
                                const leagueCode = league.leagueCode || '';
                                const leagueId = league.id || '';

                                // 处理联赛名称(移除特殊字符并转小写)
                                const processedLeagueName = leagueCode
                                    .replace(/\./g, '')
                                    .replace(/,/g, '')
                                    .replace(/\s/g, '')
                                    .replace(/-/g, '')
                                    .replace(/_/g, '')
                                    .replace(/\\/g, '')
                                    .replace(/\//g, '')
                                    .toLowerCase()
                                    .trim();

                                // 如果该联赛还没有初始化，创建数组
                                if (!window.__parsedEvents[processedLeagueName]) {
                                    window.__parsedEvents[processedLeagueName] = {
                                        leagueID: String(leagueId),
                                        leagueCode: leagueCode,
                                        processedLeagueName: processedLeagueName,
                                        events: []
                                    };
                                }

                                // 遍历该联赛下的所有事件
                                const events = league.events || [];
                                events.forEach(event => {
                                    const eventId = event.id;
                                    const eventParentId = event.parentId;

                                    // 获取主队和客队
                                    const participants = event.participants || [];
                                    let homeTeam = '';
                                    let awayTeam = '';

                                    participants.forEach(participant => {
                                        if (participant.type === 'HOME') {
                                            homeTeam = participant.englishName || '';
                                        } else if (participant.type === 'AWAY') {
                                            awayTeam = participant.englishName || '';
                                        }
                                    });

                                    // 将事件添加到该联赛的events数组中
                                    window.__parsedEvents[processedLeagueName].events.push({
                                        home: homeTeam,
                                        away: awayTeam,
                                        eventID: eventId,
                                        eventParentID: eventParentId
                                    });
                                });
                            });

                            console.log('✅ 解析完成! 共', Object.keys(window.__parsedEvents).length, '个事件');
                            console.log('可以通过 window.__parsedEvents 访问数据');
                        }
                    } else if (data.destination.trim() === 'EVENTS_DETAIL_EURO'  ||
                        data.destination.trim() === 'EVENT_DETAILS_EURO_ODDS' ) {
                        window.__pagestatus = 'EVENTS_DETAIL_EURO';
                        
                        // 只处理 FULL_ODDS
                        if (data.type === 'FULL_ODDS') {
                            // 构造并存储FULL_ODDS数据
                            window.___detailFullOdds = data.odds;
                            console.log('✅ 收到FULL_ODDS数据，已存储到window.___detailFullOdds');
                        }

                    } else {
                        // 其他值则打印出来
                        
                        console.log(`其他destination值: ${data.destination}`);
                    }
                }
            } catch (e) {
                console.log(`收到WebSocket消息: ${messageCount} - 非JSON数据`);
            }
        });

        return ws;
    };

    // Preserve prototype
    window.WebSocket.prototype = OriginalWebSocket.prototype;

    // Add helper function for sending data
    window.sendWebSocketData = function (data) {
        if (window.__ws && window.__ws.readyState === 1) {
            window.__ws.send(data);
            console.log('Data sent:', data);
            return true;
        } else {
            console.log('WebSocket not connected or not ready');
            return false;
        }
    };

    // Add function to check WebSocket status
    window.getWebSocketStatus = function () {
        if (!window.__ws) {
            return 'No WebSocket instance';
        }
        const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
        return {
            state: states[window.__ws.readyState],
            stateCode: window.__ws.readyState,
            url: window.__ws.url
        };
    };

    console.log("WebSocket hook installed successfully!");

})();