import requests
import time
import datetime

import alert1
import constant
import db
import math1
from decimal import Decimal
import traceback


def timestamp2time(unix_timestamp):
    # 将Unix时间戳转换为datetime对象
    # unix_timestamp = 1725535800000
    dt = datetime.datetime.fromtimestamp(int(unix_timestamp) / 1000)  # 除以1000是因为时间戳是毫秒

    # 格式化datetime对象为字符串
    human_readable_time = dt.strftime("%Y-%m-%d %H:%M:%S")

    return human_readable_time

def calculate_ma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[:period]) / period  # 从最新的数据开始计算

# latest_price 最新价/收盘价
def treat_with_condition(inst_id, direction, current_price):
    previous_trade = db.get_last_trade()
    # 当前股票价格
    current_price_d = Decimal(current_price)
    # 如果下交，那必须已经在系统中进行了交易，才能走清仓的逻辑
    if previous_trade:
        # 如果已建仓，遇到了下交，就全部抛售
        if previous_trade[1]== inst_id and direction == constant.CROSS_DOWN and previous_trade[2] != constant.CROSS_DOWN:
            sell_all_stock(inst_id, current_price)
    # 如果遇到上交，进入买入场景，有两种情况，一种是第一次进入系统进行交易，另外一种之前有过交易，之前有过交易的情况下，上一次的交易必须是清仓
    if direction == constant.CROSS_UP:
        if not previous_trade or previous_trade[2] == constant.CROSS_DOWN:
            # 活钱余额：如果未建仓，可能是第一次进入系统进行交易，也可能是之前有过交易。如果有过交易，直接从上一次里面获取，如果没有，就是最初投入成本金额
            if not previous_trade:
                cash = Decimal(constant.INITIAL_INVESTMENT_COST)
            else:
                cash = Decimal(previous_trade[9])
            # 买入时币价就是最新虚拟货币价格
            buy_price = Decimal(current_price)
            # 买入的数量：通过 活钱余额，当前的股票价格 计算
            buy_count = math1.calc_buy_coin_count(cash,buy_price)
            # 本次建仓成本价 = 建仓时币价 * (1 + 手续费)
            current_position_price = Decimal(current_price) * (Decimal(1) + Decimal(constant.FEE_RATE))
            buy_amount,sell_amount,buy_fee,sell_fee,new_balance,new_cash,new_currency_count,profit,total_profit,profit_rate,total_profit_rate  = (
                math1.calc_buy_all(current_position_price,current_price_d,buy_count,cash,constant.INITIAL_INVESTMENT_COST))
            # 建仓的时候，本次建仓成本金额 = 本次交易币数量 * 本次建仓成本价
            current_position_cost = buy_count * current_position_price
            # 全仓买入时 本次交易币数量 = 本次建仓买币数量
            transaction_count = buy_count
            # 因为是建仓，本次建仓的成本金额就是仓位余额
            db.add_trade(inst_id, constant.CROSS_UP, float(buy_price), 0, float(buy_amount), 0, float(buy_fee), float(new_balance), float(new_cash),
                         float(profit), float(total_profit), float(current_price), float(new_currency_count),
                         float(current_position_cost), constant.INITIAL_INVESTMENT_COST, float(profit_rate),
                         float(total_profit_rate), float(transaction_count), float(current_position_price))

def log_crossing(inst_id, direction, last_candle):
    # 查询是否记录
    time_str = timestamp2time(last_candle[0])
    rows = db.fetch_cryptocurrency_by_currency_and_time(inst_id,time_str)
    # 检查键是否已经记录
    if not rows:
        # 参数分别为 货币类型，开盘价，最高价，最低价，最新价/收盘价，成交量，时间戳
        db.insert_cryptocurrency(inst_id, last_candle[1], last_candle[2], last_candle[3], last_candle[4], 1500,time_str)
        db.insert_alert_log(inst_id,direction,1,time_str)
        # 如果已建仓，遇到了下交，就全部抛售
        # 如果未建仓，遇到上交，就建仓
        treat_with_condition(inst_id,direction,last_candle[4])


