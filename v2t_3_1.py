import os
import sys
import json
import requests
import ftplib
from requests.auth import HTTPDigestAuth
from urllib3.exceptions import InsecureRequestWarning
import openai
from dotenv import load_dotenv
from fl_tools import get_flex_log_token,download_audio_file,fl_post_free_items
from isfax import is_fax

# 環境変数の読み込み
load_dotenv()
OPEN_API_KEY = os.environ["OPEN_API_KEY"]
LOCAL_FILE_DIR = os.environ["LOCAL_FILE_DIR"]
FTP_SERVER_URL = os.environ["FTP_SERVER_URL"]
FTP_USER_ID = os.environ["FTP_USER_ID"]
FTP_PASSWORD = os.environ["FTP_PASSWORD"]
REMOTE_FILE_DIR = os.environ["REMOTE_FILE_DIR"]
WAPI_POST_TRANSCRIPT = os.environ["WAPI_POST_TRANSCRIPT"]

openai.api_key = OPEN_API_KEY
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def detect_fax():
    found_freqs = is_fax("tempin.m4a")
    detected = 0
    for freq_range, found in found_freqs.items():
        if found:
            print(f"指定周波数帯域 {freq_range[0]}Hz ～ {freq_range[1]}Hz が存在します。 (FAX)")
            detected += 1
        #else:
        #    print(f"指定周波数帯域 {freq_range[0]}Hz ～ {freq_range[1]}Hz は存在しません。")

    if detected > 1 :
        return True
    else:
        return False


def transcribe_audio():
    try:
        if detect_fax():
            response = "FAX"
        else:
            with open("tempin.m4a", "rb") as file:
                params = {
                    "response_format": "vtt",
                    "temperature": 0, 
                    "language": "ja"
                }
                response = openai.Audio.transcribe("whisper-1", file, **params)
        return response
    except Exception as e:
        print(f"Error in audio transcription: {str(e)}")
        return None

def upload_to_ftp(vid, summary,src_text):
    sum_file_name = f"sum_{vid}.txt"
    remote_file_path = f'{REMOTE_FILE_DIR}/{sum_file_name}'
    local_file_path = os.path.join(LOCAL_FILE_DIR, sum_file_name)

    try:
        with open(local_file_path, 'w', encoding='cp932', errors='ignore') as file:
            file.write(summary)
            file.write("\n\n通話履歴:\n")
            file.write(src_text)
        
        ftp = ftplib.FTP(FTP_SERVER_URL)
        ftp.set_pasv(True)
        ftp.login(FTP_USER_ID, FTP_PASSWORD)
        with open(local_file_path, "rb") as file:
            ftp.storbinary(f"STOR {remote_file_path}", file)
        ftp.quit()
        print(f"Successfully uploaded {sum_file_name} to FTP.")
    except Exception as e:
        print(f"Error in FTP upload: {str(e)}")

def is_normal(call_history):
    #lines = call_history.strip().split('\n')
    #is_pattern1 = all("【電話の呼び出し音】" not in line for line in lines)
    #is_pattern2 = not lines[0].startswith("【電話の切れる音】")
    #is_pattern3 = not lines[0].startswith("終了です")

    #return is_pattern1 and is_pattern2 and is_pattern3
    #return is_pattern1
    return True

def summarize_text(src_text):
    #req_text = extract_text(src_text)
    if src_text == "FAX":
        return json.dumps({
            'category': "FAX",
            'customer_info': {'cname':"FAX", 'phone':""},
            'product_info': {'pname':"",'maker':"",'model':"",'model':""},
            'limit': "",
            'problem': "",
            'todo': "",
            'summary': []
        })

    try:
        if is_normal(src_text):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-1106",
                response_format={ "type": "json_object" },
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "中古農機具店での電話のやりとりです。次に示す項目ごとに効果的に要約してください。"
                            "出力は下記の項目だけを純粋な配列のJSON形式でお願いします。"
                            "{"
                                "category:(会話の全体内容を一言で表現してください),\n"
                                "customer_info:{cname:(顧客の名前),phone:(電話番号など),\n"
                                "product_info:{pname:(商品名),maker:(メーカ),model:(型式など)},\n"
                                "limit:(具体的な期日がある場合など),\n"
                                "ploblem:(問題点やクレームなど),\n"
                                "todo:(やるべきアクションなど),\n"
                                "summary:[(内容を箇条書きで要約)]\n"
                                
                            "}"
                        )
                    },
                    {
                        "role": "user",
                        "content": src_text
                    }
                ],
            )
            return response.choices[0].message.content.strip()
        else:
            #return "通話内容が不通もしくは無音です。"
            return json.dumps({
                'category': "通話内容が不通もしくは無音です。",
                'customer_info': {'cname':"不通/無音", 'phone':""},
                'product_info': {'pname':"",'maker':"",'model':"",'model':""},
                'limit': "",
                'problem': "",
                'todo': "",
                'summary': []
            })
    except Exception as e:
        print("Exception in text summarization:", str(e))
        return str(e) # エラーが発生した場合はエラーメッセージを要約とする

