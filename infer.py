import argparse
import os
import torch
from models.DcaseNet import DcaseNet_v3
from models.spectogram_models import *
from dataset.spectogram import spectogram_configs as cfg
from dataset.spectogram.preprocess import multichannel_stft, multichannel_complex_to_log_mel
from dataset.dataset_utils import read_audio_from_video, read_multichannel_audio
from utils.plot_utils import plot_sample_features

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Example of parser. ')

    # Train
    parser.add_argument('audio_file', type=str)
    parser.add_argument('--ckpt', type=str, required=True)
    parser.add_argument('--outputs_dir', type=str, default='inference_outputs', help='Directory of your workspace.')
    parser.add_argument('--device', default='cuda:0', type=str)
    args = parser.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() and args.device == "cuda:0" else "cpu")

    # model = Cnn_AvgPooling(cfg.classes_num, model_config=[(32,2), (64,2), (128,2), (128,1)]).to(device)
    model = DcaseNet_v3(1).to(device)
    checkpoint = torch.load(args.ckpt, map_location=device)
    model.load_state_dict(checkpoint['model'])

    print("Preprocessing audio file..")
    input_path = args.audio_file
    multichannel_audio = None

    if input_path.endswith('.wav'):
        multichannel_audio = read_multichannel_audio(audio_path=input_path, target_fs=cfg.working_sample_rate)
    elif input_path.endswith('.mov') or input_path.endswith('.mp4'):
        multichannel_audio = read_audio_from_video(video_path=input_path)

    log_mel_features = multichannel_complex_to_log_mel(multichannel_stft(multichannel_audio))
    
    # cropped = log_mel_features[:, :cfg.train_crop_size, :]

    print("Inference..")
    with torch.no_grad():
        input = torch.from_numpy(log_mel_features).to(torch.float32).to(device)
        output_event = model(input.unsqueeze(0))
    output_event = output_event.cpu()
    os.makedirs(args.outputs_dir, exist_ok=True)
    print(input.shape, output_event.shape)
    plot_sample_features(log_mel_features,
                         mode='Spectrogram', 
                         output=output_event[0], 
                         plot_path=os.path.join(args.outputs_dir, f"{os.path.splitext(os.path.basename(args.audio_file))[0]}.png")
                         )