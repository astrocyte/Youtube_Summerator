# YouTube Video Downloader

A simple Python script to download YouTube videos from a single URL or a list of URLs.

## Features

- Download videos from a single YouTube URL or a list of URLs in a text file
- Specify video format (mp4, webm, mkv, mp3, m4a)
- Choose video quality (best, 1080p, 720p, 480p, 360p, 240p, 144p)
- Progress tracking during downloads
- Automatic file naming based on video titles
- Smart handling of audio-only formats

## Requirements

- Python 3.6 or higher
- Required Python packages (install using `pip install -r requirements.txt`):
  - yt-dlp
  - python-dotenv

## Installation

1. Make sure you have Python 3.6+ installed
2. Clone this repository or download the script
3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

### Downloading a Single Video

```bash
python youtube_downloader.py <youtube_url> [format] [quality]
```

Example:
```bash
python youtube_downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ mp4 1080p
```

### Downloading Multiple Videos from a File

Create a text file with one YouTube URL per line, then run:

```bash
python youtube_downloader.py <path_to_url_file.txt> [format] [quality]
```

Example:
```bash
python youtube_downloader.py urls.txt mp4 720p
```

### Available Formats

- mp4 (default)
- webm
- mkv
- mp3 (audio only)
- m4a (audio only)

### Available Qualities

- best (default) - Always selects the highest quality available
- 1080p
- 720p
- 480p
- 360p
- 240p
- 144p

If no quality is specified, the script will automatically use "best" quality.

## Output

Downloaded videos will be saved to the `Downloaded_Videos` directory in the same location as the script. The files will be named according to the video titles.

## Notes

- The script uses the yt-dlp library, which is a fork of youtube-dl with additional features and regular updates
- If the specified format or quality is not available, the script will fall back to the best available option
- For audio-only formats (mp3, m4a):
  - The quality parameter will be ignored
  - The script will automatically use the best audio quality available
  - Audio will be converted to the specified format with 192kbps quality

## Troubleshooting

If you encounter any issues:

1. Make sure you have the latest version of yt-dlp installed:
   ```bash
   pip install -U yt-dlp
   ```

2. For audio formats, you may need FFmpeg installed:
   - On macOS: `brew install ffmpeg`
   - On Ubuntu/Debian: `sudo apt install ffmpeg`
   - On Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

3. Check that the YouTube URL is valid and accessible
4. Ensure you have sufficient disk space for the downloads
5. If downloading fails, try a different format or quality 