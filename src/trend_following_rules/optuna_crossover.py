import os
import sys
import optuna
import pandas as pd
import numpy as np
import argparse
from datetime import datetime
from multiprocessing import Pool
sys.path.append(os.getcwd())
from src.dbmanager import DBManager
from lma import LinearMA


def get_profit(
        pr: pd.DataFrame,
        n_short: int, n_long: int, eps: float, sl: float) -> float:
    date = pr['t'].dt.date.iloc[0]
    fee = 0.04 / 100
    price_entry = None
    state = 'free'
    start = datetime(year=date.year, month=date.month, day=date.day, hour=10)  # noqa: E501
    end = datetime(year=date.year, month=date.month, day=date.day, hour=18)
    pr = pr[(pr['t'] >= start) & (pr['t'] <= end)].reset_index(drop=True)

    ma_short = LinearMA(n_short)
    ma_long = LinearMA(n_long)
    profits = []

    pr['ma_short'] = None
    pr['ma_long'] = None
    pr['action'] = None
    for i in range(0, pr.shape[0]):
        p = pr['p'].iloc[i]
        ma_value_short = ma_short.get(p)
        ma_value_long = ma_long.get(p)
        if ma_value_long is None:
            continue
        pr.loc[i, 'ma_short'] = ma_value_short
        pr.loc[i, 'ma_long'] = ma_value_long

        # enter into a deal
        if state == 'free':
            diff = ma_value_short - ma_value_long
            if diff > eps:
                state = 'long'
                pr.loc[i, 'action'] = 'open_long'
            elif diff <= -eps:
                state = 'short'
                pr.loc[i, 'action'] = 'open_short'
            else:
                continue
            price_entry = p
            cost = p * fee

        # out of the deal
        if state == 'long':
            deviation = p - price_entry
            ma_value_short = ma_short.get(p)
            ma_value_long = ma_long.get(p)
            if deviation <= sl or ma_value_long >= ma_value_short:
                cost += p * fee
                profits.append(p - price_entry - cost)
                state = 'free'
                pr.loc[i, 'action'] = 'close_long'
        if state == 'short':
            deviation = price_entry - p
            ma_value_short = ma_short.get(p)
            ma_value_long = ma_long.get(p)
            if deviation <= sl or ma_value_long <= ma_value_short:
                cost += p * fee
                profits.append(price_entry - p - cost)
                state = 'free'
                pr.loc[i, 'action'] = 'close_short'
    return profits


def objective(trial):
    db = DBManager(path=os.path.join(os.getcwd(), 'data', 'db', 'tr.db'))
    prices = db.read(
        """
        select
            *
        from
            tr
        """
    )
    prices.columns = ['t', 'd', 'p', 'v']
    prices['t'] = pd.to_datetime(prices['t'], format='mixed')
    prices['t'] = prices['t'].dt.tz_localize(None)

    # hyperparams
    n_short = trial.suggest_int('n_short', 10, 1000, step=10)
    delta_long = trial.suggest_int('n_long', 10, 5000, step=10)
    n_long = n_short + delta_long
    sl = trial.suggest_float('sl', -1, -0.1, step=0.1)
    eps = trial.suggest_float('eps', 0.01, 0.5, step=0.01)

    prices['date'] = prices['t'].dt.date
    arguments = [
        (df[1], n_short, n_long, eps, sl)
        for df in prices.groupby('date')]
    with Pool(args.n_jobs) as p:
        profits = p.starmap(get_profit, arguments)
        profits = [p for p_day in profits for p in p_day]
    return np.mean(profits), np.var(profits)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-n_jobs', type=int)
    parser.add_argument('-n_trials', type=int)
    args = parser.parse_args()

    study = optuna.create_study(directions=['maximize', 'minimize'])
    study.optimize(objective, n_trials=args.n_trials)
    study.trials_dataframe().to_csv(
        os.path.join(os.getcwd(), 'data', 'interim', 'trials.csv'))
