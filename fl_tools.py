import os
import json
import requests
from requests.auth import HTTPDigestAuth
from urllib3.exceptions import InsecureRequestWarning
from dotenv import load_dotenv

#-------------- requestのワーニングを非表示にする-----
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# 環境変数の読み込み
load_dotenv()
OPEN_API_KEY = os.environ["OPEN_API_KEY"]
LOCAL_FILE_DIR = os.environ["LOCAL_FILE_DIR"]
FL_USER_ID = os.environ["FL_USER_ID"]
FL_PASSWORD = os.environ["FL_PASSWORD"]
FLEX_LOG_TOKEN_URL = os.environ["FLEX_LOG_TOKEN_URL"]
FLEX_LOG_REQUEST_TOKEN = os.environ["FLEX_LOG_REQUEST_TOKEN"]
FLEX_LOG_API_BASE_URL = os.environ["FLEX_LOG_API_BASE_URL"]
FTP_SERVER_URL = os.environ["FTP_SERVER_URL"]
FTP_USER_ID = os.environ["FTP_USER_ID"]
FTP_PASSWORD = os.environ["FTP_PASSWORD"]
REMOTE_FILE_DIR = os.environ["REMOTE_FILE_DIR"]
WAPI_POST_TRANSCRIPT = os.environ["WAPI_POST_TRANSCRIPT"]


# 各種機能を関数化
def get_flex_log_token():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Request-token': FLEX_LOG_REQUEST_TOKEN
    }
    data = "company_id=0&service_name=calllog"
    response = requests.post(FLEX_LOG_TOKEN_URL, auth=HTTPDigestAuth(FL_USER_ID, FL_PASSWORD), headers=headers, data=data, verify=False)
    return json.loads(response.text)[0]['access_token']

def download_audio_file(vid, token):
    URL_VOICE = FLEX_LOG_API_BASE_URL + str(vid) + '/calllog/audio'
    headers = {'Access-token': token}
    params = {'encbase64': 0}
    response = requests.get(URL_VOICE, params=params, auth=HTTPDigestAuth(FL_USER_ID, FL_PASSWORD), headers=headers, verify=False)
    
    if response.status_code == 200:
        with open("tempin.m4a", 'wb') as file:
            file.write(response.content)
        return True
    else:
        print(f"Error downloading audio file for VID {vid}: {response.status_code}")
        return False

def fl_get_items(vid, token ):
    if vid:
        params = f"?uniqueid={vid}"
    else:
        params = f"?limit=100"

    url_items = FLEX_LOG_API_BASE_URL + '/calllog/'+params
    headers = {'Access-token': token}

    response = requests.get(url_items, auth=HTTPDigestAuth(FL_USER_ID, FL_PASSWORD), headers=headers, verify=False)
    
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Error get items for VID {vid}: {response.status_code}")
        return False


def fl_post_free_items(vid, token, items):
    url_free_item = FLEX_LOG_API_BASE_URL + str(vid) + '/calllog/freeitem'
    headers = {'Access-token': token}
    params = {
        'free_item_01': items[0],
        'free_item_02': items[1],
        'free_item_03': items[2],
        'free_item_04': items[3],
        'free_item_05': items[4]
    }
    response = requests.post(url_free_item, auth=HTTPDigestAuth(FL_USER_ID, FL_PASSWORD), headers=headers, data=params, verify=False)
    #print(response)
    
    if response.status_code == 200:
        return True
    else:
        print(f"Error put item, VID {vid}: {response.status_code}")
        return False

if __name__ == "__main__":

    # test用メイン
    vid = 46953

    token = get_flex_log_token()
    print(token)

    download_audio_file(vid, token)

    items=[
        "test01",
        "test02",
        "test03",
        "test04",
        "test05"
    ]
    fl_post_free_items(vid, token, items)

    items = fl_get_items(vid, token)
    for item in items:
        print(item)

    items = fl_get_items(0, token)
    for i, item in enumerate(items):
        print(i, item)
