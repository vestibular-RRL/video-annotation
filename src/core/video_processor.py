"""
Video Processor
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from pathlib import Path


class VideoProcessor:
    """Handles video file operations using OpenCV"""
    
    def __init__(self):
        self.cap = None
        self.file_path = None
        self.width = 0
        self.height = 0
        self.fps = 0.0
        self.frame_count = 0
        self.duration = 0.0
        self.current_frame_number = 0
        self.frame_cache = {}  # Cache for recently accessed frames
        self.cache_size = 50  # Reduced cache size for better performance
        self.sequential_mode = False  # Track if we're reading sequentially
    
    def load_video(self, file_path: str) -> bool:
        """Load a video file"""
        try:
            # Close any existing video
            self.close()
            
            # Open video file with software decoding (no hardware acceleration)
            self.cap = cv2.VideoCapture(file_path, cv2.CAP_FFMPEG)
            
            # Explicitly disable hardware acceleration
            self.cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_NONE)
            
            if not self.cap.isOpened():
                return False
            
            # Extract video properties
            self.file_path = file_path
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.duration = self.frame_count / self.fps if self.fps > 0 else 0.0
            
            # Set initial frame
            self.current_frame_number = 1
            self.sequential_mode = False
            
            # Clear frame cache
            self.frame_cache.clear()
            
            return True
            
        except Exception as e:
            print(f"Error loading video: {e}")
            return False
    
    def get_frame(self, frame_number: int) -> Optional[np.ndarray]:
        """Get a specific frame from the video"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        if frame_number < 1 or frame_number > self.frame_count:
            return None
        
        # Check if frame is in cache
        if frame_number in self.frame_cache:
            return self.frame_cache[frame_number]
        
        try:
            # Check if we can read sequentially (next frame)
            if self.sequential_mode and frame_number == self.current_frame_number + 1:
                # Read next frame sequentially (much faster)
                ret, frame = self.cap.read()
                if ret:
                    self.current_frame_number = frame_number
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self._cache_frame(frame_number, rgb_frame)
                    return rgb_frame
                else:
                    # End of video reached
                    self.sequential_mode = False
                    return None
            
            # Need to seek to specific frame
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
            ret, frame = self.cap.read()
            
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.current_frame_number = frame_number
                self.sequential_mode = True  # Enable sequential mode
                
                # Cache the frame
                self._cache_frame(frame_number, rgb_frame)
                
                return rgb_frame
            else:
                return None
                
        except Exception as e:
            print(f"Error getting frame {frame_number}: {e}")
            return None
    
    def get_next_frame(self) -> Optional[np.ndarray]:
        """Get the next frame sequentially (optimized for playback)"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        if self.current_frame_number >= self.frame_count:
            return None
        
        try:
            # Read next frame sequentially
            ret, frame = self.cap.read()
            if ret:
                self.current_frame_number += 1
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self._cache_frame(self.current_frame_number, rgb_frame)
                return rgb_frame
            else:
                return None
        except Exception as e:
            print(f"Error getting next frame: {e}")
            return None
    
    def _cache_frame(self, frame_number: int, frame: np.ndarray):
        """Cache a frame"""
        # Add frame to cache
        self.frame_cache[frame_number] = frame
        
        # If cache is too large, remove oldest frames
        if len(self.frame_cache) > self.cache_size:
            # Remove oldest frames (simple FIFO)
            oldest_frames = sorted(self.frame_cache.keys())[:len(self.frame_cache) - self.cache_size]
            for old_frame in oldest_frames:
                del self.frame_cache[old_frame]
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current frame"""
        return self.get_frame(self.current_frame_number)
    
    def get_previous_frame(self) -> Optional[np.ndarray]:
        """Get the previous frame"""
        if self.current_frame_number > 1:
            return self.get_frame(self.current_frame_number - 1)
        return None
    
    def seek_to_frame(self, frame_number: int) -> bool:
        """Seek to a specific frame"""
        if not self.cap or not self.cap.isOpened():
            return False
        
        if frame_number < 1 or frame_number > self.frame_count:
            return False
        
        try:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
            self.current_frame_number = frame_number
            self.sequential_mode = True  # Enable sequential mode after seeking
            return True
        except Exception as e:
            print(f"Error seeking to frame {frame_number}: {e}")
            return False
    
    def seek_to_time(self, time_seconds: float) -> bool:
        """Seek to a specific time in the video"""
        if not self.cap or not self.cap.isOpened():
            return False
        
        if time_seconds < 0 or time_seconds > self.duration:
            return False
        
        try:
            frame_number = int(time_seconds * self.fps) + 1
            return self.seek_to_frame(frame_number)
        except Exception as e:
            print(f"Error seeking to time {time_seconds}: {e}")
            return False
    
    def get_frame_at_time(self, time_seconds: float) -> Optional[np.ndarray]:
        """Get frame at a specific time"""
        if self.seek_to_time(time_seconds):
            return self.get_current_frame()
        return None
    
    def get_video_info(self) -> dict:
        """Get comprehensive video information"""
        if not self.cap or not self.cap.isOpened():
            return {}
        
        return {
            'file_path': self.file_path,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'frame_count': self.frame_count,
            'duration': self.duration,
            'current_frame': self.current_frame_number
        }
    
    def format_time(self, seconds: float) -> str:
        """Format time in HH:MM:SS.mmm format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"
    
    def close(self):
        """Close the video capture"""
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Reset properties
        self.file_path = None
        self.width = 0
        self.height = 0
        self.fps = 0.0
        self.frame_count = 0
        self.duration = 0.0
        self.current_frame_number = 0
        self.sequential_mode = False
        
        # Clear frame cache
        self.frame_cache.clear()
    
    def is_loaded(self) -> bool:
        """Check if a video is currently loaded"""
        return self.cap is not None and self.cap.isOpened()
    
    def get_frame_dimensions(self) -> Tuple[int, int]:
        """Get frame dimensions"""
        return self.width, self.height
    
    def get_total_frames(self) -> int:
        """Get total number of frames"""
        return self.frame_count
    
    def get_duration(self) -> float:
        """Get video duration in seconds"""
        return self.duration
    
    def get_fps(self) -> float:
        """Get video frame rate"""
        return self.fps
    
    def preload_frames(self, start_frame: int, end_frame: int):
        """Preload a range of frames into cache"""
        if not self.cap or not self.cap.isOpened():
            return
        
        start_frame = max(1, start_frame)
        end_frame = min(self.frame_count, end_frame)
        
        for frame_num in range(start_frame, end_frame + 1):
            if frame_num not in self.frame_cache:
                self.get_frame(frame_num)
