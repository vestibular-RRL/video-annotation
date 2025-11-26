"""
Video Player Widget
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QFrame, QCheckBox, QFileDialog,
                             QProgressBar, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QAction
import cv2
import vlc
import os
from typing import Optional

from src.core.video_processor import VideoProcessor
from src.models.video_data import VideoData


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
        self.use_vlc = False  # Flag to determine display method
        self.vlc_instance = None
        self.vlc_player = None
        self.vlc_widget = None
        # Timer to update position slider for VLC
        self.vlc_position_timer = QTimer()
        self.vlc_position_timer.timeout.connect(self.update_vlc_position)
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Video display area - we'll switch between QVideoWidget and VLC widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(640, 480)
        layout.addWidget(self.video_widget)
        
        # Audio output
        self.audio_output = QAudioOutput()
        
        # Media player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setAudioOutput(self.audio_output)
        
        # Configure media player for better compatibility
        self.configure_media_player()
        
        # Set up VLC position timer (update less frequently to reduce overhead)
        self.vlc_position_timer.setInterval(200)  # Update every 200ms (reduced from 100ms)
        

        
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
    
    def switch_to_vlc(self):
        """Switch to VLC-based display for AV1 videos"""
        self.use_vlc = True
        self.video_widget.hide()
        
        # Initialize VLC instance if not already done
        if self.vlc_instance is None:
            # Configure VLC for better performance
            # Note: Removed --avcodec-hw=any to avoid Direct3D11 issues
            # VLC will auto-detect hardware acceleration if available
            vlc_args = [
                '--intf', 'dummy',  # No interface
                '--no-audio-time-stretch',  # Disable audio time stretching
                '--live-caching=300',  # Set cache to 300ms for better performance
                '--network-caching=300',  # Network cache
                '--drop-late-frames',  # Drop late frames to prevent lag
                '--skip-frames',  # Skip frames if needed
                '--no-video-deco',  # Don't force specific decoder
            ]
            self.vlc_instance = vlc.Instance(vlc_args)
            self.vlc_player = self.vlc_instance.media_player_new()
            
            # Set additional performance options
            try:
                # Try to enable hardware decoding, but don't fail if it doesn't work
                # Direct3D11 can sometimes cause issues, so we'll let VLC choose
                pass  # Let VLC auto-detect hardware acceleration
            except:
                pass  # Fallback if not available
        
        # Create VLC widget
        if self.vlc_widget is None:
            self.vlc_widget = QWidget()
            self.vlc_widget.setMinimumSize(640, 480)
            self.vlc_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.vlc_widget.setStyleSheet("background-color: black;")  # Black background
            # Get the layout and insert VLC widget before controls
            layout = self.layout()
            layout.insertWidget(0, self.vlc_widget)
        
        # Ensure widget is visible and raised
        self.vlc_widget.show()
        self.vlc_widget.raise_()
        
        # Set VLC output to widget (Windows) - must be done after widget is shown
        # Use delayed call to ensure widget is fully ready and avoid Direct3D11 errors
        QTimer.singleShot(100, lambda: self._set_vlc_window_handle())
        
        print("Switched to VLC display for AV1 codec")
    
    def switch_to_media_player(self):
        """Switch to QMediaPlayer display"""
        self.use_vlc = False
        if self.vlc_widget:
            self.vlc_widget.hide()
        self.video_widget.show()
        self.media_player.setVideoOutput(self.video_widget)
        print("Using QMediaPlayer display")
    
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
            
            # Stop any current playback first and clean up
            if self.use_vlc and self.vlc_player:
                try:
                    self.vlc_player.stop()
                    self.vlc_position_timer.stop()
                    # Release current media to free resources
                    self.vlc_player.set_media(None)
                    # Small delay to allow cleanup
                    import time
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error cleaning up VLC player: {e}")
            elif self.media_player:
                try:
                    self.media_player.stop()
                    self.media_player.setSource(QUrl())  # Clear source
                except:
                    pass
            
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
            print(f"Video FPS: {self.video_data.fps}, Frame count: {self.video_data.total_frames}, Duration: {self.video_data.duration:.2f}s")
            
            # Choose display method based on codec
            if codec in ['AV01', 'av01']:  # AV1 codec
                print("AV1 codec detected - using VLC")
                self.switch_to_vlc()
                
                # Ensure VLC widget is visible
                if self.vlc_widget:
                    self.vlc_widget.show()
                    self.vlc_widget.raise_()
                
                # Load video in VLC with performance options
                try:
                    media = self.vlc_instance.media_new(file_path)
                    if not media:
                        raise Exception("Failed to create VLC media object")
                    
                    # Add performance options to media
                    # Removed :avcodec-hw=any to avoid Direct3D11 issues
                    media.add_options(
                        ':live-caching=300',  # Cache for smooth playback
                        ':drop-late-frames',  # Drop late frames
                    )
                    self.vlc_player.set_media(media)
                    
                    # Parse media to get duration (non-blocking)
                    try:
                        media.parse_async(0, None, None)  # Async parse
                    except:
                        media.parse()  # Fallback to sync parse
                    
                    # Verify VLC widget is properly set up (already done in switch_to_vlc, but double-check)
                    # Use delayed call to ensure widget is fully ready
                    QTimer.singleShot(100, lambda: self._set_vlc_window_handle())
                    
                    print("Video loaded successfully into VLC")
                    
                    # Set position slider range (0-1000 for percentage-based positioning)
                    self.position_slider.setRange(0, 1000)
                    self.position_slider.setValue(0)
                except Exception as e:
                    print(f"Error loading video in VLC: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback: try to show first frame using video processor
                    if self.video_processor:
                        print("Attempting fallback display...")
                        # Could add fallback display here if needed
            else:  # H.264, H.265, etc.
                print(f"{codec} codec detected - trying QMediaPlayer first")
                self.switch_to_media_player()
                try:
                    self.media_player.setSource(QUrl.fromLocalFile(file_path))
                    print("Video loaded successfully into media player")
                    
                    # Check if QMediaPlayer can actually play this video
                    # Wait a moment for media to load, then check status
                    QTimer.singleShot(500, lambda: self._check_qmediaplayer_status(file_path))
                except Exception as e:
                    print(f"Media player failed, falling back to VLC: {e}")
                    self._fallback_to_vlc(file_path)
            
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
            
        if self.use_vlc:
            # VLC mode
            state = self.vlc_player.get_state()
            is_playing = self.vlc_player.is_playing()
            
            # Check if video has ended
            if state == vlc.State.Ended:
                # Restart from beginning - stop first, then reset, then play
                self.vlc_player.stop()
                # Wait a moment for stop to take effect
                QTimer.singleShot(50, lambda: self._restart_vlc_playback())
                return
            elif is_playing:
                # Pause if playing
                self.vlc_player.pause()
                self.play_button.setText("Play")
                self.vlc_position_timer.stop()
            else:
                # Play if paused or stopped
                self.vlc_player.play()
                self.play_button.setText("Pause")
                self.vlc_position_timer.start()
        else:
            # QMediaPlayer mode
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
                self.play_button.setText("Play")
            else:
                self.media_player.play()
                self.play_button.setText("Pause")
    
    def _restart_vlc_playback(self):
        """Helper method to restart VLC playback from beginning"""
        if not self.use_vlc or not self.vlc_player:
            return
        
        # Stop position timer first
        self.vlc_position_timer.stop()
        
        # Reset position to beginning
        self.vlc_player.set_time(0)
        self.position_slider.setValue(0)
        if self.video_data:
            self.current_frame = 1
            self.frame_changed.emit(self.current_frame)
        
        # Wait a moment for position to reset, then start playing
        QTimer.singleShot(100, lambda: self._start_vlc_playback())
    
    def _start_vlc_playback(self):
        """Helper method to start VLC playback"""
        if not self.use_vlc or not self.vlc_player:
            return
        # Start playing
        self.vlc_player.play()
        self.play_button.setText("Pause")
        # Wait a moment before starting position timer to ensure playback started
        QTimer.singleShot(100, lambda: self.vlc_position_timer.start())
    
    def stop(self):
        """Stop playback"""
        if self.use_vlc:
            self.vlc_player.stop()
            self.play_button.setText("Play")
            self.vlc_position_timer.stop()
            # Reset to beginning
            self.vlc_player.set_time(0)
            self.position_slider.setValue(0)
            if self.video_data:
                self.current_frame = 1
                self.frame_changed.emit(self.current_frame)
        else:
            self.media_player.stop()
            self.play_button.setText("Play")
    
    def update_vlc_position(self):
        """Update position slider for VLC playback"""
        if not self.use_vlc or not self.vlc_player:
            return
        
        try:
            state = self.vlc_player.get_state()
            length = self.vlc_player.get_length()
            time = self.vlc_player.get_time()
            
            # Check if video has ended
            if state == vlc.State.Ended:
                # Video ended - stop timer and update button
                # Only update if not already at end to avoid repeated updates
                if self.position_slider.value() < 1000:
                    self.vlc_position_timer.stop()
                    self.play_button.setText("Play")
                    # Set position to end
                    self.position_slider.setValue(1000)
                    if self.video_data:
                        self.current_frame = self.video_data.total_frames
                        self.frame_changed.emit(self.current_frame)
                return
            
            # Only update if we have valid values
            if length > 0 and time >= 0:
                # Calculate position as percentage (0-1000)
                position = int((time / length) * 1000)
                position = max(0, min(1000, position))  # Clamp to 0-1000
                
                # Only update slider if value changed significantly to reduce overhead
                if abs(self.position_slider.value() - position) > 2:
                    self.position_slider.setValue(position)
                
                # Update position label
                current_time = time / 1000.0  # Convert to seconds
                total_time = length / 1000.0
                self.update_position_label(int(time), int(length))
                
                # Emit frame changed signal
                if self.video_data and self.video_data.fps > 0:
                    frame_number = int(current_time * self.video_data.fps) + 1
                    frame_number = max(1, min(frame_number, self.video_data.total_frames))
                    if frame_number != self.current_frame:
                        self.current_frame = frame_number
                        self.frame_changed.emit(self.current_frame)
        except Exception as e:
            print(f"Error updating VLC position: {e}")
    
    def previous_frame(self):
        """Go to previous frame (skip back 1 second)"""
        if self.use_vlc:
            # VLC mode
            current_time = self.vlc_player.get_time()
            new_time = max(0, current_time - 1000)  # 1 second back
            self.vlc_player.set_time(new_time)
        else:
            # QMediaPlayer mode
            current_pos = self.media_player.position()
            new_pos = max(0, current_pos - 1000)  # 1 second back
            self.media_player.setPosition(new_pos)
    
    def next_frame(self):
        """Go to next frame (skip forward 1 second)"""
        if self.use_vlc:
            # VLC mode
            current_time = self.vlc_player.get_time()
            duration = self.vlc_player.get_length()
            new_time = min(duration, current_time + 1000)  # 1 second forward
            self.vlc_player.set_time(new_time)
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
        
        # Convert frame to time in milliseconds
        time_ms = int((frame_number - 1) / self.video_data.fps * 1000)
        
        if self.use_vlc:
            self.vlc_player.set_time(time_ms)
        else:
            self.media_player.setPosition(time_ms)
    
    def set_position(self, position: int):
        """Set video position from slider"""
        if not self.video_data:
            return
            
        if self.use_vlc:
            # Convert position (0-1000) to time in milliseconds
            duration = self.vlc_player.get_length()
            if duration > 0:
                # Clamp position to valid range
                position = max(0, min(1000, position))
                time_ms = int(position / 1000.0 * duration)
                # Temporarily stop position updates to avoid feedback loop
                self.vlc_position_timer.stop()
                self.vlc_player.set_time(time_ms)
                # Restart timer after a short delay if playing
                if self.vlc_player.is_playing():
                    QTimer.singleShot(100, lambda: self.vlc_position_timer.start())
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
        
        # Try to recover from common errors by falling back to VLC
        if error != QMediaPlayer.Error.NoError:
            # Get the current video file path if available
            source = self.media_player.source()
            if source and source.isLocalFile():
                file_path = source.toLocalFile()
                print(f"QMediaPlayer error detected, falling back to VLC for: {file_path}")
                self._fallback_to_vlc(file_path)
    
    def _check_qmediaplayer_status(self, file_path: str):
        """Check if QMediaPlayer is actually working, fallback to VLC if not"""
        if not self.video_data or not file_path:
            return
        
        # Check if media player has valid media
        status = self.media_player.mediaStatus()
        error = self.media_player.error()
        
        # If there's an error or invalid media, fallback to VLC
        if error != QMediaPlayer.Error.NoError or status == QMediaPlayer.MediaStatus.InvalidMedia:
            print(f"QMediaPlayer has issues (error: {error}, status: {status}), falling back to VLC")
            self._fallback_to_vlc(file_path)
        # Also check if video widget is actually visible and has content
        elif not self.video_widget.isVisible() or self.video_widget.size().isEmpty():
            print("QMediaPlayer video widget not properly visible, falling back to VLC")
            self._fallback_to_vlc(file_path)
    
    def _fallback_to_vlc(self, file_path: str):
        """Fallback to VLC player"""
        if not file_path or not self.video_data:
            return
        
        print("Switching to VLC player...")
        
        # Clean up existing VLC player if switching from QMediaPlayer
        if not self.use_vlc and self.vlc_player:
            try:
                self.vlc_player.stop()
                self.vlc_player.set_media(None)
                self.vlc_position_timer.stop()
            except:
                pass
        
        self.switch_to_vlc()
        
        try:
            # Load video in VLC
            media = self.vlc_instance.media_new(file_path)
            if not media:
                raise Exception("Failed to create VLC media object")
            
            # Add performance options
            # Removed :avcodec-hw=any to avoid Direct3D11 issues
            media.add_options(
                ':live-caching=300',
                ':drop-late-frames',
            )
            
            # Set media first
            self.vlc_player.set_media(media)
            
            # Parse media
            try:
                media.parse_async(0, None, None)
            except:
                media.parse()
            
            # Set window handle - ensure widget is visible first
            if self.vlc_widget and hasattr(self.vlc_widget, 'winId'):
                try:
                    # Ensure widget is visible and has a valid window ID
                    self.vlc_widget.show()
                    self.vlc_widget.raise_()
                    # Small delay to ensure widget is ready
                    QTimer.singleShot(100, lambda: self._set_vlc_window_handle())
                except Exception as e:
                    print(f"Warning setting VLC window handle: {e}")
            
            # Set position slider
            self.position_slider.setRange(0, 1000)
            self.position_slider.setValue(0)
            
            print("Video loaded successfully into VLC (fallback)")
        except Exception as e:
            print(f"Error loading video in VLC fallback: {e}")
            import traceback
            traceback.print_exc()
    
    def _set_vlc_window_handle(self):
        """Set VLC window handle - called with delay to ensure widget is ready"""
        if not self.vlc_widget or not self.vlc_player:
            return
        try:
            if hasattr(self.vlc_widget, 'winId'):
                win_id = self.vlc_widget.winId()
                if win_id:
                    self.vlc_player.set_hwnd(int(win_id))
        except Exception as e:
            print(f"Error setting VLC window handle: {e}")
    
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
        if self.use_vlc:
            # VLC mode - enable controls if we have video data
            has_media = self.video_data is not None and self.vlc_player is not None
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
