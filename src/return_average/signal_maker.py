import os
import sys
sys.path.append(os.getcwd())
from typing import Union
from datetime import datetime
from collections import deque
from numpy import mean, quantile
from tinkoff.invest.utils import quotation_to_decimal
from tinkoff.invest import Client, MarketDataResponse


class SignalMaker:

    def __init__(
            self,
            data_cash_size: int,
            low_q: float,
            high_q: float,
            coeff_for_SL: float,
            window_avg: int,
            window_diff_high_avg: int,
            window_diff_avg_low: int,
            token: str = None,
            acc_id: str = None,
            figi: str = None,
            price_delta: float = None,
            coeff_for_TP=None,
            fee: float = 0.04 / 100,
            log_path=None,
            verbose=True
    ):

        self.figi = figi
        self.data_cash_size = data_cash_size
        self.low_q = low_q
        self.high_q = high_q
        self.coeff_for_SL = coeff_for_SL
        self.window_avg = window_avg
        self.window_diff_high_avg = window_diff_high_avg
        self.window_diff_avg_low = window_diff_avg_low
        self.__delta = price_delta
        self.__coeff_for_TP = coeff_for_TP
        self.__fee = fee

        self.__time = None
        self.__log_path = log_path
        self.__verbose = verbose

        self.profit = 0

        self.__init_state()

        if token is not None and acc_id is not None and figi is not None:
            with Client(token) as cli:
                active_positions = cli.operations\
                    .get_portfolio(account_id=acc_id).positions
                active_figis = [pos.figi for pos in active_positions]

                if figi in active_figis:
                    pos = [p for p in active_positions if p.figi == figi][0]
                    quantity = float(quotation_to_decimal(pos.quantity))
                    price = float(quotation_to_decimal(pos.average_position_price))  # noqa: E501
                    self.__entry_price = price

                    self.__locked = True
                    if quantity > 0:
                        self.__side = 'long'
                        self.__sl = price - (price * self.coeff_for_SL)
                        self.__sl = round(self.__sl, 2)

                    elif quantity < 0:
                        self.__side = 'short'
                        self.__sl = price + (price * self.coeff_for_SL)
                        self.__sl = round(self.__sl, 2)

    def __init_state(self) -> None:
        self.__prices = deque(maxlen=self.data_cash_size)
        self.__price = None
        self.__avg = None
        self.__diffs_high_avg = deque(maxlen=self.data_cash_size)
        self.__diffs_avg_low = deque(maxlen=self.data_cash_size)
        self.__high_quantile = None
        self.__low_quantile = None

        self.__entry_price = None
        self.__locked = False
        self.__side = None
        self.__sl = None
        return None

    def __update_quantiles(self, data: Union[MarketDataResponse, float]
                           ) -> None:
        self.__time = datetime.now()

        if isinstance(data, MarketDataResponse):
            self.__price = round(
                float(quotation_to_decimal(data.trade.price)), 2)
        else:
            self.__price = data
        self.__prices.append(self.__price)
        self.__avg = round(mean(list(self.__prices)[-self.window_avg:]), 2)
        self.__diffs_high_avg.append(
            round(max(list(self.__prices)[-self.window_diff_high_avg:]) - self.__avg, 2))  # noqa: E501
        self.__diffs_avg_low.append(
            round(self.__avg - min(list(self.__prices)[-self.window_diff_avg_low:]), 2))  # noqa: E501
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
            'High_q_dev': self.__deviation_quantile(self.__high_quantile),
            'Average_Price': self.__avg,
            'Low_quantile': self.__low_quantile,
            'Low_q_dev': self.__deviation_quantile(self.__low_quantile),
            'Coeff_take_profit': self.__coeff_for_TP,
            'Delta': self.__delta,
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
            return round(((self.__price - self.__entry_price) / self.__entry_price) * 100, 4)  # noqa: E501
        if side == 'short':
            return round(((self.__entry_price - self.__price) / self.__entry_price) * 100, 4)  # noqa: E501
        if side is None:
            return None

    def __deviation_quantile(self, quantile: float) -> float:
        return round((abs(self.__avg - quantile) / self.__avg) * 100, 4)

    def get_signal(self, data: Union[MarketDataResponse, float]
                   ) -> Union[None, dict]:

        self.__update_quantiles(data)

        if self.__log_path is not None:
            self.__log()

        if not self.__locked and self.__price <= self.__low_quantile\
                and self.__deviation_quantile(self.__low_quantile) >= self.__delta:  # noqa: E501
            self.__side = 'long'
            self.__locked = True
            self.__sl = self.__price -\
                (self.__price * self.coeff_for_SL)
            self.__sl = round(self.__sl, 2)
            self.__entry_price = self.__price
            signal = {
                'action': 'open', 'side': self.__side,
                'price': self.__price, 'sl': self.__sl
            }
            if self.__verbose:
                print(signal)
            return signal

        if not self.__locked and self.__price >= self.__high_quantile\
                and self.__deviation_quantile(self.__high_quantile) >= self.__delta:  # noqa: E501
            self.__side = 'short'
            self.__locked = True
            self.__sl = self.__price +\
                (self.__price * self.coeff_for_SL)
            self.__sl = round(self.__sl, 2)
            self.__entry_price = self.__price
            signal = {
                'action': 'open', 'side': self.__side,
                'price': self.__price, 'sl': self.__sl
            }
            if self.__verbose:
                print(signal)
            return signal

        if self.__locked and self.__side == 'long' and (
            self.__deviation(self.__side) >= self.__coeff_for_TP or self.__price <= self.__sl  # noqa: E501
        ):
            deviation = self.__deviation(self.__side)
            side = self.__side
            self.__side = None
            self.__locked = False
            self.__sl = None
            cost = self.__price * self.__fee * 2
            profit_current = round(
                (self.__price - self.__entry_price - cost), 2)
            self.profit += profit_current
            self.profit = round(self.profit, 2)
            signal = {
                'action': 'close', 'side': side, 'price': self.__price,
                'deviation': deviation,
                'coeff_take_profit': self.__coeff_for_TP,
                'profit_current': profit_current, 'profit_total': self.profit
            }
            if self.__verbose:
                print(signal)
            return signal

        if self.__locked and self.__side == 'short' and (
            self.__deviation(self.__side) >= self.__coeff_for_TP or self.__price >= self.__sl  # noqa: E501
        ):
            deviation = self.__deviation(self.__side)
            side = self.__side
            self.__side = None
            self.__locked = False
            self.__sl = None
            cost = self.__price * self.__fee * 2
            profit_current = round(
                (self.__entry_price - self.__price - cost), 2)
            self.profit += profit_current
            self.profit = round(self.profit, 2)
            signal = {
                'action': 'close', 'side': side, 'price': self.__price,
                'deviation': deviation,
                'coeff_take_profit': self.__coeff_for_TP,
                'profit_current': profit_current, 'profit_total': self.profit
            }
            if self.__verbose:
                print(signal)
            return signal

    def reset(self) -> None:
        self.__init_state()
        return None
