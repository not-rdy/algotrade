import os
import sqlite3

PATH = os.path.join(os.getcwd(), 'data', 'db', 'db.db')

# creating an database
conn = sqlite3.connect(PATH)
cursor = conn.cursor()
# creating a orderbook table
cursor.execute(
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
conn.commit()
# creating an trades table
cursor.execute(
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
conn.commit()
# close
conn.close()
