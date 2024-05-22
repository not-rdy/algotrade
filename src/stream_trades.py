import os
from dbmanager import DBManager
from tinkoff.invest.utils import quotation_to_decimal
from tinkoff.invest import (
    TradeInstrument,
    Client,
    InfoInstrument
)
from tinkoff.invest.services import MarketDataStreamManager

TOKEN = os.environ["TOKEN"]
DB_PATH = os.path.join(os.getcwd(), 'data', 'db', 'db.db')

db = DBManager(DB_PATH)

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
            db.write_row(
                data={
                    'ts': str(marketdata.trade.time),
                    'direction': int(marketdata.trade.direction),
                    'price': float(quotation_to_decimal(marketdata.trade.price)),
                    'quantity': marketdata.trade.quantity
                },
                table='tr'
            )

            print(marketdata.trade)
            print(' ')

if __name__ == "__main__":
    main()
