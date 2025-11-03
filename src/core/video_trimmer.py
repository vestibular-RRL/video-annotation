"""
Optimized Video Trimmer Module with FFmpeg Support
"""

import cv2
import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple


class VideoTrimmer:
    """Handles video trimming operations using FFmpeg for fast processing"""
    
    def __init__(self):
        self.ffmpeg_available = self._check_ffmpeg_availability()
        if self.ffmpeg_available:
            print("[OK] FFmpeg is available - using fast video trimming")
        else:
            print("[WARNING] FFmpeg not found - falling back to OpenCV (slower)")
    
    def _check_ffmpeg_availability(self) -> bool:
        """Check if FFmpeg is available on the system"""
        try:
            return shutil.which("ffmpeg") is not None
        except:
            return False
    
    def trim_video_by_frames(self, input_video_path: str, output_video_path: str, 
                            start_frame: int, end_frame: int, fps: float) -> bool:
        """
        Trim video from start_frame to end_frame using FFmpeg (fast) or OpenCV (fallback)
        
        Args:
            input_video_path: Path to input video file
            output_video_path: Path to output video file
            start_frame: Starting frame number (1-based)
            end_frame: Ending frame number (1-based)
            fps: Frames per second of the video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Try FFmpeg first (much faster)
            if self.ffmpeg_available:
                if self._trim_with_ffmpeg(input_video_path, output_video_path, start_frame, end_frame, fps):
                    return True
            
            # Fallback to OpenCV method
            return self._trim_with_opencv(input_video_path, output_video_path, start_frame, end_frame, fps)
            
        except Exception as e:
            print(f"Error trimming video: {e}")
            return False
    
    def _trim_with_ffmpeg(self, input_video_path: str, output_video_path: str, 
                          start_frame: int, end_frame: int, fps: float) -> bool:
        """Trim video using FFmpeg for maximum speed"""
        try:
            # Calculate start and end times in seconds
            start_time = (start_frame - 1) / fps
            duration = (end_frame - start_frame + 1) / fps
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_video_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Build FFmpeg command for fast trimming
            cmd = [
                "ffmpeg",
                "-i", input_video_path,
                "-ss", str(start_time),
                "-t", str(duration),
                "-c:v", "libx264",  # Use H.264 codec for better compatibility
                "-preset", "fast",   # Fast encoding preset
                "-crf", "23",        # Good quality with reasonable file size
                "-avoid_negative_ts", "make_zero",  # Handle negative timestamps
                "-y",                # Overwrite output file
                output_video_path
            ]
            
            print(f"Using FFmpeg for fast video trimming...")
            print(f"Frame range: {start_frame} to {end_frame}")
            print(f"Time range: {start_time:.2f}s to {start_time + duration:.2f}s")
            
            # Run FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print(f"✓ FFmpeg trimming completed successfully: {output_video_path}")
                return True
            else:
                print(f"✗ FFmpeg failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("FFmpeg operation timed out, falling back to OpenCV")
            return False
        except Exception as e:
            print(f"FFmpeg error: {e}, falling back to OpenCV")
            return False
    
    def _trim_with_opencv(self, input_video_path: str, output_video_path: str, 
                         start_frame: int, end_frame: int, fps: float) -> bool:
        """Trim video using OpenCV (fallback method)"""
        try:
            # Open input video
            cap = cv2.VideoCapture(input_video_path)
            if not cap.isOpened():
                print(f"Error: Could not open input video {input_video_path}")
                return False
            
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Validate frame range
            if start_frame < 1 or end_frame > total_frames or start_frame > end_frame:
                print(f"Error: Invalid frame range {start_frame}-{end_frame} for video with {total_frames} frames")
                cap.release()
                return False
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_video_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Use optimized codec
            fourcc = self._get_best_codec()
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                print(f"Error: Could not create output video {output_video_path}")
                cap.release()
                return False
            
            # Seek to start frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame - 1)
            
            # Read and write frames with optimized batch processing
            frames_to_process = end_frame - start_frame + 1
            processed_frames = 0
            batch_size = 100  # Process frames in larger batches
            
            print(f"Trimming video from frame {start_frame} to {end_frame} using OpenCV...")
            
            while processed_frames < frames_to_process:
                # Process frames in batches for better performance
                batch_frames = min(batch_size, frames_to_process - processed_frames)
                
                for _ in range(batch_frames):
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    out.write(frame)
                    processed_frames += 1
                
                # Progress update every 500 frames
                if processed_frames % 500 == 0 or processed_frames == frames_to_process:
                    progress = (processed_frames / frames_to_process) * 100
                    print(f"Progress: {progress:.1f}% ({processed_frames}/{frames_to_process} frames)")
            
            # Clean up
            cap.release()
            out.release()
            
            print(f"✓ OpenCV trimming completed: {output_video_path}")
            return True
            
        except Exception as e:
            print(f"Error in OpenCV trimming: {e}")
            return False
    
    def _get_best_codec(self):
        """Get the best available codec for video writing"""
        # Try different codecs in order of preference
        codecs = [
            ("mp4v", cv2.VideoWriter_fourcc(*"mp4v")),
            ("XVID", cv2.VideoWriter_fourcc(*"XVID")),
            ("MJPG", cv2.VideoWriter_fourcc(*"MJPG")),
            ("H264", cv2.VideoWriter_fourcc(*"H264")),
        ]
        
        for codec_name, codec in codecs:
            try:
                # Test if codec is available
                test_writer = cv2.VideoWriter()
                if test_writer.isOpened():
                    test_writer.release()
                return codec
            except:
                continue
        
        # Fallback to mp4v
        return cv2.VideoWriter_fourcc(*"mp4v")
    
    def create_output_folder(self, base_path: str, folder_name: str) -> str:
        """
        Create output folder with the given name
        
        Args:
            base_path: Base directory path
            folder_name: Name of the folder to create
            
        Returns:
            str: Path to the created folder
        """
        try:
            # Clean folder name (remove invalid characters)
            clean_name = self._clean_folder_name(folder_name)
            
            # Create full path
            folder_path = os.path.join(base_path, clean_name)
            
            # Create folder if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                print(f"Created output folder: {folder_path}")
            else:
                print(f"Output folder already exists: {folder_path}")
            
            return folder_path
            
        except Exception as e:
            print(f"Error creating output folder: {e}")
            return base_path
    
    def _clean_folder_name(self, name: str) -> str:
        """Clean folder name by removing invalid characters"""
        # Remove or replace invalid characters for Windows/Linux
        invalid_chars = "<>:\"/\\|?*"
        for char in invalid_chars:
            name = name.replace(char, "_")
        
        # Remove leading/trailing spaces and dots
        name = name.strip(" .")
        
        # Ensure name is not empty
        if not name:
            name = "trimmed_video"
        
        return name
    
    def get_video_info(self, video_path: str) -> Optional[dict]:
        """
        Get video information
        
        Args:
            video_path: Path to video file
            
        Returns:
            dict: Video information or None if error
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            info = {
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0
            }
            
            cap.release()
            return info
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_trimming_method(self) -> str:
        """Get the trimming method that will be used"""
        if self.ffmpeg_available:
            return "FFmpeg (Fast)"
        else:
            return "OpenCV (Slow)"
