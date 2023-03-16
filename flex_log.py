import json
import requests
from requests.auth import HTTPDigestAuth
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import os
from dotenv import load_dotenv
import urllib.parse

#-------------- requestのワーニングを非表示にする-----
urllib3.disable_warnings(InsecureRequestWarning)

#----------　OPEN AI　APIを使用するための前処理 ------
load_dotenv()

#----- 各種関数 -------
def get_fl_token():
    u = os.getenv("FL_USER_ID")
    p = os.getenv("FL_PASSWORD")
    url = os.getenv("FLEX_LOG_TOKEN_URL")
    request_token = os.getenv("FLEX_LOG_REQUEST_TOKEN")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Request-token": request_token,
    }

    data = {"company_id": 0, "service_name": "calllog"}

    response = requests.post(
        url, auth=HTTPDigestAuth(u, p), headers=headers, data=data, verify=False
    )
    access_token = response.json()[0]["access_token"]
    return access_token

def put_item_category(token, vid, categ):
    u = os.environ["FL_USER_ID"]
    p = os.environ["FL_PASSWORD"]
    url = os.environ['FLEX_LOG_API_BASE_URL'] + f'{vid}/calllog/freeitem'

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Access-token': token
    }

    data = urllib.parse.urlencode({'free_item_05': categ})

    r = requests.post(url, auth=HTTPDigestAuth(u, p), data=data, headers=headers, verify=False)

    return r

def get_free_data(token,vid):
    u = os.environ["FL_USER_ID"]
    p = os.environ["FL_PASSWORD"]
    url = os.environ['FLEX_LOG_API_BASE_URL'] + f'calllog/?uniqueid={vid}'

    headers = {
        'Access-token': token
    }
    params = {
        'encbase64': 0
    }
    r = requests.get(url,params=params,auth=HTTPDigestAuth(u,p),headers=headers,verify=False)

    return  json.loads(r.text)

#------- ここから　----------
if __name__ == '__main__':

    token = get_fl_token()

    vid =input('通話IDを入力してください:')

    fl_data = get_free_data(token,vid)
    print("free_item01:",fl_data[0]["free_item_01"])
    print("free_item02:",fl_data[0]["free_item_02"])
    print("free_item03:",fl_data[0]["free_item_03"])
    print("free_item04:",fl_data[0]["free_item_04"])
    print("free_item05:",fl_data[0]["free_item_05"])

    categ =input('カテゴリー:')
    r = put_item_category(token,vid,categ)
    print(r)