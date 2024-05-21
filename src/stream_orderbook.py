import os
from tinkoff.invest import (
    OrderBookInstrument,
    Client,
    InfoInstrument
)
from tinkoff.invest.services import MarketDataStreamManager

TOKEN = os.environ["TOKEN"]

def main():

    with Client(TOKEN) as client:
        market_data_stream: MarketDataStreamManager = client.create_market_data_stream()
        market_data_stream.order_book.subscribe(
            instruments=[
                OrderBookInstrument(
                    depth=50,
                    instrument_id="BBG004730N88",
                    order_book_type=1
                )
            ]
        )
        for marketdata in market_data_stream:
            if marketdata.orderbook is None:
                continue
            market_data_stream.info.subscribe([InfoInstrument(instrument_id="BBG004730N88")])
            print(marketdata.orderbook)


if __name__ == "__main__":
    main()