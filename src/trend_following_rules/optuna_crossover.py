import os
import sys
import optuna
import pandas as pd
import argparse
from datetime import datetime
from multiprocessing import Pool
sys.path.append(os.getcwd())
from crossover_rule import CrossoverRule


def get_profit(pr: pd.DataFrame, cr: CrossoverRule) -> float:
    print(cr.get_content())
    date = pr['t'].dt.date.iloc[0]
    start = datetime(year=date.year, month=date.month, day=date.day, hour=7)  # noqa: E501
    end = datetime(year=date.year, month=date.month, day=date.day, hour=15)
    pr = pr[(pr['t'] >= start) & (pr['t'] <= end)].reset_index(drop=True)

    deals_profit = []
    for i in range(0, pr.shape[0]):
        p = pr['p'].iloc[i]
        signal = cr.get_signal(p)
        if signal is not None and signal['action'] == 'close':
            deals_profit.append(signal['profit_current'])
    return deals_profit


def objective(trial):
    prices = pd.read_csv(
        os.path.join(
            os.getcwd(), 'data', 'raw', 'candles_SBER.csv'),
        index_col=0)
    prices.columns = ['o', 'h', 'l', 'p', 'v', 't']
    prices['t'] = pd.to_datetime(prices['t'], format='mixed')
    prices['t'] = prices['t'].dt.tz_localize(None)
    prices['week'] = prices['t'].dt.day_of_week
    prices = prices[~prices['week'].isin([5, 6])].reset_index(drop=True)

    # hyperparams
    ma_short_type = trial.suggest_categorical(
        'ma_short_type', ['sma', 'lma', 'ema'])
    ma_long_type = trial.suggest_categorical(
        'ma_long_type', ['sma', 'lma', 'ema'])
    window_short = trial.suggest_int(
        'window_short', 2, 15, step=1)
    window_long = window_short + trial.suggest_int(
        'long_window_diff', 2, 15, step=1)
    params = {
        'short_long_ma': [ma_short_type, ma_long_type],
        'window_short': window_short,
        'window_long': window_long,
        'eps': trial.suggest_float('eps', 0.01, 0.5, step=0.01),
        'sl': trial.suggest_float('sl', -1, -0.1, step=0.01)
    }
    prices['date'] = prices['t'].dt.date
    arguments = [
        (df[1], CrossoverRule(**params))
        for df in prices.groupby('date')]
    with Pool(args.n_jobs) as p:
        profits = p.starmap(get_profit, arguments)
        profits = [p for p_day in profits for p in p_day]
    if len(profits) == 0:
        return -1000000
    else:
        return sum(profits)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-n_jobs', type=int)
    parser.add_argument('-n_trials', type=int)
    args = parser.parse_args()

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=args.n_trials)
    study.trials_dataframe().to_csv(
        os.path.join(os.getcwd(), 'data', 'interim', 'trials_crossover.csv'))
