"""
Object Tracking Module using Ultralytics YOLO Segmentation
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import os
from dataclasses import dataclass
import torch


@dataclass
class EllipseData:
    """Ellipse data extracted from segmentation mask"""
    center: Tuple[int, int]  # (x, y)
    axes: Tuple[int, int]    # (major_axis, minor_axis)
    angle: float             # rotation angle in degrees
    confidence: float        # detection confidence


@dataclass
class TrackingResult:
    """Result of object tracking for a frame"""
    frame_number: int
    detections: List[Dict]
    bounding_box_areas: List[float]  # Areas of bounding boxes instead of ellipses
    tracking_id: Optional[int] = None


def get_largest_ellipse(mask):
    """Extract the largest ellipse from a binary mask"""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if len(largest) >= 5:
            return cv2.fitEllipse(largest)
    return None


class ObjectTracker:
    """Object tracker using Ultralytics YOLO segmentation models"""
    
    def __init__(self, model_path: str = None, confidence_threshold: float = 0.5):
        """
        Initialize the object tracker
        
        Args:
            model_path: Path to custom YOLO segmentation model (.pt file)
            confidence_threshold: Minimum confidence for detections
        """
        self.model = None
        self.confidence_threshold = confidence_threshold
        self.tracking_results = {}  # frame_number -> TrackingResult
        self.tracked_objects = {}   # tracking_id -> object_info
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.frame_width = 1920  # Default frame width
        self.frame_height = 1080  # Default frame height
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            # Load default YOLO segmentation model for testing
            self.load_default_model()
    
    def load_model(self, model_path: str) -> bool:
        """Load custom YOLO segmentation model"""
        try:
            self.model = YOLO(model_path)
            print(f"Loaded custom segmentation model: {model_path}")
            print(f"Using device: {self.device}")
            return True
        except Exception as e:
            print(f"Error loading custom model: {e}")
            return False
    
    def load_default_model(self):
        """Load default YOLO segmentation model for testing"""
        try:
            self.model = YOLO('yolov8n-seg.pt')  # Segmentation model
            print("Loaded default YOLO segmentation model")
            print(f"Using device: {self.device}")
        except Exception as e:
            print(f"Error loading default model: {e}")
    
    def split_frame_vertically(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Split a frame into left and right halves
        
        Args:
            frame: Input frame
            
        Returns:
            Tuple of (left_half, right_half)
        """
        height, width = frame.shape[:2]
        mid_point = width // 2
        
        left_half = frame[:, :mid_point]
        right_half = frame[:, mid_point:]
        
        return left_half, right_half
    
    def combine_frames_horizontally(self, left_frame: np.ndarray, right_frame: np.ndarray) -> np.ndarray:
        """
        Combine left and right frames horizontally
        
        Args:
            left_frame: Left half frame
            right_frame: Right half frame
            
        Returns:
            Combined frame
        """
        # Ensure both frames have the same height
        left_height, left_width = left_frame.shape[:2]
        right_height, right_width = right_frame.shape[:2]
        
        # Use the minimum height to ensure compatibility
        min_height = min(left_height, right_height)
        
        # Resize frames to have the same height
        if left_height != min_height:
            left_frame = cv2.resize(left_frame, (left_width, min_height))
        if right_height != min_height:
            right_frame = cv2.resize(right_frame, (right_width, min_height))
        
        # Combine horizontally
        combined_frame = np.hstack((left_frame, right_frame))
        
        return combined_frame
    
    def adjust_detection_coordinates(self, detection: Dict, is_right_half: bool, original_width: int) -> Dict:
        """
        Adjust detection coordinates when combining left/right halves
        
        Args:
            detection: Detection dictionary
            is_right_half: Whether this detection is from the right half
            original_width: Original frame width
            
        Returns:
            Adjusted detection dictionary
        """
        adjusted_detection = detection.copy()
        
        if is_right_half:
            # Adjust x coordinates for right half
            bbox = detection['bbox']
            adjusted_bbox = [
                bbox[0] + original_width // 2,  # x1
                bbox[1],                        # y1
                bbox[2] + original_width // 2,  # x2
                bbox[3]                         # y2
            ]
            adjusted_detection['bbox'] = adjusted_bbox
        
        return adjusted_detection
    
    def adjust_ellipse_coordinates(self, ellipse: EllipseData, is_right_half: bool, original_width: int) -> EllipseData:
        """
        Adjust ellipse coordinates when combining left/right halves
        
        Args:
            ellipse: Ellipse data
            is_right_half: Whether this ellipse is from the right half
            original_width: Original frame width
            
        Returns:
            Adjusted ellipse data
        """
        if is_right_half:
            # Adjust center x coordinate for right half
            center_x, center_y = ellipse.center
            adjusted_center = (int(center_x + original_width // 2), int(center_y))
            
            return EllipseData(
                center=adjusted_center,
                axes=ellipse.axes,
                angle=ellipse.angle,
                confidence=ellipse.confidence
            )
        
        return ellipse
    
    def track_video_split_combine(self, video_path: str, output_path: str = None) -> Dict[int, TrackingResult]:
        """
        Track video by splitting into left/right halves, tracking separately, then combining
        
        Args:
            video_path: Path to input video
            output_path: Path to save tracked video (optional)
            
        Returns:
            Dictionary of tracking results by frame number
        """
        if not self.model:
            print("No model loaded")
            return {}
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error opening video: {video_path}")
            return {}
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Initialize video writer if output path provided
        out = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_number = 0
        tracking_results = {}
        
        print(f"Starting split tracking on {total_frames} frames...")
        print(f"Video dimensions: {width}x{height}")
        print(f"Split point: {width//2}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_number += 1
            
            # Split frame into left and right halves
            left_half, right_half = self.split_frame_vertically(frame)
            
            # Track objects in left half
            left_result = self.track_frame_with_segmentation(left_half, frame_number)
            
            # Track objects in right half
            right_result = self.track_frame_with_segmentation(right_half, frame_number)
            
            # Adjust coordinates for right half detections
            adjusted_right_detections = []
            for detection in right_result.detections:
                adjusted_detection = self.adjust_detection_coordinates(detection, True, width)
                adjusted_right_detections.append(adjusted_detection)
            
            # Combine detections and bounding box areas
            combined_detections = left_result.detections + adjusted_right_detections
            combined_areas = left_result.bounding_box_areas + right_result.bounding_box_areas
            
            # Create combined tracking result
            combined_result = TrackingResult(
                frame_number=frame_number,
                detections=combined_detections,
                bounding_box_areas=combined_areas
            )
            
            tracking_results[frame_number] = combined_result
            
            # Draw tracking results on original frame
            annotated_frame = self.draw_tracking_results_with_areas(frame, combined_result)
            
            # Write frame to output video
            if out:
                out.write(annotated_frame)
            
            # Progress update
            if frame_number % 30 == 0:
                progress = (frame_number / total_frames) * 100
                print(f"Progress: {progress:.1f}% ({frame_number}/{total_frames})")
                print(f"  Left detections: {len(left_result.detections)}, Right detections: {len(right_result.detections)}")
                print(f"  Left areas: {len(left_result.bounding_box_areas)}, Right areas: {len(right_result.bounding_box_areas)}")
                print(f"  Combined: {len(combined_detections)} detections, {len(combined_areas)} areas")
        
        cap.release()
        if out:
            out.release()
        
        self.tracking_results = tracking_results
        print(f"Split tracking completed. Processed {frame_number} frames.")
        return tracking_results
    
    def segment_and_extract_eye(self, frame, conf_threshold=None):
        """
        Use YOLO to detect eye and return center + size of largest box.
        """
        if frame is None or frame.size == 0:
            print("⚠️ Skipping invalid frame")
            return -1, -1, -1.0, None

        if conf_threshold is None:
            conf_threshold = self.confidence_threshold

        try:
            results = self.model.predict(frame, verbose=False, conf=conf_threshold)[0]
        except Exception as e:
            print(f"❌ YOLO inference error: {e}")
            return -1, -1, -1.0, None

        if len(results.boxes) == 0:
            return -1, -1, -1.0, None

        boxes = results.boxes.xyxy.cpu().numpy()
        largest_box = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        x1, y1, x2, y2 = map(int, largest_box)

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        size = round(((x2 - x1) + (y2 - y1)) / 2, 2)

        # Get segmentation mask for ellipse extraction
        masks = results.masks
        if masks is not None and len(masks) > 0:
            # Get the mask corresponding to the largest box
            mask = masks.data[0].cpu().numpy()  # Get first mask
            mask = (mask * 255).astype(np.uint8)
            ellipse = get_largest_ellipse(mask)
        else:
            ellipse = None

        return cx, cy, size, ellipse
    
    def track_video(self, video_path: str, output_path: str = None) -> Dict[int, TrackingResult]:
        """
        Track objects in entire video with segmentation and ellipse extraction
        (Now uses split tracking by default)
        
        Args:
            video_path: Path to input video
            output_path: Path to save tracked video (optional)
            
        Returns:
            Dictionary of tracking results by frame number
        """
        return self.track_video_split_combine(video_path, output_path)
    
    def track_frame_with_segmentation(self, frame: np.ndarray, frame_number: int) -> TrackingResult:
        """
        Track objects in a single frame with bounding box area calculation
        
        Args:
            frame: Input frame as numpy array
            frame_number: Current frame number
            
        Returns:
            TrackingResult object with bounding box areas
        """
        if not self.model:
            return TrackingResult(frame_number=frame_number, detections=[], bounding_box_areas=[])
        
        try:
            # Run detection on frame (using regular YOLO detection, not segmentation)
            results = self.model.predict(frame, verbose=False, conf=self.confidence_threshold)
            
            detections = []
            bounding_box_areas = []
            
            if results and len(results) > 0:
                result = results[0]  # First result
                
                if result.boxes is not None:
                    boxes = result.boxes
                    
                    # Get bounding boxes, confidence scores, and class IDs
                    if boxes.xyxy is not None:
                        for i in range(len(boxes.xyxy)):
                            box = boxes.xyxy[i].cpu().numpy()
                            conf = boxes.conf[i].cpu().numpy()
                            cls = int(boxes.cls[i].cpu().numpy())
                            
                            # Get tracking ID if available
                            tracking_id = None
                            if hasattr(boxes, 'id') and boxes.id is not None:
                                tracking_id = int(boxes.id[i].cpu().numpy())
                            
                            # Calculate bounding box area
                            x1, y1, x2, y2 = box
                            width = x2 - x1
                            height = y2 - y1
                            area = width * height
                            
                            detection = {
                                'bbox': box.tolist(),  # [x1, y1, x2, y2]
                                'confidence': float(conf),
                                'class_id': cls,
                                'class_name': self.model.names[cls] if cls in self.model.names else f"class_{cls}",
                                'tracking_id': tracking_id,
                                'area': float(area)  # Add area to detection
                            }
                            
                            detections.append(detection)
                            bounding_box_areas.append(float(area))
                            
                            # Update tracked objects
                            if tracking_id is not None:
                                self.tracked_objects[tracking_id] = {
                                    'frame_number': frame_number,
                                    'bbox': box.tolist(),
                                    'class_name': detection['class_name'],
                                    'confidence': float(conf),
                                    'area': float(area)
                                }
            
            return TrackingResult(
                frame_number=frame_number,
                detections=detections,
                bounding_box_areas=bounding_box_areas
            )
            
        except Exception as e:
            print(f"Error tracking frame {frame_number}: {e}")
            return TrackingResult(frame_number=frame_number, detections=[], bounding_box_areas=[])
    
    def draw_tracking_results_with_areas(self, frame: np.ndarray, result: TrackingResult) -> np.ndarray:
        """
        Draw tracking results and bounding box areas on frame
        
        Args:
            frame: Input frame
            result: Tracking result
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        # Draw bounding boxes and labels with areas
        for i, detection in enumerate(result.detections):
            bbox = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class_name']
            tracking_id = detection.get('tracking_id')
            area = detection.get('area', 0)
            
            # Draw bounding box
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Create label with area information
            label = f"{class_name} {confidence:.2f} Area:{area:.0f}"
            if tracking_id is not None:
                label += f" ID:{tracking_id}"
            
            # Draw label background
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            
            # Draw label text
            cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Draw area text below the bounding box
            area_text = f"Area: {area:.0f} px²"
            cv2.putText(annotated_frame, area_text, (x1, y2 + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        return annotated_frame
    
    def get_tracking_results_for_frame(self, frame_number: int) -> Optional[TrackingResult]:
        """Get tracking results for a specific frame"""
        return self.tracking_results.get(frame_number)
    
    def get_tracked_object_history(self, tracking_id: int) -> List[Dict]:
        """Get history of a tracked object across frames"""
        history = []
        for frame_num, result in self.tracking_results.items():
            for detection in result.detections:
                if detection.get('tracking_id') == tracking_id:
                    # Get area from detection
                    area = detection.get('area', 0)
                    
                    history.append({
                        'frame_number': frame_num,
                        'bbox': detection['bbox'],
                        'confidence': detection['confidence'],
                        'class_name': detection['class_name'],
                        'area': area
                    })
        return history
    
    def export_tracking_data(self, output_path: str) -> bool:
        """Export tracking results to JSON file"""
        try:
            import json
            
            # Convert tracking results to serializable format
            export_data = {}
            for frame_num, result in self.tracking_results.items():
                export_data[str(frame_num)] = {
                    'frame_number': result.frame_number,
                    'detections': result.detections,
                    'bounding_box_areas': result.bounding_box_areas
                }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"Tracking data exported to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting tracking data: {e}")
            return False
    
    def set_frame_dimensions(self, width: int, height: int):
        """Set frame dimensions for proper left/right positioning"""
        self.frame_width = width
        self.frame_height = height
    
    def export_tracking_data_to_csv(self, output_path: str) -> bool:
        """Export tracking results to CSV file with left/right position and size data"""
        try:
            import pandas as pd
            
            # Prepare data for CSV export
            csv_data = []
            
            for frame_num, result in self.tracking_results.items():
                for detection in result.detections:
                    bbox = detection['bbox']
                    x1, y1, x2, y2 = bbox
                    
                    # Calculate center position and size
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    width = x2 - x1
                    height = y2 - y1
                    size = width * height
                    
                    # Determine if object is in left or right half based on center_x
                    mid_point = self.frame_width / 2
                    
                    # Determine left/right position
                    if center_x < mid_point:
                        # Object is in left half
                        left_x_position = center_x
                        left_y_position = center_y
                        left_size = size
                        right_x_position = 0
                        right_y_position = 0
                        right_size = 0
                    else:
                        # Object is in right half
                        left_x_position = 0
                        left_y_position = 0
                        left_size = 0
                        right_x_position = center_x
                        right_y_position = center_y
                        right_size = size
                    
                    row = {
                        'Frame#': frame_num,
                        'Object_ID': detection.get('tracking_id', 0),
                        'Class_Name': detection['class_name'],
                        'Confidence': detection['confidence'],
                        'BBox_X1': x1,
                        'BBox_Y1': y1,
                        'BBox_X2': x2,
                        'BBox_Y2': y2,
                        'Center_X': center_x,
                        'Center_Y': center_y,
                        'Width': width,
                        'Height': height,
                        'Area': size,
                        'Left_X_Position': left_x_position,
                        'Left_Y_Position': left_y_position,
                        'Left_Size': left_size,
                        'Right_X_Position': right_x_position,
                        'Right_Y_Position': right_y_position,
                        'Right_Size': right_size
                    }
                    
                    csv_data.append(row)
            
            # Create DataFrame and export to CSV
            df = pd.DataFrame(csv_data)
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            print(f"Tracking data exported to CSV: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting tracking data to CSV: {e}")
            return False
    
    def get_tracking_statistics(self) -> Dict:
        """Get statistics about tracking results"""
        if not self.tracking_results:
            return {}
        
        total_frames = len(self.tracking_results)
        total_detections = sum(len(result.detections) for result in self.tracking_results.values())
        total_areas = sum(len(result.bounding_box_areas) for result in self.tracking_results.values())
        unique_tracking_ids = set()
        
        for result in self.tracking_results.values():
            for detection in result.detections:
                if detection.get('tracking_id') is not None:
                    unique_tracking_ids.add(detection['tracking_id'])
        
        return {
            'total_frames': total_frames,
            'total_detections': total_detections,
            'total_areas': total_areas,
            'unique_tracked_objects': len(unique_tracking_ids),
            'average_detections_per_frame': total_detections / total_frames if total_frames > 0 else 0,
            'average_areas_per_frame': total_areas / total_frames if total_frames > 0 else 0
        }