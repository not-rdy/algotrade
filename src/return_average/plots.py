import os
import sys
import pandas as pd
sys.path.append(os.getcwd())
from retavg_rule import ReturnAvgRule
from src.utils import prepare_candles, figax

CANDLES_NAME = 'candles_ABRD_min.csv'

candles = prepare_candles(
    os.path.join(os.getcwd(), 'data', 'raw', CANDLES_NAME))

# func get deals data
days = candles['date'].unique()
profits = []
for day in days:
    ra = ReturnAvgRule(
        data_cash_size=60,
        low_q=0.5, high_q=1, sl=-0.8, window_avg=4,
        window_diff_high_avg=5, window_diff_avg_low=5,
        variance=0.08, avgprice_quantile_dist=0.16)
    df = candles[candles['t'].dt.date == day]
    for idx, row in df[['h', 'l', 'p']].iterrows():
        ra.get_signal((row['h'], row['l'], row['p']))
    profits.append({'day': day, 'profit': ra.profit})
    content = ra.get_content()
    fig, ax = figax(df=content)
    fig.suptitle(ra.profit)
    fig.savefig(os.path.join(os.getcwd(), 'data', 'plots', str(day)))
pd.DataFrame(profits).set_index('day').cumsum().plot(grid=True)\
    .figure.savefig(os.path.join(os.getcwd(), 'data', 'plots', str(day)+'cumsum'))
