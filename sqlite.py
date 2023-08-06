import sqlite3
from typing import List
import json

import sys
import csv
maxInt = sys.maxsize

while True:
    # decrease the maxInt value by factor 10 
    # as long as the OverflowError occurs.

    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)

JOIN_TABLE = 0
RECORD_TABLE = 1

class SQLITE:
    connection: sqlite3.Connection

    def __init__(self, dbname):
        self.connection = sqlite3.connect(dbname)
    
    # This function takes in a SQL file and executes it to create the tables
    def inititialize_tables(self, sql_file: str):
        cursor = self.connection.cursor()
        with open(sql_file, 'r') as sql_file:
            sql = sql_file.read()
            cursor.executescript(sql)
        self.connection.commit()

    # This function deletes all the tables in the database
    def delete_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(tables)
        for table in tables:
            cursor.execute(f"DROP TABLE {table[0]}") if table[0] != "sqlite_sequence" else None
        self.connection.commit()

    # The CSV file to load into the table has all columns except for the primary key column
    # This function inserts all the data from the csv file into the SQL table and allows the primary
    # key column to be autoincremented by the database. It uses executemany to insert all the data
    # at once, and then checks its work by printing the table
    # It determines the column names by checking the SQL that generated the table and getting the
    # column names from there, discarding the column name that is the primary key
    def enter_csv_into_table(self, table_name: str, csv_file: str):
        cursor = self.connection.cursor()
        columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        print(f"Columns: {columns}")
        columns = [column[1] for column in columns]
        columns = columns[1:]
        print(f"Columns: {columns}")
        with open(csv_file, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader)
            cursor.executemany(f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({','.join(['?'] * len(columns))})", csv_reader)
        
        #Here is where it checks its work
        rows = cursor.execute(f"SELECT * FROM {table_name}").fetchall()
        for row in rows:
            print(row)

        self.connection.commit()

    # This function usses the same logic as the previous function, but it creates a junction table
    # that connects two tables together. Each column in the junction table is a foreign key to the
    # primary key of the table it is connecting to. The input columns of the csv are the corresponding
    # values of the table it is connecting to. The function needs to treat each tables connected to as
    # a lookup table and convert the values into valid primary keys, then insert them into the junction
    # table
    def enter_junction_csv_into_table(self, left_table: str, right_table: str, csv_file: str):
        print(f"Created junction table {left_table}_to_{right_table}")
        cursor = self.connection.cursor()
        left_columns = cursor.execute(f"PRAGMA table_info({left_table})").fetchall()
        left_columns = [column[1] for column in left_columns]
        left_pk = left_columns[0]
        left_columns = left_columns[1]
        print(f"Left Columns: {left_columns}")
        right_columns = cursor.execute(f"PRAGMA table_info({right_table})").fetchall()
        right_columns = [column[1] for column in right_columns]
        right_pk = right_columns[0]
        right_columns = right_columns[1]
        print(f"Right Columns: {right_columns}")
        with open(csv_file, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            next(csv_reader)
            for row in csv_reader:
                print(row)
                left_values = row[0]
                right_values = row[1]

                left_values = cursor.execute(f"SELECT {left_pk} FROM {left_table} WHERE {left_columns} = ? ", (left_values,)).fetchall()
                
                right_values = cursor.execute(f"SELECT {right_pk} FROM {right_table} WHERE {right_columns} = ? ", (right_values,)).fetchall()

                cursor.execute(f"INSERT INTO {left_table}_to_{right_table} ({left_table}_id, {right_table}_id) VALUES (?, ?)", (left_values[0][0], right_values[0][0]))

        #Here is where it checks its work
        rows = cursor.execute(f"SELECT * FROM {left_table}_to_{right_table}").fetchall()
        for row in rows:
            print(row)

        self.connection.commit()

        # This function returns a row of info from the model table, and joins in all the info from the
        # other tables that are connected to it. It does this by using the junction tables to connect
        # the model table to the other tables, and then using the foreign keys in the junction tables
        # to connect to the other tables
        """
        SELECT DISTINCT model.context_id, model.model_hub, model.sha, model.repo_url, model.downloads, model.likes, model.excess_metadata, model_hub.url, model_hub.name, tag.name, framework.name, architecture.name, language.abbreviation, author.name, library.name, license.name,
FROM model
LEFT JOIN architecture ON architecture.architecture_id = model_to_architecture.architecture_id
LEFT JOIN author ON author.author_id = model_to_author.author_id
LEFT JOIN framework ON framework.framework_id = model_to_framework.framework_id
LEFT JOIN language ON language.language_id = dataset_to_language.language_id
LEFT JOIN library ON library.library_id = model_to_library.library_id
LEFT JOIN license ON license.license_id = model_to_license.license_id
LEFT JOIN model_hub ON model_hub.model_hub_id = model_hub_to_tag.model_hub_id
LEFT JOIN tag ON tag.tag_id = model_hub_to_tag.tag_id
WHERE model.context_id = 1"""
    def fetch_model_info(self, model_id: int):
        cursor = self.connection.cursor()
        model_info = cursor.execute(f"""
                                    SELECT model.id,
                                        model.context_id,
                                        model.model_hub,
                                        model.sha,
                                        model.repo_url,
                                        model.downloads,
                                        model.likes,
                                        tag.name,
                                        framework.name,
                                        architecture.name,
                                        language.abbreviation,
                                        author.name,
                                        library.name,
                                        license.name
                                    FROM model
                                    LEFT JOIN model_to_architecture ON model.id = model_to_architecture.model_id
                                    LEFT JOIN architecture ON model_to_architecture.architecture_id = architecture.architecture_id

                                    LEFT JOIN model_to_author ON model.id = model_to_author.model_id
                                    LEFT JOIN author ON model_to_author.author_id = author.author_id

                                    LEFT JOIN model_to_framework ON model.id = model_to_framework.model_id
                                    LEFT JOIN framework ON model_to_framework.framework_id = framework.framework_id

                                    LEFT JOIN model_to_language ON model.id = model_to_language.model_id
                                    LEFT JOIN language ON model_to_language.language_id = language.language_id

                                    LEFT JOIN model_to_library ON model.id = model_to_library.model_id
                                    LEFT JOIN library ON model_to_library.library_id = library.library_id

                                    LEFT JOIN model_to_license ON model.id = model_to_license.model_id
                                    LEFT JOIN license ON model_to_license.license_id = license.license_id

                                    LEFT JOIN model_to_tag ON model.id = model_to_tag.model_id
                                    LEFT JOIN tag ON model_to_tag.tag_id = tag.tag_id
                                    WHERE model.id = ?
                                    """, (model_id,)).fetchall()
        return model_info


if __name__ == "__main__":
    db = SQLITE("ptm.db")
    results = db.fetch_model_info(1)
    for row in results:
        print(row)
    # db.delete_tables()
    # db.inititialize_tables("ptm.sql")
    # table_names = ["architecture", "author", "framework", "language", "library", "license", "model_hub", "tag"]
    # # table_names = ["author"]
    # print("Entering model")
    # db.enter_csv_into_table("model", "csv/HuggingFace_model_updated.csv")
    # for name in table_names:
    #     print(f"Entering {name}")
    #     db.enter_csv_into_table(name, f"csv/HuggingFace_{name}_updated.csv")
    #     db.enter_junction_csv_into_table("model", name, f"csv/HuggingFace_model_to_{name}_updated.csv") if name != "model_hub" else None