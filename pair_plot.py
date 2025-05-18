import os
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm

folder_path = 'pairtrade_data_csv'

df1 = pd.read_csv(os.path.join(folder_path, '300166.csv'))
df2 = pd.read_csv(os.path.join(folder_path, '300150.csv'))

df1['date'] = pd.to_datetime(df1['date'])
df2['date'] = pd.to_datetime(df2['date'])

df1 = df1.set_index('date')
df2 = df2.set_index('date')

# 对齐数据索引
common_index = df1.index.intersection(df2.index)
s1 = df1.loc[common_index, 'close']
s2 = df2.loc[common_index, 'close']


df1['norm'] = df1['close'] / df1['close'].iloc[0]
df2['norm'] = df2['close'] / df2['close'].iloc[0]

plt.figure(figsize=(12, 6))
plt.plot(df1.index, df1['close'], label='300166.SZ (normalized)')
plt.plot(df2.index, df2['close'], label='300150.SZ (normalized)')
plt.title('Pair Trade Price Comparison')
plt.xlabel('Date')
plt.ylabel('Close Price')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

#Regression:
X = sm.add_constant(s2)  # Add constant
model = sm.OLS(s1, X).fit()
beta = model.params[1]

spread = s1 - beta * s2
mean_spread = spread.mean()
std_spread = spread.std()


plt.axhline(mean_spread, color='red', linestyle='--', label=f'Mean = {mean_spread:.2f}')
plt.axhline(mean_spread+std_spread, color='red', linestyle='-', label=f'+Std = {mean_spread+std_spread:.2f}')
plt.axhline(mean_spread-std_spread, color='red', linestyle='-', label=f'-Std = {mean_spread-std_spread:.2f}')
plt.plot(df1.index, spread, label='Spread')
plt.show()

