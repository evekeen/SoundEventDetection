import os
import logging
from pydantic import BaseModel
import torch
import requests
import tempfile
import shutil
from fastapi import FastAPI, HTTPException, status, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from models.DcaseNet import DcaseNet_v3
from dataset.spectogram import spectogram_configs as cfg
from dataset.spectogram.preprocess import multichannel_stft, multichannel_complex_to_log_mel
from dataset.dataset_utils import read_audio_from_video
from typing import Optional, List
from models.task_models import Task, TaskCreate, TaskUpdate, TaskStatus
from database import task_db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

# Mount uploads directory for serving video files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

class ImpactDetectionRequest(BaseModel):
    video_url: Optional[str] = None

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

async def process_video_task(task_id: str):
    task = task_db.get_task(task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return
    
    # Update task status to processing
    task_db.update_task(task_id, TaskUpdate(status=TaskStatus.PROCESSING))
    
    try:
        # Create a temporary file to download the video
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            video_path = temp_file.name
            try:
                # Download video from Supabase URL
                download_video(task.video_url, video_path)
                
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
                
                # Update task with results
                task_db.update_task(task_id, TaskUpdate(
                    status=TaskStatus.COMPLETED,
                    impact_time_seconds=float(impact_time)
                ))
            except Exception as e:
                error_msg = f"Error processing video: {str(e)}"
                logger.error(error_msg)
                # Update task with error
                task_db.update_task(task_id, TaskUpdate(
                    status=TaskStatus.FAILED,
                    error_message=error_msg
                ))
            finally:
                try:
                    os.unlink(video_path)
                    logger.debug(f"Temporary file deleted: {video_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {video_path}: {str(e)}")
    except Exception as e:
        error_msg = f"Error in task processing: {str(e)}"
        logger.error(error_msg)
        # Update task with error
        task_db.update_task(task_id, TaskUpdate(
            status=TaskStatus.FAILED,
            error_message=error_msg
        ))

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )
    
@app.post("/detect-impact")
async def detect_impact(impact_detection_request: ImpactDetectionRequest):
    return await detect_impact_direct(impact_detection_request=impact_detection_request, file=None)

@app.post("/detect-impact-file")
async def detect_impact_file(file: UploadFile = File(...)):
    return await detect_impact_direct(impact_detection_request=None, file=file)

async def detect_impact_direct(impact_detection_request: Optional[ImpactDetectionRequest] = None, 
                               file: Optional[UploadFile] = None):
    """
    Direct detection without task creation - legacy endpoint
    """
    logger.info("Processing direct impact detection request")
    
    if not impact_detection_request and not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Either video_url or file upload is required"
        )
    
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        try:
            if impact_detection_request and impact_detection_request.video_url:
                video_url = impact_detection_request.video_url
                logger.info(f"Using URL: {video_url}")
                download_video(video_url, temp_file.name)
            elif file:
                logger.info(f"Using uploaded file: {file.filename}")
                content = await file.read()
                with open(temp_file.name, 'wb') as f:
                    f.write(content)
            
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

@app.post("/tasks", response_model=Task)
async def create_task(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    logger.info(f"Creating new task for file: {file.filename}")
    
    # Create unique filename
    original_filename = file.filename
    file_extension = os.path.splitext(original_filename)[1].lower()
    if not file_extension or file_extension not in ['.mp4', '.mov', '.avi', '.mkv']:
        file_extension = '.mp4'  # Default to mp4 if no valid extension
        
    filename = f"{os.path.splitext(original_filename)[0]}_{os.urandom(4).hex()}{file_extension}"
    
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            try:
                # Save the uploaded file to temp location
                await file.seek(0)
                content = await file.read()
                temp_file.write(content)
                temp_file.flush()
                
                # Upload to Supabase storage
                video_url = task_db.upload_video(temp_file.name, filename)
                
                # Create task with the Supabase storage URL
                task = Task(
                    filename=filename,
                    original_filename=original_filename,
                    video_url=video_url
                )
                task = task_db.create_task(task)
                
                # Process video in background
                background_tasks.add_task(process_video_task, task.id)
                
                return task
            finally:
                try:
                    os.unlink(temp_file.name)
                    logger.debug(f"Temporary file deleted: {temp_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file.name}: {str(e)}")
    except Exception as e:
        error_msg = f"Error creating task: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)

@app.get("/tasks", response_model=List[Task])
async def list_tasks():
    return task_db.list_tasks()

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = task_db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    task = task_db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    # Delete task and associated video
    if task_db.delete_task(task_id):
        return {"message": "Task deleted successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete task")

@app.get("/tasks/{task_id}/video")
async def get_task_video(task_id: str):
    task = task_db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    if not task.video_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video URL not found for this task")
    
    # Redirect to the Supabase storage URL
    return RedirectResponse(url=task.video_url)

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