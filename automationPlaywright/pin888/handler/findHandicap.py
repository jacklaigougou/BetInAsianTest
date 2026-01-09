def find_handicap(message,detailOdds):
    
    try:
    
        market_groups = message['market_groups']
        # detailOdds = detailOdds.get('info',{})
        # print(f'detailOdds: {detailOdds}')
        
        
        
        
        
        match message['spider_sport_type']:
            case 'soccer':
                
                match market_groups:
                    case 'normal':           
                        if not detailOdds.get('normal'):
                            return 'need refresh'
                        return soccer_normal(message,detailOdds)
                    
                    case 'specials':
                        if not detailOdds.get('specials'):
                            return 'need refresh'
                        return soccer_specials(message,detailOdds)
                    
                    case 'corners':
                        if not detailOdds.get('corners'):
                            return 'need refresh'  
                        return soccer_corners(message,detailOdds)   
                    
                    case _:
                        print(f"pin888 不支持的market_groups: {market_groups}")
                        return None

            case 'basketball':
                
                
                if not detailOdds.get('normal'):
                    print(f"❌ [PIN888] detailOdds['normal'] 为 None")
                    return 'need refresh'
                

                normal_data = detailOdds.get('normal')
                periods = normal_data.get('periods')
                if periods is None:
                    print(f"❌ [PIN888] detailOdds['normal']['periods'] 为 None")
                    return None

                data = periods.get(message['period'], {})
                message['market_group_id'] = normal_data.get('id')
                # print(data)
                if not data:
                    print(f"⚠️ [PIN888] basketball 数据为空")
                    return None
            
                return basketball(message,data)
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    return None

def soccer_normal(message,detailOdds):
    try:
        message['market_group_id'] = detailOdds.get('normal',{}).get('id',0)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(detailOdds)
        return None
    if message['period'] == '0':
        data = detailOdds['normal']['periods']['0']
    elif message['period'] == '1':
        data = detailOdds['normal']['periods']['1']
    else:
        return None
    
    # ============  这里是新加入的,因为 http请求里面是需要携带一个 类型的id 
    

   
    match message['platform_handicap']:
        
        case 'moneyLine':
            data = data['moneyLine']
            _match =message['platform_handicap_param']
            odd = data[_match]
            lineID = data['lineId']
            return {
                'odd': odd,
                'lineID': lineID,

            }
        
        case 'overUnder':
            data = data['overUnder']
            for line in data:
                if float(message['platform_handicap_param']) == float(line['points']):
                    if message['platform_direction'].lower() == 'over':
                        return {
                            'odd': line['overOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt']
                        }
                    elif message['platform_direction'].lower() == 'under':
                        return {
                            'odd': line['underOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt']
                        }
                    else:
                        return None
                else:
                    continue

            # 未匹配成功,打印所有可用盘口
            print(f"⚠️ [PIN888] overUnder 未匹配成功")
            print(f"🔍 [PIN888] 寻找参数: points={message['platform_handicap_param']}, direction={message['platform_direction']}")
            print(f"[PIN888] 📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, "
                      f"lineId={line['lineId']}, offline={line['offline']}, unavailable={line['unavailable']}")
            return None
                    
            
        case 'handicap':
            data = data['handicap']
            for line in data:
                if message['platform_direction'].lower() == 'home':
                    if float(line['homeSpread']) == float(message['platform_handicap_param']):
                        return {
                            'odd': line['homeOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt']
                        }
                elif message['platform_direction'].lower() == 'away':
                    if float(line['awaySpread']) == float(message['platform_handicap_param']):
                        return {
                            'odd': line['awayOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt']
                        }
                else:
                    continue

            # 未匹配成功,打印所有可用盘口
            print(f"⚠️ [PIN888] handicap 未匹配成功")
            print(f"🔍 寻找参数: {message['platform_direction']}Spread={message['platform_handicap_param']}")
            print(f"📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] homeSpread={line['homeSpread']}, awaySpread={line['awaySpread']}, "
                      f"homeOdds={line['homeOdds']}, awayOdds={line['awayOdds']}, "
                      f"lineId={line['lineId']}, offline={line['offline']}, unavailable={line['unavailable']}")
            return None



        case 'teamTotals':
            data = data['teamTotals']
            team_type = 'awayLines' if message['platform_direction'].lower() == 'away' else 'homeLines'
            data = data[team_type]

            for line in data:
                if message['platform_match'].lower() == 'over':
                    if float(line['points']) == float(message['platform_handicap_param']):
                        return {
                            'odd': line['overOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt']
                        }
                elif message['platform_match'].lower() == 'under':
                    if float(line['points']) == float(message['platform_handicap_param']):
                        return {
                            'odd': line['underOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt']
                        }
                else:
                    continue

            # 未匹配成功,打印所有可用盘口
            print(f"⚠️ [PIN888] teamTotals 未匹配成功")
            print(f"🔍 寻找参数: {team_type}, points={message['platform_handicap_param']}, match={message['platform_match']}")
            print(f"📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, "
                      f"lineId={line['lineId']}, offline={line['offline']}, unavailable={line['unavailable']}")
            return None
           

    
   


