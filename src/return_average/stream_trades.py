import os
import sys
from tinkoff.invest import (
    TradeInstrument,
    Client,
    InfoInstrument
)
from tinkoff.invest.services import MarketDataStreamManager
sys.path.append(os.getcwd())
from signal_maker import SignalMaker
from src.account_manager import ACCManager

TOKEN = os.environ["TOKEN"]
ACCOUNT = os.environ['ACCOUNT']
FIGI = "BBG004730N88"

sm = SignalMaker(
    data_cash_size=5000,
    low_q=0.6, high_q=0.79,
    coeff_for_SL=0.06, window_avg=3269,
    window_diff_high_avg=229, window_diff_avg_low=4962,
    token=TOKEN, acc_id=ACCOUNT, figi=FIGI,
    price_delta=0.12, coeff_for_TP=0.16
)
acc = ACCManager(token=TOKEN, figi=FIGI, id_acc=ACCOUNT)


def main():

    with Client(TOKEN) as client:
        market_data_stream: MarketDataStreamManager = client.create_market_data_stream()  # noqa: E501
        market_data_stream.trades.subscribe(
            instruments=[
                TradeInstrument(
                    instrument_id=FIGI
                )
            ]
        )
        for marketdata in market_data_stream:
            if marketdata.trade is None:
                continue
            market_data_stream.info.subscribe([InfoInstrument(instrument_id=FIGI)])  # noqa: E501

            signal = sm.get_signal(marketdata)
            if signal is not None:
                acc.manage_orders_and_sl(signal, 1)


if __name__ == "__main__":
    main()
