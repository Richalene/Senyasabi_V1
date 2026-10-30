# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for SenyaSabi Desktop Application."""
import os
import sys
from pathlib import Path

block_cipher = None

# Base path for SenyaSabi source code
senyasabi_root = Path(__file__).resolve().parent if "senyasabi" in str(Path(__file__).resolve().parent.name) else (Path(__file__).resolve().parent / "senyasabi")
if not senyasabi_root.exists():
    senyasabi_root = Path(".").resolve()

# Bundled data directories
datas = [
    (str(senyasabi_root / "resources" / "data"), "resources/data"),
    (str(senyasabi_root / "resources" / "models"), "resources/models"),
    (str(senyasabi_root / "resources" / "font"), "resources/font"),
    (str(senyasabi_root / "resources" / "img"), "resources/img"),
    (str(senyasabi_root / "resources" / "styles"), "resources/styles"),
    (str(senyasabi_root / "resources" / "videos"), "resources/videos"),
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
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "cv2",
    "mediapipe",
    "tensorflow",
    "keras",
    "argon2",
    "sqlalchemy",
    "sqlite3",
    "backend",
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
    "backend.progress_sync",
    "backend.sync_service",
    "backend.training_config",
    "backend.word_landmarks",
    "backend.database",
    "backend.database.models",
    "backend.database.repository",
    "backend.database.session",
    "backend.database.init_db",
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
    "screens.auth.common",
    "screens.auth.login",
    "screens.auth.register",
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
    "screens.minigames.common",
    "screens.quizzes.module_quiz",
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
    excludes=["tkinter", "IPython", "jupyter"],
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
    name="SenyaSabi",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(senyasabi_root / "resources" / "img" / "ui" / "logo.png") if (senyasabi_root / "resources" / "img" / "ui" / "logo.png").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SenyaSabi",
)

