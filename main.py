#!/usr/bin/env python3
"""
Video Annotation Tool - Main Application Entry Point
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.gui.main_window import MainWindow
from config.settings import load_settings


def main():
    """Main application entry point"""
    # Redirect stderr to suppress AV1 error messages
    import io
    import contextlib
    
    # Set environment variables for better video compatibility
    os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'windowsmedia'
    os.environ['QT_LOGGING_RULES'] = 'qt.multimedia.*=false;qt.av.*=false;qt.media.*=false'
    os.environ['FFREPORT'] = '0'  # Disable FFmpeg reporting
    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'hwaccel=none'  # Disable hardware acceleration
    os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'  # Disable OpenCV video debug output
    os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'  # Disable Media Foundation priority
    os.environ['OPENCV_VIDEOIO_PRIORITY_INTEL_MFX'] = '0'  # Disable Intel Media SDK
    os.environ['OPENCV_VIDEOIO_PRIORITY_VAAPI'] = '0'  # Disable VAAPI
    os.environ['OPENCV_VIDEOIO_PRIORITY_FFMPEG'] = '1'  # Enable FFmpeg backend
    os.environ['OPENCV_VIDEOIO_FFMPEG_CAPTURE_OPTIONS'] = 'hwaccel=none'  # Force software decoding
    
    # Suppress AV1 error messages by redirecting stderr
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stderr(devnull):
            # Create Qt application
            app = QApplication(sys.argv)
            app.setApplicationName("Video Annotation Tool")
            app.setApplicationVersion("1.0.0")
            
            # Load application settings
            settings = load_settings()
            
            # Create and show main window
            main_window = MainWindow(settings)
            main_window.show()
            
            # Start application event loop
            sys.exit(app.exec())


if __name__ == "__main__":
    main()
