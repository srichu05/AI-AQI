"""Centralized path definitions for project data and artifacts."""

from pathlib import Path

# Base project directories
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DL_DATA_DIR = DATA_DIR / "dl"
ML_DATA_DIR = DATA_DIR / "ml"
LIVE_DATA_DIR = DATA_DIR / "live"
SAVED_MODELS_DIR = ROOT_DIR / "saved_models"
EXPERIMENTS_DIR = ROOT_DIR / "experiments"

# Centralized artifact and metadata file paths
CLASS_WEIGHTS_PATH = EXPERIMENTS_DIR / "class_weights.json"
DATASET_SUMMARY_PATH = EXPERIMENTS_DIR / "dataset_summary.json"
FEATURE_GROUPS_PATH = DL_DATA_DIR / "feature_groups.json"

# Ensure output directories exist when needed
def ensure_directories_exist() -> None:
    """Create necessary directories if they do not already exist."""
    for path in [DATA_DIR, DL_DATA_DIR, ML_DATA_DIR, LIVE_DATA_DIR, SAVED_MODELS_DIR, EXPERIMENTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)
