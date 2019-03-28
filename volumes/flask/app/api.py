#-*- coding: utf-8 -*-

from app import app

import json
import random
import string
import requests
from datetime import datetime
from tzlocal import get_localzone
import pytz
import pika
import pymysql

from flask import Flask, jsonify, request, abort, make_response, json, redirect
from flask_httpauth import HTTPBasicAuth
from requests_ntlm import HttpNtlmAuth

requests.packages.urllib3.disable_warnings()


# константы
CERT = ('/certs/client.pem', '/certs/client_key.pem')
ROOT_CERT = '/certs/root.pem'
QS_IP = '192.168.0.1'


# генератор XRF
def setXrf():
    characters = string.ascii_letters + string.digits
    return ''.join(random.sample(characters, 16))


def getQlikUserAttributes(exUserid):
    conn = pymysql.connect(host='192.168.0.1', user='user', passwd='password', db='qlik', port=3306)
    cursor = conn.cursor()
    cursor._defer_warnings = True
    cursor.execute('''SELECT qlik_userid, concat(first_name, ' ',middle_name, ' ', last_name) 
                      FROM ex_match_users WHERE ex_userid = '%s';''' % exUserid)
    item = cursor.fetchall()
    conn.close()
    qlikUserid = item[0][0]
    userName = item[0][1]
    return qlikUserid, userName


# функция определения целевого виртуального прокси Qlik Sense
def getVProxy(qlikUserid):
    xrf = setXrf()
    headers = {'X-Qlik-Xrfkey': xrf,
               'X-Qlik-User'  : 'UserDirectory=internal;UserId=sa_repository',
               'content-type' : 'application/json'
              }
    url = 'https://{0}:4242/qrs/user/?Xrfkey={1}'.format(QS_IP, xrf)
    userItems = requests.get(url, headers=headers, verify=False, cert=CERT).json()
    error_code, vproxy = 1, None
    for userItem in userItems:
        if userItem['userId'].upper() == qlikUserid.upper():
            userid = userItem['id']
            url = 'https://{0}:4242/qrs/user/{1}?Xrfkey={2}'.format('10.200.81.105', userid, xrf)
            user = requests.get(url, headers=headers, verify=False, cert=CERT).json()
            print(user)
            error_code = 0
            if 'ContentAdmin' in user['roles']:
                vproxy = 'dev'
            else:
                vproxy = 'prod'
    return error_code, vproxy


# функция получения тикета
def getTicket(qlikUserid, vproxy):
    xrf = setXrf()
    headers = {'content-type'  : 'application/json',
               'X-Qlik-Xrfkey' : xrf
              }
    payload = {'UserDirectory' : 'example','UserId':qlikUserid}
    payload = json.dumps(payload)
    url = 'https://{0}:4243/qps/{1}/ticket?Xrfkey={2}'.format(QS_IP, vproxy, xrf)
    response = requests.post(url, data=payload, headers=headers, verify=False, cert=CERT)
    ticket = response.json().get('Ticket')
    return ticket


# функция генерации ссылки
def createUrl(qlikUserid):
    error_code, vproxy = getVProxy(qlikUserid)
    if error_code == 0:
        ticket = getTicket(qlikUserid, vproxy)
        url = 'http://{0}/{1}/hub/?qlikTicket={2}'.format(QS_IP, vproxy, ticket)
    else:
        ticket = ''
        url = ''
    return error_code, ticket, url


# функция отправки сообщения об авторизации пользователя в Qlik Sense|Nprinting
def logAuthEvent(destination='', exUserid='', qlikUserid='', nprUserid='', errorCode='', ticket='', userName=''):
    todayDatetime = datetime.today()
    localTimezone = get_localzone()
    localTodayDatetime = localTimezone.localize(todayDatetime)
    utcTodayDatetime = localTodayDatetime.astimezone(pytz.timezone('UTC'))
    payload = {
        'ts'          : utcTodayDatetime.strftime('%Y-%m-%d %H:%M:%S'),
        'destination' : destination, 
        'ex_userid' : exUserid,
        'qlik_userid' : qlikUserid,
        'npr_userid'  : nprUserid,
        'error_code'  : errorCode,
        'ticket'      : ticket,
        'userName'    : userName
    }
    body = json.dumps(payload)
    credentials = pika.PlainCredentials('example', 'mpassword')
    connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.0.1', 5672, '/example', credentials))
    channel = connection.channel()
    channel.basic_publish(exchange='example_exchange', routing_key='logins', body=body, properties=pika.BasicProperties(delivery_mode=2))
    connection.close()


