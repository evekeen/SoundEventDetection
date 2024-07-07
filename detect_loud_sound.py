import argparse
import os
import sys
import librosa
import soundfile as sf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import torch
from dataset.dataset_utils import read_multichannel_audio
from dataset.spectogram.preprocess import multichannel_complex_to_log_mel, multichannel_stft
import dataset.spectogram.spectogram_configs as cfg
from models.DcaseNet import DcaseNet_v3

def find_loud_intervals(file_path, output, detected=[], visualise=False):
    max_time = 8.0
    y, sr = librosa.load(file_path, sr=None, duration=max_time)

    hop_length = int(sr * 0.02)
    frame_length = int(sr * 0.05)
    energy = np.array([
        sum(abs(y[i:i+frame_length]**2))
        for i in range(0, len(y), hop_length)
    ])
    
    if energy.size == 0 or np.max(energy) == 0:
        print(f"NO_AUDIO: {file_path}")
        return None


    energy = energy[:int(max_time * sr / hop_length)]
    energy = energy / np.max(energy)
    avg_energy = np.mean(energy)
    threshold = avg_energy * 1.4

    loud_intervals = []
    energies = []
    start_time = None
    prev_end_time = None
    interval_energy = 0
    for i, e in enumerate(energy):
        if e > threshold and start_time is None:
            start_time = i * hop_length / sr
        elif e <= threshold and start_time is not None:
            end_time = i * hop_length / sr
            if prev_end_time is not None and start_time - prev_end_time <= 1.0 / sr:
                start_time = prev_start_time
            if i + 2 < len(energy) and energy[i+1] > threshold and energy[i+2] > threshold:
                continue
            loud_intervals.append((start_time, end_time))
            interval_energy = max(interval_energy, e)
            energies.append(interval_energy)
            interval_energy = 0
            prev_start_time = start_time
            prev_end_time = end_time
            start_time = None

    if start_time is not None:
        loud_intervals.append((start_time, max_time))
    
    selected_indices = []
    if detected:
        for i, interval in enumerate(loud_intervals):
            if has_intersection(interval, detected):
                selected_indices.append(i)
    else:
        selected_indices = list(range(len(loud_intervals)))
                
    loud_intervals = [loud_intervals[i] for i in selected_indices]
    loud_energies = [energies[i] for i in selected_indices]
    
    if not loud_intervals:
        print(f"NOT_DETECTED: {file_path}")
        return None
    loudest_interval_index = np.argmax(loud_energies)
    loudest_interval = loud_intervals[loudest_interval_index]
    print("Loudest Interval:", loudest_interval)
    
    loudest_file_name = os.path.join(output, os.path.basename(file_path))
    export_interval_wav(file_path, loudest_interval, loudest_file_name)

    if visualise:
        plt.plot(energy)
        plt.axhline(y=avg_energy, color='r', linestyle='--', label='Average Energy')
        plt.xlabel('Frame')
        plt.ylabel('Energy')
        plt.title('Energy Plot')
        plt.legend()
        
        for start_time, end_time in loud_intervals:
            if start_time == loudest_interval[0] and end_time == loudest_interval[1]:
                continue
            start_frame = int(start_time * sr / hop_length)
            end_frame = int(end_time * sr / hop_length)
            plt.axvspan(start_frame, end_frame, color='g', alpha=0.3)
            
        longest_start_time, longest_end_time = loudest_interval
        longest_start_frame = int(longest_start_time * sr / hop_length)
        longest_end_frame = int(longest_end_time * sr / hop_length)
        plt.axvspan(longest_start_frame, longest_end_frame, color='r', alpha=0.5)
        
        plt.show()

    return loudest_interval


