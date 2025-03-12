#!/usr/bin/env python3
import os
import sys
import re
import yt_dlp
import logging
import time
from pathlib import Path
from typing import Dict, Union
from dotenv import load_dotenv
from tqdm import tqdm
import logging.config
from datetime import datetime

def parse_env_int(key: str, default: int) -> int:
    """Safely parse an integer from environment variable."""
    try:
        value = os.getenv(key)
        return int(value) if value is not None else default
    except ValueError as e:
        logger.warning(f"Invalid value for {key}, using default {default}: {e}")
        return default

def parse_env_bool(key: str, default: bool = False) -> bool:
    """Safely parse a boolean from environment variable."""
    value = os.getenv(key, '').lower()
    if value in ('true', '1', 'yes'):
        return True
    if value in ('false', '0', 'no'):
        return False
    return default

# Load environment variables
load_dotenv()

# Create output directory
OUTPUT_DIR = os.getenv('OUTPUT_DIR', "Downloaded_Videos")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuration from environment variables with defaults
DEBUG_MODE = parse_env_bool('DEBUG_MODE', False)
DEFAULT_FORMAT = os.getenv('DEFAULT_FORMAT', "mp4")
DEFAULT_QUALITY = os.getenv('DEFAULT_QUALITY', "best")
MAX_RETRIES = parse_env_int('MAX_RETRIES', 3)

# Logging configuration
LOG_DIR = os.getenv('LOG_DIR', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': os.path.join(LOG_DIR, f'youtube_downloader_{datetime.now().strftime("%Y%m%d")}.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': os.path.join(LOG_DIR, f'youtube_downloader_errors_{datetime.now().strftime("%Y%m%d")}.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG' if DEBUG_MODE else 'INFO',
            'propagate': True
        }
    }
}

# Apply logging configuration
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Global progress bar for tracking downloads
current_download_progress = None

class YouTubeDownloaderError(Exception):
    """Base exception class for YouTube downloader errors."""
    pass

class VideoUnavailableError(YouTubeDownloaderError):
    """Raised when a video is unavailable (private, deleted, etc.)."""
    pass

def handle_progress(d: Dict[str, Union[str, float, int]]) -> None:
    """Handle progress updates from yt-dlp with tqdm progress bar."""
    global current_download_progress
    
    if d['status'] == 'downloading':
        if '_total_bytes_str' in d:
            total = d.get('total_bytes', 0)
            downloaded = d.get('downloaded_bytes', 0)
            total_str = d.get('_total_bytes_str', '0 MiB')
            downloaded_str = d.get('_downloaded_bytes_str', '0 MiB')
            percent = d.get('_percent_str', '0%').strip()
            speed_str = d.get('_speed_str', '0 KiB/s')
            eta_str = d.get('_eta_str', 'N/A')
            
            # Log detailed progress information for the GUI to parse
            logger.info(f"Downloading: {percent} | {downloaded_str}/{total_str} | Speed: {speed_str} | ETA: {eta_str}")
            
            if not current_download_progress:
                current_download_progress = tqdm(
                    total=total,
                    unit='B',
                    unit_scale=True,
                    desc=f"Downloading {d.get('filename', '')}",
                    ncols=80
                )
            
            # Update progress
            if downloaded:
                current_download_progress.update(downloaded - current_download_progress.n)
                
            # Add download speed and ETA to progress bar description
            speed = d.get('speed', 0)
            if speed:
                current_download_progress.set_postfix(
                    speed=f"{speed/1024/1024:.1f}MB/s",
                    eta=d.get('_eta_str', 'N/A')
                )
    
    elif d['status'] == 'finished' and current_download_progress:
        current_download_progress.close()
        current_download_progress = None
        logger.info(f"Download completed: {d.get('filename', '')}")

def get_format_spec(output_format: str, quality: str) -> str:
    """Generate the format specification string based on format and quality."""
    if output_format in ["mp3", "m4a"]:
        return f'bestaudio[ext={output_format}]/bestaudio/best'
    
    # Handle video formats with specific quality
    if quality == "best":
        return f'bestvideo[ext={output_format}]+bestaudio/best[ext={output_format}]/best'
    else:
        # Remove 'p' from quality string and convert to integer
        target_height = int(quality.rstrip('p'))
        return f'bestvideo[height<={target_height}][ext={output_format}]+bestaudio/best[height<={target_height}][ext={output_format}]/best'

