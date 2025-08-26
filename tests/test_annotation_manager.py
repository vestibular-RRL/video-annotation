"""
Tests for Annotation Manager
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.core.annotation_manager import AnnotationManager
from src.models.annotation import Annotation


class TestAnnotationManager:
    """Test cases for AnnotationManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.manager = AnnotationManager()
    
    def test_init(self):
        """Test AnnotationManager initialization"""
        assert self.manager.annotations == {}
        assert self.manager.selected_annotations == set()
        assert self.manager.current_annotation is None
        assert self.manager.annotation_file_path is None
    
    def test_add_annotation(self):
        """Test adding annotation"""
        annotation = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100
        )
        
        result = self.manager.add_annotation(annotation)
        
        assert result is True
        assert 1 in self.manager.annotations
        assert len(self.manager.annotations[1]) == 1
        assert self.manager.annotations[1][0] == annotation
    
    def test_remove_annotation(self):
        """Test removing annotation"""
        annotation = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100
        )
        
        # Add annotation first
        self.manager.add_annotation(annotation)
        
        # Remove annotation
        result = self.manager.remove_annotation(annotation)
        
        assert result is True
        assert 1 not in self.manager.annotations
    
    def test_get_annotations_for_frame(self):
        """Test getting annotations for specific frame"""
        annotation1 = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100
        )
        annotation2 = Annotation(
            frame_number=1,
            annotation_type="circle",
            x1=50, y1=50, x2=80, y2=80
        )
        
        # Add annotations
        self.manager.add_annotation(annotation1)
        self.manager.add_annotation(annotation2)
        
        # Get annotations for frame 1
        annotations = self.manager.get_annotations_for_frame(1)
        
        assert len(annotations) == 2
        assert annotation1 in annotations
        assert annotation2 in annotations
    
    def test_get_all_annotations(self):
        """Test getting all annotations"""
        annotation1 = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100
        )
        annotation2 = Annotation(
            frame_number=2,
            annotation_type="circle",
            x1=50, y1=50, x2=80, y2=80
        )
        
        # Add annotations
        self.manager.add_annotation(annotation1)
        self.manager.add_annotation(annotation2)
        
        # Get all annotations
        all_annotations = self.manager.get_all_annotations()
        
        assert len(all_annotations) == 2
        assert annotation1 in all_annotations
        assert annotation2 in all_annotations
    
    def test_select_annotation(self):
        """Test selecting annotation"""
        annotation = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100
        )
        
        # Add annotation
        self.manager.add_annotation(annotation)
        
        # Select annotation
        result = self.manager.select_annotation(annotation)
        
        assert result is True
        assert annotation in self.manager.selected_annotations
    
    def test_clear_selection(self):
        """Test clearing selection"""
        annotation = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100
        )
        
        # Add and select annotation
        self.manager.add_annotation(annotation)
        self.manager.select_annotation(annotation)
        
        # Clear selection
        self.manager.clear_selection()
        
        assert len(self.manager.selected_annotations) == 0
    
    def test_get_frame_statistics(self):
        """Test getting frame statistics"""
        annotation1 = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100
        )
        annotation2 = Annotation(
            frame_number=1,
            annotation_type="circle",
            x1=50, y1=50, x2=80, y2=80
        )
        
        # Add annotations
        self.manager.add_annotation(annotation1)
        self.manager.add_annotation(annotation2)
        
        # Get statistics
        stats = self.manager.get_frame_statistics(1)
        
        assert stats['total_annotations'] == 2
        assert stats['frame_number'] == 1
        assert stats['type_counts']['rectangle'] == 1
        assert stats['type_counts']['circle'] == 1
    
    def test_get_project_statistics(self):
        """Test getting project statistics"""
        annotation1 = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100,
            color="#FF0000"
        )
        annotation2 = Annotation(
            frame_number=2,
            annotation_type="circle",
            x1=50, y1=50, x2=80, y2=80,
            color="#00FF00"
        )
        
        # Add annotations
        self.manager.add_annotation(annotation1)
        self.manager.add_annotation(annotation2)
        
        # Get statistics
        stats = self.manager.get_project_statistics()
        
        assert stats['total_annotations'] == 2
        assert stats['frames_with_annotations'] == 2
        assert stats['type_counts']['rectangle'] == 1
        assert stats['type_counts']['circle'] == 1
        assert stats['color_counts']['#FF0000'] == 1
        assert stats['color_counts']['#00FF00'] == 1
    
    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_save_annotations(self, mock_json_dump, mock_open):
        """Test saving annotations"""
        annotation = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100
        )
        
        # Add annotation
        self.manager.add_annotation(annotation)
        
        # Save annotations
        result = self.manager.save_annotations("test_annotations.json")
        
        assert result is True
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()
    
    @patch('builtins.open', create=True)
    @patch('json.load')
    def test_load_annotations(self, mock_json_load, mock_open):
        """Test loading annotations"""
        # Mock JSON data
        mock_data = {
            'annotations': {
                '1': [{
                    'frame_number': 1,
                    'annotation_type': 'rectangle',
                    'x1': 10, 'y1': 10, 'x2': 100, 'y2': 100,
                    'color': '#FF0000',
                    'line_width': 2,
                    'label': '',
                    'notes': '',
                    'timestamp': None,
                    'points': None
                }]
            }
        }
        mock_json_load.return_value = mock_data
        
        # Load annotations
        result = self.manager.load_annotations("test_annotations.json")
        
        assert result is True
        assert len(self.manager.get_all_annotations()) == 1
    
    def test_clear_all_annotations(self):
        """Test clearing all annotations"""
        annotation = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100
        )
        
        # Add annotation
        self.manager.add_annotation(annotation)
        self.manager.select_annotation(annotation)
        
        # Clear all
        self.manager.clear_all_annotations()
        
        assert len(self.manager.annotations) == 0
        assert len(self.manager.selected_annotations) == 0
        assert self.manager.current_annotation is None
    
    def test_has_unsaved_changes(self):
        """Test checking for unsaved changes"""
        # Initially no changes
        assert self.manager.has_unsaved_changes() is False
        
        # Add annotation
        annotation = Annotation(
            frame_number=1,
            annotation_type="rectangle",
            x1=10, y1=10, x2=100, y2=100
        )
        self.manager.add_annotation(annotation)
        
        # Now has changes
        assert self.manager.has_unsaved_changes() is True
