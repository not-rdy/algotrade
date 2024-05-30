import os
import sys
sys.path.append(os.getcwd())
import numpy as np  # noqa: E402
import pandas as pd
import itertools
from tqdm import tqdm
from src.dbmanager import DBManager
from src.markov.agent import Agent
from src.markov.environment import Environment

dbob = DBManager(path=os.path.join(os.getcwd(), 'data', 'db', 'ob.db'))
dbtr = DBManager(path=os.path.join(os.getcwd(), 'data', 'db', 'tr.db'))

print('Load OrderBook ...')
ob = dbob.read(
    """
    select
        *
    from
        ob
    """
)
print('Prepare Orderbook ...')
ob.columns = ['ts', 'bprice', 'bquantity', 'aprice', 'aquantity']
ob['ts'] = pd.to_datetime(ob['ts']).dt.tz_localize(None)
ob = ob.iloc[-1000000:]

print('Load Trades ...')
tr = dbtr.read(
    """
    select
        *
    from
        tr
    """
)
print('Prepare Trades ...')
tr.columns = ['ts', 'direction', 'price', 'quantity']
tr['ts'] = pd.to_datetime(tr['ts']).dt.tz_localize(None)

print('Create Actions ...')
stop_losses = [round(x, 3) for x in np.arange(-0.005, 0, 0.001)]
take_profits = [round(x, 3) for x in np.arange(0.001, 0.06, 0.001)]
buy_actions = list(itertools.product(['buy'], take_profits, stop_losses))
sell_actions = list(itertools.product(['sell'], take_profits, stop_losses))
actions = buy_actions + sell_actions
actions.append(('none', 0, 0))

print('Create States ...')
depth_ob = 5
last_trades = 5
states = set()
for ts, orderbook in tqdm(ob.groupby('ts'), total=ob['ts'].nunique()):

    cols = ['direction', 'price', 'quantity']
    trades = tr[tr['ts'] <= ts].iloc[-last_trades:]
    trades[cols] = trades[cols].apply(lambda col: col / col.iloc[-1])
    if trades.isna().sum().sum() != 0 or trades.shape[0] != last_trades:
        continue
    embd_tr = trades[cols].values.flatten()
    cols = ['bprice', 'bquantity', 'aprice', 'aquantity']
    orderbook = orderbook.iloc[:depth_ob]
    orderbook.loc[:, cols] = orderbook[cols]\
        .apply(lambda col: col / col.iloc[0])
    if orderbook.isna().sum().sum() != 0:
        continue
    embd_ob = orderbook[cols].values.flatten()
    state = tuple(np.concatenate([embd_ob, embd_tr]))
    states.add(state)
del orderbook, trades

print(f'Length states: {len(states)}')
embd_length = pd.Series([len(x) for x in states]).value_counts().index[0]
print(f'Embd length: {embd_length}')
states = [x for x in states if len(x) == embd_length]
print(f'Length states: {len(states)}')

print('Create Rewards ...')
rewards = [round(x, 2) for x in np.arange(-2.00, 2.01, 0.01)]

print('Init Agent ...')
agent = Agent(
    states=states, actions=actions,
    rewards=rewards, history_path='/Users/rkam/projs/algotrade/data/interim/history.csv')

print('Init Environment ...')
environment = Environment(
    depth_ob=depth_ob, last_trades=last_trades,
    trades=tr, orderbooks=ob, state_length=embd_length)

print('Start train ...')
n_epochs = 1000
epsilons = np.linspace(1, 0, n_epochs)
for epoch in range(1, n_epochs):
    eps = epsilons[epoch - 1]
    print(f'Epoch: {epoch}, Epsilon: {eps}')
    action = ('none', 0, 0)
    reward_epoch = 0
    for ts in ob['ts'].unique():
        # state reward
        state_reward = environment.get_state_reward(ts, action, agent.agent_state)
        if state_reward is None:
            continue
        else:
            state, reward = state_reward
        # action
        action = agent.get_action(state, reward, eps)
        reward_epoch += reward
    print(f'Reward Epoch: {reward_epoch}')
    agent.release()
    environment.release()
