import os
from utils import OrderToDict
from dbmanager import DBManager
from tinkoff.invest import (
    OrderBookInstrument,
    Client,
    InfoInstrument
)
from tinkoff.invest.utils import now
from tinkoff.invest.services import MarketDataStreamManager

TOKEN = os.environ["TOKEN"]
DB_PATH = os.path.join(os.getcwd(), 'data', 'db', 'ob.db')

db = DBManager(path=DB_PATH)

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
            ts = str(marketdata.orderbook.time)
            bids = [OrderToDict(order) for order in marketdata.orderbook.bids]
            asks = [OrderToDict(order) for order in marketdata.orderbook.asks]
            for b, a in zip(bids, asks):
                db.write_row(
                    data={
                        'ts': ts,
                        'bprice': b['price'], 'bquantity': b['quantity'],
                        'aprice': a['price'], 'aquantity': a['quantity']
                    },
                    table='ob'
                )

            print(marketdata.orderbook)
            print(' ')


if __name__ == "__main__":
    main()