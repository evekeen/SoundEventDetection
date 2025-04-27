import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export interface Task {
  id: string;
  filename: string;
  original_filename: string;
  created_at: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  impact_time_seconds: number | null;
  error_message: string | null;
  video_url: string | null;
}

export const api = {
  getTasks: async (): Promise<Task[]> => {
    const response = await axios.get(`${API_URL}/tasks`);
    return response.data;
  },

  getTask: async (taskId: string): Promise<Task> => {
    const response = await axios.get(`${API_URL}/tasks/${taskId}`);
    return response.data;
  },

  uploadVideo: async (file: File): Promise<Task> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_URL}/tasks`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  deleteTask: async (taskId: string): Promise<void> => {
    await axios.delete(`${API_URL}/tasks/${taskId}`);
  },

  getVideoUrl: (task: Task): string => {
    if (task.video_url) {
      return task.video_url;
    }
    
    return `${API_URL}/tasks/${task.id}/video`;
  }
}; 