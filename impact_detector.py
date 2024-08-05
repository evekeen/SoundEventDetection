import torch
from models.DcaseNet import DcaseNet_v3
from models.spectogram_models import *
from dataset.spectogram import spectogram_configs as cfg
from dataset.spectogram.preprocess import multichannel_stft, multichannel_complex_to_log_mel
from dataset.dataset_utils import read_audio_from_video


class ImpactDetector:
    def __init__(self, ckpt_path):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = DcaseNet_v3(1).to(self.device)
        checkpoint = torch.load(ckpt_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model'])
    

    def detect_impact(self, video_path):
        multichannel_audio = read_audio_from_video(video_path)
        log_mel_features = multichannel_complex_to_log_mel(multichannel_stft(multichannel_audio))
        
        with torch.no_grad():
            input = torch.from_numpy(log_mel_features).to(torch.float32).to(self.device)
            output_event = self.model(input.unsqueeze(0))
        output_event = output_event.cpu()
        return self.detect_impact_time(output_event[0])
    
    
    def detect_impact_time(self, model_output):
        max_frame = torch.argmax(model_output, dim=0)[0].item()
        return max_frame / cfg.working_sample_rate * cfg.hop_size

    