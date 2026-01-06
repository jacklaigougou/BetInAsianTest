// BetInAsian WebSocket Hook Script

(function () {
    // Save original WebSocket constructor
    const OriginalWebSocket = window.WebSocket;

    // Override WebSocket constructor
    window.WebSocket = function (...args) {
        // Create original WebSocket instance
        const ws = new OriginalWebSocket(...args);

        // Get WebSocket URL
        const url = args[0];

        // Check if this is the cpricefeed connection
        const isCpricefeed = url && url.includes('cpricefeed');

        if (isCpricefeed) {
            // ========== Hook cpricefeed connection ==========

            // Save to window.__ws (cpricefeed WebSocket)
            window.__ws = ws;

            // Message counter
            let messageCount = 0;
            ws.addEventListener('message', function (event) {
                messageCount++;

                try {
                    const data = JSON.parse(event.data);

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

                    // ========== 注册到数据存储器 ==========
                    if (window.registerMessage) {
                        // 处理批量消息
                        if (Array.isArray(data)) {
                            // 批量消息: [ [msg1], [msg2], [msg3], ... ]
                            data.forEach(message => {
                                if (Array.isArray(message) && message.length >= 3) {
                                    window.registerMessage(message);
                                }
                            });
                        }
                    }

                } catch (e) {
                    // Silent error
                }
            });

        } else {
            // ========== Other connections (faye etc.) - No hook ==========
            // Just save for debugging purposes
            window.__otherWebSockets = window.__otherWebSockets || [];
            window.__otherWebSockets.push({
                url: url,
                ws: ws,
                createdAt: Date.now()
            });
        }

        return ws;
    };

    // Preserve prototype
    window.WebSocket.prototype = OriginalWebSocket.prototype;

    // Helper function: Get WebSocket instance
    window.getWebSocketInstance = function () {
        return window.__ws || null;
    };

    // Helper function: Send data via WebSocket
    window.sendWebSocketData = function (data) {
        if (window.__ws && window.__ws.readyState === 1) {
            window.__ws.send(data);
            return true;
        } else {
            return false;
        }
    };

    // Helper function: Get WebSocket status
    window.getWebSocketStatus = function () {
        if (!window.__ws) {
            return {
                cpricefeed: 'Not connected',
                otherWebSockets: window.__otherWebSockets ? window.__otherWebSockets.length : 0
            };
        }
        const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
        return {
            cpricefeed: {
                state: states[window.__ws.readyState],
                stateCode: window.__ws.readyState,
                url: window.__ws.url
            },
            otherWebSockets: window.__otherWebSockets ? window.__otherWebSockets.length : 0
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
    };

})();
