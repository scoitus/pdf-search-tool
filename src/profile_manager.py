"""Manage saved search profiles stored as JSON."""

import json
from datetime import datetime
from pathlib import Path

from models.search_profile import SearchProfile

CONFIG_DIR = Path.home() / ".config" / "pdf-search-tool"
PROFILES_FILE = CONFIG_DIR / "profiles.json"


class ProfileManager:
    """Manages search profiles stored as JSON."""

    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.profiles_file = PROFILES_FILE
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_profiles(self) -> list[SearchProfile]:
        """Load all saved profiles from disk."""
        if not self.profiles_file.exists():
            return []
        try:
            with open(self.profiles_file, "r") as f:
                data = json.load(f)
            return [SearchProfile(**p) for p in data.get("profiles", [])]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []

    def save_profile(self, profile: SearchProfile):
        """Add or update a profile (matched by name)."""
        profiles = self.load_profiles()

        # Update existing or append new
        found = False
        for i, p in enumerate(profiles):
            if p.name == profile.name:
                profiles[i] = profile
                found = True
                break
        if not found:
            if not profile.created_at:
                profile.created_at = datetime.now().isoformat()
            profiles.append(profile)

        self._write_profiles(profiles)

    def delete_profile(self, name: str):
        """Remove a profile by name."""
        profiles = [p for p in self.load_profiles() if p.name != name]
        self._write_profiles(profiles)

    def update_last_used(self, name: str):
        """Update the last_used timestamp for a profile."""
        profiles = self.load_profiles()
        for p in profiles:
            if p.name == name:
                p.last_used = datetime.now().isoformat()
                break
        self._write_profiles(profiles)

    def _write_profiles(self, profiles: list[SearchProfile]):
        """Write profiles list to disk."""
        data = {
            "version": 1,
            "profiles": [self._profile_to_dict(p) for p in profiles],
        }
        with open(self.profiles_file, "w") as f:
            json.dump(data, f, indent=2)

    def _profile_to_dict(self, profile: SearchProfile) -> dict:
        return {
            "name": profile.name,
            "query": profile.query,
            "folders": profile.folders,
            "case_sensitive": profile.case_sensitive,
            "search_mode": profile.search_mode,
            "recursive": profile.recursive,
            "created_at": profile.created_at,
            "last_used": profile.last_used,
        }
