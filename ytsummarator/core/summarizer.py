"""Core YouTube video summarization functionality."""
import os
from typing import List, Dict, Optional
import openai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from ..models.summary_depth import SummaryDepth
from ..config.settings import Config
from ..services.cache import Cache
from ..utils.progress import ProgressTracker
from ..utils.error import retry_with_backoff

class YouTubeSummarizer:
    """Main class for YouTube video summarization."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the summarizer with configuration."""
        self.config = config or Config()
        self.cache = Cache()
        self.formatter = TextFormatter()
        
        # Set OpenAI API key
        openai.api_key = self.config.get("openai_api_key")
    
    def get_video_id(self, url: str) -> str:
        """Extract video ID from URL."""
        if "youtu.be" in url:
            return url.split("/")[-1]
        elif "youtube.com" in url:
            return url.split("v=")[1].split("&")[0]
        return url
    
    def get_transcript(self, video_id: str) -> List[Dict]:
        """Get video transcript with caching."""
        # Check cache first
        if self.cache.has_transcript(video_id):
            return self.cache.get_transcript(video_id)
        
        # Get transcript from YouTube
        transcript = retry_with_backoff(
            lambda: YouTubeTranscriptApi.get_transcript(video_id),
            max_retries=self.config.get("max_retries"),
            base_delay=self.config.get("base_delay")
        )
        
        # Cache transcript
        self.cache.cache_transcript(video_id, transcript)
        return transcript
    
    def chunk_transcript(self, transcript: List[Dict]) -> List[str]:
        """Split transcript into chunks."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for segment in transcript:
            segment_text = segment["text"]
            segment_length = len(segment_text.split())
            
            if current_length + segment_length > self.config.get("chunk_size"):
                chunks.append(" ".join(current_chunk))
                current_chunk = [segment_text]
                current_length = segment_length
            else:
                current_chunk.append(segment_text)
                current_length += segment_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def get_summary_prompt(self, chunk: str, depth: SummaryDepth) -> str:
        """Get appropriate prompt based on summary depth."""
        prompts = {
            SummaryDepth.BASIC: self.config.get("basic_prompt"),
            SummaryDepth.DETAILED: self.config.get("detailed_prompt"),
            SummaryDepth.TECHNICAL: self.config.get("technical_prompt")
        }
        return prompts[depth].format(text=chunk)
    
    def summarize_chunk(
        self,
        chunk: str,
        depth: SummaryDepth,
        model: str
    ) -> str:
        """Summarize a single chunk of text."""
        prompt = self.get_summary_prompt(chunk, depth)
        
        response = retry_with_backoff(
            lambda: openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.get("temperature"),
                max_tokens=self.config.get("max_tokens")
            ),
            max_retries=self.config.get("max_retries"),
            base_delay=self.config.get("base_delay")
        )
        
        return response.choices[0].message.content.strip()
    
    def summarize_video(
        self,
        url: str,
        depth: SummaryDepth = SummaryDepth.DETAILED,
        model: str = "gpt-3.5-turbo"
    ) -> str:
        """Generate summary for a YouTube video."""
        video_id = self.get_video_id(url)
        
        # Check cache for existing summary
        if self.cache.has_summary(video_id, depth.value, model):
            return self.cache.get_summary(video_id, depth.value, model)
        
        # Get and chunk transcript
        transcript = self.get_transcript(video_id)
        chunks = self.chunk_transcript(transcript)
        
        # Initialize progress tracker
        progress = ProgressTracker(len(chunks))
        
        # Generate summaries for each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            summary = self.summarize_chunk(chunk, depth, model)
            chunk_summaries.append(summary)
            progress.update(i, len(chunk.split()))
        
        # Combine summaries
        final_summary = "\n\n".join(chunk_summaries)
        progress.complete()
        
        # Cache the summary
        self.cache.cache_summary(video_id, depth.value, model, final_summary)
        
        return final_summary
    
    def save_summary(
        self,
        summary: str,
        video_id: str,
        depth: SummaryDepth,
        model: str
    ):
        """Save summary to file."""
        output_dir = self.config.get("output_dir")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{video_id}_{depth.value}_{model}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(summary)
        
        print(f"\nSummary saved to: {filepath}") 