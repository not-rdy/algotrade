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
            trades: pd.DataFrame, orderbooks: pd.DataFrame) -> None:
        self.depth_ob = depth_ob
        self.last_trades = last_trades
        self.trades = trades
        self.orderbooks = orderbooks

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
        ob[cols] = ob[cols].apply(lambda col: col / col.max())
        return ob[cols].values.flatten()
    
    def __update_entry_price_and_action(self, action: Action, agent_state: str) -> None:
        if agent_state == 'free' and action[0] != 'none':
            self.entry_price = self.current_price
            self.entry_action = action
    
    def __deviation(self) -> float:
            return (self.entry_price - self.current_price) / self.entry_price
    
    def __get_reward(self, agent_state: str) -> None:
        if agent_state == 'long' and\
                (self.__deviation() >= self.entry_action[1]\
                or (self.__deviation() < 0 and abs(self.__deviation()) >= self.entry_action[2])):
            reward = self.current_price - self.entry_price
            print(f'Agent state: {agent_state}, Deviation: {self.__deviation()}, Take profit: {self.entry_action[1]}, Stop loss: {self.entry_action[2]}, Reward: {reward}')
        elif agent_state == 'short' and\
                (self.__deviation() <= self.entry_action[1]\
                or (self.__deviation() > 0 and self.__deviation() >= self.entry_action[2])):
            reward = self.entry_price - self.current_price
            print(f'Agent state: {agent_state}, Deviation: {self.__deviation()}, Take profit: {self.entry_action[1]}, Stop loss: {self.entry_action[2]}, Reward: {reward}')
        else:
            reward = 0
        return reward
 
    def get_state_reward(self, ts: datetime, action: Action, agent_state: str) -> Tuple[State, Reward]:
        # state
        embd_tr = self.__get_trades_embd(ts)
        if embd_tr is None:
            return None
        embd_ob = self.__get_orderbook_embd(ts)
        state = tuple(np.concatenate([embd_ob, embd_tr]))
        # reward
        self.__update_entry_price_and_action(action, agent_state)
        reward = self.__get_reward(agent_state)
        return tuple([state, reward])
