"""
Tests for Video Processor
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.core.video_processor import VideoProcessor
from src.models.video_data import VideoData


class TestVideoProcessor:
    """Test cases for VideoProcessor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = VideoProcessor()
    
    def test_init(self):
        """Test VideoProcessor initialization"""
        assert self.processor.video_capture is None
        assert self.processor.video_data is None
        assert self.processor.current_frame_number == 0
    
    @patch('cv2.VideoCapture')
    def test_load_video_success(self, mock_cv2):
        """Test successful video loading"""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            3: 1920,  # CAP_PROP_FRAME_WIDTH
            4: 1080,  # CAP_PROP_FRAME_HEIGHT
            5: 30.0,  # CAP_PROP_FPS
            7: 300,   # CAP_PROP_FRAME_COUNT
            6: 123456, # CAP_PROP_FOURCC
            12: 1000000 # CAP_PROP_BITRATE
        }.get(prop, 0)
        
        mock_cv2.return_value = mock_cap
        
        # Test loading video
        result = self.processor.load_video("test_video.mp4")
        
        assert result is True
        assert self.processor.video_data is not None
        assert self.processor.video_data.width == 1920
        assert self.processor.video_data.height == 1080
        assert self.processor.video_data.fps == 30.0
        assert self.processor.video_data.frame_count == 300
    
    @patch('cv2.VideoCapture')
    def test_load_video_failure(self, mock_cv2):
        """Test video loading failure"""
        # Mock video capture that fails to open
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_cv2.return_value = mock_cap
        
        # Test loading video should raise exception
        with pytest.raises(ValueError):
            self.processor.load_video("test_video.mp4")
    
    def test_get_frame_no_video(self):
        """Test getting frame when no video is loaded"""
        frame = self.processor.get_frame(0)
        assert frame is None
    
    @patch('cv2.VideoCapture')
    def test_get_frame_success(self, mock_cv2):
        """Test successful frame extraction"""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            3: 1920,  # CAP_PROP_FRAME_WIDTH
            4: 1080,  # CAP_PROP_FRAME_HEIGHT
            5: 30.0,  # CAP_PROP_FPS
            7: 300,   # CAP_PROP_FRAME_COUNT
            6: 123456, # CAP_PROP_FOURCC
            12: 1000000 # CAP_PROP_BITRATE
        }.get(prop, 0)
        mock_cap.read.return_value = (True, np.zeros((1080, 1920, 3), dtype=np.uint8))
        
        mock_cv2.return_value = mock_cap
        
        # Load video
        self.processor.load_video("test_video.mp4")
        
        # Test getting frame
        frame = self.processor.get_frame(0)
        assert frame is not None
        assert frame.shape == (1080, 1920, 3)
    
    def test_format_time(self):
        """Test time formatting"""
        # Test various time values
        assert self.processor._format_time(0) == "00:00:00.000"
        assert self.processor._format_time(61.5) == "00:01:01.500"
        assert self.processor._format_time(3661.123) == "01:01:01.123"
    
    def test_close(self):
        """Test video processor close"""
        # Mock video capture
        mock_cap = Mock()
        self.processor.video_capture = mock_cap
        self.processor.video_data = Mock()
        
        # Test close
        self.processor.close()
        
        # Verify release was called
        mock_cap.release.assert_called_once()
        assert self.processor.video_capture is None
        assert self.processor.video_data is None
