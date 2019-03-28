#-*- coding: utf-8 -*-

import psycopg2
import pika
import json
from datetime import datetime
import pytz
import time
import os

from supfuncs import logError, dbWrite, writeWrongMessage


DB_REQ_example = "dbname='example' user='example_user' host='192.168.0.1' password='password'"

RABBITMQ_USER = 'ex'
RABBITMQ_PASSWORD = 'password'
RABBITMQ_ex_VHOST = '/ex'

RABBITMQ_ADDRESS = '172.20.0.1'
RABBITMQ_PORT = 5672


#-----------------------------------------------------------------------------------------------------------------#

def callback_1(ch, method, properties, body):
    try:
        m = json.loads(body.decode('utf-8'))
        mType = '1'
        #
        if all([isinstance(m['ts'], str),
                isinstance(m['cam_name'], str),
                isinstance(m['ms'], bool),
                isinstance(m['face_id'], int),
                isinstance(m['bbox']['x1'], int),
                isinstance(m['bbox']['x2'], int),
                isinstance(m['bbox']['y1'], int),
                isinstance(m['bbox']['y2'], int)
               ]) is not True:
            raise Exception('wrong message format')
        #
        values = '''
           (to_timestamp('%s','YYYY-MM-DD HH24:MI:SS'),
            '%s',
            %s,
            %s,
            '{%s,%s,%s,%s}'
            )
            ''' % (m['ts'],
                   m['cam_name'],
                   m['ms'],
                   m['face_id'],
                   m['bbox']['x1'],
                   m['bbox']['x2'],
                   m['bbox']['y1'],
                   m['bbox']['y2'])
        #
        with open('/rabbitmq_ex_listener/messages/dface.csv', 'at') as f:
            f.write(values.replace('\n',''))
            f.write('\n')
            f.close()
        #
        ch.basic_ack(delivery_tag = method.delivery_tag)
        #
    except Exception as err:
        logError('rabbitmq_listener_1', err)
        writeWrongMessage(mType, body)
        ch.basic_ack(delivery_tag = method.delivery_tag)


if __name__ == '__main__':
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_ADDRESS,
                                                                   RABBITMQ_PORT,
                                                                   RABBITMQ_ex_VHOST,
                                                                   credentials))
    channel = connection.channel()
    channel.basic_qos(prefetch_count=100)
    #
    channel.basic_consume(callback_1, queue='1_test')
    #
    channel.start_consuming()
