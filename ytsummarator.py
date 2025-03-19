from youtube_transcript_api import YouTubeTranscriptApi
import sys
import re
import os
from openai import OpenAI
from dotenv import load_dotenv
import yt_dlp
import tiktoken
import json
from typing import List, Dict
import time
from enum import Enum
import traceback

# Load environment variables
load_dotenv()

# Create output directory
OUTPUT_DIR = "Summarator_Output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class SummaryDepth(Enum):
    BASIC = "basic"
    DETAILED = "detailed"
    TECHNICAL = "technical"

class ProgressTracker:
    """Track and display progress of summary generation."""
    def __init__(self, total_chunks: int):
        self.total_chunks = total_chunks
        self.current_chunk = 0
        self.start_time = time.time()
        self.chunk_times = []
    
    def update(self, chunk_index: int, chunk_size: int):
        """Update progress and display status."""
        self.current_chunk = chunk_index + 1
        chunk_time = time.time() - self.start_time
        self.chunk_times.append(chunk_time)
        
        # Calculate progress
        progress = (self.current_chunk / self.total_chunks) * 100
        avg_time = sum(self.chunk_times) / len(self.chunk_times)
        remaining_chunks = self.total_chunks - self.current_chunk
        estimated_time = remaining_chunks * avg_time
        
        # Display progress
        print(f"\rProgress: {progress:.1f}% ({self.current_chunk}/{self.total_chunks}) "
              f"| Estimated time remaining: {estimated_time:.1f}s | "
              f"Current chunk size: {chunk_size} tokens", end="")
    
    def complete(self):
        """Display completion message with statistics."""
        total_time = time.time() - self.start_time
        avg_chunk_time = sum(self.chunk_times) / len(self.chunk_times)
        print(f"\n\nSummary generation completed in {total_time:.1f}s")
        print(f"Average time per chunk: {avg_chunk_time:.1f}s")
        print(f"Total chunks processed: {self.total_chunks}")