def soccer_specials(message,detailOdds):

    try:
        
        data = detailOdds['specials'][0]['events']
       
        for line in data:
            message['market_group_id'] = line['id']
            match message['platform_handicap'].lower():
                case 'total goals odd/even' | 'total goals odd/even 1st half' | 'total goals odd/even 2nd half':
                    if line['name'].lower() == message['platform_handicap'].lower():
                        contestants = line['contestants']
                        for contestant in contestants:
                            if message['platform_match'].lower() == contestant['n'].lower():
                                return {
                                    'odd': contestant['p'],
                                    'lineID': contestant['l'],

                                    'specials_i': contestant['i']
                                }
                            else:
                                continue


                case 'both teams to score?' | 'both teams to score? 1st half' | 'both teams to score? 2nd half' | 'both to score' | 'both to score? 1st half' | 'both to score? 2nd half' :
                    if line['name'].lower() == message['platform_handicap'].lower():
                        contestants = line['contestants']
                        for contestant in contestants:
                            if message['platform_handicap_param'].lower() == contestant['n'].lower():
                                return {
                                    'odd': contestant['p'],
                                    'lineID': contestant['l'],
                                    'specials_i': contestant['i']
                                }
                            else:
                                continue

                case 'double chance' | 'double chance 1st half' | 'double chance 2nd half':
                    if line['name'].lower() == message['platform_handicap'].lower():
                        contestants = line['contestants']
                        for contestant in contestants:
                            if message['platform_handicap_param'].lower() == contestant['n'].lower():
                                return {
                                    'odd': contestant['p'],
                                    'lineID': contestant['l'],
                                    'specials_i': contestant['i'],
                                    # 'specials_event_id':message['market_group_id']
                                }
                            else:
                                continue
                
                case 'draw no bet' | 'draw no bet 1st half' | 'draw no bet 2nd half':
                    
                    if line['name'].lower() == message['platform_handicap'].lower():
                        contestants = line['contestants']
                        for contestant in contestants:
                            if message['platform_handicap_param'].lower() == contestant['n'].lower():
                                return {
                                    'odd': contestant['p'],
                                    'lineID': contestant['l'],
                                    'specials_i': contestant['i'],
                                    'specials_event_id':message['market_group_id']
                                }
                            else:
                                continue
                    


                case _:
                    print(f"pin888 不支持的盘口: {message['platform_handicap']}")
                    return None
                   
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('返回的数据中没有 specials 项, 说明盘口没有开')
        return None