def convert_text(json_text):
    j = json.loads(json_text)
    converted_text = ""
    sum_txt = ""
    if j.get('summary'):
        for tx in j.get('summary'):
            sum_txt += tx+"\n" 
    customer_txt = ""
    customer_info = j.get('customer_info')
    if customer_info and customer_info.get('cname'):
        customer_txt += customer_info.get('cname')

    converted_text = (
        f"【カテゴリ】{j.get('category')}\n"
        f"【顧客名】{customer_txt}\n"
        f"【商品名】{j.get('product_info').get('pname')}\n"
        f"【メーカー】{j.get('product_info').get('maker')}\n"
        f"【型式】{j.get('product_info').get('model')}\n"
        f"【期日】{j.get('limit')}\n"
        f"【問題点】{j.get('problem')}\n"
        f"【TODO】{j.get('todo')}\n"
        f"【要点】{sum_txt}\n\n"
    )
    return converted_text

def fl_update_free_items(vid,token,json_text):
    j = json.loads(json_text)

    sum_txt = ""
    if j.get('summary'):
        for tx in j.get('summary')[0:2]:
            sum_txt += tx+"<br/>\n" 
        if len(j.get('summary')) > 2:
            sum_txt += "...<br/>\n"

    customer_txt = ""
    customer_info = j.get('customer_info')
    if customer_info and customer_info.get('cname'):
        customer_txt += customer_info.get('cname')

    etc_txt = ""
    pinfo = j.get('product_info')
    pname = pinfo.get('pname') if pinfo and pinfo.get('pname') else ""
    maker = pinfo.get('maker') if pinfo and pinfo.get('maker') else ""
    model = pinfo.get('model') if pinfo and pinfo.get('model') else ""
    #if pname or maker or model:
    #    etc_txt += f"【製品】{maker} {pname} {model}\n" 

    if j.get('limit') and j.get('limit') not in ["特になし","なし","不明"]:
        etc_txt += f"【期日】{j.get('limit')}<br/>\n"

    if j.get('problem') and j.get('problem') not in ["特になし","なし","不明"]:
        etc_txt += f"【問題点】{j.get('problem')}<br/>\n"

    if j.get('todo')  and j.get('todo') not in ["特になし","なし","不明"]:
        etc_txt += f"【TODO】{j.get('todo')}<br/>\n"

    items = ["","","","",""]
    items[0] = ""      #こちら側担当
    items[1] = customer_txt      #相手名
    items[2] = sum_txt      #内容
    items[3] = etc_txt      #仕切
    items[4] = j.get('category')  #カテゴリ

    fl_post_free_items(vid, token, items)

def process_call(vid, token):
    if download_audio_file(vid, token):
        src_text = transcribe_audio()
        if src_text:
            summary = summarize_text(src_text)
            fl_update_free_items(vid,token,summary)
            conv_text = convert_text(summary)
            #print(f'{summary}\n\n{conv_text}\n\n{src_text}')
            upload_to_ftp(vid, conv_text,src_text)
        else:
            print(f"No transcription available for VID {vid}.")
    else:
        print(f"Failed to process call for VID {vid}.")

def v2t_main(start_vid, end_vid):
    token = get_flex_log_token()
    for vid in range(start_vid, end_vid):
        process_call(vid, token)

# コマンドライン引数の処理
if __name__ == "__main__":
    if len(sys.argv) > 1:
        vids = sys.argv[1]
    else:
        vids = input('通話IDを入力してください[s-e]:')

    vids_l = vids.split('-')
    if len(vids_l) == 2:
        start_vid = int(vids_l[0])
        end_vid = int(vids_l[1]) + 1
    elif len(vids_l) == 1:
        start_vid = int(vids_l[0])
        end_vid = start_vid + 1
    else:
        print("無効な通話IDです。")
        sys.exit(1)

    v2t_main(start_vid, end_vid)
