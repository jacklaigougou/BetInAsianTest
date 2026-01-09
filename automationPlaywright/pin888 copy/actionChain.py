from automation.base import BaseActionChain
from utils import load_js_file
from automationPlaywright.pin888.handler.pom import Pin888POM
from config.settings import Settings
from core.config import config
import aiohttp
import asyncio

from utils.leagueName import transform_league_name
# from automation.mapping import Mapping
from automationPlaywright.pin888.handler.findHandicap import find_handicap
from automationPlaywright.pin888.handler.mappingBetParamsToIds import map_bet_params_to_ids
from automationPlaywright.pin888.handler.arbitrageRange import calculate_arbitrage_range
from automationPlaywright.pin888.jsCodeExecutors import subscribe_events_detail_euro, unsubscribe_events_detail_euro, subscribe_live_euro_odds
from automationPlaywright.pin888.responseAnalysis import parse_event_from_all_events, parse_team_names_from_detail_data, find_odds_from_detail_data
from automationPlaywright.pin888.responseAnalysis.findOddsWithRange import find_odds_from_detail_data_with_range
from automationPlaywright.pin888.mapping import map_handicap_full
import time
import json
import os
from datetime import datetime
from automationPlaywright.pin888.handler.timeAnalysis import analyze_remaining_time


def save_event_detail_data(event_detail_data, prefix="event_detail"):
    """
    保存 event_detail_data 到 JSON 文件

    Args:
        event_detail_data: 要保存的数据
        prefix: 文件名前缀,默认 "event_detail"

    Returns:
        str: 保存的文件路径,失败返回 None
    """
    try:
        # 创建目录
        log_dir = "logs/pin888_event_details"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 生成文件名 (使用时间戳)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        filepath = os.path.join(log_dir, filename)

        # 保存数据
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(event_detail_data, f, ensure_ascii=False, indent=2)

        print(f"📝 [PIN888] {prefix} 已保存: {filepath}")
        return filepath
    except Exception as e:
        print(f"⚠️ [PIN888] 保存 {prefix} 失败: {e}")
        return None


