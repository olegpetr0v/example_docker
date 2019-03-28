#-*- coding: utf-8 -*-

import psycopg2
import pika
import json
from datetime import datetime
from tzlocal import get_localzone
import pytz


DB_REQ_example = "dbname='example' user='example_user' host='192.168.0.1' password='password'"
RABBITMQ_WRONG_DATA_DIRPATH = '/rabbitmq_netris_listener/wrong_messages/'

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
    credentials = pika.PlainCredentials('ex', 'password')
    connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.0.1', 5672, '/ex', credentials))
    channel = connection.channel()
    channel.basic_publish(exchange='ex_exchange', routing_key='errors', body=body)
    connection.close()
    

def dbWrite(query):
    db_con = psycopg2.connect(DB_REQ_example)
    cursor = db_con.cursor()
    cursor.execute(query)
    db_con.commit()
    db_con.close()
    

def writeWrongMessage(mType, body):
    date = datetime.today().strftime('%Y%m%d')
    filePath = RABBITMQ_WRONG_DATA_DIRPATH + '%s_%s.csv' % (mType, date)
    with open(filePath, 'ab') as f:
        f.write(body)
        f.write(b'\n')
        f.close()