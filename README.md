# SenyaSabi: Computer Vision-Based Interactive Learning for Filipino Sign Language (FSL)

SenyaSabi is a desktop learning application built with **PySide6**, **OpenCV**, and **MediaPipe** / **Keras**, designed to teach Filipino Sign Language (FSL) interactively through computer vision.

---

## 1. Learning Structure & Architecture

The learning curriculum is structured into an introductory Alphabet foundation followed by exactly five top-level word categories:

1. **Lesson 1: Alphabet (Introductory Lesson)**
   - Teaches the 26 Filipino Sign Language letters (A–Z).
   - Driven by dedicated alphabet landmark extraction (single hand / 21 landmarks / 63 coordinates) and MLP recognition (`best_landmark_model.keras`).
   - Alphabet exercises are separate from word categories and evaluate static hand gestures with a confidence threshold and hold-frame verification.

2. **Five Main Word Categories**:
   - **GREETING** (`greeting.keras`): 10 core greetings signs (e.g., *GOOD MORNING*, *HELLO*, *THANK YOU*).
   - **SURVIVAL** (`survival.keras`): 10 essential communication signs (e.g., *HELP*, *PLEASE*, *DONT UNDERSTAND*).
   - **NUMBER** (`number.keras`): 10 foundational number signs.
   - **DAYS** (`days.keras`): 10 calendar and day-of-week signs (e.g., *MONDAY*, *TODAY*, *YESTERDAY*).
   - **FAMILY** (`family.keras`): 10 family relationship signs (e.g., *MOTHER*, *FATHER*, *BROTHER*).

*Note: Obsolete/legacy categories (`RELATIONSHIPS`, `CALENDAR`, `COLOR`, `FOOD`, `DRINK`) are mapped or preserved for historical progress and asset backwards-compatibility, but are rejected as top-level word categories.*

---

## 2. Interactive Features & Minigames

- **Reference Media Playback**: High-definition video player (`SignVideoPlayer`) and animated avatar demonstration for each sign.
- **Real-Time Recognition Practice**: Smooth camera preview with rounded cards, target holding indicator, and instant visual feedback (success celebration and retry prompts).
- **Three Interactive Minigames**:
  1. **FingerSpell Quest**: Practice spelling target words letter-by-letter with live camera recognition and cooldown feedback.
  2. **Sign Sprint**: Time-attack mode testing rapid identification of signed gestures.
  3. **Sign Detective**: Deductive vocabulary game identifying signs under varying clues and time limits.
- **User Dashboard & Leaderboard**:
  - Live local progress tracking, current streak calculation, and user statistics.
  - Offline-resilient leaderboards displaying all-time top scores with rank badges.

---

## 3. Database Integrity & Compatibility

**CRITICAL POLICY: The database schema, tables, relationships, constraints, and migrations have remained completely unchanged.**
- All backward compatibility (such as legacy category name aliases, punctuation normalization like `DONT UNDERSTAND` vs `DON'T UNDERSTAND` vs `DON’T UNDERSTAND`, and UUID string handling) is resolved entirely within application-level mapping and content services.
- Historical user records, attempts, and scores are preserved.

---

## 4. Setup and Installation

### Prerequisites
- Windows 10/11 (64-bit)
- Python 3.10 – 3.12 (Recommended: Python 3.12)
- Webcam / camera device (for live recognition)

### Environment Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/Mary/Senyasabi_V1.git
   cd Senyasabi_V1
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```powershell
   pip install -r senyasabi/requirements.txt
   ```

---

## 5. Running the Application

To launch SenyaSabi:
```powershell
$env:PYTHONPATH="senyasabi;.venv/Lib/site-packages"
.\.venv\Scripts\python.exe senyasabi/main.py
```
Or from the `senyasabi` directory:
```powershell
cd senyasabi
python main.py
```

### Controls & Navigation
- **F11**: Toggle Fullscreen mode.
- **Escape**: Exit Fullscreen (return to maximized view).
- **Top Bar Menu**: Access Camera Settings and Logout.
- **Back Buttons**: Step backward through the learning flow with exit confirmation safeguards during active sessions.

---

## 6. Running the Automated Test Suite

All 170 unit and integration tests run completely offline and headlessly without requiring a physical camera device:

```powershell
$env:PYTHONPATH="senyasabi;.venv/Lib/site-packages"
.\.venv\Scripts\python.exe -m unittest discover -s senyasabi/tests -p "test_*.py"
```

Or run all suites with verbose output:
```powershell
$env:PYTHONPATH="senyasabi;.venv/Lib/site-packages"
.\.venv\Scripts\python.exe senyasabi/tests/test_uat_flow.py -v
```

---

## 7. Distributed Production Builds

For distributed releases, SenyaSabi uses Supabase for authentication and backend services. The application requires the following environment variables to be configured:

### Required Environment Variables

Create a `.env` file in the application directory or set these environment variables:

```bash
# Supabase Configuration (Required for distributed builds)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# FastAPI Backend Configuration (Optional - for development)
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
API_BASE_URL=http://127.0.0.1:8000

# Production Mode
PRODUCTION=true  # Set to 'true' for distributed builds

# Database Configuration (Local SQLite cache)
SENYASABI_DB=senyasabi/resources/data/senyasabi.db
```

### Security Notes

- **SUPABASE_ANON_KEY**: This is a public key intended for client-side use. It is safe to include in distributed builds.
- **SUPABASE_SERVICE_ROLE_KEY**: Never include this in distributed builds. It should only be used server-side.
- **HTTPS**: In production mode (`PRODUCTION=true`), the application enforces HTTPS for all Supabase and API connections.

### Authentication Flow

1. Users authenticate with Supabase using their email and password
2. JWT access tokens are obtained and stored securely in the OS credential store (keyring)
3. The API client uses these tokens for authenticated requests to the FastAPI backend
4. Offline mode is supported with local SQLite caching and sync queue

### Offline Support

- The application maintains a local SQLite cache for offline operation
- Progress, quiz attempts, and minigame scores are queued when offline
- Data automatically syncs to the server when connection is restored
- A connection status indicator shows online/offline state in the UI

### Connection Testing

The application includes a connection test function (`AppController.test_connection()`) that verifies connectivity to:

1. **Supabase**: Tests if the Supabase backend is reachable (production mode only)
2. **FastAPI Backend**: Tests if the local FastAPI backend is running

The test returns a dictionary with connection status for each service and an overall message. This can be used in setup wizards or diagnostic tools to verify configuration.

### Error Handling

- User-facing errors are displayed using the `ErrorDialog` class in `screens/dialogs.py`
- Network errors are caught and logged with appropriate fallback behavior
- Authentication errors provide clear user feedback
- Offline mode gracefully degrades functionality while preserving local data

---

## 8. Packaging as a Windows Executable

The project includes a standalone PyInstaller configuration (`senyasabi.spec`) that bundles all models, fonts, styles, Qt Designer UI files, and video assets into a distributable Windows executable:

```powershell
pip install pyinstaller
pyinstaller senyasabi.spec
```

The compiled standalone executable and asset bundle will be generated in `dist/SenyaSabi/SenyaSabi.exe`.

### Distributed Build Checklist

Before creating a distributed build:

1. ✅ Remove DEV_MODE authentication (completed)
2. ✅ Configure production environment variables
3. ✅ Set `PRODUCTION=true` in environment
4. ✅ Ensure Supabase URL and anon key are configured
5. ✅ Verify HTTPS enforcement is active
6. ✅ Test offline mode functionality
7. ✅ Verify credential store (keyring) availability on target platform

