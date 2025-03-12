#!/usr/bin/env python3
import sys
import os
import json
import threading
import logging
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QComboBox, QProgressBar, QTextEdit, QFileDialog,
                            QCheckBox, QGroupBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMenu, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QMimeData, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QAction
import youtube_downloader as yd

# Import themes
from themes import get_matrix_stylesheet, get_dark_stylesheet, AVAILABLE_THEMES

# Config file for storing user preferences
CONFIG_FILE = os.path.expanduser("~/.youtube_extractor_config.json")

def load_config():
    """Load configuration from file."""
    default_config = {
        "last_output_folder": "",
        "last_format": "mp4",
        "last_quality": "best",
        "window_width": 900,
        "window_height": 700,
        "theme": "matrix",
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
        self.is_cancelled = False
    
    def run(self):
        """Main thread execution method."""
        if self.is_cancelled:
            return
            
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
            
            if not self.is_cancelled:
                self.finished.emit(True, "Download completed successfully!")
        except Exception as e:
            if not self.is_cancelled:
                self.finished.emit(False, f"Error: {str(e)}")
    
    def cancel(self):
        """Mark the thread as cancelled to prevent further processing."""
        self.is_cancelled = True

class TranscriptWorker(QThread):
    """Worker thread for generating transcripts."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, urls, output_folder=None):
        super().__init__()
        self.urls = urls
        self.output_folder = output_folder
        self.is_cancelled = False
    
    def format_timestamp(self, seconds):
        """Convert seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    def format_transcript_chunk(self, chunk):
        """Format a chunk of transcript entries with bullet points and fewer timestamps."""
        formatted_lines = []
        chunk_start = self.format_timestamp(chunk[0]['start'])
        chunk_end = self.format_timestamp(chunk[-1]['start'] + chunk[-1]['duration'])
        formatted_lines.append(f"\n[{chunk_start} - {chunk_end}]")
        formatted_lines.append("-" * 40)  # Separator line
        
        last_timestamp = chunk[0]['start']
        current_text = []
        
        for entry in chunk:
            # Show a new timestamp if there's a significant pause (more than 2 seconds)
            # or if this is the first entry
            time_gap = entry['start'] - last_timestamp if current_text else 0
            
            if time_gap > 2.0 and current_text:
                # Join the previous text entries and add them
                formatted_lines.append(f"• {' '.join(current_text)}")
                current_text = []
                # Add a timestamp for the new entry
                timestamp = self.format_timestamp(entry['start'])
                current_text.append(f"[{timestamp}] {entry['text']}")
            else:
                current_text.append(entry['text'])
            
            last_timestamp = entry['start']
        
        # Add any remaining text
        if current_text:
            formatted_lines.append(f"• {' '.join(current_text)}")
        
        return "\n".join(formatted_lines)
    
    def chunk_transcript(self, transcript, chunk_duration=300):
        """Split transcript into chunks of specified duration (default 5 minutes)."""
        chunks = []
        current_chunk = []
        chunk_start = 0
        
        for entry in transcript:
            # Start a new chunk if:
            # 1. We've exceeded the chunk duration
            # 2. There's a long pause (more than 5 seconds)
            time_since_chunk_start = entry['start'] - chunk_start
            if time_since_chunk_start >= chunk_duration or (current_chunk and entry['start'] - (current_chunk[-1]['start'] + current_chunk[-1]['duration']) > 5):
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = []
                chunk_start = entry['start']
            current_chunk.append(entry)
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def format_transcript(self, transcript):
        """Format the full transcript with metadata."""
        formatted_lines = [
            f"Title: {yt_sum.get_video_title(self.urls[0])}",
            f"URL: {self.urls[0]}",
            f"Duration: {self.format_timestamp(transcript[-1]['start'] + transcript[-1]['duration'])}",
            "\nTranscript:",
            "=" * 50  # Separator line
        ]
        
        # Add each formatted chunk
        for chunk in self.chunk_transcript(transcript):
            formatted_lines.append(self.format_transcript_chunk(chunk))
        
        full_transcript = "\n".join(formatted_lines)
        return full_transcript
    
    def run(self):
        """Main thread execution method."""
        if self.is_cancelled:
            return
            
        try:
            import ytsummarator as yt_sum
            for url in self.urls:
                if self.is_cancelled:
                    break
                    
                try:
                    self.progress.emit(f"Getting transcript for {url}")
                    video_id = yt_sum.extract_video_id(url)
                    if not video_id:
                        self.progress.emit(f"❌ Error: Could not extract video ID from URL: {url}")
                        self.progress.emit("---")
                        continue
                        
                    # Get video title
                    video_title = yt_sum.get_video_title(video_id)
                    self.progress.emit(f"Processing transcript for: {video_title}")
                    
                    # Get the transcript
                    transcript = yt_sum.YouTubeTranscriptApi.get_transcript(video_id)
                    
                    # Format the full transcript with metadata
                    formatted_transcript = self.format_transcript(transcript)
                    
                    # Save transcript with versioning and underscores instead of spaces
                    sanitized_title = video_title.replace(" ", "_")
                    base_transcript_file = f"{sanitized_title}_transcript"
                    
                    # Use output folder if provided
                    if self.output_folder:
                        base_transcript_file = os.path.join(self.output_folder, os.path.basename(base_transcript_file))
                    
                    transcript_file = yt_sum.get_next_available_filename(base_transcript_file, ".txt")
                    
                    # Save the transcript
                    with open(transcript_file, 'w', encoding='utf-8') as f:
                        f.write(formatted_transcript)
                    
                    # Update progress with success message
                    self.progress.emit(f"✓ Transcript saved to: {transcript_file}")
                    self.progress.emit("---")
                    
                except Exception as e:
                    self.progress.emit(f"❌ Error processing {url}: {str(e)}")
                    self.progress.emit("---")
            
            if not self.is_cancelled:
                self.progress.emit("✨ Transcript generation completed!")
                self.finished.emit(True, "All transcripts processed successfully!")
                
        except Exception as e:
            if not self.is_cancelled:
                self.finished.emit(False, f"Error: {str(e)}")
    
    def cancel(self):
        """Mark the thread as cancelled to prevent further processing."""
        self.is_cancelled = True

class SummaryWorker(QThread):
    """Worker thread for generating summaries."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, urls, output_folder):
        super().__init__()
        self.urls = urls
        self.output_folder = output_folder
        self.is_cancelled = False
    
    def run(self):
        """Main thread execution method."""
        if self.is_cancelled:
            return
            
        try:
            import ytsummarator as yt_sum
            for url in self.urls:
                if self.is_cancelled:
                    break
                    
                try:
                    self.progress.emit(f"Getting video information for {url}")
                    video_id = yt_sum.extract_video_id(url)
                    if not video_id:
                        self.progress.emit(f"❌ Error: Could not extract video ID from URL: {url}")
                        self.progress.emit("---")
                        continue
                        
                    # Get video title
                    video_title = yt_sum.get_video_title(video_id)
                    self.progress.emit(f"Processing video: {video_title}")
                    
                    # Store the original get_next_available_filename function
                    original_get_filename = yt_sum.get_next_available_filename
                    
                    # Create a wrapper function that replaces spaces with underscores
                    def underscore_filename_wrapper(base_filename, extension):
                        base_filename = base_filename.replace(" ", "_")
                        return original_get_filename(base_filename, extension)
                    
                    # Replace the function temporarily
                    yt_sum.get_next_available_filename = underscore_filename_wrapper
                    
                    # First get the transcript
                    self.progress.emit(f"📝 Generating transcript...")
                    transcript_file = yt_sum.get_transcript(url, output_folder=self.output_folder)
                    self.progress.emit(f"✓ Transcript saved to: {transcript_file}")
                    
                    # Now generate the summary
                    self.progress.emit(f"🤖 Generating AI summary...")
                    summary_file = yt_sum.get_summary(url, output_folder=self.output_folder)
                    self.progress.emit(f"✓ Summary saved to: {summary_file}")
                    
                    # Restore the original function
                    yt_sum.get_next_available_filename = original_get_filename
                    
                    self.progress.emit("---")
                    
                except Exception as e:
                    self.progress.emit(f"❌ Error processing {url}: {str(e)}")
                    self.progress.emit("---")
            
            if not self.is_cancelled:
                self.progress.emit("✨ Summary generation completed!")
                self.finished.emit(True, "All summaries processed successfully!")
                
        except Exception as e:
            if not self.is_cancelled:
                self.finished.emit(False, f"Error: {str(e)}")
    
    def cancel(self):
        """Mark the thread as cancelled to prevent further processing."""
        self.is_cancelled = True

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
        self.setMinimumSize(800, 600)  # Reduced minimum size for better compatibility with smaller screens
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Connect the update title signal to the slot
        self.update_title_signal.connect(self.update_title_cell)
        
        # Initialize UI components
        self.setup_ui()
        
        # Create menu bar
        self.setup_menu()
        
        # Apply theme
        self.apply_theme(self.config.get("theme", "matrix"))
        
        # Initialize thread-related attributes
        self.download_thread = None
        self.running_threads = []
        self.current_urls = []
        
        # Flag to prevent recursive cell change events
        self.is_updating_cell = False
    
    def setup_menu(self):
        """Set up the application menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # Open URLs file action
        open_action = QAction("Open URLs File", self)
        open_action.triggered.connect(self.open_urls_file)
        file_menu.addAction(open_action)
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menu_bar.addMenu("Settings")
        
        # Theme submenu
        theme_menu = QMenu("Theme", self)
        theme_menu.setObjectName("ThemeMenu")
        
        # Add theme options
        for theme_name in AVAILABLE_THEMES:
            theme_action = QAction(theme_name.capitalize(), self)
            theme_action.setCheckable(True)
            theme_action.setChecked(self.config.get("theme") == theme_name)
            theme_action.triggered.connect(lambda checked, tn=theme_name: self.apply_theme(tn))
            theme_menu.addAction(theme_action)
        
        settings_menu.addMenu(theme_menu)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def open_urls_file(self):
        """Open a file containing YouTube URLs."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open URLs File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.load_urls_from_file(file_path)
    
    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About YouTube Extractor",
            "YouTube Extractor v1.0\n\n"
            "A tool for downloading YouTube videos, transcripts, and generating summaries.\n\n"
            "© 2024 All Rights Reserved"
        )
    
    def setup_ui(self):
        """Set up the user interface components."""
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)  # Reduced spacing
        main_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins
        
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
        
        # Hide the status bar as it's redundant with the progress section
        self.statusBar().hide()
    
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
        
        # Set row height to be more compact
        self.url_table.verticalHeader().setDefaultSectionSize(30)
        
        # Make the table take a proportional amount of space
        self.url_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.url_table.setMinimumHeight(200)  # Reduced minimum height
        
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
        self.format_combo.setMinimumWidth(100)
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
        self.quality_combo.setMinimumWidth(100)
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
        action_layout.setSpacing(8)  # Reduced spacing between buttons
        
        # Download button
        self.download_button = QPushButton("Download Videos")
        self.download_button.setMinimumHeight(40)  # Reduced height
        self.download_button.clicked.connect(self.start_download)
        
        # Transcript button
        self.transcript_button = QPushButton("Save Transcripts")
        self.transcript_button.setMinimumHeight(40)  # Reduced height
        self.transcript_button.clicked.connect(self.save_transcripts)
        
        # Summary button
        self.summary_button = QPushButton("Generate Summaries")
        self.summary_button.setMinimumHeight(40)  # Reduced height
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
        progress_layout.setSpacing(5)  # Reduced spacing
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(20)  # Reduced height
        self.progress_bar.setFormat("0% - Ready")  # Simpler initial format
        self.progress_bar.setTextVisible(True)  # Ensure text is visible
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMinimumHeight(100)  # Reduced minimum height
        
        # Make the text area take a proportional amount of space
        self.progress_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        progress_layout.addWidget(self.progress_text)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
    
    def apply_theme(self, theme_name):
        """Apply the selected theme to the application."""
        # Update theme in all theme actions
        theme_menu = self.findChild(QMenu, "ThemeMenu")
        if theme_menu:
            for action in theme_menu.actions():
                action.setChecked(action.text().lower() == theme_name.capitalize())
        
        # Apply the selected theme stylesheet
        if theme_name == "matrix":
            self.setStyleSheet(get_matrix_stylesheet())
        elif theme_name == "dark":
            self.setStyleSheet(get_dark_stylesheet())
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
        self.update_progress("Only .txt files containing URLs are accepted")
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for files."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.txt'):
                self.load_urls_from_file(file_path)
                self.update_progress(f"Loaded URLs from {os.path.basename(file_path)}")
                event.acceptProposedAction()
    
    def load_urls_from_file(self, file_path):
        """Load URLs from a text file into the table."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and yd.is_url(line.strip())]
            
            if not urls:
                self.update_progress("No valid YouTube URLs found in the file")
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
            self.update_progress(f"Error loading URLs: {str(e)}")
    
    def on_cell_changed(self, row, column):
        """Handle cell changes in the URL table."""
        if self.is_updating_cell or column != 0:
            return
            
        self.is_updating_cell = True
        
        try:
            url_item = self.url_table.item(row, 0)
            if url_item and yd.is_url(url := url_item.text().strip()):
                self.update_progress(f"Fetching title for {url}...")
                
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
                self.update_progress(f"Error fetching title: {str(e)}")
            finally:
                # Remove thread from tracking list when done
                if thread in self.running_threads:
                    self.running_threads.remove(thread)
        
        thread = threading.Thread(target=fetch_title)
        thread.daemon = True
        # Add thread to tracking list
        self.running_threads.append(thread)
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
        
        # Function to strip ANSI color codes
        def strip_ansi_codes(text):
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            return ansi_escape.sub('', text)
        
        # Check for our formatted download progress message
        if "Downloading:" in message and "|" in message:
            try:
                # Strip ANSI color codes and split the message
                clean_message = strip_ansi_codes(message)
                parts = clean_message.split("|")
                
                # Parse the percentage
                percent_part = parts[0].strip().replace("Downloading:", "").strip()
                percent = int(float(percent_part.replace("%", "")))
                
                # Extract size information
                size_part = parts[1].strip()
                downloaded_size, total_size = [s.strip() for s in size_part.split("/")]
                
                # Extract speed and ETA
                speed = parts[2].strip().replace("Speed:", "").strip()
                eta = parts[3].strip().replace("ETA:", "").strip()
                
                # Update progress bar
                self.progress_bar.setValue(percent)
                self.progress_bar.setFormat(f"{percent}% - {downloaded_size}/{total_size} - {speed} - ETA: {eta}")
            except (IndexError, ValueError) as e:
                # Fall back to basic progress display if parsing fails
                print(f"Error parsing progress: {e}")
                pass
        # Handle legacy format for backward compatibility
        elif "Downloading" in message and "%" in message:
            try:
                # Strip ANSI color codes first
                clean_message = strip_ansi_codes(message)
                
                # Extract percentage and other information
                percent_text = clean_message.split('%')[0].split()[-1]
                percent = int(float(percent_text))
                self.progress_bar.setValue(percent)
                
                # Update progress bar format with more information
                if "ETA" in clean_message:
                    eta = clean_message.split("ETA")[1].strip() if "ETA" in clean_message else "unknown"
                    speed = clean_message.split("at")[1].split("ETA")[0].strip() if "at" in clean_message and "ETA" in clean_message else ""
                    self.progress_bar.setFormat(f"{percent}% - {speed} - ETA: {eta}")
                else:
                    self.progress_bar.setFormat(f"{percent}% - Downloading...")
            except (IndexError, ValueError):
                pass
        elif "completed" in message.lower():
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("100% - Download Complete")
        
        # Auto-scroll to the bottom
        scrollbar = self.progress_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def download_finished(self, success, message):
        """Handle download completion."""
        self.update_progress(message)
        
        # If there are more URLs to process, start the next one
        if hasattr(self, 'current_urls') and self.current_urls:
            next_url = self.current_urls.pop(0)
            self.download_single(next_url)
        else:
            # All downloads completed
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
        
        # Initialize the list of URLs to process
        self.current_urls = urls.copy()
        if self.current_urls:
            # Start with the first URL
            self.download_single(self.current_urls.pop(0))
        else:
            self.update_progress("No valid URLs to download.")
            self.download_button.setEnabled(True)
            self.transcript_button.setEnabled(True)
            self.summary_button.setEnabled(True)
    
    def download_single(self, url):
        """Download a single video."""
        # If there's already a download thread running, wait for it to finish
        if self.download_thread and self.download_thread.isRunning():
            # Cancel the current download
            self.download_thread.cancel()
            
            # Disconnect signals
            try:
                self.download_thread.progress.disconnect()
                self.download_thread.finished.disconnect()
            except TypeError:
                pass
            
            # Wait for it to finish
            self.download_thread.wait(1000)
            
            # If it's still running, terminate it
            if self.download_thread.isRunning():
                self.download_thread.terminate()
                self.download_thread.wait()
        
        format_type = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        output_folder = self.output_folder_input.text()

        self.update_progress(f"Starting download for: {url}")
        
        # Create a new download worker
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

        # Check if output folder is selected
        output_folder = self.output_folder_input.text()
        if not output_folder:
            self.update_progress("Please select an output folder first.")
            return

        self.update_progress(f"Found {len(urls)} URLs to process for transcripts")
        self.download_button.setEnabled(False)
        self.transcript_button.setEnabled(False)
        self.summary_button.setEnabled(False)
        
        # Create and start the transcript worker thread with output folder
        self.transcript_thread = TranscriptWorker(urls, output_folder)
        self.transcript_thread.progress.connect(self.update_progress)
        self.transcript_thread.finished.connect(self.transcript_finished)
        self.transcript_thread.start()
    
    def transcript_finished(self, success, message):
        """Handle transcript generation completion."""
        self.update_progress(message)
        
        # Re-enable buttons
        self.download_button.setEnabled(True)
        self.transcript_button.setEnabled(True)
        self.summary_button.setEnabled(True)
        
        # Clear the thread
        self.transcript_thread = None
    
    def generate_summaries(self):
        """Generate summaries for videos in the table."""
        self.progress_text.clear()
        urls = self.get_urls_from_table()

        if not urls:
            self.update_progress("Please enter at least one valid YouTube URL in the table.")
            return

        # Check if output folder is selected
        output_folder = self.output_folder_input.text()
        if not output_folder:
            self.update_progress("Please select an output folder first.")
            return

        self.update_progress(f"Found {len(urls)} URLs to process for summaries")
        self.download_button.setEnabled(False)
        self.transcript_button.setEnabled(False)
        self.summary_button.setEnabled(False)
        
        # Create and start the summary worker thread with output folder
        self.summary_thread = SummaryWorker(urls, output_folder)
        self.summary_thread.progress.connect(self.update_progress)
        self.summary_thread.finished.connect(self.summary_finished)
        self.summary_thread.start()
    
    def summary_finished(self, success, message):
        """Handle summary generation completion."""
        self.update_progress(message)
        
        # Re-enable buttons
        self.download_button.setEnabled(True)
        self.transcript_button.setEnabled(True)
        self.summary_button.setEnabled(True)
        
        # Clear the thread
        self.summary_thread = None
    
    def resizeEvent(self, event):
        """Handle window resize event to save window size."""
        self.config["window_width"] = self.width()
        self.config["window_height"] = self.height()
        save_config(self.config)
        super().resizeEvent(event)

    def closeEvent(self, event):
        """Handle window close event to ensure threads are properly terminated."""
        # Save the current output folder path before closing
        output_folder = self.output_folder_input.text()
        if output_folder:
            self.config["last_output_folder"] = output_folder
            save_config(self.config)
        
        # Properly terminate the download thread if it's running
        if self.download_thread and self.download_thread.isRunning():
            try:
                # Mark the thread as cancelled
                self.download_thread.cancel()
                
                # Disconnect all signals from this thread to prevent callbacks
                try:
                    self.download_thread.progress.disconnect()
                    self.download_thread.finished.disconnect()
                except TypeError:
                    pass  # Signals might already be disconnected
                
                # Wait for the thread to finish naturally with a longer timeout
                if not self.download_thread.wait(2000):  # Wait up to 2 seconds
                    # If thread doesn't finish in time, try to quit the event loop
                    self.download_thread.quit()
                    if not self.download_thread.wait(1000):  # Wait another second
                        # Only terminate as a last resort
                        self.download_thread.terminate()
                        self.download_thread.wait()
            except Exception as e:
                print(f"Error terminating download thread: {e}")
        
        # For other running threads, try to stop them gracefully
        remaining_threads = self.running_threads.copy()  # Make a copy to avoid modification during iteration
        for thread in remaining_threads:
            try:
                # Wait up to 1 second for each thread
                thread.join(timeout=1.0)
            except Exception as e:
                print(f"Error waiting for thread: {e}")
        
        # Clear the thread lists
        self.running_threads.clear()
        
        # Accept the close event
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = YouTubeDownloaderGUI()
    window.show()
    
    # Use a try-finally block to ensure proper cleanup
    try:
        sys.exit(app.exec())
    finally:
        # Ensure all threads are properly terminated
        if hasattr(window, 'download_thread') and window.download_thread:
            if window.download_thread.isRunning():
                window.download_thread.cancel()
                window.download_thread.terminate()
                window.download_thread.wait()

if __name__ == "__main__":
    main() 