class ActionChain(BaseActionChain):
    """
    Pin888 平台异步 ActionChain
    所有方法改为异步,使用 Playwright 执行 JavaScript
    """
    handler_info = {}
    def __init__(self, online_platform, ws_client=None):
        self.order_record = {}

        super().__init__(online_platform, ws_client=ws_client)
        self._is_SupplementaryOrder = False
        self.PIN888_CYCLEING = True  # 补单循环控制开关
        self.pom = Pin888POM(self.page)
        self.count_get_ws_result = 0  # 计数器,避免日志刷屏
        self.connect_count = 0

        # 为当前 handler 初始化存储空间
        if self.handler_name not in ActionChain.handler_info:
            ActionChain.handler_info[self.handler_name] = {
                'balance': None
            }





    async def SupplementaryOrder(self, msg, logger=None):
        """
        异步下注订单后处理
        当另一边下注成功后,重新检查盘口并尝试下注
        使用 while 循环代替递归,支持区间补单、赔率变化检查和最优金额计算
        """
        self._is_SupplementaryOrder = True
        order_id = msg.get('order_id')
        if not order_id:
            print(f"[{self.handler_name}] ❌ [PIN888] 缺少必要参数 order_id")
            return None

        bet_data = msg['bet_data']
        record = self.order_record.get(order_id)
        if not record:
            print(f"[{self.handler_name}] ❌ [PIN888] 未找到订单记录: {order_id}")
            return None

        # 检查重试次数
        retry_count = record.get('retry_count', 0)
        max_retry = config.get_max_retry_count()
        
        # 从record中获取必要信息
        pin888_standard_home_name = record.get('pin888_standard_home_name', '') or msg.get('fail_platform_home')
        pin888_standard_away_name = record.get('pin888_standard_away_name', '') or msg.get('fail_platform_away')

        print(f"[{self.handler_name}] pin888_standard_home_name: {pin888_standard_home_name}")
        print(f"[{self.handler_name}] pin888_standard_away_name: {pin888_standard_away_name}")

        event_id = record.get('event_id', '') or msg.get('event_id')
        sportId = record.get('sportId', '') or msg.get('sportsID')
        sport_type = record.get('sport_type')
        period_num = record.get('period_num', 0) or msg.get('periodNum')
        spider_handicap = record.get('spider_handicap')

        # 映射后的参数 (用于查找赔率)
        mapped_market = record['mapped_market']
        mapped_handicap = record['mapped_handicap']
        mapped_handicap_param = record['mapped_handicap_param']
        mapped_period = record['mapped_period']
        mapped_direction = record['mapped_direction']
        mapped_match = record['mapped_match']
        remaining_seconds = record.get('remaining_seconds',600)

        # 从保存的原始 msg 中获取 spider_* 参数 (用于 map_bet_params_to_ids)
        original_msg = record.get('msg', {})
        spider_handicap = record['spider_handicap']
        spider_period = record['spider_period']
        spider_sport_type = record['spider_sport_type']


        bet_data = msg
        if not (pin888_standard_home_name and pin888_standard_away_name and event_id and sportId is not None):
            print(f"[{self.handler_name}] ❌ [PIN888] 缺少必要信息,无法执行补单")
            return None

        # ==================== 进入 while 循环 ====================
        _time = time.time()
        print(f'补单时间为: {remaining_seconds} 秒')
        if not remaining_seconds:
            print(f"[{self.handler_name}] ❌ [PIN888] 未能获取剩余时间,使用默认值 600 秒")
            print(f'record: {record}')
            remaining_seconds = 900


        while time.time() - _time < remaining_seconds :

            # 检查 PIN888_CYCLEING 标志
            if 'PIN888_CYCLEING' not in self.online_platform:
                self.online_platform['PIN888_CYCLEING'] = True

            if self.online_platform['PIN888_CYCLEING'] == False:
                print(f"[{self.handler_name}] ⛔ PIN888_CYCLEING 已关闭,退出补单循环")
                self.online_platform['PIN888_CYCLEING'] = True  # 重置为 True
                break

            print(f"[{self.handler_name}] 🔄 [PIN888] 第 {retry_count + 1}/{max_retry} 次尝试补单...")
            # print(f"[{self.handler_name}] pin888_standard_home_name: {pin888_standard_home_name}")
            # print(f"[{self.handler_name}] pin888_standard_away_name: {pin888_standard_away_name}")
            pass_time = time.time() - _time
            print(f'补单总时间为 {remaining_seconds} 秒 ,已经执行了 {pass_time} 秒')
            # 第一步: 获取 event_id 
            event_id, event_detail_data = await self.get_event_id(
                sportId=sportId,
                period_num=period_num,
                spider_home=pin888_standard_home_name,
                spider_away=pin888_standard_away_name,
                event_id=event_id
            )



            
            pin888_standard_home_name = record.get('pin888_standard_home_name', '') or msg.get('fail_platform_home')
            pin888_standard_away_name = record.get('pin888_standard_away_name', '') or msg.get('fail_platform_away')
            
        
            if not event_detail_data:
                retry_count += 1
                continue

            if not event_id:
                print(f"[{self.handler_name}] ❌ [PIN888] 获取 event_id 失败,继续尝试...")
                await asyncio.sleep(2)
                retry_count += 1
                continue
            
            
            success_platform_handicap = bet_data.get('success_platform_handicap', '')
            success_platform_handicap_param = bet_data.get('success_platform_handicap_param', '')
            
            # print(f'success_platform_handicap {success_platform_handicap}')
            # 判断是否是 Draw No Bet
            success_platform_handicap_lower = success_platform_handicap.lower()
            is_draw_no_bet = "draw no bet" in success_platform_handicap_lower

            # Total 类判断
            is_total = "total" in success_platform_handicap_lower and ("over" in success_platform_handicap_lower or "under" in success_platform_handicap_lower)

            # Handicap 类判断 (排除 Draw No Bet)
            is_handicap = (
                "handicap" in success_platform_handicap_lower
                and ("handicap1" in success_platform_handicap_lower or "handicap2" in success_platform_handicap_lower)
                and not is_draw_no_bet
            )
            # 第四步: 根据盘口类型选择查找方式
            if is_total or is_handicap:
                # 使用区间补单
                
                arbitrage_condition = calculate_arbitrage_range(
                    success_platform_handicap=success_platform_handicap,
                    success_platform_handicap_param=success_platform_handicap_param
                )
                if not arbitrage_condition:
                    print(f'[{self.handler_name}] ❌ [PIN888] 补单区间计算失败')
                    await unsubscribe_events_detail_euro(self.page, event_id)
                    continue

                # 使用区间查找函数 (参数与 GetOdd 保持一致,只是用区间匹配)
                odds_result = find_odds_from_detail_data_with_range(
                    sport_type=sport_type,
                    market_group=mapped_market,
                    platform_handicap=mapped_handicap,  # ✅ 使用映射后的盘口名
                    platform_direction=mapped_direction,
                    platform_match=mapped_match,
                    period=mapped_period,
                    detail_odds=event_detail_data,
                    range_condition=arbitrage_condition
                )

                if odds_result == 'need refresh' or not odds_result:
                    print(f"[{self.handler_name}] ⚠️ [PIN888] 需要刷新详细赔率数据")
                    await unsubscribe_events_detail_euro(self.page, event_id)
                    await asyncio.sleep(2)
                    continue



                # 打印匹配到的参数值
                matched_param = odds_result.get('matched_param')
                print(f"[{self.handler_name}] ✅ [PIN888] 区间补单成功匹配: {mapped_handicap} {mapped_direction} {matched_param}")

            else:
                # 使用精确匹配 (参数与 GetOdd 保持一致)
                odds_result = find_odds_from_detail_data(
                    sport_type=sport_type,
                    market_group=mapped_market,
                    platform_handicap=mapped_handicap,  # ✅ 使用映射后的盘口名
                    platform_handicap_param=mapped_handicap_param,
                    platform_direction=mapped_direction,
                    platform_match=mapped_match,
                    period=mapped_period,
                    detail_odds=event_detail_data
                )

                if odds_result == 'need refresh':
                    print(f"[{self.handler_name}] ⚠️ [PIN888] 需要刷新详细赔率数据")
                    await unsubscribe_events_detail_euro(self.page, event_id)
                    await asyncio.sleep(2)
                    continue

                if not odds_result:
                    print(f"[{self.handler_name}] ❌ [PIN888] 未能从详细赔率数据中找到匹配的赔率")
                    await unsubscribe_events_detail_euro(self.page, event_id)
                    await asyncio.sleep(2)
                    continue
                
            
            # 从解析结果中提取字段
            parsed_odd = odds_result.get('odd')
            parsed_lineID = odds_result.get('lineID')
            parsed_market_group_id = odds_result.get('market_group_id')
            parsed_isAlt = odds_result.get('isAlt')
            parsed_specials_i = odds_result.get('specials_i')
            parsed_specials_event_id = odds_result.get('specials_event_id')

            print(f"[{self.handler_name}] 📊 [PIN888] 提取赔率字段:")
            print(f"[{self.handler_name}]   parsed_odd: {parsed_odd}")
            print(f"[{self.handler_name}]   parsed_lineID: {parsed_lineID}")
            print(f"[{self.handler_name}]   parsed_market_group_id: {parsed_market_group_id}")
            print(f"[{self.handler_name}]   parsed_isAlt: {parsed_isAlt}")
            print(f"[{self.handler_name}]   parsed_specials_i: {parsed_specials_i}")
            print(f"[{self.handler_name}]   parsed_specials_event_id: {parsed_specials_event_id}")

            # ==================== 7. 赔率变化检查 (新增) ====================
            fail_platform_final_odd = bet_data.get('fail_platform_final_odd')  # 对手失败时的赔率(我方初始赔率)
            current_odds = parsed_odd  # 当前赔率
            if fail_platform_final_odd and current_odds:
                try:
                    fail_odds = float(fail_platform_final_odd)
                    new_odds_float = float(current_odds)

                    # 计算赔率变化百分比
                    odds_change_percent = ((new_odds_float - fail_odds) / fail_odds) * 100

                    # 从配置单例获取赔率下降阈值
                    odds_drop_threshold = config.get_odds_drop_threshold()
                    if odds_change_percent < -odds_drop_threshold:
                        # 赔率下降超过阈值
                        print(f"[{self.handler_name}] ⚠️ [PIN888] 赔率下降 {abs(odds_change_percent):.2f}% 超过阈值 {odds_drop_threshold}%,继续等待更好的赔率..")
                        await self._send_message_to_electron(f"[PIN888] 赔率下降{abs(odds_change_percent):.2f}% 超过阈值,继续等待")
                        await unsubscribe_events_detail_euro(self.page, event_id)
                        await asyncio.sleep(2)
                        continue  # 继续循环,等待下一次检查

                    elif odds_change_percent < 0:
                        # 赔率下降但在可接受范围内
                        print(f"[{self.handler_name}] ✅ [PIN888] 赔率下降 {abs(odds_change_percent):.2f}% 在可接受范围内")
                    else:
                        # 赔率上升,更好的机会
                        print(f"[{self.handler_name}] ✅ [PIN888] 赔率上升 {odds_change_percent:.2f}%")

                except Exception as e:
                    print(f"[{self.handler_name}] ⚠️ [PIN888] 赔率变化检查失败: {e}, 继续下注")
           
            # ==================== 8. 计算最优下注金额 (新增) ====================
            opponent_amount = bet_data.get('success_platform_final_bet')
            opponent_odds = bet_data.get('success_platform_final_odd')
            our_odds = parsed_odd

            if opponent_amount and opponent_odds and our_odds:
                # 有对手信息,计算最优套利金额
                try:
                    from automationPlaywright.sportsbet.executors.executor_4 import calculate_optimal_betting_amount

                    optimal_amount = calculate_optimal_betting_amount(
                        opponent_amount=float(opponent_amount),
                        opponent_odds=float(opponent_odds),
                        our_odds=float(our_odds)
                    )

                    betting_amount = round(optimal_amount, 1)  # 保留一位小数
                    await self._send_message_to_electron(f"[PIN888] 套利计算: 对手${opponent_amount}@{opponent_odds}, 最优金额${betting_amount}")

                except Exception as e:
                    print(f"[{self.handler_name}] ⚠️ [PIN888] 套利金额计算失败: {e}, 使用原金额")
                    betting_amount = record.get('betting_amount', msg.get('betting_amount'))
            else:
                # 没有对手信息,使用原金额
                betting_amount = record.get('betting_amount', msg.get('betting_amount'))
                print(f"[{self.handler_name}] 💰 [原始金额]: ${betting_amount}")

            
            
            # =====================第三步:http请求询问盘口是否可用 ==============================
            # 1.组装参数 - 使用原始参数(与 GetOdd 保持一致)
            mapping_result = map_bet_params_to_ids(
                sport_type=spider_sport_type,
                handicap=spider_handicap,
                period=spider_period,
                direction=mapped_direction,
                match=mapped_match,
                handicap_param=mapped_handicap_param,
                line_id=parsed_lineID,
                market_group_id=parsed_market_group_id,
                is_alt=parsed_isAlt if parsed_isAlt else False,
                specials_i=parsed_specials_i if parsed_specials_i else 0,
                specials_event_id=parsed_specials_event_id if parsed_specials_event_id else 0
            )
            
            if not mapping_result:
                print(f"[{self.handler_name}] ❌ [PIN888] 映射失败")
                await unsubscribe_events_detail_euro(self.page, event_id)
                await asyncio.sleep(2)
                continue
            oddsID = mapping_result['oddsID']
            oddsSelectionsType = mapping_result['oddsSelectionsType']
            selectionID = mapping_result['selectionID']

            # 2.发送http请求
            response = await self.RequestAllOddsSelections(oddsID, selectionID, oddsSelectionsType)
            if not response:
                print(f"[{self.handler_name}] ❌ [PIN888] 请求 [添加订单] 失败")
                await unsubscribe_events_detail_euro(self.page, event_id)
                await asyncio.sleep(2)
                continue
            
            try:
                response_data = json.loads(response['response'])
                if not response_data or len(response_data) == 0:
                    print(f"[{self.handler_name}] ❌ [PIN888] [添加订单] 响应数据为空")
                    await unsubscribe_events_detail_euro(self.page, event_id)
                    await asyncio.sleep(2)
                    continue

                data = response_data[0]

                # 提取响应中的 selectionId
                response_selection_id = data.get('selectionId')
                odds_id = data.get('oddsId')
                odds = data.get('odds') or data.get('odd')  # 尝试 'odds' 和 'odd'
                max_stake = data.get('maxStake')
                status = data.get('status')

                # print(f'[pin888] 响应状态: {status}')
                if status == 'UNAVAILABLE':
                    print(f'[{self.handler_name}] [pin888] [添加订单]成功,但已封盘,不能下单')
                    await self._send_message_to_electron('[pin888] [添加订单]成功,但已封盘,不能下单')
                    await unsubscribe_events_detail_euro(self.page, event_id)
                    await asyncio.sleep(2)
                    continue


                if not oddsID or odds is None:
                    await self._send_message_to_electron('[pin888] [添加订单]成功,但回复数据不完整')
                    await unsubscribe_events_detail_euro(self.page, event_id)
                    await asyncio.sleep(2)
                    continue

            except Exception as e:
                print(f"[{self.handler_name}] {e}")
                

            record['selectionId'] = response_selection_id
            record['odds'] = odds
            record['oddsId'] = odds_id

            # 10. 重新执行下注
            print(f"[{self.handler_name}] 🔄 [PIN888] 使用新的盘口数据重新下注...")
            print(f"[{self.handler_name}]   下注金额: ${betting_amount}")

            retry_msg = {
                'order_id': order_id,
                'betting_amount': betting_amount
            }
            try:
                result = await self.BettingOrder(retry_msg)
            except Exception as e:
                print(f"[{self.handler_name}] ❌ [PIN888] 重新下注失败: {e}")
                asyncio.sleep(2)
                await unsubscribe_events_detail_euro(self.page, event_id)
                continue
            
            if not result:
                asyncio.sleep(2)
                await unsubscribe_events_detail_euro(self.page, event_id)
                continue

            await unsubscribe_events_detail_euro(self.page, event_id)

            # 11. 检查下注结果
            if result.get('success') == True :
                print(f"[{self.handler_name}] ✅ [PIN888] 重新下注成功")
                supplement_order_message = {
                    "type": "supplement_order",
                    "from": "automation",
                    "to": "dispatch",
                    "data": {
                        "order_id": order_id,
                        "handler_name": self.handler_name,
                        "betting_amount": betting_amount,
                        "betting_odd": odds,
                        "betting_success": True,
                        "ticket_id": result.get('ticket_id'),
                        "is_supplementary_order": self._is_SupplementaryOrder,
                    }
                }
                await self.ws_client.send(supplement_order_message)
                await self._send_message_to_electron(f"[{self.handler_name}] [PIN888] 补单:重新下注成功,订单号: {result.get('ticket_id')},赔率: {odds},金额: {betting_amount}")
            
                return True
            else:
                print(f"[{self.handler_name}] ⚠️ [PIN888] 下注失败,继续重试...")
                retry_count += 1
                record['retry_count'] = retry_count  # 更新记录中的重试次数
                if retry_count >= max_retry:
                    print(f"[{self.handler_name}] ❌ [PIN888] 已达到最大重试次数 {max_retry}")
                    supplement_order_message = {
                        "type": "supplement_order_failed",
                        "from": "automation",
                        "to": "dispatch",
                        "data": {
                            "order_id": order_id,
                            "handler_name": self.handler_name,
                            'result': 'retry_count_max',
                            "is_supplementary_order": self._is_SupplementaryOrder,
                        }
                    }
                    await self.ws_client.send(supplement_order_message)
                    await self._send_message_to_electron(f"[PIN888] 已到达最大重试次数,补单彻底失败")
                    return None
                
                await asyncio.sleep(2)
                continue  # 继续循环而非递归

        supplement_order_message = {
                        "type": "supplement_order_failed",
                        "from": "automation",
                        "to": "dispatch",
                        "data": {
                            "order_id": order_id,
                            "handler_name": self.handler_name,
                            'result': 'timeout',
                            "is_supplementary_order": self._is_SupplementaryOrder,
                        }
                    }
        await self.ws_client.send(supplement_order_message)
        print(f"[{self.handler_name}] ❌ [PIN888] 补单失败:超时")
        await self._send_message_to_electron(f"[{self.handler_name}] [PIN888] 补单失败:超时")
        return None


    async def BettingOrder(self, msg, logger=None):
        """
        异步下注订单

        Args:
            msg: 消息数据
            logger: 日志对象

        Returns:
            下注结果
        """
        bet_start_time = time.time()  # 开始计时

        order_id = msg.get('order_id','')
        if not order_id:
            print(f"[{self.handler_name}] ❌ [PIN888] 缺少必要参数 order_id")
            return None

        record = self.order_record.get(order_id)
        if not record:
            print(f"[{self.handler_name}] ❌ [PIN888] 未找到订单记录: {order_id}")
            return None

        # 获取美金金额并转换为XRP
        bet_amount_usd = float(msg.get('betting_amount', 0))
        if not bet_amount_usd or bet_amount_usd <= 0:
            print(f"[{self.handler_name}] ❌ [PIN888] bet_amount 为空或无效: {bet_amount_usd}")
            return None
        

        self.order_record[order_id]['betting_amount'] = bet_amount_usd
        

        print(f"[{self.handler_name}] 💰 [PIN888] 下注金额: {bet_amount_usd} USD")
        # 获取余额并检查 (从 online_platform 读取)
        # balance = self.online_platform.get('balance')
        balance = self.online_platform.get('balance')
        if balance is None:
            print(f"[{self.handler_name}] ❌ [PIN888] 获取余额失败")
            # balance = 10
            return None

        balance = float(balance)
        print(f"[{self.handler_name}] 💰 [PIN888]  下注金额: {bet_amount_usd:.1f} XRP")

        if balance < bet_amount_usd:
            import math
            # 向下取整到1位小数,确保不超过余额
            bet_amount_usd = math.floor(balance * 10) / 10
            print(f"[{self.handler_name}] ⚠️ [PIN888] 余额不足,调整下注金额为: {bet_amount_usd} XRP (真实余额: {balance})")

        bet_amount = bet_amount_usd

        # bet_amount = 1
        # 加载 JS 模板
        js_template = load_js_file(
            file_name='RequestBuyV2.js',
            platform_name='pin888'
        )

        if not js_template:
            print(f"[{self.handler_name}] ❌ [PIN888] 加载 RequestBuyV2.js 失败")
            return None

        # 替换占位符
        js_code = js_template.replace('__STAKE__', str(bet_amount))
        js_code = js_code.replace('__ODDS__', str(record['odds']))
        js_code = js_code.replace('__ODDS_ID__', str(record['oddsId']))
        js_code = js_code.replace('__SELECTION_ID__', str(record['selectionId']))

        print(f"[{self.handler_name}] ✅ [PIN888] 发送下注请求: order_id={order_id}, stake={bet_amount}, odds={record['odds']}")
        await self._send_message_to_electron(f"✅ [PIN888] 发送下注请求: order_id={order_id}, stake={bet_amount}, odds={record['odds']}")
        # 执行 JS 代码
        try:
            wrapped_code = f"(() => {{ {js_code} }})()"
            response = await self.page.evaluate(wrapped_code)

            if not response:
                print(f"[{self.handler_name}] ❌ [PIN888] 下注请求返回空响应")
                await self._send_message_to_electron(f"[PIN888] 下注请求返回空响应")
                return None

            if response.get('error'):
                print(f"[{self.handler_name}] ❌ [PIN888] 下注失败: {response.get('error')}")
                await self._send_message_to_electron(f"[PIN888] 下注失败: {response.get('error')}")
                return None

            if response.get('status') != 200:
                print(f"[{self.handler_name}] ❌ [PIN888] 下注失败，HTTP状态码: {response.get('status')}")
                print(f"[{self.handler_name}] 响应: {json.dumps(response, indent=2)}")
                await self._send_message_to_electron(f"[PIN888] 下注失败，HTTP状态码: {response.get('status')}")
                return None

            # 解析 response.response 字段（JSON字符串或数组）
            try:
                response_content = response.get('response', '{}')

                # 尝试解析为 JSON
                if isinstance(response_content, str):
                    response_data = json.loads(response_content)
                else:
                    response_data = response_content

                # 如果 response_data 是字典且包含 'response' 键,提取内层数组
                if isinstance(response_data, dict) and 'response' in response_data:
                    response_data = response_data['response']   
                    

                # 检查是否有错误码 (只有当response_data是字典时才检查)
                error_code = None
                error_message = None
                # if isinstance(response_data, dict):
                #     error_code = response_data.get('errorCode')
                #     error_message = response_data.get('errorMessage')
                #     await self._send_message_to_electron(f"[PIN888] 下注失败 - 错误码: {error_code}, 错误信息: {error_message}")

                if error_code or error_message:
                    print(f"[{self.handler_name}] ❌ [PIN888] 下注失败")
                    print(f"[{self.handler_name}]   错误代码: {error_code}")
                    print(f"[{self.handler_name}]   错误信息: {error_message}")
                    print(f"[{self.handler_name}]   完整响应: {json.dumps(response, indent=2, ensure_ascii=False)}")

                    # 发送WebSocket日志: 下注失败
                    
                    await self._send_message_to_electron(f"[PIN888] 下注失败 - 错误码: {error_code}, 错误信息: {error_message}")
                       

                    # 返回错误信息
                    return {
                        'success': False,
                        'error_code': error_code,
                        'error_message': error_message
                    }

                # 检查是否是数组格式的成功响应
                if isinstance(response_data, list) and len(response_data) > 0:
                    bet_result = response_data[0]
                    wager_id = bet_result.get('wagerId')
                    odds = bet_result.get('odds')
                    status = bet_result.get('status')

                    if status == 'ACCEPTED':
                        print(f"[{self.handler_name}] ✅ [PIN888] 下注成功")
                        print(f"[{self.handler_name}]   Wager ID: {wager_id}")
                        print(f"[{self.handler_name}]   赔率: {odds}")
                        print(f"[{self.handler_name}]   状态: {status}")

                        # 计算下注执行时间
                        bet_duration = time.time() - bet_start_time
                        print(f"[{self.handler_name}] ⏱️ [PIN888] BettingOrder 执行时间: {bet_duration:.3f}秒")

                        # 发送WebSocket日志: 下注成功
                        await self._send_message_to_electron(f"[PIN888] 下注成功 - WagerID: {wager_id}, 状态: {status}, 耗时: {bet_duration:.3f}秒")
                        await self._send_message_to_electron(f"[PIN888] 下注成功 - 金额：${bet_amount},  赔率： {odds}")

                        # 重新获取最新余额
                        new_balance = await self.GetBalanceByRequest()
                        if new_balance:
                            # 更新到 online_platform
                            self.online_platform['balance'] = new_balance

                            # 发送余额更新给 dispatch
                            if self.ws_client:
                                try:
                                    await self.ws_client.send({
                                        'type': 'balance_update',
                                        'from': 'automation',
                                        'to': 'dispatch',
                                        'data': {
                                            'handler_name': self.handler_name,
                                            'balance': new_balance
                                        }
                                    })
                                    print(f"[{self.handler_name}] 📤 [PIN888] 余额已更新并发送: {new_balance}")
                                except Exception as e:
                                    print(f"[{self.handler_name}] ⚠️ [PIN888] 发送余额失败: {e}")

                        # 返回成功信息
                        return {
                            'success': True,
                            'ticket_id': wager_id,
                            'betting_odd': odds,
                            'betting_amount': bet_amount_usd,
                            'status': status,
                            'is_supplementary_order': self._is_SupplementaryOrder,
                        }
                    elif status == 'PENDING_ACCEPTANCE':
                        print(f'[{self.handler_name}] 状态为 PENDING_ACCEPTANCE ....')
                        await self._send_message_to_electron(f"[PIN888] PENDING_ACCEPTANCE ....")

                        await asyncio.sleep(1)
                        js_template = load_js_file(
                            file_name='Request_myBets.js',
                            platform_name='pin888'
                        )
                        if not js_template:
                            print(f"[{self.handler_name}] ❌ [PIN888] 加载 Request_myBets.js 失败")
                            return None

                        wrapped_code = f"(() => {{ {js_template} }})()"

                        # 定义统一的响应数据解析函数
                        def parse_my_bets_response(raw_response):
                            """解析 my_bets 响应数据,返回投注记录数组"""
                            print(f"[{self.handler_name}] 📥 [DEBUG] 原始响应类型: {type(raw_response)}")

                            # 情况1: 直接是数组 (最理想)
                            if isinstance(raw_response, list):
                                print(f"[{self.handler_name}] ✅ [DEBUG] 直接获得数组,长度: {len(raw_response)}")
                                return raw_response

                            # 情况2: 是字典,包含 'response' 字段
                            if isinstance(raw_response, dict) and 'response' in raw_response:
                                response_value = raw_response['response']
                                print(f"[{self.handler_name}] 📦 [DEBUG] 从字典中提取 response 字段,类型: {type(response_value)}")

                                # 如果是字符串,尝试解析为 JSON
                                if isinstance(response_value, str):
                                    try:
                                        parsed = json.loads(response_value)
                                        print(f"[{self.handler_name}] ✅ [DEBUG] JSON 解析成功,类型: {type(parsed)}")
                                        return parsed if isinstance(parsed, list) else []
                                    except json.JSONDecodeError:
                                        print(f"[{self.handler_name}] ❌ [DEBUG] JSON 解析失败")
                                        return []

                                # 如果已经是数组或对象,直接返回
                                return response_value if isinstance(response_value, list) else []

                            # 情况3: 其他格式,返回空数组
                            print(f"[{self.handler_name}] ⚠️ [DEBUG] 无法识别的格式,返回空数组")
                            return []

                        # 第一次获取投注记录
                        my_bets_response = await self.page.evaluate(wrapped_code)
                        my_bets_response = parse_my_bets_response(my_bets_response)
                        print(f"[{self.handler_name}] 📊 [DEBUG] 初次获取投注记录数: {len(my_bets_response)}")

                        num = 0
                        while num < 30:
                            print(f"[{self.handler_name}] 🔄 [轮询 {num+1}/30] 检查投注状态...")

                            # 遍历所有投注记录
                            for bet in my_bets_response:
                                if not isinstance(bet, list) or len(bet) < 12:
                                    print(f"[{self.handler_name}] ⚠️ [DEBUG] 跳过无效记录,类型: {type(bet)}")
                                    continue

                                print(f"[{self.handler_name}] 📝 [DEBUG] 检查投注记录: WagerID={bet[0]}, 状态={bet[11] if len(bet) > 11 else 'unknown'}")

                                # 检查是否是当前的 wager_id
                                if str(bet[0]) == str(wager_id):
                                    print(f"[{self.handler_name}] ✅ [找到匹配] WagerID: {wager_id}")

                                    # 获取状态字段 (索引 11)
                                    bet_status = bet[11] if len(bet) > 11 else ""
                                    print(f"[{self.handler_name}] 📊 [状态检查] bet_status = {bet_status}, 类型 = {type(bet_status)}, repr = {repr(bet_status)}")

                                    # 1. 判断是否为 PENDING
                                    print(f"[{self.handler_name}] 🔍 [判断] bet_status == 'PENDING': {bet_status == 'PENDING'}")

                                    if bet_status == 'PENDING':
                                        print(f"[{self.handler_name}] ⏳ [PENDING] 订单还在处理中,继续等待...")
                                        await asyncio.sleep(1)
                                        break  # 跳出 for 循环,继续 while 循环等待

                                    # 2. 不是 PENDING,说明已经结算了
                                    # 3. 只有在非 PENDING 状态下,验证是否有 reject
                                    has_rejected = any('rejected' in str(value).lower() for value in bet)

                                    if has_rejected:
                                        # 整个数组中发现 rejected,判定为失败
                                        print(f"[{self.handler_name}] ❌ [PIN888] 下注失败 - 数组中发现 'rejected'")
                                        print(f"[{self.handler_name}]    完整记录: {bet}")
                                        await self._send_message_to_electron(f"[PIN888] 下注失败 - WagerID: {wager_id}, 状态: Rejected")
                                        return None
                                    else:
                                        # 整个数组中都没有 rejected,判定为成功
                                        print(f"[{self.handler_name}] ✅ [PIN888] 下注成功 - 数组中无 'rejected',状态: {bet_status}")
                                        await self._send_message_to_electron(f"[PIN888] 下注成功 - WagerID: {wager_id}, 状态: {bet_status}")

                                        # 重新获取最新余额
                                        new_balance = await self.GetBalanceByRequest()
                                        if new_balance:
                                            # 更新到 online_platform
                                            self.online_platform['balance'] = new_balance

                                            # 发送余额更新给 dispatch
                                            if self.ws_client:
                                                try:
                                                    await self.ws_client.send({
                                                        'type': 'balance_update',
                                                        'from': 'automation',
                                                        'to': 'dispatch',
                                                        'data': {
                                                            'handler_name': self.handler_name,
                                                            'balance': new_balance
                                                        }
                                                    })
                                                    print(f"[{self.handler_name}] 📤 [PIN888] 余额已更新并发送: {new_balance}")
                                                except Exception as e:
                                                    print(f"[{self.handler_name}] ⚠️ [PIN888] 发送余额失败: {e}")

                                        return {
                                            'success': True,
                                            'ticket_id': wager_id,
                                            'betting_odd': bet[9] if len(bet) > 9 else odds,
                                            'betting_amount': bet_amount_usd,
                                            'status': bet_status,
                                            'is_supplementary_order': self._is_SupplementaryOrder,
                                        }

                            # 未找到匹配记录,继续等待
                            num += 1
                            if num >= 30:
                                print(f"[{self.handler_name}] ⏱️ [超时] 已等待 30 次,仍未找到 WagerID: {wager_id}")
                                await asyncio.sleep(1)
                                break

                            await asyncio.sleep(1)

                            # 重新获取投注记录
                            raw_response = await self.page.evaluate(wrapped_code)
                            my_bets_response = parse_my_bets_response(raw_response)
                            print(f"[{self.handler_name}] 🔄 [刷新] 投注记录数: {len(my_bets_response)}")

                        # 超时仍未找到
                        # print(f"❌ [PIN888] 超时: 未能确认 WagerID {wager_id} 的最终状态")
                        await self._send_message_to_electron(f"[PIN888] 超时 - 未能确认投注状态")
                        return None

                    elif status == 'PROCESSED_WITH_ERROR':
                        print(f"[{self.handler_name}] ❌ [PIN888] 下注失败,状态: PROCESSED_WITH_ERROR")
                        print(f"[{self.handler_name}]   错误信息: {response_data}")
                        await self._send_message_to_electron(f"[PIN888] 下注失败 - 状态: PROCESSED_WITH_ERROR, 错误信息: {response_data}")
                        return None

                    else:
                        print(f"[{self.handler_name}] ❌ [PIN888] 下注失败,状态: {status}")

                        await self._send_message_to_electron(f"[PIN888] 下注失败 - WagerID: {wager_id}, 状态: {status}")
                
                
                

                else:
                    new_balance = await self.GetBalanceByRequest()
                    if new_balance:
                        # 更新到 online_platform
                        self.online_platform['balance'] = new_balance
                    print(f"[{self.handler_name}] ❌ [PIN888] 响应格式不正确")
                    print(f"[{self.handler_name}]   响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                    await self._send_message_to_electron(f"[PIN888] 响应格式不正确")
                    return None

            except json.JSONDecodeError as e:
                print(f"[{self.handler_name}] ❌ [PIN888] 解析响应数据失败: {e}")
                print(f"[{self.handler_name}] 原始响应: {response.get('response')}")
                return None

        except Exception as e:
            print(f"[{self.handler_name}] ❌ [PIN888] 执行下注请求失败: {e}")
            import traceback
            traceback.print_exc()
            return None


    async def GetOdd(self, msg, event_id=None, logger=None):

        start_time = time.time()  # 开始计时
        self._is_SupplementaryOrder = False
        # * 第一步, 找比赛,需要拿到 eventid

        original_msg = msg
        # print(msg)
        bet_data = msg.get('bet_data', {})
        # print(f"bet_data: {bet_data}")
        if not bet_data:
            print(f"[{self.handler_name}] ❌ [PIN888] msg缺少必要参数 bet_data")
            return None



        bookmaker_event_direct_link = bet_data.get('bookmaker_event_direct_link', '')
        if not event_id:
            event_id = bookmaker_event_direct_link

        order_id = msg.get('order_id','')
        if not order_id:
            print(f"[{self.handler_name}] ❌ [PIN888] msg 缺少必要参数 order_id")
            return None

        eventId = bet_data.get('event_id','')
        print(f"[{self.handler_name}] eventId {eventId}")
        matched_event_id = event_id or eventId

        sport_type=bet_data.get('spider_sport_type')
        # print(sport_type)
        sportId,period_num = self.transfan_sport(sport_type)



        # ================== 使用Betburger 给的event_id 尝试是否可以匹配到比赛 ，并拿到 event_detail_data ============
        event_detail_data = await subscribe_events_detail_euro(self.page, matched_event_id)
        if not event_detail_data:
            print(f"[{self.handler_name}] ❌ [PIN888] Betburger 提供的 eventId 无效,需要通过球队名重新匹配")
            # 如果 betburger 的event_id 无效,那么考虑使用 主队和客队的名称进行匹配
            # 1.请求所有的events并拿到结果
            all_events = await subscribe_live_euro_odds(self.page, sportId, period_num)

            if not all_events:
                print(f"[{self.handler_name}] ❌ [PIN888] 获取 all_events 失败")
                return None

            # 2.针对结果进行 数据的解析, 输入:all_events,spider_home,spider_away .输出 event_id
            spider_home = bet_data.get('spider_home', '')
            spider_away = bet_data.get('spider_away', '')

            # 3.解析并匹配比赛
            parsed_result = parse_event_from_all_events(all_events, spider_home, spider_away)

            if not parsed_result:
                print(f"[{self.handler_name}] ❌ [PIN888] 未能从 all_events 中匹配到比赛")
                return None

            # 4.提取解析结果
            matched_event_id = parsed_result['event_id']
            event_id = matched_event_id
            pin888_standard_home_name = parsed_result['home_name']
            pin888_standard_away_name = parsed_result['away_name']

            print(f"[{self.handler_name}] ✅ [PIN888] 通过球队名匹配成功:")

            event_detail_data = await subscribe_events_detail_euro(self.page, matched_event_id)
            if not event_detail_data:
                print(f'[{self.handler_name}] [pin888] 没有该场比赛 {spider_home} -- {spider_away}')
                return None
        
        team_names_result = parse_team_names_from_detail_data(event_detail_data)
        
        matchStateType = team_names_result['matchStateType']
       
        remaining_time = analyze_remaining_time(match_state_type=matchStateType, sport_type=sport_type)

        if not remaining_time:
            print(f"[{self.handler_name}] ❌ [PIN888] 未能分析剩余时间")
            return None

        match_phase = remaining_time['match_phase']
        remaining_seconds = remaining_time['remaining_seconds']

        # 转换为分秒格式
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        time_display = f"{minutes:02d}:{seconds:02d}"

        await self._send_message_to_electron(f"[PIN888] 剩余时间: {match_phase} - {time_display} ({remaining_seconds}秒)")


        if team_names_result:
            pin888_standard_home_name = team_names_result['pin888_home_name']
            pin888_standard_away_name = team_names_result['pin888_away_name']
            print(f"[{self.handler_name}] ✅ [PIN888] 提取标准球队名称: {pin888_standard_home_name} vs {pin888_standard_away_name}")
        else:
            print(f"[{self.handler_name}] ⚠️ [PIN888] 未能提取标准球队名称,使用原有球队名")
            # 保存 event_detail_data 到文件以便调试
            # save_event_detail_data(event_detail_data, prefix="failed_parse_team")

        if not pin888_standard_home_name or not pin888_standard_away_name:
            print(f"[{self.handler_name}] ❌ [PIN888] 未能提取标准球队名称,使用原有球队名")
            print(f"[{self.handler_name}] 详细的请求包:{event_detail_data}")
            # save_event_detail_data(event_detail_data, prefix="failed_parse_team")
            return None
       

        # =============== 第二步:构造 pin888 自己的参数 ==================
        msg = bet_data
        # 使用新的 mapping 函数 ，从betburger 的参数，映射到 pin888 解包时需要的参数
        mapping_result = map_handicap_full(
            sport_type=sport_type,
            handicap=msg.get('spider_handicap'),
            period=msg.get('spider_period'),
            handicap_param=msg.get('spider_handicap_param'),
            home_team=pin888_standard_home_name,
            away_team=pin888_standard_away_name
        )
        # print(mapping_result)
        if mapping_result is None:
            print(f"[{self.handler_name}] ❌ Mapping.pin888 返回 None,不支持此盘口或时段")
            return None

        # 从映射结果中提取字段到独立变量

        mapped_market = mapping_result['mapped_market']
        mapped_handicap = mapping_result['mapped_handicap']
        mapped_handicap_param = mapping_result['mapped_handicap_param']
        mapped_period = mapping_result['mapped_period']
        mapped_direction = mapping_result.get('mapped_direction', '')
        mapped_match = mapping_result.get('mapped_match', '')

        # 使用新的解析函数从详细赔率数据中查找匹配的赔率
        odds_result = find_odds_from_detail_data(
            sport_type=msg.get('spider_sport_type'),
            market_group=mapped_market,
            platform_handicap=mapped_handicap,
            platform_handicap_param=mapped_handicap_param,
            platform_direction=mapped_direction,
            platform_match=mapped_match,
            period=mapped_period,
            detail_odds=event_detail_data
        )


        if odds_result == 'need refresh':
            print(f"[{self.handler_name}] ⚠️ [PIN888] 需要刷新详细赔率数据")
            await unsubscribe_events_detail_euro(self.page, event_id)
            return None

        if not odds_result:
            print(f"[{self.handler_name}] ❌ [PIN888] 未能从详细赔率数据中找到匹配的赔率")
            await unsubscribe_events_detail_euro(self.page, event_id)
            return None

        # 从解析结果中提取字段
        parsed_odd = odds_result.get('odd')
        parsed_lineID = odds_result.get('lineID')
        parsed_market_group_id = odds_result.get('market_group_id')
        parsed_isAlt = odds_result.get('isAlt')
        parsed_specials_i = odds_result.get('specials_i')
        parsed_specials_event_id = odds_result.get('specials_event_id')

        print(f"[{self.handler_name}] ✅ [PIN888] 成功解析赔率: odd={parsed_odd}, lineID={parsed_lineID}, market_group_id={parsed_market_group_id}")

        
        mapping_result = map_bet_params_to_ids(
            sport_type=msg.get('spider_sport_type'),
            handicap=msg.get('spider_handicap'),
            period=msg.get('spider_period'),
            direction=mapped_direction,
            match=mapped_match,
            handicap_param=mapped_handicap_param,
            line_id=parsed_lineID,
            market_group_id=parsed_market_group_id,
            is_alt=parsed_isAlt if parsed_isAlt else False,
            specials_i=parsed_specials_i if parsed_specials_i else 0,
            specials_event_id=parsed_specials_event_id if parsed_specials_event_id else 0
        )
        # print(f"mapping_result: {json.dumps(mapping_result, indent=4)}")
        if not mapping_result:
            print(f"[{self.handler_name}] ❌ [PIN888] 映射失败")
            await unsubscribe_events_detail_euro(self.page, event_id)
            return None


        # =====================第三步:http请求询问盘口是否可用 ==============================
        # 从字典中提取映射结果
        oddsID = mapping_result['oddsID']
        oddsSelectionsType = mapping_result['oddsSelectionsType']
        selectionID = mapping_result['selectionID']
        print(f"[{self.handler_name}] ✅ [PIN888] 成功映射参数: oddsID={oddsID}, oddsSelectionsType={oddsSelectionsType}")
        response = await self.RequestAllOddsSelections(oddsID, selectionID, oddsSelectionsType)
        if not response:
            print(f"[{self.handler_name}] ❌ [PIN888] 请求 [添加订单] 失败")
            await unsubscribe_events_detail_euro(self.page, event_id)
            return None
        
        
        # 解析响应数据
        try:
            response_data = json.loads(response['response'])
            if not response_data or len(response_data) == 0:
                print(f"[{self.handler_name}] ❌ [PIN888] [添加订单] 响应数据为空")
                await unsubscribe_events_detail_euro(self.page, event_id)
                return None

            data = response_data[0]

            # 提取响应中的 selectionId
            response_selection_id = data.get('selectionId')
            odds_id = data.get('oddsId')
            odds = data.get('odds') or data.get('odd')  # 尝试 'odds' 和 'odd'
            max_stake = data.get('maxStake')
            status = data.get('status')

            # print(f'[pin888] 响应状态: {status}')
            if status == 'UNAVAILABLE':
                print(f'[{self.handler_name}] [pin888] [添加订单]成功,但已封盘,不能下单')
                await self._send_message_to_electron('[pin888] [添加订单]成功,但已封盘,不能下单')
                return None


            if not oddsID or odds is None:
                await self._send_message_to_electron('[pin888] [添加订单]成功,但回复数据不完整')
                await unsubscribe_events_detail_euro(self.page, event_id)
                return None

            # 使用 order_id 作为 key 存储订单信息
            self.order_record[order_id] = {
                'selectionId': response_selection_id,  # 使用请求时构造的 selectionID
                'oddsId': oddsID,            # 使用请求时构造的 oddsID
                'odds': str(odds),           # 确保是字符串
                'maxStake': max_stake,
                'pin888_standard_home_name':pin888_standard_home_name,
                'pin888_standard_away_name':pin888_standard_away_name,
                'event_id':event_id,
                'event_detail_data':event_detail_data,
                'sport_type':sport_type,
                'sportId': sportId,          # 运动类型ID
                'period_num': period_num,    # 时段编号
                'msg': original_msg,                  # 保存完整msg用于fallback
                'retry_count': 0,            # 重试计数器
                'spider_handicap':msg.get('spider_handicap'),
                'spider_period':msg.get('spider_period'),
                'spider_sport_type':sport_type,
                'mapped_market':mapped_market,
                'mapped_handicap':mapped_handicap,
                'mapped_handicap_param':mapped_handicap_param,
                'mapped_period':mapped_period,
                'mapped_direction':mapped_direction,
                'mapped_match':mapped_match,
                'remaining_seconds':remaining_seconds

          
            }
           

            await unsubscribe_events_detail_euro(self.page, event_id)
            return {
                'handler_name':self.handler_name,
                'order_id':order_id,
                'platform_odd':odds,
                'platform_max_stake':max_stake,
                'match_phase':match_phase,
                'remaining_seconds':remaining_seconds,
                'spider_handicap':msg.get('spider_handicap'),
                'spider_period':msg.get('spider_period'),
                'sport_type':sport_type,
                'success':True,
            }

        except Exception as e:
            print(f"[{self.handler_name}] ❌ [PIN888] 解析响应数据失败: {e}")
            return None







        
    async def send_websocket_data(self, data_str):
        """
        通过 WebSocket 发送数据

        Args:
            data_str: 要发送的数据字符串

        Returns:
            bool: 发送成功返回 True
        """
      

        try:
            # 通过 JavaScript 发送数据
            js_code = f"""
            (() => {{
                if (window.__ws && window.__ws.readyState === 1) {{
                    window.__ws.send({json.dumps(data_str)});
                    console.log('✅ 数据已发送:', {json.dumps(data_str)});
                    return true;
                }} else {{
                    console.log('❌ WebSocket 未连接');
                    return false;
                }}
            }})()
            """

            result = await self.page.evaluate(js_code)
            return result

        except Exception as e:
            print(f"[{self.handler_name}] ❌ [PIN888] 发送 WebSocket 数据失败: {e}")
            return False



  



    async def RequestAllOddsSelections(self, odds_id: str, selection_id: str, odds_selections_type: str):
        """
        发送获取所有赔率选项的请求

        参数:
            odds_id: 完整的oddsId字符串 (例如: "123456|0|1|0|0|0")
            selection_id: 完整的selectionId字符串 (例如: "789012|123456|0|1|0|0|0|0")
            odds_selections_type: 赔率选择类型 (例如: "NORMAL")

        返回:
            响应数据字典，包含status、response等字段，失败返回None
        """
        try:
            # 检查必要参数
            if not odds_id:
                print(f"[{self.handler_name}] [PIN888] odds_id不能为空")
                return None
            if not selection_id:
                print(f"[{self.handler_name}] [PIN888] selection_id不能为空")
                return None
            if not odds_selections_type:
                print(f"[{self.handler_name}] [PIN888] odds_selections_type不能为空")
                return None

            # 生成时间戳（毫秒）
            timestamp = int(time.time() * 1000)

            # 加载JS模板文件
            js_template = load_js_file(
                file_name="RequestAllOddsSelections.js",
                platform_name='pin888'
            )

            if not js_template:
                print(f"[{self.handler_name}] [PIN888] 加载 RequestAllOddsSelections.js 文件失败")
                return None

            # 替换占位符
            js_code = js_template.replace('__ODDS_ID__', f'"{odds_id}"')
            js_code = js_code.replace('__SELECTION_ID__', f'"{selection_id}"')
            js_code = js_code.replace('__ODDS_SELECTIONS_TYPE__', f'"{odds_selections_type}"')
            js_code = js_code.replace('__TIMESTAMP__', str(timestamp))

            print(f"[{self.handler_name}] [PIN888] 开始发送 RequestAllOddsSelections 请求")
            print(f"[{self.handler_name}] [PIN888]   Odds ID: {odds_id}")
            print(f"[{self.handler_name}] [PIN888]   Selection ID: {selection_id}")
            print(f"[{self.handler_name}] [PIN888]   Odds Selections Type: {odds_selections_type}")

            # 包装并执行JS代码
            wrapped_code = f"(() => {{ {js_code} }})()"
            response_data = await self.page.evaluate(wrapped_code)

            # 检查响应
            if not response_data:
                print(f"[{self.handler_name}] [PIN888] 请求返回空响应")
                return None

            if response_data.get('error'):
                print(f"[{self.handler_name}] [PIN888] 请求失败: {response_data.get('error')}")
                return None

            if response_data.get('status') != 200:
                print(f"[{self.handler_name}] [PIN888] 请求失败，状态码: {response_data.get('status')}")
                return None

            print(f"[{self.handler_name}] [PIN888] RequestAllOddsSelections 请求成功")

            return response_data

        except Exception as e:
            print(f"[{self.handler_name}] [PIN888] 执行 RequestAllOddsSelections 失败: {e}")
            return None


    async def GetBalance(self, logger=None):
        """
        异步获取余额 (优先使用请求方式,失败则使用元素定位)

        Args:
            logger: 日志对象

        Returns:
            str: 余额数值,如 "2.31"
        """
        # 方法1: 优先通过请求获取余额
        try:
            balance = await self.pom.find_balance_by_request()
            if balance:
                return balance
        except Exception as e:
            print(f"[{self.handler_name}] ⚠️ [PIN888] 请求方式获取余额失败,尝试元素定位: {e}")

        # 方法2: 兜底使用元素定位获取余额
        try:
            # 1. 从 POM 获取余额元素定位器
            balance_locator = await self.pom.find_balance_element()

            # 2. 等待元素出现
            await balance_locator.wait_for(timeout=10000)

            # 3. 获取文本内容
            balance_text = await balance_locator.text_content()

            # 4. 返回余额
            if balance_text:
                balance = balance_text.strip()
                return balance
            else:
                print(f"[{self.handler_name}] ⚠️ [PIN888] 余额为空")
                return None

        except Exception as e:
            print(f"[{self.handler_name}] ❌ [PIN888] 获取余额失败: {e}")
            return None

    async def GetBalanceByRequest(self, logger=None):
        """
        通过发送请求获取余额

        Args:
            logger: 日志对象

        Returns:
            str: 余额字符串,如 "19.31",失败返回 None
        """
        try:
            # 调用 POM 方法发送请求
            balance = await self.pom.find_balance_by_request()

            if balance:
                print(f"[{self.handler_name}] 💰 [PIN888] 通过请求获取余额: {balance}")
                return balance
            else:
                print(f"[{self.handler_name}] ❌ [PIN888] 通过请求获取余额失败")
                return None

        except Exception as e:
            print(f"[{self.handler_name}] ❌ [PIN888] GetBalanceByRequest 失败: {e}")
            return None

    async def prepare_work(self):
        # 调试: 打印当前页面状态
        print(f"[{self.handler_name}] 🔍 [DEBUG] 当前页面 URL: {self.page.url}")
        print(f"[{self.handler_name}] 🔍 [DEBUG] 页面是否关闭: {self.page.is_closed()}")

        # 等待页面加载完成
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
            print(f"[{self.handler_name}] ✅ [DEBUG] 页面加载完成")
        except Exception as e:
            print(f"[{self.handler_name}] ⚠️ [DEBUG] 等待页面加载超时: {e}")
        await asyncio.sleep(15)
        # 先检查是否已经登录
        deposit_link = await self.pom.find_deposit_link_element()
        deposit_count = await deposit_link.count()
        print(f"[{self.handler_name}] 🔍 [DEBUG] Deposit 按钮数量: {deposit_count}")

        if deposit_count > 0:
            print(f"[{self.handler_name}] ✅ 已登录,跳过登录流程")

            # Hook WebSocket
            hook_success = await self.hookWebSocket()
            if not hook_success:
                print(f"[{self.handler_name}] ⚠️ WebSocket hook 失败")
                return False

            # 获取余额并发送
            balance = await self.pom.find_balance_by_request()

            if balance:
                print(f"[{self.handler_name}] 💰 [PIN888] 当前余额: {balance}")
                # 保存balance到handler_info(无论ws_client是否存在)
                ActionChain.handler_info[self.handler_name]['balance'] = balance

                if self.ws_client:
                    try:
                        await self.ws_client.send({
                            'from': 'automation',
                            'to': 'dispatch',
                            'type': 'balance_update',
                            'data': {
                                'handler_name': self.handler_name,
                                'balance': balance
                            }
                        })
                        print(f"[{self.handler_name}] 📤 [PIN888] 余额已发送")
                    except Exception as e:
                        print(f"[{self.handler_name}] ⚠️ [PIN888] 发送余额失败: {e}")

            print(f"[{self.handler_name}] ✅ 初始化成功")
            return True

        # 未登录,执行登录流程
        print(f"[{self.handler_name}] 🔐 开始登录流程...")
        login_btn = await self.pom.find_Login_btn_element()
        login_btn_count = await login_btn.count()
        print(f"[{self.handler_name}] 🔍 [DEBUG] Login 按钮数量: {login_btn_count}")

        if login_btn_count > 0:
            try:
                await login_btn.click()
            except Exception as e:
                print(f"[{self.handler_name}] ⚠️ 点击登录按钮失败: {e}")
                return False
            await asyncio.sleep(3)

            login_btn_2 = await self.pom.find_Login_btn_element_2()
            if await login_btn_2.count() > 0:
                username_input = await self.pom.find_username_input_element()
                password_input = await self.pom.find_password_input_element()
                if await username_input.count() > 0:
                    # 检查输入框是否已有内容
                    username_value = await username_input.input_value()
                    password_value = await password_input.input_value()

                    if not username_value or not password_value:
                        # 输入框为空,需要发送请求填充内容
                        uri = f"/account/{self.ads_id+'_pin888'}"
                        url = f"{Settings.BASE_URL}{uri}"

                        async with aiohttp.ClientSession() as session:
                            async with session.get(url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    username_value = data.get('username')
                                    password_value = data.get('password')
                                    if username_value and password_value:
                                        await username_input.fill(username_value)
                                        await password_input.fill(password_value)
                                        await asyncio.sleep(0.5)  # 等待填充完成
                                        await login_btn_2.click()
                                    else:
                                        print(f"[{self.handler_name}] ⚠️ 无法获取账号信息")
                                        return False
                                else:
                                    print(f"[{self.handler_name}] ⚠️ 请求失败,状态码: {response.status}")
                                    return False
                    else:
                        # 输入框已有内容,直接点击登录
                        await login_btn_2.click()
                else:
                    print(f"[{self.handler_name}] ⚠️ 输入框不存在")
                    return False
            else:
                print(f"[{self.handler_name}] ⚠️ 登录按钮2不存在")
                return False
        else:
            print(f"[{self.handler_name}] ⚠️ 登录按钮不存在")
            return False

        # 登录后再次检查 deposit 按钮
        await asyncio.sleep(3)
        deposit_link = await self.pom.find_deposit_link_element()
        if await deposit_link.count() > 0:
            print(f"[{self.handler_name}] ✅ 登录成功")

            # Hook WebSocket
            ws_result = await self._get_ws_object()
            if ws_result:
                print(f"[{self.handler_name}] ✅ [PIN888] WebSocket 已连接,无需 hook")
                # 获取余额并发送
                balance = await self.pom.find_balance_by_request()
                if balance:
                    print(f"[{self.handler_name}] 💰 [PIN888] 当前余额: {balance}")
                    if self.ws_client:
                        try:
                            await self.ws_client.send({
                                'type': 'balance_update',
                                'data': {
                                    'handler_name': self.handler_name,
                                    'platform_name': self.platform_name,
                                    'balance': balance
                                }
                            })
                            # print(f"📤 [PIN888] 余额已发送")
                            print(f"[{self.handler_name}] ✅ 初始化成功")
                        except Exception as e:
                            print(f"[{self.handler_name}] ⚠️ [PIN888] 发送余额失败: {e}")
                return True

            hook_success = await self.hookWebSocket()
            if not hook_success:
                print(f"[{self.handler_name}] ⚠️ WebSocket hook 失败")
                return False





        else:
            print(f"[{self.handler_name}] ⚠️ 登录失败,未找到 Deposit 按钮")
            return False

    async def _get_ws_object(self):
        """
        获取 window.__ws 对象,并返回 WebSocket 对象
        """
        # 1. 从缓存获取 JS 代码 (程序启动时已预加载)
        js_code = load_js_file(
            file_name='Get_window__ws.js',
            platform_name='pin888'
        )

        if not js_code:
            print(f"[{self.handler_name}] ❌ [PIN888] 加载 Get_window__ws.js 失败")
            return None

        # 2. 包装成自执行函数
        wrapped_code = f"(() => {{ {js_code} }})()"

        # 3. 执行 JS 代码获取 window.__ws 对象
        try:
            ws_object = await self.page.evaluate(wrapped_code)

            # 调试: 如果返回 False,打印更多信息
            if not ws_object and self.connect_count == 0:
                # 检查 WebSocket 状态
                ws_status = await self.page.evaluate("window.getWebSocketStatus ? window.getWebSocketStatus() : 'function not found'")
                print(f"[{self.handler_name}] 🔍 [DEBUG] window.__ws: {await self.page.evaluate('typeof window.__ws')}")
                print(f"[{self.handler_name}] 🔍 [DEBUG] WebSocket 状态: {ws_status}")
                self.connect_count += 1

        except Exception as e:
            print(f"[{self.handler_name}] ❌ [PIN888] 执行 JS 失败: {e}")
            return None

        return ws_object

    async def hookWebSocket(self):
        """
        钩住 WebSocket 对象
        如果 window.__ws 已存在,直接返回成功
        如果不存在,注入 hook 脚本并重新加载页面
        """
        # 1. 检查 window.__ws 是否已存在
        # ws_result = await self._get_ws_object()
        # if ws_result:
        #     print(f"✅ [PIN888] WebSocket 已连接,无需 hook")
        #     return True

        # 2. window.__ws 不存在,需要注入 hook 脚本
        # print(f"⚠️ [PIN888] WebSocket 对象不存在,开始注入 hook 脚本...")

        # 3. 加载 hook 脚本
        hook_code = load_js_file(
            file_name='_0websocket_hook.js',
            platform_name='pin888'
        )

        if not hook_code:
            print(f"[{self.handler_name}] ❌ [PIN888] 加载 _0websocket_hook.js 失败")
            return False

        # 4. 使用 add_init_script 在页面加载前注入 hook (关键!)
        try:
            await self.page.add_init_script(hook_code)
            print(f"[{self.handler_name}] ✅ [PIN888] hook 脚本已添加到页面初始化脚本")
        except Exception as e:
            print(f"[{self.handler_name}] ❌ [PIN888] 添加 init_script 失败: {e}")
            return False

        # 5. 刷新页面,使 hook 在 WebSocket 创建之前生效
        print(f"[{self.handler_name}] 🔄 [PIN888] 刷新页面以激活 hook...")
        try:
            # 使用更宽松的等待策略,避免 networkidle 超时
            await self.page.reload(wait_until='domcontentloaded', timeout=15000)
            print(f"[{self.handler_name}] ✅ [PIN888] 页面刷新完成")
        except Exception as e:
            print(f"[{self.handler_name}] ⚠️ [PIN888] 页面刷新超时,但可能已加载: {e}")

        # ⚠️ 调试: 页面刷新后立即手动执行 hook 脚本
        # 因为 add_init_script 在 CDP 连接的浏览器中可能不生效
        print(f"[{self.handler_name}] 🔧 [DEBUG] 手动执行 hook 脚本...")
        try:
            await self.page.evaluate(hook_code)
            print(f"[{self.handler_name}] ✅ [DEBUG] hook 脚本手动执行完成")

            # 立即检查 hook 是否生效
            hook_check = await self.page.evaluate("typeof window.getWebSocketStatus")
            print(f"[{self.handler_name}] 🔍 [DEBUG] hook 检查: window.getWebSocketStatus = {hook_check}")
        except Exception as e:
            print(f"[{self.handler_name}] ❌ [DEBUG] 手动执行 hook 失败: {e}")

        try:
            balance_ele = await self.pom.find_balance_element()
            if not balance_ele:
                print(f"[{self.handler_name}] ⚠️ [PIN888] 余额元素未找到，重新加载页面")
                return False
        except Exception as e:
            print(f"[{self.handler_name}] ⚠️ [PIN888] 余额元素未找到: {e}")
            return False

            # 即使超时,也继续尝试检查 WebSocket

        # 6. 等待 WebSocket 连接建立 (最多等待 10 秒)
        print(f"[{self.handler_name}] ⏳ [PIN888] 等待 WebSocket 连接建立...")

        start_time = time.time()

        while time.time() - start_time < 15:
            ws_available = await self._get_ws_object()
            if ws_available:
                print(f"[{self.handler_name}] ✅ [PIN888] WebSocket 连接已建立")
                return True
            await asyncio.sleep(0.5)

        # 7. 检查最终结果
        ws_available = await self._get_ws_object()
        if not ws_available:
            print(f"[{self.handler_name}] ❌ [PIN888] WebSocket 连接建立失败 (超时 10 秒)")
            return False

        print(f"[{self.handler_name}] ✅ [PIN888] WebSocket 连接成功")
        return True

    
    async def _send_message_to_electron(self, message):
        message = f"[{self.handler_name}] {message}"
        log_message = {
            "from": "automation",
            "to": "electron",
            "type": "log",
            "data": {
                "type": "warn",
                "message": message
            }
        }
        await self.ws_client.send(log_message)

    def transfan_sport(self,sport_type):
        if sport_type == 'soccer':
            sportId = 29
            period_num= "0,8,39,3,4,5,6,7"
        elif sport_type == 'basketball':
            sportId= 4
            period_num = "0,2"
        else:
            print(f"[{self.handler_name}] ❌ 不支持的球类: {sport_type}")
            return None
        return sportId,period_num
    
    async def get_event_id(self, sportId, period_num, spider_home, spider_away, event_id=None):
        """
        获取 event_id 和标准球队名称

        参数:
            sportId: 运动类型ID
            period_num: 时段编号
            spider_home: 爬虫获取的主队名称
            spider_away: 爬虫获取的客队名称
            event_id: 可选的初始 event_id (如果提供则先尝试直接订阅)

        返回:
            (event_id, pin888_standard_home_name, pin888_standard_away_name, event_detail_data) 或 (None, None, None, None)
        """
        matched_event_id = event_id
        event_detail_data = None

        # 如果提供了 event_id,先尝试直接订阅
        if matched_event_id:
            event_detail_data = await subscribe_events_detail_euro(self.page, matched_event_id)
        
        if not event_detail_data:
            print(f"[{self.handler_name}] ❌ [PIN888] Betburger 提供的 eventId 无效,需要通过球队名重新匹配")
            await unsubscribe_events_detail_euro(self.page, event_id)
            all_events = await subscribe_live_euro_odds(self.page, sportId, period_num)

            if not all_events :
                print(f"[{self.handler_name}] ❌ [PIN888] 获取 all_events 失败")
                # print(f'[{self.handler_name}] all_events: {all_events}')
                if self.connect_count == 0:
                    await self.hookWebSocket()
                    self.connect_count += 1

                return None, None

            # all_events 必须是实时数据
            


            # 3.解析并匹配比赛, 此时一定是拿到了 all_events   被执行,说明all_events 不为空
            parsed_result = parse_event_from_all_events(all_events, spider_home, spider_away)

            if not parsed_result:
                print(f"[{self.handler_name}] ❌ [PIN888] all_events 获取成功,但是未能从 all_events 中匹配到比赛")
                print(f'[{self.handler_name}] 匹配使用的主队: {spider_home} 匹配使用的客队: {spider_away}')
                return None, None

            # 4.提取解析结果
            matched_event_id = parsed_result['event_id']
            event_id = matched_event_id
            pin888_standard_home_name = parsed_result['home_name']
            pin888_standard_away_name = parsed_result['away_name']

            print(f"[{self.handler_name}] ✅ [PIN888] 通过球队名匹配成功:")
            print(f"[{self.handler_name}]   event_id: {matched_event_id}")
            print(f"[{self.handler_name}]   {pin888_standard_home_name} vs {pin888_standard_away_name}")

            event_detail_data = await subscribe_events_detail_euro(self.page, matched_event_id)
            if not event_detail_data:
                print(f'[{self.handler_name}] [pin888] 没有该场比赛 {spider_home} -- {spider_away}')
                print(f'[{self.handler_name}] event_detail_data: {event_detail_data}')
                return None, None

        # 提取标准球队名称
        # team_names_result = parse_team_names_from_detail_data(event_detail_data)

        # if team_names_result:
        #     pin888_standard_home_name = team_names_result['pin888_home_name']
        #     pin888_standard_away_name = team_names_result['pin888_away_name']
        #     print(f"✅ [PIN888] 提取标准球队名称: {pin888_standard_home_name} vs {pin888_standard_away_name}")
        # else:
        #     print(f"⚠️ [PIN888] 未能提取标准球队名称,使用原有球队名")
            # pin888_standard_home_name = spider_home
            # pin888_standard_away_name = spider_away

        return event_id,  event_detail_data

           
    async def get_httpRequest_params(self, sport_type, handicap, period, handicap_param, home_team, away_team, event_detail_data, event_id):
        """
        获取 HTTP 请求参数(解析赔率数据)

        参数:
            sport_type: 运动类型 ('soccer', 'basketball')
            handicap: 盘口类型
            period: 时段
            handicap_param: 盘口参数
            home_team: 主队名称
            away_team: 客队名称
            event_detail_data: 详细赔率数据
            event_id: 比赛ID

        返回:
            dict: 包含 odd, lineID, market_group_id, isAlt, specials_i, specials_event_id 等字段
            None: 解析失败
        """
        mapping_result = map_handicap_full(
            sport_type=sport_type,
            handicap=handicap,
            period=period,
            handicap_param=handicap_param,
            home_team=home_team,
            away_team=away_team
        )
        
        if mapping_result is None:
            print(f"[{self.handler_name}] ❌ Mapping.pin888 返回 None,不支持此盘口或时段")
            return None

        # 从映射结果中提取字段到独立变量

        mapped_market = mapping_result['mapped_market']
        mapped_handicap = mapping_result['mapped_handicap']
        mapped_handicap_param = mapping_result['mapped_handicap_param']
        mapped_period = mapping_result['mapped_period']
        mapped_direction = mapping_result.get('mapped_direction', '')
        mapped_match = mapping_result.get('mapped_match', '')

        # 使用新的解析函数从详细赔率数据中查找匹配的赔率
        odds_result = find_odds_from_detail_data(
            sport_type=sport_type,
            market_group=mapped_market,
            platform_handicap=mapped_handicap,
            platform_handicap_param=mapped_handicap_param,
            platform_direction=mapped_direction,
            platform_match=mapped_match,
            period=mapped_period,
            detail_odds=event_detail_data
        )


        if odds_result == 'need refresh':
            print(f"[{self.handler_name}] ⚠️ [PIN888] 需要刷新详细赔率数据")
            await unsubscribe_events_detail_euro(self.page, event_id)
            return None

        if not odds_result:
            print(f"[{self.handler_name}] ❌ [PIN888] 未能从详细赔率数据中找到匹配的赔率")
            await unsubscribe_events_detail_euro(self.page, event_id)
            return None


        return odds_result