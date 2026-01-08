# -*- coding: utf-8 -*-
"""
BetInAsian Get Order & Bet

Python interface for querying order and bet data from browser stores
"""
from typing import Dict, Any, List, Optional
import logging
import json

logger = logging.getLogger(__name__)


async def get_order_by_id(
    page,
    order_id: str
) -> Dict[str, Any]:
    """
    Get order by ID

    Args:
        page: Playwright Page object
        order_id: Order ID

    Returns:
        {
            'order_id': 'xxx',
            'event_id': 'xxx',
            'betslip_id': 'xxx',
            'status': 'OPEN',
            'duration': 10,
            'created_at': timestamp,
            'bookie': 'bf',
            'price': 1.009,
            'stake': 15,
            'success': [],
            'inprogress': [['bf', 15]],
            'danger': [],
            'unplaced': [],
            'bet_bar': {
                'success': 0,
                'inprogress': 15,
                'danger': 0,
                'unplaced': 0
            },
            'state_summary': {
                'status': 'OPEN',
                'isDone': False,
                'betBar': {...},
                'nextState': 'PLACED'
            }
        }
    """
    try:
        result = await page.evaluate(
            """
            (order_id) => {
                if (!window.queryData || !window.queryData.queryOrderById) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                const order = window.queryData.queryOrderById(order_id);

                if (!order) {
                    return {
                        success: false,
                        reason: 'order_not_found'
                    };
                }

                return {
                    success: true,
                    data: order
                };
            }
            """,
            order_id
        )

        if result.get('success'):
            logger.info(f"✅ Order found: {order_id}")
            return result.get('data')
        else:
            logger.warning(f"⚠️ Order not found: {order_id}, reason: {result.get('reason')}")
            return None

    except Exception as e:
        logger.error(f"❌ Exception in get_order_by_id: {e}")
        return None


async def get_orders_by_status(
    page,
    status: str
) -> List[Dict[str, Any]]:
    """
    Get orders by status

    Args:
        page: Playwright Page object
        status: Order status (CREATED, OPEN, PLACED, FINISHED, EXPIRED_LOCAL)

    Returns:
        List of order data
    """
    try:
        result = await page.evaluate(
            """
            (status) => {
                if (!window.queryData || !window.queryData.getOrdersByStatus) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                const orders = window.queryData.getOrdersByStatus(status);

                return {
                    success: true,
                    data: orders
                };
            }
            """,
            status
        )

        if result.get('success'):
            orders = result.get('data', [])
            logger.info(f"✅ Found {len(orders)} orders with status: {status}")
            return orders
        else:
            logger.warning(f"⚠️ Query failed: {result.get('reason')}")
            return []

    except Exception as e:
        logger.error(f"❌ Exception in get_orders_by_status: {e}")
        return []


async def get_orders_by_event(
    page,
    event_id: str
) -> List[Dict[str, Any]]:
    """
    Get orders by event

    Args:
        page: Playwright Page object
        event_id: Event ID

    Returns:
        List of order data
    """
    try:
        result = await page.evaluate(
            """
            (event_id) => {
                if (!window.queryData || !window.queryData.getOrdersByEvent) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                const orders = window.queryData.getOrdersByEvent(event_id);

                return {
                    success: true,
                    data: orders
                };
            }
            """,
            event_id
        )

        if result.get('success'):
            orders = result.get('data', [])
            logger.info(f"✅ Found {len(orders)} orders for event: {event_id}")
            return orders
        else:
            logger.warning(f"⚠️ Query failed: {result.get('reason')}")
            return []

    except Exception as e:
        logger.error(f"❌ Exception in get_orders_by_event: {e}")
        return []


async def get_order_with_bets(
    page,
    order_id: str
) -> Dict[str, Any]:
    """
    Get order with its bets

    Args:
        page: Playwright Page object
        order_id: Order ID

    Returns:
        {
            'order': {...},
            'bets': [
                {
                    'bet_id': 'xxx',
                    'order_id': 'xxx',
                    'bookie': 'bf',
                    'status': 'MATCHED',
                    'price': 1.009,
                    'stake': 15,
                    'matched_price': 1.009,
                    'matched_stake': 15.0,
                    'slippage': {
                        'requested_price': 1.009,
                        'matched_price': 1.009,
                        'slippage': 0.0,
                        'slippage_pct': '0.0000%'
                    }
                },
                ...
            ]
        }
    """
    try:
        result = await page.evaluate(
            """
            (order_id) => {
                if (!window.queryData || !window.queryData.getOrderWithBets) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                const data = window.queryData.getOrderWithBets(order_id);

                if (!data) {
                    return {
                        success: false,
                        reason: 'order_not_found'
                    };
                }

                return {
                    success: true,
                    data: data
                };
            }
            """,
            order_id
        )

        if result.get('success'):
            data = result.get('data')
            logger.info(f"✅ Order with {len(data.get('bets', []))} bets: {order_id}")
            return data
        else:
            logger.warning(f"⚠️ Order not found: {order_id}")
            return None

    except Exception as e:
        logger.error(f"❌ Exception in get_order_with_bets: {e}")
        return None


