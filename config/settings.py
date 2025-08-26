"""
Application Settings
"""

import json
import os
import base64
from typing import Any, Dict, List, Optional
from pathlib import Path
from PyQt6.QtCore import QByteArray


class QtJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Qt objects"""
    
    def default(self, obj):
        # Handle QByteArray objects by converting to base64
        if hasattr(obj, 'toHex'):
            return {'__qbytearray__': base64.b64encode(obj.data()).decode('utf-8')}
        # Handle other Qt objects that might have a string representation
        elif hasattr(obj, '__str__'):
            return str(obj)
        return super().default(obj)


class QtJSONDecoder(json.JSONDecoder):
    """Custom JSON decoder to handle Qt objects"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)
    
    def object_hook(self, obj):
        # Convert base64 strings back to QByteArray
        if '__qbytearray__' in obj:
            data = base64.b64decode(obj['__qbytearray__'])
            return QByteArray(data)
        return obj


class Settings:
    """Application settings manager"""
    
    def __init__(self, config_file: str = "config/app_settings.json"):
        self.config_file = Path(config_file)
        self.settings: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load settings from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f, cls=QtJSONDecoder)
            else:
                # Create default settings
                self.settings = self.get_default_settings()
                self.save()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = self.get_default_settings()
    
    def save(self):
        """Save settings to file"""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False, cls=QtJSONEncoder)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_default_settings(self) -> Dict[str, Any]:
        """Get default settings"""
        return {
            # Window settings
            "window_geometry": None,
            "window_state": None,
            
            # Recent files
            "recent_files": [],
            "max_recent_files": 10,
            
            # Video settings
            "last_video_directory": "",
            "auto_load_last_video": False,
            
            # Export settings
            "last_export_directory": "",
            "export_format": "csv",
            
            # Annotation settings
            "default_annotation": "0",
            
            # Application settings
            "auto_save_interval": 30,  # seconds
            "show_frame_numbers": True,
            "show_timestamps": True
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value
    
    def add_recent_file(self, file_path: str):
        """Add a file to recent files list"""
        if not file_path:
            return
        
        # Remove if already exists
        if file_path in self.settings.get("recent_files", []):
            self.settings["recent_files"].remove(file_path)
        
        # Add to beginning
        recent_files = self.settings.get("recent_files", [])
        recent_files.insert(0, file_path)
        
        # Limit number of recent files
        max_files = self.settings.get("max_recent_files", 10)
        self.settings["recent_files"] = recent_files[:max_files]
    
    def get_recent_files(self) -> List[str]:
        """Get list of recent files"""
        return self.settings.get("recent_files", [])
    
    def clear_recent_files(self):
        """Clear recent files list"""
        self.settings["recent_files"] = []
    
    def get_last_video_directory(self) -> str:
        """Get last used video directory"""
        return self.settings.get("last_video_directory", "")
    
    def set_last_video_directory(self, directory: str):
        """Set last used video directory"""
        self.settings["last_video_directory"] = directory
    
    def get_last_export_directory(self) -> str:
        """Get last used export directory"""
        return self.settings.get("last_export_directory", "")
    
    def set_last_export_directory(self, directory: str):
        """Set last used export directory"""
        self.settings["last_export_directory"] = directory
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.get_default_settings()
        self.save()


def load_settings(config_file: str = "config/app_settings.json") -> Settings:
    """Load application settings"""
    return Settings(config_file)
