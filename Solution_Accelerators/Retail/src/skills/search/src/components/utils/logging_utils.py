from enum import Enum

class SearchLoggingEvents(Enum):
    SEARCH_BATCH_START = "Search.Batch.Start"
    SEARCH_BATCH_COMPLETE = "Search.Batch.Complete"
    SEARCH_START = "Search.Start"
    SEARCH_COMPLETE = "Search.Complete"