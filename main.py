import os
import torch
import requests
import tempfile
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from models.DcaseNet import DcaseNet_v3
from dataset.spectogram import spectogram_configs as cfg
from dataset.spectogram.preprocess import multichannel_stft, multichannel_complex_to_log_mel
from dataset.dataset_utils import read_audio_from_video

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model = DcaseNet_v3(1).to(device)
    checkpoint_path = os.environ.get("MODEL_CHECKPOINT", "model_checkpoint.pt")
    if not os.path.exists(checkpoint_path):
        raise RuntimeError(f"Model checkpoint not found at {checkpoint_path}")
    
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model'])
    model.eval()
    print(f"Model loaded from {checkpoint_path}")
    yield
    
app = FastAPI(lifespan=lifespan)

def detect_impact_time(model_output):
    """
    Args:
        model_output: torch.Tensor of shape (seq_len, num_classes)
    """
    max_frame = torch.argmax(model_output, dim=0)[0].item()
    return max_frame / cfg.working_sample_rate * cfg.hop_size

def download_video(url, output_path):
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to download video")
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

@app.post("/detect-impact")
async def detect_impact(video_url: str):
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        try:
            download_video(video_url, temp_file.name)
            video_path = temp_file.name
            
            multichannel_audio = read_audio_from_video(video_path=video_path)
            log_mel_features = multichannel_complex_to_log_mel(multichannel_stft(multichannel_audio))
            
            with torch.no_grad():
                input_tensor = torch.from_numpy(log_mel_features).to(torch.float32).to(device)
                output_event = model(input_tensor.unsqueeze(0))
            output_event = output_event.cpu()
            
            impact_time = detect_impact_time(output_event[0])
            
            return {
                "impact_time_seconds": float(impact_time),
            }
        finally:
            os.unlink(temp_file.name)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080))) 