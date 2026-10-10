"""
Central configuration for the recognition backend.

Assumes this file lives at:
    Senyasabi_V1/senyasabi/backend/config.py
and your data lives at:
    Senyasabi_V1/senyasabi/resources/data/
    Senyasabi_V1/senyasabi/resources/VRM_SIGNS/

If your paths differ, this is the only file you need to edit.
"""
from pathlib import Path

BACKEND_DIR   = Path(__file__).resolve().parent           # .../senyasabi/backend
BASE_DIR      = BACKEND_DIR.parent                         # .../senyasabi
DATA_DIR      = BASE_DIR / 'resources' / 'data'
DATABASE_PATH = DATA_DIR / "senyasabi.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"
VRM_SIGNS_DIR = BASE_DIR / 'resources' / 'VRM_SIGNS'
LESSONS_PATH  = DATA_DIR / 'lessons.json'

# ---- Database Configuration --------------------------------------------
# SQLite is the primary local database for Phase 1
# PostgreSQL will be added in Phase 2 for cloud sync
POSTGRESQL_URL = None  # Set to postgresql+psycopg2://user:pass@host/db for Phase 2

# ---- Sync Configuration (for Phase 2) ----------------------------------
SYNC_BATCH_SIZE = 10
SYNC_MAX_RETRIES = 3
SYNC_RETRY_DELAY_SECONDS = 5

# ---- Offline Authentication Configuration ------------------------------
OFFLINE_AUTH_MAX_FAILED_ATTEMPTS = 5
OFFLINE_AUTH_LOCKOUT_MINUTES = 15

# ---- Alphabet model ---------------------------------------------------
ALPHABET_MODEL_PATH  = DATA_DIR / 'alphabet.keras'
ALPHABET_LABELS_PATH = None                                 # TODO: set if you have a labels file for this model
ALPHABET_LABELS_FALLBACK = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ALPHABET_SCALER_PATH  = DATA_DIR / 'alphabetscaler.pkl'      # sklearn StandardScaler used at training time

# ---- Word model (105 signs) --------------------------------------------
WORDS_MODEL_PATH  = DATA_DIR / '105words.keras'
WORDS_LABELS_PATH = DATA_DIR / '105labels.json'
WORDS_SCALER_PATH = None   # no scaler for this one — set to a real path if you add one later

# Registry SignRecognitionEngine reads from via `mode=`
MODELS = {
    "alphabet": {
        "model_path": ALPHABET_MODEL_PATH,
        "labels_path": ALPHABET_LABELS_PATH,
        "labels_fallback": ALPHABET_LABELS_FALLBACK,
        "scaler_path": ALPHABET_SCALER_PATH,
    },
    "words": {
        "model_path": WORDS_MODEL_PATH,
        "labels_path": WORDS_LABELS_PATH,
        "labels_fallback": None,
        "scaler_path": WORDS_SCALER_PATH,
    },
}

NORM_MODE            = 'scale'
CONFIDENCE_THRESHOLD = 0.70
HOLD_FRAMES          = 18
CAM_INDEX            = 0