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

# Load environment variables
load_dotenv()

# Create output directory
OUTPUT_DIR = "Summarator_Output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def num_tokens_from_string(string: str, model: str = "gpt-4") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def chunk_transcript(text: str, max_tokens: int = 6000, overlap_tokens: int = 500) -> List[Dict[str, str]]:
    """Split transcript into chunks that respect sentence boundaries and token limits with overlap."""
    encoding = tiktoken.encoding_for_model("gpt-4")
    
    # Split into sentences (improved approach)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_tokens = []
    current_length = 0
    
    for sentence in sentences:
        sentence_tokens = encoding.encode(sentence)
        token_count = len(sentence_tokens)
        
        # If adding this sentence would exceed the limit, save current chunk and start new one
        if current_length + token_count > max_tokens and current_chunk:
            # Join the current chunk and save it
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'token_count': current_length
            })
            
            # Start new chunk with overlap
            # Calculate how many previous sentences we need for the overlap
            overlap_count = 0
            overlap_tokens_count = 0
            for sent in reversed(current_chunk):
                sent_tokens = len(encoding.encode(sent))
                if overlap_tokens_count + sent_tokens <= overlap_tokens:
                    overlap_count += 1
                    overlap_tokens_count += sent_tokens
                else:
                    break
            
            # Start new chunk with overlapping sentences
            current_chunk = current_chunk[-overlap_count:] if overlap_count > 0 else []
            current_length = sum(len(encoding.encode(s)) for s in current_chunk)
        
        current_chunk.append(sentence)
        current_length += token_count
    
    # Add the last chunk if it exists
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunks.append({
            'text': chunk_text,
            'token_count': current_length
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

def get_next_available_filename(base_filename: str, extension: str) -> str:
    """Get the next available filename by adding a version number if the file exists."""
    # Ensure base_filename is within the output directory
    base_filepath = os.path.join(OUTPUT_DIR, base_filename)
    
    if not os.path.exists(f"{base_filepath}{extension}"):
        return f"{base_filepath}{extension}"
    
    counter = 1
    while os.path.exists(f"{base_filepath} ({counter}){extension}"):
        counter += 1
    
    return f"{base_filepath} ({counter}){extension}"

def generate_chunk_summary(chunk: str, chunk_index: int, total_chunks: int, client: OpenAI) -> str:
    """Generate a summary for a single chunk of the transcript."""
    try:
        # Adjust the prompt based on whether it's an intermediate or final chunk
        if total_chunks == 1:
            prompt = f"""Create a detailed Markdown summary of this transcript. Pay special attention to specific references (e.g., forms, tools, software, numbers) while maintaining clear and concise bullet points.

## Main Topics
- List the key themes discussed (2-4 bullet points)
- Focus on the core problems or concepts addressed

## Key Details
- List all specific references mentioned:
  * Forms, documents, or official procedures
  * Tools, software, or platforms used
  * Specific numbers, dates, or timeframes
  * Names of relevant organizations or programs

## Key Points
- Break down the most important points (4-6 bullet points)
- Include specific examples and context
- Highlight any step-by-step processes or solutions mentioned
- Each point should be self-contained and clear

## Important Takeaways
- List practical lessons and insights (2-5 bullet points)
- Focus on actionable advice or warnings
- Include any recommended best practices

## Notable Quotes
- Include significant quotes that:
  * Provide specific advice or warnings
  * Explain key concepts
  * Share personal experiences
- Always attribute quotes to speakers

Transcript:
{chunk}"""
        else:
            context = "beginning of" if chunk_index == 0 else "middle of" if chunk_index < total_chunks - 1 else "end of"
            prompt = f"""This is part {chunk_index + 1} of {total_chunks} (the {context} the transcript).

Please analyze this portion and extract:
1. Any specific references:
   - Forms, documents, procedures
   - Tools, software, platforms
   - Numbers, dates, timeframes
   - Organizations, programs
2. Key points and processes discussed
3. Notable quotes with speaker attribution
4. Practical advice or warnings given

Format as bullet points, with sub-points for specific details and context.

Transcript portion:
{chunk}"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional content analyst who creates detailed, well-structured summaries. Focus on capturing specific details, references, and actionable information while maintaining clarity and conciseness."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7,
            timeout=60
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating chunk summary: {str(e)}")
        return ""

def generate_final_summary(intermediate_summaries: List[str], client: OpenAI) -> str:
    """Generate a final summary from all intermediate summaries."""
    try:
        combined_points = "\n\n".join(intermediate_summaries)
        
        prompt = f"""Based on the following collection of key points from different parts of the transcript, 
create a cohesive final summary that captures all specific details while maintaining clarity:

## Main Topics
- List the key themes discussed (2-4 bullet points)
- Focus on the core problems or concepts addressed

## Key Details
- List all specific references mentioned:
  * Forms, documents, or official procedures
  * Tools, software, or platforms used
  * Specific numbers, dates, or timeframes
  * Names of relevant organizations or programs

## Key Points
- Break down the most important points (4-6 bullet points)
- Include specific examples and context
- Highlight any step-by-step processes or solutions mentioned
- Each point should be self-contained and clear

## Important Takeaways
- List practical lessons and insights (2-4 bullet points)
- Focus on actionable advice or warnings
- Include any recommended best practices

## Notable Quotes
- Include significant quotes that:
  * Provide specific advice or warnings
  * Explain key concepts
  * Share personal experiences
- Always attribute quotes to speakers

Key points from transcript:
{combined_points}"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional content analyst. Create a cohesive final summary that captures specific details and references while maintaining clarity and actionability. Focus on information that would be most useful to someone wanting to understand or apply the content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7,
            timeout=60
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating final summary: {str(e)}")
        return None

def generate_summary(text: str) -> str:
    """Generate a structured Markdown summary using OpenAI's GPT-4 with improved chunking."""
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Get initial token count
        total_tokens = num_tokens_from_string(text)
        print(f"Total transcript tokens: {total_tokens}")
        
        # Split transcript into chunks
        chunks = chunk_transcript(text)
        total_chunks = len(chunks)
        print(f"Processing transcript in {total_chunks} chunks...")
        
        # Process each chunk and collect intermediate summaries
        intermediate_summaries = []
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i + 1}/{total_chunks} ({chunk['token_count']} tokens)...")
            summary = generate_chunk_summary(chunk['text'], i, total_chunks, client)
            if summary:
                intermediate_summaries.append(summary)
        
        # If we only had one chunk, return its summary directly
        if total_chunks == 1:
            return intermediate_summaries[0]
        
        # Generate final summary from intermediate summaries
        print("Generating final summary...")
        final_summary = generate_final_summary(intermediate_summaries, client)
        
        return final_summary
    except KeyboardInterrupt:
        print("\nSummary generation cancelled by user.")
        return None
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return None

def get_transcript(video_url):
    """Get transcript for a YouTube video, save it to a text file, and generate a summary."""
    try:
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
        transcript_file = get_next_available_filename(base_transcript_file, ".txt")
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(full_transcript)
        print(f"Transcript has been saved to {transcript_file}")
        
        # Generate and save summary
        print("\nGenerating summary...")
        summary = generate_summary(full_transcript)
        if summary:
            # Add the title at the beginning of the summary
            summary_with_title = f"# {video_title}\n\n{summary}"
            base_summary_file = f"{video_title} - summary"
            summary_file = get_next_available_filename(base_summary_file, ".md")
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_with_title)
            print(f"Summary has been saved to {summary_file}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

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