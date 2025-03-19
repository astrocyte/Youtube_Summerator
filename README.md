# YouTube Summarator

A powerful tool for downloading YouTube videos, generating transcripts, and creating AI-powered summaries.

## Features

### GUI Interface
- Modern, user-friendly interface with Matrix and Dark themes
- Support for multiple video processing
- Drag and drop support:
  - Drag and drop individual YouTube URLs directly into the table
  - Drag and drop text files containing multiple URLs (one URL per line)
- Automatic video title fetching
- Configurable options:
  - Video format (mp4, mp3, m4a, webm, mkv)
  - Video quality (best, 1080p, 720p, 480p, 360p)
  - Summary depth (concise, balanced, detailed)
  - AI model selection (gpt-3.5-turbo, gpt-4)
- Progress tracking and status updates
- Persistent settings and preferences

### Core Features
- Download YouTube videos in various formats
- Generate accurate transcripts
- Create AI-powered summaries with different levels of detail
- Support for multiple videos in batch processing
- Configurable output formats and quality settings

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/youtube_summarator.git
cd youtube_summarator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package in development mode:
```bash
pip install -e .
```

## Usage

### GUI Mode
Run the application with a graphical interface:
```bash
python run_gui.py
```

Features:
- Start with 5 empty rows for URLs by default
- Add or remove rows as needed
- Paste URLs directly into cells
- Drag and drop URLs or text files
- Select output folder and processing options
- Monitor progress in real-time

### Command Line Mode
Run the application from the command line:
```bash
python -m ytsummarator --url "https://www.youtube.com/watch?v=VIDEO_ID" --depth detailed
```

Options:
- `--url`: YouTube video URL
- `--depth`: Summary depth (concise, balanced, detailed)
- `--model`: AI model to use (gpt-3.5-turbo, gpt-4)
- `--config`: Path to configuration file

## Configuration

The application stores user preferences in `~/.youtube_extractor_config.json`, including:
- Last used output folder
- Preferred video format and quality
- Summary depth and model settings
- Window size and position
- Theme preference

## Development

### Project Structure
```
ytsummarator/
├── core/           # Core functionality
├── gui/            # GUI components
├── models/         # Data models
├── config/         # Configuration
├── services/       # External services
└── utils/          # Utility functions
```

### Building the Application
To create a standalone executable:
```bash
# For macOS
./ytsummarator/scripts/build_mac_app.sh

# For other platforms
./ytsummarator/scripts/build_app.sh
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 