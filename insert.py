
# imports
import requests   
import filecmp
import psycopg2
import os
# scrapping website to download csv file
url="https://data.ny.gov/api/views/nvxe-b625/rows.csv?accessType=DOWNLOAD"
r = requests.get(url, allow_redirects=True)
open('downloaded_lots.csv', 'wb').write(r.content)
# creating vars for each file
source_file = "data/lots.csv"
downloaded_file = "downloaded_lots.csv"
# comparing original data with new data
if filecmp.cmp(source_file, downloaded_file):
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"), sslmode='require')
    print(conn)
# if data is updated
else:
    """# connection to database
    connection = psycopg2.connect(
        host=os.environ.get("HOST"),
        database=os.environ.get("DATABASE"),
        user=os.environ.get("USER"),
        password=os.environ.get("PASSWORD")
    )
    cursor = conn.cursor()
    # update records
    sql_file = open("insert.sql")
    sql_as_string = sql_file.read()
    cursor.executescript(sql_as_string)
    for row in cursor.execute("SELECT * FROM lots"):
        print(row)"""
    
    pass
    