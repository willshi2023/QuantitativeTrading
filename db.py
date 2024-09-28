import sqlite3
import datetime

import alert1
import constant
import math1
import message1
from decimal import Decimal

from math1 import precision_adjustment_down

conn =None
cursor = None
def init():
    global conn, cursor  # 声明 conn 和 cursor 为全局变量
    # 连接到 SQLite 数据库（如果数据库不存在，会自动创建）
    conn = sqlite3.connect('cryptocurrency.db')

    # 创建游标对象
    cursor = conn.cursor()
    create_tables()


# 创建表
def create_tables():
    sql1 = '''
    CREATE TABLE IF NOT EXISTS cryptocurrency (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        currency TEXT NOT NULL,
        open_price REAL NOT NULL,
        high_price REAL NOT NULL,
        low_price REAL NOT NULL,
        close_price REAL NOT NULL,
        volume REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    '''

    sql2 = '''
    CREATE TABLE IF NOT EXISTS alert_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        currency TEXT NOT NULL,
        change_type TEXT NOT NULL,
        alert_count INTEGER NOT NULL DEFAULT 1
    );
    '''

    sql3 = '''
    CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    currency TEXT,
    direction TEXT,
    buy_price REAL,
    sell_price REAL,
    buy_amount REAL,
    sell_amount REAL,
    fee REAL,
    balance REAL,
    cash REAL,
    timestamp TEXT,
    profit REAL,
    total_profit REAL,
    current_price REAL,  -- 当前的股票价格
    currency_count REAL,   -- 仓位货币个数（允许小数）
    current_position_cost REAL,  -- 本次建仓成本金额
    initial_investment_cost REAL, -- 最初投入成本金额
    profit_rate REAL,            -- 本次交易盈利比例
    total_profit_rate REAL,       -- 累计盈利比例
    transaction_count REAL,       -- 交易的虚拟货币数量
    current_position_price REAL       -- 本次建仓成本价
);
    '''

    cursor.execute(sql1)
    cursor.execute(sql2)
    cursor.execute(sql3)


