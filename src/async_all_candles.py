import os
import asyncio
import argparse
import pandas as pd
from datetime import timedelta
from utils import historicCandles_to_df
from tinkoff.invest import AsyncClient, CandleInterval
from tinkoff.invest.utils import now

candles = []


async def main():
    async with AsyncClient(os.getenv('TOKEN')) as client:
        async for candle in client.get_all_candles(
            instrument_id=FIGI,
            from_=now() - timedelta(days=DAYS),
            interval=INTERVAL,
        ):
            candles.append(candle)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-days', type=int, help='The number of the days in the past')
    args = parser.parse_args()

    DAYS = args.days
    INTERVAL = CandleInterval.CANDLE_INTERVAL_1_MIN
    FIGI = 'BBG002W2FT69'
    NAME = 'candles_ABRD_min.csv'
    PATH_PROJ = os.getcwd()

    asyncio.run(main())
    pd.DataFrame(historicCandles_to_df(candles)).to_csv(
        os.path.join(PATH_PROJ, 'data', 'raw', NAME))
