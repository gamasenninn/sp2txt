import json
import requests
from requests.auth import HTTPDigestAuth
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import os
import sys
from pydub import AudioSegment
from pydub.silence import split_on_silence,detect_silence,detect_nonsilent
import csv
# open ai 対応
import openai
from dotenv import load_dotenv
import ftplib
import re

load_dotenv()
#----------　OPEN AI　APIを使用するための前処理 ------
openai.api_key = os.environ["OPEN_API_KEY"] 

# 要約するテキストを指定
#text = ''
# モードの選択　chatGPTかそれ以外か

# SP2TXTが存在するディレクトリ
file_dir = os.environ["LOCAL_FILE_DIR"]

#-------------- requestのワーニングを非表示にする-----

urllib3.disable_warnings(InsecureRequestWarning)

#-------------FLEX LOG ユーザ設定--------------

u = os.environ["FL_USER_ID"]
p = os.environ["FL_PASSWORD"]

#--------------FLEXLOG アクセストークン取得--------------
flex_log_token_url = os.environ["FLEX_LOG_TOKEN_URL"]
flex_log_request_token = os.environ["FLEX_LOG_REQUEST_TOKEN"]

headers = {
'Content-Type':'application/x-www-form-urlencoded',
'Request-token': flex_log_request_token
}

data = "company_id=0&service_name=calllog"


r = requests.post(flex_log_token_url,auth=HTTPDigestAuth(u,p),headers=headers,data=data, verify=False )

jdic = json.loads(r.text)
token = jdic[0]['access_token']

#print(token)

def extract_text(input_string):
    # タイムスタンプのパターンを定義
    pattern = r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\n'
    
    # タイムスタンプを削除
    text_only = re.sub(pattern, '', input_string)
    
    # 連続した改行を1つの改行に置き換え
    single_line_breaks = re.sub(r'\n{2,}', '\n', text_only)
    
    return single_line_breaks.strip()


while True:

    if len(sys.argv) > 1 :
        vids = sys.argv[1]
    else:
        vids =input('通話IDを入力してください[s-e]:')

    vids_l = vids.split('-')
    if len(vids_l) == 2 :
        start_vid = int(vids_l[0])
        end_vid = int(vids_l[1])+1
        break
    elif len(vids_l) == 1: 
        start_vid = int(vids_l[0])
        end_vid = start_vid + 1
        break
    else:
        pass

flex_log_api_base_url = os.environ["FLEX_LOG_API_BASE_URL"]
for vid in range(start_vid,end_vid):

    vid = str(vid)
    URL_VOICE = flex_log_api_base_url+vid+'/calllog/audio'

    headers = {
        'Access-token': token
    }

    params = {
        'encbase64': 0
    }

    r = requests.get(URL_VOICE,params=params,auth=HTTPDigestAuth(u,p),headers=headers,verify=False)

    with open("tempin.m4a",'wb') as fout:
        fout.write(r.content)

    #--------------文字起こし--------------
    src_text = ""
    with open("tempin.m4a", "rb") as file:
        params ={
            "response_format" : "vtt",
            "temperature" : 0, 
            "language" : "ja",
            "prompt":""
        }

        src_text = openai.Audio.transcribe("whisper-1", file,**params)
        print(src_text)

    #---- 記事の要約 -------
    if src_text:
        req_text = extract_text(src_text)
        try:
            response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system",
                                "content": "中古農機具店での電話のやりとりです。次に示す項目ごとに効果的に要約してください。" 
                                        "【カテゴリー】(会話全体のカテゴリは?)\n" 
                                        "【スタッフ名】(スタッフの名前は?)" 
                                        "【顧客情報】（顧客の名前、会社名、役職、電話番号など）" 
                                        "【商品情報】(商品名、メーカ、型式など)" 
                                        "【期日】(期日的な内容は？)" 
                                        "【問題点】(クレームなど）"
                                        "【目的】(目的を短く）"
                                        "【次のアクション】(折り返し電話、メール送信、など）"
                                        "【内容】内容を短く箇条書きで要約?\n" 
                            },
                            {
                                "role": "user",
                                "content": req_text
                            }
                        ],
            )
            summary = response.choices[0].message.content.strip()
        except Exception as e:
            print("exception:",str(e))
            summary = str(e) #エラーならその旨をテキストにする

        ftp_url = os.environ["FTP_SERVER_URL"]
        ftp_user_id = os.environ["FTP_USER_ID"]
        ftp_pass = os.environ["FTP_PASSWORD"]
        sum_file_name = f"sum_{vid}.txt"
        remote_file_path = f'{os.environ["REMOTE_FILE_DIR"]}/{sum_file_name}'
        local_file_path = os.path.join(os.environ["LOCAL_FILE_DIR"],sum_file_name)

        print("sum_text:",summary)
        with open(local_file_path,  'w' ,encoding='cp932',errors='ignore') as wf:
            wf.write(summary)
            wf.write("\n\n通話履歴:\n")
            wf.write(src_text)

        ftp = ftplib.FTP(ftp_url)
        ftp.set_pasv('true')
        ftp.login(ftp_user_id, ftp_pass)

        with open(local_file_path, "rb") as file:
            ftp.storbinary(f"STOR {remote_file_path}", file)

        ftp.quit()    

    #------- Web API コール　----------
    # 通話履歴は空のデータ　終了分をチェックするため
    header = ['CH','S-NS','START','END','TEXT']    
    with open('temp/txt_'+str(vid)+'.csv','w',newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
    #------- Web API コール　----------
    post_url = os.environ["WAPI_POST_TRANSCRIPT"]
    headers = {
    'Content-Type':'application/x-www-form-urlencoded',
    }
    data = "vid="+str(vid)+"&memo="+json.dumps([])

    r = requests.post(post_url,data=data, headers=headers,verify=False )
