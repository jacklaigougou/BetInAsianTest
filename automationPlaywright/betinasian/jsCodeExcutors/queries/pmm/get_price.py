# -*- coding: utf-8 -*-
"""
BetInAsian Get Price

Get best executable price from PMM (Price Match Message) data
"""
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


async def get_best_price(
    page,
    event_id: str,
    bet_type: str,
    required_amount: float = 10.0,
    required_currency: str = "GBP"
) -> Dict[str, Any]:
    """
    Get best executable price for a market

    Args:
        page: Playwright Page object
        event_id: Event ID (e.g., "2026-01-06,41236,40814")
        bet_type: Bet type (e.g., "for,ml,a")
        required_amount: Required stake amount (default: 10.0)
        required_currency: Required currency (default: "GBP")

    Returns:
        {
            'success': True/False,
            'betslip_id': 'xxx',  # Only if success=True
            'bookie': 'bf',
            'price': 1.009,
            'available': {'currency': 'GBP', 'amount': 92.5102},
            'updated_at': timestamp,
            'reason': 'xxx'  # Only if success=False
        }

    Examples:
        >>> # Get best price for Money Line - Away
        >>> result = await get_best_price(
        ...     page,
        ...     event_id="2026-01-06,41236,40814",
        ...     bet_type="for,ml,a"
        ... )
        >>> if result['success']:
        ...     print(f"Best price: {result['price']} from {result['bookie']}")
    """
    try:
        logger.info(f"Getting best price: event_id={event_id}, bet_type={bet_type}")

        # Call window.queryData.getBestPrice()
        result = await page.evaluate(
            """
            (params) => {
                if (!window.queryData || !window.queryData.getBestPrice) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                return window.queryData.getBestPrice(
                    params.event_id,
                    params.bet_type,
                    params.required_amount,
                    params.required_currency
                );
            }
            """,
            {
                "event_id": event_id,
                "bet_type": bet_type,
                "required_amount": required_amount,
                "required_currency": required_currency
            }
        )

        # Log result
        if result.get('success'):
            logger.info(f"✅ Best price found:")
            logger.info(f"  - Bookie: {result.get('bookie')}")
            logger.info(f"  - Price: {result.get('price')}")
            logger.info(f"  - Available: {result.get('available')}")
            # logger.info(f"  - Betslip ID: {result.get('betslip_id')}")
        else:
            logger.warning(f"⚠️ No executable price: {result.get('reason')}")
            if result.get('best_odds'):
                logger.info(f"  - Best odds (not executable): {result.get('best_odds')}")
            if result.get('filtered_reasons'):
                logger.info(f"  - Filtered reasons: {json.dumps(result.get('filtered_reasons'), indent=2)}")

        return result

    except Exception as e:
        logger.error(f"❌ Exception in get_best_price: {e}")
        return {
            'success': False,
            'error': str(e),
            'reason': 'exception'
        }


async def get_all_prices(
    page,
    event_id: str,
    bet_type: str
) -> Dict[str, Any]:
    """
    Get all bookie prices for a market

    Args:
        page: Playwright Page object
        event_id: Event ID
        bet_type: Bet type

    Returns:
        {
            'success': True/False,
            'event_id': 'xxx',
            'bet_type': 'xxx',
            'best_executable': {...},
            'best_odds': {...},
            'bookies': [
                {'bookie': 'bf', 'price': 1.009, 'available': {...}, ...},
                ...
            ]
        }
    """
    try:
        logger.info(f"Getting all prices: event_id={event_id}, bet_type={bet_type}")

        result = await page.evaluate(
            """
            (params) => {
                if (!window.queryData || !window.queryData.getAllPrices) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                return window.queryData.getAllPrices(
                    params.event_id,
                    params.bet_type
                );
            }
            """,
            {
                "event_id": event_id,
                "bet_type": bet_type
            }
        )

        if result.get('success'):
            logger.info(f"✅ Found {len(result.get('bookies', []))} bookie prices")
            for bookie_data in result.get('bookies', []):
                logger.info(f"  - {bookie_data.get('bookie')}: {bookie_data.get('price')} (status: {bookie_data.get('status', {}).get('code')})")
        else:
            logger.warning(f"⚠️ No prices available: {result.get('reason')}")

        return result

    except Exception as e:
        logger.error(f"❌ Exception in get_all_prices: {e}")
        return {
            'success': False,
            'error': str(e),
            'reason': 'exception'
        }


