import argparse
from dataset.spectogram.preprocess import multichannel_stft, multichannel_complex_to_log_mel
from dataset.dataset_utils import read_multichannel_audio
from dataset.spectogram import spectogram_configs as cfg
import matplotlib.pyplot as plt
import numpy as np
import soundfile
import matplotlib
from utils.plot_utils import plot_sample_features
import os

matplotlib.use('TkAgg')

def plot_spectogram(audio_path):
    sec_start = 0.0
    sec_end = 2.00
    
    target_start = 0.0
    target_end = 0.0
    
    cvs_path = audio_path.replace(".wav", ".csv")
    if os.path.exists(cvs_path):
        with open(cvs_path, 'r') as f:
            f.readline()
            labels = f.readline().split(",")
            target_start = float(labels[1])
            target_end = float(labels[2])
            print(f"Target start: {target_start}, Target end: {target_end}")

    multichannel_waveform = read_multichannel_audio(audio_path=audio_path, target_fs=cfg.working_sample_rate)


    multichannel_waveform = multichannel_waveform[int(cfg.working_sample_rate * sec_start): int(cfg.working_sample_rate * sec_end)]
    soundfile.write("tmp_file.WAV", multichannel_waveform, cfg.working_sample_rate)
    feature = multichannel_stft(multichannel_waveform)
    feature = multichannel_complex_to_log_mel(feature)

    frames_num = feature.shape[1]
    print(f"frames: {frames_num}")
    tick_hop = max(1, frames_num // 20)
    xticks = np.concatenate((np.arange(0, frames_num - tick_hop, tick_hop), [frames_num]))
    xlabels = [f"{x / cfg.frames_per_second:.1f}s" for x in xticks]

    fig = plt.figure()
    fig.set_size_inches(10, 8)
    ax = fig.add_subplot(211)
    ax.matshow(feature[0].T, origin='lower', cmap='jet', aspect='auto')
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, rotation='vertical')
    ax.xaxis.set_ticks_position('bottom')
    if target_end > 0:
        ax.axvspan(target_start * cfg.frames_per_second, target_end * cfg.frames_per_second, color='b', alpha=0.3)

    ax = fig.add_subplot(212)
    signal = multichannel_waveform.mean(1)
    signal = signal[:2000]
    ax.plot(range(len(signal)), signal)

    ax.get_yaxis().set_visible(False)
    plt.autoscale(tight=True)
    plt.show()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Example of parser. ')
    parser.add_argument('--input', type=str, help='file or directory to process.')
    args = parser.parse_args()
    
    if args.input is None:
        raise ValueError("Please provide input file")
    
    if os.path.isdir(args.input):
        for file_name in os.listdir(args.input):
            if file_name.endswith(".wav"):
                print(f"Analyzing {file_name}")
                audio_path = os.path.join(args.input, file_name)
                plot_spectogram(audio_path)
    else:
        plot_spectogram(args.input)
    