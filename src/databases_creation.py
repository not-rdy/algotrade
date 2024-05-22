import os
import sqlite3

PATH_OB = os.path.join(os.getcwd(), 'data', 'db', 'ob.db')
PATH_TR = os.path.join(os.getcwd(), 'data', 'db', 'tr.db')

# creating an database
conn_ob = sqlite3.connect(PATH_OB)
conn_tr = sqlite3.connect(PATH_TR)
# creating a orderbook table
cursor_ob = conn_ob.cursor()
cursor_ob.execute(
    """
    CREATE TABLE IF NOT EXISTS
        ob (
            ts TEXT NOT NULL,
            bprice REAL NOT NULL,
            bquantity INTEGER NOT NULL,
            aprice REAL NOT NULL,
            aquantity INTEGER NOT NULL
        )
    """
)
conn_ob.commit()
# creating an trades table
cursor_tr = conn_tr.cursor()
cursor_tr.execute(
    """
    CREATE TABLE IF NOT EXISTS
        tr (
            ts TEXT NOT NULL,
            direction INTEGER NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL
        )
    """
)
conn_tr.commit()
# close
conn_ob.close()
conn_tr.close()
