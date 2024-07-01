import pickle
import pandas as pd
from typing import Dict, List, Union
from tinkoff.invest import Order, HistoricCandle, Quotation, MoneyValue
from tinkoff.invest.utils import quotation_to_decimal


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
