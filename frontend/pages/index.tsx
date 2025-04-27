import TaskList from '@/components/TaskList';
import VideoUploader from '@/components/VideoUploader';
import { api, Task } from '@/utils/api';
import Head from 'next/head';
import { useEffect, useState } from 'react';

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const tasks = await api.getTasks();
      setTasks(tasks);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setError('Failed to load tasks. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  return (
    <div>
      <Head>
        <title>Sound Event Detection</title>
        <meta name="description" content="Sound Event Detection and Impact Time Analysis" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <h1 className="text-3xl font-bold mb-2">Sound Event Detection</h1>
        <p className="text-gray-600 mb-8">Upload videos to detect impact events and analyze sound</p>

        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Upload Video</h2>
          <VideoUploader onUploadSuccess={fetchTasks} />
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-4">Your Tasks</h2>
          
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : error ? (
            <div className="bg-red-100 p-4 rounded-lg text-red-700">
              <p>{error}</p>
              <button 
                onClick={fetchTasks}
                className="mt-2 text-sm text-blue-600 hover:text-blue-800"
              >
                Try again
              </button>
            </div>
          ) : (
            <TaskList tasks={tasks} onTaskDeleted={fetchTasks} />
          )}
        </div>
      </main>
    </div>
  );
} 