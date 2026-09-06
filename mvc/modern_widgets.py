from PyQt6.QtWidgets import QPushButton, QLineEdit
from PyQt6.QtGui import QFont

class ModernButton(QPushButton):
    def __init__(self, text="", style="primary", parent=None):
        super().__init__(text, parent)
        self.style_type = style
        self._setup_ui()
    def _setup_ui(self):
        self.setMinimumHeight(40)
        self.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        styles = {
            "primary": {"bg": "#3498db", "hover": "#2980b9", "text": "#ffffff"},
            "secondary": {"bg": "#95a5a6", "hover": "#7f8c8d", "text": "#ffffff"},
            "success": {"bg": "#27ae60", "hover": "#229954", "text": "#ffffff"},
            "danger": {"bg": "#e74c3c", "hover": "#c0392b", "text": "#ffffff"},
            "warning": {"bg": "#f39c12", "hover": "#e67e22", "text": "#ffffff"},
            "info": {"bg": "#17a2b8", "hover": "#138496", "text": "#ffffff"}
        }
        style = styles.get(self.style_type, styles["primary"])
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {style['bg']};
                color: {style['text']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {style['hover']};
            }}
            QPushButton:pressed {{
                background-color: {style['hover']};
                padding-top: 11px;
                padding-bottom: 9px;
            }}
        """)

class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self._setup_ui()
    def _setup_ui(self):
        self.setMinimumHeight(40)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """) 