import psycopg2
import petl as etl
from petl import Table
from typing import List
import psql_helper
from psycopg2.sql import Identifier, SQL
import json

JOIN_TABLE = 0
RECORD_TABLE = 1

class PSQL:
    connection: psycopg2.extensions.connection

    def __init__(self, hostname, dbname, username, pw):
        self.connection = psycopg2.connect(host=hostname, 
                                           database=dbname, 
                                           user=username, 
                                           password=pw, 
                                           port="5432"
        )
        self.init_db()

    def load_json(self, jsonfile: str, names: List[str], type: int):
        # table = etl.fromjson(jsonfile)
        with open(jsonfile) as js:
            raw_data = js.read()
        
        json_data = json.loads(raw_data)

        key = 2
        for entry_dict in json_data:
            entry_str = json.dumps(entry_dict)
            self.load_table(entry_dict, names, type, key)
            key +=1

    def load_table(self, table: Table, names: List[str], type: int, key: int):
        if(table == ""):
            return

        if(type == JOIN_TABLE):
            join_variables = []
            self.load(table.cut(0), names[0])
            self.load(table.cut(1), names[0])
            self.load_join_table(table, names[2], join_variables)
        elif(type == RECORD_TABLE):
            self.load(table, names[0], key)
        else:
            raise ValueError(f"Invalid table type {type}")

    def load(self, table: Table, name: str, key: int):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM information_schema.tables WHERE table_name=%s", (name,))
        ### NOTE: VERY arbitrary/manual right now because of constraints, is like this just to show that it works right now
        cursor.execute("INSERT INTO model_hub(model_hub_id, url, name) VALUES (%s, %s, %s)", (key, table["repo_url"], "huggingface"))
        cursor.execute(SQL("INSERT INTO {}(id, model_hub, context_id, repo_url) VALUES (%s, %s, %s, %s)").format(Identifier(name)), (key-1, key, table["context_id"], table["repo_url"]))
        cursor.execute(SQL("SELECT * FROM {} WHERE id IN (%s);").format(Identifier(name)), (key-1,))
        results = cursor.fetchall()
        self.connection.commit()
        cursor.close()
        print(results)

    def load_join_table(self, table: Table, name: str, join_variables: List[str]):
        cursor = self.connection.cursor()

        ### desired result: join data from table to data in "name" table

        # results = cursor.execute("select * from %s inner join %s on %s = %s", name, table, join_variables[0], join_variables[1])
        self.connection.commit()
        cursor.close()
        # print(results)

    def init_db(self):
        cursor = self.connection.cursor()
        psql_helper.init_db(cursor)
        self.connection.commit()
        cursor.close()

    # def query_table(self, name: str):

    #     cursor = self.connection.cursor()
    #     results = cursor.execute("select * from information_schema.tables where table_name=%s", (name,))
    #     self.connection.commit()
    #     cursor.close()

    #     return results
    #     pass`