async def check_order_slippage(
    page,
    order_id: str
) -> Dict[str, Any]:
    """
    Check slippage for all bets in an order

    Args:
        page: Playwright Page object
        order_id: Order ID

    Returns:
        {
            'order_id': 'xxx',
            'total_slippage': 0.0,
            'avg_slippage': 0.0,
            'avg_slippage_pct': '0.0000%',
            'bet_count': 1,
            'bets': [
                {
                    'bet_id': 'xxx',
                    'bookie': 'bf',
                    'requested_price': 1.009,
                    'matched_price': 1.009,
                    'slippage': 0.0,
                    'slippage_pct': '0.0000%'
                },
                ...
            ]
        }
    """
    try:
        result = await page.evaluate(
            """
            (order_id) => {
                if (!window.queryData || !window.queryData.checkOrderSlippage) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                const slippage = window.queryData.checkOrderSlippage(order_id);

                if (!slippage) {
                    return {
                        success: false,
                        reason: 'no_bets_found'
                    };
                }

                return {
                    success: true,
                    data: slippage
                };
            }
            """,
            order_id
        )

        if result.get('success'):
            data = result.get('data')
            logger.info(f"✅ Slippage: {data.get('avg_slippage_pct')} for order {order_id}")
            return data
        else:
            logger.warning(f"⚠️ No slippage data: {result.get('reason')}")
            return None

    except Exception as e:
        logger.error(f"❌ Exception in check_order_slippage: {e}")
        return None


async def get_bet_by_id(
    page,
    bet_id: str
) -> Dict[str, Any]:
    """
    Get bet by ID

    Args:
        page: Playwright Page object
        bet_id: Bet ID

    Returns:
        Bet data with slippage
    """
    try:
        result = await page.evaluate(
            """
            (bet_id) => {
                if (!window.queryData || !window.queryData.queryBetById) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                const bet = window.queryData.queryBetById(bet_id);

                if (!bet) {
                    return {
                        success: false,
                        reason: 'bet_not_found'
                    };
                }

                return {
                    success: true,
                    data: bet
                };
            }
            """,
            bet_id
        )

        if result.get('success'):
            logger.info(f"✅ Bet found: {bet_id}")
            return result.get('data')
        else:
            logger.warning(f"⚠️ Bet not found: {bet_id}")
            return None

    except Exception as e:
        logger.error(f"❌ Exception in get_bet_by_id: {e}")
        return None


async def get_bets_by_order(
    page,
    order_id: str
) -> List[Dict[str, Any]]:
    """
    Get bets by order

    Args:
        page: Playwright Page object
        order_id: Order ID

    Returns:
        List of bet data
    """
    try:
        result = await page.evaluate(
            """
            (order_id) => {
                if (!window.queryData || !window.queryData.getBetsByOrder) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                const bets = window.queryData.getBetsByOrder(order_id);

                return {
                    success: true,
                    data: bets
                };
            }
            """,
            order_id
        )

        if result.get('success'):
            bets = result.get('data', [])
            logger.info(f"✅ Found {len(bets)} bets for order: {order_id}")
            return bets
        else:
            logger.warning(f"⚠️ Query failed: {result.get('reason')}")
            return []

    except Exception as e:
        logger.error(f"❌ Exception in get_bets_by_order: {e}")
        return []


async def get_order_bet_stats(page) -> Dict[str, Any]:
    """
    Get statistics for orders and bets

    Returns:
        {
            'orders': {
                'total_orders': 10,
                'total_events': 5,
                'by_status': [
                    {'status': 'OPEN', 'count': 3},
                    {'status': 'FINISHED', 'count': 7}
                ]
            },
            'bets': {
                'total_bets': 15,
                'total_bookies': 2,
                'by_status': [...]
            },
            'handlers': {
                'order_handler': {...},
                'bet_handler': {...}
            }
        }
    """
    try:
        result = await page.evaluate(
            """
            () => {
                if (!window.queryData || !window.queryData.getOrderBetStats) {
                    return {
                        success: false,
                        reason: 'query_function_not_available'
                    };
                }

                const stats = window.queryData.getOrderBetStats();

                return {
                    success: true,
                    data: stats
                };
            }
            """
        )

        if result.get('success'):
            stats = result.get('data')
            logger.info(f"📊 Order/Bet Stats:")
            logger.info(f"  - Orders: {stats.get('orders', {}).get('total_orders', 0)}")
            logger.info(f"  - Bets: {stats.get('bets', {}).get('total_bets', 0)}")
            return stats
        else:
            logger.warning(f"⚠️ Stats query failed: {result.get('reason')}")
            return {}

    except Exception as e:
        logger.error(f"❌ Exception in get_order_bet_stats: {e}")
        return {}
