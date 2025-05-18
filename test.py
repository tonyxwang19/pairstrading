import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np


df1 = pd.read_csv('pairtrade_data_csv/300166.csv', parse_dates=['date'])
df2 = pd.read_csv('pairtrade_data_csv/300150.csv', parse_dates=['date'])

# df1 = pd.read_csv('pairtrade_data_csv/300523.csv', parse_dates=['date'])
# df2 = pd.read_csv('pairtrade_data_csv/000555.csv', parse_dates=['date'])

# df1 = pd.read_csv('pairtrade_data_csv/600410.csv', parse_dates=['date'])
# df2 = pd.read_csv('pairtrade_data_csv/300150.csv', parse_dates=['date'])

# df1 = pd.read_csv('pairtrade_data_csv/688365.csv', parse_dates=['date'])
# df2 = pd.read_csv('pairtrade_data_csv/300170.csv', parse_dates=['date'])


df1.set_index('date', inplace=True)
df2.set_index('date', inplace=True)


def calculate_max_drawdown(cum_profits):
    peak = cum_profits[0]
    max_drawdown = 0
    peak_idx = 0
    valley_idx = 0

    for i in range(1, len(cum_profits)):
        if cum_profits[i] > peak:
            peak = cum_profits[i]
            peak_idx = i
        drawdown = peak - cum_profits[i]
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            valley_idx = i

    return max_drawdown, peak_idx, valley_idx

class PairTradeStrategy(bt.Strategy):
    params = dict(
        entry_z= 1.5,
        exit_z= 0.2,
        lookback=200
    )

    def __init__(self):
        self.data0 = self.datas[0]  # stock1
        self.data1 = self.datas[1]  # stock2
        self.order = None
        self.entry_price_stock0 = None
        self.entry_price_stock1 = None
        self.position_type = None
        self.total_trades = 0
        self.winning_trades = 0
        self.positive_profit = 0
        self.negative_profit = 0

        self.trade_profits = []  # 保存每笔套利的盈亏
        self.cumulative_profits = []  # 保存累计收益曲线
        self.trade_records = []


    def next(self):
        if self.broker.get_cash() < self.data0.close[0] * 100:
            return  # 资金不足，跳过本次交易

        if len(self.data0) < self.params.lookback:
            return

        # 取过去 lookback 天的收盘价
        s1 = pd.Series([self.data0.close[-i] for i in range(self.params.lookback)][::-1])
        s2 = pd.Series([self.data1.close[-i] for i in range(self.params.lookback)][::-1])

        # 回归
        X = sm.add_constant(s2)
        model = sm.OLS(s1, X).fit()
        beta = model.params.iloc[1]

        spread = s1 - beta * s2
        z = (spread.iloc[-1] - spread.mean()) / spread.std()

        # 平仓条件
        if self.position_type == "long" and abs(z) < self.params.exit_z:
            self.sell(data=self.data0, size=100)
            self.buy(data=self.data1, size=100)
            self.calculate_profit('long')

        if self.position_type == "short" and abs(z) < self.params.exit_z:
            self.buy(data=self.data0, size=100)
            self.sell(data=self.data1, size=100)
            self.calculate_profit('short')

        if z > self.params.entry_z and self.position_type == None:
            # 做空 spread: 卖 s1, 买 s2
            self.sell(data=self.data0,size = 100)
            self.buy(data=self.data1,size = 100)
            self.entry_price_stock0 = self.data0.close[0]
            self.entry_price_stock1 = self.data1.close[0]
            self.position_type = "short"

        elif z < -self.params.entry_z and self.position_type == None:
            # 做多 spread: 买 s1, 卖 s2
            self.buy(data=self.data0,size = 100)
            self.sell(data=self.data1,size = 100)
            self.entry_price_stock0 = self.data0.close[0]
            self.entry_price_stock1 = self.data1.close[0]
            self.position_type = "long"

    def calculate_profit(self, position_type):
        exit_price_stock0 = self.data0.close[0]
        exit_price_stock1 = self.data1.close[0]

        if position_type == 'long':
            # 多：买入data0，卖出data1
            profit_stock0 = (exit_price_stock0 - self.entry_price_stock0) * 100
            profit_stock1 = (self.entry_price_stock1 - exit_price_stock1) * 100
        elif position_type == 'short':
            # 空：卖出data0，买入data1
            profit_stock0 = (self.entry_price_stock0 - exit_price_stock0) * 100
            profit_stock1 = (exit_price_stock1 - self.entry_price_stock1) * 100
        else:
            profit_stock0 = profit_stock1 = 0

        self.total_trades += 1
        total_profit = profit_stock0 + profit_stock1

        if total_profit > 0:
            self.winning_trades += 1
            self.positive_profit = self.positive_profit + total_profit
        elif total_profit < 0:
            self.negative_profit = self.negative_profit + total_profit

        # print('=== Trade Completed ===')
        # print('Entry Date: {}, Exit Date: {}'.format(self.data.datetime.date(-1), self.data.datetime.date(0)))
        # print('Stock 0 - Entry Price: {:.2f}, Exit Price: {:.2f}, Profit: {:.2f}'.format(self.entry_price_stock0,
        #                                                                                  exit_price_stock0,
        #                                                                                  profit_stock0))
        # print('Stock 1 - Entry Price: {:.2f}, Exit Price: {:.2f}, Profit: {:.2f}'.format(self.entry_price_stock1,
        #                                                                                  exit_price_stock1,
        #                                                                                  profit_stock1))
        # print('Total Arbitrage Profit: {:.2f}'.format(total_profit))
        # print('=========================')

        #Keep the trading record
        trade_record = {
            'Entry Date': str(self.data.datetime.date(-1)),
            'Exit Date': str(self.data.datetime.date(0)),
            'Profit': total_profit,
            'Win': 1 if total_profit > 0 else 0
        }
        self.trade_records.append(trade_record)

        self.trade_profits.append(total_profit)

        # 更新累计收益
        if len(self.cumulative_profits) == 0:
            self.cumulative_profits.append(total_profit)
        else:
            self.cumulative_profits.append(self.cumulative_profits[-1] + total_profit)

        # 清空记录
        self.entry_price_stock0 = None
        self.entry_price_stock1 = None
        self.entry_date = None
        self.position_type = None

