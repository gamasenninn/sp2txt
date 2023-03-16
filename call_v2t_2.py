import subprocess
import glob
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import time
import os
from dotenv import load_dotenv

#-------------- requestのワーニングを非表示にする-----
urllib3.disable_warnings(InsecureRequestWarning)

#----------　WEB APIのアドレス ------
load_dotenv()
WAPI_GET_ITEM = os.environ['WAPI_GET_ITEM'] 

while True:

    #------- 現在起こし済のリスト-------
    f_txt_l = glob.glob('temp/txt_*.csv')
    vids = [os.path.splitext(os.path.basename(f_txt))[0][4:] for f_txt in f_txt_l]
        
    #------- 発生したデータリスト-------
    r = requests.get(WAPI_GET_ITEM,verify=False )
    json_l = r.json()
    vid2s = [j['uniqueid'] for j in json_l]

    #------ 集合演算 vid2s - vids　------
    diff_vids = sorted(set(vid2s) - set(vids))
    print('----- 差分 ------')
    print(diff_vids)

    for vid in diff_vids:
        if not os.path.exists(f'temp/txt_{vid}.csv'):
            subprocess.run(['python', 'v2t_2.py', vid])
        else:
            print(f'txt_{vid}.csvはもう存在するから、スキップするわ！')

    # 5分待機する
    time.sleep(300)
