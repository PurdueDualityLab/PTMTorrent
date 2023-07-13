import psycopg2
import petl as etl
from petl import Table
from typing import List

JOIN_TABLE = 0
RECORD_TABLE = 1

class PSQL:
    connection: psycopg2.extensions.connection

    def __init__(self):
        self.connection = psycopg2.connect()

    def load_json(self, jsonfile: str, names: List[str], type: int):
        table = etl.fromjson(jsonfile)
        self.load_table(table, names, type)

    def load_table(self, table: Table, names: List[str], type: int):
        if(table.nrows() == 0):
            return

        if(type == JOIN_TABLE):
            self.load_record_table(table.cut(0), names[0])
            self.load_record_table(table.cut(1), names[0])
            self.load_join_table(table, names[2])
        elif(type == RECORD_TABLE):
            self.load_record_table(table, names[0])
        else:
            raise ValueError(f"Invalid table type {type}")

    def load(self, table: Table, name: str):
        cursor = self.connection.cursor()
        cursor.execute("select * from information_schema.tables where table_name=%s", (name,))
        if bool(cursor.rowcount):
            cursor.execute(f"CREATE TABLE %s", (table,))
        cursor.execute(f"INSERT INTO %s VALUES %s", (name, table,))
        results = cursor.execute(f"SELECT * FROM %s WHERE value IN %s", (name, table))
        print(results)
        return results

