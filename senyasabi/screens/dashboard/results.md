Running 21 test suites...

Running test_audio_service.py... PASS
Running test_auth.py... PASS
Running test_auth_loading.py... PASS
Running test_auth_token_handoff.py... PASS
Running test_camera_preview.py... FAIL
--- STDOUT ---

--- STDERR ---
.qt.qpa.fonts: Populating font family aliases took 83 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
EEUnknown property transform
Unknown property transform
Unknown property transform
........
======================================================================
ERROR: test_all_five_camera_screens_present_frames_through_shared_component (senyasabi.tests.test_camera_preview.CameraPreviewTests.test_all_five_camera_screens_present_frames_through_shared_component)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_camera_preview.py", line 221, in test_all_five_camera_screens_present_frames_through_shared_component
    for screen in (AlphabetLessonWidget(letters=['A']),
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/lessons/alphabet/alphabet_lesson.py", line 100, in __init__
    self._refresh_ui()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/lessons/alphabet/alphabet_lesson.py", line 170, in _refresh_ui
    self._load_ref_image(letter)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/lessons/alphabet/alphabet_lesson.py", line 141, in _load_ref_image
    self.video.set_sign("alphabet", letter.lower())
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/media_player.py", line 80, in set_sign
    self.media = resolve_sign_video(module_code, sign_code)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 109, in resolve_sign_video
    return _service.resolve_sign_video(module_code, sign_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 70, in resolve_sign_video
    sign = get_sign(module_code, sign_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 255, in get_sign
    for sign in get_signs_for_module(module_code):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_all_five_camera_screens_present_frames_through_shared_component (senyasabi.tests.test_camera_preview.CameraPreviewTests.test_all_five_camera_screens_present_frames_through_shared_component)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_camera_preview.py", line 29, in tearDown
    window.close()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/lessons/alphabet/alphabet_lesson.py", line 407, in closeEvent
    self._cleanup_resources()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/lessons/alphabet/alphabet_lesson.py", line 385, in _cleanup_resources
    self._cancel_camera_setup()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/camera_access.py", line 148, in _cancel_camera_setup
    dialog, self._camera_dialog = self._camera_dialog, None
                                  ^^^^^^^^^^^^^^^^^^^
AttributeError: Error calling Python override of QWidget::closeEvent(): 'AlphabetLessonWidget' object has no attribute '_camera_dialog'. Did you mean: '_camera_failed'?

----------------------------------------------------------------------
Ran 10 tests in 0.817s

FAILED (errors=2)

Running test_camera_setup.py... FAIL
--- STDOUT ---

--- STDERR ---
.qt.qpa.fonts: Populating font family aliases took 88 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
EUnknown property transform
This plugin does not support propagateSizeHints()
.This plugin does not support propagateSizeHints()
.EUnknown property transform
.This plugin does not support propagateSizeHints()
Camera preview unavailable: SECRET_TECHNICAL_TRACEBACK
.This plugin does not support propagateSizeHints()
.This plugin does not support propagateSizeHints()
...This plugin does not support propagateSizeHints()
..QRhi *(anonymous namespace)::ThreadLocalRhiHolder::ensureRhi(QRhi::Implementation) : No RHI backend. Using CPU conversion.
.QRhi *(anonymous namespace)::ThreadLocalRhiHolder::ensureRhi(QRhi::Implementation) : No RHI backend. Using CPU conversion.
..EUnknown property transform

======================================================================
ERROR: test_cancel_onboarding_then_back_keeps_session_and_module (senyasabi.tests.test_camera_setup.CameraSetupTests.test_cancel_onboarding_then_back_keeps_session_and_module)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_camera_setup.py", line 217, in test_cancel_onboarding_then_back_keeps_session_and_module
    c.dev_login()
    ^^^^^^^^^^^
AttributeError: 'AppController' object has no attribute 'dev_login'

======================================================================
ERROR: test_configured_gate_is_automatic_and_settings_are_reachable (senyasabi.tests.test_camera_setup.CameraSetupTests.test_configured_gate_is_automatic_and_settings_are_reachable)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_camera_setup.py", line 204, in test_configured_gate_is_automatic_and_settings_are_reachable
    c.dev_login()
    ^^^^^^^^^^^
AttributeError: 'AppController' object has no attribute 'dev_login'

======================================================================
ERROR: test_repeated_game_and_quiz_routes_do_not_reset_active_windows (senyasabi.tests.test_camera_setup.CameraSetupTests.test_repeated_game_and_quiz_routes_do_not_reset_active_windows)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_camera_setup.py", line 289, in test_repeated_game_and_quiz_routes_do_not_reset_active_windows
    c.dev_login()
    ^^^^^^^^^^^
AttributeError: 'AppController' object has no attribute 'dev_login'

----------------------------------------------------------------------
Ran 17 tests in 2.289s

FAILED (errors=3)

Running test_dashboard.py... PASS
Running test_data_loading.py... PASS
Running test_leaderboard.py... PASS
Running test_leaderboard_data.py... PASS
Running test_loading.py... PASS
Running test_minigame_scope.py... FAIL
--- STDOUT ---

--- STDERR ---
EE.EEqt.qpa.fonts: Populating font family aliases took 106 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 216, in show_module_map
    from screens.main_menu.module_select import ModuleSelectWidget
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 46, in <module>
    MODULE_NODES = _build_nodes()
                   ^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 30, in _build_nodes
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
                     ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
FUnknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 216, in show_module_map
    from screens.main_menu.module_select import ModuleSelectWidget
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 46, in <module>
    MODULE_NODES = _build_nodes()
                   ^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 30, in _build_nodes
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
                     ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
FUnknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/minigame_select.py", line 110, in <lambda>
    self.menu.sprint_requested.connect(lambda: self.open_game("sprint"))
                                               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/minigame_select.py", line 143, in open_game
    self.game = factory(self.stack, scope=context.scope, module_code=context.module_code)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/sign_sprint.py", line 380, in __init__
    self.session = GameSession("sprint", rounds=5, module_code=module_code, scope=scope)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 77, in __init__
    labels = (get_all_minigame_words() if self.scope == "global"
              ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 56, in get_all_minigame_words
    return [word for code in MODULE_CODES for word in module_words(code)]
                                                      ^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 249, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
FUnknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 216, in show_module_map
    from screens.main_menu.module_select import ModuleSelectWidget
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 46, in <module>
    MODULE_NODES = _build_nodes()
                   ^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 30, in _build_nodes
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
                     ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
FUnknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
.Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 216, in show_module_map
    from screens.main_menu.module_select import ModuleSelectWidget
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 46, in <module>
    MODULE_NODES = _build_nodes()
                   ^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 30, in _build_nodes
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
                     ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
FTraceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 216, in show_module_map
    from screens.main_menu.module_select import ModuleSelectWidget
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 46, in <module>
    MODULE_NODES = _build_nodes()
                   ^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 30, in _build_nodes
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
                     ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
FTraceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 216, in show_module_map
    from screens.main_menu.module_select import ModuleSelectWidget
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 46, in <module>
    MODULE_NODES = _build_nodes()
                   ^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 30, in _build_nodes
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
                     ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
FTraceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 216, in show_module_map
    from screens.main_menu.module_select import ModuleSelectWidget
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 46, in <module>
    MODULE_NODES = _build_nodes()
                   ^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 30, in _build_nodes
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
                     ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
FTraceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 216, in show_module_map
    from screens.main_menu.module_select import ModuleSelectWidget
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 46, in <module>
    MODULE_NODES = _build_nodes()
                   ^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 30, in _build_nodes
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
                     ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
FTraceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 216, in show_module_map
    from screens.main_menu.module_select import ModuleSelectWidget
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 46, in <module>
    MODULE_NODES = _build_nodes()
                   ^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 30, in _build_nodes
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
                     ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
F
======================================================================
ERROR: test_global_sessions_have_complete_appropriate_pool_for_each_game (senyasabi.tests.test_minigame_scope.MinigameContentScopeTests.test_global_sessions_have_complete_appropriate_pool_for_each_game)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 37, in test_global_sessions_have_complete_appropriate_pool_for_each_game
    words = get_all_minigame_words()
            ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 56, in get_all_minigame_words
    return [word for code in MODULE_CODES for word in module_words(code)]
                                                      ^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 249, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_global_words_use_all_ten_content_modules_and_exclude_alphabet (senyasabi.tests.test_minigame_scope.MinigameContentScopeTests.test_global_words_use_all_ten_content_modules_and_exclude_alphabet)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 30, in test_global_words_use_all_ten_content_modules_and_exclude_alphabet
    expected = [word for code in MODULE_CODES for word in get_words_for_module(code)]
                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 249, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (senyasabi.tests.test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 50, in test_module_sessions_never_fall_back_to_global_and_alphabet_still_works
    allowed = get_words_for_module(module_code)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 249, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_older_direct_game_callers_keep_their_intended_scope (senyasabi.tests.test_minigame_scope.MinigameContentScopeTests.test_older_direct_game_callers_keep_their_intended_scope)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 69, in test_older_direct_game_callers_keep_their_intended_scope
    self.assertEqual(GameSession("sprint").scope, "global")
                     ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 77, in __init__
    labels = (get_all_minigame_words() if self.scope == "global"
              ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 56, in get_all_minigame_words
    return [word for code in MODULE_CODES for word in module_words(code)]
                                                      ^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 249, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
FAIL: test_food_back_to_main_then_minigames_ignores_food_and_preserves_learning_state (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_food_back_to_main_then_minigames_ignores_food_and_preserves_learning_state)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 153, in test_food_back_to_main_then_minigames_ignores_food_and_preserves_learning_state
    self.open_module_from_menu("survival")
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 110, in open_module_from_menu
    self.only(c.module_map)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.dashboard.dashboard.DashboardWin[41 chars]380>] != [None]

First differing element 0:
<screens.dashboard.dashboard.DashboardWin[40 chars]e380>
None

- [<screens.dashboard.dashboard.DashboardWindow(0xaba909880, name="main") at 0x12c9ce380>]
+ [None]

======================================================================
FAIL: test_food_sprint_back_uses_the_captured_module_hub (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_food_sprint_back_uses_the_captured_module_hub)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 181, in test_food_sprint_back_uses_the_captured_module_hub
    self.open_module_from_menu("survival")
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 110, in open_module_from_menu
    self.only(c.module_map)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.dashboard.dashboard.DashboardWin[41 chars]000>] != [None]

First differing element 0:
<screens.dashboard.dashboard.DashboardWin[40 chars]1000>
None

- [<screens.dashboard.dashboard.DashboardWindow(0xaba4ea840, name="main") at 0x12cef1000>]
+ [None]

======================================================================
FAIL: test_global_sprint_back_returns_to_global_hub_then_main_menu (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_global_sprint_back_returns_to_global_hub_then_main_menu)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 169, in test_global_sprint_back_returns_to_global_hub_then_main_menu
    game = self.assert_game_context("sprint", "global", None)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 124, in assert_game_context
    self.assertIsNotNone(game)
AssertionError: unexpectedly None

======================================================================
FAIL: test_greeting_detective_then_global_detective_does_not_inherit_greeting (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_greeting_detective_then_global_detective_does_not_inherit_greeting)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 194, in test_greeting_detective_then_global_detective_does_not_inherit_greeting
    self.open_module_from_menu("greeting")
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 110, in open_module_from_menu
    self.only(c.module_map)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.dashboard.dashboard.DashboardWin[41 chars]9c0>] != [None]

First differing element 0:
<screens.dashboard.dashboard.DashboardWin[40 chars]49c0>
None

- [<screens.dashboard.dashboard.DashboardWindow(0xaba9ffb80, name="main") at 0x12cfd49c0>]
+ [None]

======================================================================
FAIL: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='survival', kind='sprint')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 214, in test_repeated_global_module_switches_include_all_games_and_alphabet
    self.open_module_from_menu(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 110, in open_module_from_menu
    self.only(c.module_map)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.dashboard.dashboard.DashboardWin[41 chars]880>] != [None]

First differing element 0:
<screens.dashboard.dashboard.DashboardWin[40 chars]8880>
None

- [<screens.dashboard.dashboard.DashboardWindow(0xaba4e8fc0, name="main") at 0x12d038880>]
+ [None]

======================================================================
FAIL: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='greeting', kind='detective')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 214, in test_repeated_global_module_switches_include_all_games_and_alphabet
    self.open_module_from_menu(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 110, in open_module_from_menu
    self.only(c.module_map)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.dashboard.dashboard.DashboardWin[41 chars]880>] != [None]

First differing element 0:
<screens.dashboard.dashboard.DashboardWin[40 chars]8880>
None

- [<screens.dashboard.dashboard.DashboardWindow(0xaba4e8fc0, name="main") at 0x12d038880>]
+ [None]

======================================================================
FAIL: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='alphabet', kind='quest')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 214, in test_repeated_global_module_switches_include_all_games_and_alphabet
    self.open_module_from_menu(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 110, in open_module_from_menu
    self.only(c.module_map)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.dashboard.dashboard.DashboardWin[41 chars]880>] != [None]

