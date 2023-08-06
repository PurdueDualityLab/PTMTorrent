import petl as etl
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

model_table = etl.fromcsv('csv/HuggingFace_model.csv')
disc_table = etl.fromjson('json/discussions/HF_model_0k-1k_discussions.json')
for i in range(1, 15):
    if i == 10: continue
    table = etl.fromjson(f'json/discussions/HF_model_{i}k-{i+1}k_discussions.json')
    disc_table = etl.cat(disc_table, table)
table3 = etl.leftjoin(model_table, disc_table, key='context_id')
etl.tocsv(table3, 'csv/HF_model_0k-15k.csv')