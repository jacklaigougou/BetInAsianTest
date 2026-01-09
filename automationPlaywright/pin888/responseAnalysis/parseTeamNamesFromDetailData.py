"""
PIN888 平台 - 从 EVENTS_DETAIL_EURO 数据中解析标准球队名称
"""


def parse_team_names_from_detail_data(detail_data):
    """
    从 EVENTS_DETAIL_EURO 订阅返回的详细数据中提取 PIN888 标准球队名称

    Args:
        detail_data: window.___detailFullOdds 数据 (包含 normal 对象)
                    数据样本参考: src/automation/handlers/pin888/response/allDetails.json

    Returns:
        dict: 成功返回 {
            'pin888_home_name': str,  # PIN888 的标准主队名
            'pin888_away_name': str   # PIN888 的标准客队名
        }
        None: 解析失败或数据不完整
    """
    try:
        if not detail_data:
            print(f"⚠️ [PIN888 解析] detail_data 为空")
            return None

        # 获取 normal 对象
        normal = detail_data.get('normal')
        if not normal:
            print(f"⚠️ [PIN888 解析] detail_data 中没有 normal 字段")
            return None

        # 获取 participants 数组
        participants = normal.get('participants', [])
        if not participants or len(participants) < 2:
            print(f"⚠️ [PIN888 解析] participants 数据不完整，长度: {len(participants)}")
            return None
        matchStateType = normal.get('matchStateType', {})
      
        
        

        # 查找主队和客队
        home_participant = None
        away_participant = None

        for participant in participants:
            participant_type = participant.get('type', '')
            if participant_type == 'HOME':
                home_participant = participant
            elif participant_type == 'AWAY':
                away_participant = participant

        if not home_participant or not away_participant:
            print(f"⚠️ [PIN888 解析] 未找到完整的主客队信息")
            print(f"  home_participant: {home_participant is not None}")
            print(f"  away_participant: {away_participant is not None}")
            return None

        # 提取球队名称 (优先使用 name 字段，fallback 到 englishName)
        pin888_home_name = home_participant.get('name') or home_participant.get('englishName', '')
        pin888_away_name = away_participant.get('name') or away_participant.get('englishName', '')

        if not pin888_home_name or not pin888_away_name:
            print(f"⚠️ [PIN888 解析] 球队名称为空")
            print(f"  pin888_home_name: {pin888_home_name}")
            print(f"  pin888_away_name: {pin888_away_name}")
            return None

        print(f"✅ [PIN888 解析] 成功提取球队名称:")
        print(f"  主队: {pin888_home_name}")
        print(f"  客队: {pin888_away_name}")

        return {
            'pin888_home_name': pin888_home_name,
            'pin888_away_name': pin888_away_name,
            'matchStateType': matchStateType,
            # 'elapsed': elapsed
        }

    except Exception as e:
        print(f"❌ [PIN888 解析] 解析球队名称失败: {e}")
        import traceback
        traceback.print_exc()
        return None
