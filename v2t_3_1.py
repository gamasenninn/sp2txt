import os
import sys
import requests
import ftplib
from requests.auth import HTTPDigestAuth
from urllib3.exceptions import InsecureRequestWarning
import openai
from dotenv import load_dotenv
from fl_tools import get_flex_log_token,download_audio_file

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

def transcribe_audio():
    try:
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
    lines = call_history.strip().split('\n')
    is_pattern1 = all("【電話の呼び出し音】" not in line for line in lines)
    is_pattern2 = not lines[0].startswith("【電話の切れる音】")
    is_pattern3 = not lines[0].startswith("終了です")

    return is_pattern1 and is_pattern2 and is_pattern3

def summarize_text(src_text):
    #req_text = extract_text(src_text)
    try:
        if is_normal(src_text):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": ("中古農機具店での電話のやりとりです。次に示す項目ごとに効果的に要約してください。"
                                    "【カテゴリー】(会話全体のカテゴリは?)\n" 
                                    "【スタッフ名】(スタッフの名前は?)" 
                                    "【顧客情報】（顧客の名前、会社名、役職、電話番号など）" 
                                    "【商品情報】(商品名、メーカ、型式など)" 
                                    "【期日】(期日的な内容は？)" 
                                    "【問題点】(クレームなど）"
                                    "【目的】(目的を短く）"
                                    "【次のアクション】(折り返し電話、メール送信、など）"
                                    "【内容】内容を短く箇条書きで要約?\n")
                    },
                    {
                        "role": "user",
                        "content": src_text
                    }
                ],
            )
            return response.choices[0].message.content.strip()
        else:
            return "通話内容が不通もしくは無音です。"
    except Exception as e:
        print("Exception in text summarization:", str(e))
        return str(e) # エラーが発生した場合はエラーメッセージを要約とする

def process_call(vid, token):
    if download_audio_file(vid, token):
        src_text = transcribe_audio()
        if src_text:
            summary = summarize_text(src_text)
            print(f'{summary}\n\n{src_text}')
            upload_to_ftp(vid, summary,src_text)
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
