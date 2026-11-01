Running 21 test suites...

Running test_audio_service.py... PASS
Running test_auth.py... PASS
Running test_auth_loading.py... PASS
Running test_auth_token_handoff.py... PASS
Running test_camera_preview.py... FAIL
--- STDOUT ---

--- STDERR ---
.qt.qpa.fonts: Populating font family aliases took 79 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
Unknown property transform
Unknown property transform
Unknown property transform
Inference worker diagnostic mode SENYASABI_DIAG_NO_INFERENCE=disabled
Word lesson cleanup: reason=test caller=test_all_five_camera_screens_present_frames_through_shared_component:233
[DIAG] SignVideoPlayer.release: enter (has_player=False, has_audio=False, has_video=False)
[DIAG] SignVideoPlayer.release: exit
E[DIAG] SignVideoPlayer.release: enter (has_player=False, has_audio=False, has_video=False)
[DIAG] SignVideoPlayer.release: exit
EUnknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
........
======================================================================
ERROR: test_all_five_camera_screens_present_frames_through_shared_component (senyasabi.tests.test_camera_preview.CameraPreviewTests.test_all_five_camera_screens_present_frames_through_shared_component)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_camera_preview.py", line 236, in test_all_five_camera_screens_present_frames_through_shared_component
    quest = FingerSpellQuest(module_code='greeting')
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/fingerspell_quest.py", line 358, in __init__
    self.session = GameSession("quest", rounds=5, module_code=module_code, scope=scope)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 78, in __init__
    else get_words_for_module(self.module_code))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 61, in get_words_for_module
    return module_words(module_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 264, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 253, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 245, in get_module
    raise ValueError(f"Unknown module: {module_code}")
ValueError: Unknown module: greeting

======================================================================
ERROR: test_all_five_camera_screens_present_frames_through_shared_component (senyasabi.tests.test_camera_preview.CameraPreviewTests.test_all_five_camera_screens_present_frames_through_shared_component)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_camera_preview.py", line 29, in tearDown
    window.close()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/fingerspell_quest.py", line 490, in closeEvent
    self.stop()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/fingerspell_quest.py", line 482, in stop
    self.game_view.stop_activity()
    ^^^^^^^^^^^^^^
AttributeError: Error calling Python override of QWidget::closeEvent(): 'FingerSpellQuest' object has no attribute 'game_view'

----------------------------------------------------------------------
Ran 10 tests in 1.029s

FAILED (errors=2)

Running test_camera_setup.py... FAIL
--- STDOUT ---

--- STDERR ---
Camera capture released (owner=SignRecognitionEngine, error=<Mock name='mock().error' id='5012193696'>, caller=recognition_engine.py:close_camera:212 <- recognition_engine.py:close:238<- test_camera_setup.py:test_both_recognition_engines_reopen_the_shared_selected_camera:191)
[DIAG] CategoryRecognitionEngine.close: enter (has_capture=True, has_preprocessor=True)
[DIAG] CategoryRecognitionEngine.close: before capture.release()
Camera capture released (owner=CategoryRecognitionEngine, error=<Mock name='mock().error' id='5012194176'>, caller=model_service.py:close:294 <- test_camera_setup.py:test_both_recognition_engines_reopen_the_shared_selected_camera:191 <- case.py:_callTestMethod:589)
[DIAG] CategoryRecognitionEngine.close: after capture.release()
[DIAG] CategoryRecognitionEngine.close: before recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: after recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: before preprocessor.close()
[DIAG] CategoryRecognitionEngine.close: after preprocessor.close()
[DIAG] CategoryRecognitionEngine.close: exit
[DIAG] CategoryRecognitionEngine.close: enter (has_capture=False, has_preprocessor=False)
[DIAG] CategoryRecognitionEngine.close: before recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: after recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: exit
Camera capture released (owner=SignRecognitionEngine, error=<Mock name='mock().error' id='5011979536'>, caller=recognition_engine.py:close_camera:212 <- recognition_engine.py:close:238<- test_camera_setup.py:test_both_recognition_engines_reopen_the_shared_selected_camera:191)
[DIAG] CategoryRecognitionEngine.close: enter (has_capture=True, has_preprocessor=True)
[DIAG] CategoryRecognitionEngine.close: before capture.release()
Camera capture released (owner=CategoryRecognitionEngine, error=<Mock name='mock().error' id='5012193696'>, caller=model_service.py:close:294 <- test_camera_setup.py:test_both_recognition_engines_reopen_the_shared_selected_camera:191 <- case.py:_callTestMethod:589)
[DIAG] CategoryRecognitionEngine.close: after capture.release()
[DIAG] CategoryRecognitionEngine.close: before recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: after recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: before preprocessor.close()
[DIAG] CategoryRecognitionEngine.close: after preprocessor.close()
[DIAG] CategoryRecognitionEngine.close: exit
[DIAG] CategoryRecognitionEngine.close: enter (has_capture=False, has_preprocessor=False)
[DIAG] CategoryRecognitionEngine.close: before recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: after recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: exit
Camera capture released (owner=SignRecognitionEngine, error=<Mock name='mock().error' id='5012195616'>, caller=recognition_engine.py:close_camera:212 <- recognition_engine.py:close:238<- test_camera_setup.py:test_both_recognition_engines_reopen_the_shared_selected_camera:191)
[DIAG] CategoryRecognitionEngine.close: enter (has_capture=True, has_preprocessor=True)
[DIAG] CategoryRecognitionEngine.close: before capture.release()
Camera capture released (owner=CategoryRecognitionEngine, error=<Mock name='mock().error' id='5012196192'>, caller=model_service.py:close:294 <- test_camera_setup.py:test_both_recognition_engines_reopen_the_shared_selected_camera:191 <- case.py:_callTestMethod:589)
[DIAG] CategoryRecognitionEngine.close: after capture.release()
[DIAG] CategoryRecognitionEngine.close: before recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: after recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: before preprocessor.close()
[DIAG] CategoryRecognitionEngine.close: after preprocessor.close()
[DIAG] CategoryRecognitionEngine.close: exit
[DIAG] CategoryRecognitionEngine.close: enter (has_capture=False, has_preprocessor=False)
[DIAG] CategoryRecognitionEngine.close: before recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: after recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: exit
.qt.qpa.fonts: Populating font family aliases took 92 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
EUnknown property transform
This plugin does not support propagateSizeHints()
Camera capture released (owner=CameraSetupDialog, error=<Mock name='mock.error' id='5249009808'>, caller=camera_setup.py:stop_preview:226 <- camera_setup.py:closeEvent:234 <- test_camera_setup.py:test_close_during_preview_releases_and_does_not_save:127)
.This plugin does not support propagateSizeHints()
Camera capture released (owner=CameraSetupDialog, error=<Mock name='mock.error' id='5249689568'>, caller=camera_setup.py:<lambda>:168 <- loading.py:discard:36 <- loading.py:run:31)
.EUnknown property transform
.This plugin does not support propagateSizeHints()
Camera preview unavailable: SECRET_TECHNICAL_TRACEBACK
.This plugin does not support propagateSizeHints()
.This plugin does not support propagateSizeHints()
.Camera capture released (owner=CameraSetupTests, error=<Mock name='mock.error' id='5249895504'>, caller=test_camera_setup.py:test_numeric_fallback_is_explicit_and_centralized:171 <- case.py:_callTestMethod:589 <- case.py:run:634)
..This plugin does not support propagateSizeHints()
Camera capture released (owner=CameraSetupDialog, error=<Mock name='mock.error' id='5249694176'>, caller=camera_setup.py:stop_preview:226 <- camera_setup.py:save:210 <- test_camera_setup.py:test_preview_save_release_then_activity_uses_same_device:109)
Camera capture released (owner=object, error=<Mock name='mock().error' id='5249692112'>, caller=test_camera_setup.py:test_preview_save_release_then_activity_uses_same_device:119 <- case.py:_callTestMethod:589 <- case.py:run:634)
.[DIAG] _QtCapture.release: enter (thread.isRunning=False)
[DIAG] _QtCapture.release: before thread.wait(1500)
[DIAG] _QtCapture.release: after thread.wait(1500) -> returned=True, thread.isRunning=False
Camera capture released (owner=CameraSetupTests, error='Device busy', caller=camera_service.py:open_capture:285 <- test_camera_setup.py:test_qt_camera_start_failure_releases_lease:266 <- case.py:_callTestMethod:589)
.QRhi *(anonymous namespace)::ThreadLocalRhiHolder::ensureRhi(QRhi::Implementation) : No RHI backend. Using CPU conversion.
[DIAG] _QtCapture.release: enter (thread.isRunning=True)
[DIAG] _QtCapture.release: before stop_requested.emit()
[DIAG] _QtCapture.release: after stop_requested.emit()
[DIAG] _QtCapture.release: before thread.wait(1500)
[DIAG] _QtCapture.release: after thread.wait(1500) -> returned=True, thread.isRunning=False
.QRhi *(anonymous namespace)::ThreadLocalRhiHolder::ensureRhi(QRhi::Implementation) : No RHI backend. Using CPU conversion.
.Camera capture released (owner=CameraSetupTests, error=<Mock name='mock.error' id='5248687360'>, caller=test_camera_setup.py:test_repeated_failed_reads_release_capture_once:160 <- case.py:_callTestMethod:589 <- case.py:run:634)
.EUnknown property transform

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
Ran 17 tests in 2.328s

FAILED (errors=3)

Running test_dashboard.py... PASS
Running test_data_loading.py... PASS
Running test_leaderboard.py... PASS
Running test_leaderboard_data.py... PASS
Running test_loading.py... PASS
Running test_minigame_scope.py... FAIL
--- STDOUT ---

--- STDERR ---
FFFF.EEqt.qpa.fonts: Populating font family aliases took 87 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
EUnknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
EUnknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
FUnknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 229, in open_module
    self.show_module_choices(code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 242, in show_module_choices
    self.module_lessons = LessonSelectWidget(module_code=self.selected_module)
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/lesson_select.py", line 95, in __init__
    self.set_module(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/lesson_select.py", line 138, in set_module
    btn.setToolTip(lessons[idx]["title"])
                   ~~~~~~~~~~~~^^^^^^^^^
TypeError: 'LessonRecord' object is not subscriptable
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
ETraceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 229, in open_module
    self.show_module_choices(code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 242, in show_module_choices
    self.module_lessons = LessonSelectWidget(module_code=self.selected_module)
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/lesson_select.py", line 95, in __init__
    self.set_module(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/lesson_select.py", line 138, in set_module
    btn.setToolTip(lessons[idx]["title"])
                   ~~~~~~~~~~~~^^^^^^^^^
TypeError: 'LessonRecord' object is not subscriptable
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
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
FETraceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 229, in open_module
    self.show_module_choices(code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/app_controller.py", line 249, in show_module_choices
    self.module_lessons.set_module(self.selected_module)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/main_menu/lesson_select.py", line 138, in set_module
    btn.setToolTip(lessons[idx]["title"])
                   ~~~~~~~~~~~~^^^^^^^^^
TypeError: 'LessonRecord' object is not subscriptable
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
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
F
======================================================================
ERROR: test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (senyasabi.tests.test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 50, in test_module_sessions_never_fall_back_to_global_and_alphabet_still_works
    allowed = get_words_for_module(module_code)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 264, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 253, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 245, in get_module
    raise ValueError(f"Unknown module: {module_code}")
ValueError: Unknown module: survival

======================================================================
ERROR: test_older_direct_game_callers_keep_their_intended_scope (senyasabi.tests.test_minigame_scope.MinigameContentScopeTests.test_older_direct_game_callers_keep_their_intended_scope)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 70, in test_older_direct_game_callers_keep_their_intended_scope
    module = GameSession("sprint", module_code="survival")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 78, in __init__
    else get_words_for_module(self.module_code))
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/minigame_service.py", line 61, in get_words_for_module
    return module_words(module_code)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 264, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 253, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 245, in get_module
    raise ValueError(f"Unknown module: {module_code}")
ValueError: Unknown module: survival

======================================================================
ERROR: test_days_back_to_main_then_minigames_ignores_days_and_preserves_learning_state (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_days_back_to_main_then_minigames_ignores_days_and_preserves_learning_state)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 153, in test_days_back_to_main_then_minigames_ignores_days_and_preserves_learning_state
    self.open_module_from_menu("basic_communication")
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 111, in open_module_from_menu
    node = next(button for button in c.module_map.buttons
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
StopIteration

======================================================================
ERROR: test_days_sprint_back_uses_the_captured_module_hub (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_days_sprint_back_uses_the_captured_module_hub)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 181, in test_days_sprint_back_uses_the_captured_module_hub
    self.open_module_from_menu("basic_communication")
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 111, in open_module_from_menu
    node = next(button for button in c.module_map.buttons
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
StopIteration

======================================================================
ERROR: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='basic_communication', kind='sprint')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 214, in test_repeated_global_module_switches_include_all_games_and_alphabet
    self.open_module_from_menu(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 111, in open_module_from_menu
    node = next(button for button in c.module_map.buttons
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
StopIteration

======================================================================
ERROR: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='basic_communication', kind='sprint')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 214, in test_repeated_global_module_switches_include_all_games_and_alphabet
    self.open_module_from_menu(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 111, in open_module_from_menu
    node = next(button for button in c.module_map.buttons
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
StopIteration

======================================================================
FAIL: test_global_sessions_have_complete_appropriate_pool_for_each_game (senyasabi.tests.test_minigame_scope.MinigameContentScopeTests.test_global_sessions_have_complete_appropriate_pool_for_each_game) (kind='sprint')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 45, in test_global_sessions_have_complete_appropriate_pool_for_each_game
    self.assertEqual(list(session.pool), expected)
AssertionError: Lists differ: ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SI[555 chars]BER'] != ['1', '2', '3', '4', '5', '6', '7', '8', '9[531 chars]ber']

First differing element 0:
'ONE'
'1'

Diff is 1546 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_global_sessions_have_complete_appropriate_pool_for_each_game (senyasabi.tests.test_minigame_scope.MinigameContentScopeTests.test_global_sessions_have_complete_appropriate_pool_for_each_game) (kind='quest')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 45, in test_global_sessions_have_complete_appropriate_pool_for_each_game
    self.assertEqual(list(session.pool), expected)
AssertionError: Lists differ: ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SI[632 chars]BER'] != ['1', '2', '3', '4', '5', '6', '7', '8', '9[609 chars]ber']

First differing element 0:
'ONE'
'1'

Diff is 1725 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_global_sessions_have_complete_appropriate_pool_for_each_game (senyasabi.tests.test_minigame_scope.MinigameContentScopeTests.test_global_sessions_have_complete_appropriate_pool_for_each_game) (kind='detective')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 45, in test_global_sessions_have_complete_appropriate_pool_for_each_game
    self.assertEqual(list(session.pool), expected)
AssertionError: Lists differ: ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SI[632 chars]BER'] != ['1', '2', '3', '4', '5', '6', '7', '8', '9[609 chars]ber']

First differing element 0:
'ONE'
'1'

Diff is 1725 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_global_words_use_all_ten_content_modules_and_exclude_alphabet (senyasabi.tests.test_minigame_scope.MinigameContentScopeTests.test_global_words_use_all_ten_content_modules_and_exclude_alphabet)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 31, in test_global_words_use_all_ten_content_modules_and_exclude_alphabet
    self.assertEqual(len(MODULE_CODES), 5)
AssertionError: 6 != 5

======================================================================
FAIL: test_global_sprint_back_returns_to_global_hub_then_main_menu (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_global_sprint_back_returns_to_global_hub_then_main_menu)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 169, in test_global_sprint_back_returns_to_global_hub_then_main_menu
    game = self.assert_game_context("sprint", "global", None)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 129, in assert_game_context
    self.assertEqual(list(game.session.pool), appropriate_words(kind, words))
AssertionError: Lists differ: ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SI[555 chars]BER'] != ['1', '2', '3', '4', '5', '6', '7', '8', '9[531 chars]ber']

First differing element 0:
'ONE'
'1'

Diff is 1546 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_greeting_detective_then_global_detective_does_not_inherit_greeting (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_greeting_detective_then_global_detective_does_not_inherit_greeting)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 194, in test_greeting_detective_then_global_detective_does_not_inherit_greeting
    self.open_module_from_menu("number")
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 114, in open_module_from_menu
    self.only(c.module_lessons)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.main_menu.module_select.ModuleSe[35 chars]a80>] != [None]

First differing element 0:
<screens.main_menu.module_select.ModuleSelectWidget(0x8099e4000) at 0x128ecea80>
None

- [<screens.main_menu.module_select.ModuleSelectWidget(0x8099e4000) at 0x128ecea80>]
+ [None]

======================================================================
FAIL: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='number', kind='detective')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 214, in test_repeated_global_module_switches_include_all_games_and_alphabet
    self.open_module_from_menu(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 114, in open_module_from_menu
    self.only(c.module_lessons)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.main_menu.module_select.ModuleSe[35 chars]f40>] != [None]

First differing element 0:
<screens.main_menu.module_select.ModuleSelectWidget(0x8099e6d80) at 0x129738f40>
None

- [<screens.main_menu.module_select.ModuleSelectWidget(0x8099e6d80) at 0x129738f40>]
+ [None]

======================================================================
FAIL: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='alphabet', kind='quest')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 224, in test_repeated_global_module_switches_include_all_games_and_alphabet
    game = self.assert_game_context(kind, "global", None)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 129, in assert_game_context
    self.assertEqual(list(game.session.pool), appropriate_words(kind, words))
AssertionError: Lists differ: ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SI[632 chars]BER'] != ['1', '2', '3', '4', '5', '6', '7', '8', '9[609 chars]ber']

First differing element 0:
'ONE'
'1'

Diff is 1725 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='number', kind='detective')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 214, in test_repeated_global_module_switches_include_all_games_and_alphabet
    self.open_module_from_menu(module_code)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 114, in open_module_from_menu
    self.only(c.module_lessons)
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 105, in only
    self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])
AssertionError: Lists differ: [<screens.main_menu.module_select.ModuleSelectWidget(0x8099e6[16 chars]f40>] != [<screens.main_menu.lesson_select.LessonSelectWidget(0x808024[16 chars]f40>]

First differing element 0:
<screens.main_menu.module_select.ModuleSelectWidget(0x8099e6d80) at 0x129738f40>
<screens.main_menu.lesson_select.LessonSelectWidget(0x808024540) at 0x12975bf40>

- [<screens.main_menu.module_select.ModuleSelectWidget(0x8099e6d80) at 0x129738f40>]
?                     ----          ^ ^^^^                 -----             ^^

+ [<screens.main_menu.lesson_select.LessonSelectWidget(0x808024540) at 0x12975bf40>]
?                       ++++        ^^^^ ^                   +++++           ^^


======================================================================
FAIL: test_repeated_global_module_switches_include_all_games_and_alphabet (senyasabi.tests.test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet) (module_code='alphabet', kind='quest')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 224, in test_repeated_global_module_switches_include_all_games_and_alphabet
    game = self.assert_game_context(kind, "global", None)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_minigame_scope.py", line 129, in assert_game_context
    self.assertEqual(list(game.session.pool), appropriate_words(kind, words))
AssertionError: Lists differ: ['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SI[632 chars]BER'] != ['1', '2', '3', '4', '5', '6', '7', '8', '9[609 chars]ber']

First differing element 0:
'ONE'
'1'

Diff is 1725 characters long. Set self.maxDiff to None to see it.

----------------------------------------------------------------------
Ran 11 tests in 3.302s

FAILED (failures=10, errors=6)

Running test_navigation.py... PASS
Running test_navigation_assets.py... PASS
Running test_progress_sync.py... FAIL
--- STDOUT ---

--- STDERR ---
EProgress sync failed: (sqlite3.IntegrityError) FOREIGN KEY constraint failed
[SQL: INSERT INTO lesson_progress (user_id, lesson_id, completion_percentage, status, last_accessed, completed_at, time_spent_seconds, client_updated_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)]
[parameters: ('00000000000000000000000000000007', 999, 0.0, 'Not Started', None, None, 0, '2026-11-01 01:48:31.119669', '2026-11-01 01:48:31.119670')]
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
F....EEEEE.......<frozen importlib._bootstrap>:488: DeprecationWarning: Type google._upb._message.MessageMapContainer uses PyType_Spec with a metaclass that has custom tp_new. This is deprecated and will no longer be allowed in Python 3.14.
<frozen importlib._bootstrap>:488: DeprecationWarning: Type google._upb._message.ScalarMapContainer uses PyType_Spec with a metaclass that has custom tp_new. This is deprecated and will no longer be allowed in Python 3.14.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1793497730.509324  662654 gl_context.cc:357] GL version: 2.1 (2.1 Metal - 90.5), renderer: Apple M1
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
W0000 00:00:1793497730.531893  663066 inference_feedback_manager.cc:114] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1793497730.554341  663066 inference_feedback_manager.cc:114] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
I0000 00:00:1793497730.556125  662654 gl_context.cc:357] GL version: 2.1 (2.1 Metal - 90.5), renderer: Apple M1
W0000 00:00:1793497730.627530  663074 inference_feedback_manager.cc:114] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1793497730.642190  663075 inference_feedback_manager.cc:114] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
F
======================================================================
ERROR: test_bundled_and_manifest_paths (senyasabi.tests.test_resources.MediaTests.test_bundled_and_manifest_paths)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 101, in test_bundled_and_manifest_paths
    self.assertEqual(self.service.resolve_sign_video("days", "bread").local_path, path)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 72, in resolve_sign_video
    raise ValueError(f"Unknown sign: {module_code}/{sign_code}")