async def get_total_amount_at_price(
    page,
    event_id: str,
    bet_type: str,
    target_price: float,
    required_currency: str = "GBP"
) -> Dict[str, Any]:
    """
    Get total available amount at or above target price

    Args:
        page: Playwright Page object
        event_id: Event ID
        bet_type: Bet type
        target_price: Target price (e.g., 1.5)
        required_currency: Currency (default: "GBP")

    Returns:
        {
            'success': True/False,
            'event_id': 'xxx',
            'bet_type': 'xxx',
            'target_price': 1.5,
            'currency': 'GBP',
            'total_amount': 1500.25,  # Total amount across all bookies
            'bookie_count': 3,
            'bookies': [
                {
                    'bookie': 'bf',
                    'betslip_id': 'xxx',
                    'total_amount': 800.0,
                    'tiers': [
                        {'price': 1.55, 'amount': 500, 'min': 10},
                        {'price': 1.60, 'amount': 300, 'min': 10}
                    ]
                },
                ...
            ]
        }

    Examples:
        >>> # Get total amount available at price >= 1.5
        >>> result = await get_total_amount_at_price(
        ...     page,
        ...     event_id="2026-01-06,41236,40814",
        ...     bet_type="for,ml,a",
        ...     target_price=1.5
        ... )
        >>> print(f"Total: {result['total_amount']} from {result['bookie_count']} bookies")
    """
    try:
        logger.info(f"Getting total amount at price: event_id={event_id}, bet_type={bet_type}, target_price={target_price}")

        result = await page.evaluate(
            """
            (params) => {
                if (!window.queryData || !window.queryData.getTotalAmountAtPrice) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                return window.queryData.getTotalAmountAtPrice(
                    params.event_id,
                    params.bet_type,
                    params.target_price,
                    params.required_currency
                );
            }
            """,
            {
                "event_id": event_id,
                "bet_type": bet_type,
                "target_price": target_price,
                "required_currency": required_currency
            }
        )

        if result.get('success'):
            logger.info(f"✅ Total amount at price >= {target_price}:")
            logger.info(f"  - Total: {result.get('total_amount')} {result.get('currency')}")
            logger.info(f"  - Bookie count: {result.get('bookie_count')}")

            for bookie_data in result.get('bookies', []):
                logger.info(f"\n  [{bookie_data.get('bookie')}] Total: {bookie_data.get('total_amount')}")
                for tier in bookie_data.get('tiers', []):
                    logger.info(f"    - Price {tier['price']}: {tier['amount']} (min: {tier['min']})")
        else:
            logger.warning(f"⚠️ No amount available: {result.get('reason')}")

        return result

    except Exception as e:
        logger.error(f"❌ Exception in get_total_amount_at_price: {e}")
        return {
            'success': False,
            'error': str(e),
            'reason': 'exception'
        }


