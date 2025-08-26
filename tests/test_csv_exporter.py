"""
Tests for CSV Exporter
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from src.core.csv_exporter import CSVExporter
from src.models.annotation import Annotation
from src.models.video_data import VideoData


class TestCSVExporter:
    """Test cases for CSVExporter class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.exporter = CSVExporter()
        
        # Create test video data
        self.video_data = VideoData(
            file_path="test_video.mp4",
            filename="test_video.mp4",
            width=1920,
            height=1080,
            fps=30.0,
            frame_count=300,
            duration=10.0
        )
        
        # Create test annotations
        self.annotation1 = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100,
            color="#FF0000",
            line_width=2,
            label="Test Object",
            notes="Test annotation"
        )
        
        self.annotation2 = Annotation(
            frame_number=2,
            annotation_type="circle",
            x1=50, y1=50, x2=80, y2=80,
            color="#00FF00",
            line_width=1,
            label="Test Circle",
            notes=""
        )
    
    def test_init(self):
        """Test CSVExporter initialization"""
        assert self.exporter.export_format == "csv"
        assert self.exporter.include_timestamp is True
        assert self.exporter.include_coordinates is True
        assert self.exporter.include_metadata is True
    
    @patch('builtins.open', create=True)
    @patch('csv.DictWriter')
    def test_export_annotations_to_csv(self, mock_csv_writer, mock_open):
        """Test exporting annotations to CSV"""
        annotations = [self.annotation1, self.annotation2]
        
        # Mock CSV writer
        mock_writer = Mock()
        mock_csv_writer.return_value = mock_writer
        
        # Test export
        result = self.exporter.export_annotations_to_csv(
            annotations, self.video_data, "test_export.csv"
        )
        
        assert result is True
        mock_open.assert_called_once()
        mock_csv_writer.assert_called_once()
        mock_writer.writeheader.assert_called_once()
        assert mock_writer.writerows.call_count == 1
    
    def test_export_annotations_to_dataframe(self):
        """Test exporting annotations to DataFrame"""
        annotations = [self.annotation1, self.annotation2]
        
        # Test export
        df = self.exporter.export_annotations_to_dataframe(
            annotations, self.video_data
        )
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'frame_number' in df.columns
        assert 'annotation_type' in df.columns
        assert 'x1' in df.columns
        assert 'y1' in df.columns
        assert 'x2' in df.columns
        assert 'y2' in df.columns
        assert 'color' in df.columns
        assert 'line_width' in df.columns
        assert 'label' in df.columns
        assert 'notes' in df.columns
    
    def test_prepare_export_data(self):
        """Test preparing export data"""
        annotations = [self.annotation1, self.annotation2]
        
        # Test with include_empty_frames=False
        export_data = self.exporter._prepare_export_data(
            annotations, self.video_data, include_empty_frames=False
        )
        
        assert len(export_data) == 2
        assert export_data[0]['frame_number'] == 1
        assert export_data[1]['frame_number'] == 2
        
        # Test with include_empty_frames=True
        export_data = self.exporter._prepare_export_data(
            annotations, self.video_data, include_empty_frames=True
        )
        
        # Should include all frames (300 total)
        assert len(export_data) == 300
    
    def test_annotation_to_row(self):
        """Test converting annotation to CSV row"""
        row = self.exporter._annotation_to_row(self.annotation1, self.video_data)
        
        assert row['frame_number'] == 1
        assert row['annotation_type'] == 'rectangle'
        assert row['x1'] == 10
        assert row['y1'] == 10
        assert row['x2'] == 100
        assert row['y2'] == 100
        assert row['color'] == '#FF0000'
        assert row['line_width'] == 2
        assert row['label'] == 'Test Object'
        assert row['notes'] == 'Test annotation'
        assert 'timestamp' in row
    
    def test_empty_frame_to_row(self):
        """Test converting empty frame to CSV row"""
        row = self.exporter._empty_frame_to_row(5, self.video_data)
        
        assert row['frame_number'] == 5
        assert row['annotation_type'] == ''
        assert row['x1'] == ''
        assert row['y1'] == ''
        assert row['x2'] == ''
        assert row['y2'] == ''
        assert row['color'] == ''
        assert row['line_width'] == ''
        assert row['label'] == ''
        assert row['notes'] == ''
        assert 'timestamp' in row
    
    @patch('builtins.open', create=True)
    @patch('csv.DictWriter')
    def test_export_frame_summary(self, mock_csv_writer, mock_open):
        """Test exporting frame summary"""
        annotations = [self.annotation1, self.annotation2]
        
        # Mock CSV writer
        mock_writer = Mock()
        mock_csv_writer.return_value = mock_writer
        
        # Test export
        result = self.exporter.export_frame_summary(
            annotations, self.video_data, "test_summary.csv"
        )
        
        assert result is True
        mock_open.assert_called_once()
        mock_csv_writer.assert_called_once()
        mock_writer.writeheader.assert_called_once()
        assert mock_writer.writerows.call_count == 1
    
    @patch('builtins.open', create=True)
    @patch('csv.DictWriter')
    def test_export_statistics(self, mock_csv_writer, mock_open):
        """Test exporting statistics"""
        annotations = [self.annotation1, self.annotation2]
        
        # Mock CSV writer
        mock_writer = Mock()
        mock_csv_writer.return_value = mock_writer
        
        # Test export
        result = self.exporter.export_statistics(
            annotations, self.video_data, "test_stats.csv"
        )
        
        assert result is True
        mock_open.assert_called_once()
        mock_csv_writer.assert_called_once()
        mock_writer.writeheader.assert_called_once()
        assert mock_writer.writerows.call_count == 1
    
    def test_export_error_handling(self):
        """Test error handling in export functions"""
        # Test with invalid file path
        result = self.exporter.export_annotations_to_csv(
            [], self.video_data, "/invalid/path/test.csv"
        )
        
        # Should return False on error
        assert result is False
    
    def test_dataframe_export_with_empty_annotations(self):
        """Test DataFrame export with empty annotations"""
        df = self.exporter.export_annotations_to_dataframe([], self.video_data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        # Should still have the expected columns
        expected_columns = [
            'frame_number', 'timestamp', 'annotation_type',
            'x1', 'y1', 'x2', 'y2', 'color', 'line_width', 'label', 'notes'
        ]
        for col in expected_columns:
            assert col in df.columns