def get_current_time():
    # 获取当前的日期和时间
    now = datetime.datetime.now()
    # 将时间转换为字符串
    time_string = now.strftime("%Y-%m-%d %H:%M:%S")

    return time_string
# 逃出诱多陷阱
def sell_all_stock(inst_id,current_price):
    previous_trade = get_held_stock()
    if previous_trade and inst_id == previous_trade[1]:
        # 因为是全部抛售，活钱余额直接从上一条记录获取即可
        cash = Decimal(previous_trade[9])
        # 上一次仓位余额
        previous_balance = Decimal(previous_trade[8])
        # 全部抛售的 卖出数量 = 当前仓库
        sell_count = Decimal(previous_trade[14])
        # 上一次仓位剩余货币个数
        previous_currency_count = Decimal(previous_trade[14])
        # 本次建仓成本价 取上一条即可
        current_position_price = Decimal(previous_trade[20])
        buy_amount, sell_amount, buy_fee, sell_fee, new_balance, new_cash, new_currency_count, profit, total_profit, profit_rate, total_profit_rate = (
            math1.calc_sell_all(current_position_price, Decimal(current_price), sell_count, previous_balance, cash,
                                previous_currency_count, Decimal(constant.INITIAL_INVESTMENT_COST)))
        # 本次建仓成本金额 因为是全部抛售，所以直接从上一次取就行了
        current_position_cost = previous_trade[15]
        # 本次交易的货币数量 = 上一次剩余的货币数量 - 本次仓位剩余货币个数
        transaction_count = previous_currency_count - new_currency_count
        # 因为是抛售，所以是没有买入时币价的
        db.add_trade(inst_id, constant.CROSS_DOWN, 0, float(current_price), float(buy_amount), float(sell_amount),
                     float(sell_fee), float(new_balance), float(new_cash),
                     float(profit), float(total_profit), float(current_price),
                     float(new_currency_count), float(current_position_cost), constant.INITIAL_INVESTMENT_COST,
                     float(profit_rate),
                     float(total_profit_rate), float(transaction_count), float(current_position_price))

# 逃离诱多陷阱，如果股价假装上交，买入后股价迅速下跌，这就是诱多陷阱，要赶紧逃离
def escape_the_bull_trap(inst_id,current_price):
    # 如果有仓位
    held_stock = get_held_stock()
    if held_stock and inst_id == held_stock[1]:
        bull_trap_flag = math1.is_bull_trap(Decimal(held_stock[20]),Decimal(current_price))
        if bull_trap_flag:
            sell_all_stock(inst_id,current_price)


