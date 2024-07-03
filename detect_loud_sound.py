import argparse
import os
import sys
import librosa
import soundfile as sf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import dataset.spectogram.spectogram_configs as cfg

def find_loud_intervals(file_path, output, visualise=False):
    y, sr = librosa.load(file_path, sr=None, duration=2)

    hop_length = int(sr * 0.02)
    frame_length = int(sr * 0.05)
    print(f'len(y) = {len(y)}')
    energy = np.array([
        sum(abs(y[i:i+frame_length]**2))
        for i in range(0, len(y), hop_length)
    ])
    
    if energy.size == 0 or np.max(energy) == 0:
        print(f"NO_AUDIO: {file_path}")
        return None

    max_time = 2.0
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
        loud_intervals.append((start_time, 1.0))
        
    
    loud_intervals, load_energies = merge_intervals(loud_intervals, energies, sr)
    if not loud_intervals:
        print(f"NOT_DETECTED: {file_path}")
        return None
    loudest_interval_index = np.argmax(load_energies)
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
    
    files = os.listdir(directory)
    files.sort()
    for file in files:
        if file.endswith(".wav"):
            file_path = os.path.join(directory, file)
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