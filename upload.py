import os
import ftplib
from dotenv import load_dotenv

FTP_SERVER_URL = os.environ["FTP_SERVER_URL"]
FTP_USER_ID = os.environ["FTP_USER_ID"]
FTP_PASSWORD = os.environ["FTP_PASSWORD"]
LOCAL_FILE_DIR = os.environ["LOCAL_FILE_DIR"]
REMOTE_FILE_DIR = os.environ["REMOTE_FILE_DIR"]

# 環境変数の読み込み
load_dotenv()

def upload_init(vid):
    # この処理は最初にサマリーテキストのファイルだけ作っておく
    # 並列に走らせるとき、まずファイルをリザーブするために利用する
    #
    sum_file_name = f"sum_{vid}.txt"
    local_file_path = os.path.join(LOCAL_FILE_DIR, sum_file_name)
    try:
        with open(local_file_path, 'w', encoding='cp932', errors='ignore') as file:
            file.write("処理中")
    except Exception as e:
        print(f"Error file write !!: {str(e)}")
        return False
    return True

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
        return True
    except Exception as e:
        print(f"Error in FTP upload: {str(e)}")
        return False
