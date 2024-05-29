import sys
sys.path.append('/Users/rkam/projs/algotrade')
import numpy as np
import pandas as pd
import itertools
from tqdm import tqdm
from src.dbmanager import DBManager
from src.markov.agent import Agent
from src.markov.environment import Environment

dbob = DBManager(path='/Users/rkam/projs/algotrade/data/db/ob.db')
dbtr = DBManager(path='/Users/rkam/projs/algotrade/data/db/tr.db')

ob = dbob.read(
    """
    select
        *
    from
        ob
    """
)
ob.columns = ['ts', 'bprice', 'bquantity', 'aprice', 'aquantity']
ob['ts'] = pd.to_datetime(ob['ts']).dt.tz_localize(None)

tr = dbtr.read(
    """
    select
        *
    from
        tr
    """
)
tr.columns = ['ts', 'direction', 'price', 'quantity']
tr['ts'] = pd.to_datetime(tr['ts']).dt.tz_localize(None)

stop_losses = [round(x, 5) for x in np.arange(-0.0005, 0, 0.0001)]
take_profits = [round(x, 5) for x in np.arange(0.0001, 0.0006, 0.0001)]
buy_actions = list(itertools.product(['buy'], take_profits, stop_losses))
sell_actions = list(itertools.product(['sell'], take_profits, stop_losses))
actions = buy_actions + sell_actions
actions.append(('none', 0, 0))

ob_groupped = ob.groupby('ts', group_keys=True).apply(lambda df_: df_)
depth_ob = 5
last_trades = 5
states = set()
for ts in tqdm(ob['ts'].unique(), total=ob['ts'].nunique()):
     
    cols = ['direction', 'price', 'quantity']
    trades = tr[tr['ts'] <= ts].iloc[-last_trades:]
    trades[cols] = trades[cols].apply(lambda col: col / col.iloc[-1])
    embd_tr = trades[cols].values.flatten()
    if trades.shape[0] != last_trades:
        continue
    cols = ['bprice', 'bquantity', 'aprice', 'aquantity']
    orderbook = ob_groupped.loc[ts].iloc[:depth_ob]
    orderbook[cols] = orderbook[cols].apply(lambda col: col / col.max())
    embd_ob = orderbook[cols].values.flatten()

    state = tuple(np.concatenate([embd_ob, embd_tr]))
    states.add(state)
embd_length = pd.Series([len(x) for x in states]).value_counts().index[0]
states = [x for x in states if len(x) == embd_length]

rewards = [round(x, 2) for x in np.arange(-1.00, 1.01, 0.01)]

agent = Agent(
    states=states, actions=actions,
    rewards=rewards, history_path='/Users/rkam/projs/algotrade/data/interim/history.csv')
environment = Environment(
    depth_ob=depth_ob, last_trades=last_trades,
    trades=tr, orderbooks=ob, state_length=embd_length)

n_epochs = 50
epsilons = np.linspace(1, 0.05, n_epochs)
for epoch in range(1, n_epochs):
    eps = epsilons[epoch - 1]
    print(f'Epoch: {epoch}, Epsilon: {eps}')
    action = ('none', 0, 0)
    rewards_epoch = []
    for ts in ob['ts'].unique():
        # state reward
        state_reward = environment.get_state_reward(ts, action, agent.agent_state)
        if state_reward is None:
            continue
        else:
            state, reward = state_reward
        # action
        action = agent.get_action(state, reward, eps)
        if reward != 0:
            rewards_epoch.append(reward)
    if len(rewards_epoch) > 0:
        print(f'Mean Reward: {sum(rewards_epoch) / len(rewards_epoch)}')
    else:
        print(f'Mean Reward: {0}')
    agent.release()
    environment.release()

