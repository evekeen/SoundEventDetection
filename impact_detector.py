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
        self.log_mel_features = None
        self.output = None
    

    def detect_impact(self, video_path):
        multichannel_audio = read_audio_from_video(video_path)
        log_mel_features = multichannel_complex_to_log_mel(multichannel_stft(multichannel_audio))
        self.log_mel_features = log_mel_features
        
        with torch.no_grad():
            input = torch.from_numpy(log_mel_features).to(torch.float32).to(self.device)
            output_event = self.model(input.unsqueeze(0))
        output_event = output_event.cpu()
        self.output = output_event[0]
        return self.detect_impact_time(output_event[0])
    
    
    def detect_impact_time(self, model_output):
        to_search = model_output[0:int(model_output.shape[0] / 3)]
        max_frame = torch.argmax(to_search, dim=0)[0].item()
        return max_frame / cfg.working_sample_rate * cfg.hop_size

    