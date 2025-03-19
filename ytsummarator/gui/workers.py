"""Worker threads for background processing."""
import os
import json
import time
import threading
import logging
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp
from ..core.summarizer import YouTubeSummarizer
from ..models.summary_depth import SummaryDepth

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
    
    def __init__(self, url, format_type, quality, output_folder, custom_title=None):
        super().__init__()
        self.url = url
        self.format_type = format_type
        self.quality = quality
        self.output_folder = output_folder
        self.custom_title = custom_title
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
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': self.get_format_spec(),
                'progress_hooks': [self.handle_progress],
                'restrictfilenames': True,
                'windowsfilenames': True,
                'overwrites': True,
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
                'retries': 3,
                'fragment_retries': 3,
                'file_access_retries': 3,
                'extractor_retries': 3,
                'ignoreerrors': False,
            }
            
            # Set output template based on custom title or default
            if self.custom_title:
                sanitized_title = self.custom_title.replace(' ', '_')
                sanitized_title = ''.join(c for c in sanitized_title if c.isalnum() or c in '_-')
                ydl_opts['outtmpl'] = os.path.join(self.output_folder, f"{sanitized_title}.%(ext)s")
            else:
                ydl_opts['outtmpl'] = os.path.join(self.output_folder, '%(title)s.%(ext)s')
            
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            if not self.is_cancelled:
                self.finished.emit(True, "Download completed successfully!")
        except Exception as e:
            if not self.is_cancelled:
                self.finished.emit(False, f"Error: {str(e)}")
    
    def get_format_spec(self):
        """Get format specification based on format type and quality."""
        if self.format_type in ['mp3', 'm4a']:
            return 'bestaudio/best'
        elif self.format_type in ['mp4', 'webm', 'mkv']:
            if self.quality == 'best':
                return f'bestvideo[ext={self.format_type}]+bestaudio[ext={self.format_type}]/best[ext={self.format_type}]'
            else:
                return f'bestvideo[height<={self.quality[:-1]}][ext={self.format_type}]+bestaudio[ext={self.format_type}]/best[height<={self.quality[:-1]}][ext={self.format_type}]'
        return 'best'
    
    def handle_progress(self, d):
        """Handle download progress updates."""
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes', 0)
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                if total:
                    percent = (downloaded / total) * 100
                    size_str = f"{self.format_size(downloaded)}/{self.format_size(total)}"
                    speed_str = self.format_size(speed) + "/s"
                    eta_str = self.format_time(eta)
                    
                    self.progress.emit(
                        f"Downloading: {percent:.1f}% | {size_str} | "
                        f"Speed: {speed_str} | ETA: {eta_str}"
                    )
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.progress.emit("Download completed, processing...")
    
    def format_size(self, size):
        """Format size in bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
    
    def format_time(self, seconds):
        """Format time in seconds to human readable string."""
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds / 60
        if minutes < 60:
            return f"{minutes:.1f}m"
        hours = minutes / 60
        return f"{hours:.1f}h"
    
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
        self.summarizer = YouTubeSummarizer()
    
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
            time_gap = entry['start'] - last_timestamp if current_text else 0
            
            if time_gap > 2.0 and current_text:
                formatted_lines.append(f"• {' '.join(current_text)}")
                current_text = []
                timestamp = self.format_timestamp(entry['start'])
                current_text.append(f"[{timestamp}] {entry['text']}")
            else:
                current_text.append(entry['text'])
            
            last_timestamp = entry['start']
        
        if current_text:
            formatted_lines.append(f"• {' '.join(current_text)}")
        
        return "\n".join(formatted_lines)
    
    def chunk_transcript(self, transcript, chunk_duration=300):
        """Split transcript into chunks of specified duration (default 5 minutes)."""
        chunks = []
        current_chunk = []
        chunk_start = 0
        
        for entry in transcript:
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
    
    def format_transcript(self, transcript, video_title, video_url, duration):
        """Format the full transcript with metadata."""
        formatted_lines = [
            f"Title: {video_title}",
            f"URL: {video_url}",
            f"Duration: {self.format_timestamp(duration)}",
            "\nTranscript:",
            "=" * 50  # Separator line
        ]
        
        for chunk in self.chunk_transcript(transcript):
            formatted_lines.append(self.format_transcript_chunk(chunk))
        
        return "\n".join(formatted_lines)
    
    def run(self):
        """Main thread execution method."""
        if self.is_cancelled:
            return
            
        try:
            for url in self.urls:
                if self.is_cancelled:
                    break
                    
                try:
                    self.progress.emit(f"Getting transcript for {url}")
                    video_id = self.summarizer.get_video_id(url)
                    if not video_id:
                        self.progress.emit(f"❌ Error: Could not extract video ID from URL: {url}")
                        self.progress.emit("---")
                        continue
                    
                    # Get video title and transcript
                    video_title = self.summarizer.get_video_title(video_id)
                    self.progress.emit(f"Processing transcript for: {video_title}")
                    
                    transcript = self.summarizer.get_transcript(video_id)
                    if not transcript:
                        self.progress.emit(f"❌ Error: Could not get transcript for {url}")
                        self.progress.emit("---")
                        continue
                    
                    # Format the full transcript with metadata
                    formatted_transcript = self.format_transcript(
                        transcript,
                        video_title,
                        url,
                        transcript[-1]['start'] + transcript[-1]['duration']
                    )
                    
                    # Save transcript
                    sanitized_title = video_title.replace(" ", "_")
                    base_transcript_file = f"{sanitized_title}_transcript"
                    
                    if self.output_folder:
                        base_transcript_file = os.path.join(self.output_folder, os.path.basename(base_transcript_file))
                    
                    transcript_file = self.get_next_available_filename(base_transcript_file, ".txt")
                    
                    with open(transcript_file, 'w', encoding='utf-8') as f:
                        f.write(formatted_transcript)
                    
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
    
    def get_next_available_filename(self, base_filename, extension):
        """Get the next available filename by appending a number if needed."""
        counter = 1
        filename = f"{base_filename}{extension}"
        
        while os.path.exists(filename):
            filename = f"{base_filename}_{counter}{extension}"
            counter += 1
        
        return filename
    
    def cancel(self):
        """Mark the thread as cancelled to prevent further processing."""
        self.is_cancelled = True

class SummaryWorker(QThread):
    """Worker thread for generating summaries."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, urls, output_folder, depth, model):
        super().__init__()
        self.urls = urls
        self.output_folder = output_folder
        self.depth = depth
        self.model = model
        self.is_cancelled = False
        self.summarizer = YouTubeSummarizer()
    
    def run(self):
        """Main thread execution method."""
        if self.is_cancelled:
            return
        
        try:
            for url in self.urls:
                if self.is_cancelled:
                    break
                
                try:
                    self.progress.emit(f"Getting video information for {url}")
                    video_id = self.summarizer.get_video_id(url)
                    if not video_id:
                        self.progress.emit(f"❌ Error: Could not extract video ID from URL: {url}")
                        self.progress.emit("---")
                        continue
                    
                    # Get video title
                    video_title = self.summarizer.get_video_title(video_id)
                    self.progress.emit(f"Processing video: {video_title}")
                    
                    # Generate summary
                    self.progress.emit(f"🤖 Generating AI summary (Depth: {self.depth.value.capitalize()}, Model: {self.model})...")
                    summary = self.summarizer.summarize_video(url, self.depth, self.model)
                    
                    if summary:
                        # Add the title at the beginning of the summary
                        summary_with_title = f"# {video_title}\n\n{summary}"
                        
                        # Save summary
                        base_summary_file = f"{video_title} - summary"
                        summary_file = self.get_next_available_filename(base_summary_file, ".md", self.output_folder)
                        
                        with open(summary_file, 'w', encoding='utf-8') as f:
                            f.write(summary_with_title)
                        
                        self.progress.emit(f"✓ Summary saved to: {summary_file}")
                    else:
                        self.progress.emit(f"❌ Error: Could not generate summary for {url}")
                    
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
    
    def get_next_available_filename(self, base_filename, extension, output_dir=None):
        """Get the next available filename by appending a number if needed."""
        if output_dir:
            base_filename = os.path.join(output_dir, os.path.basename(base_filename))
        
        counter = 1
        filename = f"{base_filename}{extension}"
        
        while os.path.exists(filename):
            filename = f"{base_filename}_{counter}{extension}"
            counter += 1
        
        return filename
    
    def cancel(self):
        """Mark the thread as cancelled to prevent further processing."""
        self.is_cancelled = True 