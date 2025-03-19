"""Main window for the YouTube Summarator GUI."""
import os
import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit,
    QFileDialog, QProgressBar, QMessageBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenuBar,
    QMenu, QStatusBar, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QMimeData, QUrl
from PyQt6.QtGui import QIcon, QAction, QDragEnterEvent, QDropEvent
from .workers import DownloadWorker, TranscriptWorker, SummaryWorker
from .themes import get_matrix_stylesheet, get_dark_stylesheet, AVAILABLE_THEMES
from ..models.summary_depth import SummaryDepth
from ..config.settings import Config

# Config file for storing user preferences
CONFIG_FILE = os.path.expanduser("~/.youtube_extractor_config.json")

def load_config():
    """Load configuration from file."""
    default_config = {
        "last_output_folder": "",
        "last_format": "mp4",
        "last_quality": "best",
        "last_depth": SummaryDepth.DETAILED.value,
        "last_model": "gpt-3.5-turbo",
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

class YouTubeDownloaderGUI(QMainWindow):
    """Main window for the YouTube Summarator application."""
    
    # Define a custom signal for updating the title cell
    update_title_signal = pyqtSignal(int, str)
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("YouTube Summarator")
        
        # Load configuration
        self.config = load_config()
        self.setMinimumSize(self.config["window_width"], self.config["window_height"])
        
        # Initialize UI
        self.init_ui()
        
        # Set up theme
        self.apply_theme(self.config["theme"])
        
        # Initialize workers
        self.download_worker = None
        self.transcript_worker = None
        self.summary_worker = None
        
        # Connect signals
        self.update_title_signal.connect(self.update_title_cell)
    
    def init_ui(self):
        """Initialize the user interface."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create URL table section
        url_group = QGroupBox("Video URLs")
        url_layout = QVBoxLayout()
        
        # Create URL table
        self.url_table = QTableWidget()
        self.url_table.setColumnCount(2)
        self.url_table.setHorizontalHeaderLabels(["URL", "Title"])
        self.url_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.url_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.url_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.url_table.customContextMenuRequested.connect(self.show_table_context_menu)
        
        # Add 5 rows by default
        self.url_table.setRowCount(5)
        for row in range(5):
            self.url_table.setItem(row, 0, QTableWidgetItem(""))
            self.url_table.setItem(row, 1, QTableWidgetItem(""))
        
        # Add URL table buttons
        table_buttons_layout = QHBoxLayout()
        add_row_button = QPushButton("Add Row")
        add_row_button.clicked.connect(self.add_table_row)
        table_buttons_layout.addWidget(add_row_button)
        
        remove_row_button = QPushButton("Remove Selected")
        remove_row_button.clicked.connect(self.remove_selected_rows)
        table_buttons_layout.addWidget(remove_row_button)
        
        url_layout.addWidget(self.url_table)
        url_layout.addLayout(table_buttons_layout)
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)
        
        # Create options section
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mp3", "m4a", "webm", "mkv"])
        self.format_combo.setCurrentText(self.config["last_format"])
        self.format_combo.currentTextChanged.connect(self.save_format_preference)
        format_layout.addWidget(self.format_combo)
        options_layout.addLayout(format_layout)
        
        # Quality selection
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["best", "1080p", "720p", "480p", "360p"])
        self.quality_combo.setCurrentText(self.config["last_quality"])
        self.quality_combo.currentTextChanged.connect(self.save_quality_preference)
        quality_layout.addWidget(self.quality_combo)
        options_layout.addLayout(quality_layout)
        
        # Summary depth selection
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(QLabel("Summary Depth:"))
        self.depth_combo = QComboBox()
        self.depth_combo.addItems([d.value for d in SummaryDepth])
        self.depth_combo.setCurrentText(self.config["last_depth"])
        self.depth_combo.currentTextChanged.connect(self.save_depth_preference)
        depth_layout.addWidget(self.depth_combo)
        options_layout.addLayout(depth_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-3.5-turbo", "gpt-4"])
        self.model_combo.setCurrentText(self.config["last_model"])
        self.model_combo.currentTextChanged.connect(self.save_model_preference)
        model_layout.addWidget(self.model_combo)
        options_layout.addLayout(model_layout)
        
        # Custom title option
        title_layout = QHBoxLayout()
        self.custom_title_check = QCheckBox("Use Custom Title")
        title_layout.addWidget(self.custom_title_check)
        self.custom_title_input = QLineEdit()
        self.custom_title_input.setPlaceholderText("Enter custom title")
        self.custom_title_input.setEnabled(False)
        title_layout.addWidget(self.custom_title_input)
        options_layout.addLayout(title_layout)
        
        # Connect custom title checkbox
        self.custom_title_check.stateChanged.connect(
            lambda state: self.custom_title_input.setEnabled(state == Qt.CheckState.Checked.value)
        )
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Create output section
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        
        # Output folder selection
        folder_layout = QHBoxLayout()
        self.output_folder_input = QLineEdit()
        self.output_folder_input.setPlaceholderText("Select output folder")
        self.output_folder_input.setText(self.config["last_output_folder"])
        folder_layout.addWidget(self.output_folder_input)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_output_folder)
        folder_layout.addWidget(browse_button)
        output_layout.addLayout(folder_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        output_layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        output_layout.addWidget(self.status_text)
        
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # Create action buttons
        button_layout = QHBoxLayout()
        
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_button)
        
        self.transcript_button = QPushButton("Get Transcripts")
        self.transcript_button.clicked.connect(self.start_transcript)
        button_layout.addWidget(self.transcript_button)
        
        self.summary_button = QPushButton("Generate Summaries")
        self.summary_button.clicked.connect(self.start_summary)
        button_layout.addWidget(self.summary_button)
        
        main_layout.addLayout(button_layout)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open URLs File", self)
        open_action.triggered.connect(self.open_urls_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Theme menu
        theme_menu = menubar.addMenu("Theme")
        
        for theme in AVAILABLE_THEMES:
            theme_action = QAction(theme.capitalize(), self)
            theme_action.triggered.connect(lambda checked, t=theme: self.apply_theme(t))
            theme_menu.addAction(theme_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def add_table_row(self):
        """Add a new row to the URL table."""
        row = self.url_table.rowCount()
        self.url_table.insertRow(row)
        self.url_table.setItem(row, 0, QTableWidgetItem(""))
        self.url_table.setItem(row, 1, QTableWidgetItem(""))
    
    def remove_selected_rows(self):
        """Remove selected rows from the URL table."""
        rows = set(item.row() for item in self.url_table.selectedItems())
        for row in sorted(rows, reverse=True):
            self.url_table.removeRow(row)
    
    def show_table_context_menu(self, position):
        """Show context menu for the URL table."""
        menu = QMenu()
        paste_action = menu.addAction("Paste")
        paste_action.triggered.connect(lambda: self.paste_to_table(
            self.url_table.currentRow(),
            self.url_table.currentColumn()
        ))
        menu.exec(self.url_table.mapToGlobal(position))
    
    def paste_to_table(self, row, column):
        """Paste clipboard content to the specified table cell."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasText():
            text = mime_data.text().strip()
            if text:
                self.url_table.setItem(row, column, QTableWidgetItem(text))
                if column == 0:  # URL column
                    self.fetch_video_title(row, text)
    
    def fetch_video_title(self, row, url):
        """Fetch video title for the given URL."""
        def fetch_title():
            try:
                from ..core.summarizer import YouTubeSummarizer
                summarizer = YouTubeSummarizer()
                video_id = summarizer.get_video_id(url)
                if video_id:
                    title = summarizer.get_video_title(video_id)
                    if title:
                        self.update_title_signal.emit(row, title)
            except Exception as e:
                self.update_title_signal.emit(row, f"Error: {str(e)}")
        
        # Start title fetch in a separate thread
        thread = QThread()
        thread.run = fetch_title
        thread.start()
    
    @pyqtSlot(int, str)
    def update_title_cell(self, row, title):
        """Update the title cell in the URL table."""
        if 0 <= row < self.url_table.rowCount():
            self.url_table.setItem(row, 1, QTableWidgetItem(title))
    
    def open_urls_file(self):
        """Open a file containing URLs."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open URLs File",
            "",
            "Text Files (*.txt);;All Files (*.*)"
        )
        if file_path:
            self.load_urls_from_file(file_path)
    
    def load_urls_from_file(self, file_path):
        """Load URLs from a file."""
        try:
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            self.url_table.setRowCount(len(urls))
            for i, url in enumerate(urls):
                self.url_table.setItem(i, 0, QTableWidgetItem(url))
                self.fetch_video_title(i, url)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load URLs: {str(e)}")
    
    def get_urls_from_table(self):
        """Get all URLs from the table."""
        urls = []
        for row in range(self.url_table.rowCount()):
            url_item = self.url_table.item(row, 0)
            if url_item and url_item.text().strip():
                urls.append(url_item.text().strip())
        return urls
    
    def apply_theme(self, theme_name):
        """Apply the selected theme."""
        if theme_name == "matrix":
            self.setStyleSheet(get_matrix_stylesheet())
        elif theme_name == "dark":
            self.setStyleSheet(get_dark_stylesheet())
        
        # Save theme preference
        self.config["theme"] = theme_name
        save_config(self.config)
    
    def save_format_preference(self, format_type):
        """Save format preference."""
        self.config["last_format"] = format_type
        save_config(self.config)
    
    def save_quality_preference(self, quality):
        """Save quality preference."""
        self.config["last_quality"] = quality
        save_config(self.config)
    
    def save_depth_preference(self, depth):
        """Save depth preference."""
        self.config["last_depth"] = depth
        save_config(self.config)
    
    def save_model_preference(self, model):
        """Save model preference."""
        self.config["last_model"] = model
        save_config(self.config)
    
    def browse_output_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            self.output_folder_input.text() or os.path.expanduser("~")
        )
        if folder:
            self.output_folder_input.setText(folder)
            self.config["last_output_folder"] = folder
            save_config(self.config)
    
    def update_status(self, message):
        """Update the status text."""
        self.status_text.append(message)
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
    
    def start_download(self):
        """Start the download process."""
        urls = self.get_urls_from_table()
        if not urls:
            QMessageBox.warning(self, "Error", "Please enter at least one YouTube URL")
            return
        
        output_folder = self.output_folder_input.text().strip()
        if not output_folder:
            QMessageBox.warning(self, "Error", "Please select an output folder")
            return
        
        # Create download worker
        self.download_worker = DownloadWorker(
            urls[0],  # For now, we'll handle one URL at a time
            self.format_combo.currentText(),
            self.quality_combo.currentText(),
            output_folder,
            self.custom_title_input.text() if self.custom_title_check.isChecked() else None
        )
        
        # Connect signals
        self.download_worker.progress.connect(self.update_status)
        self.download_worker.finished.connect(self.download_finished)
        
        # Start download
        self.download_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_text.clear()
        self.download_worker.start()
    
    def start_transcript(self):
        """Start the transcript generation process."""
        urls = self.get_urls_from_table()
        if not urls:
            QMessageBox.warning(self, "Error", "Please enter at least one YouTube URL")
            return
        
        output_folder = self.output_folder_input.text().strip()
        if not output_folder:
            QMessageBox.warning(self, "Error", "Please select an output folder")
            return
        
        # Create transcript worker
        self.transcript_worker = TranscriptWorker(urls, output_folder)
        
        # Connect signals
        self.transcript_worker.progress.connect(self.update_status)
        self.transcript_worker.finished.connect(self.transcript_finished)
        
        # Start transcript generation
        self.transcript_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_text.clear()
        self.transcript_worker.start()
    
    def start_summary(self):
        """Start the summary generation process."""
        urls = self.get_urls_from_table()
        if not urls:
            QMessageBox.warning(self, "Error", "Please enter at least one YouTube URL")
            return
        
        output_folder = self.output_folder_input.text().strip()
        if not output_folder:
            QMessageBox.warning(self, "Error", "Please select an output folder")
            return
        
        # Create summary worker
        self.summary_worker = SummaryWorker(
            urls,
            output_folder,
            SummaryDepth(self.depth_combo.currentText()),
            self.model_combo.currentText()
        )
        
        # Connect signals
        self.summary_worker.progress.connect(self.update_status)
        self.summary_worker.finished.connect(self.summary_finished)
        
        # Start summary generation
        self.summary_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_text.clear()
        self.summary_worker.start()
    
    def download_finished(self, success, message):
        """Handle download completion."""
        self.download_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(message)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def transcript_finished(self, success, message):
        """Handle transcript generation completion."""
        self.transcript_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(message)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def summary_finished(self, success, message):
        """Handle summary generation completion."""
        self.summary_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(message)
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About YouTube Summarator",
            "YouTube Summarator\n\n"
            "A tool for downloading YouTube videos, generating transcripts, "
            "and creating AI-powered summaries.\n\n"
            "Version 1.0.0"
        )
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        urls = [url.toLocalFile() for url in event.mimeData().urls()]
        for url in urls:
            if url.endswith('.txt'):
                self.load_urls_from_file(url)
            else:
                row = self.url_table.rowCount()
                self.url_table.insertRow(row)
                self.url_table.setItem(row, 0, QTableWidgetItem(url))
                self.fetch_video_title(row, url)
    
    def resizeEvent(self, event):
        """Handle window resize event."""
        super().resizeEvent(event)
        self.config["window_width"] = self.width()
        self.config["window_height"] = self.height()
        save_config(self.config)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up resources
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait()
        
        if self.transcript_worker and self.transcript_worker.isRunning():
            self.transcript_worker.cancel()
            self.transcript_worker.wait()
        
        if self.summary_worker and self.summary_worker.isRunning():
            self.summary_worker.cancel()
            self.summary_worker.wait()
        
        # Save configuration
        save_config(self.config)
        
        event.accept() 