# -*- coding: utf-8 -*-
"""
Delete Betslip - 删除 Betslip
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def delete_betslip(
    page,
    betslip_id: str
) -> Dict[str, Any]:
    """
    删除 Betslip

    Args:
        page: Playwright Page 对象
        betslip_id: Betslip ID (例如: "5b0c08d6be3d44d2abe468e2a26755a5")

    Returns:
        {
            'success': True/False,
            'status': int,
            'statusText': str,
            'data': dict/None,
            'timestamp': str,
            'request': {
                'url': str,
                'method': 'DELETE',
                'betslipId': str
            }
        }

    Examples:
        >>> result = await delete_betslip(page, "5b0c08d6be3d44d2abe468e2a26755a5")
        >>> if result['success']:
        ...     print("Betslip 删除成功")
    """
    try:
        logger.info(f"删除 Betslip: {betslip_id}")

        # 调用 JS 函数
        result = await page.evaluate(
            """
            (betslipId) => {
                if (typeof window.deleteBetslip !== 'function') {
                    return {
                        success: false,
                        error: 'deleteBetslip function not available',
                        status: 0
                    };
                }
                return window.deleteBetslip(betslipId);
            }
            """,
            betslip_id
        )

        if result.get('success'):
            logger.info(f"✅ Betslip 删除成功: {betslip_id}")
        else:
            logger.error(f"❌ Betslip 删除失败: {result.get('error', 'Unknown error')}")

        return result

    except Exception as e:
        logger.error(f"❌ 删除 Betslip 异常: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'status': 0
        }
