"""Error handling and retry logic."""
import time
from typing import Callable, Any, Optional

class RetryError(Exception):
    """Exception raised when all retries are exhausted."""
    pass

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
    
    Returns:
        Result of the function call
    
    Raises:
        RetryError: If all retries are exhausted
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise RetryError(f"Failed after {max_retries} attempts: {str(e)}")
            
            # Calculate delay with exponential backoff
            delay = min(
                base_delay * (exponential_base ** attempt),
                max_delay
            )
            
            # Add jitter if enabled
            if jitter:
                delay *= (1 + (time.time() % 1) * 0.1)
            
            time.sleep(delay)
    
    raise RetryError(f"Failed after {max_retries} attempts") 