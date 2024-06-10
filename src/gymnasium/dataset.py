import os
import sys
import pandas as pd
from datetime import timedelta
sys.path.append(os.getcwd())
from src.dbmanager import DBManager

PATH_OBDB = os.path.join(os.getcwd(), 'data', 'db', 'ob.db')
PATH_TRDB = os.path.join(os.getcwd(), 'data', 'db', 'tr.db')

conob = DBManager(PATH_OBDB)
contr = DBManager(PATH_TRDB)

orderbook = conob.read(
    """
    select
        *
    from
        ob
    """
)
orderbook.columns = ['time', 'bprice', 'bvol', 'aprice', 'avol']
orderbook['time'] = pd.to_datetime(orderbook['time'], format='mixed')\
    .dt.tz_localize(None)
orderbook['date'] = orderbook['time'].dt.date

trades = contr.read(
    """
    select
        *
    from
        tr
    """
)
trades.columns = ['time', 'direction', 'price', 'vol']
trades['time'] = pd.to_datetime(trades['time'], format='mixed')\
    .dt.tz_localize(None)
trades['date'] = trades['time'].dt.date

dates = orderbook['date'].unique()
orderbook = orderbook.groupby('date')
trades = trades.groupby('date')
rows = []
for date in dates:
    filtered_orderbook = orderbook.get_group(date)
    filtered_trades = trades.get_group(date)
    ts_start = filtered_orderbook['time'].iloc[0]
    ts_end = ts_start + timedelta(seconds=1)
    bpoint = filtered_orderbook['time'].iloc[-1]
    tr = pd.DataFrame({
        'price': [0],
        'vol': [0],
        'direction': [0]
    })
    ob = pd.DataFrame({
        'bprice': [0],
        'bvol': [0],
        'aprice': [0],
        'avol': [0]
    })
    while ts_end <= bpoint:
        tmp_trades = filtered_trades[
            (filtered_trades['time'] >= ts_start) & (filtered_trades['time'] < ts_end)]  # noqa: E501
        if not tmp_trades.empty:
            tr = tmp_trades
            filtered_trades = filtered_trades.drop(tmp_trades.index)
        tmp_orderbook = filtered_orderbook[
            (filtered_orderbook['time'] >= ts_start) & (filtered_orderbook['time'] < ts_end)]  # noqa: E501
        if not tmp_orderbook.empty:
            ob = tmp_orderbook
            filtered_orderbook = filtered_orderbook.drop(tmp_orderbook.index)
        ts_start = ts_end
        ts_end += timedelta(seconds=1)
        row = {
            'time': ts_end,
            'open': tr['price'].iloc[0],
            'high': tr['price'].max(),
            'low': tr['price'].min(),
            'close': tr['price'].iloc[-1],
            'volume': tr['vol'].sum(),
            'feature_direction_1': sum([x == 1 for x in tr['direction']]),
            'feature_direction_2': sum([x == 2 for x in tr['direction']]),
            'feature_mean_bprice': ob['bprice'].mean(),
            'feature_mean_bvol': ob['bvol'].mean(),
            'feature_mean_aprice': ob['aprice'].mean(),
            'feature_mean_avol': ob['avol'].mean()
        }
        rows.append(row)
        print(f'Lines to the end: {filtered_orderbook.shape[0]}')
pd.DataFrame(rows).drop_duplicates().reset_index(drop=True).to_csv(
    os.path.join(os.getcwd(), 'data', 'interim', 'dataset.csv'))
