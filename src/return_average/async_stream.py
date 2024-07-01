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
                    figi='BBG004730N88',
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
            [InfoInstrument(figi='BBG004730N88')])


if __name__ == "__main__":

    ra = ReturnAvgRule(
        data_cash_size=60,
        low_q=0.001, high_q=0.001,
        sl=-0.4, window_avg=60,
        window_diff_high_avg=60, window_diff_avg_low=60,
        token=os.getenv('TOKEN'), acc_id=os.getenv('ACCOUNT'),
        figi='BBG004730N88', avgprice_quantile_dist=0.01
    )
    acc = ACCManager(
        token=os.getenv('TOKEN'),
        figi='BBG004730N88',
        id_acc=os.getenv('ACCOUNT'))

    asyncio.run(main())
