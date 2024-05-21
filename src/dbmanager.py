import sqlite3

class DBManager:
    def __init__(self, path: str) -> None:
        self.conn = sqlite3.connect(path)
        self.cur = self.conn.cursor()

    
    def write_row(self, data: dict, table: str) -> None:
        self.cur.execute(
            f"""
            INSERT INTO
                {table} ({', '.join(data.keys())})
            VALUES
                ({', '.join(["'"+str(x)+"'" for x in data.values()])})
            """
        )
    
    def read(self, query: str) -> str:
        return self.cur.execute(f"{query}").fetchall()
 
    def __del__(self) -> None:
        self.conn.commit()
        self.conn.close()

