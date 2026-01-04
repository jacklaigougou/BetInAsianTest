// BetInAsian WebSocket Hook Script

(function () {
    // Save original WebSocket constructor
    const OriginalWebSocket = window.WebSocket;
    console.log('[BetInAsian Hook] Hook script started');

    // Override WebSocket constructor
    window.WebSocket = function (...args) {
        console.log('[BetInAsian Hook] New WebSocket connection:', args[0]);

        // Create original WebSocket instance
        const ws = new OriginalWebSocket(...args);

        // Save to window.__ws (latest WebSocket)
        window.__ws = ws;

        // Save all WebSockets to an array
        window.__allWebSockets = window.__allWebSockets || [];
        window.__allWebSockets.push(ws);

        console.log('[BetInAsian Hook] WebSocket saved to window.__ws');

        // Add event listeners for debugging
        ws.addEventListener('open', function (event) {
            console.log('[BetInAsian Hook] WebSocket connected:', ws.url);
        });

        ws.addEventListener('close', function (event) {
            console.log('[BetInAsian Hook] WebSocket closed:', event.code, event.reason);
        });

        ws.addEventListener('error', function (event) {
            console.log('[BetInAsian Hook] WebSocket error:', event);
        });

        // Message counter
        let messageCount = 0;
        ws.addEventListener('message', function (event) {
            messageCount++;

            try {
                const data = JSON.parse(event.data);
                console.log(`[BetInAsian Hook] WebSocket message #${messageCount}:`, data);

                // Store all messages for Python access (legacy)
                window.__wsMessages = window.__wsMessages || [];
                window.__wsMessages.push({
                    count: messageCount,
                    timestamp: Date.now(),
                    data: data
                });

                // Keep only last 100 messages to prevent memory issues
                if (window.__wsMessages.length > 100) {
                    window.__wsMessages.shift();
                }

                // ========== 新增: 注册到数据存储器 ==========
                if (window.registerMessage) {
                    // 处理批量消息
                    if (Array.isArray(data)) {
                        // 批量消息: [ [msg1], [msg2], [msg3], ... ]
                        data.forEach(message => {
                            if (Array.isArray(message) && message.length >= 3) {
                                window.registerMessage(message);
                            }
                        });
                    } else if (Array.isArray(data) === false && typeof data === 'object') {
                        // 单条消息但不是数组格式,跳过
                        console.log(`[BetInAsian Hook] Skipping non-array message`);
                    }
                } else {
                    console.warn(`[BetInAsian Hook] window.registerMessage not available yet`);
                }

            } catch (e) {
                console.log(`[BetInAsian Hook] WebSocket message #${messageCount}: Non-JSON data`);
            }
        });

        return ws;
    };

    // Preserve prototype
    window.WebSocket.prototype = OriginalWebSocket.prototype;

    // Helper function: Send data via WebSocket
    window.sendWebSocketData = function (data) {
        if (window.__ws && window.__ws.readyState === 1) {
            window.__ws.send(data);
            console.log('[BetInAsian Hook] Data sent via WebSocket:', data);
            return true;
        } else {
            console.log('[BetInAsian Hook] WebSocket not connected or not ready');
            return false;
        }
    };

    // Helper function: Get WebSocket status
    window.getWebSocketStatus = function () {
        if (!window.__ws) {
            return 'No WebSocket instance';
        }
        const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
        return {
            state: states[window.__ws.readyState],
            stateCode: window.__ws.readyState,
            url: window.__ws.url,
            totalWebSockets: window.__allWebSockets ? window.__allWebSockets.length : 0
        };
    };

    // Helper function: Get recent messages
    window.getRecentMessages = function (count = 10) {
        if (!window.__wsMessages || window.__wsMessages.length === 0) {
            return [];
        }
        return window.__wsMessages.slice(-count);
    };

    // Helper function: Clear message history
    window.clearMessageHistory = function () {
        window.__wsMessages = [];
        console.log('[BetInAsian Hook] Message history cleared');
    };

    console.log("[BetInAsian Hook] WebSocket hook installed successfully!");
    console.log("[BetInAsian Hook] Available functions:");
    console.log("  - window.sendWebSocketData(data)");
    console.log("  - window.getWebSocketStatus()");
    console.log("  - window.getRecentMessages(count)");
    console.log("  - window.clearMessageHistory()");

})();