class Config:
    """Configuration management for the summarizer."""
    def __init__(self):
        self.config_file = "summarizer_config.json"
        self.default_config = {
            "output_dir": "Summarator_Output",
            "max_retries": 4,
            "base_delay": 10,
            "adaptive_delay_min": 5,
            "adaptive_delay_max": 20,
            "chunk_overlap_ratio": 0.1,
            "chunk_size_ratio": 0.4,
            "reserved_tokens": 1000,
            "default_model": "gpt-3.5-turbo-16k",
            "default_depth": "detailed",
            "max_tokens_per_chunk": 2000,
            "max_tokens_final": 1500,
            "temperature": 0.5,
            "timeout": 60,
            "error_logging": True,
            "progress_tracking": True
        }
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Load configuration from file or create default."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**self.default_config, **config}
            return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {str(e)}")
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value and save."""
        self.config[key] = value
        self.save_config()

class Cache:
    """Cache management for transcripts and summaries."""
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.transcript_dir = os.path.join(cache_dir, "transcripts")
        self.summary_dir = os.path.join(cache_dir, "summaries")
        self.metadata_file = os.path.join(cache_dir, "cache_metadata.json")
        os.makedirs(self.transcript_dir, exist_ok=True)
        os.makedirs(self.summary_dir, exist_ok=True)
        self.metadata = self.load_metadata()
    
    def load_metadata(self) -> dict:
        """Load cache metadata."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_metadata(self):
        """Save cache metadata."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=4)
    
    def get_transcript_path(self, video_id: str) -> str:
        """Get the path for a cached transcript."""
        return os.path.join(self.transcript_dir, f"{video_id}.json")
    
    def get_summary_path(self, video_id: str, depth: str, model: str) -> str:
        """Get the path for a cached summary."""
        return os.path.join(self.summary_dir, f"{video_id}_{depth}_{model}.md")
    
    def has_transcript(self, video_id: str) -> bool:
        """Check if transcript is cached."""
        return os.path.exists(self.get_transcript_path(video_id))
    
    def has_summary(self, video_id: str, depth: str, model: str) -> bool:
        """Check if summary is cached."""
        return os.path.exists(self.get_summary_path(video_id, depth, model))
    
    def get_transcript(self, video_id: str) -> List[Dict]:
        """Get cached transcript."""
        if self.has_transcript(video_id):
            with open(self.get_transcript_path(video_id), 'r') as f:
                return json.load(f)
        return None
    
    def get_summary(self, video_id: str, depth: str, model: str) -> str:
        """Get cached summary."""
        if self.has_summary(video_id, depth, model):
            with open(self.get_summary_path(video_id, depth, model), 'r') as f:
                return f.read()
        return None
    
    def cache_transcript(self, video_id: str, transcript: List[Dict]):
        """Cache transcript."""
        with open(self.get_transcript_path(video_id), 'w') as f:
            json.dump(transcript, f)
        self.metadata[f"transcript_{video_id}"] = {
            "timestamp": time.time(),
            "size": len(str(transcript))
        }
        self.save_metadata()
    
    def cache_summary(self, video_id: str, depth: str, model: str, summary: str):
        """Cache summary."""
        with open(self.get_summary_path(video_id, depth, model), 'w') as f:
            f.write(summary)
        self.metadata[f"summary_{video_id}_{depth}_{model}"] = {
            "timestamp": time.time(),
            "size": len(summary)
        }
        self.save_metadata()
    
    def cleanup(self, max_age_days: int = 30):
        """Clean up old cache entries."""
        current_time = time.time()
        max_age = max_age_days * 24 * 60 * 60  # Convert days to seconds
        
        for key, data in list(self.metadata.items()):
            if current_time - data["timestamp"] > max_age:
                if key.startswith("transcript_"):
                    video_id = key.split("_")[1]
                    os.remove(self.get_transcript_path(video_id))
                elif key.startswith("summary_"):
                    _, video_id, depth, model = key.split("_")
                    os.remove(self.get_summary_path(video_id, depth, model))
                del self.metadata[key]
        
        self.save_metadata()

# Initialize global configuration
config = Config()

# Initialize global cache
cache = Cache()

def num_tokens_from_string(string: str, model: str = "gpt-4") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def get_model_context_window(model: str) -> int:
    """Get the context window size for a specific model."""
    context_windows = {
        "gpt-4-turbo": 128000,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16385,
    }
    return context_windows.get(model, 4096)  # Default to 4K if model unknown

def get_chunk_parameters(model: str) -> tuple[int, int]:
    """Get appropriate chunk and overlap sizes for a model."""
    context_window = get_model_context_window(model)
    
    # Get configuration values
    reserved_tokens = config.get("reserved_tokens", 1000)
    chunk_size_ratio = config.get("chunk_size_ratio", 0.4)
    chunk_overlap_ratio = config.get("chunk_overlap_ratio", 0.1)
    
    # Calculate maximum chunk size (leave room for overlap)
    max_chunk_tokens = min(
        context_window - reserved_tokens,
        int(context_window * chunk_size_ratio)
    )
    
    # Calculate overlap
    overlap_tokens = int(max_chunk_tokens * chunk_overlap_ratio)
    
    return max_chunk_tokens, overlap_tokens

def chunk_transcript(text: str, model: str = "gpt-4", max_tokens: int = None, overlap_tokens: int = None) -> List[Dict[str, str]]:
    """Split transcript into chunks using tiktoken's tokenizer with improved semantic chunking."""
    encoding = tiktoken.encoding_for_model(model)
    
    # Get appropriate chunk parameters if not provided
    if max_tokens is None or overlap_tokens is None:
        max_tokens, overlap_tokens = get_chunk_parameters(model)
    
    # First split into sentences for better semantic chunking
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for sentence in sentences:
        # Get token count for this sentence
        sentence_tokens = encoding.encode(sentence)
        sentence_token_count = len(sentence_tokens)
        
        # If adding this sentence would exceed the limit, save current chunk
        if current_tokens + sentence_token_count > max_tokens and current_chunk:
            # Join the current chunk
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'token_count': current_tokens
            })
            
            # Start new chunk with overlap
            # Find sentences that fit within overlap_tokens
            overlap_text = ''
            overlap_tokens_count = 0
            for prev_sentence in reversed(current_chunk):
                prev_tokens = len(encoding.encode(prev_sentence))
                if overlap_tokens_count + prev_tokens <= overlap_tokens:
                    overlap_text = prev_sentence + ' ' + overlap_text
                    overlap_tokens_count += prev_tokens
                else:
                    break
            
            current_chunk = overlap_text.strip().split()
            current_tokens = overlap_tokens_count
        
        current_chunk.append(sentence)
        current_tokens += sentence_token_count
    
    # Add the last chunk if it exists
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunks.append({
            'text': chunk_text,
            'token_count': current_tokens
        })
    
    return chunks

