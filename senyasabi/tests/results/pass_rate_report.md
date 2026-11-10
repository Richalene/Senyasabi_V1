# SenyaSabi evaluation - pass rates

Generated 2026-11-10 13:33:39

| Category | Total | Pass | Fail | Error | Skipped | Pass rate |
|---|---:|---:|---:|---:|---:|---:|
| Functional (Sec. 8) | 17 | 16 | 0 | 0 | 1 | **100.0%** |
| Input validation (Sec. 9) | 10 | 10 | 0 | 0 | 0 | **100.0%** |
| Database (Sec. 10) | 8 | 8 | 0 | 0 | 0 | **100.0%** |
| API / external services (Sec. 11) | 12 | 9 | 0 | 3 | 0 | **75.0%** |
| Performance (Sec. 12) | 10 | 8 | 1 | 0 | 1 | **88.9%** |
| Security (Sec. 13) | 17 | 16 | 1 | 0 | 0 | **94.1%** |
| Compatibility (Sec. 14) | 9 | 9 | 0 | 0 | 0 | **100.0%** |
| Usability / UI (Sec. 15) | 16 | 13 | 3 | 0 | 0 | **81.2%** |
| REG-001 Login | 15 | 13 | 2 | 0 | 0 | **86.7%** |
| REG-002 Registration | 13 | 11 | 2 | 0 | 0 | **84.6%** |
| REG-003 Database operations | 18 | 17 | 0 | 1 | 0 | **94.4%** |
| REG-004 Sign recognition & feedback | 45 | 36 | 3 | 6 | 0 | **80.0%** |
| REG-005 Minigames | 37 | 9 | 27 | 1 | 0 | **24.3%** |
| REG-006 Progress tracking | 16 | 16 | 0 | 0 | 0 | **100.0%** |

**Overall (new suites, excluding regression): 89/97 = 91.8%**

## Per test-case ID

| Category | ID | Result |
|---|---|---|
| Functional (Sec. 8) | TC-F-001 | PASS |
| Functional (Sec. 8) | TC-F-002 | PASS |
| Functional (Sec. 8) | TC-F-003 | PASS |
| Functional (Sec. 8) | TC-F-004 | PASS |
| Functional (Sec. 8) | TC-F-005 | PASS |
| Functional (Sec. 8) | TC-F-006 | PASS |
| Functional (Sec. 8) | TC-F-007 | PASS |
| Functional (Sec. 8) | TC-F-008 | PASS |
| Functional (Sec. 8) | TC-F-009 | PASS |
| Functional (Sec. 8) | TC-F-010 | PASS |
| Functional (Sec. 8) | TC-F-011 | PASS |
| Functional (Sec. 8) | TC-F-012 | PASS |
| Functional (Sec. 8) | TC-F-013 | PASS |
| Functional (Sec. 8) | TC-F-014 | PASS |
| Functional (Sec. 8) | TC-F-015 | SKIP |
| Functional (Sec. 8) | TC-F-016 | PASS |
| Input validation (Sec. 9) | IV-001 | PASS |
| Input validation (Sec. 9) | IV-002 | PASS |
| Input validation (Sec. 9) | IV-003 | PASS |
| Input validation (Sec. 9) | IV-004 | PASS |
| Input validation (Sec. 9) | IV-005 | PASS |
| Input validation (Sec. 9) | IV-006 | PASS |
| Input validation (Sec. 9) | IV-007 | PASS |
| Input validation (Sec. 9) | IV-008 | PASS |
| Database (Sec. 10) | DB-001 | PASS |
| Database (Sec. 10) | DB-002 | PASS |
| Database (Sec. 10) | DB-003 | PASS |
| Database (Sec. 10) | DB-004 | PASS |
| Database (Sec. 10) | DB-005 | PASS |
| Database (Sec. 10) | DB-006 | PASS |
| Database (Sec. 10) | DB-007 | PASS |
| Database (Sec. 10) | DB-008 | PASS |
| API / external services (Sec. 11) | API-001 | PASS |
| API / external services (Sec. 11) | API-002 | PASS |
| API / external services (Sec. 11) | API-003 | PASS |
| API / external services (Sec. 11) | API-004 | FAIL |
| API / external services (Sec. 11) | API-005 | PASS |
| API / external services (Sec. 11) | API-006 | PASS |
| API / external services (Sec. 11) | API-007 | PASS |
| API / external services (Sec. 11) | API-008 | FAIL |
| Performance (Sec. 12) | PT-001 | PASS |
| Performance (Sec. 12) | PT-002 | PASS |
| Performance (Sec. 12) | PT-003 | PASS |
| Performance (Sec. 12) | PT-004 | PASS |
| Performance (Sec. 12) | PT-005 | FAIL |
| Performance (Sec. 12) | PT-006 | PASS |
| Performance (Sec. 12) | PT-007 | SKIP |
| Security (Sec. 13) | SEC-001 | PASS |
| Security (Sec. 13) | SEC-002 | PASS |
| Security (Sec. 13) | SEC-003 | PASS |
| Security (Sec. 13) | SEC-004 | PASS |
| Security (Sec. 13) | SEC-005 | PASS |
| Security (Sec. 13) | SEC-006 | FAIL |
| Security (Sec. 13) | SEC-007 | PASS |
| Security (Sec. 13) | SEC-008 | PASS |
| Usability / UI (Sec. 15) | UI-001 | PASS |
| Usability / UI (Sec. 15) | UI-002 | FAIL |
| Usability / UI (Sec. 15) | UI-003 | PASS |
| Usability / UI (Sec. 15) | UI-004 | PASS |
| Usability / UI (Sec. 15) | UI-005 | PASS |
| Usability / UI (Sec. 15) | UI-006 | FAIL |
| Usability / UI (Sec. 15) | UI-007 | PASS |

