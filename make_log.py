# 以下は上記で説明したコードの全体です。

import os
import glob
import re

# 番号を切り出す関数
def extract_numbers_from_filename(filenames):
    extracted_numbers = []
    for filename in filenames:
        match = re.search(r'txt_(\d+).csv', filename)
        if match:
            extracted_numbers.append(int(match.group(1)))
    return extracted_numbers

# globライブラリを使って指定したパターンにマッチするファイル名を読み出す関数
def fetch_filenames_with_glob(directory_path, pattern):
    return glob.glob(f"{directory_path}/{pattern}")

# 番号をログファイルに保存する関数
def save_numbers_to_log(numbers, log_file_path):
    try:
        with open(log_file_path, 'w') as log_file:
            for number in numbers:
                log_file.write(f"{number}\n")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

# ディレクトリパスと検索パターン、ログファイルパス（実際のパスに置き換えてください）
directory_path = "temp"
search_pattern = "txt_*.csv"
log_file_path = "temp/extracted_numbers.log"

# ディレクトリからglobを使ってファイル名を読み出す
fetched_filenames = fetch_filenames_with_glob(directory_path, search_pattern)
# ファイルパスからファイル名だけを取得（ディレクトリ部分を除去）
fetched_filenames = [os.path.basename(f) for f in fetched_filenames]

# ファイル名から番号を抽出する
extracted_numbers = extract_numbers_from_filename(fetched_filenames)
extracted_numbers.sort(reverse=True)
print("降順で1000件出力します:",extracted_numbers[:1000])

# 番号をログファイルに保存する
save_success = save_numbers_to_log(extracted_numbers, log_file_path)

print(directory_path, search_pattern, log_file_path, save_success )
