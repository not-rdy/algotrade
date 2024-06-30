import os
import sys
from typing import Union
sys.path.append(os.getcwd())
from sma import SimpleMA
from lma import LinearMA
from ema import ExponentialMA
from tinkoff.invest import Client, MarketDataResponse
from tinkoff.invest.utils import quotation_to_decimal


class CrossoverRule:

    def __init__(
            self,
            short_long_ma: list,
            window_short: int, window_long: int,
            eps: float, sl: float,
            token: str = None, acc_id: str = None, figi: str = None,
            fee: float = 0.04 / 100,) -> None:

        all = {
            'sma': SimpleMA, 'lma': LinearMA, 'ema': ExponentialMA}
        self.ma_short = all[short_long_ma[0]](window_short)
        self.ma_long = all[short_long_ma[1]](window_long)
        self.__eps = eps
        self.__sl = sl
        self.__fee = fee
        self.__price = None
        self.__main_price = None
        self.__entry_price = None
        self.__state = None
        self.__profit = 0

        if token is not None and acc_id is not None and figi is not None:
            with Client(token) as cli:
                active_positions = cli.operations\
                    .get_portfolio(account_id=acc_id).positions
                active_figis = [pos.figi for pos in active_positions]

                if figi in active_figis:
                    pos = [p for p in active_positions if p.figi == figi][0]
                    quantity = float(quotation_to_decimal(pos.quantity))
                    if quantity > 0:
                        self.__state = 'long'
                    elif quantity < 0:
                        self.__state = 'short'

    def __update_price(self, data: Union[MarketDataResponse, float]):
        if isinstance(data, MarketDataResponse):
            self.__price = round(
                quotation_to_decimal(float(data.candle.close)), 2)
        else:
            self.__price = data

    def get_content(self) -> None:
        print(self.ma_short.prices)
        print(self.ma_long.prices)

    def get_signal(
            self, data: Union[MarketDataResponse, float]) -> Union[None, dict]:
        self.__update_price(data)
        ma_value_short = self.ma_short.get(self.__price)
        ma_value_long = self.ma_long.get(self.__price)
        if ma_value_long is None:
            return None

        # update main price
        if self.__state is None:
            self.__main_price = self.__price
        if self.__state == 'long' and self.__price > self.__main_price:
            self.__main_price = self.__price
        if self.__state == 'short' and self.__price < self.__main_price:
            self.__main_price = self.__price

        # enter into a deal
        if self.__state is None:
            diff = ma_value_short - ma_value_long
            if diff > self.__eps:
                self.__state = 'long'
                self.__entry_price = self.__price
                self.__main_price = self.__price
                signal = {
                    'action': 'open', 'side': self.__state,
                    'price': self.__price, 'sl': self.__sl
                }
                print(signal)
                return signal
            elif diff <= -self.__eps:
                self.__state = 'short'
                self.__entry_price = self.__price
                self.__main_price = self.__price
                signal = {
                    'action': 'open', 'side': self.__state,
                    'price': self.__price, 'sl': self.__sl
                }
                print(signal)
                return signal

        # out of the deal
        if self.__state == 'long':
            deviation = self.__price - self.__main_price
            ma_value_short = self.ma_short.get(self.__price)
            ma_value_long = self.ma_long.get(self.__price)
            if deviation <= self.__sl or ma_value_long >= ma_value_short:
                cost = self.__price * self.__fee * 2
                current_profit = self.__price - self.__entry_price - cost
                self.__profit += current_profit
                self.__main_price = None
                signal = {
                    'action': 'close', 'side': self.__state,
                    'price': self.__price, 'deviation': deviation,
                    'profit_current': current_profit,
                    'profit_total': self.__profit
                }
                print(signal)
                self.__state = None
                return signal
        if self.__state == 'short':
            deviation = self.__main_price - self.__price
            ma_value_short = self.ma_short.get(self.__price)
            ma_value_long = self.ma_long.get(self.__price)
            if deviation <= self.__sl or ma_value_long <= ma_value_short:
                cost = self.__price * self.__fee * 2
                current_profit = self.__entry_price - self.__price - cost
                self.__profit += current_profit
                self.__main_price = None
                signal = {
                    'action': 'close', 'side': self.__state,
                    'price': self.__price, 'deviation': deviation,
                    'profit_current': current_profit,
                    'profit_total': self.__profit
                }
                print(signal)
                self.__state = None
                return signal