def sanitize_filename(title):
    """Convert title to a valid filename."""
    # Remove invalid filename characters
    invalid_chars = r'<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '')
    # Limit length and strip whitespace
    return title.strip()[:100]

def get_video_title(video_id):
    """Get the title of a YouTube video."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return sanitize_filename(info.get('title', video_id))
    except Exception as e:
        print(f"Warning: Could not fetch video title: {str(e)}")
        return video_id

def extract_video_id(url):
    """Extract the video ID from a YouTube URL."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/|/embed/)([^&?\n]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_next_available_filename(base_filename: str, extension: str, output_dir: str = None) -> str:
    """Get the next available filename by adding a version number if the file exists."""
    # Use provided output directory or default
    target_dir = output_dir if output_dir else OUTPUT_DIR
    
    # Ensure base_filename is within the target directory
    base_filepath = os.path.join(target_dir, base_filename)
    
    if not os.path.exists(f"{base_filepath}{extension}"):
        return f"{base_filepath}{extension}"
    
    counter = 1
    while os.path.exists(f"{base_filepath} ({counter}){extension}"):
        counter += 1
    
    return f"{base_filepath} ({counter}){extension}"

def generate_chunk_summary(chunk: str, chunk_index: int, total_chunks: int, client: OpenAI, depth: SummaryDepth = SummaryDepth.DETAILED, model: str = None) -> str:
    """Generate a summary for a single chunk of the transcript with configurable depth."""
    try:
        # Use configured model if none provided
        model = model or config.get("default_model", "gpt-4")
        
        # Get configuration values
        max_tokens = config.get("max_tokens_per_chunk", 2000)
        temperature = config.get("temperature", 0.5)
        timeout = config.get("timeout", 60)
        
        # Base prompt structure
        base_prompt = {
            SummaryDepth.BASIC: """Create a concise summary of this video section focusing on the main points and key takeaways.

## Main Points
- List the key ideas or arguments (3-4 bullet points)
- Focus on the core message or purpose

## Key Takeaways
- List practical insights or lessons (2-3 bullet points)
- Include any actionable advice or recommendations
""",
            SummaryDepth.DETAILED: """Create a detailed summary of this video section, capturing both content and context.

## Main Topics
- List key themes or subjects discussed (2-4 bullet points)
- Include any relevant background or context

## Content Breakdown
- Break down the main content points (4-6 bullet points)
- Include specific examples or demonstrations
- Note any visual elements or demonstrations
- Document any step-by-step processes

## Important Details
- List specific references:
  * Names, dates, or statistics mentioned
  * Tools, resources, or materials referenced
  * External sources or citations
  * Related topics or concepts

## Notable Points
- Include significant explanations or insights
- Document any tips or advice given
- Note any audience engagement elements
""",
            SummaryDepth.TECHNICAL: """Create a comprehensive technical summary of this video section.

## Technical Overview
- List main technical concepts (2-3 bullet points)
- Identify key technologies or tools
- Note system or process architecture

## Technical Details
- Document specifications:
  * Technologies and frameworks
  * Requirements and dependencies
  * Performance considerations
  * Security implications

## Implementation Steps
- Break down technical processes:
  * Step-by-step instructions
  * Code examples or configurations
  * Best practices and guidelines
  * Common pitfalls to avoid

## Technical Resources
- List mentioned:
  * Tools and software
  * Documentation references
  * Learning resources
  * Community resources
"""
        }

        # Select prompt based on depth
        selected_prompt = base_prompt[depth]
        
        # Add context for multi-chunk summaries
        if total_chunks > 1:
            context = "beginning of" if chunk_index == 0 else "middle of" if chunk_index < total_chunks - 1 else "end of"
            selected_prompt = f"This is part {chunk_index + 1} of {total_chunks} (the {context} the video).\n\n{selected_prompt}"

        # Complete prompt
        prompt = f"{selected_prompt}\n\nTranscript portion:\n{chunk}"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a technical documentation expert who creates detailed, well-structured technical summaries. Focus on technical details, implementation specifics, and actionable information while maintaining clarity and precision."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating chunk summary: {str(e)}")
        return ""

