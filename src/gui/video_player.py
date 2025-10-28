"""
Video Player Widget
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QFrame, QCheckBox, QFileDialog,
                             QProgressBar, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QAction, QPixmap, QImage
import cv2
import numpy as np

from src.core.video_processor import VideoProcessor
from src.models.video_data import VideoData
import os
from typing import Optional


class VideoPlayer(QWidget):
    """Video player widget"""
    
    # Signals
    frame_changed = pyqtSignal(int)  # Emitted when current frame changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_processor = None
        self.video_data = None
        self.current_frame = 1
        self.audio_output = None
        self.stored_volume = 1.0  # Store volume when muting
        self.use_custom_display = False  # Flag to determine display method
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self.update_custom_frame)
        self.is_playing = False
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Video display area - we'll switch between QVideoWidget and QLabel
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(640, 480)
        
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("background-color: black; border: 1px solid gray;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("No video loaded")
        self.video_label.hide()  # Hide initially
        # Use expanding size policy to match QVideoWidget behavior
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.setScaledContents(True)  # Let Qt handle the scaling
        
        layout.addWidget(self.video_widget)
        layout.addWidget(self.video_label)
        
        # Audio output
        self.audio_output = QAudioOutput()
        
        # Media player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        
        # Configure media player for better compatibility
        self.configure_media_player()
        

        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Play")
        self.play_button.setEnabled(False)
        controls_layout.addWidget(self.play_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        self.prev_button = QPushButton("Previous")
        self.prev_button.setEnabled(False)
        controls_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.setEnabled(False)
        controls_layout.addWidget(self.next_button)
        
        # Audio controls
        self.mute_button = QPushButton("🔊")
        self.mute_button.setEnabled(False)
        self.mute_button.setToolTip("Mute/Unmute audio")
        self.mute_button.setMaximumWidth(40)
        controls_layout.addWidget(self.mute_button)
        
        layout.addLayout(controls_layout)
        
        # Position slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Position:"))
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setEnabled(False)
        slider_layout.addWidget(self.position_slider)
        
        self.position_label = QLabel("00:00 / 00:00")
        slider_layout.addWidget(self.position_label)
        
        layout.addLayout(slider_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)  # Default to full volume
        self.volume_slider.setEnabled(False)
        self.volume_slider.setMaximumWidth(150)
        self.volume_slider.setToolTip("Adjust audio volume")
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("100%")
        self.volume_label.setMinimumWidth(40)
        volume_layout.addWidget(self.volume_label)
        
        # Add stretch to push volume controls to the right
        volume_layout.addStretch()
        
        layout.addLayout(volume_layout)
    
    def configure_media_player(self):
        """Configure media player for better compatibility"""
        # Set playback rate to normal
        self.media_player.setPlaybackRate(1.0)
    
    def detect_video_codec(self, file_path: str) -> str:
        """Detect the video codec"""
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return "unknown"
            
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            cap.release()
            return codec_str
        except:
            return "unknown"
    
    def switch_to_custom_display(self):
        """Switch to custom OpenCV-based display"""
        self.use_custom_display = True
        self.video_widget.hide()
        self.video_label.show()
        self.media_player.setVideoOutput(None)  # Disconnect video output
        
        # Initialize position slider for custom display
        if self.video_data:
            self.position_slider.setRange(0, 1000)
            self.position_slider.setValue(0)
        
        print("Switched to custom display for unsupported codec")
    
    def switch_to_media_player(self):
        """Switch to QMediaPlayer display"""
        self.use_custom_display = False
        self.video_label.hide()
        self.video_widget.show()
        self.media_player.setVideoOutput(self.video_widget)
        print("Using QMediaPlayer display")
    
    def cv2_to_qpixmap(self, cv_image):
        """Convert OpenCV image to QPixmap for display"""
        if cv_image is None:
            return None
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        # Get image dimensions
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        
        # Create QImage from numpy array
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Convert to QPixmap
        pixmap = QPixmap.fromImage(qt_image)
        
        return pixmap
    
    def update_custom_frame(self):
        """Update the custom frame display"""
        if not self.video_processor or not self.video_data:
            return
        
        # Get current frame from video processor
        frame = self.video_processor.get_frame(self.current_frame)
        if frame is not None:
            # Convert OpenCV frame to QPixmap
            pixmap = self.cv2_to_qpixmap(frame)
            if pixmap:
                # Set the pixmap directly - Qt will handle scaling with setScaledContents(True)
                self.video_label.setPixmap(pixmap)
        
        # Emit frame changed signal
        self.frame_changed.emit(self.current_frame)
        
        # Update position slider
        if self.video_data and self.video_data.total_frames > 0:
            position = int((self.current_frame - 1) / self.video_data.total_frames * 1000)
            self.position_slider.setValue(position)
            
            # Update position label
            current_time = (self.current_frame - 1) / self.video_data.fps
            total_time = self.video_data.duration
            self.update_position_label(int(current_time * 1000), int(total_time * 1000))
        
        # Move to next frame if playing
        if self.is_playing:
            self.current_frame += 1
            if self.current_frame > self.video_data.total_frames:
                self.current_frame = self.video_data.total_frames
                self.stop()
    
    def setup_connections(self):
        """Set up signal connections"""
        # Media player connections
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media_player.errorOccurred.connect(self.on_error_occurred)
        
        # Control button connections
        self.play_button.clicked.connect(self.toggle_play)
        self.stop_button.clicked.connect(self.stop)
        self.prev_button.clicked.connect(self.previous_frame)
        self.next_button.clicked.connect(self.next_frame)
        self.mute_button.clicked.connect(self.toggle_mute)
        
        # Slider connections
        self.position_slider.sliderMoved.connect(self.set_position)
        self.volume_slider.valueChanged.connect(self.set_volume)
        

    
    def load_video(self, file_path: str):
        """Load a video file with automatic codec detection and display method selection"""
        if not file_path:
            return
        
        try:
            print(f"Loading video: {file_path}")
            
            # Detect video codec
            codec = self.detect_video_codec(file_path)
            print(f"Detected codec: {codec}")
            
            # Initialize video processor
            self.video_processor = VideoProcessor()
            if not self.video_processor.load_video(file_path):
                print("Failed to load video with processor")
                return
            
            # Create video data
            self.video_data = VideoData(
                file_path=file_path,
                width=self.video_processor.width,
                height=self.video_processor.height,
                fps=self.video_processor.fps,
                frame_count=self.video_processor.frame_count,
                duration=self.video_processor.duration
            )
            
            # Choose display method based on codec
            if codec in ['AV01', 'av01']:  # AV1 codec
                print("AV1 codec detected - using custom display")
                self.switch_to_custom_display()
                # Load first frame immediately
                self.current_frame = 1
                self.update_custom_frame()
            else:  # H.264, H.265, etc.
                print(f"{codec} codec detected - using QMediaPlayer")
                self.switch_to_media_player()
                try:
                    self.media_player.setSource(QUrl.fromLocalFile(file_path))
                    print("Video loaded successfully into media player")
                except Exception as e:
                    print(f"Media player failed, falling back to custom display: {e}")
                    self.switch_to_custom_display()
                    self.current_frame = 1
                    self.update_custom_frame()
            
            # Update controls
            self.update_controls()
            
            # Connect position updates to frame changes
            self.media_player.positionChanged.connect(self.update_frame_from_position)
            
        except Exception as e:
            print(f"Error loading video: {e}")
    

    

    

    
    def toggle_play(self):
        """Toggle play/pause"""
        if not self.video_processor or not self.video_data:
            return
            
        if self.use_custom_display:
            # Custom display mode
            if self.is_playing:
                self.pause()
            else:
                self.play()
        else:
            # QMediaPlayer mode
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
                self.play_button.setText("Play")
            else:
                self.media_player.play()
                self.play_button.setText("Pause")
    
    def play(self):
        """Start playback (custom display mode)"""
        if not self.video_processor or not self.video_data:
            return
            
        self.is_playing = True
        self.play_button.setText("Pause")
        
        # Start frame timer based on video FPS
        fps = self.video_data.fps
        if fps > 0:
            interval = int(1000 / fps)  # Convert to milliseconds
            self.frame_timer.start(interval)
    
    def pause(self):
        """Pause playback (custom display mode)"""
        self.is_playing = False
        self.play_button.setText("Play")
        self.frame_timer.stop()
    
    def stop(self):
        """Stop playback"""
        if self.use_custom_display:
            self.is_playing = False
            self.play_button.setText("Play")
            self.frame_timer.stop()
            self.current_frame = 1
            self.update_custom_frame()
            self.frame_changed.emit(self.current_frame)
        else:
            self.media_player.stop()
            self.play_button.setText("Play")
    
    def previous_frame(self):
        """Go to previous frame (skip back 1 second)"""
        if self.use_custom_display:
            # Custom display mode - go back by frames
            if self.video_data and self.video_data.fps > 0:
                frames_to_skip = int(self.video_data.fps)  # 1 second worth of frames
                self.current_frame = max(1, self.current_frame - frames_to_skip)
                self.update_custom_frame()
        else:
            # QMediaPlayer mode
            current_pos = self.media_player.position()
            new_pos = max(0, current_pos - 1000)  # 1 second back
            self.media_player.setPosition(new_pos)
    
    def next_frame(self):
        """Go to next frame (skip forward 1 second)"""
        if self.use_custom_display:
            # Custom display mode - go forward by frames
            if self.video_data and self.video_data.fps > 0:
                frames_to_skip = int(self.video_data.fps)  # 1 second worth of frames
                self.current_frame = min(self.video_data.total_frames, self.current_frame + frames_to_skip)
                self.update_custom_frame()
        else:
            # QMediaPlayer mode
            current_pos = self.media_player.position()
            duration = self.media_player.duration()
            new_pos = min(duration, current_pos + 1000)  # 1 second forward
            self.media_player.setPosition(new_pos)
    
    def seek_to_frame(self, frame_number: int):
        """Seek to a specific frame"""
        if not self.video_data:
            return
        
        frame_number = max(1, min(frame_number, self.video_data.total_frames))
        
        if self.use_custom_display:
            self.current_frame = frame_number
            self.update_custom_frame()
        else:
            # Convert frame to time for QMediaPlayer
            time_ms = int((frame_number - 1) / self.video_data.fps * 1000)
            self.media_player.setPosition(time_ms)
    
    def set_position(self, position: int):
        """Set video position from slider"""
        if not self.video_data:
            return
            
        if self.use_custom_display:
            # Convert position to frame number
            frame_number = int(position / 1000.0 * self.video_data.total_frames) + 1
            frame_number = max(1, min(frame_number, self.video_data.total_frames))
            self.current_frame = frame_number
            self.update_custom_frame()
        else:
            self.media_player.setPosition(position)
    
    
    def set_volume(self, volume: int):
        """Set the audio volume (0-100)"""
        if self.audio_output:
            # Convert 0-100 to 0.0-1.0 range
            volume_float = volume / 100.0
            self.audio_output.setVolume(volume_float)
            self.volume_label.setText(f"{volume}%")
            
            # Update mute button icon based on volume
            if volume == 0:
                self.mute_button.setText("🔇")
            else:
                self.mute_button.setText("🔊")
    
    def toggle_mute(self):
        """Toggle audio mute/unmute"""
        if self.audio_output:
            current_volume = self.audio_output.volume()
            if current_volume > 0:
                # Store current volume and mute
                self.stored_volume = current_volume
                self.audio_output.setVolume(0.0)
                self.volume_slider.setValue(0)
                self.mute_button.setText("🔇")
            else:
                # Restore previous volume
                restored_volume = getattr(self, 'stored_volume', 1.0)
                self.audio_output.setVolume(restored_volume)
                volume_percent = int(restored_volume * 100)
                self.volume_slider.setValue(volume_percent)
                self.mute_button.setText("🔊")
    
    def on_position_changed(self, position: int):
        """Handle position changes from media player"""
        # Update slider
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)
        
        # Update position label
        self.update_position_label(position, self.media_player.duration())
    
    def on_duration_changed(self, duration: int):
        """Handle duration changes from media player"""
        self.position_slider.setRange(0, duration)
        self.update_position_label(self.media_player.position(), duration)
    
    def on_media_status_changed(self, status: QMediaPlayer.MediaStatus):
        """Handle media status changes"""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.update_controls()
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Video finished playing
            pass
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            print("Invalid media format")
        elif status == QMediaPlayer.MediaStatus.NoMedia:
            print("No media loaded")
    
    def on_error_occurred(self, error: QMediaPlayer.Error, error_string: str):
        """Handle media player errors"""
        print(f"Media player error: {error} - {error_string}")
        
        # Try to recover from common errors
        if error == QMediaPlayer.Error.FormatError:
            print("Unsupported video format. Trying alternative approach...")
            self.fallback_to_custom_player()
        elif error == QMediaPlayer.Error.NetworkError:
            print("Network error occurred")
        elif error == QMediaPlayer.Error.ResourceError:
            print("Resource error occurred")
    
    def fallback_to_custom_player(self):
        """Fallback to custom video player if media player fails"""
        print("Falling back to custom video player...")
        # This would implement the custom frame-by-frame player
        # For now, just show an error message
        pass
    
    def update_position_label(self, position: int, duration: int):
        """Update the position label"""
        pos_str = self.format_time(position)
        dur_str = self.format_time(duration)
        self.position_label.setText(f"{pos_str} / {dur_str}")
    
    def format_time(self, milliseconds: int) -> str:
        """Format time in MM:SS format"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def update_frame_from_position(self, position: int):
        """Update frame number based on current position"""
        if not self.video_data:
            return
        
        # Calculate frame number from position
        frame_number = int(position / 1000.0 * self.video_data.fps) + 1
        frame_number = max(1, min(frame_number, self.video_data.total_frames))
        
        if frame_number != self.current_frame:
            self.current_frame = frame_number
            self.frame_changed.emit(self.current_frame)
    
    def get_current_frame(self) -> int:
        """Get the current frame number"""
        return self.current_frame
    
    def is_playing(self) -> bool:
        """Check if video is currently playing"""
        return self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
    
    def update_controls(self):
        """Update control button states"""
        if self.use_custom_display:
            # Custom display mode - enable controls if we have video data
            has_media = self.video_data is not None and self.video_processor is not None
        else:
            # QMediaPlayer mode - check media status
            has_media = self.media_player.mediaStatus() == QMediaPlayer.MediaStatus.LoadedMedia
        
        self.play_button.setEnabled(has_media)
        self.stop_button.setEnabled(has_media)
        self.prev_button.setEnabled(has_media)
        self.next_button.setEnabled(has_media)
        self.position_slider.setEnabled(has_media)
        self.mute_button.setEnabled(has_media)
        self.volume_slider.setEnabled(has_media)
    
    def set_video_processor(self, processor: VideoProcessor):
        """Set the video processor (kept for compatibility)"""
        self.video_processor = processor
    
    def set_video_data(self, video_data: VideoData):
        """Set the video data and load the video"""
        self.video_data = video_data
        self.load_video(video_data.file_path)
