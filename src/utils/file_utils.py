"""
File Utility Functions
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from config.constants import SUPPORTED_VIDEO_FORMATS


def ensure_directory_exists(directory_path: str) -> bool:
    """Ensure directory exists, create if it doesn't"""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False


def get_file_extension(file_path: str) -> str:
    """Get file extension from path"""
    return Path(file_path).suffix.lower()


def is_video_file(file_path: str) -> bool:
    """Check if file is a supported video format"""
    extension = get_file_extension(file_path)
    return extension in SUPPORTED_VIDEO_FORMATS


def get_video_files_in_directory(directory_path: str) -> List[str]:
    """Get all video files in a directory"""
    video_files = []
    
    try:
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            return video_files
        
        for file_path in directory.iterdir():
            if file_path.is_file() and is_video_file(str(file_path)):
                video_files.append(str(file_path))
        
        return sorted(video_files)
    
    except Exception as e:
        print(f"Error scanning directory {directory_path}: {e}")
        return video_files


def get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes"""
    try:
        return Path(file_path).stat().st_size
    except Exception as e:
        print(f"Error getting file size for {file_path}: {e}")
        return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def save_json_data(data: Dict[str, Any], file_path: str) -> bool:
    """Save data to JSON file"""
    try:
        ensure_directory_exists(Path(file_path).parent)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    
    except Exception as e:
        print(f"Error saving JSON data to {file_path}: {e}")
        return False


def load_json_data(file_path: str) -> Optional[Dict[str, Any]]:
    """Load data from JSON file"""
    try:
        if not Path(file_path).exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    except Exception as e:
        print(f"Error loading JSON data from {file_path}: {e}")
        return None


def get_unique_filename(base_path: str, extension: str = "") -> str:
    """Get unique filename by appending number if file exists"""
    path = Path(base_path)
    
    if not path.exists():
        return str(path)
    
    # Split path into directory, name, and extension
    directory = path.parent
    name = path.stem
    ext = path.suffix if not extension else extension
    
    counter = 1
    while True:
        new_name = f"{name}_{counter}{ext}"
        new_path = directory / new_name
        
        if not new_path.exists():
            return str(new_path)
        
        counter += 1


def create_backup_file(file_path: str) -> Optional[str]:
    """Create backup of file with timestamp"""
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_backup_{timestamp}{path.suffix}"
        backup_path = path.parent / backup_name
        
        # Copy file
        import shutil
        shutil.copy2(file_path, backup_path)
        
        return str(backup_path)
    
    except Exception as e:
        print(f"Error creating backup of {file_path}: {e}")
        return None


def get_relative_path(file_path: str, base_directory: str) -> str:
    """Get relative path from base directory"""
    try:
        file_path_obj = Path(file_path).resolve()
        base_dir_obj = Path(base_directory).resolve()
        
        return str(file_path_obj.relative_to(base_dir_obj))
    
    except ValueError:
        # File is not in base directory
        return file_path


def validate_file_path(file_path: str) -> bool:
    """Validate if file path is valid and accessible"""
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except Exception:
        return False


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get comprehensive file information"""
    try:
        path = Path(file_path)
        stat = path.stat()
        
        return {
            'name': path.name,
            'stem': path.stem,
            'suffix': path.suffix,
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'accessed': stat.st_atime,
            'is_file': path.is_file(),
            'is_dir': path.is_dir(),
            'exists': path.exists(),
            'absolute': str(path.absolute()),
            'parent': str(path.parent)
        }
    
    except Exception as e:
        print(f"Error getting file info for {file_path}: {e}")
        return {}