def generate_final_summary(intermediate_summaries: List[str], client: OpenAI, depth: SummaryDepth, model: str = "gpt-4") -> str:
    """Generate a final summary from all intermediate summaries."""
    try:
        combined_points = "\n\n".join(intermediate_summaries)
        
        prompt = f"""Based on the following collection of key points from different parts of the video, 
create a cohesive final summary that captures all key elements while maintaining clarity:

## Video Overview
- Summarize the main purpose and context
- Identify the target audience
- Note any prerequisites or background needed

## Key Content
- Break down the main points (4-6 bullet points)
- Include specific examples and demonstrations
- Highlight any step-by-step processes
- Note any visual elements or demonstrations

## Important Details
- List specific references:
  * Names, dates, or statistics
  * Tools, resources, or materials
  * External sources or citations
  * Related topics or concepts

## Notable Quotes
- Include significant quotes that:
  * Provide key insights
  * Explain important concepts
  * Share personal experiences
- Always attribute quotes to speakers

## Additional Elements
- Note any:
  * Calls to action
  * Community engagement aspects
  * Related videos or resources
  * Timestamps for key moments

Key points from transcript:
{combined_points}"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional content analyst. Create a cohesive final summary that captures specific details and references while maintaining clarity and actionability. Focus on information that would be most useful to someone wanting to understand or apply the content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.get("max_tokens_final", 1500),
            temperature=0.7,
            timeout=60
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating final summary: {str(e)}")
        return None

def generate_summary(text: str, depth: SummaryDepth = SummaryDepth.DETAILED, model: str = "gpt-3.5-turbo-16k") -> str:
    """Generate a structured Markdown summary using OpenAI's GPT models with configurable depth."""
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not client.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your environment variables.")

        # Add exponential backoff for rate limiting with adaptive delays
        max_retries = config.get("max_retries", 4)
        base_delay = config.get("base_delay", 10)  # Increased base delay for rate limits
        total_tokens = num_tokens_from_string(text)
        print(f"Total transcript tokens: {total_tokens}")
        
        # Get appropriate chunk parameters for the model
        max_chunk_tokens, overlap_tokens = get_chunk_parameters(model)
        print(f"Using chunk size: {max_chunk_tokens} tokens, overlap: {overlap_tokens} tokens")
        
        # Use smaller chunks to stay within rate limits
        chunks = chunk_transcript(text, model=model, max_tokens=max_chunk_tokens, overlap_tokens=overlap_tokens)
        total_chunks = len(chunks)
        print(f"Processing transcript in {total_chunks} chunks...")
        
        # Initialize progress tracker
        progress = ProgressTracker(total_chunks)
        
        intermediate_summaries = []
        for i, chunk in enumerate(chunks):
            # Update progress
            progress.update(i, chunk['token_count'])
            
            # Calculate adaptive delay based on token count
            adaptive_delay = max(5, min(20, chunk['token_count'] / 500))  # 5-20 seconds based on chunk size
            
            for retry in range(max_retries):
                try:
                    if retry > 0:
                        delay = base_delay * (1.5 ** (retry - 1))
                        print(f"\nRetry {retry}/{max_retries} after {delay:.1f} seconds...")
                        time.sleep(delay)
                    
                    summary = generate_chunk_summary(chunk['text'], i, total_chunks, client, depth, model)
                    if summary:
                        intermediate_summaries.append(summary)
                        # Add adaptive delay between chunks
                        if i < total_chunks - 1:
                            time.sleep(adaptive_delay)
                        break
                except Exception as e:
                    error_msg = str(e).lower()
                    if "rate limit" in error_msg or "too many requests" in error_msg:
                        if retry == max_retries - 1:
                            print(f"\nRate limit exceeded after {max_retries} retries")
                            raise
                        # Increase delay for rate limit errors
                        time.sleep(base_delay * (2 ** retry))
                        continue
                    raise
        
        if not intermediate_summaries:
            print("\nNo summaries were generated from any chunks")
            return None
        
        # Generate final summary with retry logic and longer delay
        print("\nGenerating final summary...")
        for retry in range(max_retries):
            try:
                if retry > 0:
                    delay = base_delay * 2 * (1.5 ** (retry - 1))  # Double base delay for final summary
                    print(f"Retrying final summary after {delay:.1f} seconds...")
                    time.sleep(delay)
                
                final_summary = generate_final_summary(intermediate_summaries, client, depth, model)
                progress.complete()
                return final_summary
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "too many requests" in error_msg:
                    if retry == max_retries - 1:
                        print(f"\nRate limit exceeded during final summary after {max_retries} retries")
                        raise
                    continue
                raise
                
    except KeyboardInterrupt:
        print("\nSummary generation cancelled by user.")
        return None
    except Exception as e:
        print(f"\nError generating summary: {str(e)}")
        return None

