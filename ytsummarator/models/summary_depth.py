"""Summary depth options for video summarization."""
from enum import Enum

class SummaryDepth(Enum):
    """Available summary depth levels."""
    BASIC = "basic"
    DETAILED = "detailed"
    TECHNICAL = "technical" 