First differing element 0:
<screens.dashboard.dashboard.DashboardWin[40 chars]8880>
None

- [<screens.dashboard.dashboard.DashboardWindow(0xaba4e8fc0, name="main") at 0x12d038880>]
+ [None]

======================================================================
FAIL: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='survival', kind='sprint')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 214, in test_repeated_global_module_switches_include_all_games_and_alphabet
    self.open_module_from_menu(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 110, in open_module_from_menu
    self.only(c.module_map)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.dashboard.dashboard.DashboardWin[41 chars]880>] != [None]

First differing element 0:
<screens.dashboard.dashboard.DashboardWin[40 chars]8880>
None

- [<screens.dashboard.dashboard.DashboardWindow(0xaba4e8fc0, name="main") at 0x12d038880>]
+ [None]

======================================================================
FAIL: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='greeting', kind='detective')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 214, in test_repeated_global_module_switches_include_all_games_and_alphabet
    self.open_module_from_menu(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 110, in open_module_from_menu
    self.only(c.module_map)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.dashboard.dashboard.DashboardWin[41 chars]880>] != [None]

First differing element 0:
<screens.dashboard.dashboard.DashboardWin[40 chars]8880>
None

- [<screens.dashboard.dashboard.DashboardWindow(0xaba4e8fc0, name="main") at 0x12d038880>]
+ [None]

