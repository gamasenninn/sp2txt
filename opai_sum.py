import openai
import sys
import csv
import os
from dotenv import load_dotenv
import ftplib
import time

# OpenAI APIキーを設定
load_dotenv()
openai.api_key = os.environ["OPEN_API_KEY"] 

# 要約するテキストを指定
text = ''
# モードの選択　chatGPTかそれ以外か

# SP2TXTが存在するディレクトリ
file_dir = os.environ["LOCAL_FILE_DIR"]

def summarize_text(text):
    print("selected chatGPT")
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
#                    {
#                        "role": "system",
#                        "content": "電話のやりとりを項目ごとに要約してください。以下の情報を含めてください。" 
#                                   "1. 電話をかけた相手の情報(名前、会社名、役職など)" 
#                                   "2. 会話の目的・内容" 
#                                   "3. 次のステップ・アクションアイテム（電話の予定、メールの送信、手紙の書き方など）" 
#                                   "4. その他重要な情報（緊急性がある情報、注目すべき詳細、特定の資料など）" 
#                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
        )

    # 要約されたテキストを取得
    summary = response.choices[0].message.content.strip()
    return summary

def read_text(file_path):
    src_text = ''
    with open(file_path, newline='', encoding='cp932') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            #print(row[0],row[4])
            src_text +=  f"{row[0]}: {row[4]}\n"
    print(src_text)
    return src_text

def write_sum_text(file_path,text):
    src_text = ''
    with open(file_path,  'w' ,encoding='cp932') as wf:
        wf.write(text)

def upload_to_server(file_name):
    # FTPサーバーに接続する
    ftp_url = os.environ["FTP_SERVER_URL"]
    ftp_user_id = os.environ["FTP_USER_ID"]
    ftp_pass = os.environ["FTP_PASSWORD"]
    remote_file_path = f'{os.environ["REMOTE_FILE_DIR"]}/{file_name}'
    local_file_path = os.path.join(os.environ["LOCAL_FILE_DIR"],file_name)

    ftp = ftplib.FTP(ftp_url)
    ftp.set_pasv('true')
    ftp.login(ftp_user_id, ftp_pass)

    #ftp.cwd(f'{os.environ["REMOTE_FILE_DIR"]}')
    #files = ftp.nlst()
    #print("files:",files)

    ## バイナリモードでファイルを開く
    #print("remote_file:",remote_file_path)
    with open(local_file_path, "rb") as file:
        # FTPサーバーにファイルをアップロードする
        #print("uploding......")
        ftp.storbinary(f"STOR {remote_file_path}", file)

    ftp.quit()    



if __name__ == "__main__":


    if len(sys.argv) > 1 :       
        file_path = os.path.join(file_dir,f"txt_{sys.argv[1]}.csv")
        src_text = read_text(file_path)
        sum_text = summarize_text(src_text)
        print(sum_text)
    else:
        while True:
            fid_range = input("\nパラメータ=文書番号を指定してください")
            start ,end = fid_range.split("-")
            num_list =  list(range(int(start), int(end)+1))
            for fid in num_list: 
                file_name = f"txt_{fid}.csv"
                file_path = os.path.join(file_dir,file_name)
                src_text = read_text(file_path)
                sum_text = summarize_text(src_text)
                print(sum_text)
                sum_file_name = f"sum_{fid}.txt"
                wfile_path = os.path.join(file_dir,sum_file_name)
                write_sum_text(wfile_path,sum_text)    
                upload_to_server(sum_file_name)
                time.sleep(15)
        


    
