import argparse
import csv
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

class LoudIntervalSelector:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Loudest Interval Selection")
        self.fig = Figure(figsize=(10, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=3, columnspan=4)
        self.energy = None
        self.sr = None
        self.hop_length = None
        self.loudest_interval = None
        self.y = None
        self.start_slider = None
        self.frames_slider = None

    def update_plot(self):
        self.fig.clear()
        plot1 = self.fig.add_subplot(111)
        plot1.plot(self.energy)
        plot1.set_xticks(np.arange(0, len(self.energy), self.sr/self.hop_length))
        plot1.set_xticks(np.arange(0, len(self.energy), self.sr/self.hop_length/10), minor=True)
        plot1.axvspan(self.loudest_interval[0] * self.sr / self.hop_length,
                      self.loudest_interval[1] * self.sr / self.hop_length, color='r', alpha=0.5)
        self.canvas.draw()

    def update_loudest_interval(self):
        start_frame_index = self.start_slider.get()
        frames_to_override = self.frames_slider.get()
        start_time = start_frame_index * self.hop_length / self.sr
        end_time = (start_frame_index + frames_to_override) * self.hop_length / self.sr
        self.loudest_interval = (start_time, end_time)
        self.update_plot()

    def update_start_label(self, event):
        self.start_value.set(f"Start Frame: {int(self.start_slider.get())}")
        self.update_loudest_interval()

    def update_frames_label(self, event):
        self.frames_value.set(f"Frames: {int(self.frames_slider.get())}")
        self.update_loudest_interval()
        
    def decrement_start(self):
        self.start_slider.set(self.start_slider.get() - 1)
        self.update_start_label(None)
        
    def increment_start(self):
        self.start_slider.set(self.start_slider.get() + 1)
        self.update_start_label(None)

    def play_sound(self):
        start_frame = int(self.loudest_interval[0] * self.sr)
        end_frame = int(self.loudest_interval[1] * self.sr)
        audio_data = self.y[start_frame:end_frame]
        sd.stop()
        sd.play(audio_data, self.sr)

    def play_all(self):
        sd.stop()
        sd.play(self.y, self.sr)

    def save(self):
        self.update_loudest_interval()
        sd.stop()
        self.window.quit()

    def skip(self):
        self.loudest_interval = None
        sd.stop()
        self.window.quit()
        

    def configure_window(self, energy, sr, hop_length, loudest_interval, y):
        self.energy = energy
        self.sr = sr
        self.hop_length = hop_length
        self.loudest_interval = loudest_interval
        self.y = y

        self.start_value = tk.StringVar()
        self.start_value.set(f"Start Frame: {int(self.loudest_interval[0] * self.sr / self.hop_length)}")
        start_label = ttk.Label(self.window, textvariable=self.start_value)
        start_label.grid(row=0, column=1)

        self.start_slider = ttk.Scale(self.window, from_=0, to=len(self.energy)-1, orient="horizontal", length=500)
        self.start_slider.set(self.loudest_interval[0] * self.sr / self.hop_length)
        self.start_slider.grid(row=0, column=2)
        self.start_slider.bind("<Motion>", self.update_start_label)
        self.start_slider.bind("<ButtonRelease-1>", self.update_start_label)
        
        decrement_button = ttk.Button(self.window, text="<", command=self.decrement_start)
        decrement_button.grid(row=0, column=0)

        increment_button = ttk.Button(self.window, text=">", command=self.increment_start)
        increment_button.grid(row=0, column=3)

        self.frames_value = tk.StringVar()
        self.frames_value.set(f"Frames: {int((self.loudest_interval[1] - self.loudest_interval[0]) * self.sr / self.hop_length)}")
        frames_label = ttk.Label(self.window, textvariable=self.frames_value)
        frames_label.grid(row=1, column=1)

        self.frames_slider = ttk.Scale(self.window, from_=1, to=10, orient="horizontal", length=500)
        self.frames_slider.set((self.loudest_interval[1] - self.loudest_interval[0]) * self.sr / self.hop_length)
        self.frames_slider.grid(row=1, column=2)
        self.frames_slider.bind("<Motion>", self.update_frames_label)
        self.frames_slider.bind("<ButtonRelease-1>", self.update_frames_label)

        play_all_button = ttk.Button(self.window, text="Play All", command=self.play_all)
        play_all_button.grid(row=2, column=0)
        play_button = ttk.Button(self.window, text="Play", command=self.play_sound)
        play_button.grid(row=2, column=1)
        update_button = ttk.Button(self.window, text="Set", command=self.save)
        update_button.grid(row=2, column=2)
        skip_button = ttk.Button(self.window, text="Skip", command=self.skip)
        skip_button.grid(row=2, column=3)

        self.update_plot()

    def run(self):
        self.window.mainloop()


def find_loud_intervals(file_path, output, detected=[], visualise=False, selector=None):
    max_time = 8.0
    y, sr = librosa.load(file_path, sr=None, duration=max_time)
    hop_length = int(sr * 0.02)
    frame_length = int(sr * 0.05)
    energy = np.array([
        max(y[i:i+frame_length]**2)
        for i in range(0, len(y), hop_length)
    ])
    
    if energy.size == 0 or np.max(energy) == 0:
        print(f"NO_AUDIO: {file_path}")
        return None

    energy = energy[:int(max_time * sr / hop_length)]
    max_energy_index = np.argmax(energy)
    frame_start = max_energy_index * hop_length / sr
    frame_end = (max_energy_index + 1) * hop_length / sr
    loud_intervals = [(frame_start, frame_end)]
    
    if detected:
        for i, interval in enumerate(loud_intervals):
            if has_intersection(interval, detected):
                selected_indices.append(i)
    else:
        selected_indices = [0]
                
    loud_intervals = [loud_intervals[i] for i in selected_indices]
    
    if not loud_intervals:
        print(f"NOT_DETECTED: {file_path}")
        return None
    loudest_interval = loud_intervals[0]
    start_time = max(0, loudest_interval[0] - hop_length * 2 / sr)
    loudest_interval = (start_time, loudest_interval[1] + hop_length * 2 / sr)
    
    if visualise:
        print("Visualising...")
        selector.configure_window(energy, sr, hop_length, loudest_interval, y)
        selector.play_sound()
        selector.run()
        
    if not loudest_interval:
        return None

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
            end_time = next_end_time 
        else:
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
    
    skip_list = []
    csv_file = os.path.join(directory, 'skip.csv')
    if not os.path.exists(csv_file):
        with open(csv_file, "w") as file:
            pass
    with open(csv_file, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            skip_list.append(row[0])
    
    files = os.listdir(directory)
    files.sort()
    selector = LoudIntervalSelector()
    for file in files:
        if file.endswith(".wav"):
            file_path = os.path.join(directory, file)
            
            if file_path in skip_list:
                print(f"Skipping {file_path}")
                continue
            
            csv_path = os.path.join(csv_output, os.path.basename(file_path).replace('.wav', '.csv'))
            if os.path.exists(csv_path):
                print(f"CSV file already exists for {file_path}")
                continue
            print(f"Processing {file}")
            interval = find_loud_intervals(file_path, output, visualise=True, selector=selector)
            if not interval:
                print(f"Skipping {file}")
                skip_list.append(file)
                with open(csv_file, "a") as file:
                    writer = csv.writer(file)
                    writer.writerow([file_path])
                continue
            (start_time, end_time) = interval
            data = [['golf_impact', start_time, end_time, 0, 0, 1]]
            df = pd.DataFrame(data, columns=["sound_event_recording","start_time","end_time","ele","azi","dist"])
            df.to_csv(csv_path, index=False)

if __name__ == "__main__":
    input = sys.argv[1]
    
    if os.path.isdir(input):
        process_directory(input)
    else:
        selector = LoudIntervalSelector()
        find_loud_intervals(input, os.path.dirname(input), visualise=True, selector=selector)
    print("CSV file has been created.")
