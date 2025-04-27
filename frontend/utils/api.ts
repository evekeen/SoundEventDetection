import axios from 'axios';
import { supabase } from './supabase';

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

// Create an axios instance that includes the auth token
const apiClient = axios.create({
  baseURL: API_URL,
});

// Add an interceptor to add the auth token to each request
apiClient.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const session = data.session;
  
  if (session) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  
  return config;
});

export const api = {
  getTasks: async (): Promise<Task[]> => {
    const response = await apiClient.get('/tasks');
    return response.data;
  },

  getTask: async (taskId: string): Promise<Task> => {
    const response = await apiClient.get(`/tasks/${taskId}`);
    return response.data;
  },

  uploadVideo: async (file: File): Promise<Task> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/tasks', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  deleteTask: async (taskId: string): Promise<void> => {
    await apiClient.delete(`/tasks/${taskId}`);
  },

  getVideoUrl: (task: Task): string => {
    if (task.video_url) {
      return task.video_url;
    }
    
    return `${API_URL}/tasks/${task.id}/video`;
  }
}; 