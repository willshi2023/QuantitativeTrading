from decimal import Decimal, ROUND_UP, ROUND_DOWN

import constant


# 向上调整到目标精度 value_d Decimal类型的金额  precision int类型的精度
def precision_adjustment_up(value_d, precision):
    # 设置目标精度
    target_precision = precision
    # 向上调整到目标精度
    value_rounded_up = value_d.quantize(Decimal('0.' + '0' * (target_precision - 1) + '1'), rounding=ROUND_UP)
    return value_rounded_up
# 向下调整到目标精度 str1 Decimal类型的金额  precision int类型的精度
def precision_adjustment_down(value_d, precision):
    # 设置目标精度
    target_precision = precision
    # 向下调整到目标精度
    value_rounded_down = value_d.quantize(Decimal('0.' + '0' * (target_precision - 1) + '1'), rounding=ROUND_DOWN)
    return value_rounded_down

# 买币的个数 = 总金额 / (比特币价格 + 手续费) 向下调整精度
def calc_buy_coin_count(cash,price):
    coin_count = cash / (price * (Decimal(1) + Decimal(constant.FEE_RATE)))
    coin_count = precision_adjustment_down(coin_count,constant.COIN_COUNT_PRECISION)
    return coin_count
# 买币的金额 = 比特币价格 * 买币的个数 向上精度调整
def calc_buy_coin_amount(cash,price):
    coin_count = calc_buy_coin_count(cash,price)
    price_float = float(price)
    buy_coin_amount = price_float * coin_count
    buy_coin_amount = precision_adjustment_up(buy_coin_amount,constant.ACCOUNT_PRECISION)
    return buy_coin_amount
# 买币的手续费 = 平台手续费 * 买币的个数 向上精度调整
def calc_buy_coin_fee(cash,price):
    buy_coin_count = calc_buy_coin_count(cash,price)
    buy_coin_fee = buy_coin_count* constant.FEE_RATE
    buy_coin_fee = precision_adjustment_up(buy_coin_fee, constant.ACCOUNT_PRECISION)
    return buy_coin_fee

# 计算下一次预估卖出价 : 上一次交易币价 * (预设的收益率 + 1) 精度向下即可
def calc_next_estimate_sell_price(previous_treat_price):
    next_estimate_sell_price = precision_adjustment_down(previous_treat_price * (Decimal(1) + Decimal(constant.INCREASE_RATIO)), constant.ACCOUNT_PRECISION)
    return next_estimate_sell_price
# 计算当前价格卖出半仓的
# 入参: 本次建仓成本价，上一次仓位余额,上一次活钱余额，最新币价，上一次仓位剩余货币个数，
# 返回值：买入金额，卖出金额，手续费，手续费，本次结算后仓位余额，本次结算后活钱余额，本次仓位剩余货币个数，本次交易盈利，累计盈利，本次交易盈利比例，累计盈利比例
def calc_sell_half_position(current_position_price,balance, cash, current_price,currency_count):
    return calc_core(current_position_price,current_price,Decimal(0),currency_count/2,balance,cash,currency_count,constant.INITIAL_INVESTMENT_COST)

# 计算全部买入需要的各种数据:零头就不算了，送给区块链了，实际上赚的话会更多，但是多不了几毛钱
# 入参: 本次建仓成本价，最新币价，买入数量，上一次活钱余额，最初投入成本金额
# 返回值：买入金额，卖出金额，手续费，手续费，本次结算后仓位余额，本次结算后活钱余额，本次仓位剩余货币个数，本次交易盈利，累计盈利，本次交易盈利比例，累计盈利比例
def calc_buy_all(current_position_price,current_price,buy_count,cash,initial_investment_cost):
    return calc_core(current_position_price,current_price,buy_count,Decimal(0),Decimal(0),cash,Decimal(0),initial_investment_cost)

# 计算全部抛售需要的各种数据
# 入参：本次建仓成本价，最新币价，买入数量，卖出数量，上一次仓位余额，上一次活钱余额，上一次仓位剩余货币个数，最初投入成本金额
# 返回值：买入金额，卖出金额，手续费，手续费，本次结算后仓位余额，本次结算后活钱余额，本次仓位剩余货币个数，本次交易盈利，累计盈利，本次交易盈利比例，累计盈利比例
def calc_sell_all(current_position_price,current_price,sell_count,balance,cash,currency_count,initial_investment_cost):
    return calc_core(current_position_price,current_price,Decimal(0),sell_count,balance,cash,currency_count,initial_investment_cost)

