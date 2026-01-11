"""
PIN888 平台 - 从 AllEvents 数据中解析并匹配比赛事件
"""

from utils.leagueName import transform_league_name


def parse_event_from_all_events(all_events, spider_home, spider_away):
    """
    从 AllEvents 数据中通过球队名字匹配比赛事件

    参考 get_parsed_events 函数中的 "优先级2: 通过球队名字匹配" 逻辑

    Args:
        all_events: window.__AllEvents 数据 (包含 leagues 列表)
        spider_home: 主队名称 (来自 spider)
        spider_away: 客队名称 (来自 spider)

    Returns:
        dict: 匹配成功返回 {
            'event_id': int,       # PIN888 的比赛 ID
            'home_name': str,      # PIN888 的主队名
            'away_name': str       # PIN888 的客队名
        }
        None: 未找到匹配
    """
    try:
        if not all_events:
            print(f"⚠️ [PIN888] all_events 为空")
            return None

        if not spider_home and not spider_away:
            print(f"⚠️ [PIN888] spider_home 和 spider_away 都为空,无法匹配")
            return None
        
        isLive = all_events.get('isLive',False)
        print(f'isLive : {isLive}')
        if not isLive:
            print('all_events 数据并非实时数据')
            return None,None
     

        # 遍历 leagues
        leagues = all_events.get('leagues', [])
        # print(f'📊 [PIN888 解析] 共获取联赛 {len(leagues)} 个')

        for league in leagues:
            events = league.get('events', [])
            # print(f"📊 [PIN888 解析] 当前联赛有 {len(events)} 场比赛")

            for event in events:
                # 通过球队名字匹配
                participants = event.get('participants', [])

                if len(participants) >= 2:
                    home_participant = next((p for p in participants if p.get('type') == 'HOME'), None)
                    away_participant = next((p for p in participants if p.get('type') == 'AWAY'), None)

                    if home_participant and away_participant:
                        # 标准化球队名字
                        home_name_normalized = transform_league_name(home_participant.get('name', ''))
                        home_english_normalized = transform_league_name(home_participant.get('englishName', ''))
                        away_name_normalized = transform_league_name(away_participant.get('name', ''))
                        away_english_normalized = transform_league_name(away_participant.get('englishName', ''))

                        # 模糊匹配 (检查是否包含关键字)
                        matched = False

                        # 调试信息
                        # print(f"🔍 [PIN888 解析] 比较比赛: {home_participant.get('name', '')} vs {away_participant.get('name', '')}")
                        # print(f"  home_normalized={home_name_normalized}")
                        # print(f"  away_normalized={away_name_normalized}")

                        # if spider_home:
                        #     print(f"  搜索主队: {transform_league_name(spider_home)}")
                        # if spider_away:
                        #     print(f"  搜索客队: {transform_league_name(spider_away)}")

                        # 检查提供的主队名是否匹配比赛中的主队或客队
                        if spider_home:
                            spider_home_normalized = transform_league_name(spider_home)

                            # 主队名可能匹配比赛的主队
                            if (spider_home_normalized in home_name_normalized or
                                spider_home_normalized in home_english_normalized or
                                home_name_normalized in spider_home_normalized or
                                home_english_normalized in spider_home_normalized):
                                matched = True
                                # print(f"✅ [PIN888 解析] 主队名匹配到比赛的主队")

                            # 主队名也可能匹配比赛的客队
                            elif (spider_home_normalized in away_name_normalized or
                                  spider_home_normalized in away_english_normalized or
                                  away_name_normalized in spider_home_normalized or
                                  away_english_normalized in spider_home_normalized):
                                matched = True
                                # print(f"✅ [PIN888 解析] 主队名匹配到比赛的客队")

                        # 检查提供的客队名是否匹配比赛中的主队或客队
                        if spider_away and not matched:
                            spider_away_normalized = transform_league_name(spider_away)

                            # 客队名可能匹配比赛的客队
                            if (spider_away_normalized in away_name_normalized or
                                spider_away_normalized in away_english_normalized or
                                away_name_normalized in spider_away_normalized or
                                away_english_normalized in spider_away_normalized):
                                matched = True
                                # print(f"✅ [PIN888 解析] 客队名匹配到比赛的客队")

                            # 客队名也可能匹配比赛的主队
                            elif (spider_away_normalized in home_name_normalized or
                                  spider_away_normalized in home_english_normalized or
                                  home_name_normalized in spider_away_normalized or
                                  home_english_normalized in spider_away_normalized):
                                matched = True
                                # print(f"✅ [PIN888 解析] 客队名匹配到比赛的主队")

                        if matched:
                            home_name = home_participant.get('name', '')
                            away_name = away_participant.get('name', '')
                            event_id = event.get('id')

                            # print(f"✅ [PIN888 解析] 通过球队名匹配到比赛:")
                            # print(f"  event_id: {event_id}")
                            # print(f"  {home_name} vs {away_name}")

                            return {
                                'event_id': event_id,
                                'home_name': home_name,
                                'away_name': away_name
                            }

        # 未找到匹配
        # print(f"⚠️ [PIN888 解析] 未找到球队 {spider_home} vs {spider_away} 的比赛")
        return None

    except Exception as e:
        # print(f"❌ [PIN888 解析] 解析事件数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None
