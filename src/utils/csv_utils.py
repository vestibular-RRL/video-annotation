"""
CSV Utility Functions
"""

import csv
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


def write_csv_data(data: List[Dict[str, Any]], file_path: str, headers: Optional[List[str]] = None) -> bool:
    """Write data to CSV file"""
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Determine headers
        if headers is None and data:
            headers = list(data[0].keys())
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        
        return True
    
    except Exception as e:
        print(f"Error writing CSV data to {file_path}: {e}")
        return False


def read_csv_data(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """Read data from CSV file"""
    try:
        if not Path(file_path).exists():
            return None
        
        data = []
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(dict(row))
        
        return data
    
    except Exception as e:
        print(f"Error reading CSV data from {file_path}: {e}")
        return None


def append_csv_data(data: List[Dict[str, Any]], file_path: str, headers: Optional[List[str]] = None) -> bool:
    """Append data to existing CSV file"""
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Determine headers
        if headers is None and data:
            headers = list(data[0].keys())
        
        # Check if file exists to determine if we need to write headers
        file_exists = Path(file_path).exists()
        
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            
            # Write headers only if file doesn't exist
            if not file_exists:
                writer.writeheader()
            
            writer.writerows(data)
        
        return True
    
    except Exception as e:
        print(f"Error appending CSV data to {file_path}: {e}")
        return False


def merge_csv_files(file_paths: List[str], output_path: str) -> bool:
    """Merge multiple CSV files into one"""
    try:
        all_data = []
        headers = None
        
        for file_path in file_paths:
            data = read_csv_data(file_path)
            if data:
                if headers is None:
                    headers = list(data[0].keys())
                all_data.extend(data)
        
        if all_data:
            return write_csv_data(all_data, output_path, headers)
        else:
            return False
    
    except Exception as e:
        print(f"Error merging CSV files: {e}")
        return False


def filter_csv_data(data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filter CSV data based on criteria"""
    filtered_data = []
    
    for row in data:
        match = True
        for key, value in filters.items():
            if key in row:
                if isinstance(value, (list, tuple)):
                    if row[key] not in value:
                        match = False
                        break
                else:
                    if row[key] != value:
                        match = False
                        break
            else:
                match = False
                break
        
        if match:
            filtered_data.append(row)
    
    return filtered_data


def sort_csv_data(data: List[Dict[str, Any]], sort_key: str, reverse: bool = False) -> List[Dict[str, Any]]:
    """Sort CSV data by a specific key"""
    try:
        return sorted(data, key=lambda x: x.get(sort_key, ""), reverse=reverse)
    except Exception as e:
        print(f"Error sorting CSV data: {e}")
        return data


def get_csv_statistics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get statistics from CSV data"""
    if not data:
        return {}
    
    stats = {
        'total_rows': len(data),
        'columns': list(data[0].keys()) if data else [],
        'column_counts': {},
        'unique_values': {}
    }
    
    # Count unique values for each column
    for column in stats['columns']:
        values = [row.get(column) for row in data if column in row]
        unique_values = set(values)
        stats['column_counts'][column] = len(values)
        stats['unique_values'][column] = len(unique_values)
    
    return stats


def validate_csv_data(data: List[Dict[str, Any]], required_columns: Optional[List[str]] = None) -> bool:
    """Validate CSV data structure"""
    if not data:
        return False
    
    # Check if all rows have the same columns
    first_row_keys = set(data[0].keys())
    for row in data[1:]:
        if set(row.keys()) != first_row_keys:
            return False
    
    # Check required columns
    if required_columns:
        for column in required_columns:
            if column not in first_row_keys:
                return False
    
    return True


def convert_dataframe_to_csv_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert pandas DataFrame to CSV data format"""
    try:
        return df.to_dict('records')
    except Exception as e:
        print(f"Error converting DataFrame to CSV data: {e}")
        return []


def convert_csv_data_to_dataframe(data: List[Dict[str, Any]]) -> Optional[pd.DataFrame]:
    """Convert CSV data to pandas DataFrame"""
    try:
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error converting CSV data to DataFrame: {e}")
        return None


def create_csv_template(headers: List[str], file_path: str) -> bool:
    """Create a CSV template with headers only"""
    try:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
        
        return True
    
    except Exception as e:
        print(f"Error creating CSV template: {e}")
        return False


def update_csv_row(file_path: str, row_index: int, updates: Dict[str, Any]) -> bool:
    """Update a specific row in CSV file"""
    try:
        data = read_csv_data(file_path)
        if data is None or row_index >= len(data):
            return False
        
        # Update the row
        data[row_index].update(updates)
        
        # Write back to file
        return write_csv_data(data, file_path)
    
    except Exception as e:
        print(f"Error updating CSV row: {e}")
        return False


def delete_csv_row(file_path: str, row_index: int) -> bool:
    """Delete a specific row from CSV file"""
    try:
        data = read_csv_data(file_path)
        if data is None or row_index >= len(data):
            return False
        
        # Remove the row
        del data[row_index]
        
        # Write back to file
        return write_csv_data(data, file_path)
    
    except Exception as e:
        print(f"Error deleting CSV row: {e}")
        return False


def add_csv_column(file_path: str, column_name: str, default_value: Any = "") -> bool:
    """Add a new column to CSV file"""
    try:
        data = read_csv_data(file_path)
        if data is None:
            return False
        
        # Add column to all rows
        for row in data:
            row[column_name] = default_value
        
        # Write back to file
        return write_csv_data(data, file_path)
    
    except Exception as e:
        print(f"Error adding CSV column: {e}")
        return False


def remove_csv_column(file_path: str, column_name: str) -> bool:
    """Remove a column from CSV file"""
    try:
        data = read_csv_data(file_path)
        if data is None:
            return False
        
        # Remove column from all rows
        for row in data:
            if column_name in row:
                del row[column_name]
        
        # Write back to file
        return write_csv_data(data, file_path)
    
    except Exception as e:
        print(f"Error removing CSV column: {e}")
        return False


def backup_csv_file(file_path: str) -> Optional[str]:
    """Create backup of CSV file"""
    try:
        from src.utils.file_utils import create_backup_file
        return create_backup_file(file_path)
    except Exception as e:
        print(f"Error creating CSV backup: {e}")
        return None
