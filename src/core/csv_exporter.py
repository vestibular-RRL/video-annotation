"""
CSV Exporter
"""

import pandas as pd
import os
from typing import List, Dict, Optional
from pathlib import Path
from .video_trimmer import VideoTrimmer


class CSVExporter:
    """Handles export of annotation data to CSV format"""
    
    def __init__(self):
        self.video_trimmer = VideoTrimmer()
    
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

    def export_with_trimmed_video(self, data: List[Dict], output_path: str, 
                             video_path: str, start_frame: int, end_frame: int,
                             fps: float, custom_name: str = None) -> bool:
        """
        Export CSV with trimmed video in a dedicated folder with custom naming
        
        Args:
            data: Annotation data
            output_path: Base output path for CSV file
            video_path: Path to original video file
            start_frame: Starting frame for trimming
            end_frame: Ending frame for trimming
            fps: Video frame rate
            custom_name: Custom name for the output folder and files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get base directory and filename
            base_dir = os.path.dirname(output_path)
            csv_filename = os.path.basename(output_path)
            
            # Generate folder name
            if custom_name:
                # Use custom name provided by user
                folder_name = custom_name
            else:
                # Generate default name from video and frame range
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                folder_name = f"{video_name}_frames_{start_frame}_to_{end_frame}"
            
            # Create output folder
            output_folder = self.video_trimmer.create_output_folder(base_dir, folder_name)
            
            # Create trimmed video path with custom name
            if custom_name:
                video_filename = f"{custom_name}.mp4"
            else:
                video_filename = f"trimmed_video_frames_{start_frame}_to_{end_frame}.mp4"
            trimmed_video_path = os.path.join(output_folder, video_filename)
            
            # Trim the video
            print(f"Creating trimmed video: {trimmed_video_path}")
            video_success = self.video_trimmer.trim_video_by_frames(
                video_path, trimmed_video_path, start_frame, end_frame, fps
            )
            
            if not video_success:
                print("Warning: Failed to create trimmed video")
            
            # Create CSV path in the same folder with custom name
            if custom_name:
                csv_filename = f"{custom_name}.csv"
            csv_path = os.path.join(output_folder, csv_filename)
            
            # Filter data to only include frames in the range
            filtered_data = []
            for row in data:
                frame_num = row.get("Frame#", 0)
                if start_frame <= frame_num <= end_frame:
                    filtered_data.append(row)
            
            # Export filtered CSV
            csv_success = self.export_annotations_to_csv(filtered_data, csv_path)
            
            if csv_success:
                print(f"CSV exported successfully: {csv_path}")
                print(f"Output folder: {output_folder}")
                
                # Create a summary file with custom name
                if custom_name:
                    summary_filename = f"{custom_name}_summary.txt"
                else:
                    summary_filename = "export_summary.txt"
                summary_path = os.path.join(output_folder, summary_filename)
                
                self._create_summary_file(summary_path, video_path, start_frame, end_frame, 
                                        fps, len(filtered_data), video_success)
                
                return True
            else:
                print("Error: Failed to export CSV")
                return False
                
        except Exception as e:
            print(f"Error in export_with_trimmed_video: {e}")
            return False
    
    def _create_summary_file(self, summary_path: str, video_path: str, start_frame: int, 
                           end_frame: int, fps: float, annotation_count: int, 
                           video_success: bool) -> None:
        """
        Create a summary file with export details
        
        Args:
            summary_path: Path to the summary file
            video_path: Path to original video file
            start_frame: Starting frame number
            end_frame: Ending frame number
            fps: Video frame rate
            annotation_count: Number of annotations exported
            video_success: Whether video trimming was successful
        """
        try:
            from datetime import datetime
            
            # Calculate duration
            duration_seconds = (end_frame - start_frame + 1) / fps
            duration_str = self.video_trimmer.format_duration(duration_seconds)
            
            # Get video info
            video_info = self.video_trimmer.get_video_info(video_path)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("VIDEO ANNOTATION EXPORT SUMMARY\n")
                f.write("=" * 40 + "\n\n")
                
                f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("ORIGINAL VIDEO:\n")
                f.write(f"  File: {os.path.basename(video_path)}\n")
                f.write(f"  Path: {video_path}\n")
                if video_info:
                    f.write(f"  Resolution: {video_info['width']}x{video_info['height']}\n")
                    f.write(f"  FPS: {video_info['fps']:.2f}\n")
                    f.write(f"  Total Frames: {video_info['frame_count']}\n")
                    f.write(f"  Total Duration: {self.video_trimmer.format_duration(video_info['duration'])}\n")
                f.write("\n")
                
                f.write("EXPORTED RANGE:\n")
                f.write(f"  Start Frame: {start_frame}\n")
                f.write(f"  End Frame: {end_frame}\n")
                f.write(f"  Frame Count: {end_frame - start_frame + 1}\n")
                f.write(f"  Duration: {duration_str}\n")
                f.write(f"  FPS: {fps:.2f}\n\n")
                
                f.write("EXPORTED FILES:\n")
                f.write(f"  Video: {'✓ Created' if video_success else '✗ Failed'}\n")
                f.write(f"  CSV: ✓ Created ({annotation_count} annotations)\n")
                f.write(f"  Summary: ✓ Created\n\n")
                
                f.write("NOTES:\n")
                f.write("- The trimmed video contains only the specified frame range\n")
                f.write("- The CSV file contains annotations for the specified frame range only\n")
                f.write("- All files are located in the same folder for easy access\n")
                
            print(f"Summary file created: {summary_path}")
            
        except Exception as e:
            print(f"Error creating summary file: {e}")