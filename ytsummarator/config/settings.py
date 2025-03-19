"""Configuration management for the summarizer."""
import json
import os

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