import subprocess
import glob
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import time
import os
from dotenv import load_dotenv


#環境変数設定
load_dotenv()
WAPI_GET_ITEM = os.environ['WAPI_GET_ITEM'] 
LOCAL_FILE_DIR = os.environ['LOCAL_FILE_DIR']
wait_time = 300

#ワーニング抑制
urllib3.disable_warnings(InsecureRequestWarning)

while True:

    #------- 現在起こし済のリスト-------
    f_txt_l = glob.glob(f'{LOCAL_FILE_DIR}/sum_*.txt')
    vids = [os.path.splitext(os.path.basename(f_txt))[0][4:] for f_txt in f_txt_l]
        
    #------- 発生したデータリスト-------
    r = requests.get(WAPI_GET_ITEM,verify=False )
    json_l = r.json()
    vid2s = [j['uniqueid'] for j in json_l]
    #print(vid2s)

    #------ 集合演算 vid2s - vids　------
    diff_vids = sorted(set(vid2s) - set(vids))
    print('----- 差分 ------')
    print(diff_vids)

    for vid in diff_vids:
        if not os.path.exists(f'{LOCAL_FILE_DIR}/sum_{vid}.txt'):
            subprocess.run(['python', 'v2t_3.py', vid])
        else:
            print(f'存在するから、スキップすわ！')

    # 5分待機する
    time.sleep(wait_time)
