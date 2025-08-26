"""
Video Utility Functions
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
from src.utils.file_utils import is_video_file


def get_video_info(file_path: str) -> Optional[Dict[str, Any]]:
    """Get comprehensive video information"""
    try:
        if not is_video_file(file_path):
            return None
        
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return None
        
        # Get basic properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Get additional properties
        codec = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec_str = "".join([chr((codec >> 8 * i) & 0xFF) for i in range(4)])
        
        bitrate = int(cap.get(cv2.CAP_PROP_BITRATE))
        
        # Get file size
        from src.utils.file_utils import get_file_size, format_file_size
        file_size = get_file_size(file_path)
        file_size_formatted = format_file_size(file_size) if file_size else "Unknown"
        
        cap.release()
        
        return {
            'file_path': file_path,
            'filename': Path(file_path).name,
            'width': width,
            'height': height,
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration,
            'duration_formatted': format_duration(duration),
            'codec': codec_str,
            'bitrate': bitrate,
            'file_size': file_size,
            'file_size_formatted': file_size_formatted,
            'aspect_ratio': width / height if height > 0 else 0,
            'format': Path(file_path).suffix.lower()
        }
    
    except Exception as e:
        print(f"Error getting video info for {file_path}: {e}")
        return None


def format_duration(seconds: float) -> str:
    """Format duration in HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def extract_frame(video_path: str, frame_number: int) -> Optional[np.ndarray]:
    """Extract specific frame from video"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        # Set frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Read frame
        ret, frame = cap.read()
        cap.release()
        
        return frame if ret else None
    
    except Exception as e:
        print(f"Error extracting frame {frame_number} from {video_path}: {e}")
        return None


def extract_frames(video_path: str, frame_numbers: List[int]) -> List[np.ndarray]:
    """Extract multiple frames from video"""
    frames = []
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return frames
        
        for frame_number in frame_numbers:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        
        cap.release()
        return frames
    
    except Exception as e:
        print(f"Error extracting frames from {video_path}: {e}")
        return frames


def get_frame_at_time(video_path: str, timestamp: float) -> Optional[np.ndarray]:
    """Get frame at specific timestamp"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(timestamp * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        return frame if ret else None
    
    except Exception as e:
        print(f"Error getting frame at time {timestamp} from {video_path}: {e}")
        return None


def resize_frame(frame: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
    """Resize frame to target size while maintaining aspect ratio"""
    target_width, target_height = target_size
    height, width = frame.shape[:2]
    
    # Calculate aspect ratios
    aspect_ratio = width / height
    target_aspect_ratio = target_width / target_height
    
    if aspect_ratio > target_aspect_ratio:
        # Frame is wider than target
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:
        # Frame is taller than target
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
    
    # Resize frame
    resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    # Create target-sized frame with black padding
    result = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    
    # Calculate padding
    y_offset = (target_height - new_height) // 2
    x_offset = (target_width - new_width) // 2
    
    # Place resized frame in center
    result[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized
    
    return result


def convert_frame_to_qimage(frame: np.ndarray) -> Optional['QImage']:
    """Convert OpenCV frame to QImage"""
    try:
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get frame dimensions
        height, width, channel = rgb_frame.shape
        bytes_per_line = 3 * width
        
        # Convert to QImage
        from PyQt6.QtGui import QImage
        q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        
        return q_image
    
    except Exception as e:
        print(f"Error converting frame to QImage: {e}")
        return None


def convert_frame_to_qpixmap(frame: np.ndarray, target_size: Optional[Tuple[int, int]] = None) -> Optional['QPixmap']:
    """Convert OpenCV frame to QPixmap"""
    try:
        q_image = convert_frame_to_qimage(frame)
        if q_image is None:
            return None
        
        pixmap = QPixmap.fromImage(q_image)
        
        if target_size:
            pixmap = pixmap.scaled(
                target_size[0], target_size[1],
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        
        return pixmap
    
    except Exception as e:
        print(f"Error converting frame to QPixmap: {e}")
        return None


def create_thumbnail(video_path: str, frame_number: int = 0, size: Tuple[int, int] = (320, 240)) -> Optional[np.ndarray]:
    """Create thumbnail from video frame"""
    try:
        frame = extract_frame(video_path, frame_number)
        if frame is None:
            return None
        
        return resize_frame(frame, size)
    
    except Exception as e:
        print(f"Error creating thumbnail for {video_path}: {e}")
        return None


def get_video_preview_frames(video_path: str, num_frames: int = 5) -> List[np.ndarray]:
    """Get preview frames from video"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            cap.release()
            return []
        
        # Calculate frame intervals
        interval = max(1, total_frames // num_frames)
        frame_numbers = [i * interval for i in range(min(num_frames, total_frames // interval))]
        
        frames = []
        for frame_number in frame_numbers:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        
        cap.release()
        return frames
    
    except Exception as e:
        print(f"Error getting preview frames from {video_path}: {e}")
        return []


def validate_video_file(video_path: str) -> bool:
    """Validate if video file can be opened and read"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False
        
        # Try to read first frame
        ret, frame = cap.read()
        cap.release()
        
        return ret and frame is not None
    
    except Exception:
        return False


def get_video_duration(video_path: str) -> Optional[float]:
    """Get video duration in seconds"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if fps > 0:
            return frame_count / fps
        else:
            return None
    
    except Exception as e:
        print(f"Error getting duration for {video_path}: {e}")
        return None
