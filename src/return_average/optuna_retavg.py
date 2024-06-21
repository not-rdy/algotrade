import os
import sys
import optuna
import pandas as pd
import argparse
from datetime import datetime
from multiprocessing import Pool
sys.path.append(os.getcwd())
from src.dbmanager import DBManager
from signal_maker import SignalMaker


def get_profit(pr: pd.DataFrame, params: dict) -> float:
    date = pr['t'].dt.date.iloc[0]
    start = datetime(year=date.year, month=date.month, day=date.day, hour=10)  # noqa: E501
    end = datetime(year=date.year, month=date.month, day=date.day, hour=18)
    pr = pr[(pr['t'] >= start) & (pr['t'] <= end)].reset_index(drop=True)

    sm = SignalMaker(**params)
    deals_profit = []
    for i in range(0, pr.shape[0]):
        p = pr['p'].iloc[i]
        signal = sm.get_signal(p)
        if signal is not None and signal['action'] == 'close':
            deals_profit.append(signal['profit_current'])
    return deals_profit


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
    data_cash_size = 5000
    params = {
        'data_cash_size': data_cash_size,
        'low_q': trial.suggest_float(
            'low_q', 0.5, 0.9, step=0.01),
        'high_q': trial.suggest_float(
            'high_q', 0.5, 0.9, step=0.01),
        'coeff_for_SL': trial.suggest_float(
            'coeff_for_SL', 0.01, 0.1, step=0.01),
        'window_avg': trial.suggest_int(
            'window_avg', 1, data_cash_size),
        'window_diff_high_avg': trial.suggest_int(
            'window_diff_high_avg', 1, data_cash_size),
        'window_diff_avg_low': trial.suggest_int(
            'window_diff_avg_low', 1, data_cash_size),
        'coeff_for_TP': trial.suggest_float(
            'take_profit', 0.05, 0.2, step=0.01),
        'price_delta': trial.suggest_float(
            'price_delta', 0.05, 0.2, step=0.01)
    }

    prices['date'] = prices['t'].dt.date
    arguments = [
        (df[1], params)
        for df in prices.groupby('date')]
    with Pool(args.n_jobs) as p:
        profits = p.starmap(get_profit, arguments)
        profits = [p for p_day in profits for p in p_day]
        if len(profits) == 0:
            return -10
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
