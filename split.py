# -*- coding: utf-8 -*-
from pydub import AudioSegment
from pydub.silence import split_on_silence

# wavファイルのデータ取得
sound = AudioSegment.from_file("814.wav", format="wav")

# wavデータの分割（無音部分で区切る）
chunks = split_on_silence(sound, min_silence_len=1000, silence_thresh=-40, keep_silence=600)

# 分割したデータ毎にファイルに出力
for i, chunk in enumerate(chunks):
    chunk.export("output" + str(i) +".wav", format="wav")
