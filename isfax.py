import sys
from pydub import AudioSegment
import numpy as np
import matplotlib.pyplot as plt

num_top_freq = 100

def truncate(frequency, decimals=0):
    # 小数点以下を切り捨てる関数
    multiplier = 10 ** decimals
    return int(frequency * multiplier) / multiplier

def load_audio(audio_file_path):
    # 音声ファイルを読み込んで正規化し、データとサンプルレートを返す
    audio = AudioSegment.from_file(audio_file_path, format="m4a")
    data = np.array(audio.split_to_mono()[0].get_array_of_samples())
    data = data / np.max(np.abs(data))
    samplerate = audio.frame_rate
    return data, samplerate

def calculate_fft(data, samplerate, start_from_beginning=10, end_from_last=10):
    """
    Perform FFT analysis and return frequencies and amplitudes.
    Optionally, sample n seconds from the beginning or end of the data.
    Default is 10 seconds from the beginning.
    """
    duration_ms = len(data) * 1000 / samplerate
    if start_from_beginning is not None:
        # Sampling n seconds from the beginning
        start_index = 0
        end_index = int(samplerate * start_from_beginning)
        data = data[start_index:end_index]
    elif end_from_last is not None:
        # Sampling n seconds from the end
        start_index = int(samplerate * (duration_ms / 1000 - end_from_last))
        end_index = -1
        data = data[start_index:end_index]
    
    fft_result = np.fft.fft(data)
    fft_freq = np.fft.fftfreq(len(data), 1 / samplerate)
    amplitudes = np.abs(fft_result)
    return fft_freq, amplitudes

def load_audio_fft(audio_file_path,start_from_beginning=10, end_from_last=10):
    data,samplerate = load_audio(audio_file_path)
    return calculate_fft(data,samplerate,start_from_beginning=10, end_from_last=10)

def find_top_frequencies(fft_freq, amplitudes, num_frequencies):
    # 上位の周波数と振幅を返す
    sorted_indices = np.argsort(amplitudes)[::-1]
    sorted_amplitudes = amplitudes[sorted_indices]
    sorted_freq = fft_freq[sorted_indices]
    
    top_freq = []
    seen_freq = set()
    
    for i in range(num_frequencies):
        truncated_freq = int(truncate(sorted_freq[i], 0))
        if truncated_freq not in seen_freq:
            seen_freq.add(truncated_freq)
            top_freq.append((truncated_freq, sorted_amplitudes[i]))
    
    return top_freq

def check_target_freq_ranges(top_freq, target_freq_ranges):
    # 指定周波数帯域が存在するかどうかをチェック
    found_freqs = {freq_range: False for freq_range in target_freq_ranges}

    for freq, _ in top_freq:
        for freq_range in target_freq_ranges:
            if freq_range[0] <= freq <= freq_range[1]:
                found_freqs[freq_range] = True

    return found_freqs

def is_fax(audio_file_path):
    target_freq_ranges = [(1660, 1665), (2099, 2100)] #FAXの音源の特徴周波数
    fft_freq, amplitudes =  load_audio_fft(audio_file_path,start_from_beginning=30)  
    top_freq = find_top_frequencies(fft_freq, amplitudes, num_top_freq)    
    return check_target_freq_ranges(top_freq, target_freq_ranges)

def detect_sound(top_freq,target_freq_ranges):
    found_freqs = check_target_freq_ranges(top_freq, target_freq_ranges)
    detected = 0
    for freq_range, found in found_freqs.items():
        if found:
            #print(f"指定周波数帯域 {freq_range[0]}Hz ～ {freq_range[1]}Hz が存在します。")
            detected += 1

    if detected > 1 :
        return True
    else:
        return False
    
def classify_audio_type(audio_file_path):
    target_fax_ranges = [(1660, 1665), (2099, 2100)] #FAXの音源の特徴周波数
    target_call_only_ranges = [(397, 400), (416, 417)] #呼び出しのみの音源の特徴周波数

    data, samplerate = load_audio(audio_file_path)

    #--- 最初の30秒を解析 ---
    first_fft_freq, first_amplitudes = calculate_fft(data, samplerate,start_from_beginning=30)
    first_top_freq = find_top_frequencies(first_fft_freq, first_amplitudes, num_top_freq)
    #--- 最後の20秒を解析 ---
    last_fft_freq, last_amplitudes = calculate_fft(data, samplerate,start_from_beginning=None, end_from_last=20) 
    last_top_freq = find_top_frequencies(last_fft_freq, last_amplitudes, num_top_freq)    

    #----- FAXの識別 ------
    if detect_sound(first_top_freq,target_fax_ranges):
        return "FAX"
    #----- CALL ONLYの識別 ------
    if detect_sound(last_top_freq,target_call_only_ranges):
        return "CALL_ONLY"

    return "NORMAL"

#------ main のための関数　--------
def plot_sound(fft_freq, amplitudes,samplerate,file):
    plt.figure(figsize=(15, 5))
    plt.plot(fft_freq, amplitudes)
    plt.title("FFT of the Audio File")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Amplitude")
    plt.xlim(0, samplerate / 2)
    plt.savefig(f'{file}.png')
    plt.show()

def go_test():
    def_test = [
        ["sound/fax.m4a","FAX"],
        ["sound/call_only_01.m4a","CALL_ONLY"],
        ["sound/call_only_02.m4a","CALL_ONLY"],
        ["sound/call_only_03.m4a","CALL_ONLY"],
        ["sound/call_hum_01.m4a","NORMAL"],
        ["sound/call_hum_02.m4a","NORMAL"]
    ]
    for file,type in def_test:
        print(file,type)
        assert classify_audio_type(file) == type


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python isfax.py <audio_file_path>")
        print("-----\n-----\nGo test\n\n")
        go_test()
        sys.exit(0)

    audio_file_path = sys.argv[1]

    #------ FAXの判定　--------

    found_freqs = is_fax(audio_file_path)

    for freq_range, found in found_freqs.items():
        if found:
            print(f"指定周波数帯域 {freq_range[0]}Hz ～ {freq_range[1]}Hz が存在します。 (FAX)")
        else:
            print(f"指定周波数帯域 {freq_range[0]}Hz ～ {freq_range[1]}Hz は存在しません。")


    #---FAX以外をチェックする場合(コールだけ)
    target_freq_ranges = [(397, 400), (416, 417)] #FAXの音源の特徴周波数

    data, samplerate = load_audio(audio_file_path)
    fft_freq, amplitudes = calculate_fft(data, samplerate,start_from_beginning=20)
    plot_sound(fft_freq, amplitudes,samplerate,audio_file_path+"01")


    fft_freq, amplitudes = calculate_fft(data, samplerate,start_from_beginning=None, end_from_last=20) 
    top_freq = find_top_frequencies(fft_freq, amplitudes, num_top_freq)
    
    found_freqs = check_target_freq_ranges(top_freq, target_freq_ranges)
    for freq_range, found in found_freqs.items():
        if found:
            print(f"指定周波数帯域 {freq_range[0]}Hz ～ {freq_range[1]}Hz が存在します。 (CALL)")
        else:
            print(f"指定周波数帯域 {freq_range[0]}Hz ～ {freq_range[1]}Hz は存在しません。")

    plot_sound(fft_freq, amplitudes,samplerate,audio_file_path+"02")