def extract_video_id(url: str) -> str:
    """Extract the video ID from a YouTube URL."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/|/embed/)([^&?\n]+)',
        r'(?:shorts/)([^&?\n]+)',  # Pattern for YouTube Shorts
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def is_url(text: str) -> bool:
    """Check if the input is a URL."""
    url_pattern = r'https?://(?:www\.)?(?:youtube\.com|youtu\.be)/.+'
    return bool(re.match(url_pattern, text))

def download_video(video_url: str, output_format: str = DEFAULT_FORMAT, quality: str = DEFAULT_QUALITY, output_folder: str = None) -> None:
    """Download a YouTube video."""
    global current_download_progress
    
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {video_url}")

        logger.info(f"Downloading video: {video_url}")
        
        # Get format specification
        format_spec = get_format_spec(output_format, quality)
        if DEBUG_MODE:
            logger.debug(f"Using format specification: {format_spec}")
        
        # Use provided output folder or default
        output_dir = output_folder if output_folder else OUTPUT_DIR
        
        # First extract video info to get the title
        info_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(info_opts) as ydl_info:
            info = ydl_info.extract_info(video_url, download=False)
            video_title = info.get('title', 'Unknown_Title')
            
            # Sanitize title (replace spaces with underscores)
            sanitized_title = video_title.replace(' ', '_')
            
            # Create a custom output template with incrementing
            def get_next_available_filename(base_name, extension):
                """Get the next available filename with incrementing number if file exists."""
                counter = 0
                while True:
                    if counter == 0:
                        filename = f"{base_name}{extension}"
                    else:
                        filename = f"{base_name}_{counter}{extension}"
                    
                    if not os.path.exists(os.path.join(output_dir, filename)):
                        return filename
                    counter += 1
            
            # Get the output filename with proper extension
            output_filename = get_next_available_filename(sanitized_title, f".{output_format}")
            output_path = os.path.join(output_dir, output_filename)
            
            logger.info(f"Will save video as: {output_path}")
        
        # Configure yt-dlp to use our custom filename
        ydl_opts = {
            'format': format_spec,
            'outtmpl': output_path,
            'restrictfilenames': True,
            'noplaylist': True,
            'ignoreerrors': False,
            'quiet': not DEBUG_MODE,
            'no_warnings': False,
            'extract_flat': False,
            'progress_hooks': [lambda d: handle_progress(d)],
            'retries': MAX_RETRIES,
            'fragment_retries': MAX_RETRIES,
            'file_access_retries': MAX_RETRIES,
            'extractor_retries': MAX_RETRIES,
            'retry_sleep_functions': {'http': lambda n: 1 + n * 2},  # Exponential backoff
            'max_sleep_interval': 60,  # Maximum sleep time between retries
            'socket_timeout': 30,
            'concurrent_fragment_downloads': 3,  # Reduced parallel downloads to avoid throttling
            'merge_output_format': output_format,
            # YouTube specific options
            'youtube_include_dash_manifest': True,  # Include DASH manifests
            'prefer_insecure': False,  # Use HTTPS
            'source_address': '0.0.0.0',  # Use all available interfaces
            'sleep_interval': 2,  # Add delay between requests
            'max_sleep_interval': 5,
            'sleep_interval_requests': 3,  # Number of requests between sleeps
            'http_chunk_size': 10485760,  # 10MB chunks for better stability
            # Format selection improvements
            'format_sort': [
                'res:1080',
                'ext:mp4:m4a',
                'codec:h264:aac',
                'size',
                'br',
                'fps',
                'asr'
            ],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': output_format,
            }] if output_format not in ['mp4', 'webm'] else [],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Download the video
                ydl.download([video_url])
                logger.info(f"Successfully downloaded video to {output_path}")
                
            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e).lower()
                
                if "video unavailable" in error_msg:
                    raise VideoUnavailableError("This video is unavailable (it might be private or deleted)")
                elif "sign in" in error_msg or "login" in error_msg:
                    print("\nThis video requires authentication.")
                    print("Try one of these options:")
                    print("1. Make sure the video is public and accessible")
                    print("2. For age-restricted videos, try using a different video")
                    raise YouTubeDownloaderError("Video requires authentication")
                elif "throttle" in error_msg or "429" in error_msg:
                    print("\nYouTube is throttling our requests.")
                    print("Waiting 30 seconds before retrying...")
                    time.sleep(30)
                    # Retry with more conservative settings
                    ydl_opts.update({
                        'concurrent_fragment_downloads': 1,
                        'sleep_interval': 5,
                        'sleep_interval_requests': 1
                    })
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl_retry:
                        ydl_retry.download([video_url])
                    logger.info(f"Successfully downloaded video after throttling retry")
                else:
                    raise YouTubeDownloaderError(f"Download failed: {str(e)}")
                    
    except YouTubeDownloaderError:
        raise
    except Exception as e:
        logger.error(f"Error downloading video {video_url}: {str(e)}")
        if DEBUG_MODE:
            import traceback
            logger.debug(f"Full error traceback:\n{traceback.format_exc()}")
        raise YouTubeDownloaderError(f"Failed to download video: {str(e)}")
    finally:
        if current_download_progress:
            current_download_progress.close()
            current_download_progress = None

def process_url_file(file_path: str, output_format: str = DEFAULT_FORMAT, quality: str = DEFAULT_QUALITY) -> None:
    """Process a file containing YouTube URLs, one per line."""
    try:
        with open(file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and is_url(line.strip())]
        
        if not urls:
            print(f"No valid YouTube URLs found in {file_path}")
            return
        
        print(f"Found {len(urls)} URLs to process")
        for i, url in enumerate(urls, 1):
            print(f"\nProcessing URL {i}/{len(urls)}")
            print(f"URL: {url}")
            print("-" * 50)
            try:
                download_video(url, output_format, quality)
            except YouTubeDownloaderError as e:
                print(f"Error downloading {url}: {str(e)}")
                print("Continuing with next video...")
            print("-" * 50)
    
    except Exception as e:
        print(f"Error processing URL file: {str(e)}")

def main():
    """Main function to handle command line arguments."""
    # Define available formats and qualities
    available_formats = ["mp4", "webm", "mkv", "mp3", "m4a"]
    available_qualities = ["best", "1080p", "720p", "480p", "360p", "240p", "144p"]
    
    # Default values
    output_format = DEFAULT_FORMAT
    quality = DEFAULT_QUALITY
    default_url_file = "urls.txt"
    
    # Check for debug flag
    if "--debug" in sys.argv:
        sys.argv.remove("--debug")
        global DEBUG_MODE
        DEBUG_MODE = True
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        if os.path.exists(default_url_file):
            print(f"No arguments provided. Using default URL file: {default_url_file}")
            input_path = default_url_file
        else:
            print("Usage:")
            print("  For single video: python youtube_downloader.py <youtube_url> [format] [quality]")
            print("  For multiple videos: python youtube_downloader.py <path_to_url_file.txt> [format] [quality]")
            print(f"  Available formats: {', '.join(available_formats)}")
            print(f"  Available qualities: {', '.join(available_qualities)}")
            print(f"  Default format: {DEFAULT_FORMAT}, Default quality: {DEFAULT_QUALITY}")
            sys.exit(1)
    else:
        input_path = sys.argv[1]
    
    # Check for format and quality arguments
    if len(sys.argv) >= 3 and sys.argv[2] in available_formats:
        output_format = sys.argv[2]
    
    if len(sys.argv) >= 4 and sys.argv[3] in available_qualities:
        quality = sys.argv[3]
    
    print(f"Using format: {output_format}, quality: {quality}")
    
    # Check if input is a URL or a file
    if is_url(input_path):
        try:
            download_video(input_path, output_format, quality)
        except YouTubeDownloaderError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    else:
        if not os.path.exists(input_path):
            print(f"Error: File '{input_path}' not found")
            sys.exit(1)
        process_url_file(input_path, output_format, quality)

if __name__ == "__main__":
    main() 