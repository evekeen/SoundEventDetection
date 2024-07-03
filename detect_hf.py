import sys
import librosa
import numpy as np
from dataset.spectogram.preprocess import multichannel_complex_to_log_mel, multichannel_stft
import dataset.spectogram.spectogram_configs as cfg

from dataset.dataset_utils import read_multichannel_audio

def detect_high_pitch_intervals(file_path):
    multichannel_waveform, sr = librosa.load(file_path, sr=cfg.working_sample_rate, duration=2)
    if len(multichannel_waveform.shape) == 1:
        multichannel_waveform = multichannel_waveform.reshape(-1, 1)
    # multichannel_waveform = multichannel_waveform[int(cfg.working_sample_rate * sec_start): int(cfg.working_sample_rate * sec_end)]
    feature = multichannel_stft(multichannel_waveform)
    feature = multichannel_complex_to_log_mel(feature)
    feature = (feature - np.min(feature)) / (np.max(feature) - np.min(feature))
    
    mid_freq = cfg.mel_bins // 2
    
    upper_bins = feature[0, :, mid_freq:]  # Select upper frequency bins
    lower_bins = feature[0, :, :mid_freq]  # Select lower frequency bins
    mean_hf = np.mean(np.sum(upper_bins, axis=1))
    mean_lf = np.mean(np.sum(lower_bins, axis=1))
    frame_length = cfg.frame_size
    hop_length = cfg.hop_size
    
    print(f'len(multichannel_waveform) = {len(multichannel_waveform)}')
    energies = np.array([
        sum(abs(multichannel_waveform[i:i+frame_length]**2))
        for i in range(0, len(multichannel_waveform), hop_length)
    ])

    intervals = []
    for i in range(upper_bins.shape[0]):
        hf = np.sum(upper_bins[i, :])
        lf = np.sum(lower_bins[i, :])        
        if hf > mean_hf and lf > mean_lf and hf / lf > mean_hf / mean_lf:
            print(f"High pitch detected at {i}")
            intervals.append((i * hop_length / cfg.working_sample_rate, (i + 1) * hop_length / cfg.working_sample_rate))

    return intervals


if __name__ == '__main__':
    audio_file = sys.argv[1]
    intervals = detect_high_pitch_intervals(audio_file)
    print(intervals)