async def get_price_by_betslip_id(
    page,
    betslip_id: str,
    required_amount: float = 10.0,
    required_currency: str = "GBP"
) -> Dict[str, Any]:
    """
    Get best executable price by betslip_id

    This function bypasses the bet_type format mismatch issue by directly
    querying the PMM store using the betslip_id returned from CreateBetslip.

    Args:
        page: Playwright Page object
        betslip_id: Betslip ID from CreateBetslip response
        required_amount: Required stake amount (default: 10.0)
        required_currency: Required currency (default: "GBP")

    Returns:
        {
            'success': True/False,
            'betslip_id': 'xxx',
            'event_id': 'xxx',
            'bet_type': 'xxx',
            'bookie': 'bf',
            'price': 1.009,
            'available': {'currency': 'GBP', 'amount': 92.5102},
            'updated_at': timestamp,
            'reason': 'xxx'  # Only if success=False
        }

    Examples:
        >>> # Create betslip first
        >>> betslip_result = await create_betslip(...)
        >>> betslip_id = betslip_result['data']['id']
        >>>
        >>> # Get price by betslip_id
        >>> result = await get_price_by_betslip_id(
        ...     page,
        ...     betslip_id=betslip_id
        ... )
    """
    try:
        logger.info(f"Getting price by betslip_id: {betslip_id}")

        # Call window.queryData.queryBetslipById() then extract best price
        result = await page.evaluate(
            """
            (params) => {
                if (!window.queryData || !window.queryData.queryBetslipById) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                const betslip = window.queryData.queryBetslipById(params.betslip_id);

                if (!betslip) {
                    return {
                        success: false,
                        reason: 'betslip_not_found',
                        betslip_id: params.betslip_id
                    };
                }

                // Extract best executable price
                const now = Date.now();
                const validBookies = [];
                const debugInfo = {
                    total_bookies: betslip.bookies.size,
                    filtered_bookies: {}
                };

                for (const [bookie, data] of betslip.bookies) {
                    const bookieDebug = {
                        status_code: data.status?.code,
                        has_top_available: !!data.top_available,
                        currency: data.top_available?.currency,
                        top_price: data.top_price,
                        price_tiers_count: data.price_tiers?.length || 0,
                        last_update: data.last_update,
                        age_ms: now - data.last_update
                    };

                    // Filter: success status
                    if (data.status.code !== 'success') {
                        bookieDebug.filtered_reason = 'status_not_success';
                        debugInfo.filtered_bookies[bookie] = bookieDebug;
                        continue;
                    }

                    // Filter: not expired
                    if (data.expires_at && data.expires_at < now) {
                        bookieDebug.filtered_reason = 'expired';
                        debugInfo.filtered_bookies[bookie] = bookieDebug;
                        continue;
                    }

                    // Filter: correct currency
                    if (!data.top_available || data.top_available.currency !== params.required_currency) {
                        bookieDebug.filtered_reason = 'currency_mismatch';
                        debugInfo.filtered_bookies[bookie] = bookieDebug;
                        continue;
                    }

                    // 找到所有 min <= required_amount 的 tier
                    let executableTiers = data.price_tiers.filter(tier =>
                        tier.min <= params.required_amount
                    );

                    if (executableTiers.length > 0) {
                        // 排序：优先选择 max 最大的，其次选择赔率最高的
                        executableTiers.sort((a, b) => {
                            // 第一优先级：max 最大（降序）
                            if (b.max !== a.max) {
                                return b.max - a.max;
                            }
                            // 第二优先级：赔率最高（降序）
                            return b.price - a.price;
                        });

                        const executableTier = executableTiers[0];

                        bookieDebug.filtered_reason = 'passed';
                        bookieDebug.executable_tier = executableTier;
                        bookieDebug.selected_reason = 'max_amount_priority';  // 标记选择原因
                        debugInfo.filtered_bookies[bookie] = bookieDebug;

                        validBookies.push({
                            bookie: bookie,
                            price: executableTier.price,
                            available: data.top_available,
                            status: data.status,
                            updated_at: data.last_update,
                            tier: executableTier
                        });
                    } else {
                        bookieDebug.filtered_reason = 'no_executable_tier';
                        bookieDebug.price_tiers = data.price_tiers;
                        debugInfo.filtered_bookies[bookie] = bookieDebug;
                    }
                }

                if (validBookies.length === 0) {
                    return {
                        success: false,
                        reason: 'no_executable_price',
                        betslip_id: betslip.betslip_id,
                        event_id: betslip.event_id,
                        bet_type: betslip.bet_type,
                        debug_info: debugInfo  // 添加调试信息
                    };
                }

                // Sort by price (descending - best odds first)
                validBookies.sort((a, b) => b.price - a.price);

                const best = validBookies[0];

                return {
                    success: true,
                    betslip_id: betslip.betslip_id,
                    event_id: betslip.event_id,
                    bet_type: betslip.bet_type,
                    bookie: best.bookie,
                    price: best.price,
                    available: best.available,
                    updated_at: best.updated_at,
                    tier: best.tier,
                    all_bookies: validBookies.length
                };
            }
            """,
            {
                "betslip_id": betslip_id,
                "required_amount": required_amount,
                "required_currency": required_currency
            }
        )

        # Log result
        if result.get('success'):
            logger.info(f"✅ 找到最佳赔率:")
            # logger.info(f"  - Betslip ID: {result.get('betslip_id')}")
            # logger.info(f"  - Event ID: {result.get('event_id')}")
            # logger.info(f"  - Bet Type: {result.get('bet_type')}")
            logger.info(f"  - 市场: {result.get('bookie')}")
            logger.info(f"  - 价格: {result.get('price')}")
            # logger.info(f"  - Available: {result.get('available')}")
            # logger.info(f"  - Total bookies: {result.get('all_bookies')}")
        else:
            logger.warning(f"⚠️ 未找到最佳赔率: {result.get('reason')}")
            # logger.info(f"  - Betslip ID: {result.get('betslip_id')}")

            # 输出详细的调试信息
            debug_info = result.get('debug_info')
            if debug_info:
                # logger.info(f"\n🔍 调试信息:")
                # logger.info(f"  - 总 Bookie 数: {debug_info.get('total_bookies')}")
                # logger.info(f"\n  各 Bookie 过滤原因:")
                for bookie, info in debug_info.get('filtered_bookies', {}).items():
                    logger.info(f"\n    [{bookie}]")
                    logger.info(f"      - 过滤原因: {info.get('filtered_reason')}")
                    # logger.info(f"      - 状态码: {info.get('status_code')}")
                    # logger.info(f"      - 货币: {info.get('currency')}")
                    # logger.info(f"      - 最高价格: {info.get('top_price')}")
                    # logger.info(f"      - 价格层级数: {info.get('price_tiers_count')}")
                    # logger.info(f"      - 数据年龄: {info.get('age_ms')}ms")
                    if info.get('filtered_reason') == 'no_executable_tier':
                        logger.info(f"      - 价格层级: {info.get('price_tiers')}")

        return result

    except Exception as e:
        logger.error(f"❌ Exception in get_price_by_betslip_id: {e}")
        return {
            'success': False,
            'error': str(e),
            'reason': 'exception'
        }


async def get_pmm_stats(page) -> Dict[str, Any]:
    """
    Get PMM store statistics

    Returns:
        {
            'total_betslips': 100,
            'total_events': 50,
            'total_markets': 200,
            'total_bookies': 3,
            'dirty_count': 5,
            'heap_size': 100,
            'handler_stats': {...}
        }
    """
    try:
        result = await page.evaluate(
            """
            () => {
                const stats = {};

                if (window.pmmStore && window.pmmStore.getStats) {
                    stats.store = window.pmmStore.getStats();
                }

                if (window.__pmmHandler && window.__pmmHandler.getStats) {
                    stats.handler = window.__pmmHandler.getStats();
                }

                return stats;
            }
            """
        )

        logger.info(f"PMM Stats: {json.dumps(result, indent=2)}")
        return result

    except Exception as e:
        logger.error(f"❌ Exception in get_pmm_stats: {e}")
        return {
            'error': str(e)
        }
