# -*- coding: utf-8 -*-
"""
BetInAsian 获取赔率
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def GetOdd(self, dispatch_message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    获取赔率

    Args:
        dispatch_message: 调度消息,包含所有必要的参数
        **kwargs: 额外参数

    Returns:
        {
            'success': bool,
            'odd': float,
            'message': str,
            'data': Any
        }
    """
    pass

async def get_event_key_by_name(self, dispatch_message: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
        由于 betinasian 目前正在维修,所以需要通过其他平台(如:SBO)的比赛名字映射到 betinasian 的比赛名字
        然后通过 betinasian 的比赛名字获取比赛ID
    """
    sport_type = dispatch_message.get('spider_sport_type')
    home_team = dispatch_message.get('spider_home')
    away_team = dispatch_message.get('spider_away')

    pass
