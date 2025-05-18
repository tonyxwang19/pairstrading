from lib.data_prep import *
import pandas as pd
import akshare as ak
import time
import os

tu = Tushare()
akrequest = AkRequest()

# Step 1: 获取板块数据
industry_stock = akrequest.ak_industry("互联网服务")

# Step 2: 清洗数据 - 去除 ST、价格高的
industry_stock = industry_stock[~industry_stock['名称'].str.contains(r'\*?ST')]
industry_stock['最新价'] = pd.to_numeric(industry_stock['最新价'], errors='coerce')
industry_stock = industry_stock[industry_stock['最新价'] <= 20]

# Step 4: 提取代码列表
stock_list = industry_stock['代码'].tolist()
print(stock_list)
'''

# 参数设定
target_start_date = '20200911'
target_end_date = '20250411'
expected_len = 1108
start_datetime = pd.to_datetime(target_start_date)

# 保存目录
save_folder = "pairtrade_data_csv"
os.makedirs(save_folder, exist_ok=True)

# 有效股票列表
valid_stocks = []

for stock in stock_list:
    try:
        print(f"⏳ 正在处理: {stock}")
        df = ak.stock_zh_a_hist(symbol=stock, start_date=target_start_date, end_date=target_end_date, adjust='', period='daily')

        if df.empty:
            print(f"⚠️ {stock} 数据为空，跳过")
            continue

        # 转换日期字段
        df['日期'] = pd.to_datetime(df['日期'])
        actual_start = df['日期'].iloc[0]

        if actual_start > start_datetime:
            print(f"❌ {stock} 实际起始时间为 {actual_start.date()} 晚于设定的 {start_datetime.date()}，跳过")
            continue

        if len(df) != expected_len:
            print(f"❌ {stock} 数据长度为 {len(df)} ≠ {expected_len}，跳过")
            continue

        # 列名标准化
        df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high',
            '最低': 'low', '成交量': 'volume', '成交额': 'amount'
        }, inplace=True)

        # 保存文件
        save_path = os.path.join(save_folder, f"{stock}.csv")
        df.to_csv(save_path, index=False)
        print(f"✅ {stock} 数据已保存，行数: {len(df)}")
        valid_stocks.append(stock)

        time.sleep(1.5)

    except Exception as e:
        print(f"❌ 错误 - {stock}: {e}")

# 输出最终有效股票列表
print("\n🎯 有效股票（满足起始日期和数据长度）:")
print(valid_stocks)
'''
