from dataclasses import dataclass, field


@dataclass
class MatchContext:
    """A single match within a page."""
    page_number: int        # 1-based page number
    match_text: str         # The matched text fragment
    context_before: str     # Text before the match (short, ~80 chars)
    context_after: str      # Text after the match (short, ~80 chars)
    char_offset: int        # Character offset within the page text
    extended_context: str = ""  # Larger snippet (~300 chars each side) for expanded view


@dataclass
class FileResult:
    """All matches within a single PDF file."""
    file_path: str
    file_name: str
    matches: list[MatchContext] = field(default_factory=list)
    total_pages: int = 0
    error: str | None = None


@dataclass
class SearchResults:
    """Complete results from a search operation."""
    query: str
    files_searched: int = 0
    files_with_matches: int = 0
    total_matches: int = 0
    file_results: list[FileResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0
