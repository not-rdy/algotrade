import os
import sys
sys.path.append(os.getcwd())
import asyncio
from crossover_rule import CrossoverRule
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
                signal = cr.get_signal(marketdata)
                acc.manage_orders_and_sl(signal=signal, quantity=1)

        market_data_stream.info.subscribe(
            [InfoInstrument(figi='BBG004730N88')])


if __name__ == "__main__":

    cr = CrossoverRule(
        short_long_ma=['sma', 'lma'],
        window_short=7, window_long=7 + 2,
        eps=0.07, sl=-0.87,
        token=os.getenv('TOKEN'), acc_id=os.getenv('ACCOUNT'),
        figi='BBG004730N88'
    )
    acc = ACCManager(
        token=os.getenv('TOKEN'),
        figi='BBG004730N88',
        id_acc=os.getenv('ACCOUNT'))

    asyncio.run(main())
