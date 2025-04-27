import os
import logging
from pydantic import BaseModel
import torch
import requests
import tempfile
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models.DcaseNet import DcaseNet_v3
from dataset.spectogram import spectogram_configs as cfg
from dataset.spectogram.preprocess import multichannel_stft, multichannel_complex_to_log_mel
from dataset.dataset_utils import read_audio_from_video

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {device}")
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    try:
        model = DcaseNet_v3(1).to(device)
        checkpoint_path = os.environ.get("MODEL_CHECKPOINT", "model_checkpoint.pt")
        if not os.path.exists(checkpoint_path):
            error_msg = f"Model checkpoint not found at {checkpoint_path}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model'])
        model.eval()
        logger.info(f"Model loaded successfully from {checkpoint_path}")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise
    yield
    logger.info("Application shutting down")
    
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImpactDetectionRequest(BaseModel):
    video_url: str

def detect_impact_time(model_output):
    """
    Args:
        model_output: torch.Tensor of shape (seq_len, num_classes)
    """
    try:
        max_frame = torch.argmax(model_output, dim=0)[0].item()
        return max_frame / cfg.working_sample_rate * cfg.hop_size
    except Exception as e:
        logger.error(f"Error in detect_impact_time: {str(e)}")
        raise

def download_video(url, output_path):
    try:
        logger.info(f"Downloading video from {url}")
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code != 200:
            error_msg = f"Failed to download video: status code {response.status_code}"
            logger.error(error_msg)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Video downloaded successfully to {output_path}")
    except requests.RequestException as e:
        error_msg = f"Error downloading video: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

@app.post("/detect-impact")
async def detect_impact(impact_detection_request: ImpactDetectionRequest):
    video_url = impact_detection_request.video_url
    logger.info(f"Processing impact detection request for URL: {video_url}")
    
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        try:
            download_video(video_url, temp_file.name)
            video_path = temp_file.name
            
            try:
                logger.debug(f"Reading audio from video: {video_path}")
                multichannel_audio = read_audio_from_video(video_path=video_path)
                
                logger.debug("Extracting log-mel features")
                log_mel_features = multichannel_complex_to_log_mel(multichannel_stft(multichannel_audio))
                
                logger.debug("Running inference")
                with torch.no_grad():
                    input_tensor = torch.from_numpy(log_mel_features).to(torch.float32).to(device)
                    output_event = model(input_tensor.unsqueeze(0))
                output_event = output_event.cpu()
                
                impact_time = detect_impact_time(output_event[0])
                logger.debug(f"Impact detected at time: {impact_time} seconds")
                
                return {
                    "impact_time_seconds": float(impact_time),
                    "status": "success"
                }
            except Exception as e:
                error_msg = f"Error processing video: {str(e)}"
                logger.error(error_msg)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)
        except Exception as e:
            logger.error(f"Error in detect_impact endpoint: {str(e)}")
            raise
        finally:
            try:
                os.unlink(temp_file.name)
                logger.debug(f"Temporary file deleted: {temp_file.name}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file.name}: {str(e)}")

@app.get("/health")
async def health_check():
    if model is None:
        logger.error("Health check failed: Model not loaded")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "message": "Model not loaded"}
        )
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port) 