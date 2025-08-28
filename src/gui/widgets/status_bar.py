"""
Status Bar Widget
"""

from PyQt6.QtWidgets import QStatusBar, QLabel, QProgressBar, QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from src.models.video_data import VideoData
from config.constants import REPORT_PROBLEM_URL


class StatusBar(QStatusBar):
    """Custom status bar for displaying application status"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Video info label
        self.video_info_label = QLabel("No video loaded")
        self.video_info_label.setMinimumWidth(200)
        self.addWidget(self.video_info_label)
        
        # Separator
        self.addPermanentWidget(QLabel("|"))
        
        # Frame info label
        self.frame_info_label = QLabel("Frame: 0 / 0")
        self.frame_info_label.setMinimumWidth(150)
        self.addPermanentWidget(self.frame_info_label)
        
        # Separator
        self.addPermanentWidget(QLabel("|"))
        
        # Annotation count label
        self.annotation_count_label = QLabel("Annotations: 0")
        self.annotation_count_label.setMinimumWidth(120)
        self.addPermanentWidget(self.annotation_count_label)
        
        # Separator
        self.addPermanentWidget(QLabel("|"))
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.addPermanentWidget(self.progress_bar)
        

        
        # Report Problem button
        self.report_button = QPushButton("Report Problem")
        self.report_button.setMaximumWidth(120)
        self.report_button.clicked.connect(self.report_problem)
        self.addPermanentWidget(self.report_button)
    
    def update_video_info(self, video_data: VideoData):
        """Update video information display"""
        if video_data:
            filename = video_data.file_path.split('/')[-1] if '/' in video_data.file_path else video_data.file_path
            resolution = f"{video_data.width}x{video_data.height}"
            duration = self.format_time(video_data.duration)
            
            info_text = f"{filename} | {resolution} | {duration} | {video_data.fps:.2f} FPS"
            self.video_info_label.setText(info_text)
        else:
            self.video_info_label.setText("No video loaded")
    
    def update_frame_info(self, current_frame: int, video_data: VideoData):
        """Update frame information display"""
        if video_data:
            total_frames = video_data.total_frames
            current_time = (current_frame - 1) / video_data.fps
            time_str = self.format_time(current_time)
            
            frame_text = f"Frame: {current_frame} / {total_frames} | {time_str}"
            self.frame_info_label.setText(frame_text)
        else:
            self.frame_info_label.setText("Frame: 0 / 0")
    
    def update_annotation_count(self, count: int):
        """Update annotation count display"""
        self.annotation_count_label.setText(f"Annotations: {count}")
    

    
    def show_progress(self, visible: bool = True):
        """Show or hide progress bar"""
        self.progress_bar.setVisible(visible)
    
    def set_progress(self, value: int, maximum: int = 100):
        """Set progress bar value"""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
    
    def show_message(self, message: str, timeout: int = 5000):
        """Show temporary message"""
        self.showMessage(message, timeout)
    
    def clear_message(self):
        """Clear temporary message"""
        self.clearMessage()
    
    def format_time(self, seconds: float) -> str:
        """Format time in HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def show_status(self, video_data: VideoData, current_frame: int, annotation_count: int):
        """Update all status information at once"""
        self.update_video_info(video_data)
        self.update_frame_info(current_frame, video_data)
        self.update_annotation_count(annotation_count)

    def report_problem(self):
        """Open the report problem link in the default browser"""
        try:
            # You can replace this URL with your actual contact/issue reporting link
            report_url = REPORT_PROBLEM_URL
            
            # Alternative URLs you might want to use:
            # report_url = "mailto:your-email@example.com?subject=Video Annotation Tool - Problem Report"
            # report_url = "https://forms.gle/your-google-form-id"
            # report_url = "https://your-website.com/contact"
            
            # Open the URL in the default browser
            QDesktopServices.openUrl(QUrl(report_url))
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", 
                              f"Could not open the report problem link.\n"
                              f"Error: {str(e)}\n\n"
                              f"Please manually visit: {report_url}")
