import VideoPlayer from '@/components/VideoPlayer';
import { api, Task } from '@/utils/api';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

export default function TaskDetail() {
  const router = useRouter();
  const { id } = router.query;
  
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  const fetchTask = async () => {
    if (!id) return;
    
    try {
      const task = await api.getTask(id as string);
      setTask(task);
      
      // If task is still processing, continue refreshing
      if (task.status === 'pending' || task.status === 'processing') {
        if (!refreshInterval) {
          const interval = setInterval(() => {
            fetchTask();
          }, 3000);
          setRefreshInterval(interval);
        }
      } else if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
      
      setError(null);
    } catch (error) {
      console.error('Error fetching task:', error);
      setError('Failed to load task details');
      if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
    } finally {
      setLoading(false);
    }
  };

  // Cleanup the interval on component unmount
  useEffect(() => {
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [refreshInterval]);

  useEffect(() => {
    if (id) {
      fetchTask();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="bg-red-100 p-6 rounded-lg text-red-700">
          <h2 className="text-xl font-bold mb-2">Error</h2>
          <p>{error || 'Task not found'}</p>
          <Link href="/" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
            ← Back to tasks
          </Link>
        </div>
      </div>
    );
  }

  const videoUrl = task.video_url || api.getVideoUrl(task);
  
  const getStatusUI = () => {
    switch (task.status) {
      case 'completed':
        return (
          <div className="py-2 px-4 bg-green-100 text-green-800 rounded-full inline-block">
            Ready
          </div>
        );
      case 'processing':
        return (
          <div className="py-2 px-4 bg-blue-100 text-blue-800 rounded-full inline-block flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-800 mr-2"></div>
            Processing video...
          </div>
        );
      case 'failed':
        return (
          <div className="py-2 px-4 bg-red-100 text-red-800 rounded-full inline-block">
            Processing failed
          </div>
        );
      default:
        return (
          <div className="py-2 px-4 bg-gray-100 text-gray-800 rounded-full inline-block">
            Pending
          </div>
        );
    }
  };

  return (
    <div>
      <Head>
        <title>{task.original_filename} - Sound Event Detection</title>
        <meta name="description" content={`Impact analysis for ${task.original_filename}`} />
      </Head>

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center">
            <Link href="/" className="text-blue-600 hover:text-blue-800">
              ← Back to tasks
            </Link>
            <span className="text-md font-bold ml-4">{task.original_filename.length > 50 ? `${task.original_filename.substring(0, 50)}...` : task.original_filename}</span>
          </div>
          {getStatusUI()}
        </div>

        {task.status === 'completed' ? (
          <VideoPlayer 
            videoUrl={videoUrl} 
            impactTimeSeconds={task.impact_time_seconds} 
          />
        ) : task.status === 'failed' ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-red-800 mb-2">Processing Error</h2>
            <p className="text-red-700">{task.error_message || 'Unknown error occurred'}</p>
          </div>
        ) : (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-blue-800 mb-2">Processing Video</h2>
            <p className="text-blue-700">
              Please wait while we analyze the video to detect impact events...
            </p>
          </div>
        )}

        <div className="mt-8 bg-gray-50 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Task Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Task ID</p>
              <p className="font-mono">{task.id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Created</p>
              <p>{new Date(task.created_at).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <p className="capitalize">{task.status}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Impact Time</p>
              <p>
                {task.impact_time_seconds !== null 
                  ? `${task.impact_time_seconds.toFixed(2)} seconds` 
                  : 'Not detected yet'}
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 