"""Progress tracking for summary generation."""
import time

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