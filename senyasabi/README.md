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

## 7. Packaging as a Windows Executable

The project includes a standalone PyInstaller configuration (`senyasabi.spec`) that bundles all models, fonts, styles, Qt Designer UI files, and video assets into a distributable Windows executable:

```powershell
pip install pyinstaller
pyinstaller senyasabi.spec
```

The compiled standalone executable and asset bundle will be generated in `dist/SenyaSabi/SenyaSabi.exe`.
