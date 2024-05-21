import os
from tinkoff.invest import (
    TradeInstrument,
    Client,
    InfoInstrument
)
from tinkoff.invest.services import MarketDataStreamManager

TOKEN = os.environ["TOKEN"]

def main():

    with Client(TOKEN) as client:
        market_data_stream: MarketDataStreamManager = client.create_market_data_stream()
        market_data_stream.trades.subscribe(
            instruments=[
                TradeInstrument(
                    instrument_id="BBG004730N88"
                )
            ]
        )
        for marketdata in market_data_stream:
            if marketdata.trade is None:
                continue
            market_data_stream.info.subscribe([InfoInstrument(instrument_id="BBG004730N88")])
            print(marketdata.trade)

if __name__ == "__main__":
    main()
