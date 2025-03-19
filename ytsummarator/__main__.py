"""Main entry point for the YouTube Summarator package."""
import argparse
from .core.summarizer import YouTubeSummarizer
from .models.summary_depth import SummaryDepth
from .config.settings import Config
from .gui.main_window import YouTubeDownloaderGUI
from PyQt6.QtWidgets import QApplication
import sys

def cli_main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Summarize YouTube videos")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--depth",
        choices=[d.value for d in SummaryDepth],
        default=SummaryDepth.DETAILED.value,
        help="Summary depth level"
    )
    parser.add_argument(
        "--model",
        default="gpt-3.5-turbo",
        help="OpenAI model to use"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config) if args.config else Config()
    
    # Create summarizer
    summarizer = YouTubeSummarizer(config)
    
    # Generate summary
    summary = summarizer.summarize_video(
        args.url,
        SummaryDepth(args.depth),
        args.model
    )
    
    # Save summary
    video_id = summarizer.get_video_id(args.url)
    summarizer.save_summary(summary, video_id, SummaryDepth(args.depth), args.model)

def gui_main():
    """Main entry point for the GUI."""
    app = QApplication(sys.argv)
    window = YouTubeDownloaderGUI()
    window.show()
    sys.exit(app.exec())

def main():
    """Main entry point that handles both CLI and GUI modes."""
    parser = argparse.ArgumentParser(description="YouTube Summarator")
    parser.add_argument("--gui", action="store_true", help="Run in GUI mode")
    args, remaining_args = parser.parse_known_args()
    
    if args.gui:
        gui_main()
    else:
        sys.argv = [sys.argv[0]] + remaining_args
        cli_main()

if __name__ == "__main__":
    main() 