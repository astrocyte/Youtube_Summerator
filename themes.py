"""
Theme definitions for the YouTube Extractor application.
This module contains stylesheets for different application themes.
"""

# List of available themes
AVAILABLE_THEMES = ["matrix", "dark"]

def get_matrix_stylesheet():
    """Return the Matrix-inspired green-on-black stylesheet."""
    return """
        QWidget {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            color: #00FF41;
            background-color: #0D0208;
        }
        QMainWindow {
            background-color: #0D0208;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #00FF41;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 16px;
            background-color: #0D0208;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #00FF41;
        }
        QPushButton {
            background-color: #003B00;
            color: #00FF41;
            padding: 8px 16px;
            border-radius: 4px;
            border: 1px solid #00FF41;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #005000;
            border: 1px solid #00FF00;
        }
        QPushButton:pressed {
            background-color: #008000;
        }
        QPushButton:disabled {
            background-color: #1A1A1A;
            color: #3A3A3A;
            border: 1px solid #3A3A3A;
        }
        QLineEdit, QTextEdit {
            border: 1px solid #00FF41;
            border-radius: 4px;
            padding: 8px;
            background-color: #0D0208;
            color: #00FF41;
            selection-background-color: #003B00;
            selection-color: #00FF41;
        }
        QComboBox {
            border: 1px solid #00FF41;
            border-radius: 4px;
            padding: 8px;
            padding-right: 20px;
            background-color: #0D0208;
            color: #00FF41;
            selection-background-color: #003B00;
            selection-color: #00FF41;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 20px;
            border: none;
            background: #003B00;
        }
        QComboBox::down-arrow {
            background: #00FF41;
            width: 10px;
            height: 10px;
            border-radius: 5px;
        }
        QComboBox QAbstractItemView {
            border: 1px solid #00FF41;
            background-color: #0D0208;
            color: #00FF41;
            selection-background-color: #003B00;
            selection-color: #00FF41;
            padding: 4px;
            min-height: 24px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #00FF00;
        }
        QProgressBar {
            border: 1px solid #00FF41;
            border-radius: 4px;
            text-align: center;
            background-color: #0D0208;
            color: #000000;
        }
        QProgressBar::chunk {
            background-color: #00FF41;
            border-radius: 3px;
        }
        QTableWidget {
            border: 1px solid #00FF41;
            border-radius: 4px;
            background-color: #0D0208;
            gridline-color: #003B00;
            color: #00FF41;
            selection-background-color: transparent;
            selection-color: #00FF41;
        }
        QTableWidget::item {
            padding: 4px;
            border: none;
        }
        QTableWidget::item:selected {
            background-color: transparent;
            color: #00FF41;
            border: 1px solid #00FF00;
        }
        QTableWidget::item:focus {
            background-color: transparent;
            color: #00FF41;
            border: 1px solid #00FF00;
        }
        QHeaderView::section {
            background-color: #003B00;
            padding: 8px;
            border: none;
            font-weight: bold;
            color: #00FF41;
        }
        QScrollBar:vertical {
            border: none;
            background: #0D0208;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #00FF41;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QCheckBox {
            spacing: 8px;
            color: #00FF41;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 1px solid #00FF41;
        }
        QCheckBox::indicator:checked {
            background-color: #00FF41;
        }
        QLabel {
            color: #00FF41;
        }
        QStatusBar {
            color: #00FF41;
            background-color: #0D0208;
        }
        QMenuBar {
            background-color: #0D0208;
            color: #00FF41;
            border-bottom: 1px solid #00FF41;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 10px;
        }
        QMenuBar::item:selected {
            background-color: #003B00;
            color: #00FF41;
        }
        QMenu {
            background-color: #0D0208;
            color: #00FF41;
            border: 1px solid #00FF41;
        }
        QMenu::item {
            padding: 6px 20px;
        }
        QMenu::item:selected {
            background-color: #003B00;
        }
        QMenu::separator {
            height: 1px;
            background-color: #00FF41;
            margin: 4px 0px;
        }
        QTableWidget QLineEdit {
            padding: 4px;
            border: none;
            background-color: #0D0208;
            color: #00FF41;
            selection-background-color: #003B00;
            selection-color: #00FF41;
        }
    """

