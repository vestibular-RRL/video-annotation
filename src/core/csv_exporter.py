"""
CSV Exporter
"""

import csv
import os
from itertools import chain
from time import perf_counter
from typing import List, Dict, Optional, Iterable, Callable, Any

import pandas as pd
from pathlib import Path
from .video_trimmer import VideoTrimmer


class CSVExporter:
    """Handles export of annotation data to CSV format"""
    
    def __init__(self):
        self.video_trimmer = VideoTrimmer()
    
    def export_annotations_to_csv(
        self,
        data: Iterable[Dict[str, Any]],
        file_path: str,
        method: str = "fast",
        chunk_size: int = 5000,
        process_callback: Optional[Callable[[], None]] = None,
    ) -> bool:
        """Export annotations to CSV file.

        Args:
            data: Iterable of rows containing at least Frame# and Annotation keys
            file_path: Destination CSV path
            method: "fast" (streaming csv module) or "pandas"
            chunk_size: Callback interval in rows for the fast method
            process_callback: Optional callback to keep UI responsive during long exports
        """
        if method == "pandas":
            return self._export_annotations_to_csv_pandas(data, file_path)
        return self._export_annotations_to_csv_fast(data, file_path, chunk_size, process_callback)

    def export_annotations_to_csv_with_metrics(
        self,
        data: Iterable[Dict[str, Any]],
        file_path: str,
        method: str = "fast",
        chunk_size: int = 5000,
        process_callback: Optional[Callable[[], None]] = None,
    ) -> Dict[str, Any]:
        """Export annotations and return timing/blocking metrics."""
        start = perf_counter()
        try:
            if method == "pandas":
                success = self._export_annotations_to_csv_pandas(data, file_path)
                elapsed = perf_counter() - start
                return {
                    "success": success,
                    "method": "pandas",
                    "rows_written": None,
                    "duration_seconds": elapsed,
                    "max_block_seconds": elapsed,
                    "chunk_count": 1,
                }

            success, rows_written, max_block_seconds, chunk_count = self._export_annotations_to_csv_fast(
                data,
                file_path,
                chunk_size,
                process_callback,
                collect_metrics=True,
            )
            elapsed = perf_counter() - start
            return {
                "success": success,
                "method": "fast",
                "rows_written": rows_written,
                "duration_seconds": elapsed,
                "max_block_seconds": max_block_seconds,
                "chunk_count": chunk_count,
            }
        except Exception as e:
            elapsed = perf_counter() - start
            print(f"Error exporting to CSV with metrics: {e}")
            return {
                "success": False,
                "method": method,
                "rows_written": 0,
                "duration_seconds": elapsed,
                "max_block_seconds": elapsed,
                "chunk_count": 0,
                "error": str(e),
            }

    def _export_annotations_to_csv_pandas(self, data: Iterable[Dict[str, Any]], file_path: str) -> bool:
        """Legacy pandas export path used as fallback and benchmark baseline."""
        try:
            rows = data if isinstance(data, list) else list(data)
            df = pd.DataFrame(rows)

            if "Frame#" not in df.columns or "Annotation" not in df.columns:
                return False

            df.to_csv(file_path, index=False, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error exporting to CSV with pandas: {e}")
            return False

    def _export_annotations_to_csv_fast(
        self,
        data: Iterable[Dict[str, Any]],
        file_path: str,
        chunk_size: int,
        process_callback: Optional[Callable[[], None]],
        collect_metrics: bool = False,
    ):
        """Fast streaming CSV export path using Python's csv module."""
        try:
            iterator = iter(data)
            first_row = next(iterator, None)
            if first_row is None:
                return (False, 0, 0.0, 0) if collect_metrics else False

            if not isinstance(first_row, dict):
                return (False, 0, 0.0, 0) if collect_metrics else False

            fieldnames = list(first_row.keys())
            if "Frame#" not in fieldnames or "Annotation" not in fieldnames:
                return (False, 0, 0.0, 0) if collect_metrics else False

            rows_written = 0
            chunk_count = 0
            max_block_seconds = 0.0
            block_start = perf_counter()

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()

                for row in chain([first_row], iterator):
                    if not isinstance(row, dict):
                        continue

                    writer.writerow({column: row.get(column, "") for column in fieldnames})
                    rows_written += 1

                    if process_callback and rows_written % max(1, chunk_size) == 0:
                        chunk_count += 1
                        now = perf_counter()
                        max_block_seconds = max(max_block_seconds, now - block_start)
                        process_callback()
                        block_start = perf_counter()

                if process_callback:
                    now = perf_counter()
                    max_block_seconds = max(max_block_seconds, now - block_start)
                    process_callback()

            if collect_metrics:
                if not process_callback:
                    max_block_seconds = 0.0
                    chunk_count = 1
                elif rows_written % max(1, chunk_size) != 0:
                    chunk_count += 1
                return True, rows_written, max_block_seconds, chunk_count

            return True
        except Exception as e:
            print(f"Error exporting to CSV with fast method: {e}")
            return (False, 0, 0.0, 0) if collect_metrics else False
    
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
                    summary_filename = f"{custom_name}_summary.json"
                else:
                    summary_filename = "export_summary.json"
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
        Create a summary file with export details in JSON format
        
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
            import json
            from datetime import datetime
            
            # Calculate duration
            duration_seconds = (end_frame - start_frame + 1) / fps
            duration_str = self.video_trimmer.format_duration(duration_seconds)
            
            # Get video info
            video_info = self.video_trimmer.get_video_info(video_path)
            
            # Create structured data for JSON export
            summary_data = {
                "export_info": {
                    "export_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "export_type": "video_annotation_export"
                },
                "original_video": {
                    "filename": os.path.basename(video_path),
                    "full_path": video_path,
                    "resolution": f"{video_info['width']}x{video_info['height']}" if video_info else None,
                    "fps": round(video_info['fps'], 2) if video_info else None,
                    "total_frames": video_info['frame_count'] if video_info else None,
                    "total_duration": self.video_trimmer.format_duration(video_info['duration']) if video_info else None,
                    "duration_seconds": video_info['duration'] if video_info else None
                },
                "exported_range": {
                    "start_frame": start_frame,
                    "end_frame": end_frame,
                    "frame_count": end_frame - start_frame + 1,
                    "duration": duration_str,
                    "duration_seconds": duration_seconds,
                    "fps": round(fps, 2)
                },
                "exported_files": {
                    "video": {
                        "status": "created" if video_success else "failed",
                        "success": video_success
                    },
                    "csv": {
                        "status": "created",
                        "success": True,
                        "annotation_count": annotation_count
                    },
                    "summary": {
                        "status": "created",
                        "success": True,
                        "format": "json"
                    }
                },
                "notes": [
                    "The trimmed video contains only the specified frame range",
                    "The CSV file contains annotations for the specified frame range only",
                    "All files are located in the same folder for easy access"
                ]
            }
            
            # Write JSON file with proper formatting
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
                
            print(f"Summary file created: {summary_path}")
            
        except Exception as e:
            print(f"Error creating summary file: {e}")