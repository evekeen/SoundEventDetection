from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_filename: str
    created_at: datetime = Field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    impact_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    video_url: Optional[str] = None
    
class TaskCreate(BaseModel):
    filename: str
    original_filename: str
    video_url: Optional[str] = None
    
class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    impact_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    video_url: Optional[str] = None 