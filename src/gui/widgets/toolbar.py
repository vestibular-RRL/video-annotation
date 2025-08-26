"""
Toolbar Widget
"""

from PyQt6.QtWidgets import (QToolBar, QComboBox, QSpinBox, 
                             QLabel, QColorDialog, QWidget, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QAction
from config.constants import DEFAULT_ANNOTATION_COLORS, DEFAULT_LINE_WIDTHS


class ToolBar(QToolBar):
    """Main toolbar with annotation tools"""
    
    # Signals
    drawing_mode_changed = pyqtSignal(str)  # Emitted when drawing mode changes
    color_changed = pyqtSignal(str)  # Emitted when color changes
    line_width_changed = pyqtSignal(int)  # Emitted when line width changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Annotation Tools")
        self.setMovable(True)
        
        # Drawing mode selector
        self.addWidget(QLabel("Tool:"))
        self.drawing_mode_combo = QComboBox()
        self.drawing_mode_combo.addItems([
            "Rectangle", "Circle", "Line", "Point", "Polygon"
        ])
        self.drawing_mode_combo.setCurrentText("Rectangle")
        self.addWidget(self.drawing_mode_combo)
        
        self.addSeparator()
        
        # Color selector
        self.addWidget(QLabel("Color:"))
        self.color_button = QAction("Color", self)
        self.color_button.setIcon(self.create_color_icon(DEFAULT_ANNOTATION_COLORS[0]))
        self.addAction(self.color_button)
        
        # Color dropdown
        self.color_combo = QComboBox()
        for color in DEFAULT_ANNOTATION_COLORS:
            self.color_combo.addItem(color)
        self.color_combo.setCurrentText(DEFAULT_ANNOTATION_COLORS[0])
        self.addWidget(self.color_combo)
        
        self.addSeparator()
        
        # Line width selector
        self.addWidget(QLabel("Width:"))
        self.line_width_spin = QSpinBox()
        self.line_width_spin.setMinimum(1)
        self.line_width_spin.setMaximum(10)
        self.line_width_spin.setValue(2)
        self.addWidget(self.line_width_spin)
        
        self.addSeparator()
        
        # Annotation actions
        self.select_action = QAction("Select", self)
        self.select_action.setCheckable(True)
        self.select_action.setChecked(True)
        self.addAction(self.select_action)
        
        self.delete_action = QAction("Delete", self)
        self.addAction(self.delete_action)
        
        self.addSeparator()
        
        # View actions
        self.show_annotations_action = QAction("Show Annotations", self)
        self.show_annotations_action.setCheckable(True)
        self.show_annotations_action.setChecked(True)
        self.addAction(self.show_annotations_action)
    
    def setup_connections(self):
        """Set up signal connections"""
        self.drawing_mode_combo.currentTextChanged.connect(self.on_drawing_mode_changed)
        self.color_button.triggered.connect(self.show_color_dialog)
        self.color_combo.currentTextChanged.connect(self.on_color_changed)
        self.line_width_spin.valueChanged.connect(self.on_line_width_changed)
        
        self.select_action.triggered.connect(self.on_select_toggled)
        self.delete_action.triggered.connect(self.on_delete_clicked)
        self.show_annotations_action.triggered.connect(self.on_show_annotations_toggled)
    
    def create_color_icon(self, color_name: str) -> QIcon:
        """Create a color icon for the toolbar"""
        # This is a simple implementation - you might want to create actual icons
        return QIcon()
    
    def on_drawing_mode_changed(self, mode: str):
        """Handle drawing mode change"""
        mode_lower = mode.lower()
        self.drawing_mode_changed.emit(mode_lower)
        
        # Update select action state
        if mode_lower == "select":
            self.select_action.setChecked(True)
        else:
            self.select_action.setChecked(False)
    
    def on_color_changed(self, color: str):
        """Handle color change"""
        self.color_changed.emit(color)
        self.color_button.setIcon(self.create_color_icon(color))
    
    def on_line_width_changed(self, width: int):
        """Handle line width change"""
        self.line_width_changed.emit(width)
    
    def show_color_dialog(self):
        """Show color picker dialog"""
        color = QColorDialog.getColor()
        if color.isValid():
            color_name = color.name()
            self.color_combo.setCurrentText(color_name)
            self.color_changed.emit(color_name)
    
    def on_select_toggled(self, checked: bool):
        """Handle select tool toggle"""
        if checked:
            self.drawing_mode_combo.setCurrentText("Select")
        else:
            self.drawing_mode_combo.setCurrentText("Rectangle")
    
    def on_delete_clicked(self):
        """Handle delete action"""
        # This will be connected to the main window's delete function
        if self.parent:
            self.parent.delete_selected_annotation()
    
    def on_show_annotations_toggled(self, checked: bool):
        """Handle show annotations toggle"""
        # This will be connected to the main window's visibility toggle
        pass
    
    def get_current_drawing_mode(self) -> str:
        """Get current drawing mode"""
        return self.drawing_mode_combo.currentText().lower()
    
    def get_current_color(self) -> str:
        """Get current color"""
        return self.color_combo.currentText()
    
    def get_current_line_width(self) -> int:
        """Get current line width"""
        return self.line_width_spin.value()
    
    def set_drawing_mode(self, mode: str):
        """Set drawing mode"""
        mode_capitalized = mode.capitalize()
        if mode_capitalized in ["Rectangle", "Circle", "Line", "Point", "Polygon", "Select"]:
            self.drawing_mode_combo.setCurrentText(mode_capitalized)
    
    def set_color(self, color: str):
        """Set color"""
        if color in DEFAULT_ANNOTATION_COLORS:
            self.color_combo.setCurrentText(color)
    
    def set_line_width(self, width: int):
        """Set line width"""
        if 1 <= width <= 10:
            self.line_width_spin.setValue(width)
