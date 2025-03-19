"""Cache management for transcripts and summaries."""
import os
import json
import time
from typing import List, Dict

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