def detect_impact_regions(model, audio_file):
    multichannel_audio = read_multichannel_audio(audio_path=audio_file, target_fs=cfg.working_sample_rate)
    log_mel_features = multichannel_complex_to_log_mel(multichannel_stft(multichannel_audio))
    
    with torch.no_grad():
        input = torch.from_numpy(log_mel_features).to(torch.float32).to('cpu')
        output_event = model(input.unsqueeze(0))
    output_event = output_event.cpu()
    time_intervals = []
    step = cfg.frame_size - cfg.hop_size
    for i, frame_value in enumerate(output_event[0]):
        if frame_value > 0.3:
            start_time = i * step / cfg.working_sample_rate
            end_time = start_time + cfg.frame_size / cfg.working_sample_rate
            time_intervals.append((start_time, end_time))
            
    merged = []
    for interval in time_intervals:
        if not merged:
            merged.append(interval)
        else:
            prev_start, prev_end = merged[-1]
            start, end = interval
            if start <= prev_end:
                merged[-1] = (prev_start, end)
            else:
                merged.append(interval)
    return merged

def has_intersection(interval, intervals):
    return any([interval[0] <= end and interval[1] >= start for start, end in intervals])

def merge_intervals(intervals, energies, sr):
    merged_intervals = []
    merged_energies = []
    merged_interval_energy = 0
    i = 0
    current_start_time = 0
    while i < len(intervals) - 1:
        start_time, end_time = intervals[i]
        current_start_time = start_time if current_start_time == 0 else current_start_time
        
        next_start_time, next_end_time = intervals[i+1]
        if next_start_time - end_time <= 5000.0 / sr:
            print('Adding end time to the next merge:', next_end_time)
            end_time = next_end_time 
        else:
            print('Merging interval:', current_start_time, end_time)
            merged_intervals.append((current_start_time, end_time))
            merged_interval_energy = max(merged_interval_energy, energies[i])
            merged_energies.append(merged_interval_energy)
            merged_interval_energy = 0
            current_start_time = 0
        i += 1
    if current_start_time != 0:
        merged_intervals.append((current_start_time, intervals[-1][1]))
        merged_interval_energy = max(merged_interval_energy, energies[-1])
        merged_energies.append(merged_interval_energy)
    if intervals:
        merged_intervals.append(intervals[-1])
        merged_energies.append(energies[-1] if energies else 0)  
        
    return merged_intervals, merged_energies

def export_interval_wav(file_path, interval, output_file):
    y, sr = librosa.load(file_path, sr=None, duration=2)
    start_frame = int(interval[0] * sr)
    end_frame = int(interval[1] * sr)
    y = y[start_frame:end_frame]
    sf.write(output_file, y, sr)
    print(f"Exported loudest interval to {output_file}")

def process_directory(directory):
    output = os.path.join(directory, 'loudest')
    os.makedirs(output, exist_ok=True)
    csv_output = os.path.join(output, 'csv')
    os.makedirs(csv_output, exist_ok=True)
    
    model = DcaseNet_v3(1).to('cpu')
    checkpoint = torch.load('/Users/ivkin/git/SoundEventDetection-Pytorch/networks/dcasenet_fixed_order/iteration_5000.pth', map_location='cpu')
    model.load_state_dict(checkpoint['model'])
    
    files = os.listdir(directory)
    files.sort()
    for file in files:
        if file.endswith(".wav"):
            file_path = os.path.join(directory, file)
            # detected = detect_impact_regions(model, file_path)
            interval = find_loud_intervals(file_path, output)
            if interval is None:
                continue
            (start_time, end_time) = interval
            data = [['golf_impact', start_time, end_time, 0, 0, 1]]
            df = pd.DataFrame(data, columns=["sound_event_recording","start_time","end_time","ele","azi","dist"])
            csv_path = os.path.join(csv_output, os.path.basename(file_path).replace('.wav', '.csv'))
            df.to_csv(csv_path, index=False)

if __name__ == "__main__":
    input = sys.argv[1]
    
    if os.path.isdir(input):
        process_directory(input)
    else:
        find_loud_intervals(input, os.path.dirname(input), visualise=True)
    print("CSV file has been created.")