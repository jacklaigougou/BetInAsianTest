

## window.__ws
存储在 浏览器中ws 对象,可以直接使用


## 通过 window.__pagestatus 判断是在主页还是详情页
它只有两种状态:
    --- 'LIVE_EURO_ODDS' - 赛事列表页面
    --- 'EVENT_DETAILS_EURO_ODDS' - 比赛详情页面


## window.___detailFullOdds 
包含详细赔率数据

## window.__AllEvents


## pin888 自己的执行逻辑
发送: {"type":"SUBSCRIBE","destination":"LIVE_EURO_ODDS","body":{"dpMs1":"rb4iGmltP4X4okKDTjuL","sportId":"29","isHlE":false,"isLive":true,"oddsType":1,"version":0,"eventType":0,"periodNum":"0,8,39,3,4,5,6,7","locale":"en_US"}}

作用是订阅所有的 LIVE_EURO_ODDS


返回的数据有两种
        --- 1. Full odds(所有的比赛信息),一次把当前所有的数据都发送过来了 
        --- 2. updata odds (更新信息) , 信息更新,这里很重要的一点,可能即更新 赔率,盘口,也更新比赛id

### 拆解 full odds , MATCHUPS_EURO_ODDS 这个是
第一层 odds --> {}       sportsId:29 是足球, sportsId:4 是篮球
    第二层 leagues --> []
        第三层 league --> {}
            第四层 events --> []
                第五层 event --> {}
                    第六层 id(主要判断比赛依据), participants(比赛主客队信息) -->[] ,periods(时段) --> {}

对于full odds 的数据解析,只需要到第六层就够了,拿到id 就可以了
这里的id 有两种方式
    1.直接匹配id
    2.没有匹配上id,说明已经被更新了,那么此时应该重新请求LIVE_EURO_ODDS,然后再根据名字进行匹配

所以,我其实可以,直接使用id试试? 还是说先找,再弄? 


## detil odd 具体的盘口分析

第一层 odds --> {}
    第二层 normal, --> {}
        第三层 periodss --> {}
            第四层 "0" , "1" --> {}
                 第五层 handicap,moneyLine,overUnder,TeamTotals --> {}
    

    第二层 specials ---> {}
        第三层 "0" , "1" --> {}
            第四层 events ---> []
                第五层 匹配 name 即可


    第二层 corners ---> {}
        第三层 periodss --> {}
            第四层 "0" , "1" --> {}
                第五层 handicap,moneyLine,overUnder,TeamTotals --> {}

篮球 : 0 全场 1 半场 ,2 下半场 ,3 第一节, 4第二节, 5第三节,6第四节

isAlt 是 "is Alternative" (是否为替代盘口) 的缩写

第一个位置  0-->全场  1---> 上半场   (确定)
第二个位置  主/客队? 
第三个位置  over/under ? 
第四个位置  盘口参数    (确定)
第五个位置


请求1: oddsID  就是我自己搞的 