"""
Main Window
"""

import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QMenuBar, QMenu, QFileDialog, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSlider,
                             QLabel, QLineEdit, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence

from src.gui.video_player import VideoPlayer
from src.gui.widgets.status_bar import StatusBar
from src.core.video_processor import VideoProcessor
from src.core.annotation_manager import AnnotationManager
from src.core.csv_exporter import CSVExporter
from src.models.video_data import VideoData
from config.constants import SUPPORTED_VIDEO_FORMATS, WINDOW_TITLE
from config.settings import Settings


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.video_processor = None
        self.video_data = None
        self.annotation_manager = AnnotationManager()
        self.csv_exporter = CSVExporter()
        
        self.init_ui()
        self.setup_menus()
        self.setup_connections()
        self.load_window_settings()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Splitter for video and annotation table
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side - Video player
        self.video_player = VideoPlayer()
        splitter.addWidget(self.video_player)
        
        # Right side - Annotation table and range controls
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Range annotation controls
        range_group = QWidget()
        range_layout = QVBoxLayout(range_group)
        
        # Range sliders
        range_slider_layout = QHBoxLayout()
        range_slider_layout.addWidget(QLabel("Frame Range:"))
        
        # Start frame slider
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Start:"))
        self.start_slider = QSlider(Qt.Orientation.Horizontal)
        self.start_slider.setEnabled(False)
        start_layout.addWidget(self.start_slider)
        
        # End frame slider
        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("End:"))
        self.end_slider = QSlider(Qt.Orientation.Horizontal)
        self.end_slider.setEnabled(False)
        end_layout.addWidget(self.end_slider)
        
        range_slider_layout.addLayout(start_layout)
        range_slider_layout.addLayout(end_layout)
        
        self.range_label = QLabel("0 - 0")
        range_slider_layout.addWidget(self.range_label)
        
        range_layout.addLayout(range_slider_layout)
        
        # Annotation input
        annotation_layout = QHBoxLayout()
        annotation_layout.addWidget(QLabel("Annotation:"))
        
        self.annotation_input = QLineEdit()
        self.annotation_input.setPlaceholderText("Enter annotation text...")
        annotation_layout.addWidget(self.annotation_input)
        
        self.apply_button = QPushButton("Apply to Range")
        self.apply_button.setEnabled(False)
        annotation_layout.addWidget(self.apply_button)
        
        range_layout.addLayout(annotation_layout)
        
        right_layout.addWidget(range_group)
        
        # Annotation table
        self.annotation_table = QTableWidget()
        self.annotation_table.setColumnCount(2)
        self.annotation_table.setHorizontalHeaderLabels(["Frame#", "Annotation"])
        self.annotation_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.annotation_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.annotation_table.setAlternatingRowColors(True)
        
        right_layout.addWidget(self.annotation_table)
        
        splitter.addWidget(right_widget)
        
        # Set splitter proportions (60% video, 40% table)
        splitter.setSizes([720, 480])
        
        # Status bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)
    
    def setup_menus(self):
        """Set up the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Open video action
        open_action = QAction("&Open Video...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_video)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Save annotations action
        save_action = QAction("&Save Annotations...", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_annotations)
        file_menu.addAction(save_action)
        
        # Export CSV action
        export_action = QAction("&Export CSV...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        """Set up signal connections"""
        # Video player connections
        self.video_player.frame_changed.connect(self.on_frame_changed)
        
        # Range slider connections
        self.start_slider.valueChanged.connect(self.on_range_changed)
        self.end_slider.valueChanged.connect(self.on_range_changed)
        
        # Apply button connection
        self.apply_button.clicked.connect(self.apply_annotation_to_range)
        
        # Table connections
        self.annotation_table.itemChanged.connect(self.on_annotation_changed)
    
    def open_video(self):
        """Open a video file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            f"Video Files ({' '.join(['*' + ext for ext in SUPPORTED_VIDEO_FORMATS])})"
        )
        
        if file_path:
            self.load_video(file_path)
    
    def load_video(self, file_path: str):
        """Load a video file"""
        try:
            # Initialize video processor
            self.video_processor = VideoProcessor()
            if not self.video_processor.load_video(file_path):
                QMessageBox.critical(self, "Error", "Failed to load video file.")
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
            
            # Update video player
            self.video_player.set_video_processor(self.video_processor)
            self.video_player.set_video_data(self.video_data)
            
            # Initialize annotation table
            self.initialize_annotation_table()
            
            # Initialize range slider
            self.initialize_range_slider()
            
            # Update status bar
            self.status_bar.update_video_info(self.video_data)
            
            # Update window title
            filename = os.path.basename(file_path)
            self.setWindowTitle(f"{WINDOW_TITLE} - {filename}")
            
            # Save to recent files
            self.settings.add_recent_file(file_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load video: {str(e)}")
    
    def initialize_annotation_table(self):
        """Initialize the annotation table with frame numbers"""
        if not self.video_data:
            return
        
        # Clear existing table
        self.annotation_table.setRowCount(0)
        
        # Add rows for each frame
        for frame_num in range(1, self.video_data.total_frames + 1):
            row = self.annotation_table.rowCount()
            self.annotation_table.insertRow(row)
            
            # Frame number (read-only)
            frame_item = QTableWidgetItem(str(frame_num))
            frame_item.setFlags(frame_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.annotation_table.setItem(row, 0, frame_item)
            
            # Annotation (editable, starts with "0")
            annotation_item = QTableWidgetItem("0")
            self.annotation_table.setItem(row, 1, annotation_item)
    
    def initialize_range_slider(self):
        """Initialize the range sliders with time-based values"""
        if not self.video_data:
            return
        
        # Calculate total duration in seconds
        total_seconds = int(self.video_data.duration)
        
        # Initialize start slider (in seconds)
        self.start_slider.setEnabled(True)
        self.start_slider.setMinimum(0)
        self.start_slider.setMaximum(total_seconds)
        self.start_slider.setValue(0)
        
        # Initialize end slider (in seconds)
        self.end_slider.setEnabled(True)
        self.end_slider.setMinimum(0)
        self.end_slider.setMaximum(total_seconds)
        self.end_slider.setValue(total_seconds)
        
        # Update range label with time format
        self.update_range_label()
        self.apply_button.setEnabled(True)
    
    def on_frame_changed(self, frame_number: int):
        """Handle frame change from video player"""
        # Update status bar
        self.status_bar.update_frame_info(frame_number, self.video_data)
    
    def on_range_changed(self, value: int):
        """Handle range slider value change"""
        if not self.video_data:
            return
        
        # Ensure start time is not greater than end time
        start_seconds = self.start_slider.value()
        end_seconds = self.end_slider.value()
        
        if start_seconds > end_seconds:
            # If start time is greater than end time, adjust end time
            if self.sender() == self.start_slider:
                self.end_slider.setValue(start_seconds)
                end_seconds = start_seconds
            else:
                self.start_slider.setValue(end_seconds)
                start_seconds = end_seconds
        
        # Update range label with time format
        self.update_range_label()
    
    def apply_annotation_to_range(self):
        """Apply annotation to the selected frame range"""
        if not self.video_data:
            return
        
        annotation_text = self.annotation_input.text().strip()
        if not annotation_text:
            QMessageBox.warning(self, "Warning", "Please enter an annotation text.")
            return
        
        # Get the range from the sliders (in seconds)
        start_seconds = self.start_slider.value()
        end_seconds = self.end_slider.value()
        
        # Convert seconds to frame numbers
        start_frame = self.seconds_to_frame(start_seconds)
        end_frame = self.seconds_to_frame(end_seconds)
        
        # Apply annotation to all frames in the range
        for frame_num in range(start_frame, end_frame + 1):
            # Update the table
            table_row = frame_num - 1
            if table_row < self.annotation_table.rowCount():
                annotation_item = self.annotation_table.item(table_row, 1)
                if annotation_item:
                    annotation_item.setText(annotation_text)
            
            # Update annotation manager
            self.annotation_manager.update_annotation(frame_num, annotation_text)
        
        # Update status bar
        self.status_bar.update_annotation_count(self.annotation_manager.get_total_annotations())
        
        # Clear the input
        self.annotation_input.clear()
        
        # Convert back to time for display
        start_time_str = self.format_time(start_seconds)
        end_time_str = self.format_time(end_seconds)
        QMessageBox.information(self, "Success", f"Annotation '{annotation_text}' applied to time range {start_time_str} - {end_time_str}")
    
    def on_annotation_changed(self, item: QTableWidgetItem):
        """Handle annotation value change in table"""
        if item.column() == 1:  # Annotation column
            row = item.row()
            frame_number = row + 1  # Convert to 1-based frame number
            annotation_value = item.text()
            
            # Update annotation manager
            self.annotation_manager.update_annotation(frame_number, annotation_value)
            
            # Update status bar
            self.status_bar.update_annotation_count(self.annotation_manager.get_total_annotations())
    
    def save_annotations(self):
        """Save annotations to JSON file"""
        if not self.video_data:
            QMessageBox.warning(self, "Warning", "No video loaded.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Annotations",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                # Get annotations from table
                annotations = {}
                for row in range(self.annotation_table.rowCount()):
                    frame_number = row + 1
                    annotation_item = self.annotation_table.item(row, 1)
                    if annotation_item and annotation_item.text() != "0":
                        annotations[frame_number] = annotation_item.text()
                
                # Save to file
                self.annotation_manager.save_annotations(file_path, annotations)
                QMessageBox.information(self, "Success", "Annotations saved successfully.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save annotations: {str(e)}")
    
    def export_csv(self):
        """Export annotations to CSV file"""
        if not self.video_data:
            QMessageBox.warning(self, "Warning", "No video loaded.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            "",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                # Prepare data for export
                data = []
                for row in range(self.annotation_table.rowCount()):
                    frame_number = row + 1
                    annotation_item = self.annotation_table.item(row, 1)
                    annotation_value = annotation_item.text() if annotation_item else "0"
                    
                    data.append({
                        "Frame#": frame_number,
                        "Annotation": annotation_value
                    })
                
                # Export to CSV
                self.csv_exporter.export_annotations_to_csv(data, file_path)
                QMessageBox.information(self, "Success", "CSV exported successfully.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export CSV: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Video Annotation Tool",
            "Video Annotation Tool v1.0.0\n\n"
            "A simple tool for annotating video frames with text annotations.\n"
            "Watch the video and use the range slider to apply annotations to frame ranges."
        )
    
    def load_window_settings(self):
        """Load window settings from configuration"""
        try:
            geometry = self.settings.get("window_geometry")
            if geometry and hasattr(geometry, 'data'):  # Check if it's a proper QByteArray
                self.restoreGeometry(geometry)
        except Exception as e:
            print(f"Error restoring window geometry: {e}")
        
        try:
            state = self.settings.get("window_state")
            if state and hasattr(state, 'data'):  # Check if it's a proper QByteArray
                self.restoreState(state)
        except Exception as e:
            print(f"Error restoring window state: {e}")
    
    def seconds_to_frame(self, seconds: int) -> int:
        """Convert seconds to frame number"""
        if not self.video_data or self.video_data.fps <= 0:
            return 1
        frame_number = int(seconds * self.video_data.fps) + 1
        return max(1, min(frame_number, self.video_data.total_frames))
    
    def frame_to_seconds(self, frame_number: int) -> int:
        """Convert frame number to seconds"""
        if not self.video_data or self.video_data.fps <= 0:
            return 0
        seconds = (frame_number - 1) / self.video_data.fps
        return int(seconds)
    
    def format_time(self, seconds: int) -> str:
        """Format seconds to MM:SS format"""
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:02d}"
    
    def update_range_label(self):
        """Update the range label with formatted time"""
        if not self.video_data:
            return
        
        start_seconds = self.start_slider.value()
        end_seconds = self.end_slider.value()
        
        start_time_str = self.format_time(start_seconds)
        end_time_str = self.format_time(end_seconds)
        
        self.range_label.setText(f"{start_time_str} - {end_time_str}")
    
    def save_window_settings(self):
        """Save window settings to configuration"""
        self.settings.set("window_geometry", self.saveGeometry())
        self.settings.set("window_state", self.saveState())
        self.settings.save()
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.save_window_settings()
        
        if self.video_processor:
            self.video_processor.close()
        
        event.accept()
