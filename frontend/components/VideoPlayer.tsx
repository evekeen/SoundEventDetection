import { useEffect, useRef, useState } from 'react';
import ReactPlayer from 'react-player';

interface VideoPlayerProps {
  videoUrl: string;
  impactTimeSeconds: number | null;
}

export default function VideoPlayer({ videoUrl, impactTimeSeconds }: VideoPlayerProps) {
  const playerRef = useRef<ReactPlayer>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const [duration, setDuration] = useState<number>(0);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [currentFrameImage, setCurrentFrameImage] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewPosition, setPreviewPosition] = useState({ x: 0, time: 0 });
  const [fps, setFps] = useState(24);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isVideoError, setIsVideoError] = useState(false);

  // Function to capture frames from video
  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) {
      console.error("Video or canvas ref not available");
      return null;
    }
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      console.error("Could not get canvas context");
      return null;
    }
    
    // Only capture if video has dimensions and is ready
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      console.error("Video dimensions not available", video.videoWidth, video.videoHeight);
      return null;
    }
    
    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Capture the current frame
    try {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      return canvas.toDataURL('image/jpeg', 0.9);
    } catch (e) {
      console.error("Error capturing frame:", e);
      return null;
    }
  };
  
  // Handle when video is ready
  const handleVideoLoaded = () => {
    console.log("Video loaded event fired");
    setIsLoaded(true);
    
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
      
      // If we have an impact time, seek to it
      if (impactTimeSeconds !== null) {
        handleSeek(impactTimeSeconds);
      } else {
        // Otherwise capture the current frame
        const frame = captureFrame();
        if (frame) {
          setCurrentFrameImage(frame);
        }
      }
    }
  };
  
  // Handle seeking in the video
  const handleSeek = (time: number) => {
    if (!videoRef.current) return;
    
    console.log("Seeking to time:", time);
    // Pause while seeking
    setPlaying(false);
    
    // Update current time and seek video
    setCurrentTime(time);
    videoRef.current.currentTime = time;
  };
  
  // Handle timeupdate event to capture frames
  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    
    setCurrentTime(videoRef.current.currentTime);
    
    // Capture the current frame
    const frame = captureFrame();
    if (frame) {
      setCurrentFrameImage(frame);
    }
  };
  
  // Handle video error
  const handleVideoError = () => {
    console.error("Video error occurred");
    setIsVideoError(true);
  };
  
  // Handle play/pause
  const togglePlay = () => {
    if (!videoRef.current) return;
    
    if (playing) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    
    setPlaying(!playing);
  };
  
  // Format time for display
  const formatTime = (timeInSeconds: number) => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Mouse event handlers for timeline
  const handleTimelineMouseDown = (e: React.MouseEvent) => {
    if (!timelineRef.current || duration <= 0) return;
    
    setIsDragging(true);
    const rect = timelineRef.current.getBoundingClientRect();
    const position = (e.clientX - rect.left) / rect.width;
    const newTime = position * duration;
    handleSeek(newTime);
  };

  // Handle document-level mouse events for smooth dragging
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !timelineRef.current || duration <= 0) return;
      
      const rect = timelineRef.current.getBoundingClientRect();
      const position = Math.max(0, Math.min((e.clientX - rect.left) / rect.width, 1));
      const newTime = position * duration;
      handleSeek(newTime);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, duration]);

  const handleTimelineMouseMove = (e: React.MouseEvent) => {
    if (!timelineRef.current || duration <= 0) return;
    
    const rect = timelineRef.current.getBoundingClientRect();
    const position = (e.clientX - rect.left) / rect.width;
    const previewTime = Math.max(0, Math.min(position * duration, duration));
    
    setPreviewPosition({ 
      x: e.clientX - rect.left, 
      time: previewTime 
    });
    
    if (!isDragging) {
      setShowPreview(true);
    }
  };

  const handleTimelineMouseLeave = () => {
    if (!isDragging) {
      setShowPreview(false);
    }
  };

  // Calculate current frame number
  const getCurrentFrameNumber = () => {
    return Math.round(currentTime * fps);
  };

  const handleFrameStep = (steps: number) => {
    const newTime = Math.max(0, Math.min(duration, currentTime + (steps / fps)));
    handleSeek(newTime);
  };

  // Effect to seek to impact time when it changes
  useEffect(() => {
    if (impactTimeSeconds !== null && isLoaded && videoRef.current) {
      handleSeek(impactTimeSeconds);
    }
  }, [impactTimeSeconds, isLoaded, videoUrl]);

  // Current frame number calculated from time
  const currentFrameNumber = getCurrentFrameNumber();
  const totalFrames = Math.round(duration * fps);

  // Frame displays
  const frameDisplay = currentFrameNumber > 0 ? `Frame ${currentFrameNumber}/${totalFrames}` : '';

  return (
    <div className="w-full">
      {/* Current Frame Preview */}
      <div className="w-full bg-black rounded-lg overflow-hidden mb-4 relative" style={{ maxHeight: '400px' }}>
        {currentFrameImage ? (
          <>
            <img src={currentFrameImage} alt="Current frame" className="w-full h-auto max-h-[400px] object-contain mx-auto" />
            <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-sm px-2 py-1 rounded">
              {formatTime(currentTime)} {frameDisplay && `(${frameDisplay})`}
            </div>
          </>
        ) : (
          <div className="w-full h-[400px] flex items-center justify-center text-gray-400">
            No frame captured yet
          </div>
        )}
      </div>
      
      {/* Timeline */}
      {duration > 0 && (
        <div className="mb-4">
          <div 
            ref={timelineRef}
            className="relative w-full h-8 bg-gray-200 rounded-full cursor-pointer"
            onMouseDown={handleTimelineMouseDown}
            onMouseMove={handleTimelineMouseMove}
            onMouseLeave={handleTimelineMouseLeave}
          >
            {/* Timeline background with segments */}
            <div className="absolute inset-0 flex">
              {Array.from({ length: 10 }).map((_, i) => (
                <div 
                  key={i} 
                  className="h-full flex-1 border-r border-gray-300 last:border-r-0"
                />
              ))}
            </div>
            
            {/* Impact marker */}
            {impactTimeSeconds !== null && (
              <div 
                className="absolute w-1.5 h-10 bg-red-500 transform -translate-y-1 rounded-full cursor-pointer z-20"
                style={{ left: `${(impactTimeSeconds / duration) * 100}%` }}
                onClick={() => handleSeek(impactTimeSeconds)}
                title={`Impact at ${formatTime(impactTimeSeconds)}`}
              >
                <div className="w-3 h-3 bg-red-500 rounded-full absolute -top-2 -left-1"></div>
              </div>
            )}
            
            {/* Timeline scrubber */}
            <div 
              className="absolute h-full bg-blue-500 rounded-l-full z-10" 
              style={{ width: `${(currentTime / duration) * 100}%` }}
            />
            
            {/* Timeline handle */}
            <div 
              className="absolute w-4 h-4 bg-white border-2 border-blue-600 rounded-full transform -translate-x-1/2 -translate-y-1/2 top-1/2 z-30"
              style={{ left: `${(currentTime / duration) * 100}%` }}
            />
            
            {/* Preview tooltip */}
            {showPreview && (
              <div 
                className="absolute bottom-full mb-2 transform -translate-x-1/2 z-40 pointer-events-none"
                style={{ left: previewPosition.x }}
              >
                <div className="bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                  {formatTime(previewPosition.time)}
                </div>
              </div>
            )}
          </div>
          
          <div className="flex justify-between mt-1 text-xs text-gray-600">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>
      )}
      
      {/* Frame Navigation Controls */}
      <div className="flex items-center justify-center gap-2 mb-6 flex-wrap">
        <button 
          className="px-2 py-1 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition flex items-center"
          onClick={() => handleFrameStep(-10)}
          title="Jump back 10 frames"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M8.445 14.832A1 1 0 0010 14v-2.798l5.445 3.63A1 1 0 0017 14V6a1 1 0 00-1.555-.832L10 8.798V6a1 1 0 00-1.555-.832l-6 4a1 1 0 000 1.664l6 4z" />
          </svg>
        </button>
        
        <button 
          className="px-2 py-1 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition flex items-center"
          onClick={() => handleFrameStep(-1)}
          title="Previous frame"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </button>
        
        <div className="px-3 py-1 bg-gray-100 text-gray-800 rounded-md text-sm">
          {frameDisplay || 'Frame 0/0'}
        </div>
        
        <button 
          className="px-2 py-1 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition flex items-center"
          onClick={() => handleFrameStep(1)}
          title="Next frame"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
        </button>
        
        <button 
          className="px-2 py-1 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition flex items-center"
          onClick={() => handleFrameStep(10)}
          title="Jump forward 10 frames"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M4.555 5.168A1 1 0 003 6v8a1 1 0 001.555.832L10 11.202V14a1 1 0 001.555.832l6-4a1 1 0 000-1.664l-6-4A1 1 0 0010 6v2.798l-5.445-3.63z" />
          </svg>
        </button>
        
        <div className="w-full flex justify-center mt-2">
          <button 
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition mx-2"
            onClick={togglePlay}
          >
            {playing ? 'Pause' : 'Play'}
          </button>
          
          {impactTimeSeconds !== null && (
            <button 
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition mx-2"
              onClick={() => handleSeek(impactTimeSeconds)}
            >
              Jump to Impact
            </button>
          )}
        </div>
      </div>
      
      {/* Hidden, but functional video player */}
      <div style={{ position: 'absolute', opacity: 0, pointerEvents: 'none', width: '1px', height: '1px', overflow: 'hidden' }}>
        <video
          ref={videoRef}
          src={videoUrl}
          crossOrigin="anonymous"
          preload="auto"
          width="640"
          height="360"
          onLoadedData={handleVideoLoaded}
          onTimeUpdate={handleTimeUpdate}
          onError={handleVideoError}
        />
      </div>
      
      <canvas ref={canvasRef} style={{ display: 'none' }} width="640" height="360" />
    </div>
  );
} 