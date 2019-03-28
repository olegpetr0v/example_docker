#-*- coding: utf-8 -*-

from datetime import datetime, timedelta
from tzlocal import get_localzone
import pytz
import os
import json
import requests
import psycopg2


BEGIN_DATE_FILEPATH = '/db_loader/bDate.txt'

DB_REQ_BI_ECHD = "dbname='dbname' user='db_user' host='192.168.20.100' password='password'"

ZABBIX = 'http://192.168.0.1/zabbix/api_jsonrpc.php' #адрес Zabbix
LOGIN = 'login' #логин для подключения к Zabbix
PASSWORD = 'password' #пароль для подключения к Zabbix

ITEMS = {
    'in15.1989':{ #Incoming (itemid: 2291066)
        'itemid':2291066,
        'channel':'internet',
        'direction':'in'
    },
    'out15.1989':{ #Outgoing (itemid: 2291067)
        'itemid':2291067,
        'channel':'internet',
        'direction':'out'
    },
    'in12.3827':{ #Incoming (itemid: 6082786)
        'itemid':6082786,
        'channel':'kms',
        'direction':'in'
    },
    'out12.3827':{ #Outgoing (itemid: 6082789)
        'itemid':6082789,
        'channel':'kms',
        'direction':'out'
    }
}


def getTodayDate():
    localTimeZone = get_localzone()
    localDate = localTimeZone.localize(datetime.today())
    cDate = localDate.astimezone(pytz.timezone('Europe/Moscow')).date()
    return cDate

def getBeginDate():
    if os.path.isfile(BEGIN_DATE_FILEPATH) is True:
        with open(BEGIN_DATE_FILEPATH) as f:
            strdate = f.read()
            f.close()
        lastDate = datetime.strptime(strdate, '%Y-%m-%d').date()
    else:
        lastDate = None
    return lastDate


def getYesterdayDate():
    cDate = getTodayDate()
    yDate = cDate - timedelta(days=1)
    return yDate


def getDatesForLoad(bDate, eDate):
    dates = []
    if bDate == None:
        dates.append(eDate)
    elif bDate == eDate:
        dates.append(eDate)
    else:
        d = bDate
        while True:
            if d == eDate:
                break
            dates.append(d)
            d = d + timedelta(days=1)
    return dates


# получение ключа аутентификации
def getAuthKey():    
    data = json.dumps({'jsonrpc':'2.0',
                       'method':'user.login',
                       'params':{'user':LOGIN,
                                 'password':PASSWORD
                                 },
                       'id':1,
                       'auth':None
                      })
    headers = {'content-type': 'application/json-rpc'}
    r = requests.post(ZABBIX, headers=headers, data=data)
    authKey = r.json()['result']
    return authKey


def getHistoryData(ch, datesForLoad, valuesList):
    itemid = ch['itemid']
    authKey = getAuthKey()
    data = json.dumps({'jsonrpc':'2.0',
                   'method':'history.get',
                   'params':{
                             'output':'extend',
                             'history':0,
                             'itemids':itemid,
                             'sortfield':'clock',
                             'sortorder':'DESC',
                             'limit':8000
                             },
                   'id':1,
                   'auth':authKey
                  })
    headers = {'content-type': 'application/json-rpc'}
    r = requests.post(ZABBIX, headers=headers, data=data)
    graphData = r.json()['result']
    trueItems = []
    for item in graphData:
        itemDate = datetime.fromtimestamp(int(item['clock']), tz=pytz.timezone('UTC')).date()
        if itemDate in datesForLoad:
            trueItems.append(item)
    for item in trueItems:
        d = {}
        itemDatetime = datetime.fromtimestamp(int(item['clock']), tz=pytz.timezone('UTC'))
        d['ts'] = itemDatetime.strftime('%Y-%m-%d %H:%M:%S')
        d['mer'] = itemDatetime.strftime('%p')
        d['speed'] = float(item['value'])
        d['channel'] = ch['channel']
        d['direction'] = ch['direction']
        values = '''
            (to_timestamp('%s','YYYY-MM-DD HH24:MI:SS'),
            '%s',
            %s,
            '%s',
            '%s')
        ''' % (d['ts'], d['mer'], d['speed'], d['channel'], d['direction'])
        valuesList.append(values.replace('\n',''))
    return valuesList


def dbWrite(query):
    db_con = psycopg2.connect(DB_REQ_BI_ECHD)
    cursor = db_con.cursor()
    cursor.execute(query)
    db_con.commit()
    db_con.close()


def runZabbixDataLoad():
    bDate = getBeginDate()
    eDate = getYesterdayDate()
    datesForLoad = getDatesForLoad(bDate, eDate)
    #
    valuesList = []
    valuesList = getHistoryData(ITEMS['in15.1989'], datesForLoad, valuesList)
    valuesList = getHistoryData(ITEMS['out15.1989'], datesForLoad, valuesList)
    valuesList = getHistoryData(ITEMS['in12.3827'], datesForLoad, valuesList)
    valuesList = getHistoryData(ITEMS['out12.3827'], datesForLoad, valuesList)
    #
    query = '''INSERT INTO echd.t_download_channels VALUES %s''' % ','.join(valuesList)
    dbWrite(query)
    #
    with open(BEGIN_DATE_FILEPATH, 'wt') as f:
        cDate = getTodayDate()
        f.write(cDate.strftime('%Y-%m-%d'))
        f.close()
