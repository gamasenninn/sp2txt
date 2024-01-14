import os
import sys
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
import openai
from dotenv import load_dotenv
from fl_tools import get_flex_log_token,download_audio_file,fl_post_free_items
from isfax import classify_audio_type
from upload import upload_to_ftp
from replace_word import load_conversion_dict,replace_text

# 環境変数の読み込み
load_dotenv()
OPEN_API_KEY = os.environ["OPEN_API_KEY"]
TEMP_FILE = "tempin.m4a"
REPLACE_DICT = "replace.dic" 
# メッセージのテンプレート
MESSAGE_TEMPLATE = """
{keyword}次に示す項目ごとに効果的に要約してください。
出力は下記の項目だけを純粋な配列のJSON形式でお願いします。
{{
    'category':(会話の全体内容を一言で表現してください),
    'customer_info':{{'cname':(顧客の名前),'phone':(電話番号など)}},
    'product_info':{{'pname':(商品名),'maker':(メーカ),'model':(型式など)}},
    'limit':(具体的な期日がある場合など),
    'problem':(問題点やクレームなど),
    'todo':(やるべきアクションなど),
    'summary':[(内容を箇条書きで要約)]
}}
"""

openai.api_key = OPEN_API_KEY

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

replace_dict = load_conversion_dict(REPLACE_DICT)

def transcribe_audio():
    try:
        sound_type = classify_audio_type(TEMP_FILE)
        if not sound_type == "NORMAL":
            print("detected:",sound_type)
            return sound_type
        else:
            with open(TEMP_FILE, "rb") as file:
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

def create_json_response(category, cname, 
        phone="", pname="", maker="", model="", 
        limit="", problem="", todo="", summary=[]):
    return json.dumps({
        'category': category,
        'customer_info': {'cname': cname, 'phone': phone},
        'product_info': {'pname': pname, 'maker': maker, 'model': model},
        'limit': limit,
        'problem': problem,
        'todo': todo,
        'summary': summary
    })

def summarize_text(src_text):
    #req_text = extract_text(src_text)
    if src_text == "FAX":
        return create_json_response("FAX", "FAX")

    if src_text == "CALL_ONLY":
        return create_json_response("不通/不達", "不通")

    try:
        keyword = "中古農機具店での電話のやりとりです。"
        system_message_content = MESSAGE_TEMPLATE.format(keyword=keyword)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            response_format={ "type": "json_object" },
            messages=[
                {
                    "role": "system",
                    "content": system_message_content
                },
                {
                    "role": "user",
                    "content": src_text
                }
            ],
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Exception in text summarization:", str(e))
        return str(e) # エラーが発生した場合はエラーメッセージを要約とする

def get_text_or_empty(source, key):
    """ キーに対応するテキストを取得するか、空の文字列を返す """
    return source.get(key, "")

def convert_text(json_text):
    j = json.loads(json_text)
    
    # 顧客情報のテキストを生成
    customer_info = j.get('customer_info', {})
    customer_txt = get_text_or_empty(customer_info, 'cname')
    
    # 商品情報のテキストを生成
    product_info = j.get('product_info', {})
    product_txt = "\n".join([f"【商品名】{get_text_or_empty(product_info, 'pname')}",
                             f"【メーカー】{get_text_or_empty(product_info, 'maker')}",
                             f"【型式】{get_text_or_empty(product_info, 'model')}"])

    # 要点のテキストを生成
    summary_txt = "\n".join(j.get('summary', []))

    # 最終的なテキストを組み立て
    converted_text = (
        f"【カテゴリ】{get_text_or_empty(j, 'category')}\n"
        f"【顧客名】{customer_txt}\n"
        f"{product_txt}\n"
        f"【期日】{get_text_or_empty(j, 'limit')}\n"
        f"【問題点】{get_text_or_empty(j, 'problem')}\n"
        f"【TODO】{get_text_or_empty(j, 'todo')}\n"
        f"【要点】{summary_txt}\n\n"
    )
    return converted_text


def add_text_if_present(j, key, label):
    if j.get(key) and j.get(key) not in ["特になし", "なし", "不明"]:
        return f"【{label}】{j.get(key)}<br/>\n"
    return ""

def join_summary_text(summary_list):
    """ 要約のテキストを結合する。最初の2要素のみ表示し、それ以上ある場合は'...'を追加 """
    summary_text = "<br/>\n".join(summary_list[:2])
    if len(summary_list) > 2:
        summary_text += "<br/>\n..."
    return summary_text

def fl_update_free_items(vid,token,json_text):

    j = json.loads(json_text)   

    sum_txt = join_summary_text(j.get('summary', []))
    customer_info = j.get('customer_info', {})
    customer_txt = get_text_or_empty(customer_info, 'cname')

    #etc_txt = ""
    etc_txt = add_text_if_present(j, 'limit', '期日')
    etc_txt += add_text_if_present(j, 'problem', '問題点')
    etc_txt += add_text_if_present(j, 'todo', 'TODO')

    items = [
        "",                    # こちら側担当者の名前 (現在は空)
        customer_txt,          # 顧客名
        sum_txt,               # トランザクションの内容
        etc_txt,               # 追加情報または注記
        j.get('category', "")  # カテゴリ
    ]

    if fl_post_free_items(vid, token, items):
        print(f"Successfully updated flexlog : {vid}")
    else:
        print(f"Update error flexlog : {vid}")


def process_call(vid, token):
    if download_audio_file(vid, token):
        src_text = transcribe_audio()
        if src_text:
            src_text = replace_text(src_text,replace_dict)
            summary = summarize_text(src_text)
            fl_update_free_items(vid,token,summary)
            conv_text = convert_text(summary)
            if upload_to_ftp(vid, conv_text,src_text):
                print(f"Successfully uploaded {vid} to FTP.")
        else:
            print(f"No transcription available for VID {vid}.")
    else:
        print(f"Failed to process call for VID {vid}.")

def v2t_main(start_vid, end_vid):
    token = get_flex_log_token()
    for vid in range(start_vid, end_vid):
        process_call(vid, token)

# コマンドライン引数の処理
def parse_vids(vids):
    # '-'で分割し、数値に変換
    vids_l = list(map(int, vids.split('-')))

    if len(vids_l) == 1: # 単一の数値の場合
        return vids_l[0], vids_l[0] + 1
    elif len(vids_l) == 2: # 範囲が指定された場合
        return vids_l[0], vids_l[1] + 1
    else:
        print("無効な通話ID形式です。")
        sys.exit(1)
 
if __name__ == "__main__":
    if len(sys.argv) > 1:
        vids = sys.argv[1]
    else:
        vids = input('通話IDを入力してください[s-e]:')

    start_vid, end_vid = parse_vids(vids)
    v2t_main(start_vid, end_vid)
