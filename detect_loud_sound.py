import argparse
import os
import sys
import librosa
from matplotlib.figure import Figure
import soundfile as sf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import torch
from dataset.dataset_utils import read_multichannel_audio
from dataset.spectogram.preprocess import multichannel_complex_to_log_mel, multichannel_stft
import dataset.spectogram.spectogram_configs as cfg
from models.DcaseNet import DcaseNet_v3
import tkinter as tk
from tkinter import ttk
import sounddevice as sd
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk) 

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
        energies.append(interval_energy)
    
    selected_indices = []
    if detected:
        for i, interval in enumerate(loud_intervals):
            if has_intersection(interval, detected):
                selected_indices.append(i)
    else:
        selected_indices = list(range(len(loud_intervals)))
    print("Selected Indices:", selected_indices)
    print("energies:", len(energies))
                
    loud_intervals = [loud_intervals[i] for i in selected_indices]
    loud_energies = [energies[i] for i in selected_indices]
    
    if not loud_intervals:
        print(f"NOT_DETECTED: {file_path}")
        return None
    loudest_interval_index = np.argmax(loud_energies)
    loudest_interval = loud_intervals[loudest_interval_index]
    print("Loudest Interval:", loudest_interval)
    
    def do_visualise():
        nonlocal loudest_interval
        window = tk.Tk()
        window.title("Loudest Interval Selection")
        
        def plot():
            fig = Figure(figsize=(10, 5))
            plot1 = fig.add_subplot(111)
            plot1.plot(energy)
            plot1.axhline(y=avg_energy, color='r', linestyle='--', label='Average Energy')
            plot1.legend()
                
            longest_start_time, longest_end_time = loudest_interval
            longest_start_frame = int(longest_start_time * sr / hop_length)
            longest_end_frame = int(longest_end_time * sr / hop_length)
            plot1.axvspan(longest_start_frame, longest_end_frame, color='r', alpha=0.5)        
            
            canvas = FigureCanvasTkAgg(fig, master = window)   
            canvas.draw() 
            canvas.get_tk_widget().grid(row=3, columnspan=4)
        
        def update_loudest_interval(draw=True):
            nonlocal loudest_interval
            start_frame_index = start_slider.get()
            frames_to_override = frames_slider.get()
            start_time = start_frame_index * hop_length / sr
            end_time = (start_frame_index + frames_to_override) * hop_length / sr
            loudest_interval = (start_time, end_time)
            print(f"Updated Loudest Interval: {loudest_interval[0]:.2f} - {loudest_interval[1]:.2f}")
            window.destroy()
            if draw:
                do_visualise()
        
        def update_start_label(event):
            start_value.set(f"Start Frame: {int(start_slider.get())}")
            update_loudest_interval()

        def update_frames_label(event):
            frames_value.set(f"Frames: {int(frames_slider.get())}")
            update_loudest_interval()
            
        def increment_start_frame():
            current_frame = start_slider.get()
            start_slider.set(current_frame + 1)
            frames_slider.set(frames_slider.get() - 1)
            update_start_label(None)
            
        def decrement_start_frame():
            current_frame = start_slider.get()
            start_slider.set(current_frame - 1)
            frames_slider.set(frames_slider.get() + 1)
            update_start_label(None)                        
        
        decrement_button = ttk.Button(window, text="<", command=decrement_start_frame)
        decrement_button.grid(row=0, column=0)
        
        start_value = tk.StringVar()
        start_value.set(f"Start Frame: {int(loudest_interval[0] * sr / hop_length)}")
        start_label = ttk.Label(window, textvariable=start_value)
        start_label.grid(row=0, column=1)
        
        start_slider = ttk.Scale(window, from_=0, to=len(energy)-1, orient="horizontal", length=200)
        start_slider.set(loudest_interval[0] * sr / hop_length)
        start_slider.grid(row=0, column=2)
        # start_slider.bind("<Motion>", update_start_label)
        start_slider.bind("<ButtonRelease-1>", update_start_label)
        
        increment_button = ttk.Button(window, text=">", command=increment_start_frame)
        increment_button.grid(row=0, column=3)

        frames_value = tk.StringVar()
        frames_value.set(f"Frames: {int((loudest_interval[1] - loudest_interval[0]) * sr / hop_length)}")
        frames_label = ttk.Label(window, textvariable=frames_value)
        frames_label.grid(row=1, column=1)
        
        frames_slider = ttk.Scale(window, from_=1, to=len(energy), orient="horizontal", length=200)
        frames_slider.set((loudest_interval[1] - loudest_interval[0]) * sr / hop_length)
        frames_slider.grid(row=1, column=2)
        # frames_slider.bind("<Motion>", update_frames_label)
        frames_slider.bind("<ButtonRelease-1>", update_frames_label)           
        
        def play_sound():
            start_frame = int(loudest_interval[0] * sr)
            end_frame = int(loudest_interval[1] * sr)
            audio_data = y[start_frame:end_frame]
            sd.play(audio_data, sr)

        def save():
            update_loudest_interval(draw=False)
            window.destroy()
            
        play_button = ttk.Button(window, text="Play Sound", command=play_sound)
        play_button.grid(row=2, column=1)
        update_button = ttk.Button(window, text="Set", command=save)
        update_button.grid(row=2, column=2)
        plot()
        window.mainloop()
    
    if visualise:
        print("Visualising...")
        do_visualise()
        
    loudest_file_name = os.path.join(output, os.path.basename(file_path))
    export_interval_wav(file_path, loudest_interval, loudest_file_name)

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
            interval = find_loud_intervals(file_path, output, visualise=True)
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