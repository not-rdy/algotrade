import os
import sqlite3
from tqdm import tqdm
from utils import load
from dbmanager import DBManager

PATH = os.path.join(os.getcwd(), 'data', 'db', 'db.db')
conn = sqlite3.connect(PATH)
cursor = conn.cursor()

db = DBManager(PATH)

data_ob = load('/Users/rkam/projs/algotrade/data/interim/orderbook.pkl')
data_tr = load('/Users/rkam/projs/algotrade/data/interim/trades.pkl')

for ts in tqdm(data_ob.keys(), total=len(data_ob)):
    bids = data_ob[ts]['bids']
    asks = data_ob[ts]['asks']
    for b, a in zip(bids, asks):
        bprice = b['bids_price']
        bquantity = b['bids_quantity']
        aprice = a['asks_price']
        aquantity = a['asks_quantity']
        cursor.execute(
            f"""
            INSERT INTO
                ob (ts, bprice, bquantity, aprice, aquantity)
            VALUES
                ('{ts}', '{bprice}', '{bquantity}', '{aprice}', '{aquantity}');
            """
        )
conn.commit()

for tr in tqdm(data_tr, total=len(data_tr)):
    ts, direction, price, quantity = tr['time'], tr['direction'], tr['price'], tr['quantity']
    cursor.execute(
        f"""
        INSERT INTO
            tr (ts, direction, price, quantity)
        VALUES
            ('{ts}', '{direction}', '{price}', '{quantity}')
        """
    )
conn.commit()
conn.close()

for ts in tqdm(data_ob.keys(), total=len(data_ob)):
    bids = data_ob[ts]['bids']
    asks = data_ob[ts]['asks']
    for b, a in zip(bids, asks):
        bprice = b['bids_price']
        bquantity = b['bids_quantity']
        aprice = a['asks_price']
        aquantity = a['asks_quantity']
        db.write_row(
            data={
                'ts': ts,
                'bprice': bprice, 'bquantity': bquantity,
                'aprice': aprice, 'aquantity': aquantity
                },
            table='ob'
        )

for tr in tqdm(data_tr, total=len(data_tr)):
    del tr['figi']
    db.write_row(
        data={
            'ts': tr['time'],
            'direction': tr['direction'],
            'price': tr['price'],
            'quantity': tr['quantity']
        },
        table='tr')

print(
    db.read(
        """
        select
            *
        from
            ob
        """
        )
    )
print(
    db.read(
        """
        select
            *
        from
            tr
        """
        )
    )