CROSS_UP = '上交'
CROSS_DOWN = '下交'
BUY = '买入'
SELL = '卖出'
UP = '涨'
DOWN = '跌'
# 交易手续费费率
FEE_RATE = 0.001
# 账户余额小数点精度
ACCOUNT_PRECISION = 8
# 可以购买的虚拟币的小数点的精度
COIN_COUNT_PRECISION =8
# 预设的收益率，涨了这么多就抛出
INCREASE_RATIO = 0.015
# 统计的盈利比例精度
PROFIT_PRECISION = 4
# 最初投入成本金额
INITIAL_INVESTMENT_COST = 10000
# 止损位：快速跳出诱多陷阱，垃圾车不上也没关系，甩下了就甩下了，少上几次垃圾车，多上好车
# 首先是稳，其次才是收益，求稳的前提下，尽可能提高收益才是重点，做成数学，要通过数学赚钱，而不是盲目赚钱
# 在概率的条件下，确保即使只卖出一次，即便是有诱多陷阱，也不会亏损，只有当一次也没卖出的特别垃圾车才会亏损，但是亏损的也不多
ESCAPE_BULL_TRAP_RATIO = -0.01
# 最大稀释次数，如果股价一直没有交，一直蹭蹭蹭的往上涨，如果一直卖出，大概率要等很久，因为仓位又不多了，卖也卖不了几个钱，
# 干脆就不等了，直接清仓，与其为了赚仓位很少的钱苦苦等待浪费时间，不如直接等下一次机会更合理，赚到的更多
MAXIMUM_DILUTION_COUNT = 2
PUSH_DEER_KEY = '你的key'
TELEGRAM_BOT_TOKEN = '你的key'