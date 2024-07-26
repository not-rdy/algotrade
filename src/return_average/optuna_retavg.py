import os
import sys
import optuna
import pandas as pd
import argparse
from datetime import datetime
from multiprocessing import Pool
sys.path.append(os.getcwd())
from retavg_rule import ReturnAvgRule


def get_profit(pr: pd.DataFrame, ra: ReturnAvgRule) -> float:
    date = pr['t'].dt.date.iloc[0]
    start = datetime(year=date.year, month=date.month, day=date.day, hour=7)  # noqa: E501
    end = datetime(year=date.year, month=date.month, day=date.day, hour=15)
    pr = pr[(pr['t'] >= start) & (pr['t'] <= end)].reset_index(drop=True)

    deals_profit = []
    for i in range(0, pr.shape[0]):
        h, l, p = pr[['h', 'l', 'p']].iloc[i]
        signal = ra.get_signal((h, l, p))
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
    params = {
        'data_cash_size': 60,
        'low_q': trial.suggest_float('low_q', 0.5, 1, step=0.1),
        'high_q': trial.suggest_float('high_q', 0.5, 1, step=0.1),
        'sl': trial.suggest_float('sl', -1, -0.1, step=0.1),
        'window_avg': trial.suggest_int('window_avg', 2, 60),
        'window_diff_high_avg': trial.suggest_int(
            'window_diff_high_avg', 2, 60),
        'window_diff_avg_low': trial.suggest_int(
            'window_diff_avg_low', 2, 60),
        'avgprice_quantile_dist': trial.suggest_float(
            'avgprice_quantile_dist', 0.01, 0.5, step=0.01),
        'variance': trial.suggest_float(
            'variance', 0.01, 0.1, step=0.01),
        'verbose': False
    }
    prices['date'] = prices['t'].dt.date
    arguments = [
        (df[1], ReturnAvgRule(**params))
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
        os.path.join(os.getcwd(), 'data', 'interim', 'trials_retavg.csv'))
