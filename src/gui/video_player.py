"""
Video Player Widget
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QAction

from src.core.video_processor import VideoProcessor
from src.models.video_data import VideoData


class VideoPlayer(QWidget):
    """Video player widget using standard media player"""
    
    # Signals
    frame_changed = pyqtSignal(int)  # Emitted when current frame changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_processor = None
        self.video_data = None
        self.current_frame = 1
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Video display area using QVideoWidget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(640, 480)
        layout.addWidget(self.video_widget)
        
        # Media player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        
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
    
    def configure_media_player(self):
        """Configure media player for better compatibility"""
        # Set playback rate to normal
        self.media_player.setPlaybackRate(1.0)
    
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
        
        # Slider connections
        self.position_slider.sliderMoved.connect(self.set_position)
    
    def set_video_processor(self, processor: VideoProcessor):
        """Set the video processor (kept for compatibility)"""
        self.video_processor = processor
    
    def set_video_data(self, video_data: VideoData):
        """Set the video data and load the video"""
        self.video_data = video_data
        self.load_video(video_data.file_path)
    
    def load_video(self, file_path: str):
        """Load a video file into the media player"""
        if not file_path:
            return
        
        try:
            # Load the video file
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            
            # Update controls
            self.update_controls()
            
            # Connect position updates to frame changes
            self.media_player.positionChanged.connect(self.update_frame_from_position)
            
        except Exception as e:
            print(f"Error loading video: {e}")
    
    def update_controls(self):
        """Update control states based on video availability"""
        has_video = self.media_player.mediaStatus() == QMediaPlayer.MediaStatus.LoadedMedia
        
        self.play_button.setEnabled(has_video)
        self.stop_button.setEnabled(has_video)
        self.prev_button.setEnabled(has_video)
        self.next_button.setEnabled(has_video)
        self.position_slider.setEnabled(has_video)
        
        if has_video:
            self.position_slider.setRange(0, self.media_player.duration())
    
    def toggle_play(self):
        """Toggle play/pause"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def stop(self):
        """Stop the video and go to beginning"""
        self.media_player.stop()
    
    def previous_frame(self):
        """Go to previous frame (skip back 1 second)"""
        current_pos = self.media_player.position()
        new_pos = max(0, current_pos - 1000)  # 1 second back
        self.media_player.setPosition(new_pos)
    
    def next_frame(self):
        """Go to next frame (skip forward 1 second)"""
        current_pos = self.media_player.position()
        duration = self.media_player.duration()
        new_pos = min(duration, current_pos + 1000)  # 1 second forward
        self.media_player.setPosition(new_pos)
    
    def seek_to_frame(self, frame_number: int):
        """Seek to a specific frame"""
        if not self.video_data:
            return
        
        if 1 <= frame_number <= self.video_data.total_frames:
            # Calculate position based on frame number
            frame_time = (frame_number - 1) / self.video_data.fps * 1000  # Convert to milliseconds
            self.media_player.setPosition(int(frame_time))
    
    def set_position(self, position: int):
        """Set the media player position"""
        self.media_player.setPosition(position)
    
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
