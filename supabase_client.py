import os
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from dotenv import load_dotenv
import datetime
import json

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Get bucket name from environment or use default
BUCKET_NAME = os.getenv("BUCKET_NAME")

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)

class SupabaseClient:
    def __init__(self):
        if not SUPABASE_URL:
            error_msg = "Supabase URL not found in environment variables"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not SUPABASE_KEY:
            error_msg = "Supabase key not found in environment variables"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Log configuration details for debugging
        logger.info(f"Supabase URL: {SUPABASE_URL}")
        logger.info(f"Using bucket name: {BUCKET_NAME}")
        
        if SUPABASE_KEY:
            # Show only first and last few characters of the key for security
            key_preview = f"{SUPABASE_KEY[:5]}...{SUPABASE_KEY[-5:]}" if len(SUPABASE_KEY) > 10 else "Invalid key format"
            logger.info(f"Supabase key format: {key_preview}")
        
        if SUPABASE_SERVICE_KEY:
            # Show only first and last few characters of the key for security
            service_key_preview = f"{SUPABASE_SERVICE_KEY[:5]}...{SUPABASE_SERVICE_KEY[-5:]}" if len(SUPABASE_SERVICE_KEY) > 10 else "Invalid key format"
            logger.info(f"Supabase service key format: {service_key_preview}")
        else:
            logger.warning("Supabase service key is not set")
        
        try:
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase client initialized successfully")
            
            if SUPABASE_SERVICE_KEY:
                self.service_client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
                logger.info("Supabase service client initialized successfully")
            else:
                self.service_client = None
                logger.warning("Supabase service key not found, some operations may be restricted")
        except Exception as e:
            error_msg = f"Failed to initialize Supabase client: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    # Task Database Operations
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task in the database"""
        try:
            # Serialize datetime objects to ISO format strings
            serialized_data = {}
            for key, value in task_data.items():
                if isinstance(value, (datetime.datetime, datetime.date)):
                    serialized_data[key] = value.isoformat()
                else:
                    serialized_data[key] = value
            
            response = self.client.table("tasks").insert(serialized_data).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Task created with ID: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise RuntimeError("No data returned from task creation")
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            raise
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID"""
        try:
            response = self.client.table("tasks").select("*").eq("id", task_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {str(e)}")
            raise
    
    def update_task(self, task_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a task by ID"""
        try:
            # Serialize datetime objects to ISO format strings
            serialized_data = {}
            for key, value in update_data.items():
                if isinstance(value, (datetime.datetime, datetime.date)):
                    serialized_data[key] = value.isoformat()
                else:
                    serialized_data[key] = value
            
            response = self.client.table("tasks").update(serialized_data).eq("id", task_id).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Task {task_id} updated successfully")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {str(e)}")
            raise
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID"""
        try:
            response = self.client.table("tasks").delete().eq("id", task_id).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Task {task_id} deleted successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {str(e)}")
            raise
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks"""
        try:
            response = self.client.table("tasks").select("*").order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to list tasks: {str(e)}")
            raise
    
    # Storage Operations
    def upload_video(self, file_path: str, file_name: str) -> str:
        """
        Upload a video file to Supabase Storage
        Returns the public URL of the uploaded file
        """
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Use service client for upload if available
            client_to_use = self.service_client if self.service_client else self.client
            logger.info(f"Using {'service role' if self.service_client else 'public'} client for upload")
            logger.info(f"Uploading to bucket: {BUCKET_NAME}, file: {file_name}")
            
            # Try upload with bucket name
            bucket = BUCKET_NAME.strip()
            response = client_to_use.storage.from_(bucket).upload(
                path=file_name,
                file=file_content,
                file_options={"content-type": "video/mov"}
            )
            
            # Get public URL with the same bucket name
            file_url = self.client.storage.from_(bucket).get_public_url(file_name)
            
            logger.info(f"Video uploaded successfully: {file_url}")
            return file_url
        except Exception as e:
            logger.error(f"Failed to upload video: {str(e)}")
            # Add more detailed error info if possible
            if hasattr(e, 'args') and e.args:
                logger.error(f"Error details: {e.args}")
            raise
    
    def get_video_url(self, file_name: str) -> str:
        """Get the public URL for a video file"""
        try:
            return self.client.storage.from_(BUCKET_NAME).get_public_url(file_name)
        except Exception as e:
            logger.error(f"Failed to get video URL for {file_name}: {str(e)}")
            raise
    
    def delete_video(self, file_name: str) -> bool:
        """Delete a video file from storage"""
        try:
            response = self.client.storage.from_(BUCKET_NAME).remove([file_name])
            logger.info(f"Video {file_name} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete video {file_name}: {str(e)}")
            raise

# Create a singleton instance
supabase = SupabaseClient() 