# 根据传入的买卖金额及数量，计算各种手续费，仓位剩余，盈利情况，
# 入参：本次建仓成本价，最新币价，买入数量，卖出数量，上一次仓位余额，上一次活钱余额，上一次仓位剩余货币个数，最初投入成本金额
# 返回值：买入金额，卖出金额，手续费，手续费，本次结算后仓位余额，本次结算后活钱余额，本次仓位剩余货币个数，本次交易盈利，累计盈利，本次交易盈利比例，累计盈利比例
def calc_core(current_position_price,current_price, buy_count, sell_count, previous_balance, previous_cash, previous_currency_count, initial_investment_cost):
    # 买入金额 = 买入数量 * 最新币价  向上取精度
    # 买入卖出金额不考虑手续费
    buy_amount = precision_adjustment_up(buy_count * current_price , constant.ACCOUNT_PRECISION)
    # 卖出金额 = 卖出数量 * 最新币价  向上取精度
    sell_amount = precision_adjustment_up(sell_count * current_price , constant.ACCOUNT_PRECISION)
    # 买卖币数 要么买，要么卖
    coin_count = buy_count
    if sell_count >buy_count:
        coin_count = sell_count
    # 手续费 = 现价 * 买卖币数 * 手续费率 向上取精度
    fee = precision_adjustment_up(current_price * coin_count * Decimal(constant.FEE_RATE), constant.ACCOUNT_PRECISION)
    # 本次结算后活钱余额 = 前一次的活钱余额 - 买入金额 + 卖出金额 - 手续费
    # 如果是买入 = 前一次的活钱余额 - 买入金额 - 手续费
    if buy_amount > sell_amount:
        new_cash = previous_cash - buy_amount - fee
    else:
    # 如果是卖出 = 前一次的活钱余额 + 卖出金额 - 手续费
        new_cash = previous_cash + sell_amount - fee
    # 本次仓位剩余货币个数 = 上一次仓位剩余货币个数 + 买入数量 - 卖出数量
    new_currency_count = precision_adjustment_down(previous_currency_count + buy_count - sell_count,constant.COIN_COUNT_PRECISION)
    # 本次结算后仓位余额 = 本次仓位剩余货币个数 * 最新币价 精度向下
    new_balance = precision_adjustment_down(new_currency_count * current_price, constant.ACCOUNT_PRECISION)
    # 本次交易盈利 = 毛利润 - 手续费（仅限本回合的本次交易） - 手续费（仅限本回合的本次交易）
    # 毛利润 = 卖出数量 *（ 最新币价 - 本次建仓成本价）
    # 手续费 = 买入数量 * 最新币价 * 手续费率
    # 手续费 = 卖出数量 * 最新币价 * 手续费率
    # 精度向下调整
    profit = (sell_count * (current_price - current_position_price)
              - buy_count * current_price * Decimal(constant.FEE_RATE)
              -sell_count * current_price * Decimal(constant.FEE_RATE))
    profit = precision_adjustment_down(profit, constant.ACCOUNT_PRECISION)
    # 累计盈利 = 本次结算后仓位余额 + 本次结算后活钱余额 - 最初投入成本金额
    total_profit = new_balance + new_cash - initial_investment_cost
    # 交易金额，如果交易是买，就是买币的价格，如果是卖，就是卖币的价格
    treat_amount = buy_amount
    if sell_amount > buy_amount:
        treat_amount = sell_amount
    # 本次交易盈利比例 = 本次交易盈利 / (本次交易金额) 向下取精度
    profit_rate = precision_adjustment_down(profit / treat_amount, constant.ACCOUNT_PRECISION)
    # 累计盈利比例 = 累计盈利 / 最初投入成本金额 向下取精度
    total_profit_rate = precision_adjustment_down(total_profit / initial_investment_cost, constant.ACCOUNT_PRECISION)
    # 返回值：买入金额，卖出金额，手续费，手续费，本次结算后仓位余额，本次结算后活钱余额，本次仓位剩余货币个数，本次交易盈利，累计盈利，本次交易盈利比例，累计盈利比例
    return buy_amount,sell_amount,fee,fee,new_balance,new_cash,new_currency_count,profit,total_profit,profit_rate,total_profit_rate

# 计算是否是诱多陷阱
def is_bull_trap(buy_price, current_price):
    return (current_price-buy_price)/buy_price <= Decimal(constant.ESCAPE_BULL_TRAP_RATIO)


if __name__ == '__main__':
    # 调用本函数，参数一律都得传入 Decimal !!!
    var1 = is_bull_trap(Decimal(100),Decimal(99))
    print(var1)