def monitor_and_treat(inst_id):
    # if inst_id:
    #     print(inst_id)
    #     return inst_id
    # 休眠3秒，避免被远程关闭
    time.sleep(10)
    # 设置请求的URL和参数
    url = "https://www.okx.com/api/v5/market/candles"
    params = {
        "instId": inst_id,
        "bar": "4H",
        # "bar": "1H",
        # "bar": "1m",
        "limit": 100  # 获取最近100条数据
    }

    # 发送GET请求
    response = requests.get(url, params=params)

    # 解析返回的数据
    data = response.json()

    # 打印K线数据
    if data['code'] == '0':  # 检查请求是否成功
        candles = data['data']
        current_candle = candles[0]
        print(inst_id, " 最新币价 时间:", timestamp2time(current_candle[0]), "开盘:", current_candle[1], "最高:", current_candle[2], "最低:", current_candle[3],
              "收盘:", current_candle[4],
              "成交量:", current_candle[5])

        # 提取收盘价
        close_prices = [float(candle[4]) for candle in candles]  # candle[4]是收盘价

        # 计算MA5和MA20
        ma5 = calculate_ma(close_prices, 5)
        ma20 = calculate_ma(close_prices, 20)
        latest_price = close_prices[0]  # 最新的收盘价
        # 判断MA5与MA20的交叉情况
        if ma5 is not None and ma20 is not None:
            previous_ma5 = calculate_ma(close_prices[1:], 5) if len(close_prices) > 5 else None
            previous_ma20 = calculate_ma(close_prices[1:], 20) if len(close_prices) > 20 else None
            # 查询是否记录
            # 触发上交下交的时间
            trigger_time = timestamp2time(current_candle[0])
            rows = db.fetch_cryptocurrency_by_currency_and_time(inst_id,trigger_time )
            # 避免同一个上穿数据反复的被记录到数据库中
            if not rows:
                if previous_ma5 is not None and previous_ma20 is not None:
                    if previous_ma5 < previous_ma20 and ma5 > ma20:
                        direction = constant.CROSS_UP
                        log_crossing(inst_id, direction, current_candle)  # 记录到文件
                    elif previous_ma5 > previous_ma20 and ma5 < ma20:
                        direction = constant.CROSS_DOWN
                        log_crossing(inst_id, direction, current_candle)  # 记录到文件
                else:
                    print("无法计算前一个MA值")
        # 非上交和下交的情况，虚拟货币涨到一定比例，进行抛售
        previous_trade = db.get_last_trade()
        # 如果之前没有任何交易数据，则不走售卖的逻辑，等上交的数据进来了才会进行卖出
        if previous_trade:
            # 如果已经记录了上穿或者下交，但是因为时间比较长，比如1天，柱子还是那个柱子，
            # 但是这一天内的任何时刻，都有可能涨到一定程度而提醒卖掉，所以这个就和ma的不一样，
            # 只要当前最后一条数据币种一样，并且不是下交，并且盈利额度达到，即可认为可以进行交易
            if previous_trade[1] == inst_id and previous_trade[2] != constant.CROSS_DOWN:
                # 上一次交易币价: 交易数据中最后一条数据中有记录
                # 如果上一次是买入，那上一次交易币价就是上一次买入价格，否则就是卖出价格
                if previous_trade[2] == constant.CROSS_UP:
                    previous_treat_price = Decimal(previous_trade[3])
                else:
                    previous_treat_price = Decimal(previous_trade[4])
                # 计算下一次预估卖出价 : 上一次交易币价 * (预设的收益率 + 1) 精度向下即可
                next_estimate_sell_price = math1.calc_next_estimate_sell_price(previous_treat_price)
                # 上一次仓位余额
                balance = Decimal(previous_trade[8])
                cash = Decimal(previous_trade[9])
                current_price = Decimal(latest_price)
                # 上一次剩余的货币数量
                previous_currency_count = Decimal(previous_trade[14])
                # 本次建仓成本价 取上一条即可
                current_position_price = Decimal(previous_trade[20])
                # 如果最新的股价 >= 下一次预估卖出价 ，就进行交易,交易金额为仓位余额的一半，如果有精度问题，就向上设置精度，多卖点
                if current_price >= next_estimate_sell_price:
                    # 如果仓位已经稀释到一定次数，价格即便继续上涨，赚到的钱也只剩零头了，再继续涨或者跌已经很难影响收益了
                    # 与其继续占用仓位，不如直接清仓，寻找下一次机会
                    rise_count = db.get_rise_count()
                    if rise_count >= constant.MAXIMUM_DILUTION_COUNT:
                        sell_all_stock(inst_id, current_price)
                        return candles
                    # 返回值：买入金额，卖出金额，买入手续费，卖出手续费，本次结算后仓位余额，本次结算后活钱余额，本次仓位剩余货币个数，本次盈利，累计盈利，本次盈利比例，累计盈利比例
                    buy_amount,sell_amount,buy_fee,sell_fee,new_balance,new_cash,new_currency_count,profit,total_profit,profit_rate,total_profit_rate = (
                        math1.calc_sell_half_position(current_position_price,balance, cash, current_price,previous_currency_count))
                    # 本次交易的货币数量 = 上一次剩余的货币数量 - 本次仓位剩余货币个数
                    transaction_count = previous_currency_count - new_currency_count
                    # 本次建仓成本金额 因为是卖出部分，所以直接从上一次取就行了
                    current_position_cost = previous_trade[15]
                    # 因为是卖出，所以没有买入时股价
                    db.add_trade(inst_id, constant.UP, 0, float(latest_price), 0, float(sell_amount), float(sell_fee), float(new_balance),float(new_cash),
                         float(profit),float(total_profit),float(latest_price),float(new_currency_count),float(current_position_cost),
                                 constant.INITIAL_INVESTMENT_COST,float(profit_rate),float(total_profit_rate),float(transaction_count),float(current_position_price))
                # 逃出诱多陷阱:除了上交下交上涨之外，还有一种就是诱多陷阱，对于这种垃圾车，直接跳车
                escape_the_bull_trap(inst_id, current_candle[4])
            return candles
    else:
        print(inst_id, "请求失败:", data['msg'])
        return None

