#!/usr/bin/env python3
import sys
import os
import json
import threading
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QComboBox, QProgressBar, QTextEdit, QFileDialog,
                            QCheckBox, QGroupBox, QTableWidget, QTableWidgetItem,
                            QHeaderView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QMimeData, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
import youtube_downloader as yd

# Config file for storing user preferences
CONFIG_FILE = os.path.expanduser("~/.youtube_extractor_config.json")

def get_matrix_stylesheet():
    """Return the Matrix-inspired stylesheet."""
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
        QLineEdit, QComboBox, QTextEdit {
            border: 1px solid #00FF41;
            border-radius: 4px;
            padding: 8px;
            background-color: #0D0208;
            color: #00FF41;
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
        QTableWidget::item:selected {
            background-color: transparent;
            color: #00FF41;
            border: 3px solid #00FF00;
        }
        QTableWidget::item:focus {
            background-color: transparent;
            color: #00FF41;
            border: 3px solid #00FF00;
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
    """

def load_config():
    """Load configuration from file."""
    default_config = {
        "last_output_folder": "",
        "last_format": "mp4",
        "last_quality": "best",
        "window_width": 900,
        "window_height": 700,
        "theme": "matrix"
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure all default keys exist
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
    return default_config

def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving config: {e}")

class ProgressHandler(logging.Handler):
    """Custom logging handler that emits progress signals."""
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
    
    def emit(self, record):
        self.signal.emit(self.format(record))

class DownloadWorker(QThread):
    """Worker thread for downloading videos."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, url, format_type, quality, output_folder):
        super().__init__()
        self.url = url
        self.format_type = format_type
        self.quality = quality
        self.output_folder = output_folder
        
    def run(self):
        try:
            # Create a custom logger for this thread
            thread_logger = logging.getLogger(f'download_thread_{id(self)}')
            thread_logger.setLevel(logging.INFO)
            
            # Add custom handler that emits progress signals
            handler = ProgressHandler(self.progress)
            handler.setFormatter(logging.Formatter('%(message)s'))
            thread_logger.addHandler(handler)
            
            # Temporarily replace the global logger
            original_logger = yd.logger
            yd.logger = thread_logger
            
            # Download the video with the specified output folder
            yd.download_video(self.url, self.format_type, self.quality, self.output_folder)
            
            # Restore the original logger
            yd.logger = original_logger
            
            self.finished.emit(True, "Download completed successfully!")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

class YouTubeDownloaderGUI(QMainWindow):
    # Define a custom signal for updating the title cell
    update_title_signal = pyqtSignal(int, str)
    
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = load_config()
        
        # Set window properties from config
        self.setWindowTitle("YouTube Extractor")
        self.resize(self.config.get("window_width", 900), self.config.get("window_height", 700))
        self.setMinimumSize(900, 700)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Connect the update title signal to the slot
        self.update_title_signal.connect(self.update_title_cell)
        
        # Initialize UI components
        self.setup_ui()
        
        # Apply theme
        self.apply_theme(self.config.get("theme", "matrix"))
        
        # Initialize download worker
        self.download_thread = None
        
        # Flag to prevent recursive cell change events
        self.is_updating_cell = False
    
    def setup_ui(self):
        """Set up the user interface components."""
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add header section
        self.setup_header(main_layout)
        
        # Add URL table section
        self.setup_url_table(main_layout)
        
        # Add options section
        self.setup_options(main_layout)
        
        # Add action buttons
        self.setup_action_buttons(main_layout)
        
        # Add progress section
        self.setup_progress_section(main_layout)
        
        # Status bar at bottom
        self.statusBar().showMessage("Ready")
    
    def setup_header(self, main_layout):
        """Set up the header section with title and drag-drop hint."""
        header_layout = QHBoxLayout()
        title_label = QLabel("YOUTUBE EXTRACTOR")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #00FF41;")
        header_layout.addWidget(title_label)
        
        # Add drag-drop hint
        drag_hint = QLabel("Drag & Drop URL files here")
        drag_hint.setStyleSheet("font-size: 14px; color: #00FF41; font-style: italic;")
        header_layout.addWidget(drag_hint)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
    
    def setup_url_table(self, main_layout):
        """Set up the URL table section."""
        table_label = QLabel("Enter YouTube URLs:")
        table_label.setStyleSheet("color: #00FF41;")
        main_layout.addWidget(table_label)
        
        self.url_table = QTableWidget()
        self.url_table.setColumnCount(2)
        self.url_table.setHorizontalHeaderLabels(["YouTube URLs", "Video Title"])
        self.url_table.setRowCount(10)
        self.url_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.url_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.url_table.setMinimumHeight(300)
        self.url_table.cellChanged.connect(self.on_cell_changed)
        main_layout.addWidget(self.url_table)
    
    def setup_options(self, main_layout):
        """Set up the options section with format, quality, and output folder selection."""
        options_layout = QHBoxLayout()
        
        # Format selection
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        format_label.setStyleSheet("color: #00FF41;")
        format_layout.addWidget(format_label)
        self.format_combo = QComboBox()
        self.format_combo.setMinimumHeight(30)
        self.format_combo.addItems(["mp4", "webm", "mkv", "mp3", "m4a"])
        
        # Set the last used format if available
        last_format = self.config.get("last_format", "mp4")
        format_index = self.format_combo.findText(last_format)
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)
            
        # Connect format change to save config
        self.format_combo.currentTextChanged.connect(self.save_format_preference)
        
        format_layout.addWidget(self.format_combo)
        options_layout.addLayout(format_layout)
        
        # Quality selection
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Quality:")
        quality_label.setStyleSheet("color: #00FF41;")
        quality_layout.addWidget(quality_label)
        self.quality_combo = QComboBox()
        self.quality_combo.setMinimumHeight(30)
        self.quality_combo.addItems(["best", "1080p", "720p", "480p", "360p", "240p", "144p"])
        
        # Set the last used quality if available
        last_quality = self.config.get("last_quality", "best")
        quality_index = self.quality_combo.findText(last_quality)
        if quality_index >= 0:
            self.quality_combo.setCurrentIndex(quality_index)
            
        # Connect quality change to save config
        self.quality_combo.currentTextChanged.connect(self.save_quality_preference)
        
        quality_layout.addWidget(self.quality_combo)
        options_layout.addLayout(quality_layout)
        
        # Output folder selection
        output_layout = QHBoxLayout()
        output_label = QLabel("Output:")
        output_label.setStyleSheet("color: #00FF41;")
        output_layout.addWidget(output_label)
        self.output_folder_input = QLineEdit()
        self.output_folder_input.setPlaceholderText("Select output folder")
        self.output_folder_input.setMinimumHeight(30)
        
        # Set the last used output folder if available
        if self.config.get("last_output_folder"):
            self.output_folder_input.setText(self.config["last_output_folder"])
            
        browse_output_button = QPushButton("Browse")
        browse_output_button.setMinimumHeight(30)
        browse_output_button.setFixedWidth(80)
        browse_output_button.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(self.output_folder_input)
        output_layout.addWidget(browse_output_button)
        options_layout.addLayout(output_layout)
        
        main_layout.addLayout(options_layout)
    
    def setup_action_buttons(self, main_layout):
        """Set up the action buttons section."""
        action_layout = QHBoxLayout()
        
        # Download button
        self.download_button = QPushButton("Download Videos")
        self.download_button.setMinimumHeight(50)
        self.download_button.clicked.connect(self.start_download)
        
        # Transcript button
        self.transcript_button = QPushButton("Save Transcripts")
        self.transcript_button.setMinimumHeight(50)
        self.transcript_button.clicked.connect(self.save_transcripts)
        
        # Summary button
        self.summary_button = QPushButton("Generate Summaries")
        self.summary_button.setMinimumHeight(50)
        self.summary_button.clicked.connect(self.generate_summaries)
        
        action_layout.addWidget(self.download_button)
        action_layout.addWidget(self.transcript_button)
        action_layout.addWidget(self.summary_button)
        
        main_layout.addLayout(action_layout)
    
    def setup_progress_section(self, main_layout):
        """Set up the progress section with progress bar and text area."""
        progress_group = QGroupBox("Progress")
        progress_group.setStyleSheet("color: #00FF41;")
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(10)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMinimumHeight(150)
        progress_layout.addWidget(self.progress_text)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
    
    def apply_theme(self, theme_name):
        """Apply the selected theme to the application."""
        if theme_name == "matrix":
            self.setStyleSheet(get_matrix_stylesheet())
        # Add more themes here as needed
        
        # Save the theme preference
        self.config["theme"] = theme_name
        save_config(self.config)
    
    def save_format_preference(self, format_type):
        """Save the selected format to config."""
        self.config["last_format"] = format_type
        save_config(self.config)
    
    def save_quality_preference(self, quality):
        """Save the selected quality to config."""
        self.config["last_quality"] = quality
        save_config(self.config)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for files."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.txt'):
                    event.acceptProposedAction()
                    return
        self.statusBar().showMessage("Only .txt files containing URLs are accepted")
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for files."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.txt'):
                self.load_urls_from_file(file_path)
                self.statusBar().showMessage(f"Loaded URLs from {os.path.basename(file_path)}")
                event.acceptProposedAction()
    
    def load_urls_from_file(self, file_path):
        """Load URLs from a text file into the table."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and yd.is_url(line.strip())]
            
            if not urls:
                self.statusBar().showMessage("No valid YouTube URLs found in the file")
                return
            
            # Clear existing URLs
            for row in range(self.url_table.rowCount()):
                self.url_table.setItem(row, 0, None)
                self.url_table.setItem(row, 1, None)
            
            # Add new URLs
            for i, url in enumerate(urls):
                if i >= self.url_table.rowCount():
                    self.url_table.setRowCount(i + 1)
                self.url_table.setItem(i, 0, QTableWidgetItem(url))
                # Titles will be fetched automatically by the cell changed event
            
            self.update_progress(f"Loaded {len(urls)} URLs from {os.path.basename(file_path)}")
        except Exception as e:
            self.statusBar().showMessage(f"Error loading URLs: {str(e)}")
    
    def on_cell_changed(self, row, column):
        """Handle cell changes in the URL table."""
        if self.is_updating_cell or column != 0:
            return
            
        self.is_updating_cell = True
        
        try:
            url_item = self.url_table.item(row, 0)
            if url_item and yd.is_url(url := url_item.text().strip()):
                self.statusBar().showMessage(f"Fetching title for {url}...")
                
                # Create a thread to fetch the video title
                self.fetch_video_title(row, url)
        finally:
            self.is_updating_cell = False
    
    def fetch_video_title(self, row, url):
        """Fetch the video title in a separate thread."""
        def fetch_title():
            try:
                # Extract video ID
                video_id = yd.extract_video_id(url)
                if not video_id:
                    return
                    
                # Use yt-dlp to get video info
                import yt_dlp
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Title')
                    
                    # Update the title cell in the main thread
                    self.update_title_signal.emit(row, title)
            except Exception as e:
                print(f"Error fetching title: {str(e)}")
            finally:
                self.statusBar().showMessage("Ready")
        
        thread = threading.Thread(target=fetch_title)
        thread.daemon = True
        thread.start()
    
    @pyqtSlot(int, str)
    def update_title_cell(self, row, title):
        """Update the title cell in the table."""
        self.url_table.setItem(row, 1, QTableWidgetItem(title))
    
    def browse_output_folder(self):
        """Open folder dialog to select output directory."""
        # Start from the last used folder if available
        start_dir = self.config.get("last_output_folder", "")
        if not start_dir or not os.path.exists(start_dir):
            start_dir = os.path.expanduser("~")
            
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", start_dir)
        if folder:
            self.output_folder_input.setText(folder)
            # Save the selected folder to config
            self.config["last_output_folder"] = folder
            save_config(self.config)
    
    def update_progress(self, message):
        """Update progress text and progress bar."""
        self.progress_text.append(message)
        if "Downloading" in message and "%" in message:
            try:
                percent = int(message.split('%')[0].split()[-1])
                self.progress_bar.setValue(percent)
            except (IndexError, ValueError):
                pass
        scrollbar = self.progress_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def download_finished(self, success, message):
        """Handle download completion."""
        self.update_progress(message)
        self.progress_bar.setValue(100 if success else 0)
        self.download_button.setEnabled(True)
        self.transcript_button.setEnabled(True)
        self.summary_button.setEnabled(True)
        self.download_thread = None
    
    def get_urls_from_table(self):
        """Get all valid URLs from the table."""
        urls = []
        for row in range(self.url_table.rowCount()):
            item = self.url_table.item(row, 0)
            if item and yd.is_url(item := item.text().strip()):
                urls.append(item)
        return urls
    
    def start_download(self):
        """Start the download process."""
        self.progress_text.clear()
        urls = self.get_urls_from_table()

        if not urls:
            self.update_progress("Please enter at least one valid YouTube URL in the table.")
            return

        self.update_progress(f"Found {len(urls)} URLs to process")
        self.download_button.setEnabled(False)
        self.transcript_button.setEnabled(False)
        self.summary_button.setEnabled(False)
        
        for url in urls:
            self.download_single(url)
    
    def download_single(self, url):
        """Download a single video."""
        format_type = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        output_folder = self.output_folder_input.text()

        # Create a custom download worker with underscore filenames
        self.download_thread = DownloadWorker(url, format_type, quality, output_folder)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()
    
    def save_transcripts(self):
        """Save transcripts for videos in the table."""
        self.progress_text.clear()
        urls = self.get_urls_from_table()

        if not urls:
            self.update_progress("Please enter at least one valid YouTube URL in the table.")
            return

        self.update_progress(f"Found {len(urls)} URLs to process for transcripts")
        self.download_button.setEnabled(False)
        self.transcript_button.setEnabled(False)
        self.summary_button.setEnabled(False)
        
        # Run in a separate thread to avoid freezing the UI
        thread = threading.Thread(target=self.process_transcripts, args=(urls,))
        thread.daemon = True
        thread.start()
    
    def process_transcripts(self, urls):
        """Process transcripts for the given URLs."""
        for url in urls:
            try:
                self.update_progress(f"Getting transcript for {url}")
                import ytsummarator as yt_sum
                video_id = yt_sum.extract_video_id(url)
                if not video_id:
                    self.update_progress(f"Error: Could not extract video ID from URL: {url}")
                    continue
                    
                # Get video title
                video_title = yt_sum.get_video_title(video_id)
                self.update_progress(f"Processing {video_title}")
                
                # Get the transcript
                transcript = yt_sum.YouTubeTranscriptApi.get_transcript(video_id)
                full_transcript = "\n".join([entry['text'] for entry in transcript])
                
                # Save transcript with versioning and underscores instead of spaces
                sanitized_title = video_title.replace(" ", "_")
                base_transcript_file = f"{sanitized_title}_transcript"
                transcript_file = yt_sum.get_next_available_filename(base_transcript_file, ".txt")
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write(full_transcript)
                self.update_progress(f"Transcript has been saved to {transcript_file}")
            except Exception as e:
                self.update_progress(f"Error processing {url}: {str(e)}")
        
        # Re-enable buttons when done
        self.download_button.setEnabled(True)
        self.transcript_button.setEnabled(True)
        self.summary_button.setEnabled(True)
    
    def generate_summaries(self):
        """Generate summaries for videos in the table."""
        self.progress_text.clear()
        urls = self.get_urls_from_table()

        if not urls:
            self.update_progress("Please enter at least one valid YouTube URL in the table.")
            return

        self.update_progress(f"Found {len(urls)} URLs to process for summaries")
        self.download_button.setEnabled(False)
        self.transcript_button.setEnabled(False)
        self.summary_button.setEnabled(False)
        
        # Run in a separate thread to avoid freezing the UI
        thread = threading.Thread(target=self.process_summaries, args=(urls,))
        thread.daemon = True
        thread.start()
    
    def process_summaries(self, urls):
        """Process summaries for the given URLs."""
        for url in urls:
            try:
                self.update_progress(f"Processing summary for {url}")
                
                # We need to modify the ytsummarator behavior to use underscores
                import ytsummarator as yt_sum
                
                # Store the original get_next_available_filename function
                original_get_filename = yt_sum.get_next_available_filename
                
                # Create a wrapper function that replaces spaces with underscores
                def underscore_filename_wrapper(base_filename, extension):
                    # Replace spaces with underscores in the base filename
                    base_filename = base_filename.replace(" ", "_")
                    return original_get_filename(base_filename, extension)
                
                # Replace the function temporarily
                yt_sum.get_next_available_filename = underscore_filename_wrapper
                
                # Call the original function
                yt_sum.get_transcript(url)
                
                # Restore the original function
                yt_sum.get_next_available_filename = original_get_filename
                
            except Exception as e:
                self.update_progress(f"Error processing {url}: {str(e)}")
        
        # Re-enable buttons when done
        self.download_button.setEnabled(True)
        self.transcript_button.setEnabled(True)
        self.summary_button.setEnabled(True)

    def resizeEvent(self, event):
        """Handle window resize event to save window size."""
        self.config["window_width"] = self.width()
        self.config["window_height"] = self.height()
        save_config(self.config)
        super().resizeEvent(event)

    def closeEvent(self, event):
        """Handle window close event to ensure threads are properly terminated."""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.quit()
            self.download_thread.wait()
            
        # Save the current output folder path before closing
        output_folder = self.output_folder_input.text()
        if output_folder:
            self.config["last_output_folder"] = output_folder
            save_config(self.config)
            
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = YouTubeDownloaderGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 