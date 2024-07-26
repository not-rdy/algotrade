import os
import pickle
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure, axes
from typing import Dict, List, Union, Tuple
from tinkoff.invest import Order, HistoricCandle, Quotation, MoneyValue
from tinkoff.invest.utils import quotation_to_decimal


def figax(df: pd.DataFrame) -> Tuple[figure, axes]:
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(20, 8))
    ax.plot(df.index, df['price'], label='price')
    ax.plot(df.index, df['avg'], label='price average')
    ax.plot(df.index, df['lowq'], label='quantile low')
    ax.plot(df.index, df['highq'], label='quantile high')

    open_long = df[df['action'] == 'open_long']
    open_short = df[df['action'] == 'open_short']
    close_long = df[df['action'] == 'close_long']
    close_short = df[df['action'] == 'close_short']
    ax.scatter(
        open_long.index, open_long['price'],
        marker='o', color='green', s=50, label='open long')
    ax.scatter(
        open_short.index, open_short['price'],
        marker='o', color='red', s=50, label='open short')
    ax.scatter(
        close_long.index, close_long['price'],
        marker='x', color='green', s=50, label='close long')
    ax.scatter(
        close_short.index, close_short['price'],
        marker='x', color='red', s=50, label='close short')

    ax.legend()
    ax.grid()
    return fig, ax


def prepare_candles(name: str) -> pd.DataFrame:
    prices = pd.read_csv(
        os.path.join(os.getcwd(), 'data', 'raw', name),
        index_col=0)
    prices.columns = ['o', 'h', 'l', 'p', 'v', 't']
    prices['t'] = pd.to_datetime(prices['t'], format='mixed')
    prices['t'] = prices['t'].dt.tz_localize(None)
    prices['week'] = prices['t'].dt.day_of_week
    prices['date'] = prices['t'].dt.date
    prices = prices[~prices['week'].isin([5, 6])].reset_index(drop=True)
    dfs = []
    for (date, pr) in prices.groupby('date'):
        start = datetime(year=date.year, month=date.month, day=date.day, hour=7)  # noqa: E501
        end = datetime(year=date.year, month=date.month, day=date.day, hour=15)
        pr = pr[(pr['t'] >= start) & (pr['t'] <= end)].reset_index(drop=True)
        dfs.append(pr)
    prices = pd.concat(dfs).reset_index(drop=True)
    return prices


def price_to_float(price: Union[Quotation, MoneyValue]) -> float:
    fractional = price.nano / 10e8
    return price.units + fractional


def OrderToDict(order: Order) -> Dict[float, int]:
    return {
        'price': float(quotation_to_decimal(order.price)),
        'quantity': order.quantity}


def save(obj, path):
    with open(path, 'wb') as obj_file:
        pickle.dump(obj, obj_file, protocol=pickle.HIGHEST_PROTOCOL)


def load(path):
    with open(path, 'rb') as obj_file:
        obj = pickle.load(obj_file)
    return obj


def historicCandles_to_df(candles: List[HistoricCandle]) -> pd.DataFrame:
    rows = []
    for candle in candles:
        rows.append(
            {
                'open': float(quotation_to_decimal(candle.open)),
                'high': float(quotation_to_decimal(candle.high)),
                'low': float(quotation_to_decimal(candle.low)),
                'close': float(quotation_to_decimal(candle.close)),
                'volume': candle.volume,
                'time': candle.time
            }
        )
    return pd.DataFrame(rows)
