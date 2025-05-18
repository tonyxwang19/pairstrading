import os
import itertools
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

# 获取 CSV 文件夹路径
folder_path = 'pairtrade_data_csv'

# 获取所有 .csv 文件
csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
print(f"共发现 {len(csv_files)} 个股票数据文件")

cointegrated_pairs = []

for file1, file2 in itertools.combinations(csv_files, 2):
    # 读取数据
    df1 = pd.read_csv(os.path.join(folder_path, file1))
    df2 = pd.read_csv(os.path.join(folder_path, file2))

    df1['date'] = pd.to_datetime(df1['date'])
    df2['date'] = pd.to_datetime(df2['date'])

    df1 = df1.set_index('date')
    df2 = df2.set_index('date')

    # 对齐数据索引
    common_index = df1.index.intersection(df2.index)
    s1 = df1.loc[common_index, 'close']
    s2 = df2.loc[common_index, 'close']

    # 回归 + 残差
    X = sm.add_constant(s2)
    model = sm.OLS(s1, X).fit()
    residuals = s1 - model.predict(X)

    # ADF 检验残差
    adf_result = adfuller(residuals)
    p_value = adf_result[1]

    if p_value < 0.05:
        cointegrated_pairs.append({
            'stock1': file1.replace('.csv', ''),
            'stock2': file2.replace('.csv', ''),
            'p_value': p_value,
            'ADF_stat': adf_result[0]
        })

result_df = pd.DataFrame(cointegrated_pairs)
result_df = result_df.sort_values(by='p_value')
result_df.to_csv("cointegrated_pairs.csv", index=False)

# plt.figure(figsize=(12, 6))
#
# stock1['norm'] = stock1['close'] / stock1['close'].iloc[0]
# stock2['norm'] = stock2['close'] / stock2['close'].iloc[0]
#
# plt.plot(stock1.index, stock1['norm'], label='000409.SZ (normalized)')
# plt.plot(stock2.index, stock2['norm'], label='300017.SZ (normalized)')
#
#
# plt.title('Pair Trade Price Comparison')
# plt.xlabel('Date')
# plt.ylabel('Close Price')
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.show()

# # Step 1: 对 stock1 和 stock2 做线性回归
# X = sm.add_constant(s2)  # 加常数项
# model = sm.OLS(s1, X).fit()
# print(model.summary())
#
# # Step 2: 获取残差（residual）
# residuals = s1 - model.predict(X)
#
# # Step 3: 对残差做ADF检验
# adf_result = adfuller(residuals)
# print("ADF Statistic:", adf_result[0])
# print("p-value:", adf_result[1])
# for key, value in adf_result[4].items():
#     print(f"Critical Value {key}: {value}")
#
# # 判别是否协整
# if adf_result[1] < 0.05:
#     print("✅ 协整存在：这对股票可能适合做配对交易")
# else:
#     print("❌ 没有协整关系")