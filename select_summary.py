# ローカルの要約ファイルをFROM_TOで指定し、要約部分だけを切り抜く連続処理をする。
import glob
import os
import re
from dotenv import load_dotenv


load_dotenv()


# SP2TXTが存在するディレクトリ
file_dir = os.environ["LOCAL_FILE_DIR"]
file_path = os.path.join(file_dir,"sum_*.txt")

file_list = glob.glob(file_path)

from_num = 46274
to_num = 46292


# Pattern to extract the number from the filename
pattern = re.compile(r'sum_(\d+)\.txt')

for file in file_list:
    # Extract the number from the filename
    match = pattern.search(file)
    if match:
        file_num = int(match.group(1))
        if from_num <= file_num <= to_num:
            # This file is within the specified range
            # Add your processing logic here

            #ファイルを読み、＜通話履歴:＞というワードの前のテキストだけを抜き出す
            # Open and read the file
            with open(file, 'r', encoding='cp932') as f:
                content = f.read()

                # Find the position of "＜通話履歴:＞" in the text
                index = content.find("通話履歴:")

                # Check if the phrase is found
                if index != -1:
                    # Extract everything before the phrase
                    extracted_text = content[index:]

                    # Process the extracted text here
                    print(f"file: {file}")
                    print(f"summary:\n{extracted_text}")  # extracted text
                    print("-----------------")




