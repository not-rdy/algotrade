import os
import sys
sys.path.append(os.getcwd())
from src.utils import price_to_float
from typing import Union, Tuple
from datetime import datetime
from collections import deque
from numpy import mean, quantile
from tinkoff.invest import Client, MarketDataResponse


class ReturnAvgRule:

    def __init__(
            self,
            data_cash_size: int,
            low_q: float,
            high_q: float,
            sl: float,
            window_avg: int,
            window_diff_high_avg: int,
            window_diff_avg_low: int,
            token: str = None,
            acc_id: str = None,
            figi: str = None,
            avgprice_quantile_dist: float = None,
            fee: float = 0.04 / 100,
            log_path=None,
            verbose=True,
            data_type='candles'
    ):

        self.figi = figi
        self.data_cash_size = data_cash_size
        self.low_q = low_q
        self.high_q = high_q
        self.__sl = sl
        self.window_avg = window_avg
        self.window_diff_high_avg = window_diff_high_avg
        self.window_diff_avg_low = window_diff_avg_low
        self.__dist = avgprice_quantile_dist
        self.__fee = fee

        self.__time = None
        self.__log_path = log_path
        self.__verbose = verbose
        self.__data_type = data_type

        self.profit = 0

        self.__init_state()

        if token is not None and acc_id is not None and figi is not None:
            with Client(token) as cli:
                active_positions = cli.operations\
                    .get_portfolio(account_id=acc_id).positions
                active_figis = [pos.figi for pos in active_positions]

                if figi in active_figis:
                    pos = [p for p in active_positions if p.figi == figi][0]
                    quantity = price_to_float(pos.quantity)
                    price = price_to_float(pos.average_position_price)
                    self.__entry_price = price

                    if quantity > 0:
                        self.__side = 'long'

                    elif quantity < 0:
                        self.__side = 'short'

    def __init_state(self) -> None:
        self.__bufer = deque(maxlen=self.data_cash_size)
        self.__high_prices = deque(maxlen=self.data_cash_size)
        self.__low_prices = deque(maxlen=self.data_cash_size)
        self.__prices = deque(maxlen=self.data_cash_size)
        self.__high = None
        self.__low = None
        self.__price = None
        self.__avg = None
        self.__diffs_high_avg = deque(maxlen=self.data_cash_size)
        self.__diffs_avg_low = deque(maxlen=self.data_cash_size)
        self.__high_quantile = None
        self.__low_quantile = None

        self.__entry_price = None
        self.__main_price = None
        self.__side = None
        return None

    def __update_quantiles(
            self,
            data: Union[MarketDataResponse, Tuple[float, float, float], float]) -> None:  # noqa: E501

        self.__time = datetime.now()

        if self.__data_type == 'candles':
            if isinstance(data, MarketDataResponse):
                self.__high = price_to_float(data.candle.high)
                self.__low = price_to_float(data.candle.low)
                self.__price = price_to_float(data.candle.close)
            else:
                self.__high, self.__low, self.__price = data
        if self.__data_type == 'trades':
            if isinstance(data, MarketDataResponse):
                self.__price = price_to_float(data.trade)
            else:
                self.__price = data
            self.__bufer.append(self.__price)
            self.__high = max(self.__bufer)
            self.__low = min(self.__bufer)

        self.__high_prices.append(self.__high)
        self.__low_prices.append(self.__low)
        self.__prices.append(self.__price)
        self.__avg = round(mean(list(self.__prices)[-self.window_avg:]), 2)
        self.__diffs_high_avg.append(
            round(max(list(self.__high_prices)[-self.window_diff_high_avg:]) - self.__avg, 2))  # noqa: E501
        self.__diffs_avg_low.append(
            round(self.__avg - min(list(self.__low_prices)[-self.window_diff_avg_low:]), 2))  # noqa: E501
        self.__high_quantile = self.__avg +\
            quantile(self.__diffs_high_avg, q=self.high_q)
        self.__high_quantile = round(self.__high_quantile, 2)
        self.__low_quantile = self.__avg -\
            quantile(self.__diffs_avg_low, q=self.low_q)
        self.__low_quantile = round(self.__low_quantile, 2)
        return None

    def __log(self) -> None:
        log = {
            'Time': self.__time,
            'Price': self.__price,
            'High_quantile': self.__high_quantile,
            'High_q_dev': self.__deviation_quantile('high'),
            'Average_Price': self.__avg,
            'Low_quantile': self.__low_quantile,
            'Low_q_dev': self.__deviation_quantile('low'),
            'Dist': self.__dist,
            'Stop_loss': self.__sl,
            'Price_dev_from_entry': self.__deviation(self.__side)
        }

        line = '\n'
        for key, val in log.items():
            line += key + ' ' + str(val) + '\n'
        line += '\n'
        with open(self.__log_path, 'a') as outp:
            outp.write(line)

        if self.__verbose:
            print(line)

    def __deviation(self, side: str) -> float:
        if side == 'long':
            return round(self.__price - self.__main_price, 2)
        if side == 'short':
            return round(self.__main_price - self.__price, 2)

    def __deviation_quantile(self, qtype: str) -> float:
        if qtype == 'low':
            return round(self.__avg - self.__low_quantile, 2)
        if qtype == 'high':
            return round(self.__high_quantile - self.__avg, 2)

    def __input_signal(self, side: str) -> dict:
        self.__side = side
        self.__entry_price = self.__price
        self.__main_price = self.__price
        signal = {
            'action': 'open', 'side': self.__side,
            'price': self.__price, 'sl': self.__sl
        }
        if self.__verbose:
            print(signal)
        return signal

    def __output_signal(self) -> dict:
        cost = self.__price * self.__fee * 2
        if self.__side == 'long':
            profit_current = round(
                (self.__price - self.__entry_price - cost), 2)
        elif self.__side == 'short':
            profit_current = round(
                (self.__entry_price - self.__price - cost), 2)
        self.profit += profit_current
        self.profit = round(self.profit, 2)
        signal = {
            'action': 'close', 'side': self.__side,
            'price': self.__price, 'deviation': self.__deviation(self.__side),
            'profit_current': profit_current,
            'profit_total': self.profit
        }
        if self.__verbose:
            print(signal)
        return signal

    def get_content(self) -> None:
        print(self.__prices)

    def get_signal(self, data: Union[MarketDataResponse, Tuple[float, float, float]]  # noqa: E501
                   ) -> Union[None, dict]:

        self.__update_quantiles(data)

        if self.__log_path is not None:
            self.__log()

        # update main price
        if self.__main_price is None:
            self.__main_price = self.__price
        if self.__side == 'long' and self.__price > self.__main_price:
            self.__main_price = self.__price
        if self.__side == 'short' and self.__price < self.__main_price:
            self.__main_price = self.__price

        # enter into a deal
        if self.__side is None and self.__price <= self.__low_quantile\
                and self.__deviation_quantile('low') >= self.__dist:  # noqa: E501
            return self.__input_signal(side='long')
        if self.__side is None and self.__price >= self.__high_quantile\
                and self.__deviation_quantile('high') >= self.__dist:  # noqa: E501
            return self.__input_signal(side='short')

        # out of the deal
        if self.__side == 'long':
            if self.__deviation(self.__side) <= self.__sl\
                    or self.__price >= self.__avg:
                signal = self.__output_signal()
                self.__side = None
                return signal
        if self.__side == 'short':
            if self.__deviation(self.__side) <= self.__sl\
                    or self.__price <= self.__avg:
                signal = self.__output_signal()
                self.__side = None
                return signal

    def reset(self) -> None:
        self.__init_state()
        return None
