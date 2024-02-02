#! /usr/bin/env python3
import http
import json
import os
import requests
import socket
import urllib3


STATUSPAGE_API_KEY = os.environ.get('STATUSPAGE_APIKEY', '')
LOCATION_POSTING_API_KEY=os.environ.get('LOCATION_POSTING_API_KEY', '')
PAGE_ID = 'j9njnl3qx7d8'

socket.setdefaulttimeout(3)


def update_status(page_id, component_id, status):
    url = f'https://api.statuspage.io/v1/pages/{page_id}/components/{component_id}/?api_key={STATUSPAGE_API_KEY}'
    r = requests.patch(
        url,
        data=json.dumps({"component":{"status": status}})
    )


def check_queclink_tcp_server():
    location = ('routechoices.com', 2002)
    heartbeat_data = b"+ACK:GTHBD,C30203,860201061588748,,20230202181922,FFFF$"
    ack_data_expected = b"+SACK:GTHBD,C30203,FFFF$"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(location)
            s.sendall(heartbeat_data)
            ack_data = s.recv(1024)
            check = ack_data == ack_data_expected
        except:
            check = False
    return check


def check_teltonika_tcp_server():
    location = ('routechoices.com', 2000)
    conn_data = bytes.fromhex('000f333536333037303432343431303133')
    ack_data_expected = b"\x01"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(location)
            s.sendall(conn_data)
            ack_data = s.recv(1024)
            check = ack_data == ack_data_expected
        except Exception as e:
            check = False
    return check


def check_frontend_server():
    try :
        r = requests.get('https://www.routechoices.com/events', timeout=5)
    except (http.client.HTTPException, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
        return False
    else:
        return r.status_code == 200


def check_wms_server():
    try :
        r = requests.get(
            "https://wms.routechoices.com/?service=WMS&request=GetMap&layers=fhDbzlQSLho&styles=&format=image%2Fjpeg&transparent=false&version=1.1.1&width=512&height=512&srs=EPSG%3A3857&bbox=2641663.6975356913,8727274.141488286,2661231.576776697,8746842.020729292",
            timeout=5
        )
    except (http.client.HTTPException, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
        return False
    else:
        return r.status_code == 200


def check_phone_api():
    r = None
    try:
        r = requests.post(
            'https://api.routechoices.com/locations',
            data={
                "device_id": "71588519",
                "longitudes": "",
                "latitudes": "",
                "timestamps": ""
            },
            headers={
                "Authorization": f"Bearer {LOCATION_POSTING_API_KEY}"
            }
        )
    except (http.client.HTTPException, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
        return False
    else:
        return r.status_code == 201


def check_api():
    r = None
    try :
        r = requests.get('https://api.routechoices.com/time/')
    except (http.client.HTTPException, urllib3.exceptions.MaxRetryError, requests.exceptions.ConnectionError):
        return False
    else:
        return r.status_code == 200


def update_phone_api_status():
    component_id = 'ltkggcnccgwr'
    if check_phone_api():
        print("Phone API works")
        update_status(PAGE_ID, component_id, 'operational')
        return True
    else:
        print("Phone API down")
        update_status(PAGE_ID, component_id, 'major_outage')
        return False


def update_api_status():
    component_id = 'tqwvqj1jzq1x'
    if check_api():
        print("API server is running")
        update_status(PAGE_ID, component_id, 'operational')
        return True
    else:
        print("API server is not accessible")
        update_status(PAGE_ID, component_id, 'major_outage')
        return False


def update_tcp_server_status():
    check = all([
        check_queclink_tcp_server,
        check_teltonika_tcp_server,
    ])
    component_id = '1v1vrvkcf0h7'
    if check:
        print("TCP server is running")
        update_status(PAGE_ID, component_id, 'operational')
        return True
    else:
        print("TCP server is not accessible")
        update_status(PAGE_ID, component_id, 'major_outage')
        return False


def update_frontend_status():
    component_id = '8f1yqmjd83w8'
    if check_frontend_server():
        print("Frontend server is accessible")
        update_status(PAGE_ID, component_id, 'operational')
        return True
    else:
        print("Frontend server is not accessible")
        update_status(PAGE_ID, component_id, 'major_outage')
        return False


def update_wms_server_status():
    component_id = '3wy38sslv3r0'
    if check_wms_server():
        print("WMS server is running")
        update_status(PAGE_ID, component_id, 'operational')
        return True
    else:
        print("WMS server is not accessible")
        update_status(PAGE_ID, component_id, 'major_outage')
        return False


if __name__ == '__main__':
    api_status = update_api_status()
    frontend_status = update_frontend_status()
    phone_api_status = update_phone_api_status()
    tcp_server_status = update_tcp_server_status()
    wms_server_status = update_wms_server_status()
    if all([
        api_status,
        frontend_status,
        phone_api_status,
        tcp_server_status,
        wms_server_status,
    ]):
        print("\033[92mAll systems operational\033[00m")
    elif any([
        api_status,
        frontend_status,
        phone_api_status,
        tcp_server_status,
        wms_server_status,
    ]):
        print("\033[93mPartial outage\033[00m")
    else:
        print("\033[91mAll systems down\033[00m")
