# Original taken from https://mfadhel.com/transferring_data_to_influx/
# by MUNTAZIR FADHEL

from datetime import datetime

### PostgreSQL DB info ###
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
load_dotenv(verbose=True)

import os
POSTGRESQL_HOST = os.getenv("POSTGRESQL_HOST")
POSTGRESQL_PORT = os.getenv("POSTGRESQL_PORT")
POSTGRESQL_USER = os.getenv("POSTGRESQL_USER")
POSTGRESQL_PASS = os.getenv("POSTGRESQL_PASS")
POSTGRESQL_DB = os.getenv("POSTGRESQL_DB")
INFLUXDB_HOST = os.getenv("INFLUXDB_HOST")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
INFLUXDB_USER = os.getenv("INFLUXDB_USER")
INFLUXDB_PASS = os.getenv("INFLUXDB_PASS")
INFLUXDB_DB = os.getenv("INFLUXDB_DB")

postgresql_table_name = ""
conn = psycopg2.connect("dbname=%s user=%s password=%s host=%s port=%s" %
        (
            POSTGRESQL_DB, POSTGRESQL_USER, POSTGRESQL_PASS, POSTGRESQL_HOST, POSTGRESQL_PORT
        ))

### InfluxDB info ####
from influxdb import InfluxDBClient
influxClient = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER, INFLUXDB_PASS, INFLUXDB_DB)

# influxClient.delete_database(INFLUXDB_DB)
influxClient.create_database(INFLUXDB_DB)

# dictates how columns will be mapped to key/fields in InfluxDB
schema = {
    "time_column": "date", # the column that will be used as the time stamp in influx
    "columns_to_fields" : ["price", "title", "url"], # columns that will map to fields 
    "columns_to_tags" : ["title","url"], # columns that will map to tags
    "table_name_to_measurement" : "prices", # table name that will be mapped to measurement
    }

'''
Generates an collection of influxdb points from the given SQL records
'''
def generate_influx_points(records):
    influx_points = []
    for record in records:
        tags = {}
        fields = {}
        for tag_label in schema['columns_to_tags']:
            tags[tag_label] = record[tag_label]
        for field_label in schema['columns_to_fields']:
            fields[field_label] = record[field_label]

        influx_points.append({
            "measurement": schema['table_name_to_measurement'],
            "tags": tags,
            "time": record[schema['time_column']],
            "fields": fields
        })
    return influx_points

# query relational DB for all records
curr = conn.cursor('cursor', cursor_factory=psycopg2.extras.RealDictCursor)
# curr = conn.cursor(dictionary=True)
curr.execute("SELECT * FROM " + schema['table_name_to_measurement'] + " ORDER BY " + schema['time_column'] + " DESC;")
row_count = 0
# process 1000 records at a time
while True:
    print("Processing row #" + str(row_count + 1))
    selected_rows = curr.fetchmany(1000)
    influxClient.write_points(generate_influx_points(selected_rows))
    row_count += 1000
    if len(selected_rows) < 1000:
        break
conn.close()