# 插入数据（cryptocurrency 表）
# 参数分别为 货币类型，开盘价，最高价，最低价，最新价/收盘价，成交量，时间戳
def insert_cryptocurrency(currency, open_price, high_price, low_price, close_price, volume,time_str):
    cursor.execute('''
        INSERT INTO cryptocurrency (currency, open_price, high_price, low_price, close_price, volume,timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (currency, open_price, high_price, low_price, close_price, volume,time_str))
    conn.commit()
    # print(f"Inserted {currency} data successfully.")


# # 查询数据（cryptocurrency 表）
# def fetch_cryptocurrencies():
#     cursor.execute("SELECT * FROM cryptocurrency")
#     rows = cursor.fetchall()
#     print("Cryptocurrency data:")
#     for row in rows:
#         print(row)


def fetch_cryptocurrency_by_currency_and_time(currency, time_str):
    cursor.execute('''
        SELECT * FROM cryptocurrency
        WHERE currency = ? AND timestamp = ?
    ''', (currency,time_str))

    rows = cursor.fetchall()
    # print(f"Cryptocurrency data for {currency} and {time_str}:")
    # for row in rows:
    #     print(row)
    return rows

# # 更新数据（cryptocurrency 表）
# def update_cryptocurrency(id, close_price):
#     cursor.execute('''
#         UPDATE cryptocurrency SET close_price = ? WHERE id = ?
#     ''', (close_price, id))
#     conn.commit()
#     print(f"Updated cryptocurrency with ID {id} successfully.")


# 删除数据（cryptocurrency 表）
# def delete_cryptocurrency(id):
#     cursor.execute('DELETE FROM cryptocurrency WHERE id = ?', (id,))
#     conn.commit()
#     print(f"Deleted cryptocurrency with ID {id} successfully.")


# 插入数据（alert_log 表）
def insert_alert_log(currency, change_type, alert_count,time_str):
    cursor.execute('''
        INSERT INTO alert_log (currency, change_type, alert_count,timestamp)
        VALUES (?, ?, ?, ?)
    ''', (currency, change_type, alert_count,time_str))
    conn.commit()
    # print(f"Inserted alert log for {currency} successfully.")


# # 查询数据（alert_log 表）
# def fetch_alert_logs():
#     cursor.execute("SELECT * FROM alert_log")
#     rows = cursor.fetchall()
#     print("Alert log data:")
#     for row in rows:
#         print(row)


# # 更新数据（alert_log 表）
# def update_alert_log(id, alert_count):
#     cursor.execute('''
#         UPDATE alert_log SET alert_count = ? WHERE id = ?
#     ''', (alert_count, id))
#     conn.commit()
#     print(f"Updated alert log with ID {id} successfully.")


# 删除数据（alert_log 表）
# def delete_alert_log(id):
#     cursor.execute('DELETE FROM alert_log WHERE id = ?', (id,))
#     conn.commit()
#     print(f"Deleted alert log with ID {id} successfully.")

def close():
    cursor.close()
    conn.close()
    print("Database connection closed.")


# 增加记录
def add_trade(currency, direction, buy_price, sell_price, buy_amount, sell_amount, fee, balance, cash,
                 profit, total_profit, current_price, currency_count, current_position_cost, initial_investment_cost,
                 profit_rate, total_profit_rate,transaction_count,current_position_price):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
            INSERT INTO trades (
                currency, direction, buy_price, sell_price, buy_amount, sell_amount, 
                fee, balance, cash, timestamp, profit, total_profit, 
                current_price, currency_count, current_position_cost, 
                initial_investment_cost, profit_rate, total_profit_rate,
                transaction_count,current_position_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
        currency, direction, buy_price, sell_price, buy_amount, sell_amount,
        fee, balance, cash, timestamp, profit, total_profit,
        current_price, currency_count, current_position_cost,
        initial_investment_cost, profit_rate, total_profit_rate,
        transaction_count,current_position_price
    ))

    conn.commit()
    # 同步铃声
    alert1.play_remind()
    # 推送消息到手机 货币种类 交易类型:买/卖 本次交易盈利比例 累计盈利比例
    # 只有上交是购买，其余都是卖掉
    transaction_type = constant.SELL
    if direction == constant.CROSS_UP:
        transaction_type = constant.BUY
    # 交易金额，如果交易是买，就是买币的价格，如果是卖，就是卖币的价格
    treat_amount = None
    # 当前币价，如果交易是买，就是买时的币价，如果是卖，就是卖时的币价
    current_price = None
    if transaction_type == constant.BUY:
        treat_amount = buy_amount
        current_price = buy_price
    elif transaction_type == constant.SELL:
        treat_amount = sell_amount
        current_price = sell_price
    profit_rate100 = math1.precision_adjustment_down(Decimal(profit_rate*100),constant.PROFIT_PRECISION)
    total_profit_rate100 = math1.precision_adjustment_down(Decimal(total_profit_rate * 100),constant.PROFIT_PRECISION)
    # 本次建仓买币数量 = 本次建仓成本金额 / 本次建仓成本价
    current_position_count = precision_adjustment_down(Decimal(current_position_cost) / Decimal(current_position_price),constant.COIN_COUNT_PRECISION)
    # 活钱余额 进行 向下精度计算
    cash = math1.precision_adjustment_down(Decimal(cash),constant.ACCOUNT_PRECISION)
    # 累计盈利 进行 向下精度计算
    total_profit = math1.precision_adjustment_down(Decimal(total_profit),constant.ACCOUNT_PRECISION)
    message2 = (
        f'货币种类: *{currency}*\n'
        f'交易类型: *{transaction_type}*\n'
        f'时间: *{timestamp}*\n'
        f'\n'
        f'本次建仓成本价: *{current_position_price}*\n'
        f'本次建仓买币数量: *{current_position_count}*\n'
        f'本次建仓成本金额: *{current_position_cost}*\n'
        f'当前币价: *{current_price}*\n'
        f'本次交易币数量: *{transaction_count}*\n'
        f'本次买入/卖出金额: *{treat_amount}*\n'
        f'仓位剩余货币个数: *{currency_count}*\n'
        f'本次交易盈利: *{profit}*\n'
        f'本次交易盈利比例: *{profit_rate100}%*\n'
        f'本次手续费: *{fee}*\n'
        f'\n'
        f'最初投入成本金额: *{initial_investment_cost}*\n'
        f'仓位余额: *{balance}*\n'
        f'活钱余额: *{cash}*\n'
        f'累计盈利: *{total_profit}*\n'
        f'累计盈利比例: *{total_profit_rate100}%*'
    )
    print(message2)
    message1.send_message2group(message2)
    message1.send_message_by_push_deer(message2)


def get_total_profit():
    cursor.execute("SELECT SUM(profit) FROM trades")
    total_profit = cursor.fetchone()[0]

    return total_profit or 0  # 如果没有记录,返回0