def get_dark_stylesheet():
    """Return a dark blue theme stylesheet."""
    return """
        QWidget {
            font-family: 'Arial', sans-serif;
            font-size: 14px;
            color: #FFFFFF;
            background-color: #1E1E2E;
        }
        QMainWindow {
            background-color: #1E1E2E;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #6272A4;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 16px;
            background-color: #282A36;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #BD93F9;
        }
        QPushButton {
            background-color: #44475A;
            color: #FFFFFF;
            padding: 8px 16px;
            border-radius: 4px;
            border: 1px solid #6272A4;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #6272A4;
            border: 1px solid #BD93F9;
        }
        QPushButton:pressed {
            background-color: #BD93F9;
            color: #282A36;
        }
        QPushButton:disabled {
            background-color: #282A36;
            color: #6272A4;
            border: 1px solid #44475A;
        }
        QLineEdit, QTextEdit {
            border: 1px solid #6272A4;
            border-radius: 4px;
            padding: 8px;
            background-color: #282A36;
            color: #FFFFFF;
            selection-background-color: #44475A;
            selection-color: #FFFFFF;
        }
        QComboBox {
            border: 1px solid #6272A4;
            border-radius: 4px;
            padding: 8px;
            padding-right: 20px;
            background-color: #282A36;
            color: #FFFFFF;
            selection-background-color: #44475A;
            selection-color: #FFFFFF;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 20px;
            border: none;
            background: #44475A;
        }
        QComboBox::down-arrow {
            background: #BD93F9;
            width: 10px;
            height: 10px;
            border-radius: 5px;
        }
        QComboBox QAbstractItemView {
            border: 1px solid #6272A4;
            background-color: #282A36;
            color: #FFFFFF;
            selection-background-color: #44475A;
            selection-color: #FFFFFF;
            padding: 4px;
            min-height: 24px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #BD93F9;
        }
        QProgressBar {
            border: 1px solid #6272A4;
            border-radius: 4px;
            text-align: center;
            background-color: #282A36;
            color: #FFFFFF;
        }
        QProgressBar::chunk {
            background-color: #BD93F9;
            border-radius: 3px;
        }
        QTableWidget {
            border: 1px solid #6272A4;
            border-radius: 4px;
            background-color: #282A36;
            gridline-color: #44475A;
            color: #FFFFFF;
            selection-background-color: transparent;
            selection-color: #FFFFFF;
        }
        QTableWidget::item {
            padding: 4px;
            border: none;
        }
        QTableWidget::item:selected {
            background-color: transparent;
            color: #FFFFFF;
            border: 1px solid #BD93F9;
        }
        QTableWidget::item:focus {
            background-color: transparent;
            color: #FFFFFF;
            border: 1px solid #BD93F9;
        }
        QHeaderView::section {
            background-color: #44475A;
            padding: 8px;
            border: none;
            font-weight: bold;
            color: #FFFFFF;
        }
        QScrollBar:vertical {
            border: none;
            background: #282A36;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #6272A4;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QCheckBox {
            spacing: 8px;
            color: #FFFFFF;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 1px solid #6272A4;
        }
        QCheckBox::indicator:checked {
            background-color: #BD93F9;
        }
        QLabel {
            color: #FFFFFF;
        }
        QStatusBar {
            color: #FFFFFF;
            background-color: #282A36;
        }
        QMenuBar {
            background-color: #282A36;
            color: #FFFFFF;
            border-bottom: 1px solid #6272A4;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 10px;
        }
        QMenuBar::item:selected {
            background-color: #44475A;
            color: #FFFFFF;
        }
        QMenu {
            background-color: #282A36;
            color: #FFFFFF;
            border: 1px solid #6272A4;
        }
        QMenu::item {
            padding: 6px 20px;
        }
        QMenu::item:selected {
            background-color: #44475A;
        }
        QMenu::separator {
            height: 1px;
            background-color: #6272A4;
            margin: 4px 0px;
        }
        QTableWidget QLineEdit {
            padding: 4px;
            border: none;
            background-color: #282A36;
            color: #FFFFFF;
            selection-background-color: #44475A;
            selection-color: #FFFFFF;
        }
    """ 