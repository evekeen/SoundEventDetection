import { useEffect, useRef, useState } from 'react';
import ReactPlayer from 'react-player';

interface VideoPlayerProps {
  videoUrl: string;
  impactTimeSeconds: number | null;
}

export default function VideoPlayer({ videoUrl, impactTimeSeconds }: VideoPlayerProps) {
  const playerRef = useRef<ReactPlayer>(null);
  const [duration, setDuration] = useState<number>(0);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [impactFrame, setImpactFrame] = useState<string | null>(null);

  // Function to capture the impact frame
  const captureImpactFrame = async () => {
    if (!impactTimeSeconds || !playerRef.current) return;
    
    // First pause and seek to impact time
    setPlaying(false);
    playerRef.current.seekTo(impactTimeSeconds, 'seconds');
    
    // Wait a bit for the video to update
    setTimeout(() => {
      // This is a simplified approach - in a real app, you'd use a 
      // canvas to capture the actual frame
      setImpactFrame(videoUrl);
    }, 500);
  };

  useEffect(() => {
    if (impactTimeSeconds !== null && playerRef.current) {
      captureImpactFrame();
    }
  }, [impactTimeSeconds, videoUrl]);

  const handleDuration = (duration: number) => {
    setDuration(duration);
  };

  const handleProgress = (state: { played: number; playedSeconds: number }) => {
    setCurrentTime(state.playedSeconds);
  };

  const handleSeek = (time: number) => {
    if (playerRef.current) {
      playerRef.current.seekTo(time, 'seconds');
    }
  };

  const formatTime = (timeInSeconds: number) => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full">
      <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
        <ReactPlayer
          ref={playerRef}
          url={videoUrl}
          width="100%"
          height="100%"
          playing={playing}
          controls={true}
          onDuration={handleDuration}
          onProgress={handleProgress}
          config={{
            file: {
              attributes: {
                crossOrigin: "anonymous"
              }
            }
          }}
        />
      </div>
      
      {duration > 0 && (
        <div className="mt-4">
          <div className="relative w-full h-6 bg-gray-200 rounded-full">
            {/* Impact marker */}
            {impactTimeSeconds !== null && (
              <div 
                className="absolute w-1 h-8 bg-red-500 transform -translate-y-1 rounded-full cursor-pointer"
                style={{ left: `${(impactTimeSeconds / duration) * 100}%` }}
                onClick={() => handleSeek(impactTimeSeconds)}
                title={`Impact at ${formatTime(impactTimeSeconds)}`}
              />
            )}
            
            {/* Timeline scrubber */}
            <div 
              className="h-full bg-gray-400 rounded-full" 
              style={{ width: `${(currentTime / duration) * 100}%` }}
            />
          </div>
          
          <div className="flex justify-between mt-1 text-xs text-gray-600">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>
      )}
      
      {impactTimeSeconds !== null && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-2">Impact Detected</h3>
          <p className="text-sm text-gray-600 mb-3">
            Impact detected at {formatTime(impactTimeSeconds)} 
            ({impactTimeSeconds.toFixed(2)} seconds)
          </p>
          
          <div className="flex gap-4">
            <button 
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
              onClick={() => handleSeek(impactTimeSeconds)}
            >
              Jump to Impact
            </button>
            
            <button 
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition"
              onClick={captureImpactFrame}
            >
              Recapture Impact Frame
            </button>
          </div>
          
          {impactFrame && (
            <div className="mt-4">
              <h4 className="text-md font-medium mb-2">Impact Frame</h4>
              <div className="w-full max-w-md aspect-video bg-black rounded-lg overflow-hidden">
                <img src={impactFrame} alt="Impact moment" className="w-full h-full object-contain" />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
} 