======================================================================
FAIL: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='alphabet', kind='quest')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 214, in test_repeated_global_module_switches_include_all_games_and_alphabet
    self.open_module_from_menu(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 110, in open_module_from_menu
    self.only(c.module_map)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.dashboard.dashboard.DashboardWin[41 chars]880>] != [None]

First differing element 0:
<screens.dashboard.dashboard.DashboardWin[40 chars]8880>
None

- [<screens.dashboard.dashboard.DashboardWindow(0xaba4e8fc0, name="main") at 0x12d038880>]
+ [None]

----------------------------------------------------------------------
Ran 11 tests in 3.441s

FAILED (failures=10, errors=4)

Running test_navigation.py... FAIL
--- STDOUT ---

--- STDERR ---
qt.qpa.fonts: Populating font family aliases took 115 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 216, in show_module_map
    from screens.main_menu.module_select import ModuleSelectWidget
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 46, in <module>
    MODULE_NODES = _build_nodes()
                   ^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/module_select.py", line 30, in _build_nodes
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
                     ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES
F
======================================================================
FAIL: test_authenticated_routes_reuse_windows_and_logout (senyasabi.tests.test_navigation.NavigationRoutingTests.test_authenticated_routes_reuse_windows_and_logout)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_navigation.py", line 36, in test_authenticated_routes_reuse_windows_and_logout
    self.assert_only(c.module_map)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_navigation.py", line 92, in assert_only
    self.assertEqual([w for w in self.app.topLevelWidgets() if w.isVisible()], [screen])
