import os
import sys
import pandas as pd
from tqdm import tqdm
sys.path.append(os.getcwd())
from retavg_rule import ReturnAvgRule

prices = pd.read_csv(
    os.path.join(
        os.getcwd(), 'data', 'raw', 'candles_SBER.csv'),
    index_col=0)
prices.columns = ['o', 'h', 'l', 'p', 'v', 't']
prices['t'] = pd.to_datetime(prices['t'], format='mixed')
prices['t'] = prices['t'].dt.tz_localize(None)
prices['week'] = prices['t'].dt.day_of_week
prices = prices[~prices['week'].isin([5, 6])].reset_index(drop=True)

ra = ReturnAvgRule(
    data_cash_size=60,
    low_q=0.9, high_q=0.7,
    sl=-1, window_avg=5,
    window_diff_high_avg=5, window_diff_avg_low=6,
    avgprice_quantile_dist=0.5
)

deals_profit = []
for i in tqdm(range(prices.shape[0]), total=prices.shape[0]):
    h, l, p = prices[['h', 'l', 'p']].iloc[i]
    signal = ra.get_signal((h, l, p))
    if signal is not None and signal['action'] == 'close':
        deals_profit.append(signal['profit_current'])
print(sum(deals_profit))
