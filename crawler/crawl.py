from pprint import pprint
from os import environ
import requests
from bs4 import BeautifulSoup
import schedule
import time
import datetime
import os
from influxdb import InfluxDBClient

domain = 'https://www.ss.com'

INFLUXDB_HOST = os.getenv("INFLUXDB_HOST")
INFLUXDB_PORT = os.getenv("INFLUXDB_PORT")
INFLUXDB_USER = os.getenv("INFLUXDB_USER")
INFLUXDB_PASS = os.getenv("INFLUXDB_PASS")
INFLUXDB_DB = os.getenv("INFLUXDB_DB")

def crawl_page(url, urls_parsed = None):

    pprint('Crawl ' + url)
    pprint('Urls already parsed:')
    pprint(urls_parsed)

    if( urls_parsed == None) :
        urls_parsed = [url]

    code = requests.get(url)
    s = BeautifulSoup(code.text, "html.parser")

    items = []

    next_page = domain + s.find('a', {'rel': 'next'}).get('href');

    for item in s.findAll('tr'):

        title_column = item.find('td', {'class': 'msg2'})
        price_column = item.find('td', {'class': 'msga2-o pp6'})

        if( price_column == None  ):
            print('No price found, skipping ...')
            # pprint([item, title_column, price_column])
            continue

        title = title_column.find('a', {'class': 'am'}).get_text('', strip=True)
        link = domain + title_column.find('a', {'class': 'am'}).get('href')
        price = price_column.get_text('', strip=True)

        if( price == None or price == 'pērku'  ):
            print('No price found, skipping ...')
            # pprint([item, title_column, price_column])
            continue

        price = float(price.replace(",", "").replace(" ", "").replace("€/t.", ""))

        items.append({
            "title": title,
            "link": link,
            "price": price
        })

    pprint('got ' + str(len(items)) + ' items')

    if( next_page not in urls_parsed ):
        urls_parsed.append(next_page)
        time.sleep(1)
        pprint('crawl next page')
        (items_2, urls_parsed) = crawl_page(next_page, urls_parsed)
        items = items + items_2

    return (items, urls_parsed)

def crawl():

    pprint("Starting crawler ...")
    
    influxClient = InfluxDBClient(INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USER, INFLUXDB_PASS, INFLUXDB_DB)
    influxClient.create_database(INFLUXDB_DB)

    (items, urls_parsed) = crawl_page('https://www.ss.com/lv/production-work/firewood/granules/')
    pprint(items)
    pprint(urls_parsed)

    time_now = datetime.datetime.now()

    pprint('to insert:')
    pprint(len(items))

    items_to_insert = []

    for item in items:
        (item['title'], item['link'], item['price'], time_now)
        items_to_insert.append({
                "measurement": "prices",
                "tags": {"title": item['title'], "url": item['link']},
                "time": time_now,
                "fields": {"title": item['title'], "url": item['link'], "price": item['price']}
            })

    try:
        influxClient.write_points(items_to_insert)
        print("inserted %d items" % len(items_to_insert))
    except (Exception) as error:
        print(error)

schedule.every(4).hours.do(crawl)

while True:
    schedule.run_pending()
    time.sleep(1)