ValueError: Unknown sign: days/bread

======================================================================
ERROR: test_cache_precedence_and_remote_metadata_retained (senyasabi.tests.test_resources.MediaTests.test_cache_precedence_and_remote_metadata_retained)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 112, in test_cache_precedence_and_remote_metadata_retained
    media = self.service.resolve_sign_video("days", "bread")
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 72, in resolve_sign_video
    raise ValueError(f"Unknown sign: {module_code}/{sign_code}")
ValueError: Unknown sign: days/bread

======================================================================
ERROR: test_invalid_manifest_value_does_not_crash_or_mask_bundled_video (senyasabi.tests.test_resources.MediaTests.test_invalid_manifest_value_does_not_crash_or_mask_bundled_video)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 136, in test_invalid_manifest_value_does_not_crash_or_mask_bundled_video
    self.assertTrue(self.service.resolve_sign_video("days", "bread").available)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 72, in resolve_sign_video
    raise ValueError(f"Unknown sign: {module_code}/{sign_code}")
ValueError: Unknown sign: days/bread

======================================================================
ERROR: test_missing_keeps_logical_identity (senyasabi.tests.test_resources.MediaTests.test_missing_keeps_logical_identity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 91, in test_missing_keeps_logical_identity
    media = self.service.resolve_sign_video("days", "bread")
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 72, in resolve_sign_video
    raise ValueError(f"Unknown sign: {module_code}/{sign_code}")
ValueError: Unknown sign: days/bread

======================================================================
ERROR: test_unavailable_repository_and_invalid_manifest (senyasabi.tests.test_resources.MediaTests.test_unavailable_repository_and_invalid_manifest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 124, in test_unavailable_repository_and_invalid_manifest
    self.assertFalse(self.service.resolve_sign_video("days", "bread").available)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/media_service.py", line 72, in resolve_sign_video
    raise ValueError(f"Unknown sign: {module_code}/{sign_code}")
ValueError: Unknown sign: days/bread

======================================================================
FAIL: test_105_signs_and_module_scoped_games_quizzes (senyasabi.tests.test_resources.ContentTests.test_105_signs_and_module_scoped_games_quizzes)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 29, in test_105_signs_and_module_scoped_games_quizzes
    self.assertEqual(sum(len(get_signs_for_module(code)) for code in MODULE_CODES), 50)
AssertionError: 62 != 50

======================================================================
FAIL: test_missing_does_not_load_tensorflow_or_legacy (senyasabi.tests.test_resources.ModelTests.test_missing_does_not_load_tensorflow_or_legacy)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_resources.py", line 163, in test_missing_does_not_load_tensorflow_or_legacy
    with self.assertRaises(ValueError):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 18 tests in 18.880s

FAILED (failures=2, errors=5)

Running test_schema_drift.py... PASS
Running test_startup.py... PASS
Running test_ui_polish.py... FAIL
--- STDOUT ---

--- STDERR ---
.qt.qpa.fonts: Populating font family aliases took 79 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
QWidget::mapTo(): parent must be in parent hierarchy
.EEE
======================================================================
ERROR: test_quiz_long_sequences_reflow_without_losing_answer (senyasabi.tests.test_ui_polish.UiPolishTests.test_quiz_long_sequences_reflow_without_losing_answer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_ui_polish.py", line 80, in test_quiz_long_sequences_reflow_without_losing_answer
    quiz = ModuleQuiz('relationships')
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/quizzes/module_quiz.py", line 165, in __init__
    self.session = QuizSession(self.module_code)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/quiz_service.py", line 32, in __init__
    self.definition = get_quiz(module_code)
                      ^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/quiz_service.py", line 22, in get_quiz
    get_signs_for_module(code)  # Validate; never widen to another module.
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 253, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 245, in get_module
    raise ValueError(f"Unknown module: {module_code}")
ValueError: Unknown module: relationships

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
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 264, in get_words_for_module
    return [sign.label for sign in get_signs_for_module(module_code)]
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 253, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 245, in get_module
    raise ValueError(f"Unknown module: {module_code}")
ValueError: Unknown module: greeting

======================================================================
ERROR: test_sprint_playback_and_back_controls_remain_reachable_at_600_height (senyasabi.tests.test_ui_polish.UiPolishTests.test_sprint_playback_and_back_controls_remain_reachable_at_600_height)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_ui_polish.py", line 27, in tearDown
    window.close()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/sign_sprint.py", line 515, in closeEvent
    self.stop()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/screens/minigames/sign_sprint.py", line 506, in stop
    self.game_view.countdown_timer.stop()
    ^^^^^^^^^^^^^^
AttributeError: Error calling Python override of QWidget::closeEvent(): 'SignSprint' object has no attribute 'game_view'

----------------------------------------------------------------------
Ran 4 tests in 0.391s

FAILED (errors=3)

Running test_word_recognition.py... FAIL
--- STDOUT ---

--- STDERR ---
..[DIAG] CategoryRecognitionEngine.close: enter (has_capture=True, has_preprocessor=True)
[DIAG] CategoryRecognitionEngine.close: before capture.release()
[DIAG] CategoryRecognitionEngine.close: after capture.release()
[DIAG] CategoryRecognitionEngine.close: before recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: after recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: before preprocessor.close()
[DIAG] CategoryRecognitionEngine.close: after preprocessor.close()
[DIAG] CategoryRecognitionEngine.close: exit
[DIAG] CategoryRecognitionEngine.close: enter (has_capture=False, has_preprocessor=False)
[DIAG] CategoryRecognitionEngine.close: before recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: after recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: exit
.[DIAG] CategoryRecognitionEngine.close: enter (has_capture=True, has_preprocessor=True)
[DIAG] CategoryRecognitionEngine.close: before capture.release()
[DIAG] CategoryRecognitionEngine.close: after capture.release()
[DIAG] CategoryRecognitionEngine.close: before recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: after recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: before preprocessor.close()
[DIAG] CategoryRecognitionEngine.close: after preprocessor.close()
[DIAG] CategoryRecognitionEngine.close: exit
[DIAG] CategoryRecognitionEngine.close: enter (has_capture=False, has_preprocessor=False)
[DIAG] CategoryRecognitionEngine.close: before recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: after recognizer.reset()
[DIAG] CategoryRecognitionEngine.close: exit
..............E
======================================================================
ERROR: test_recognition_canonicalization_preserves_display_and_sign_code (senyasabi.tests.test_word_recognition.TrainingParityTests.test_recognition_canonicalization_preserves_display_and_sign_code)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_word_recognition.py", line 49, in test_recognition_canonicalization_preserves_display_and_sign_code
    sign = next(sign for sign in get_signs_for_module('survival') if 'UNDERSTAND' in sign.label and 'DON' in sign.label)
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 253, in get_signs_for_module
    return list(get_module(module_code).signs)
                ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/backend/content_service.py", line 245, in get_module
    raise ValueError(f"Unknown module: {module_code}")
ValueError: Unknown module: survival

----------------------------------------------------------------------
Ran 18 tests in 0.110s

FAILED (errors=1)

Running test_uat_flow.py... FAIL
--- STDOUT ---

--- STDERR ---
....Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
qt.qpa.fonts: Populating font family aliases took 78 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
API unreachable (GET /api/v1/leaderboard?board_code=all_time&limit=100): HTTPConnectionPool(host='127.0.0.1', port=8000): Max retries exceeded with url: /api/v1/leaderboard?board_code=all_time&limit=100 (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=8000): Failed to establish a new connection: [Errno 61] Connection refused"))
.Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
Unknown property transform
FingerSpell Quest camera unavailable: Camera unavailable. Check permission/device and retry.
..FEUnknown property transform
EUnknown property transform
EUnknown property transform
EUnknown property transform
EUnknown property transform
EUnknown property transform
EUnknown property transform

======================================================================
ERROR: test_alphabet_camera_close_on_navigation_and_reopen (senyasabi.tests.test_uat_flow.UatFlowTests.test_alphabet_camera_close_on_navigation_and_reopen)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 224, in test_alphabet_camera_close_on_navigation_and_reopen
    self.login()
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 62, in login
    self.controller.login.dev_button.click()
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'LoginScreen' object has no attribute 'dev_button'

======================================================================
ERROR: test_alphabet_unavailable_camera_and_hide_cleanup (senyasabi.tests.test_uat_flow.UatFlowTests.test_alphabet_unavailable_camera_and_hide_cleanup)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 208, in test_alphabet_unavailable_camera_and_hide_cleanup
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
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 182, in test_sprint_and_detective_module_scoping_and_lifecycle
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
  File "/Users/louezetheianilicirsaldua/Documents/GitHub/Senyasabi_V1/senyasabi/tests/test_uat_flow.py", line 403, in test_real_application_fullscreen_keys_and_aspect_ratio
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
AssertionError: 1 != 0 : qt.qpa.fonts: Populating font family aliases took 78 ms. Replace uses of missing font family "Sans Serif" with one that exists to avoid this cost. 
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
Ran 15 tests in 4.282s

FAILED (failures=1, errors=7)


==========================================
Summary: 13/21 test suites passed.
Failed test suites: ['test_camera_preview.py', 'test_camera_setup.py', 'test_minigame_scope.py', 'test_progress_sync.py', 'test_resources.py', 'test_ui_polish.py', 'test_word_recognition.py', 'test_uat_flow.py']