# 查看是否有已持仓的股票
def get_held_stock():
    held_stock = db.get_last_trade()
    # 账户数据已经有交易且没有下交，就认为是已持仓了
    if held_stock and held_stock[2] != constant.CROSS_DOWN:
        return held_stock


if __name__ == '__main__':
    db.init()
    # 测试上交建仓
    # treat_with_condition('LTC-USDT',constant.CROSS_UP,50.53047)
    # 测试下交清仓
    # treat_with_condition('LTC-USDT',constant.CROSS_DOWN,68.53047)
    # 测试跳出诱多陷阱
    # escape_the_bull_trap('CELR-USDT',0.010839829)
    # 假设这是你的集合
    my_list = [
         'BTC-USDT', 'ETH-USDT','DOGE-USDT', 'LTC-USDT',
    'SOL-USDT',  'AVAX-USDT', 'LINK-USDT', 'UNI-USDT',
    'AAVE-USDT', 'APT-USDT', 'STX-USDT', 'ATOM-USDT', 'MKR-USDT',
    'LDO-USDT', 'CRV-USDT', 'XTZ-USDT', 'FIL-USDT', 'NEAR-USDT',
    'ALGO-USDT', 'XRP-USDT', 'FLOW-USDT', 'HBAR-USDT', 'ETC-USDT',
    'MANA-USDT', 'SAND-USDT', 'ENJ-USDT',  'AXS-USDT',
    'THETA-USDT',  'EGLD-USDT',  'KLAY-USDT',
    'GALA-USDT', 'ICP-USDT', 'SHIB-USDT', 'CELO-USDT',
     'ZIL-USDT',  'QTUM-USDT', 'MINA-USDT',
    'IOST-USDT',   'CHZ-USDT',
    'MOVR-USDT', 'PERP-USDT',  'MASK-USDT',
    'DYDX-USDT',
    'CELR-USDT',
    'CVC-USDT',
    'REN-USDT', 'SKL-USDT',
    'CTXC-USDT',  'BORA-USDT',
    'AUCTION-USDT',   'BADGER-USDT',
    'SUSHI-USDT',
      'ALPHA-USDT',
    ]
    while True:
        try:
            last_trade1  = db.get_last_trade()

            # 如果仓位中已经持仓了股票，就只监控仓位中的股票
            held_stock1 = get_held_stock()
            if held_stock1:
                monitor_and_treat(held_stock1[1])
            else:
                # 增加大晚上不要买股票的功能，大晚上不要交易，多休息一下，
                # 卖的话还是正常提醒，因为醒来随时都可以卖，错过这几个小时问题也不大，更重要的就是避免因为错过了下交，影响到算法
                need_rest = False
                # 获取当前时间
                current_time = datetime.datetime.now()
                current_hour = current_time.hour

                # 仅在8点到22点之间进行交易，超出这段时间，只卖不买
                if 8 <= current_hour <= 22:
                    pass
                else:
                    need_rest = True
                    # 暂停1小时
                    time.sleep(60 * 60)
                if not need_rest:
                    for currency in my_list:
                        monitor_and_treat(currency)
            time.sleep(300)  # 暂停300秒
        # except ValueError as e:
        #     # 普通异常，记录下来即可，程序不终止
        #     print(f"发生了一个异常: {e}")
        #     traceback.print_exc()
        except Exception as e:
            print(f"发生了一个异常: {e}")
            traceback.print_exc()
            alert1.play_error()
            db.close()
            # 特殊异常，程序停止
            break