# функция отправки сообщения об ошибке
def logError(resource, message):
    payload = {
        'ts'       :  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'resource' : '%s' % resource,
        'message'  : '%s' % message
    }
    body = json.dumps(payload)
    credentials = pika.PlainCredentials('example', 'mpassword')
    connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.0.1', 5672, '/example', credentials))
    channel = connection.channel()
    channel.basic_publish(exchange='example_exchange', routing_key='errors', body=body, properties=pika.BasicProperties(delivery_mode=2))
    connection.close()
    

# обработка Basic Auth
auth = HTTPBasicAuth()
@auth.get_password
def get_password(username):
    if username == 'username':
        return 'password'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error' : 'Unauthorized access'}), 401)


# REST API метод получения клиентом ссылки
@app.route('/get_qs_url', methods=['POST'])
@auth.login_required
def get_url():
    try:
        data = request.json
        exUserid = data['userid']
        qlikUserid, userName = getQlikUserAttributes(exUserid)
        errorCode, ticket, qsUrl = createUrl(qlikUserid)
        payload = {'userid'       : exUserid,
                   'error_code'   : errorCode,
                   'total_qs_url' : qsUrl
                  }
        logAuthEvent(destination='sense',
                     exUserid=exUserid,
                     qlikUserid=qlikUserid,
                     errorCode=errorCode,
                     ticket=ticket,
                     userName=userName)
        return jsonify(payload)
    except Exception as err:
        logError('flask:/get_qs_url', err)


# функция получения аттрибутов пользователя NPrinting
def getNprUserAttributes(qlikUseridShort):
    # Аутентификация в NPrinting
    auth = HttpNtlmAuth('VM\\nprinting','Mpassword')
    headers = {'content-type':'application/json'}
    url = '''http://192.168.0.1:4993/api/v1/login/ntlm'''
    response = requests.get(url, headers=headers, auth=auth)
    cookies = requests.utils.dict_from_cookiejar(response.cookies)
    token = cookies['NPWEBCONSOLE_XSRF-TOKEN']
    cookies = response.cookies
    #
    # Получение списка пользователей NPrinting
    headers = {'content-type':'application/json'}
    url = '''http://192.168.0.1:4993/api/v1/users'''
    response = requests.get(url, headers=headers, cookies=cookies)
    data = response.json()
    #
    nprUserid, userName = None, None
    for item in data['data']['items']:
        nprUserid = item['id']
        domainAccount = item['domainAccount']
        account = domainAccount.split('\\')[1]
        userName = item['userName']
        if account == qlikUseridShort:
            break
    return nprUserid, userName
        

# REST API метод аутентификации в NPriting
@app.route('/setnprintingcookie', methods=['GET'])
def setnprintingcookie():
    try:
        target = request.args.get('target')
        userparams = request.args.get('userparams')
        qlikUserid = userparams.split(';')[1].split('=')[1]
        qlikUseridShort = userparams.split(';')[1].split('=')[1].split('-')[0]
        nprUserid, userName = getNprUserAttributes(qlikUseridShort)
        #
        auth = HttpNtlmAuth('VM\\%s' % qlikUseridShort,'password')
        headers = {'content-type':'application/json'}
        #
        if target == 'console':
            url = "http://192.168.0.1:4993/api/v1/login/ntlm"
            authresponse = requests.get(url, headers=headers, auth=auth)
            cookies = requests.utils.dict_from_cookiejar(authresponse.cookies)
            session = cookies['NPWEBCONSOLE_SESSION']
            token = cookies['NPWEBCONSOLE_XSRF-TOKEN']
            #
            response = make_response(redirect('http:/192.168.0.1:4993'))
            response.set_cookie('NPWEBCONSOLE_SESSION', session)
            response.set_cookie('NPWEBCONSOLE_XSRF-TOKEN', token)
        elif target == 'newsstand':
            url = "http://192.168.0.1:4994/api/v1/login/ntlm"
            authresponse = requests.get(url, headers=headers, auth=auth)
            cookies = requests.utils.dict_from_cookiejar(authresponse.cookies)
            session = cookies['NPNEWSSTAND_SESSION']
            token = cookies['NPNEWSSTAND_XSRF-TOKEN']
            #
            response = make_response(redirect('192.168.0.1:4994'))
            response.set_cookie('NPNEWSSTAND_SESSION', session)
            response.set_cookie('NPNEWSSTAND_XSRF-TOKEN', token)   
        #
        logAuthEvent(destination=target,
                     qlikUserid=qlikUserid,
                     nprUserid=nprUserid,
                     userName=userName)
        #
        return response
    except Exception as err:
        logError('flask:/setnptintingcookie', err)
