import sys
import cv2
from impact_detector import ImpactDetector
import os
import tkinter as tk
from PIL import ImageTk, Image
import yaml


class VideoLabeler:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Impact Preview")
        self.detector = ImpactDetector("networks/dcase_pool_1/iteration_21600.pth")
        self.image_label = None
        self.frame_num = 0
        self.video_path = None
        self.video_files = None
        self.current_video_index = 0
        self.video_dir = None
        self.output_dir = None


    def load_videos(self, video_dir, output_dir="output"):
        self.video_dir = video_dir
        self.output_dir = output_dir
        video_files = [f for f in os.listdir(video_dir) if os.path.isfile(os.path.join(video_dir, f))]
        self.video_files = [f for f in video_files if f.lower().endswith(('.mp4', '.avi', '.mov'))]
        
        if len(self.video_files) == 0:
            print("No video files found in the directory.")
            return
        
        self.video_path = os.path.join(video_dir, self.video_files[self.current_video_index])
        self.preview_impact_selection()
        self.root.mainloop()


    def prepare_ui(self):
        self.image_label = tk.Label(self.root)
        self.image_label.grid(row=0, column=0, columnspan=3)
        
        prev_button = tk.Button(self.root, text="Previous Frame", command=lambda: self.prev_frame())
        prev_button.grid(row=1, column=0)
        
        next_button = tk.Button(self.root, text="Next Frame", command=lambda: self.next_frame())
        next_button.grid(row=1, column=1)
        
        continue_button = tk.Button(self.root, text="Continue", command=lambda: self.open_next_video())
        continue_button.grid(row=1, column=2)
    
    
    def prev_frame(self):
        if self.frame_num > 0:
            self.load_frame(self.frame_num - 1)
            
        
    def next_frame(self):
        self.load_frame(self.frame_num + 1)
    
        
    def load_frame(self, new_frame_num):
        print(f"Loading frame {new_frame_num}")
        self.prepare_ui()
        
        self.frame_num = new_frame_num
        
        frame = get_frame(self.video_path, self.frame_num)
        frame = cv2.resize(frame, (int(frame.shape[1] * 512 / frame.shape[0]), 512))
        
        image = ImageTk.PhotoImage(Image.fromarray(frame))
        self.image_label.configure(image=image)
        self.image_label.image = image
    
    
    def preview_impact_selection(self):
        impact_time = self.detector.detect_impact(self.video_path)
        frame_num = int(impact_time * get_fps(self.video_path))
        self.load_frame(frame_num)
        
        
    def open_next_video(self):
        self.save_impact_selection()
        self.current_video_index += 1
        print(f"Opening next video: {self.current_video_index}")
        if self.current_video_index >= len(self.video_files):
            print("No more videos to label.")
            return
        self.video_path = os.path.join(self.video_dir, self.video_files[self.current_video_index])
        self.preview_impact_selection()
        
        
    def save_impact_selection(self):
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        output_dir = os.path.join(self.output_dir, video_name)
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_file = os.path.join(output_dir, f"{video_name}.yaml")
        impact_data = {"impact_frame": self.frame_num}
        
        with open(output_file, 'w') as f:
            yaml.dump(impact_data, f)


def prepare_dataset(video_dir, output_dir):
    labeler = VideoLabeler()
    labeler.load_videos(video_dir, output_dir)
    
    
def get_fps(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    return fps


def get_frame(video_path, frame_num):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    _, frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Rotate the frame according to the transformation in the video
    transformation_matrix = cv2.getRotationMatrix2D((frame.shape[1] / 2, frame.shape[0] / 2), 180, 1)
    transformed_frame = cv2.warpAffine(frame, transformation_matrix, (frame.shape[1], frame.shape[0]))
    return transformed_frame


if __name__ == '__main__':
    video_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"

    if not os.path.exists(video_dir):
        print("The specified directory does not exist.")
        sys.exit(1)
        
    if not os.path.isdir(video_dir):
        print("The specified path is not a directory.")
        sys.exit(1)
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    prepare_dataset(video_dir, output_dir)