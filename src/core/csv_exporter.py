"""
CSV Exporter
"""

import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path


class CSVExporter:
    """Handles export of annotation data to CSV format"""
    
    def __init__(self):
        pass
    
    def export_annotations_to_csv(self, data: List[Dict], file_path: str) -> bool:
        """Export annotations to CSV file"""
        try:
            # Create DataFrame from data
            df = pd.DataFrame(data)
            
            # Ensure required columns exist
            if "Frame#" not in df.columns or "Annotation" not in df.columns:
                return False
            
            # Export to CSV
            df.to_csv(file_path, index=False, encoding='utf-8')
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def export_annotations_to_dataframe(self, data: List[Dict]) -> Optional[pd.DataFrame]:
        """Export annotations to pandas DataFrame"""
        try:
            df = pd.DataFrame(data)
            
            # Ensure required columns exist
            if "Frame#" not in df.columns or "Annotation" not in df.columns:
                return None
            
            return df
            
        except Exception as e:
            print(f"Error creating DataFrame: {e}")
            return None
    
    def create_annotation_template(self, total_frames: int) -> List[Dict]:
        """Create a template for annotations with all frames"""
        template = []
        for frame_num in range(1, total_frames + 1):
            template.append({
                "Frame#": frame_num,
                "Annotation": "0"
            })
        return template
    
    def merge_annotations_with_template(self, annotations: Dict[int, str], total_frames: int) -> List[Dict]:
        """Merge annotations with a template to ensure all frames are included"""
        template = self.create_annotation_template(total_frames)
        
        # Update template with actual annotations
        for frame_num, annotation in annotations.items():
            if 1 <= frame_num <= total_frames:
                template[frame_num - 1]["Annotation"] = annotation
        
        return template
    
    def validate_csv_data(self, data: List[Dict]) -> bool:
        """Validate CSV data structure"""
        if not data:
            return False
        
        # Check if all rows have required columns
        required_columns = {"Frame#", "Annotation"}
        
        for row in data:
            if not isinstance(row, dict):
                return False
            
            if not required_columns.issubset(set(row.keys())):
                return False
            
            # Validate frame number
            try:
                frame_num = int(row["Frame#"])
                if frame_num < 1:
                    return False
            except (ValueError, TypeError):
                return False
            
            # Validate annotation is string
            if not isinstance(row["Annotation"], str):
                return False
        
        return True
    
    def get_csv_statistics(self, data: List[Dict]) -> Dict:
        """Get statistics from CSV data"""
        if not data:
            return {
                "total_frames": 0,
                "annotated_frames": 0,
                "annotation_rate": 0.0
            }
        
        total_frames = len(data)
        annotated_frames = sum(1 for row in data if row.get("Annotation", "0") != "0")
        
        return {
            "total_frames": total_frames,
            "annotated_frames": annotated_frames,
            "annotation_rate": annotated_frames / total_frames if total_frames > 0 else 0.0
        }
    
    def filter_annotations(self, data: List[Dict], min_frame: Optional[int] = None, 
                          max_frame: Optional[int] = None, 
                          annotation_filter: Optional[str] = None) -> List[Dict]:
        """Filter annotations based on criteria"""
        filtered_data = []
        
        for row in data:
            frame_num = row.get("Frame#", 0)
            annotation = row.get("Annotation", "")
            
            # Frame range filter
            if min_frame is not None and frame_num < min_frame:
                continue
            if max_frame is not None and frame_num > max_frame:
                continue
            
            # Annotation filter
            if annotation_filter is not None and annotation_filter not in annotation:
                continue
            
            filtered_data.append(row)
        
        return filtered_data
    
    def sort_annotations(self, data: List[Dict], sort_by: str = "Frame#", 
                        ascending: bool = True) -> List[Dict]:
        """Sort annotations by specified column"""
        try:
            df = pd.DataFrame(data)
            df_sorted = df.sort_values(by=sort_by, ascending=ascending)
            return df_sorted.to_dict('records')
        except Exception as e:
            print(f"Error sorting data: {e}")
            return data
    
    def convert_to_annotation_dict(self, data: List[Dict]) -> Dict[int, str]:
        """Convert CSV data to annotation dictionary"""
        annotations = {}
        
        for row in data:
            try:
                frame_num = int(row["Frame#"])
                annotation = str(row["Annotation"])
                
                if annotation != "0":
                    annotations[frame_num] = annotation
            except (ValueError, KeyError):
                continue
        
        return annotations
    
    def convert_from_annotation_dict(self, annotations: Dict[int, str], 
                                   total_frames: int) -> List[Dict]:
        """Convert annotation dictionary to CSV data"""
        return self.merge_annotations_with_template(annotations, total_frames)