# 获取已经持续上涨的次数，每涨一次，持仓稀释一半
def get_rise_count():
    cursor.execute('''
    select COUNT(1) from trades t1 
where 1=1
and t1.id> 
(
select t.id from trades t 
where t.direction = '上交' order by t.id desc limit 1
)
    ''')
    rise_count = cursor.fetchone()[0]

    return rise_count or 0  # 如果没有记录,返回0

# # 删除记录
# def delete_trade(trade_id):
#     cursor.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
#     conn.commit()


# # 更新记录
# def update_trade(trade_id, currency, direction, buy_price, sell_price, buy_amount, sell_amount, fee, balance, cash):
#     timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     profit = (sell_price * sell_amount) - (buy_price * buy_amount) - fee
#     total_profit = get_total_profit() + profit - get_trade_profit(trade_id)
#
#     cursor.execute(
#         "UPDATE trades SET currency = ?, direction = ?, buy_price = ?, sell_price = ?, buy_amount = ?, sell_amount = ?, fee = ?, balance = ?, cash = ?, timestamp = ?, profit = ?, total_profit = ? WHERE id = ?",
#         (currency, direction, buy_price, sell_price, buy_amount, sell_amount, fee, balance, cash, timestamp, profit,
#          total_profit, trade_id))
#
#     conn.commit()

#
# def get_trade_profit(trade_id):
#     cursor.execute("SELECT profit FROM trades WHERE id = ?", (trade_id,))
#     profit = cursor.fetchone()[0]
#
#     return profit


# 查询记录
# def get_trades():
#     cursor.execute("SELECT * FROM trades")
#     trades = cursor.fetchall()
#
#     return trades


# 获取最后一条数据
def get_last_trade():
    cursor.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 1")
    latest_trade = cursor.fetchone()

    return latest_trade

# # 获得买入价
# def get_buy_price(inst_id):
#     latest_trade = get_last_trade()
#     if latest_trade[1] == inst_id:
#         cursor.execute("SELECT buy_price FROM trades WHERE currency = ? and direction= ? order by id desc limit 1", (inst_id,constant.CROSS_UP))
#         profit = cursor.fetchone()[3]
#         return profit
#     return None


# 获取最新的一次上交
# def get_latest_cross_up_trade():
#     cursor.execute("SELECT * FROM trades where direction = ? ORDER BY id DESC LIMIT 1", (constant.CROSS_UP,))
#     latest_cross_up_trade = cursor.fetchone()
#
#     return latest_cross_up_trade

#
# def get_latest_up_trade_count(latest_cross_up_id):
#     cursor.execute("SELECT count(1) FROM trades where id > ? ", (latest_cross_up_id,))
#     latest_cross_up_trade = cursor.fetchone()
#
#     return latest_cross_up_trade[0]


# def calc_up_count():
#     # 获取最新的一次操作，必须不是下交，然后获取最新的一次上交，最后取id超过上交的数量即可
#     latest_trade = get_last_trade()
#     if latest_trade[2] != constant.CROSS_DOWN:
#         latest_cross_up_trade = get_latest_cross_up_trade()
#         if not latest_cross_up_trade:
#             return 0
#         latest_cross_up_id = latest_cross_up_trade[0]
#         return get_latest_up_trade_count(latest_cross_up_id)
#     return 0
# 主程序
if __name__ == "__main__":
    init()
    create_tables()  # 创建表
    rise_count = get_rise_count()
    print(rise_count)
    # add_trade('SHIB-USDT',constant.CROSS_UP,56000.0,0,100000.0,0,2.23,100000.0,1000,-0.14,5112,55456.6,0.4455,76542.1,10000,0.1,1.2,100.1)
    #
    # # 示例插入数据
    # insert_cryptocurrency('BTC', 30000, 31000, 29000, 30500, 1500)
    # insert_cryptocurrency('ETH', 2000, 2100, 1950, 2050, 800)
    #
    # # 查询数据
    # fetch_cryptocurrencies()
    #
    # # 更新数据
    # update_cryptocurrency(1, 30600)
    #
    # # 删除数据
    # delete_cryptocurrency(2)
    #
    # # 插入提醒日志
    # insert_alert_log('BTC', '上涨', 1)
    # insert_alert_log('ETH', '下跌', 2)
    #
    # # 查询提醒日志
    # fetch_alert_logs()
    #
    # # 更新提醒日志
    # update_alert_log(1, 3)
    #
    # # 删除提醒日志
    # delete_alert_log(2)

    # fetch_cryptocurrency_by_currency_and_time('BTC','2024-09-07 08:18:55')
    close()
