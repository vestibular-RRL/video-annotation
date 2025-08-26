"""
Frame Navigator Widget
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSpinBox, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.models.video_data import VideoData


class FrameNavigator(QWidget):
    """Frame navigation widget for precise frame control"""
    
    # Signals
    frame_selected = pyqtSignal(int)  # Emitted when a frame is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_data = None
        self.current_frame = 1
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Frame navigation group
        nav_group = QGroupBox("Frame Navigation")
        nav_layout = QGridLayout(nav_group)
        
        # Frame slider and spinbox
        nav_layout.addWidget(QLabel("Frame:"), 0, 0)
        
        self.frame_spinbox = QSpinBox()
        self.frame_spinbox.setMinimum(1)
        self.frame_spinbox.setMaximum(1)
        self.frame_spinbox.setValue(1)
        self.frame_spinbox.setEnabled(False)
        nav_layout.addWidget(self.frame_spinbox, 0, 1)
        
        # Navigation buttons
        button_layout = QHBoxLayout()
        
        self.first_button = QPushButton("First")
        self.first_button.setEnabled(False)
        button_layout.addWidget(self.first_button)
        
        self.prev_button = QPushButton("Previous")
        self.prev_button.setEnabled(False)
        button_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.setEnabled(False)
        button_layout.addWidget(self.next_button)
        
        self.last_button = QPushButton("Last")
        self.last_button.setEnabled(False)
        button_layout.addWidget(self.last_button)
        
        nav_layout.addLayout(button_layout, 1, 0, 1, 2)
        
        # Step navigation
        nav_layout.addWidget(QLabel("Step:"), 2, 0)
        
        self.step_spinbox = QSpinBox()
        self.step_spinbox.setMinimum(1)
        self.step_spinbox.setMaximum(100)
        self.step_spinbox.setValue(10)
        nav_layout.addWidget(self.step_spinbox, 2, 1)
        
        self.step_prev_button = QPushButton("Step Back")
        self.step_prev_button.setEnabled(False)
        nav_layout.addWidget(self.step_prev_button, 3, 0)
        
        self.step_next_button = QPushButton("Step Forward")
        self.step_next_button.setEnabled(False)
        nav_layout.addWidget(self.step_next_button, 3, 1)
        
        layout.addWidget(nav_group)
        
        # Video information group
        info_group = QGroupBox("Video Information")
        info_layout = QGridLayout(info_group)
        
        # Current frame info
        info_layout.addWidget(QLabel("Current Frame:"), 0, 0)
        self.current_frame_label = QLabel("0")
        info_layout.addWidget(self.current_frame_label, 0, 1)
        
        info_layout.addWidget(QLabel("Total Frames:"), 1, 0)
        self.total_frames_label = QLabel("0")
        info_layout.addWidget(self.total_frames_label, 1, 1)
        
        info_layout.addWidget(QLabel("Current Time:"), 2, 0)
        self.current_time_label = QLabel("00:00:00.000")
        info_layout.addWidget(self.current_time_label, 2, 1)
        
        info_layout.addWidget(QLabel("Duration:"), 3, 0)
        self.duration_label = QLabel("00:00:00.000")
        info_layout.addWidget(self.duration_label, 3, 1)
        
        info_layout.addWidget(QLabel("FPS:"), 4, 0)
        self.fps_label = QLabel("0")
        info_layout.addWidget(self.fps_label, 4, 1)
        
        info_layout.addWidget(QLabel("Resolution:"), 5, 0)
        self.resolution_label = QLabel("0x0")
        info_layout.addWidget(self.resolution_label, 5, 1)
        
        layout.addWidget(info_group)
        
        # Set fixed width for better layout
        self.setFixedWidth(300)
    
    def setup_connections(self):
        """Set up signal connections"""
        self.frame_spinbox.valueChanged.connect(self.on_frame_spinbox_changed)
        self.first_button.clicked.connect(self.go_to_first_frame)
        self.prev_button.clicked.connect(self.go_to_previous_frame)
        self.next_button.clicked.connect(self.go_to_next_frame)
        self.last_button.clicked.connect(self.go_to_last_frame)
        self.step_prev_button.clicked.connect(self.step_backward)
        self.step_next_button.clicked.connect(self.step_forward)
    
    def set_video_data(self, video_data: VideoData):
        """Set the video data"""
        self.video_data = video_data
        self.update_controls()
        self.update_video_info()
    
    def set_current_frame(self, frame_number: int):
        """Set the current frame"""
        if not self.video_data:
            return
        
        if 1 <= frame_number <= self.video_data.total_frames:
            self.current_frame = frame_number
            
            # Update spinbox (block signals to avoid recursion)
            self.frame_spinbox.blockSignals(True)
            self.frame_spinbox.setValue(frame_number)
            self.frame_spinbox.blockSignals(False)
            
            self.update_frame_info()
    
    def update_controls(self):
        """Update control states based on video availability"""
        has_video = self.video_data is not None
        
        self.frame_spinbox.setEnabled(has_video)
        self.first_button.setEnabled(has_video)
        self.prev_button.setEnabled(has_video)
        self.next_button.setEnabled(has_video)
        self.last_button.setEnabled(has_video)
        self.step_prev_button.setEnabled(has_video)
        self.step_next_button.setEnabled(has_video)
        
        if has_video:
            self.frame_spinbox.setMinimum(1)
            self.frame_spinbox.setMaximum(self.video_data.total_frames)
            self.frame_spinbox.setValue(1)
            self.current_frame = 1
        else:
            self.frame_spinbox.setMinimum(1)
            self.frame_spinbox.setMaximum(1)
            self.frame_spinbox.setValue(1)
            self.current_frame = 1
    
    def update_video_info(self):
        """Update video information display"""
        if not self.video_data:
            self.total_frames_label.setText("0")
            self.duration_label.setText("00:00:00.000")
            self.fps_label.setText("0")
            self.resolution_label.setText("0x0")
            return
        
        self.total_frames_label.setText(str(self.video_data.total_frames))
        self.duration_label.setText(self.format_time(self.video_data.duration))
        self.fps_label.setText(f"{self.video_data.fps:.2f}")
        self.resolution_label.setText(f"{self.video_data.width}x{self.video_data.height}")
    
    def update_frame_info(self):
        """Update current frame information"""
        if not self.video_data:
            self.current_frame_label.setText("0")
            self.current_time_label.setText("00:00:00.000")
            return
        
        self.current_frame_label.setText(str(self.current_frame))
        
        # Calculate current time
        current_time = (self.current_frame - 1) / self.video_data.fps
        self.current_time_label.setText(self.format_time(current_time))
    
    def format_time(self, seconds: float) -> str:
        """Format time in HH:MM:SS.mmm format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"
    
    def on_frame_spinbox_changed(self, value: int):
        """Handle frame spinbox value change"""
        if not self.video_data:
            return
        
        if value != self.current_frame:
            self.current_frame = value
            self.update_frame_info()
            self.frame_selected.emit(value)
    
    def go_to_first_frame(self):
        """Go to first frame"""
        if self.video_data:
            self.set_current_frame(1)
            self.frame_selected.emit(1)
    
    def go_to_last_frame(self):
        """Go to last frame"""
        if self.video_data:
            self.set_current_frame(self.video_data.total_frames)
            self.frame_selected.emit(self.video_data.total_frames)
    
    def go_to_previous_frame(self):
        """Go to previous frame"""
        if self.video_data and self.current_frame > 1:
            self.set_current_frame(self.current_frame - 1)
            self.frame_selected.emit(self.current_frame)
    
    def go_to_next_frame(self):
        """Go to next frame"""
        if self.video_data and self.current_frame < self.video_data.total_frames:
            self.set_current_frame(self.current_frame + 1)
            self.frame_selected.emit(self.current_frame)
    
    def step_backward(self):
        """Step backward by step size"""
        if self.video_data:
            step_size = self.step_spinbox.value()
            new_frame = max(1, self.current_frame - step_size)
            self.set_current_frame(new_frame)
            self.frame_selected.emit(new_frame)
    
    def step_forward(self):
        """Step forward by step size"""
        if self.video_data:
            step_size = self.step_spinbox.value()
            new_frame = min(self.video_data.total_frames, self.current_frame + step_size)
            self.set_current_frame(new_frame)
            self.frame_selected.emit(new_frame)
