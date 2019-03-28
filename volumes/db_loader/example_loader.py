#-*- coding: utf-8 -*-

import psycopg2
import os


DB_REQ = "dbname='dbname' user='db_user' host='192.168.20.100' password='password'"


def dbWrite(query):
    db_con = psycopg2.connect(DB_REQ)
    cursor = db_con.cursor()
    cursor.execute(query)
    db_con.commit()
    db_con.close()

    
def load(filename, filenameInUse, query):
    try:
        os.rename(filename, filenameInUse)
        values, i = [], 0
        with open(filenameInUse, 'rt') as f:
            for line in f.readlines():
                line = line.replace('\n','')
                if len(line) != 0:
                    values.append(line)
                i += 1
                if i == 100000 and len(values) != 0:
                    dbWrite(query % ','.join(values))
                    values, i = [], 0
            f.close()
        if i != 0 and len(values) != 0:
            dbWrite(query % ','.join(values))
            values, i = [], 0 
        #
        os.remove(filenameInUse)
    except FileNotFoundError:
        pass

    
def Load1():
    filename = '/rabbitmq_listener/messages/1.csv' 
    filenameInUse = '/rabbitmq_listener/messages/1InUse.csv'
    query = "INSERT INTO example.t_1_test VALUES %s;"
    load(filename, filenameInUse, query)


def Load2():
    filename = '/rabbitmq_listener/messages/2.csv' 
    filenameInUse = '/rabbitmq_listener/messages/2InUse.csv'
    query = "INSERT INTO example.t_2_test VALUES %s;"
    load(filename, filenameInUse, query)


def runNetrisDataLoad():
    Load1()
    Load2()
