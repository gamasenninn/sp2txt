import sys
from replace_word import replace_text,load_conversion_dict
from fl_tools import get_flex_log_token,fl_get_items,fl_post_free_items


def replace_fl_free_items(vid):
    token = get_flex_log_token()

    res  = fl_get_items(vid,token)

    # CSVファイルから辞書を読み込み
    filename = 'replace.dic'
    conversion_dict = load_conversion_dict(filename)

    replaced_items = [
        replace_text(res[0]['free_item_01'],conversion_dict),
        replace_text(res[0]['free_item_02'],conversion_dict),
        replace_text(res[0]['free_item_03'],conversion_dict),
        replace_text(res[0]['free_item_04'],conversion_dict),
        replace_text(res[0]['free_item_05'],conversion_dict)
    ]

    ret = fl_post_free_items(vid,token,replaced_items)
    if ret:
        print(f"更新しました({vid})")
    else:
        print(f"更新エラー({vid})")

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
    for  vid in range(start_vid, end_vid):
        replace_fl_free_items(vid)