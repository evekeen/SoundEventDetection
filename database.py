import os
import logging
from typing import Dict, List, Optional, Any
from models.task_models import Task, TaskUpdate, TaskStatus
from supabase_client import supabase

logger = logging.getLogger(__name__)

class TaskDatabase:
    def __init__(self):
        self.supabase = supabase
        logger.info("Task database initialized with Supabase")
        
    def create_task(self, task: Task) -> Task:
        """Create a new task in the database"""
        try:
            # Convert Task to dict for Supabase
            task_dict = task.dict()
            
            # Adjust any data types if needed
            task_dict["status"] = task.status.value
            
            # Create task in Supabase
            result = self.supabase.create_task(task_dict)
            
            # Convert back to our Task model
            created_task = Task.parse_obj(result)
            logger.info(f"Task created with ID: {created_task.id}")
            
            return created_task
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            raise
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        try:
            result = self.supabase.get_task(task_id)
            if result:
                # Convert status string back to enum
                if isinstance(result["status"], str):
                    result["status"] = TaskStatus(result["status"])
                return Task.parse_obj(result)
            return None
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {str(e)}")
            raise
    
    def update_task(self, task_id: str, update_data: TaskUpdate) -> Optional[Task]:
        """Update a task by ID"""
        try:
            # Convert update data to dict, excluding unset values
            update_dict = update_data.dict(exclude_unset=True)
            
            # If status is set, convert enum to string
            if "status" in update_dict and update_dict["status"]:
                update_dict["status"] = update_dict["status"].value
            
            # Update in Supabase
            result = self.supabase.update_task(task_id, update_dict)
            
            if result:
                # Convert status string back to enum for our model
                if isinstance(result["status"], str):
                    result["status"] = TaskStatus(result["status"])
                return Task.parse_obj(result)
            
            return None
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {str(e)}")
            raise
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID"""
        try:
            # First, get the task to check if we need to delete a video file
            task = self.get_task(task_id)
            if task and task.filename:
                try:
                    # Try to delete the associated video file
                    self.supabase.delete_video(task.filename)
                except Exception as video_error:
                    logger.warning(f"Failed to delete video for task {task_id}: {str(video_error)}")
            
            # Delete the task
            return self.supabase.delete_task(task_id)
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {str(e)}")
            raise
    
    def list_tasks(self) -> List[Task]:
        """List all tasks"""
        try:
            results = self.supabase.list_tasks()
            tasks = []
            
            for task_data in results:
                # Convert status string back to enum
                if isinstance(task_data["status"], str):
                    task_data["status"] = TaskStatus(task_data["status"])
                
                tasks.append(Task.parse_obj(task_data))
            
            return tasks
        except Exception as e:
            logger.error(f"Failed to list tasks: {str(e)}")
            raise
    
    def upload_video(self, file_path: str, file_name: str) -> str:
        """Upload a video to Supabase Storage and return the URL"""
        try:
            return self.supabase.upload_video(file_path, file_name)
        except Exception as e:
            logger.error(f"Failed to upload video: {str(e)}")
            raise
    
    def get_video_url(self, file_name: str) -> str:
        """Get the URL for a video file"""
        try:
            return self.supabase.get_video_url(file_name)
        except Exception as e:
            logger.error(f"Failed to get video URL: {str(e)}")
            raise

# Create a singleton instance
task_db = TaskDatabase() 