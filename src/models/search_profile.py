from dataclasses import dataclass, field


@dataclass
class SearchProfile:
    """A saved search configuration."""
    name: str
    query: str
    folders: list[str] = field(default_factory=list)
    case_sensitive: bool = False
    search_mode: str = "plain"  # "plain", "regex", "boolean"
    recursive: bool = True
    created_at: str = ""
    last_used: str = ""
