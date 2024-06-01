import os
import numpy as np
import pandas as pd
import gymnasium as gym
import gym_trading_env  # noqa: F401
from reinforce import REINFORCE

df = pd.read_csv(
    os.path.join(os.getcwd(), 'data', 'raw', 'candles_SBER_min.csv'),
    index_col=0)
df['time'] = pd.to_datetime(df['time'])
df = df.sort_values(by='time')
df = df.set_index('time')
df["feature_pct_change"] = df["close"].pct_change()
df["feature_high"] = df["high"] / df["close"] - 1
df["feature_low"] = df["low"] / df["close"] - 1
df.dropna(inplace=True)


# reward func
def reward_function(history):
    if history['position', -2] == 1 and history['position', -1] == 0:
        current_close = history['data_close', -1]
        idx = -2
        position = 1
        while position == 1:
            position = history['position', idx]
            idx -= 1
        idx += 1
        entry_close = history['data_close', idx]
        reward = current_close - entry_close
    elif history['position', -2] == -1 and history['position', -1] == 0:
        current_close = history['data_close', -1]
        idx = -2
        position = -1
        while position == -1:
            position = history['position', idx]
            idx -= 1
        idx += 1
        entry_close = history['data_close', idx]
        reward = entry_close - current_close
    else:
        reward = np.random.normal(0, 0.0001)
    return reward


# actions decoder
decoder = {0: -1, 1: 0, 2: 1}
# Env
env = gym.make(
    "TradingEnv", name='SBER_MIN',
    df=df, positions=[-1, 0, 1], initial_position=1,
    trading_fees=0.04 / 100,
    borrow_interest_rate=0,
    reward_function=reward_function)
# Agent
obs_space_dims = env.observation_space.shape[0]
action_space_dims = 3
agent = REINFORCE(obs_space_dims, action_space_dims)
# Train agent
epochs = 100
total_info = []
for epoch in range(1, epochs + 1):
    reward_over_epoch = 0
    obs, info = env.reset(seed=1411)
    done = False
    counter = 0
    while not done:
        action = agent.sample_action(obs)
        action = decoder.get(action.item())
        obs, reward, terminated, truncated, info = env.step(action)
        info['epoch'] = epoch
        agent.rewards.append(reward)
        reward_over_epoch += reward
        total_info.append(info)
        done = (terminated or truncated)
        counter += 1
    agent.update()
    print(f'Epoch: {epoch}, Reward: {reward_over_epoch}')
pd.DataFrame(total_info).to_csv('info.csv')