# 创建Cerebro回测引擎
cerebro = bt.Cerebro()

data_feed_0 = bt.feeds.PandasData(dataname=df1)
data_feed_1 = bt.feeds.PandasData(dataname=df2)


# 创建数据输入源，注意传入处理后的DataFrame
cerebro.adddata(data_feed_0)
cerebro.adddata(data_feed_1)

cerebro.broker.setcommission(0.001)

# 添加策略
cerebro.addstrategy(PairTradeStrategy)

# 设置初始资金
cerebro.broker.set_cash(3000)

# 在运行回测之前，添加以下绘图设置
cerebro.addobserver(bt.observers.DrawDown)  # 添加回撤观察器
cerebro.addobserver(bt.observers.BuySell)   # 添加买卖点观察器
cerebro.addobserver(bt.observers.Value)     # 添加资产价值观察器

# 添加最大回撤和夏普比率分析器
cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Days, riskfreerate=0.0)

# 显示初始资金
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# 运行回测，并接收回测结果
result = cerebro.run()
strategy = result[0]

# 显示结束时资金
print('Ending Portfolio Value: %.2f' % cerebro.broker.getvalue())


# 打印最大回撤
max_dd, peak_trade, valley_trade = calculate_max_drawdown(strategy.cumulative_profits)

print(f'Maximum Drawdown: {max_dd:.2f}')
print(f'Occurred between Trade {peak_trade} and Trade {valley_trade}')

# 打印夏普比率
sharpe_ratio = strategy.analyzers.sharpe.get_analysis().get('sharperatio', None)
print('Sharpe Ratio: %.2f' % sharpe_ratio)

win_rate = strategy.winning_trades / strategy.total_trades
print('Total Trades: {}'.format(strategy.total_trades))
print('Winning Rate: {:.2f}%'.format(win_rate * 100))

avgpos_profit = strategy.positive_profit / strategy.total_trades
avgneg_profit = strategy.negative_profit / strategy.total_trades

print('Average Earning: {}'.format(avgpos_profit))
print('Average Loss: {}'.format(avgneg_profit))

trade_df = pd.DataFrame(strategy.trade_records)

# 展示
# print(trade_df)

trade_df.to_excel('trade_records.xlsx', index=False)


# 创建绘图对象
cerebro.plot(style='candlestick',   # 使用K线图样式
                   barup='red',            # 上涨蜡烛颜色
                   bardown='green',        # 下跌蜡烛颜色
                   volume=True,            # 显示成交量
                   subtxtsize=7,          # 子图文本大小
                   plotdist=0.1,          # 图表间距
                   grid=True,             # 显示网格
                   width=16,              # 图表宽度
                   height=9,              # 图表高度
                   dpi=100,              # 分辨率
                   tight=True)            # 紧凑布局

# 直方图：盈亏分布
plt.figure(figsize=(10,6))
plt.hist(strategy.trade_profits, bins=15, edgecolor='black')
plt.title('Distribution of Arbitrage Trade Profits')
plt.xlabel('Profit per Trade')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()

# 折线图：累计收益曲线
plt.figure(figsize=(10,6))
plt.plot(strategy.cumulative_profits, marker='o')
plt.title('Cumulative Arbitrage Profit Curve')
plt.xlabel('Trade Number')
plt.ylabel('Cumulative Profit')
plt.grid(True)
plt.show()