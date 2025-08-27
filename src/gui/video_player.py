"""
Video Player Widget with YOLO Segmentation Tracking
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QFrame, QCheckBox, QFileDialog,
                             QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl, QThread
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QAction

from src.core.video_processor import VideoProcessor
from src.core.object_tracker import ObjectTracker, TrackingResult
from src.models.video_data import VideoData
import os
from typing import Optional


class TrackingThread(QThread):
    """Thread for running object tracking to avoid blocking UI"""
    tracking_finished = pyqtSignal(dict)
    progress_updated = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, tracker, video_path, output_path):
        super().__init__()
        self.tracker = tracker
        self.video_path = video_path
        self.output_path = output_path
    
    def run(self):
        try:
            results = self.tracker.track_video(self.video_path, self.output_path)
            self.tracking_finished.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))


class VideoPlayer(QWidget):
    """Video player widget with YOLO segmentation tracking capabilities"""
    
    # Signals
    frame_changed = pyqtSignal(int)  # Emitted when current frame changes
    tracking_completed = pyqtSignal(dict)  # Emitted when tracking is completed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_processor = None
        self.video_data = None
        self.current_frame = 1
        
        # Object tracking
        self.object_tracker = None
        self.tracking_results = {}
        self.show_tracking = False
        self.tracking_video_path = None
        self.tracking_thread = None
        
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
        
        # Tracking controls
        tracking_layout = QHBoxLayout()
        
        self.track_button = QPushButton("Start Segmentation Tracking")
        self.track_button.setEnabled(False)
        tracking_layout.addWidget(self.track_button)
        
        self.show_tracking_checkbox = QCheckBox("Show Tracking Results")
        self.show_tracking_checkbox.setEnabled(False)
        tracking_layout.addWidget(self.show_tracking_checkbox)
        
        self.export_tracking_button = QPushButton("Export Tracking Data")
        self.export_tracking_button.setEnabled(False)
        tracking_layout.addWidget(self.export_tracking_button)
        
        self.export_csv_button = QPushButton("Export Tracking CSV")
        self.export_csv_button.setEnabled(False)
        tracking_layout.addWidget(self.export_csv_button)
        
        layout.addLayout(tracking_layout)
        
        # Progress bar for tracking
        self.tracking_progress = QProgressBar()
        self.tracking_progress.setVisible(False)
        layout.addWidget(self.tracking_progress)
        
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
        
        # Tracking connections
        self.track_button.clicked.connect(self.start_tracking)
        self.show_tracking_checkbox.toggled.connect(self.toggle_tracking_display)
        self.export_tracking_button.clicked.connect(self.export_tracking_data)
        self.export_csv_button.clicked.connect(self.export_tracking_csv)
    
    def load_video(self, file_path: str):
        """Load a video file into the media player"""
        if not file_path:
            return
        
        try:
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
            
            # Load video into media player
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            
            # Update controls
            self.update_controls()
            
            # Connect position updates to frame changes
            self.media_player.positionChanged.connect(self.update_frame_from_position)
            
            # Enable tracking controls
            self.track_button.setEnabled(True)
            self.show_tracking_checkbox.setEnabled(True)
            
        except Exception as e:
            print(f"Error loading video: {e}")
    
    def start_tracking(self):
        """Start YOLO segmentation tracking on the loaded video"""
        if not self.video_data:
            return
        
        try:
            # Get model path
            model_path = self.get_model_path()
            
            # Initialize object tracker with segmentation model
            self.object_tracker = ObjectTracker(model_path=model_path)
            
            if not self.object_tracker.model:
                QMessageBox.warning(self, "Model Error", 
                                  "Failed to load YOLO segmentation model. Please check your model file.")
                return
            
            # Create output path for tracked video
            base_name = os.path.splitext(self.video_data.file_path)[0]
            self.tracking_video_path = f"{base_name}_split_tracked.mp4"
            
            # Start tracking in a separate thread
            self.track_button.setText("Split Tracking...")
            self.track_button.setEnabled(False)
            self.tracking_progress.setVisible(True)
            self.tracking_progress.setRange(0, 0)  # Indeterminate progress
            
            # Create and start tracking thread
            self.tracking_thread = TrackingThread(
                self.object_tracker, 
                self.video_data.file_path, 
                self.tracking_video_path
            )
            self.tracking_thread.tracking_finished.connect(self.on_tracking_completed)
            self.tracking_thread.error_occurred.connect(self.on_tracking_error)
            self.tracking_thread.start()
            
        except Exception as e:
            print(f"Error starting tracking: {e}")
            self.reset_tracking_ui()
            QMessageBox.critical(self, "Tracking Error", f"Failed to start tracking: {str(e)}")
    
    def on_tracking_completed(self, results):
        """Handle tracking completion"""
        self.tracking_results = results
        self.reset_tracking_ui()
        self.export_tracking_button.setEnabled(True)
        self.export_csv_button.setEnabled(True)
        
        # Set frame dimensions for proper left/right positioning
        if self.video_data and self.object_tracker:
            self.object_tracker.set_frame_dimensions(self.video_data.width, self.video_data.height)
        
        # Show tracking statistics
        if self.object_tracker:
            stats = self.object_tracker.get_tracking_statistics()
            print(f"Tracking completed: {stats}")
            
            # Show completion message with statistics
            message = (f"Split tracking completed!\n\n"
                      f"Processed {stats.get('total_frames', 0)} frames\n"
                      f"Total detections: {stats.get('total_detections', 0)}\n"
                      f"Total areas: {stats.get('total_areas', 0)}\n"
                      f"Unique objects: {stats.get('unique_tracked_objects', 0)}")
            
            QMessageBox.information(self, "Tracking Complete", message)
        
        # Emit signal
        self.tracking_completed.emit(results)
    
    def on_tracking_error(self, error_message):
        """Handle tracking error"""
        self.reset_tracking_ui()
        QMessageBox.critical(self, "Tracking Error", f"Tracking failed: {error_message}")
    
    def reset_tracking_ui(self):
        """Reset tracking UI elements"""
        self.track_button.setText("Start Split Tracking")
        self.track_button.setEnabled(True)
        self.tracking_progress.setVisible(False)
        self.export_csv_button.setEnabled(False)
    
    def toggle_tracking_display(self, show: bool):
        """Toggle tracking display on/off"""
        self.show_tracking = show
        
        if show and self.tracking_video_path and os.path.exists(self.tracking_video_path):
            # Load tracked video
            self.media_player.setSource(QUrl.fromLocalFile(self.tracking_video_path))
        elif not show and self.video_data:
            # Load original video
            self.media_player.setSource(QUrl.fromLocalFile(self.video_data.file_path))
    
    def export_tracking_data(self):
        """Export tracking results to JSON file"""
        if not self.object_tracker or not self.tracking_results:
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Tracking Data", "", "JSON Files (*.json)"
            )
            
            if file_path:
                success = self.object_tracker.export_tracking_data(file_path)
                if success:
                    QMessageBox.information(self, "Success", 
                                          "Segmentation tracking data exported successfully!")
                else:
                    QMessageBox.warning(self, "Export Error", 
                                      "Failed to export tracking data.")
        
        except Exception as e:
            print(f"Error exporting tracking data: {e}")
            QMessageBox.critical(self, "Export Error", f"Error exporting data: {str(e)}")
    
    def export_tracking_csv(self):
        """Export tracking results to CSV file with left/right position and size data"""
        if not self.object_tracker or not self.tracking_results:
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Tracking CSV", "", "CSV Files (*.csv)"
            )
            
            if file_path:
                success = self.object_tracker.export_tracking_data_to_csv(file_path)
                if success:
                    QMessageBox.information(self, "Success", 
                                          "Tracking data exported to CSV successfully!")
                else:
                    QMessageBox.warning(self, "Export Error", 
                                      "Failed to export tracking data to CSV.")
        
        except Exception as e:
            print(f"Error exporting tracking data to CSV: {e}")
            QMessageBox.critical(self, "Export Error", f"Error exporting CSV data: {str(e)}")
    
    def get_model_path(self) -> str:
        """Get path to custom YOLO segmentation model"""
        # Use the specific segmentation model in src/segment_model/
        model_path = "src/segment_model/best copy.pt"
        
        if os.path.exists(model_path):
            print(f"Using segmentation model: {model_path}")
            return model_path
        
        # Fallback to other possible paths
        possible_paths = [
            "models/best.pt",
            "models/yolov8n-seg-custom.pt", 
            "models/eye_segmentation.pt",
            "models/segmentation_model.pt"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Using fallback model: {path}")
                return path
        
        # If no custom model found, show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select YOLO Segmentation Model", "", 
            "YOLO Models (*.pt);;All Files (*)"
        )
        
        if file_path:
            return file_path
        
        # Return None to use default model
        print("No custom model found, using default YOLO segmentation model")
        return None
    
    def get_current_tracking_results(self) -> Optional[TrackingResult]:
        """Get tracking results for current frame"""
        if not self.tracking_results:
            return None
        
        return self.tracking_results.get(self.current_frame)
    
    def toggle_play(self):
        """Toggle play/pause"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setText("Play")
        else:
            self.media_player.play()
            self.play_button.setText("Pause")
    
    def stop(self):
        """Stop playback"""
        self.media_player.stop()
        self.play_button.setText("Play")
    
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
    
    def update_controls(self):
        """Update control button states"""
        has_media = self.media_player.mediaStatus() == QMediaPlayer.MediaStatus.LoadedMedia
        
        self.play_button.setEnabled(has_media)
        self.stop_button.setEnabled(has_media)
        self.prev_button.setEnabled(has_media)
        self.next_button.setEnabled(has_media)
        self.position_slider.setEnabled(has_media)
    
    def set_video_processor(self, processor: VideoProcessor):
        """Set the video processor (kept for compatibility)"""
        self.video_processor = processor
    
    def set_video_data(self, video_data: VideoData):
        """Set the video data and load the video"""
        self.video_data = video_data
        self.load_video(video_data.file_path)
