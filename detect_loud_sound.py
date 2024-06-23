import argparse
import os
import librosa
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def find_loud_intervals(file_path, visualise=False):
    y, sr = librosa.load(file_path, sr=None, duration=2)

    hop_length = int(sr * 0.02)
    frame_length = int(sr * 0.05)
    energy = np.array([
        sum(abs(y[i:i+frame_length]**2))
        for i in range(0, len(y), hop_length)
    ])

    energy = energy / np.max(energy)
    avg_energy = np.mean(energy)

    loud_intervals = []
    start_time = None
    prev_end_time = None
    for i, e in enumerate(energy):
        if e > avg_energy and start_time is None:
            start_time = i * hop_length / sr
        elif e <= avg_energy and start_time is not None:
            end_time = i * hop_length / sr
            if prev_end_time is not None and start_time - prev_end_time <= 1.0 / sr:
                start_time = prev_start_time
            if i + 2 < len(energy) and energy[i+1] > avg_energy and energy[i+2] > avg_energy:
                continue
            loud_intervals.append((start_time, end_time))
            prev_start_time = start_time
            prev_end_time = end_time
            start_time = None

    if start_time is not None:
        loud_intervals.append((start_time, 1.0))
        
    merged_intervals = []
    i = 0
    current_start_time = 0
    while i < len(loud_intervals) - 1:
        start_time, end_time = loud_intervals[i]
        current_start_time = start_time if current_start_time == 0 else current_start_time
        
        next_start_time, next_end_time = loud_intervals[i+1]
        if next_start_time - end_time <= 5000.0 / sr:
            print('Adding end time to the next merge:', next_end_time)
            end_time = next_end_time 
        else:
            print('Merging interval:', current_start_time, end_time)
            merged_intervals.append((current_start_time, end_time))
            current_start_time = 0
        i += 1
    if current_start_time != 0:
        merged_intervals.append((current_start_time, loud_intervals[-1][1]))
    if loud_intervals:
        merged_intervals.append(loud_intervals[-1])
    loud_intervals = merged_intervals
    longest_interval = max(loud_intervals, key=lambda interval: interval[1] - interval[0])
    print("Longest Loud Interval:", longest_interval)

    if visualise:
        plt.plot(energy)
        plt.axhline(y=avg_energy, color='r', linestyle='--', label='Average Energy')
        plt.xlabel('Frame')
        plt.ylabel('Energy')
        plt.title('Energy Plot')
        plt.legend()
        
        for start_time, end_time in loud_intervals:
            if start_time == longest_interval[0] and end_time == longest_interval[1]:
                continue
            start_frame = int(start_time * sr / hop_length)
            end_frame = int(end_time * sr / hop_length)
            plt.axvspan(start_frame, end_frame, color='g', alpha=0.3)
            
        longest_start_time, longest_end_time = longest_interval
        longest_start_frame = int(longest_start_time * sr / hop_length)
        longest_end_frame = int(longest_end_time * sr / hop_length)
        plt.axvspan(longest_start_frame, longest_end_frame, color='r', alpha=0.5)
        
        plt.show()

    return longest_interval

def process_directory(directory):
    for root, _, files in os.walk(directory):
        files.sort()
        for file in files:
            if file.endswith(".wav"):
                file_path = os.path.join(root, file)
                interval = find_loud_intervals(file_path)
                (start_time, end_time) = interval
                data = [['golf_impact', start_time, end_time, 0, 0, 1]]
                df = pd.DataFrame(data, columns=["sound_event_recording","start_time","end_time","ele","azi","dist"])
                csv_file = file_path.replace('.wav', '.csv')
                df.to_csv(csv_file, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Example of parser. ')
    parser.add_argument('--input', type=str, help='file or directory to process.')
    args = parser.parse_args()
    
    process_directory(args.input)
    print("CSV file has been created.")