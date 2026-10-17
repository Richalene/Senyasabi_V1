"""Explicit global/module game context and the learner's navigation regressions."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QPushButton
from backend import auth_service
from backend.content_service import MODULE_CODES, get_words_for_module
from backend.minigame_service import (
    CONFIG, GameSession, MinigameContext, get_all_minigame_words, letters,
)
from screens.app_controller import AppController


def appropriate_words(kind, words):
    if kind in ("sprint", "quest"):
        maximum = 12 if kind == "sprint" else 14
        return [word for word in words if len(letters(word)) <= maximum]
    return list(words)


class MinigameContentScopeTests(unittest.TestCase):
    def test_global_words_use_all_ten_content_modules_and_exclude_alphabet(self):
        expected = [word for code in MODULE_CODES for word in get_words_for_module(code)]
        self.assertEqual(len(MODULE_CODES), 10)
        self.assertEqual(len(expected), 105)
        self.assertEqual(get_all_minigame_words(), expected)
        self.assertFalse(set(expected) & set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

    def test_global_sessions_have_complete_appropriate_pool_for_each_game(self):
        words = get_all_minigame_words()
        for kind in CONFIG:
            with self.subTest(kind=kind):
                session = GameSession(kind, rounds=200, scope="global")
                expected = appropriate_words(kind, words)
                self.assertEqual(session.scope, "global")
                self.assertIsNone(session.module_code)
                self.assertEqual(session.context, MinigameContext("global", None))
                self.assertEqual(list(session.pool), expected)
                self.assertCountEqual(session.words, expected)

    def test_module_sessions_never_fall_back_to_global_and_alphabet_still_works(self):
        for module_code in ("food", "greeting", "alphabet"):
            allowed = get_words_for_module(module_code)
            for kind in CONFIG:
                with self.subTest(module_code=module_code, kind=kind):
                    session = GameSession(kind, rounds=200, module_code=module_code, scope="module")
                    self.assertEqual(session.scope, "module")
                    self.assertEqual(session.module_code, module_code)
                    self.assertEqual(list(session.pool), appropriate_words(kind, allowed))
                    self.assertCountEqual(session.words, appropriate_words(kind, allowed))
        self.assertEqual(set(get_words_for_module("alphabet")), set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))

    def test_inconsistent_scope_and_module_are_rejected(self):
        for scope, module_code in (("global", "food"), ("module", None), ("invalid", None)):
            with self.subTest(scope=scope, module_code=module_code):
                with self.assertRaises(ValueError):
                    MinigameContext(scope, module_code)
                with self.assertRaises(ValueError):
                    GameSession("sprint", scope=scope, module_code=module_code)

    def test_older_direct_game_callers_keep_their_intended_scope(self):
        self.assertEqual(GameSession("sprint").scope, "global")
        module = GameSession("sprint", module_code="food")
        self.assertEqual(module.context, MinigameContext("module", "food"))


class MinigameNavigationScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        authenticated = patch.object(auth_service, "get_current_user", return_value={"user_id": "scope-uat"})
        authenticated.start()
        self.addCleanup(authenticated.stop)
        # Scope/navigation checks never open hardware or load recognition models.
        self.camera_gate = patch(
            "screens.camera_access.request_camera",
            side_effect=lambda parent, ready, cancelled, **kwargs: cancelled(),
        )
        self.camera_gate.start()
        self.addCleanup(self.camera_gate.stop)
        self.controller = AppController()
        self.controller.show_main_menu()
        self.only(self.controller.main_menu)

    def tearDown(self):
        self.controller.shutdown()
        for window in self.app.topLevelWidgets():
            window.close()
            window.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def only(self, screen):
        self.app.processEvents()
        self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])

    def open_module_from_menu(self, module_code):
        c = self.controller
        c.main_menu.ui.btnStartLearning.click()
        self.only(c.module_map)
        node = next(button for button in c.module_map.buttons
                    if button.property("module_code").casefold() == module_code)
        node.click()
        self.only(c.module_lessons)
        self.assertEqual(c.module_lessons.module_code, module_code)

    def module_menu_button(self, name):
        return self.controller.module_lessons._ui.findChild(QPushButton, name)

    def assert_game_context(self, kind, scope, module_code):
        selector = self.controller.minigames
        self.only(selector)
        game = selector.game
        self.assertIsNotNone(game)
        for subject in (selector, game, game.session):
            self.assertEqual(subject.scope, scope)
            self.assertEqual(subject.module_code, module_code)
        words = get_all_minigame_words() if scope == "global" else get_words_for_module(module_code)
        self.assertEqual(list(game.session.pool), appropriate_words(kind, words))
        self.assertTrue(set(game.session.words) <= set(words))
        return game

    def test_main_menu_opens_three_global_games_without_a_module(self):
        c = self.controller
        c.main_menu.ui.btnMinigames.click()
        hub = c.minigames
        self.only(hub)
        self.assertIsNone(c.module_map)
        self.assertIsNone(c.selected_module)
        self.assertEqual(hub.scope, "global")
        self.assertIsNone(hub.module_code)
        self.assertIs(hub.stack.currentWidget(), hub.menu)
        self.assertEqual(set(hub.game_buttons), {"sprint", "quest", "detective"})
        self.assertEqual(len(hub.menu.findChildren(QPushButton)), 4)
        for kind, (title, difficulty, _) in CONFIG.items():
            self.assertIn(title, hub.game_buttons[kind].text())
            self.assertIn(difficulty, hub.game_buttons[kind].text())
        hub.back_button.click()
        self.only(c.main_menu)

    def test_food_back_to_main_then_minigames_ignores_food_and_preserves_learning_state(self):
        c = self.controller
        self.open_module_from_menu("food")
        self.module_menu_button("backBtn").click()
        self.only(c.module_map)
        c.module_map.back_button.click()
        self.only(c.main_menu)
        c.main_menu.ui.btnMinigames.click()
        self.only(c.minigames)
        self.assertIs(c.minigames.stack.currentWidget(), c.minigames.menu)
        self.assertEqual(c.minigames.scope, "global")
        self.assertIsNone(c.minigames.module_code)
        self.assertEqual(c.selected_module, "food")

    def test_global_sprint_back_returns_to_global_hub_then_main_menu(self):
        c = self.controller
        c.main_menu.ui.btnMinigames.click()
        c.minigames.game_buttons["sprint"].click()
        game = self.assert_game_context("sprint", "global", None)
        self.assertTrue(game.countdown.isActive())
        game.back_button.click()
        self.only(c.minigames)
        self.assertIsNone(c.minigames.game)
        self.assertFalse(game.countdown.isActive())
        self.assertIs(c.minigames.stack.currentWidget(), c.minigames.menu)
        c.minigames.back_button.click()
        self.only(c.main_menu)

    def test_food_sprint_back_uses_the_captured_module_hub(self):
        c = self.controller
        self.open_module_from_menu("food")
        c.module_lessons.game_buttons["sprint"].click()
        game = self.assert_game_context("sprint", "module", "food")
        # A later learning selection must not alter an active game's return target.
        c.selected_module = "greeting"
        game.back_button.click()
        self.only(c.module_lessons)
        self.assertEqual(c.module_lessons.module_code, "food")
        self.assertEqual(c.selected_module, "food")
        self.assertIsNone(c.minigames.game)

    def test_greeting_detective_then_global_detective_does_not_inherit_greeting(self):
        c = self.controller
        self.open_module_from_menu("greeting")
        c.module_lessons.game_buttons["detective"].click()
        game = self.assert_game_context("detective", "module", "greeting")
        game.back_button.click()
        self.only(c.module_lessons)
        self.module_menu_button("menuBtn").click()
        self.only(c.main_menu)
        c.main_menu.ui.btnMinigames.click()
        c.minigames.game_buttons["detective"].click()
        game = self.assert_game_context("detective", "global", None)
        self.assertGreater(len(game.session.pool), len(get_words_for_module("greeting")))
        game.back_button.click()
        self.only(c.minigames)
        self.assertEqual(c.selected_module, "greeting")

    def test_repeated_global_module_switches_include_all_games_and_alphabet(self):
        c = self.controller
        for _ in range(2):
            for module_code, kind in (("food", "sprint"), ("greeting", "detective"), ("alphabet", "quest")):
                with self.subTest(module_code=module_code, kind=kind):
                    self.open_module_from_menu(module_code)
                    c.module_lessons.game_buttons[kind].click()
                    game = self.assert_game_context(kind, "module", module_code)
                    game.back_button.click()
                    self.only(c.module_lessons)
                    self.assertEqual(c.module_lessons.module_code, module_code)
                    self.module_menu_button("menuBtn").click()
                    self.only(c.main_menu)
                    c.main_menu.ui.btnMinigames.click()
                    c.minigames.game_buttons[kind].click()
                    game = self.assert_game_context(kind, "global", None)
                    game.back_button.click()
                    self.only(c.minigames)
                    self.assertIsNone(c.minigames.game)
                    self.assertEqual(c.selected_module, module_code)
                    c.minigames.back_button.click()
                    self.only(c.main_menu)


if __name__ == "__main__":
    unittest.main()