def soccer_corners(message,detailOdds):
    try:
       
        data = detailOdds.get('corners',{})
        market_group_id = data['id']
        if not data:
            print(f"⚠️ [PIN888] corners 数据为空")
            return None
        data = data['periods'].get(message['period'],{})
        if not data:
            print(f"⚠️ [PIN888] corners 数据为空")
            return None
        
        match message['platform_handicap'].lower():
            
            case 'handicap':
                data = data.get('handicap',[])
                for line in data:
                    if message['platform_direction'].lower() == 'home':
                        
                        if float(line['homeSpread']) == float(message['platform_handicap_param']):
                            return {
                                'odd': line['homeOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id':market_group_id
                            }
                    elif message['platform_direction'].lower() == 'away':
                        if float(line['awaySpread']) == float(message['platform_handicap_param']):
                            return {
                                'odd': line['awayOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                "market_group_id":market_group_id
                            }
                    else:
                        continue

                # 未匹配成功,打印所有可用盘口
                print(f"⚠️ [PIN888] corners handicap 未匹配成功")
                print(f"🔍 寻找参数: {message['platform_direction']}Spread={message['platform_handicap_param']}")
                print(f"📋 所有可用盘口 (共 {len(data)} 个):")
                for idx, line in enumerate(data, 1):
                    print(f"  [{idx}] homeSpread={line['homeSpread']}, awaySpread={line['awaySpread']}, "
                          f"homeOdds={line['homeOdds']}, awayOdds={line['awayOdds']}, lineId={line['lineId']}")
                return None

            case 'overunder':
                data = data.get('overUnder',[])
                print(data)
                for line in data:
                    if message['platform_direction'].lower() == 'over':
                        if float(line['points']) == float(message['platform_handicap_param']):
                            return {
                                'odd': line['overOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id':market_group_id
                            }
                    elif message['platform_direction'].lower() == 'under':
                        if float(line['points']) == float(message['platform_handicap_param']):
                            return {
                                'odd': line['underOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt'],
                                'market_group_id':market_group_id
                            }
                    else:
                        continue

                # 未匹配成功,打印所有可用盘口
                print(f"⚠️ [PIN888] corners overUnder 未匹配成功")
                print(f"🔍 寻找参数: points={message['platform_handicap_param']}, direction={message['platform_direction']}")
                print(f"📋 所有可用盘口 (共 {len(data)} 个):")
                for idx, line in enumerate(data, 1):
                    print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, lineId={line['lineId']}")
                return None
            case _:
                print(f"pin888 不支持的盘口: {message['platform_handicap']}")
                return None

    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    return None


def basketball(message,detailOdds):

    
    match message['platform_handicap'].lower():
        case 'handicap':
            data = detailOdds.get('handicap')
            
            if not data:
                print(f"⚠️ [PIN888] basketball handicap 数据为空")
                return None
            for line in data:
                if message['platform_direction'].lower() == 'home':
                    if float(line['homeSpread']) == float(message['platform_handicap_param']):
                        return {
                            'odd': line['homeOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt']
                        }
                    
                elif message['platform_direction'].lower() == 'away':
                    if float(line['awaySpread']) == float(message['platform_handicap_param']):
                        return {
                            'odd': line['awayOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt']
                            }
                    
            
            print(f"⚠️ [PIN888] basketball handicap 未匹配成功")
            print(f"🔍 寻找参数: {message['platform_direction']}Spread={message['platform_handicap_param']}")
            print(f"📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] homeSpread={line['homeSpread']}, awaySpread={line['awaySpread']}, "
                      f"homeOdds={line['homeOdds']}, awayOdds={line['awayOdds']}, "
                      f"lineId={line['lineId']}, offline={line['offline']}, unavailable={line['unavailable']}")
            return None
        
        case 'overunder':
         
            data = detailOdds.get('overUnder')
            if not data:
                print(f"⚠️ [PIN888] basketball overUnder 数据为空")
                return None
            for line in data:
                if message['platform_direction'].lower() == 'over':
                    if float(line['points']) == float(message['platform_handicap_param']):
                        return {
                            'odd': line['overOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt']
                        }
                elif message['platform_direction'].lower() == 'under':
                    if float(line['points']) == float(message['platform_handicap_param']):
                        return {
                            'odd': line['underOdds'],
                            'lineID': line['lineId'],
                            'isAlt': line['isAlt']
                        }
                else:
                    continue

            print(f"⚠️ [PIN888] basketball overUnder 未匹配成功")
            print(f"🔍 寻找参数: points={message['platform_handicap_param']}")
            print(f"📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, lineId={line['lineId']}")
            return None


        case 'moneyline':
         
            data = detailOdds.get('moneyLine')
            if not data:
                print(f"⚠️ [PIN888] basketball moneyLine 数据为空")
                return None
            
            if message['platform_direction'].lower() == 'home':
                return {
                        'odd': data.get('homePrice',''),
                        'lineID': data.get('lineId','')
                    }
            elif message['platform_direction'].lower() == 'away':
                return {
                    'odd': data.get('awayPrice',''),
                    'lineID': data.get('lineId','')
                }
            
            print(f"⚠️ [PIN888] basketball moneyLine 未匹配成功")
            print(f"🔍 寻找参数: {message['platform_direction']}")
            print(f"📋 所有可用盘口 (共 {len(data)} 个):")
            for idx, line in enumerate(data, 1):
                print(f"  [{idx}] homePrice={line['homePrice']}, awayPrice={line['awayPrice']}, lineId={line['lineId']}")
            return None 


        case 'teamtotals':
            teamTotalsData = detailOdds.get('teamTotals')

            if not teamTotalsData:
                print(f"⚠️ [PIN888] basketball teamTotals 数据为空")
                return None


            if message['platform_direction'].lower() == 'home':

                data = teamTotalsData.get('homeLines',{})
                for line in data:
                    if message['platform_match'].lower() == 'over':
                        if float(line['points']) == float(message['platform_handicap_param']):
                            return {
                                'odd': line['overOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt']
                            }
                    elif message['platform_match'].lower() == 'under':
                        if float(line['points']) == float(message['platform_handicap_param']):
                            return {
                                'odd': line['underOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt']
                            }
                    else:
                        continue
            elif message['platform_direction'].lower() == 'away':
                data = teamTotalsData.get('awayLines',{})
                for line in data:
                    if message['platform_match'].lower() == 'over':
                        if float(line['points']) == float(message['platform_handicap_param']):
                            return {
                                'odd': line['overOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt']
                            }
                    elif message['platform_match'].lower() == 'under':
                        if float(line['points']) == float(message['platform_handicap_param']):
                            return {
                                'odd': line['underOdds'],
                                'lineID': line['lineId'],
                                'isAlt': line['isAlt']
                            }
                    else:
                        continue

            print(f"⚠️ [PIN888] basketball teamTotals 未匹配成功")
            print(f"🔍 寻找参数: {message['platform_direction']}, points={message['platform_handicap_param']}, match={message.get('platform_match', 'N/A')}")

            # 根据 platform_direction 选择对应的盘口数据 (从原始数据中获取)
            if message['platform_direction'].lower() == 'home':
                lines = teamTotalsData.get('homeLines', [])
                team_label = "主队"
            elif message['platform_direction'].lower() == 'away':
                print(teamTotalsData)
                lines = teamTotalsData.get('awayLines', [])
                team_label = "客队"
            else:
                lines = []
                team_label = "未知"

            if lines:
                print(f"📋 {team_label}盘口 (共 {len(lines)} 个):")
                for idx, line in enumerate(lines, 1):
                    print(f"  [{idx}] points={line['points']}, over={line['overOdds']}, under={line['underOdds']}, "
                          f"lineId={line['lineId']}, isAlt={line.get('isAlt', False)}")
            else:
                print(f"📋 未找到 {team_label} 盘口数据")

            return None