## Failures and errors

- **API / external services (Sec. 11)** `test_external_services.LandmarkTests.test_api_004_model_returns_sign_and_confidence` - AttributeError: module 'cv2.dnn' has no attribute 'DictValue'
- **API / external services (Sec. 11)** `test_external_services.LandmarkTests.test_api_004_word_model_needs_24_frames_then_predicts` - AttributeError: module 'cv2.dnn' has no attribute 'DictValue'
- **API / external services (Sec. 11)** `test_external_services.ServiceFailureTests.test_api_008_alphabet_model_missing_file` - AttributeError: module 'cv2.dnn' has no attribute 'DictValue'
- **Performance (Sec. 12)** `test_performance.DatabasePerformanceTests.test_pt_005_continuous_use_is_stable` - AssertionError: 1355.419956 not less than 50 : memory grew by 1355.4 MB over 73030 frames
- **Security (Sec. 13)** `test_security.SecretHandlingTests.test_sec_006_api_errors_do_not_echo_raw_exceptions` - -  'main.py:134'] : Internal exception text (SQL, hosts) is returned to clients
- **Usability / UI (Sec. 15)** `test_usability_ui.ReadabilityTests.test_ui_002_back_to_lessons_white_on_green` - AssertionError: 2.9395688754965135 not greater than or equal to 3.0 : #FFFFFF on #8C9F3E = 2.94:1 (needs 3.0:1)
- **Usability / UI (Sec. 15)** `test_usability_ui.ReadabilityTests.test_ui_002_next_button_white_on_green` - AssertionError: 1.9701962235267558 not greater than or equal to 3.0 : #FFFFFF on #ACC412 = 1.97:1 (needs 3.0:1)
- **Usability / UI (Sec. 15)** `test_usability_ui.ResponsivenessTests.test_ui_006_minigame_scales_with_window` - AssertionError: 1820 not less than or equal to 1024 : (1024, 600)
- **REG-001 Login** `test_auth.NavigationTests.test_complete_flow` - + [<screens.auth.login.LoginScreen(0x71a3cc1c0) at 0x10bda32c0>]
- **REG-001 Login** `test_auth.NavigationTests.test_password_visibility_toggles_preserve_text` - AssertionError: 348 != 368
- **REG-002 Registration** `test_auth.NavigationTests.test_complete_flow` - + [<screens.auth.login.LoginScreen(0x71a3cc1c0) at 0x10bda32c0>]
- **REG-002 Registration** `test_auth.NavigationTests.test_password_visibility_toggles_preserve_text` - AssertionError: 348 != 368
- **REG-003 Database operations** `setUpClass (tests_backend_smoke.BackendSmoke)` - AttributeError: 'NoneType' object has no attribute 'content_version_id'
- **REG-004 Sign recognition & feedback** `test_word_recognition.TrainingParityTests.test_recognition_canonicalization_preserves_display_and_sign_code` - StopIteration
- **REG-004 Sign recognition & feedback** `test_camera_setup.CameraSetupTests.test_cancel_onboarding_then_back_keeps_session_and_module` - AttributeError: 'NoneType' object has no attribute '_camera_dialog'
- **REG-004 Sign recognition & feedback** `test_camera_setup.CameraSetupTests.test_configured_gate_is_automatic_and_settings_are_reachable` - AttributeError: 'NoneType' object has no attribute '_camera_dialog'
- **REG-004 Sign recognition & feedback** `test_camera_setup.CameraSetupTests.test_nothing_opens_until_explicit_setup_and_test` - AttributeError: 'PySide6.QtWidgets.QWidget' object has no attribute '_camera_dialog'
- **REG-004 Sign recognition & feedback** `test_camera_setup.CameraSetupTests.test_numeric_fallback_is_explicit_and_centralized` -   Actual: VideoCapture(3, 1200)
- **REG-004 Sign recognition & feedback** `test_camera_setup.CameraSetupTests.test_preview_save_release_then_activity_uses_same_device` - AssertionError: Timed out waiting for camera UI
- **REG-004 Sign recognition & feedback** `test_camera_setup.CameraSetupTests.test_qt_camera_start_failure_releases_lease` - AssertionError: "Device busy" does not match "Another SenyaSabi activity is still using the camera. Please retry."
- **REG-004 Sign recognition & feedback** `test_camera_setup.CameraSetupTests.test_repeated_failed_reads_release_capture_once` - backend.camera_service.CameraError: Another SenyaSabi activity is still using the camera. Please retry.
- **REG-004 Sign recognition & feedback** `test_camera_setup.CameraSetupTests.test_repeated_game_and_quiz_routes_do_not_reset_active_windows` - AttributeError: 'NoneType' object has no attribute 'game'
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_global_sessions_have_complete_appropriate_pool_for_each_game (kind='sprint')` - Diff is 1546 characters long. Set self.maxDiff to None to see it.
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_global_sessions_have_complete_appropriate_pool_for_each_game (kind='quest')` - Diff is 1725 characters long. Set self.maxDiff to None to see it.
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_global_sessions_have_complete_appropriate_pool_for_each_game (kind='detective')` - Diff is 1725 characters long. Set self.maxDiff to None to see it.
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (module_code='survival', kind='sprint')` - +  'Fast']
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (module_code='survival', kind='quest')` - Diff is 657 characters long. Set self.maxDiff to None to see it.
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (module_code='survival', kind='detective')` - Diff is 657 characters long. Set self.maxDiff to None to see it.
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (module_code='greeting', kind='sprint')` - +  'Fast']
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (module_code='greeting', kind='quest')` - Diff is 657 characters long. Set self.maxDiff to None to see it.
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (module_code='greeting', kind='detective')` - Diff is 657 characters long. Set self.maxDiff to None to see it.
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (module_code='basic_communication', kind='sprint')` - +  'Fast']
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (module_code='basic_communication', kind='quest')` - Diff is 657 characters long. Set self.maxDiff to None to see it.
- **REG-005 Minigames** `test_minigame_scope.MinigameContentScopeTests.test_module_sessions_never_fall_back_to_global_and_alphabet_still_works (module_code='basic_communication', kind='detective')` - Diff is 657 characters long. Set self.maxDiff to None to see it.
- **REG-005 Minigames** `test_minigame_scope.MinigameNavigationScopeTests.test_days_back_to_main_then_minigames_ignores_days_and_preserves_learning_state` - + [<screens.dashboard.dashboard.DashboardWindow(0x7da331f80, name="main") at 0x128fe2780>]
- **REG-005 Minigames** `test_minigame_scope.MinigameNavigationScopeTests.test_days_sprint_back_uses_the_captured_module_hub` - -  <screens.app_controller.MainWindowShell(0x7dc66c8c0) at 0x128fed400>]
- **REG-005 Minigames** `test_minigame_scope.MinigameNavigationScopeTests.test_global_sprint_back_returns_to_global_hub_then_main_menu` - -  <screens.app_controller.MainWindowShell(0x7dc66c8c0) at 0x128fed400>]
- **REG-005 Minigames** `test_minigame_scope.MinigameNavigationScopeTests.test_greeting_detective_then_global_detective_does_not_inherit_greeting` - -  <screens.app_controller.MainWindowShell(0x7dc66c1c0) at 0x1138786c0>]
- **REG-005 Minigames** `test_minigame_scope.MinigameNavigationScopeTests.test_main_menu_opens_three_global_games_without_a_module` - -  <screens.app_controller.MainWindowShell(0x7dc66c1c0) at 0x1138786c0>]
- **REG-005 Minigames** `test_minigame_scope.MinigameNavigationScopeTests.test_repeated_global_module_switches_include_all_games_and_alphabet` - -  <screens.app_controller.MainWindowShell(0x7dc66c1c0) at 0x1138786c0>]
- **REG-005 Minigames** `test_ui_polish.UiPolishTests.test_coming_soon_copy_wraps_and_next_lesson_is_optional` - AssertionError: False is not true
- **REG-005 Minigames** `test_ui_polish.UiPolishTests.test_dashboard_buttons_bounce_on_hover_and_restore_geometry` - AssertionError: 500 not greater than 500
- **REG-005 Minigames** `test_ui_polish.UiPolishTests.test_dashboard_primary_actions_are_tight_and_nonoverlapping` - AssertionError: -20 != 0
- **REG-005 Minigames** `test_ui_polish.UiPolishTests.test_dashboard_stats_load_survives_screen_hide` - AssertionError: False is not true
- **REG-005 Minigames** `test_ui_polish.UiPolishTests.test_fullscreen_persists_across_reused_screen_switches` - AssertionError
- **REG-005 Minigames** `test_ui_polish.UiPolishTests.test_home_stats_do_not_reload_on_same_user_screen_revisits` - Calls: [call(), call()].
- **REG-005 Minigames** `test_ui_polish.UiPolishTests.test_module_transition_uses_fireflies_without_a_full_window_overlay` - AssertionError: unexpectedly None
- **REG-005 Minigames** `test_ui_polish.UiPolishTests.test_quiz_long_sequences_reflow_without_losing_answer` - ValueError: Unknown module: relationships
- **REG-005 Minigames** `test_ui_polish.UiPolishTests.test_sprint_game_scales_with_window_size` - AssertionError: 1820 not less than or equal to 1200
- **REG-005 Minigames** `test_ui_polish.UiPolishTests.test_sprint_playback_and_back_controls_remain_reachable_at_600_height` - AssertionError: False is not true