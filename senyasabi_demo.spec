# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for SenyaSabi Windows Demo Application (under 1 GB)."""
import os
import sys
from pathlib import Path

block_cipher = None

# Base path for SenyaSabi source code
senyasabi_root = Path(SPECPATH).resolve() / "senyasabi"
if not senyasabi_root.exists():
    senyasabi_root = Path(".").resolve()

# Bundled data files specifically for Module 1 Demo
datas = [
    # Demo configuration (.env.production as .env)
    (str(senyasabi_root / ".env"), "."),
    
    # Core resources
    (str(senyasabi_root / "resources" / "data" / "senyasabi.db"), "resources/data"),
    (str(senyasabi_root / "resources" / "data" / "alphabet.keras"), "resources/data"),
    (str(senyasabi_root / "resources" / "data" / "alphabetscaler.pkl"), "resources/data"),
    (str(senyasabi_root / "resources" / "data" / "105labels.json"), "resources/data"),
    (str(senyasabi_root / "resources" / "data" / "expected_dataset.md"), "resources/data"),
    (str(senyasabi_root / "resources" / "data" / "module_lessons.json"), "resources/data"),
    (str(senyasabi_root / "resources" / "data" / "lesson_curriculum_plan.json"), "resources/data"),
    (str(senyasabi_root / "resources" / "data" / "quizzes"), "resources/data/quizzes"),
    
    # Models (MediaPipe hand & pose detector tasks)
    (str(senyasabi_root / "resources" / "models" / "mediapipe"), "resources/models/mediapipe"),
    
    # VRM signs for alphabet stills
    (str(senyasabi_root / "resources" / "VRM_SIGNS"), "resources/VRM_SIGNS"),
    
    # UI Presentation
    (str(senyasabi_root / "resources" / "font"), "resources/font"),
    (str(senyasabi_root / "resources" / "img"), "resources/img"),
    (str(senyasabi_root / "resources" / "styles"), "resources/styles"),
    
    # Qt designer & generated forms
    (str(senyasabi_root / "ui" / "designer"), "ui/designer"),
    (str(senyasabi_root / "ui" / "generated"), "ui/generated"),
]

# MediaPipe modules data
try:
    import mediapipe
    mp_path = Path(mediapipe.__file__).parent
    datas.append((str(mp_path / "modules"), "mediapipe/modules"))
except Exception:
    pass

hidden_imports = [
    # Core PySide6
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    
    # Computer Vision & ML
    "cv2",
    "mediapipe",
    "mediapipe.tasks.python.vision",
    "tensorflow",
    "keras",
    "sklearn",
    "sklearn.preprocessing",
    
    # Security, Keyring, and DB
    "argon2",
    "keyring",
    "keyring.backends.Windows",
    "keyring.backends.macOS",
    "sqlalchemy",
    "sqlite3",
    "supabase",
    "postgrest",
    "gotrue",
    
    # Backend application modules
    "backend",
    "backend.paths",
    "backend.config",
    "backend.api_client",
    "backend.audio_service",
    "backend.auth_service",
    "backend.camera_ownership",
    "backend.camera_service",
    "backend.content_data",
    "backend.content_service",
    "backend.credential_store",
    "backend.dashboard_service",
    "backend.leaderboard_service",
    "backend.media_service",
    "backend.minigame_service",
    "backend.model_service",
    "backend.progress_sync",
    "backend.quiz_service",
    "backend.recognition_engine",
    "backend.recognition_labels",
    "backend.security",
    "backend.session_state",
    "backend.sync_service",
    "backend.sync_supabase",
    "backend.training_config",
    "backend.word_landmarks",
    "backend.database",
    "backend.database.models",
    "backend.database.repository",
    "backend.database.session",
    "backend.database.init_db",
    "backend.api.auth_client_distributed",
    
    # Screens
    "screens",
    "screens.app_controller",
    "screens.camera_access",
    "screens.camera_preview",
    "screens.camera_setup",
    "screens.dialogs",
    "screens.image_card",
    "screens.loading",
    "screens.media_player",
    "screens.navigation",
    "screens.startup",
    "screens.hover_bounce",
    "screens.auth.common",
    "screens.auth.login",
    "screens.auth.register",
    "screens.auth.password_visibility",
    "screens.dashboard.dashboard",
    "screens.dashboard.leaderboard",
    "screens.lessons.lesson_ui_components",
    "screens.lessons.alphabet.alphabet_lesson",
    "screens.lessons.spelling.spell_lesson",
    "screens.lessons.words.word_lesson",
    "screens.main_menu.main_menu",
    "screens.main_menu.module_select",
    "screens.main_menu.lesson_select",
    "screens.main_menu.alphabet_menu",
    "screens.main_menu.spell_select",
    "screens.main_menu.word_menu",
    "screens.minigames.common",
    "screens.minigames.minigame_select",
    "screens.minigames.minigame_ui_components",
    "screens.minigames.fingerspell_quest",
    "screens.minigames.sign_sprint",
    "screens.minigames.sign_detective",
    "screens.quizzes.module_quiz",
]

# Targeted exclusions to keep package well under 1 GB:
excludes = [
    # Heavy unused Qt6 components (~300 MB savings)
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtTest",
    "PySide6.QtSensors",
    "PySide6.QtPositioning",
    "PySide6.QtCharts",
    
    # Unused ML & scientific libraries (~500 MB savings)
    "jax",
    "jaxlib",
    "scipy",
    "matplotlib",
    "tensorboard",
    "boto3",
    "botocore",
    "s3transfer",
    
    # Development tools
    "IPython",
    "jupyter",
    "tkinter",
    "unittest",
    "pytest",
]

a = Analysis(
    [str(senyasabi_root / "main.py")],
    pathex=[str(senyasabi_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SenyaSabi_Demo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(senyasabi_root / "resources" / "img" / "ui" / "senyasabi_logo.png") if (senyasabi_root / "resources" / "img" / "ui" / "senyasabi_logo.png").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SenyaSabi_Demo",
)

# On macOS, generate a proper .app bundle with camera permission strings
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="SenyaSabi_Demo.app",
        icon=str(senyasabi_root / "resources" / "img" / "ui" / "senyasabi_logo.png") if (senyasabi_root / "resources" / "img" / "ui" / "senyasabi_logo.png").exists() else None,
        bundle_identifier="com.senyasabi.demo",
        info_plist={
            "NSCameraUsageDescription": "SenyaSabi requires camera access for sign language recognition during lessons and minigames.",
            "NSMicrophoneUsageDescription": "SenyaSabi does not require microphone access.",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSHighResolutionCapable": "True",
        },
    )
