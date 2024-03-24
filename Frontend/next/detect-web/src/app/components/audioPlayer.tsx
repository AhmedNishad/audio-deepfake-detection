import { useState, useRef } from 'react';
import { PlayIcon, PauseIcon } from '@heroicons/react/solid'; // Import icons from Heroicons

interface AudioPlayerProps {
  url: string;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ url }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const togglePlay = () => {
    if (audioRef.current?.paused) {
      audioRef.current?.play();
      setIsPlaying(true);
    } else {
      audioRef.current?.pause();
      setIsPlaying(false);
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
  };

  return (
    <div className="audio-player flex items-center">
      <audio ref={audioRef} src={url} onEnded={handleEnded} className="mr-4" />
      <button className="play-button bg-black text-white py-2 px-4 rounded-md" onClick={togglePlay}>
        {isPlaying ? (
          <PauseIcon className="h-6 w-6 text-white" /> // Use the PauseIcon when playing
        ) : (
          <PlayIcon className="h-6 w-6 text-white" /> // Use the PlayIcon when not playing
        )}
      </button>
    </div>
  );
};

export default AudioPlayer;
