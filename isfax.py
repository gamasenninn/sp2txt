import sys
from pydub import AudioSegment
import numpy as np

target_freq_ranges = [(1660, 1665), (2099, 2100)] #FAXの音源の特徴周波数
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

def calculate_fft(data, samplerate):
    # FFT解析を行い、周波数と振幅を返す
    fft_result = np.fft.fft(data)
    fft_freq = np.fft.fftfreq(len(data), 1 / samplerate)
    amplitudes = np.abs(fft_result)
    return fft_freq, amplitudes

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

    data, samplerate = load_audio(audio_file_path)
    fft_freq, amplitudes = calculate_fft(data, samplerate)
    
    top_freq = find_top_frequencies(fft_freq, amplitudes, num_top_freq)
    
    return check_target_freq_ranges(top_freq, target_freq_ranges)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python isfax.py <audio_file_path>")
        sys.exit(1)

    audio_file_path = sys.argv[1]

    found_freqs = is_fax(audio_file_path)

    for freq_range, found in found_freqs.items():
        if found:
            print(f"指定周波数帯域 {freq_range[0]}Hz ～ {freq_range[1]}Hz が存在します。 (FAX)")
        else:
            print(f"指定周波数帯域 {freq_range[0]}Hz ～ {freq_range[1]}Hz は存在しません。")

