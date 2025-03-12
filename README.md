# YouTube Video Downloader

A robust and feature-rich YouTube video downloader with support for various formats, qualities, and authentication methods.

## Features

- Download videos in multiple formats (mp4, webm, mkv, mp3, m4a)
- Multiple quality options (up to 4K)
- Batch download support from URL file
- Browser cookie integration for premium content
- Progress bar visualization
- Comprehensive logging system
- Automatic retry mechanism with exponential backoff
- Support for age-restricted and premium videos (with authentication)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd youtube-downloader
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Download a single video:
```bash
python youtube_downloader.py <youtube-url>
```

Download with specific format and quality:
```bash
python youtube_downloader.py <youtube-url> mp4 1080p
```

### Batch Download

Create a text file (e.g., `urls.txt`) with YouTube URLs (one per line):
```
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
```

Then run:
```bash
python youtube_downloader.py urls.txt
```

### Available Formats
- mp4 (default)
- webm
- mkv
- mp3 (audio only)
- m4a (audio only)

### Available Qualities
- best (default)
- 2160p (4K)
- 1440p
- 1080p
- 720p
- 480p
- 360p
- 240p
- 144p

## Configuration

The script can be configured using environment variables. Create a `.env` file with any of these settings:

```env
OUTPUT_DIR=Downloaded_Videos
DEFAULT_FORMAT=mp4
DEFAULT_QUALITY=best
COOKIES_FILE=youtube_cookies.txt
COOKIE_CACHE_FILE=.youtube_cookie_cache.json
COOKIE_CACHE_DURATION=3600
DEBUG_MODE=false
MAX_RETRIES=3
LOG_DIR=logs
USER_AGENT=Mozilla/5.0 ...
```

## Authentication

For premium content or age-restricted videos, the script will automatically try to use cookies from your browser. Supported browsers:
- Chrome
- Firefox

If automatic cookie extraction fails, you can manually export cookies using the Cookie-Editor browser extension:

1. Install the "Cookie-Editor" extension
2. Go to youtube.com and log in
3. Click the Cookie-Editor extension icon
4. Click "Export" -> "Export as Netscape HTTP Cookie File"
5. Save as `youtube_cookies.txt` in the script directory

## Logging

Logs are stored in the `logs` directory:
- `youtube_downloader_YYYYMMDD.log`: General logs
- `youtube_downloader_errors_YYYYMMDD.log`: Error logs only

Enable debug mode for verbose logging:
```bash
DEBUG_MODE=true python youtube_downloader.py <youtube-url>
```

## Error Handling

The script includes comprehensive error handling for:
- Network issues
- Authentication problems
- Age restrictions
- Region restrictions
- SSL certificate issues
- Video availability
- Format/quality issues

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for personal use only. Please respect YouTube's terms of service and content creators' rights. 