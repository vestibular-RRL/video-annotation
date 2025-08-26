# Video Annotation Tool

A comprehensive Python-based video annotation tool for frame-by-frame annotation with CSV export functionality. Built with PyQt6 and OpenCV, this tool provides an intuitive interface for annotating video frames with various shapes and exporting the annotations to CSV format.

## Features

### Core Functionality
- **Video Playback**: Load and play video files with frame-by-frame navigation
- **Multiple Annotation Types**: Rectangle, circle, line, point, and polygon annotations
- **Real-time Drawing**: Interactive annotation drawing on video frames
- **Frame Navigation**: Precise frame-by-frame navigation with slider and keyboard controls
- **CSV Export**: Export annotations to CSV format with comprehensive metadata

### Annotation Tools
- **Rectangle Tool**: Draw rectangular bounding boxes
- **Circle Tool**: Draw circular annotations
- **Line Tool**: Draw line annotations
- **Point Tool**: Mark specific points
- **Polygon Tool**: Draw complex polygon shapes
- **Selection Tool**: Select and edit existing annotations

### Export Options
- **Full CSV Export**: Export all annotations with frame numbers and timestamps
- **Frame Summary**: Export frame-by-frame annotation counts
- **Statistics Export**: Export project statistics and metadata
- **Custom Formats**: Flexible CSV formatting options

### User Interface
- **Modern GUI**: Clean and intuitive PyQt6-based interface
- **Toolbar**: Quick access to annotation tools and settings
- **Status Bar**: Real-time information about video and annotations
- **Frame Navigator**: Advanced frame navigation controls
- **Settings Management**: Persistent application settings

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenCV
- PyQt6
- NumPy
- Pandas

### Quick Start
1. Clone the repository:
```bash
git clone https://github.com/yourusername/video-annotation-tool.git
cd video-annotation-tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

### Development Installation
For development, install with additional development dependencies:
```bash
pip install -e .[dev]
```

## Usage

### Getting Started
1. **Open Video**: Use File → Open Video to load a video file
2. **Navigate Frames**: Use the frame navigator or video player controls
3. **Draw Annotations**: Select a tool from the toolbar and draw on the video
4. **Save Annotations**: Use File → Save Annotations to save your work
5. **Export to CSV**: Use File → Export → Export to CSV to export annotations

### Annotation Tools

#### Rectangle Tool
- Click and drag to draw rectangular bounding boxes
- Perfect for object detection annotations

#### Circle Tool
- Click and drag to draw circles
- Useful for marking points of interest

#### Line Tool
- Click and drag to draw lines
- Ideal for tracking paths or boundaries

#### Point Tool
- Click to place points
- Great for marking specific locations

#### Polygon Tool
- Click multiple points to create polygon
- Press Ctrl+Click to complete polygon
- Perfect for complex shape annotations

### Keyboard Shortcuts
- `Space`: Play/Pause video
- `Left Arrow`: Previous frame
- `Right Arrow`: Next frame
- `Home`: First frame
- `End`: Last frame
- `Delete`: Delete selected annotation
- `Ctrl+S`: Save annotations
- `Ctrl+O`: Open video
- `Ctrl+E`: Export to CSV

### Export Options

#### Full CSV Export
Exports all annotations with the following columns:
- `frame_number`: Frame number
- `timestamp`: Timestamp in seconds
- `annotation_type`: Type of annotation
- `x1, y1, x2, y2`: Coordinates
- `color`: Annotation color
- `line_width`: Line width
- `label`: Custom label
- `notes`: Additional notes

#### Frame Summary Export
Exports frame-by-frame statistics:
- `frame_number`: Frame number
- `timestamp`: Timestamp
- `total_annotations`: Total annotations in frame
- `rectangle_count`: Number of rectangles
- `circle_count`: Number of circles
- `line_count`: Number of lines
- `point_count`: Number of points
- `polygon_count`: Number of polygons

#### Statistics Export
Exports project-wide statistics:
- Total annotations
- Frames with annotations
- Annotation type counts
- Color usage statistics

## Project Structure

```
video-annotatoin/
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
├── config/                       # Configuration
│   ├── settings.py               # Application settings
│   └── constants.py              # Constants
├── src/                          # Source code
│   ├── core/                     # Core functionality
│   │   ├── video_processor.py    # Video processing
│   │   ├── annotation_manager.py # Annotation management
│   │   └── csv_exporter.py       # CSV export
│   ├── gui/                      # User interface
│   │   ├── main_window.py        # Main window
│   │   ├── video_player.py       # Video player
│   │   ├── annotation_canvas.py  # Annotation canvas
│   │   ├── frame_navigator.py    # Frame navigation
│   │   └── widgets/              # UI widgets
│   ├── models/                   # Data models
│   │   ├── annotation.py         # Annotation model
│   │   └── video_data.py         # Video data model
│   └── utils/                    # Utilities
│       ├── file_utils.py         # File operations
│       ├── video_utils.py        # Video utilities
│       └── csv_utils.py          # CSV utilities
├── data/                         # Data directory
│   ├── annotations/              # Annotation files
│   └── exports/                  # Exported files
├── assets/                       # Assets
│   ├── icons/                    # Application icons
│   └── styles/                   # Stylesheets
└── tests/                        # Unit tests
```

## Configuration

### Application Settings
The application stores settings in `config/app_settings.json`:
- Window size and position
- Video playback settings
- Annotation defaults
- Export preferences
- Recent files

### Supported Video Formats
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)
- WMV (.wmv)
- FLV (.flv)

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Type Checking
```bash
mypy src/
```

### Building Distribution
```bash
python setup.py sdist bdist_wheel
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenCV for video processing capabilities
- PyQt6 for the modern GUI framework
- NumPy for numerical operations
- Pandas for data manipulation and CSV export

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code examples

## Roadmap

- [ ] Batch processing for multiple videos
- [ ] Machine learning integration
- [ ] Cloud storage support
- [ ] Collaborative annotation features
- [ ] Advanced export formats (JSON, XML)
- [ ] Plugin system for custom annotation types
- [ ] Performance optimizations for large videos
