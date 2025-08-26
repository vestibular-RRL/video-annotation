"""
Video Data Model
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VideoData:
    """Video metadata and properties"""
    
    file_path: str
    width: int
    height: int
    fps: float
    frame_count: int
    duration: float
    
    @property
    def total_frames(self) -> int:
        """Get total number of frames"""
        return self.frame_count
    
    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio (width/height)"""
        return self.width / self.height if self.height > 0 else 0.0
    
    @property
    def frame_time(self) -> float:
        """Get time per frame in seconds"""
        return 1.0 / self.fps if self.fps > 0 else 0.0
    
    def get_frame_time(self, frame_number: int) -> float:
        """Get timestamp for a specific frame"""
        if frame_number < 1 or frame_number > self.total_frames:
            return 0.0
        return (frame_number - 1) / self.fps if self.fps > 0 else 0.0
    
    def get_frame_number(self, time_seconds: float) -> int:
        """Get frame number for a specific time"""
        if time_seconds < 0 or time_seconds > self.duration:
            return 1
        return int(time_seconds * self.fps) + 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'file_path': self.file_path,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'frame_count': self.frame_count,
            'duration': self.duration,
            'total_frames': self.total_frames,
            'aspect_ratio': self.aspect_ratio,
            'frame_time': self.frame_time
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VideoData':
        """Create from dictionary"""
        return cls(
            file_path=data['file_path'],
            width=data['width'],
            height=data['height'],
            fps=data['fps'],
            frame_count=data['frame_count'],
            duration=data['duration']
        )
