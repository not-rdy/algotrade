import os
import sys
sys.path.append(os.getcwd())
import asyncio
from retavg_rule import ReturnAvgRule
from src.account_manager import ACCManager
from tinkoff.invest import (
    AsyncClient,
    CandleInstrument,
    InfoInstrument
)
from tinkoff.invest.async_services import AsyncMarketDataStreamManager
from tinkoff.invest import SubscriptionInterval


async def main():
    async with AsyncClient(os.getenv('TOKEN')) as client:
        market_data_stream: AsyncMarketDataStreamManager = (
            client.create_market_data_stream()
        )
        market_data_stream.candles.waiting_close().subscribe(
            [
                CandleInstrument(
                    figi=FIGI,
                    interval=SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE  # noqa: E501
                )
            ]
        )
        async for marketdata in market_data_stream:

            if marketdata.candle is not None:
                print(marketdata.candle)
                signal = ra.get_signal(marketdata)
                acc.manage_orders_and_sl(signal=signal, quantity=1)

        market_data_stream.info.subscribe(
            [InfoInstrument(figi=FIGI)])


if __name__ == "__main__":

    FIGI = 'BBG002W2FT69'

    ra = ReturnAvgRule(
        data_cash_size=60,
        low_q=0.5, high_q=1, sl=-0.8, window_avg=4,
        window_diff_high_avg=5, window_diff_avg_low=5,
        variance=0.08, avgprice_quantile_dist=0.16)
    acc = ACCManager(
        token=os.getenv('TOKEN'),
        figi=FIGI,
        id_acc=os.getenv('ACCOUNT'))

    asyncio.run(main())
