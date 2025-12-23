from __future__ import annotations

from pathlib import Path

from .settings import settings

# ---------------------------------------------------------------------------
# Path constants - Multi-sport structure
#
# Usage:
#   from spread_eagle.config import get_data_paths
#   paths = get_data_paths("cfb")  # or "cbb"
#   paths.raw / "games_2024.json"
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = DATA_DIR / "models"

# Legacy aliases for backwards compatibility (CFB)
RAW_DIR = DATA_DIR / "cfb" / "raw"
PROCESSED_DIR = DATA_DIR / "cfb" / "processed"


class SportPaths:
    """Data paths for a specific sport."""

    def __init__(self, sport: str):
        self.sport = sport
        self.base = DATA_DIR / sport
        self.raw = self.base / "raw"
        self.processed = self.base / "processed"
        self.external = self.base / "external"

    def ensure_dirs(self) -> None:
        """Create all directories if they don't exist."""
        self.raw.mkdir(parents=True, exist_ok=True)
        self.processed.mkdir(parents=True, exist_ok=True)
        self.external.mkdir(parents=True, exist_ok=True)


def get_data_paths(sport: str) -> SportPaths:
    """
    Get data paths for a sport.

    Args:
        sport: Sport code ("cfb", "cbb", etc.)

    Returns:
        SportPaths object with raw, processed, external paths
    """
    return SportPaths(sport)