def get_transcript_with_retry(video_id: str, max_retries: int = 3, base_delay: int = 5) -> List[Dict]:
    """Get transcript with retry mechanism and caching."""
    # Check cache first
    if cache.has_transcript(video_id):
        print("Using cached transcript...")
        return cache.get_transcript(video_id)
    
    # If not in cache, fetch with retry
    for attempt in range(max_retries):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            # Cache the transcript
            cache.cache_transcript(video_id, transcript)
            return transcript
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1}/{max_retries} failed. Retrying in {delay} seconds...")
            time.sleep(delay)

def get_summary(video_url, output_dir: str = None):
    """Get summary for a YouTube video with caching."""
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            print("Error: Could not extract video ID from URL")
            return

        # Get video title with retry
        print("Fetching video title...")
        video_title = get_video_title(video_id)
        print(f"Parsing {video_title}")
        
        # Get the transcript with caching
        print("Downloading transcript...")
        transcript = get_transcript_with_retry(video_id)
        
        # Combine transcript text
        full_transcript = "\n".join([entry['text'] for entry in transcript])
        
        # Check if summary is cached
        depth = os.getenv('SUMMARY_DEPTH', 'detailed')
        model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo-16k')
        
        if cache.has_summary(video_id, depth, model):
            print("Using cached summary...")
            summary = cache.get_summary(video_id, depth, model)
        else:
            # Generate new summary
            print("\nGenerating summary...")
            summary = generate_summary(full_transcript)
            if summary:
                # Cache the summary
                cache.cache_summary(video_id, depth, model, summary)
        
        if summary:
            # Add metadata to the summary
            metadata = f"""# {video_title}

## Video Information
- URL: {video_url}
- Video ID: {video_id}
- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
- Model: {model}
- Summary Depth: {depth}

"""
            summary_with_metadata = f"{metadata}\n{summary}"
            
            # Save summary with versioning
            base_summary_file = f"{video_title} - summary"
            summary_file = get_next_available_filename(base_summary_file, ".md", output_dir)
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_with_metadata)
            print(f"Summary has been saved to {summary_file}")
            return summary_file
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Log error details
        error_log = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'video_url': video_url,
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        log_file = os.path.join(output_dir if output_dir else OUTPUT_DIR, 'error_log.json')
        try:
            with open(log_file, 'a') as f:
                json.dump(error_log, f)
                f.write('\n')
        except:
            print("Could not write to error log")
    return None

def get_transcript(video_url, output_dir: str = None):
    """Get transcript for a YouTube video and save it to a text file."""
    try:
        # Create output directory if it doesn't exist
        target_dir = output_dir if output_dir else OUTPUT_DIR
        os.makedirs(target_dir, exist_ok=True)

        video_id = extract_video_id(video_url)
        if not video_id:
            print("Error: Could not extract video ID from URL")
            return

        # Get video title
        print("Fetching video title...")
        video_title = get_video_title(video_id)
        print(f"Parsing {video_title}")
        
        # Get the transcript
        print("Downloading transcript...")
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine transcript text
        full_transcript = "\n".join([entry['text'] for entry in transcript])
        
        # Save transcript with versioning
        base_transcript_file = f"{video_title} - transcript"
        transcript_file = get_next_available_filename(base_transcript_file, ".txt", target_dir)
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(full_transcript)
        print(f"Transcript has been saved to {transcript_file}")
        return transcript_file, full_transcript
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    return None, None

def is_url(text: str) -> bool:
    """Check if the input is a URL."""
    url_pattern = r'https?://(?:www\.)?(?:youtube\.com|youtu\.be)/.+'
    return bool(re.match(url_pattern, text))

def process_url_file(file_path: str):
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
            get_transcript(url)
            print("-" * 50)
    
    except Exception as e:
        print(f"Error processing URL file: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:")
        print("  For single video: python youtube_transcript.py <youtube_url>")
        print("  For multiple videos: python youtube_transcript.py <path_to_url_file.txt>")
        sys.exit(1)
    
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key or set it in your environment")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # Check if input is a URL or a file
    if is_url(input_path):
        get_transcript(input_path)
    else:
        if not os.path.exists(input_path):
            print(f"Error: File '{input_path}' not found")
            sys.exit(1)
        process_url_file(input_path) 