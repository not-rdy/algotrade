import os
import sys
sys.path.append(os.getcwd())
import numpy as np
import pandas as pd
from typing import Tuple, NewType
from datetime import datetime

State = NewType('State', tuple)
Action = NewType('Action', str)
Reward = NewType('Reward', float)


class Environment:
    def __init__(
            self,
            depth_ob: int, last_trades: int,
            trades: pd.DataFrame,
            orderbooks: pd.DataFrame, state_length: int) -> None:
        self.depth_ob = depth_ob
        self.last_trades = last_trades
        self.trades = trades
        self.orderbooks = orderbooks

        self.entry_price = None
        self.entry_action = None
        self.current_price = None

        self.state_length = state_length

    def release(self) -> None:
        self.entry_price = None
        self.entry_action = None
        self.current_price = None

    def __get_trades_embd(self, ts: datetime) -> np.array:
        cols = ['direction', 'price', 'quantity']
        tr = self.trades[self.trades['ts'] <= ts].iloc[-self.last_trades:]
        if tr.shape[0] != self.last_trades:
            return None
        self.current_price = tr['price'].iloc[-1].item()
        tr[cols] = tr[cols].apply(lambda col: col / col.iloc[-1])
        return tr[cols].values.flatten()

    def __get_orderbook_embd(self, ts: datetime) -> np.array:
        cols = ['bprice', 'bquantity', 'aprice', 'aquantity']
        ob = self.orderbooks[self.orderbooks['ts'] == ts].iloc[:self.depth_ob]
        ob[cols] = ob[cols].apply(lambda col: col / col.iloc[0])
        return ob[cols].values.flatten()

    def __update_entry_price_and_action(self, action: Action) -> None:
        if action[0] != 'none':
            self.entry_price = self.current_price
            self.entry_action = action

    def __deviation_long(self) -> float:
        dev = (self.current_price - self.entry_price) / self.entry_price
        return round(dev, 5)

    def __deviation_short(self) -> float:
        dev = (self.entry_price - self.current_price) / self.entry_price
        return round(dev, 5)

    def __print_close(
            self,
            agent_state: str, deviation: float,
            take_profit: float, stop_loss: float, reward: float) -> None:
        string = f"""
        Agent state: {agent_state} Deviation: {deviation}
        Take profit: {take_profit} Stop loss: {stop_loss}
        Reward: {reward}"""
        print(string)

    def __get_reward(self, agent_state: str) -> None:
        long, short = (agent_state == 'long'), (agent_state == 'short')
        if long and (self.__deviation_long() >= self.entry_action[1] or self.__deviation_long() <= self.entry_action[2]):  # noqa: E501
            reward = round(self.current_price - self.entry_price, 2)
            self.__print_close(
                agent_state, self.__deviation_long(),
                self.entry_action[1], self.entry_action[2], reward)
        elif short and (self.__deviation_short() >= self.entry_action[1] or self.__deviation_short() <= self.entry_action[2]):  # noqa: E501
            reward = round(self.entry_price - self.current_price, 2)
            self.__print_close(
                agent_state, self.__deviation_short(),
                self.entry_action[1], self.entry_action[2], reward)
        else:
            reward = 0
        return reward

    def get_state_reward(
            self,
            ts: datetime, action: Action,
            agent_state: str) -> Tuple[State, Reward]:
        # state
        embd_tr = self.__get_trades_embd(ts)
        embd_ob = self.__get_orderbook_embd(ts)
        if embd_tr is None or embd_ob is None:
            return None
        state = tuple(np.concatenate([embd_ob, embd_tr]))
        if len(state) != self.state_length:
            return None
        # reward
        self.__update_entry_price_and_action(action)
        reward = self.__get_reward(agent_state)
        return tuple([state, reward])
