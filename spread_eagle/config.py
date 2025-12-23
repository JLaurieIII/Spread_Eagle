"""
Legacy config module - redirects to spread_eagle.config package.
Kept for backwards compatibility with existing scripts.
"""
from spread_eagle.config import (
    ROOT_DIR,
    DATA_DIR,
    RAW_DIR,
    PROCESSED_DIR,
    MODELS_DIR,
    get_data_paths,
    settings,
)

__all__ = [
    "ROOT_DIR",
    "DATA_DIR", 
    "RAW_DIR",
    "PROCESSED_DIR",
    "MODELS_DIR",
    "get_data_paths",
    "settings",
]
