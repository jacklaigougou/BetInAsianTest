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
        1.拿到dispatch_message 中的 sport_type, home_team, away_team
        2.对  home_team, away_team 进行清晰
        3.拿到浏览器中存储的数据,根据索引表格进行,通过sport_type ,拿到所有该运动,正在进行的所有比赛比赛
        4.进行模糊匹配.
    """
    sport_type = dispatch_message.get('spider_sport_type')
    home_team = dispatch_message.get('spider_home')
    away_team = dispatch_message.get('spider_away')

    pass
