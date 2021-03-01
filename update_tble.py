
# imports
import requests   
import filecmp
import psycopg2
from psycopg2 import Error
import os
# scrapping website to download csv file
url="https://data.ny.gov/api/views/nvxe-b625/rows.csv?accessType=DOWNLOAD"
r = requests.get(url, allow_redirects=True)
open('data/downloaded_lots.csv', 'wb').write(r.content)
# creating vars for each file
source_file = "data/Thruway_Commuter_Park_and_Ride_Lots.csv"
downloaded_file = "data/downloaded_lots.csv"
# comparing original data with new data
if filecmp.cmp(source_file, downloaded_file):
    pass
else:   # if data is updated
    try:
        # connection to database
        connection = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = connection.cursor()
        print("PostgreSQL connection is opened")
        # dropping table
        tble_name = "lots"
        drop_table_query = "DROP TABLE IF EXISTS "+tble_name+";"
        cursor.execute(drop_table_query)
        # creating new table
        create_table_query = "CREATE TABLE "+tble_name+"(lot_name varchar, exit varchar, operator varchar, available_spaces int, is_paved varchar, light varchar, comments varchar, latitutide float, longtitude float, lot_location varchar);"
        cursor.execute(create_table_query)
        # copying data into new created table
        with open(downloaded_file, "r") as f:
            next(f)
            cursor.copy_from(f, 'lots', sep=',')
        connection.commit()
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
    