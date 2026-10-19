"""
Central configuration.

Lives at senyasabi/backend/config.py. Data lives in senyasabi/resources/.

Env vars (see .env):
  DATABASE_URL               Postgres (Supabase session pooler)
  SUPABASE_URL / *_KEY / JWT Supabase API (server side only)
  S3_*                       Supabase Storage S3 credentials (admin scripts only)
  FASTAPI_*                  API host/port

The desktop client imports this module, so never rely on secrets being present
there. Server/admin scripts should check for what they need.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

BACKEND_DIR = Path(__file__).resolve().parent      # .../senyasabi/backend
BASE_DIR = BACKEND_DIR.parent                      # .../senyasabi

# Explicit .env location first, then the default upward search as a fallback.
load_dotenv(BASE_DIR / ".env")
load_dotenv()

DATA_DIR = BASE_DIR / "resources" / "data"
VRM_SIGNS_DIR = BASE_DIR / "resources" / "VRM_SIGNS"
LESSONS_PATH = DATA_DIR / "lessons.json"

# ---- Local SQLite cache ------------------------------------------------
# DATABASE_PATH = DATA_DIR / "senyasabi.db"
DATABASE_PATH = Path(os.getenv("SENYASABI_DB") or DATA_DIR / "senyasabi.db")
SQLITE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

MEDIA_CACHE_DIR = Path(os.getenv("SENYASABI_MEDIA_CACHE") or BASE_DIR / "cache" / "media")

# ---- Client Mode -------------------------------------------------------
# CLIENT_MODE determines how the app connects to Supabase:
# - "fastapi" (default): Client uses FastAPI proxy, FastAPI uses service_role
# - "distributed": Client connects directly to Supabase with anon key
CLIENT_MODE = os.getenv("SENYESABI_MODE", "fastapi").lower()

# ---- Postgres (Supabase) -----------------------------------------------
def _normalize_pg_url(url: str | None) -> str | None:
    """Force the psycopg3 driver. Supabase hands out plain postgresql:// URLs,
    which SQLAlchemy would otherwise map to psycopg2."""
    if not url:
        return None
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


# In distributed mode, we don't need direct PostgreSQL access
POSTGRESQL_URL = _normalize_pg_url(os.getenv("DATABASE_URL")) if CLIENT_MODE == "fastapi" else None

# ---- Supabase API -------------------------------------------------------
# SUPABASE_URL and SUPABASE_ANON_KEY are PUBLIC and safe to bundle with client
# SUPABASE_SERVICE_ROLE_KEY and SUPABASE_JWT_SECRET are SECRET and only for FastAPI
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") if CLIENT_MODE == "fastapi" else None
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET") if CLIENT_MODE == "fastapi" else None

# ---- Supabase Storage, S3 protocol (admin scripts only) ----------------
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_REGION = os.getenv("S3_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")

# ---- FastAPI -----------------------------------------------------------
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "127.0.0.1")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
FASTAPI_DEBUG = os.getenv("FASTAPI_DEBUG", "false").lower() == "true"
API_BASE_URL = os.getenv("API_BASE_URL", f"http://{FASTAPI_HOST}:{FASTAPI_PORT}")

# ---- Sync --------------------------------------------------------------
SYNC_BATCH_SIZE = 10
SYNC_MAX_RETRIES = 3
SYNC_RETRY_DELAY_SECONDS = 5

# ---- Offline auth ------------------------------------------------------
OFFLINE_AUTH_MAX_FAILED_ATTEMPTS = 5
OFFLINE_AUTH_LOCKOUT_MINUTES = 15
OFFLINE_AUTH_MAX_DAYS = 30

# ---- Alphabet model ----------------------------------------------------
ALPHABET_MODEL_PATH = DATA_DIR / "alphabet.keras"
ALPHABET_LABELS_PATH = None
ALPHABET_LABELS_FALLBACK = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ALPHABET_SCALER_PATH = DATA_DIR / "alphabetscaler.pkl"

# ---- Word model (105 signs) --------------------------------------------
WORDS_MODEL_PATH = DATA_DIR / "105words.keras"
WORDS_LABELS_PATH = DATA_DIR / "105labels.json"
WORDS_SCALER_PATH = None

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

NORM_MODE = "scale"
CONFIDENCE_THRESHOLD = 0.70
HOLD_FRAMES = 18
CAM_INDEX = 0