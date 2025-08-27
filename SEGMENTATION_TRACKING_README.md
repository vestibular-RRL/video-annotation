# YOLO Segmentation Tracking with Split Processing and Ellipse Extraction

This module integrates YOLO segmentation models with ellipse extraction for object tracking in videos. It uses a **split processing approach** where videos are divided into left and right halves, tracked separately, and then combined back into a single video with all tracked objects.

## Features

- **Split Processing**: Videos are split into left/right halves for independent tracking
- **YOLO Segmentation Integration**: Uses Ultralytics YOLO segmentation models
- **Ellipse Extraction**: Automatically extracts ellipses from segmentation masks
- **Coordinate Adjustment**: Automatically adjusts coordinates when combining halves
- **Video Tracking**: Process entire videos with split tracking and ellipse extraction
- **Real-time Display**: Toggle between original and tracked video views
- **Data Export**: Export tracking results to JSON format
- **Threading**: Non-blocking UI with background processing

## Split Tracking Process

1. **Video Split**: Each frame is split vertically into left and right halves
2. **Independent Tracking**: Each half is processed separately with YOLO segmentation
3. **Coordinate Adjustment**: Right half coordinates are adjusted to match original frame
4. **Result Combination**: Detections and ellipses from both halves are combined
5. **Final Display**: User sees the complete video with all tracked objects

## Installation

Make sure you have the required dependencies:

```bash
pip install ultralytics torch torchvision opencv-python numpy
```

## Usage

### 1. Prepare Your Model

Place your YOLO segmentation model in the `models/` directory:

```
models/
├── best.pt                    # Your trained model
├── eye_segmentation.pt        # Eye-specific model
└── yolov8n-seg-custom.pt     # Custom segmentation model
```

### 2. Using the GUI Application

1. **Load a video** using the "Open Video" menu
2. **Click "Start Split Tracking"** to begin split processing
3. **Toggle "Show Tracking Results"** to switch between original and tracked video
4. **Export tracking data** using the "Export Tracking Data" button

### 3. Programmatic Usage

#### Split Tracking

```python
from src.core.object_tracker import ObjectTracker

# Initialize tracker with your model
tracker = ObjectTracker(model_path="models/best.pt", confidence_threshold=0.5)

# Track video using split processing
results = tracker.track_video_split_combine("input.mp4", "output_tracked.mp4")

# Get statistics
stats = tracker.get_tracking_statistics()
print(f"Processed {stats['total_frames']} frames")
print(f"Found {stats['total_ellipses']} ellipses")
```

#### Frame-by-Frame Split Processing

```python
# Split a single frame
left_half, right_half = tracker.split_frame_vertically(frame)

# Track each half separately
left_result = tracker.track_frame_with_segmentation(left_half, frame_number)
right_result = tracker.track_frame_with_segmentation(right_half, frame_number)

# Adjust coordinates for right half
adjusted_right_detections = []
for detection in right_result.detections:
    adjusted_detection = tracker.adjust_detection_coordinates(detection, True, original_width)
    adjusted_right_detections.append(adjusted_detection)

# Combine results
combined_detections = left_result.detections + adjusted_right_detections
```

#### Coordinate Adjustment

```python
# Adjust detection coordinates for right half
adjusted_detection = tracker.adjust_detection_coordinates(detection, True, original_width)

# Adjust ellipse coordinates for right half
adjusted_ellipse = tracker.adjust_ellipse_coordinates(ellipse, True, original_width)
```

### 4. Ellipse Extraction

The `get_largest_ellipse()` function extracts the largest ellipse from a binary mask:

```python
from src.core.object_tracker import get_largest_ellipse

# Extract ellipse from segmentation mask
ellipse = get_largest_ellipse(mask)

if ellipse is not None:
    center, axes, angle = ellipse
    # Draw ellipse
    cv2.ellipse(image, center, axes, angle, 0, 360, (0, 255, 0), 2)
```

## Data Structures

### TrackingResult

```python
@dataclass
class TrackingResult:
    frame_number: int
    detections: List[Dict]      # Bounding box detections
    ellipses: List[EllipseData] # Extracted ellipses
    tracking_id: Optional[int]  # Tracking ID (if available)
```

### EllipseData

```python
@dataclass
class EllipseData:
    center: Tuple[int, int]     # (x, y) center coordinates
    axes: Tuple[int, int]       # (major_axis, minor_axis)
    angle: float                # rotation angle in degrees
    confidence: float           # detection confidence
```

## Split Processing Methods

### Frame Splitting

```python
def split_frame_vertically(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Split a frame into left and right halves"""
    height, width = frame.shape[:2]
    mid_point = width // 2
    
    left_half = frame[:, :mid_point]
    right_half = frame[:, mid_point:]
    
    return left_half, right_half
```

