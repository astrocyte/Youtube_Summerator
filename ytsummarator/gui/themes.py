"""Theme definitions for the GUI."""
AVAILABLE_THEMES = ["matrix", "dark"]

def get_matrix_stylesheet():
    """Get the Matrix-inspired theme stylesheet."""
    return """
        QMainWindow {
            background-color: #000000;
        }
        QWidget {
            background-color: #000000;
            color: #00FF41;
            font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
        }
        QPushButton {
            background-color: #003B00;
            border: 1px solid #00FF41;
            color: #00FF41;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #004D00;
        }
        QPushButton:disabled {
            background-color: #001A00;
            color: #006600;
        }
        QLineEdit {
            background-color: #001A00;
            border: 1px solid #00FF41;
            color: #00FF41;
            padding: 5px;
            border-radius: 3px;
        }
        QComboBox {
            background-color: #001A00;
            border: 1px solid #00FF41;
            color: #00FF41;
            padding: 5px;
            border-radius: 3px;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: url(down_arrow.png);
            width: 12px;
            height: 12px;
        }
        QTableWidget {
            background-color: #001A00;
            border: 1px solid #00FF41;
            gridline-color: #003300;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QTableWidget::item:selected {
            background-color: #004D00;
            color: #00FF41;
        }
        QHeaderView::section {
            background-color: #003300;
            color: #00FF41;
            padding: 5px;
            border: 1px solid #00FF41;
        }
        QProgressBar {
            border: 1px solid #00FF41;
            border-radius: 3px;
            text-align: center;
            background-color: #001A00;
        }
        QProgressBar::chunk {
            background-color: #00FF41;
        }
        QTextEdit {
            background-color: #001A00;
            border: 1px solid #00FF41;
            color: #00FF41;
            padding: 5px;
            border-radius: 3px;
        }
        QGroupBox {
            border: 1px solid #00FF41;
            border-radius: 3px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
        }
        QMenuBar {
            background-color: #001A00;
            border-bottom: 1px solid #00FF41;
        }
        QMenuBar::item {
            padding: 5px 10px;
        }
        QMenuBar::item:selected {
            background-color: #004D00;
        }
        QMenu {
            background-color: #001A00;
            border: 1px solid #00FF41;
        }
        QMenu::item {
            padding: 5px 20px;
        }
        QMenu::item:selected {
            background-color: #004D00;
        }
    """

def get_dark_stylesheet():
    """Get the dark theme stylesheet."""
    return """
        QMainWindow {
            background-color: #1E1E1E;
        }
        QWidget {
            background-color: #1E1E1E;
            color: #FFFFFF;
            font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
        }
        QPushButton {
            background-color: #2D2D2D;
            border: 1px solid #3D3D3D;
            color: #FFFFFF;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #3D3D3D;
        }
        QPushButton:disabled {
            background-color: #1D1D1D;
            color: #666666;
        }
        QLineEdit {
            background-color: #2D2D2D;
            border: 1px solid #3D3D3D;
            color: #FFFFFF;
            padding: 5px;
            border-radius: 3px;
        }
        QComboBox {
            background-color: #2D2D2D;
            border: 1px solid #3D3D3D;
            color: #FFFFFF;
            padding: 5px;
            border-radius: 3px;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: url(down_arrow.png);
            width: 12px;
            height: 12px;
        }
        QTableWidget {
            background-color: #2D2D2D;
            border: 1px solid #3D3D3D;
            gridline-color: #3D3D3D;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QTableWidget::item:selected {
            background-color: #3D3D3D;
            color: #FFFFFF;
        }
        QHeaderView::section {
            background-color: #2D2D2D;
            color: #FFFFFF;
            padding: 5px;
            border: 1px solid #3D3D3D;
        }
        QProgressBar {
            border: 1px solid #3D3D3D;
            border-radius: 3px;
            text-align: center;
            background-color: #2D2D2D;
        }
        QProgressBar::chunk {
            background-color: #4D4D4D;
        }
        QTextEdit {
            background-color: #2D2D2D;
            border: 1px solid #3D3D3D;
            color: #FFFFFF;
            padding: 5px;
            border-radius: 3px;
        }
        QGroupBox {
            border: 1px solid #3D3D3D;
            border-radius: 3px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
        }
        QMenuBar {
            background-color: #2D2D2D;
            border-bottom: 1px solid #3D3D3D;
        }
        QMenuBar::item {
            padding: 5px 10px;
        }
        QMenuBar::item:selected {
            background-color: #3D3D3D;
        }
        QMenu {
            background-color: #2D2D2D;
            border: 1px solid #3D3D3D;
        }
        QMenu::item {
            padding: 5px 20px;
        }
        QMenu::item:selected {
            background-color: #3D3D3D;
        }
    """ 