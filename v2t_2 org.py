import json
import requests
from requests.auth import HTTPDigestAuth
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import os
import sys
#import pydub
from pydub import AudioSegment
from pydub.silence import split_on_silence,detect_silence,detect_nonsilent
import speech_recognition as sr
import subprocess
import glob
import csv
# open ai 対応
import openai
from dotenv import load_dotenv
import ftplib

load_dotenv()
#----------　OPEN AI　APIを使用するための前処理 ------
openai.api_key = os.environ["OPEN_API_KEY"] 

# 要約するテキストを指定
text = ''
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

    sound = AudioSegment.from_file("tempin.m4a",format="m4a")
    up_sound = sound + 10
    up_sound.export('tempout.wav',format="wav")

    subprocess.run("stereo_split.bat")

    #--------------文字お越し--------------

    chs = ["L","R"]
    min_silence_len = 2000

    for file in glob.glob('temp/temp_NS_*.wav'):
        os.remove(file)

    print ("\n#######<"+vid+">#############")

    all_ranges = []
    sound ={}
    for ch in chs:
        sound = AudioSegment.from_file("tempout_"+ch+".wav", format="wav")

        print ("----Detect NonSilent---",ch)
        nonsilent_ranges = detect_nonsilent(sound, min_silence_len=min_silence_len, silence_thresh=-40)
        for l in nonsilent_ranges:
            l.insert(0,ch)
            l.insert(1,'N')
            sound[l[2]:l[3]+500].export("temp\\temp_NS_"+str(l[2])+".wav",format='wav')
        #print("nonsilent_ranges:",nonsilent_ranges)

        print ("----Detect Silent---",ch)
        silent_ranges = detect_silence(sound, min_silence_len=min_silence_len, silence_thresh=-40)
        for l in silent_ranges:
            l.insert(0,ch)
            l.insert(1,'S')
            l.insert(4,'')
        #print("silent_ranges:",silent_ranges)

        all_ranges += silent_ranges+nonsilent_ranges
        #print(all_ranges)
        

    srt_all_ranges = sorted(all_ranges,key=lambda x: x[2])
    #print(srt_all_ranges)


    r = sr.Recognizer()
    for voice_l in srt_all_ranges:
        if voice_l[1] == 'N':
            with sr.AudioFile("temp\\temp_NS_" + str(voice_l[2]) +".wav") as source:
                audio = r.record(source)
            try: 
                text = r.recognize_google(audio, language='ja-JP')
            except:
                text = ''
                pass
            voice_l.insert(4,text)
            #print('[',voice_l[0],voice_l[2],']',text)
            print(voice_l)


    header = ['CH','S-NS','START','END','TEXT']    
    with open('temp/txt_'+str(vid)+'.csv','w',newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i in srt_all_ranges:
            if i[4] != '':
                i[4] = i[4].replace('&','＆')
                writer.writerow(i)

    #---- 記事の要約 -------
    src_text = '' 
    for i in srt_all_ranges:
        if i[4] != '':
            i[4] = i[4].replace('&','＆')
            src_text +=  f"{i[0]}: {i[4]}\n"
    #print("src_text:",src_text)
    if src_text:
        try:
            response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system",
                                "content": "電話でのやりとりです。次に示す項目ごとに効果的に要約してください。" 
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
                                "content": src_text
                            }
                        ],
            )
            summary = response.choices[0].message.content.strip()
        except Exception as e:
            print("exception:",e)
            summary = e #エラーならその旨をテキストにする

        ftp_url = os.environ["FTP_SERVER_URL"]
        ftp_user_id = os.environ["FTP_USER_ID"]
        ftp_pass = os.environ["FTP_PASSWORD"]
        sum_file_name = f"sum_{vid}.txt"
        remote_file_path = f'{os.environ["REMOTE_FILE_DIR"]}/{sum_file_name}'
        local_file_path = os.path.join(os.environ["LOCAL_FILE_DIR"],sum_file_name)

        print("sum_text:",summary)
        with open(local_file_path,  'w' ,encoding='cp932') as wf:
            wf.write(summary)

        ftp = ftplib.FTP(ftp_url)
        ftp.set_pasv('true')
        ftp.login(ftp_user_id, ftp_pass)

        with open(local_file_path, "rb") as file:
            ftp.storbinary(f"STOR {remote_file_path}", file)

        ftp.quit()    

    #------- Web API コール　----------
    post_url = os.environ["WAPI_POST_TRANSCRIPT"]
    headers = {
    'Content-Type':'application/x-www-form-urlencoded',
    }
    data = "vid="+str(vid)+"&memo="+json.dumps(srt_all_ranges)

    r = requests.post(post_url,data=data, headers=headers,verify=False )

    print(r)

