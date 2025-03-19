"""GUI entry point for the YouTube Summarator."""
import sys
from PyQt6.QtWidgets import QApplication
from .main_window import YouTubeDownloaderGUI

def main():
    """Main entry point for the GUI."""
    app = QApplication(sys.argv)
    window = YouTubeDownloaderGUI()
    window.show()
    sys.exit(app.exec()) 