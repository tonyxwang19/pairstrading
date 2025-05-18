from lib.backtest import *
import backtrader as bt
import pandas as pd
import statsmodels.api as sm

# 加载数据
df1 = pd.read_csv('pairtrade_data_csv/300166.csv', parse_dates=['date'])
df2 = pd.read_csv('pairtrade_data_csv/300150.csv', parse_dates=['date'])


df1.set_index('date', inplace=True)
df2.set_index('date', inplace=True)



# class PairTradeStrategy(bt.Strategy):
#     params = dict(
#         entry_z= 1.2,
#         exit_z= 0.2,
#         lookback=150
#     )
#
#     def __init__(self):
#         self.data0 = self.datas[0]  # stock1
#         self.data1 = self.datas[1]  # stock2
#         self.spread = []  # 用于计算 rolling mean/std
#         self.order = None
#         self.long_spread = False
#         self.short_spread = False
#
#     def next(self):
#         if len(self.data0) < self.params.lookback:
#             return
#         notional = 10000
#
#         price1 = self.data0.close[0]
#         price2 = self.data1.close[0]
#
#         qty1 = int((notional / 2) / price1)
#         qty2 = int((notional / 2) / price2)
#
#         # 取过去 lookback 天的收盘价
#         s1 = pd.Series([self.data0.close[-i] for i in range(self.params.lookback)][::-1])
#         s2 = pd.Series([self.data1.close[-i] for i in range(self.params.lookback)][::-1])
#
#         # 回归
#         X = sm.add_constant(s2)
#         model = sm.OLS(s1, X).fit()
#         beta = model.params.iloc[1]
#
#         spread = s1 - beta * s2
#         z = (spread.iloc[-1] - spread.mean()) / spread.std()
#
#         # 平仓条件
#         if self.long_spread or self.short_spread:
#             if abs(z) < self.params.exit_z:
#                 self.close(self.data0)
#                 self.close(self.data1)
#                 self.long_spread = self.short_spread = False
#                 return
#
#         # 开仓条件
#         if not self.position:
#             if z > self.params.entry_z:
#                 # 做空 spread: 卖 s1, 买 s2
#                 self.sell(data=self.data0, size=qty1)
#                 # self.buy(data=self.data1, size=int(1000 * beta))
#                 self.buy(data=self.data1, size=qty2)
#                 self.short_spread = True
#             elif z < -self.params.entry_z:
#                 # 做多 spread: 买 s1, 卖 s2
#                 self.buy(data=self.data0, size=qty1)
#                 # self.sell(data=self.data1, size=int(1000 * beta))
#                 self.sell(data=self.data1, size=qty2)
#                 self.long_spread = True


class PairTradeStrategy(bt.Strategy):
    params = dict(
        entry_z= 0.8,
        exit_z= 0.5,
        lookback=150
    )

    def __init__(self):
        self.data0 = self.datas[0]  # stock1
        self.data1 = self.datas[1]  # stock2
        self.spread = []  # 用于计算 rolling mean/std
        self.order = None
        self.long_spread = False
        self.short_spread = False

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
        if self.long_spread and abs(z) < self.params.exit_z:
            self.sell(data=self.data0, size=100)
            self.buy(data=self.data1, size=100)
            self.long_spread = self.short_spread = False
            return
        if self.short_spread and abs(z) < self.params.exit_z:
            self.buy(data=self.data0, size=100)
            self.sell(data=self.data1, size=100)
            self.long_spread = self.short_spread = False

        if z > self.params.entry_z and self.short_spread == False:
            # 做空 spread: 卖 s1, 买 s2
            self.sell(data=self.data0,size = 100)
            self.buy(data=self.data1,size = 100)
            self.short_spread = True
        elif z < -self.params.entry_z and self.long_spread == False:
            # 做多 spread: 买 s1, 卖 s2
            self.buy(data=self.data0,size = 100)
            self.sell(data=self.data1,size = 100)
            self.long_spread = True

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return  # 订单提交中或已接受，还未成交

        if order.status in [order.Completed]:
            action = '买入' if order.isbuy() else '卖出'
            print(f"{self.datetime.date()} 执行订单: {action} {order.data._name} "
                  f"数量: {order.size} 价格: {order.executed.price:.2f} "
                  f"成本: {order.executed.value:.2f} 手续费: {order.executed.comm:.2f}")

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(f"{self.datetime.date()} 订单失败: {order.Status[order.status]}")

    def notify_trade(self, trade):
        if trade.isclosed:
            print(f"{self.datetime.date()} 交易完成: 总盈亏: {trade.pnl:.2f} "
                  f"毛利: {trade.pnlcomm:.2f} 手续费: {trade.commission:.2f}")

br = BacktestRunner(strategy_class=PairTradeStrategy, data_feeds=[df1,df2], timeframe=bt.TimeFrame.Days)
br.run()