### Frame Combining

```python
def combine_frames_horizontally(self, left_frame: np.ndarray, right_frame: np.ndarray) -> np.ndarray:
    """Combine left and right frames horizontally"""
    # Ensure both frames have the same height
    min_height = min(left_frame.shape[0], right_frame.shape[0])
    
    # Resize if necessary and combine
    combined_frame = np.hstack((left_frame, right_frame))
    return combined_frame
```

### Coordinate Adjustment

```python
def adjust_detection_coordinates(self, detection: Dict, is_right_half: bool, original_width: int) -> Dict:
    """Adjust detection coordinates when combining left/right halves"""
    if is_right_half:
        bbox = detection['bbox']
        adjusted_bbox = [
            bbox[0] + original_width // 2,  # x1
            bbox[1],                        # y1
            bbox[2] + original_width // 2,  # x2
            bbox[3]                         # y2
        ]
        detection['bbox'] = adjusted_bbox
    return detection
```

## Configuration

### Model Selection

The application automatically looks for models in this order:

1. `models/best.pt`
2. `models/yolov8n-seg-custom.pt`
3. `models/eye_segmentation.pt`
4. `models/segmentation_model.pt`

If no custom model is found, it will prompt you to select one or use the default YOLO segmentation model.

### Confidence Threshold

Adjust the confidence threshold when initializing the tracker:

```python
tracker = ObjectTracker(confidence_threshold=0.7)  # Higher confidence
```

## Output Files

### Tracked Video

The tracked video includes:
- Bounding boxes around detected objects from both halves
- Ellipses drawn on segmentation masks from both halves
- Confidence scores and class labels
- Tracking IDs (if available)
- All objects properly positioned in the original frame coordinates

### JSON Export

The exported JSON contains:

```json
{
  "1": {
    "frame_number": 1,
    "detections": [
      {
        "bbox": [x1, y1, x2, y2],
        "confidence": 0.95,
        "class_name": "eye",
        "tracking_id": 1
      }
    ],
    "ellipses": [
      {
        "center": [x, y],
        "axes": [major, minor],
        "angle": 45.0,
        "confidence": 0.95
      }
    ]
  }
}
```

## Performance Tips

1. **Split Processing**: Processing smaller halves can be faster than full frames
2. **GPU Acceleration**: The tracker automatically uses CUDA if available
3. **Model Optimization**: Use smaller models (e.g., YOLOv8n-seg) for faster inference
4. **Confidence Threshold**: Increase threshold to reduce false positives
5. **Parallel Processing**: Consider processing left/right halves in parallel for better performance

## Troubleshooting

### Common Issues

1. **Model not found**: Ensure your model file exists and is in the correct format
2. **CUDA out of memory**: Reduce batch size or use CPU processing
3. **No ellipses detected**: Check if your model produces segmentation masks
4. **Slow processing**: Consider using a smaller model or reducing video resolution
5. **Coordinate misalignment**: Verify that coordinate adjustment is working correctly

### Debug Mode

Enable debug output by setting the confidence threshold lower:

```python
tracker = ObjectTracker(confidence_threshold=0.1)  # More detections for debugging
```

## Example Scripts

Run the example script to test the functionality:

```bash
python example_split_tracking.py
```

This script includes examples for:
- Split video tracking
- Frame-by-frame split processing
- Split visualization
- Coordinate adjustment

## Integration with Annotation System

The tracking results can be integrated with the annotation system:

```python
# Get tracking results for current frame
current_results = video_player.get_current_tracking_results()

if current_results:
    # Use ellipse data for annotations
    for ellipse in current_results.ellipses:
        annotation_text = f"Ellipse: {ellipse.center}, {ellipse.axes}"
        annotation_manager.add_annotation(frame_number, annotation_text)
```

## Advanced Usage

### Custom Split Processing

You can extend the split processing for specific applications:

```python
def custom_split_processing(tracker, frame):
    """Custom split processing for specific use cases"""
    # Split frame
    left_half, right_half = tracker.split_frame_vertically(frame)
    
    # Custom processing for each half
    left_result = custom_process_half(left_half)
    right_result = custom_process_half(right_half)
    
    # Combine results
    return combine_results(left_result, right_result)
```

### Multi-Object Tracking with Split Processing

For tracking multiple objects with different classes:

```python
# Filter by class after split processing
eye_detections = [d for d in combined_detections if d['class_name'] == 'eye']
face_detections = [d for d in combined_detections if d['class_name'] == 'face']

# Process each class separately
for detection in eye_detections:
    # Process eye detection
    pass
```

This integration provides a complete solution for YOLO segmentation-based object tracking with split processing and ellipse extraction, perfect for applications like eye tracking, medical imaging, or any scenario requiring precise shape analysis with improved processing efficiency.