AssertionError: Lists differ: [<screens.dashboard.dashboard.DashboardWin[41 chars]500>] != [None]

First differing element 0:
<screens.dashboard.dashboard.DashboardWin[40 chars]4500>
None

- [<screens.dashboard.dashboard.DashboardWindow(0x72ddd7d40, name="main") at 0x113864500>]
+ [None]

----------------------------------------------------------------------
Ran 1 test in 1.207s

FAILED (failures=1)

Running test_navigation_assets.py... PASS
Running test_progress_sync.py... FAIL
--- STDOUT ---

--- STDERR ---
EProgress sync failed: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
[SQL: INSERT INTO lesson_progress (user_id, lesson_id, completion_percentage, status, last_accessed, completed_at, time_spent_seconds, client_updated_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)]
[parameters: ('00000000000000000000000000000007', 999, 0.0, 'Not Started', None, None, 0, '2026-10-31 13:49:41.152607', '2026-10-31 13:49:41.152608')]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
.EProgress sync failed: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
[SQL: INSERT INTO lesson_progress (user_id, lesson_id, completion_percentage, status, last_accessed, completed_at, time_spent_seconds, client_updated_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)]
[parameters: ('00000000000000000000000000000007', 1, 100.0, 'Completed', '2026-10-17 10:00:00.000000', '2026-10-17 10:00:00.000000', 300, '2026-10-17 10:00:00.000000', '2026-10-17 10:00:00.000000')]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
F
======================================================================
ERROR: test_apply_merges_rows_and_is_idempotent (senyasabi.tests.test_progress_sync.ProgressSyncTests.test_apply_merges_rows_and_is_idempotent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
sqlite3.IntegrityError: FOREIGN KEY constraint failed

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_progress_sync.py", line 76, in test_apply_merges_rows_and_is_idempotent
    counts = progress_sync.apply_snapshot(self.snapshot())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/progress_sync.py", line 68, in apply_snapshot
    db.flush()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 4353, in flush
    self._flush(objects)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 4488, in _flush
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 122, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 4449, in _flush
    flush_context.execute()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/unitofwork.py", line 465, in execute
    rec.execute(self)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/unitofwork.py", line 641, in execute
    util.preloaded.orm_persistence.save_obj(
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/persistence.py", line 94, in save_obj
    _emit_insert_statements(
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/persistence.py", line 1049, in _emit_insert_statements
    result = connection.execute(
             ^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1421, in execute
    return meth(
           ^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1643, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
[SQL: INSERT INTO lesson_progress (user_id, lesson_id, completion_percentage, status, last_accessed, completed_at, time_spent_seconds, client_updated_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)]
[parameters: ('00000000000000000000000000000007', 1, 100.0, 'Completed', '2026-10-17 10:00:00.000000', '2026-10-17 10:00:00.000000', 300, '2026-10-17 10:00:00.000000', '2026-10-17 10:00:00.000000')]
(Background on this error at: https://sqlalche.me/e/20/gkpj)

======================================================================
ERROR: test_server_value_updates_existing_row_without_deleting_others (senyasabi.tests.test_progress_sync.ProgressSyncTests.test_server_value_updates_existing_row_without_deleting_others)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
sqlite3.IntegrityError: FOREIGN KEY constraint failed

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_progress_sync.py", line 85, in test_server_value_updates_existing_row_without_deleting_others
    progress_sync.apply_snapshot(self.snapshot(pct=50))
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/progress_sync.py", line 68, in apply_snapshot
    db.flush()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 4353, in flush
    self._flush(objects)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 4488, in _flush
    with util.safe_reraise():
         ^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 122, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 4449, in _flush
    flush_context.execute()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/unitofwork.py", line 465, in execute
    rec.execute(self)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/unitofwork.py", line 641, in execute
    util.preloaded.orm_persistence.save_obj(
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/persistence.py", line 94, in save_obj
    _emit_insert_statements(
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/orm/persistence.py", line 1049, in _emit_insert_statements
    result = connection.execute(
             ^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1421, in execute
    return meth(
           ^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/sql/elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1643, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1848, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1988, in _exec_single_context
    self._handle_dbapi_exception(
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2365, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 1969, in _exec_single_context
    self.dialect.do_execute(
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 952, in do_execute
    cursor.execute(statement, parameters)
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
[SQL: INSERT INTO lesson_progress (user_id, lesson_id, completion_percentage, status, last_accessed, completed_at, time_spent_seconds, client_updated_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)]
[parameters: ('00000000000000000000000000000007', 1, 50.0, 'Completed', '2026-10-17 10:00:00.000000', '2026-10-17 10:00:00.000000', 300, '2026-10-17 10:00:00.000000', '2026-10-17 10:00:00.000000')]
(Background on this error at: https://sqlalche.me/e/20/gkpj)

======================================================================
FAIL: test_successful_pull_returns_true (senyasabi.tests.test_progress_sync.ProgressSyncTests.test_successful_pull_returns_true)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_progress_sync.py", line 107, in test_successful_pull_returns_true
    self.assertTrue(progress_sync.pull_user_progress())
AssertionError: False is not true

----------------------------------------------------------------------
Ran 4 tests in 0.143s

FAILED (failures=1, errors=2)

Running test_resources.py... FAIL
--- STDOUT ---

--- STDERR ---
E.EE.EEEEE.......Category model food unavailable: Recognition model not installed: missing best_landmark_model.keras.
.
======================================================================
ERROR: test_105_signs_and_module_scoped_games_quizzes (senyasabi.tests.test_resources.ContentTests.test_105_signs_and_module_scoped_games_quizzes)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 29, in test_105_signs_and_module_scoped_games_quizzes
    self.assertEqual(sum(len(get_signs_for_module(code)) for code in MODULE_CODES), 50)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 29, in <genexpr>
    self.assertEqual(sum(len(get_signs_for_module(code)) for code in MODULE_CODES), 50)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_quiz_scores_once_and_requires_answer_before_next (senyasabi.tests.test_resources.ContentTests.test_quiz_scores_once_and_requires_answer_before_next)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 52, in test_quiz_scores_once_and_requires_answer_before_next
    quiz = QuizSession("food", count=2)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/quiz_service.py", line 29, in __init__
    self.definition = get_quiz(module_code)
                      ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/quiz_service.py", line 19, in get_quiz
    module = get_module(code)                 # raises ValueError for unknown modules
             ^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_timer_pause_expiry_and_single_scoring (senyasabi.tests.test_resources.ContentTests.test_timer_pause_expiry_and_single_scoring)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 65, in test_timer_pause_expiry_and_single_scoring
    game = GameSession("sprint", rounds=2, module_code="food", clock=clock)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 78, in __init__
    else get_words_for_module(self.module_code))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 61, in get_words_for_module
    return module_words(module_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 249, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_bundled_and_manifest_paths (senyasabi.tests.test_resources.MediaTests.test_bundled_and_manifest_paths)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 101, in test_bundled_and_manifest_paths
    self.assertEqual(self.service.resolve_sign_video("food", "bread").local_path, path)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 70, in resolve_sign_video
    sign = get_sign(module_code, sign_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 255, in get_sign
    for sign in get_signs_for_module(module_code):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_cache_precedence_and_remote_metadata_retained (senyasabi.tests.test_resources.MediaTests.test_cache_precedence_and_remote_metadata_retained)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 112, in test_cache_precedence_and_remote_metadata_retained
    media = self.service.resolve_sign_video("food", "bread")
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 70, in resolve_sign_video
    sign = get_sign(module_code, sign_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 255, in get_sign
    for sign in get_signs_for_module(module_code):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_invalid_manifest_value_does_not_crash_or_mask_bundled_video (senyasabi.tests.test_resources.MediaTests.test_invalid_manifest_value_does_not_crash_or_mask_bundled_video)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 136, in test_invalid_manifest_value_does_not_crash_or_mask_bundled_video
    self.assertTrue(self.service.resolve_sign_video("food", "bread").available)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 70, in resolve_sign_video
    sign = get_sign(module_code, sign_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 255, in get_sign
    for sign in get_signs_for_module(module_code):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_missing_keeps_logical_identity (senyasabi.tests.test_resources.MediaTests.test_missing_keeps_logical_identity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 91, in test_missing_keeps_logical_identity
    media = self.service.resolve_sign_video("food", "bread")
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 70, in resolve_sign_video
    sign = get_sign(module_code, sign_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 255, in get_sign
    for sign in get_signs_for_module(module_code):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_unavailable_repository_and_invalid_manifest (senyasabi.tests.test_resources.MediaTests.test_unavailable_repository_and_invalid_manifest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 124, in test_unavailable_repository_and_invalid_manifest
    self.assertFalse(self.service.resolve_sign_video("food", "bread").available)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 70, in resolve_sign_video
    sign = get_sign(module_code, sign_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 255, in get_sign
    for sign in get_signs_for_module(module_code):
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

----------------------------------------------------------------------
Ran 18 tests in 0.035s

FAILED (errors=8)

Running test_schema_drift.py... PASS
Running test_startup.py... PASS
Running test_ui_polish.py... FAIL
--- STDOUT ---

--- STDERR ---
.qt.qpa.fonts: Populating font family aliases took 80 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
QWidget::mapTo(): parent must be in parent hierarchy
.EEE
======================================================================
ERROR: test_quiz_long_sequences_reflow_without_losing_answer (senyasabi.tests.test_ui_polish.UiPolishTests.test_quiz_long_sequences_reflow_without_losing_answer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_ui_polish.py", line 80, in test_quiz_long_sequences_reflow_without_losing_answer
    quiz = ModuleQuiz('relationships')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/quizzes/module_quiz.py", line 34, in __init__
    self.session = QuizSession(self.module_code)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/quiz_service.py", line 29, in __init__
    self.definition = get_quiz(module_code)
                      ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/quiz_service.py", line 19, in get_quiz
    module = get_module(code)                 # raises ValueError for unknown modules
             ^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_sprint_playback_and_back_controls_remain_reachable_at_600_height (senyasabi.tests.test_ui_polish.UiPolishTests.test_sprint_playback_and_back_controls_remain_reachable_at_600_height)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_ui_polish.py", line 65, in test_sprint_playback_and_back_controls_remain_reachable_at_600_height
    game = SignSprint(module_code='greeting')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/sign_sprint.py", line 380, in __init__
    self.session = GameSession("sprint", rounds=5, module_code=module_code, scope=scope)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 78, in __init__
    else get_words_for_module(self.module_code))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 61, in get_words_for_module
    return module_words(module_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 249, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_sprint_playback_and_back_controls_remain_reachable_at_600_height (senyasabi.tests.test_ui_polish.UiPolishTests.test_sprint_playback_and_back_controls_remain_reachable_at_600_height)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_ui_polish.py", line 27, in tearDown
    window.close()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/sign_sprint.py", line 514, in closeEvent
    self.stop()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/sign_sprint.py", line 506, in stop
    self.game_view.countdown_timer.stop()
    ^^^^^^^^^^^^^^
AttributeError: Error calling Python override of QWidget::closeEvent(): 'SignSprint' object has no attribute 'game_view'

----------------------------------------------------------------------
Ran 4 tests in 0.394s

FAILED (errors=3)

Running test_word_recognition.py... FAIL
--- STDOUT ---

--- STDERR ---
.................E
======================================================================
ERROR: test_recognition_canonicalization_preserves_display_and_sign_code (senyasabi.tests.test_word_recognition.TrainingParityTests.test_recognition_canonicalization_preserves_display_and_sign_code)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_word_recognition.py", line 49, in test_recognition_canonicalization_preserves_display_and_sign_code
    sign = next(sign for sign in get_signs_for_module('survival') if 'UNDERSTAND' in sign.label and 'DON' in sign.label)
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

----------------------------------------------------------------------
Ran 18 tests in 0.261s

FAILED (errors=1)

Running test_uat_flow.py... FAIL
--- STDOUT ---

--- STDERR ---
....API unreachable (GET /api/v1/leaderboard?board_code=all_time&limit=100): HTTPConnectionPool(host='127.0.0.1', port=8000): Max retries exceeded with url: /api/v1/leaderboard?board_code=all_time&limit=100 (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=8000): Failed to establish a new connection: [Errno 61] Connection refused"))
EEEE.Fqt.qpa.fonts: Populating font family aliases took 79 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
EUnknown property transform
EUnknown property transform
EUnknown property transform
EUnknown property transform
EUnknown property transform
EUnknown property transform
EUnknown property transform

======================================================================
ERROR: test_quest_tuning_top_prediction_cooldown_and_cleanup (senyasabi.tests.test_uat_flow.CameraAndLoadingTests.test_quest_tuning_top_prediction_cooldown_and_cleanup)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 257, in test_quest_tuning_top_prediction_cooldown_and_cleanup
    game = FingerSpellQuest(engine_factory=lambda **kwargs: engine, module_code="food")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/fingerspell_quest.py", line 358, in __init__
    self.session = GameSession("quest", rounds=5, module_code=module_code, scope=scope)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 78, in __init__
    else get_words_for_module(self.module_code))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 61, in get_words_for_module
    return module_words(module_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 249, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_quest_tuning_top_prediction_cooldown_and_cleanup (senyasabi.tests.test_uat_flow.CameraAndLoadingTests.test_quest_tuning_top_prediction_cooldown_and_cleanup)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 250, in tearDown
    widget.close()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/fingerspell_quest.py", line 489, in closeEvent
    self.stop()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/fingerspell_quest.py", line 482, in stop
    self.game_view.stop_activity()
    ^^^^^^^^^^^^^^
AttributeError: Error calling Python override of QWidget::closeEvent(): 'FingerSpellQuest' object has no attribute 'game_view'

======================================================================
ERROR: test_quest_unavailable_camera_and_retry (senyasabi.tests.test_uat_flow.CameraAndLoadingTests.test_quest_unavailable_camera_and_retry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 282, in test_quest_unavailable_camera_and_retry
    game = FingerSpellQuest(engine_factory=lambda **kwargs: engine, module_code="food")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/fingerspell_quest.py", line 358, in __init__
    self.session = GameSession("quest", rounds=5, module_code=module_code, scope=scope)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 78, in __init__
    else get_words_for_module(self.module_code))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 61, in get_words_for_module
    return module_words(module_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 249, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 238, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 227, in get_module
    for module in get_modules():
                  ^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 222, in get_modules
    return _repository.get_modules()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 203, in get_modules
    return list(_load_modules())
                ^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 172, in _load_modules
    raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
ValueError: Dataset module 'Survival Signs' has no code in DATASET_MODULE_CODES

======================================================================
ERROR: test_quest_unavailable_camera_and_retry (senyasabi.tests.test_uat_flow.CameraAndLoadingTests.test_quest_unavailable_camera_and_retry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 250, in tearDown
    widget.close()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/fingerspell_quest.py", line 489, in closeEvent
    self.stop()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/fingerspell_quest.py", line 482, in stop
    self.game_view.stop_activity()
    ^^^^^^^^^^^^^^
AttributeError: Error calling Python override of QWidget::closeEvent(): 'FingerSpellQuest' object has no attribute 'game_view'

======================================================================
ERROR: test_alphabet_camera_close_on_navigation_and_reopen (senyasabi.tests.test_uat_flow.UatFlowTests.test_alphabet_camera_close_on_navigation_and_reopen)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 223, in test_alphabet_camera_close_on_navigation_and_reopen
    self.login()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 62, in login
    self.controller.login.dev_button.click()
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'LoginScreen' object has no attribute 'dev_button'

======================================================================
ERROR: test_alphabet_unavailable_camera_and_hide_cleanup (senyasabi.tests.test_uat_flow.UatFlowTests.test_alphabet_unavailable_camera_and_hide_cleanup)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 207, in test_alphabet_unavailable_camera_and_hide_cleanup
    self.login()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 62, in login
    self.controller.login.dev_button.click()
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'LoginScreen' object has no attribute 'dev_button'

======================================================================
ERROR: test_dev_guard_and_session_not_persisted (senyasabi.tests.test_uat_flow.UatFlowTests.test_dev_guard_and_session_not_persisted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 68, in test_dev_guard_and_session_not_persisted
    with patch.object(login, "DEV_MODE", False):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/.pyenv/versions/3.12.13/lib/python3.12/unittest/mock.py", line 1467, in __enter__
    original, local = self.get_original()
                      ^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/.pyenv/versions/3.12.13/lib/python3.12/unittest/mock.py", line 1437, in get_original
    raise AttributeError(
AttributeError: <module 'screens.auth.login' from '/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/auth/login.py'> does not have the attribute 'DEV_MODE'

======================================================================
ERROR: test_missing_word_resources_quiz_and_all_back_routes (senyasabi.tests.test_uat_flow.UatFlowTests.test_missing_word_resources_quiz_and_all_back_routes)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 83, in test_missing_word_resources_quiz_and_all_back_routes
    self.login()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 62, in login
    self.controller.login.dev_button.click()
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'LoginScreen' object has no attribute 'dev_button'

======================================================================
ERROR: test_repeated_word_lessons_do_not_leave_hidden_windows (senyasabi.tests.test_uat_flow.UatFlowTests.test_repeated_word_lessons_do_not_leave_hidden_windows)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 134, in test_repeated_word_lessons_do_not_leave_hidden_windows
    self.login()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 62, in login
    self.controller.login.dev_button.click()
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'LoginScreen' object has no attribute 'dev_button'

======================================================================
ERROR: test_sprint_and_detective_module_scoping_and_lifecycle (senyasabi.tests.test_uat_flow.UatFlowTests.test_sprint_and_detective_module_scoping_and_lifecycle)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 181, in test_sprint_and_detective_module_scoping_and_lifecycle
    self.login()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 62, in login
    self.controller.login.dev_button.click()
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'LoginScreen' object has no attribute 'dev_button'

======================================================================
ERROR: test_word_recognition_uses_canonical_label_but_keeps_display_text (senyasabi.tests.test_uat_flow.UatFlowTests.test_word_recognition_uses_canonical_label_but_keeps_display_text)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 153, in test_word_recognition_uses_canonical_label_but_keeps_display_text
    self.login()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 62, in login
    self.controller.login.dev_button.click()
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'LoginScreen' object has no attribute 'dev_button'

======================================================================
FAIL: test_real_application_fullscreen_keys_and_aspect_ratio (senyasabi.tests.test_uat_flow.PresentationTests.test_real_application_fullscreen_keys_and_aspect_ratio)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 402, in test_real_application_fullscreen_keys_and_aspect_ratio
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
AssertionError: 1 != 0 : qt.qpa.fonts: Populating font family aliases took 79 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
Unknown property transform

================ CRITICAL CRASH ================
Traceback (most recent call last):
  File "<string>", line 18, in <module>
AttributeError: 'AppController' object has no attribute 'dev_login'

================================================
Traceback (most recent call last):
  File "<string>", line 18, in <module>
AttributeError: 'AppController' object has no attribute 'dev_login'


----------------------------------------------------------------------
Ran 15 tests in 4.392s

FAILED (failures=1, errors=11)


==========================================
Summary: 12/21 test suites passed.
Failed test suites: ['test_camera_preview.py', 'test_camera_setup.py', 'test_minigame_scope.py', 'test_navigation.py', 'test_progress_sync.py', 'test_resources.py', 'test_ui_polish.py', 'test_word_recognition.py', 'test_uat_flow.py']