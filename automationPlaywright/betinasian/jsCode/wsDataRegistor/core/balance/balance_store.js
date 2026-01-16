// Balance Store - 余额存储（极简版）
// 职责: 存储当前余额，不保留历史记录

class BalanceStore {
    constructor() {
        // 当前余额数据
        this.current = null;
    }

    /**
     * 更新余额
     * @param {Object} balanceData - 余额数据
     * @param {number} timestamp - 时间戳（毫秒）
     */
    update(balanceData, timestamp) {
        try {
            // 解析余额数据
            const balance = this.parseAmount(balanceData.balance);
            const open_stake = this.parseAmount(balanceData.open_stake);
            const smart_credit = this.parseAmount(balanceData.smart_credit);

            // 更新当前余额
            this.current = {
                balance: balance.amount,
                currency: balance.currency,
                open_stake: open_stake.amount,
                smart_credit: smart_credit.amount,
                last_update: timestamp || Date.now()
            };

            console.log(`[Balance Store] Updated: ${balance.amount} ${balance.currency}`);
            return true;

        } catch (error) {
            console.error('[Balance Store] Update error:', error);
            return false;
        }
    }

    /**
     * 解析金额格式
     * @param {Array|Object} data - 金额数据
     * @returns {Object} {currency, amount}
     */
    parseAmount(data) {
        // 格式 1: ["USD", 47.0512]
        if (Array.isArray(data) && data.length === 2) {
            return {
                currency: data[0],
                amount: data[1]
            };
        }

        // 格式 2: {currency: "USD", amount: 47.0512}
        if (typeof data === 'object' && data.currency && data.amount !== undefined) {
            return {
                currency: data.currency,
                amount: data.amount
            };
        }

        // 默认值
        return { currency: "USD", amount: 0 };
    }

    /**
     * 获取当前余额
     * @returns {Object|null}
     */
    get() {
        return this.current;
    }

    /**
     * 清空数据
     */
    clear() {
        this.current = null;
    }
}

// 全局单例
if (typeof window !== 'undefined') {
    window.__balanceStore = new BalanceStore();
}
