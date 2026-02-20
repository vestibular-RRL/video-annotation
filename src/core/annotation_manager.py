"""
Annotation Manager
"""

import json
from typing import Dict, List, Optional


class AnnotationManager:
    """Manages annotation data for video frames"""
    
    def __init__(self):
        self.annotations: Dict[int, str] = {}  # frame_number -> annotation_string
        self.selected_frame: Optional[int] = None
    
    def add_annotation(self, frame_number: int, annotation_text: str) -> bool:
        """Add or update an annotation for a frame"""
        if frame_number < 1:
            return False

        normalized_annotation = "" if annotation_text is None else str(annotation_text).strip()
        if normalized_annotation in {"", "0"}:
            self.annotations.pop(frame_number, None)
            return True

        self.annotations[frame_number] = normalized_annotation
        return True
    
    def update_annotation(self, frame_number: int, annotation_text: str) -> bool:
        """Update an existing annotation"""
        return self.add_annotation(frame_number, annotation_text)
    
    def remove_annotation(self, frame_number: int) -> bool:
        """Remove an annotation for a frame"""
        if frame_number in self.annotations:
            del self.annotations[frame_number]
            return True
        return False
    
    def get_annotation(self, frame_number: int) -> Optional[str]:
        """Get annotation for a specific frame"""
        return self.annotations.get(frame_number)
    
    def get_all_annotations(self) -> Dict[int, str]:
        """Get all annotations"""
        return self.annotations.copy()
    
    def get_annotations_for_frames(self, frame_numbers: List[int]) -> Dict[int, str]:
        """Get annotations for specific frames"""
        result = {}
        for frame_num in frame_numbers:
            if frame_num in self.annotations:
                result[frame_num] = self.annotations[frame_num]
        return result
    
    def clear_annotations(self):
        """Clear all annotations"""
        self.annotations.clear()
        self.selected_frame = None
    
    def has_annotation(self, frame_number: int) -> bool:
        """Check if a frame has an annotation"""
        return frame_number in self.annotations
    
    def get_total_annotations(self) -> int:
        """Get total number of annotated frames"""
        return len(self.annotations)
    
    def get_annotated_frames(self) -> List[int]:
        """Get list of frame numbers that have annotations"""
        return list(self.annotations.keys())
    
    def get_annotation_statistics(self) -> Dict:
        """Get annotation statistics"""
        total_frames = max(self.annotations.keys()) if self.annotations else 0
        annotated_frames = len(self.annotations)
        
        return {
            "total_frames": total_frames,
            "annotated_frames": annotated_frames,
            "annotation_rate": annotated_frames / total_frames if total_frames > 0 else 0
        }
    
    def save_annotations(self, file_path: str, annotations: Optional[Dict[int, str]] = None) -> bool:
        """Save annotations to a JSON file"""
        try:
            data_to_save = annotations if annotations is not None else self.annotations
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving annotations: {e}")
            return False
    
    def load_annotations(self, file_path: str) -> bool:
        """Load annotations from a JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate data structure
            if isinstance(data, dict):
                # Convert keys to integers if they're strings
                self.annotations = {}
                for key, value in data.items():
                    try:
                        frame_num = int(key)
                        if isinstance(value, str):
                            self.annotations[frame_num] = value
                    except ValueError:
                        continue
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error loading annotations: {e}")
            return False
    
    def export_to_csv_data(self) -> List[Dict]:
        """Export annotations to CSV-compatible data"""
        if not self.annotations:
            return []
        
        data = []
        max_frame = max(self.annotations.keys())
        
        for frame_num in range(1, max_frame + 1):
            annotation = self.annotations.get(frame_num, "0")
            data.append({
                "Frame#": frame_num,
                "Annotation": annotation
            })
        
        return data
    
    def import_from_csv_data(self, data: List[Dict]) -> bool:
        """Import annotations from CSV-compatible data"""
        try:
            self.annotations.clear()
            
            for row in data:
                if "Frame#" in row and "Annotation" in row:
                    try:
                        frame_num = int(row["Frame#"])
                        annotation = str(row["Annotation"])
                        
                        if annotation != "0":  # Only store non-zero annotations
                            self.annotations[frame_num] = annotation
                    except (ValueError, TypeError):
                        continue
            
            return True
        except Exception as e:
            print(f"Error importing annotations: {e}")
            return False
    
    def get_frame_range_annotations(self, start_frame: int, end_frame: int) -> Dict[int, str]:
        """Get annotations for a range of frames"""
        result = {}
        for frame_num in range(start_frame, end_frame + 1):
            if frame_num in self.annotations:
                result[frame_num] = self.annotations[frame_num]
        return result
    
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes"""
        # For now, always return True if there are annotations
        # In a more sophisticated implementation, you might track changes
        return len(self.annotations) > 0
