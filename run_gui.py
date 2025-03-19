"""Entry point for running the YouTube Summarator GUI."""
import sys
from PyQt6.QtWidgets import QApplication
from ytsummarator.gui.main_window import YouTubeDownloaderGUI

def main():
    """Main entry point for the GUI."""
    app = QApplication(sys.argv)
    window = YouTubeDownloaderGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 