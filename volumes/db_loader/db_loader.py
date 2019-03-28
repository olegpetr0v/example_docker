#-*- coding: utf-8 -*-

from datetime import datetime
from tzlocal import get_localzone
import pytz
import time
import pika
import json
import os
import schedule

from zabbix_loader import runZabbixDataLoad
from example_loader import runExampleDataLoad


# функция отправки сообщения об ошибке
def logError(resource, message):
    localTimeZone = get_localzone()
    localDatetime = localTimeZone.localize(datetime.today())
    cDatetime = localDatetime.astimezone(pytz.timezone('UTC'))
    payload = {
        'ts'       :  cDatetime.strftime('%Y-%m-%d %H:%M:%S'),
        'resource' : '%s' % resource,
        'message'  : '%s' % message
    }
    body = json.dumps(payload)
    credentials = pika.PlainCredentials('user', 'password')
    connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.20.100', 5672, '/vhost', credentials))
    channel = connection.channel()
    channel.basic_publish(exchange='e_exchange', routing_key='errors', body=body)
    connection.close()


def job():
    try:
        # загрузка данных из Zabbix
        runZabbixDataLoad()
    except Exception as err:
        logError('db_zabbix_loader', err)
    #
    try:
        # загрузка данных example
        runExampleDataLoad()
    except Exception as err:
        logError('example_loader', err)

if __name__ == '__main__':
    schedule.every().day.at("00:00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)
