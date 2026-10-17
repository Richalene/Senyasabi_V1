"""Render supplied navigation artwork and exercise its real Qt interactions."""
import hashlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QRect, QSize, QTimer, Qt
from PySide6.QtGui import QFontDatabase, QImage, QRegion
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from backend import auth_service, dashboard_service
from screens.dashboard.dashboard import DashboardWindow, StatisticsDashboardWindow
from screens.navigation import ASSETS, AssetButton, BackButton, SenyaSabiHeader
from screens.startup import FittedForm


class NavigationAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)
        # Windows' offscreen Qt plugin may not discover system fonts on its own.
        font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/segoeui.ttf"
        if font.is_file():
            QFontDatabase.addApplicationFont(str(font))

    def tearDown(self):
        for window in self.app.topLevelWidgets():
            window.close()
            window.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def render(self, widget):
        self.app.processEvents()
        image = QImage(widget.size(), QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        widget.render(image, QPoint(), QRegion(), QWidget.RenderFlag.DrawChildren)
        return image

    def alpha_bounds(self, image):
        coordinates = [(x, y) for y in range(image.height()) for x in range(image.width())
                       if image.pixelColor(x, y).alpha() > 32]
        self.assertTrue(coordinates, "The supplied PNG was not painted")
        xs, ys = zip(*coordinates)
        return QRect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)

    def wait_for_data(self, window):
        for _ in range(300):
            self.app.processEvents()
            if not window.loading.busy:
                return
            QTest.qWait(10)
        self.fail("Dashboard data did not finish loading")

    def test_buttons_preserve_png_transparency_aspect_and_original_bytes(self):
        names = ("streak-bg.png", "streak.png", "hamburger.png", "back-button.png")
        before = {name: hashlib.sha256((ASSETS / name).read_bytes()).digest() for name in names}
        for name, factory in (("hamburger.png", AssetButton), ("back-button.png", BackButton)):
            source = QImage(str(ASSETS / name))
            self.assertFalse(source.isNull())
            original_bounds = self.alpha_bounds(source)
            button = factory()
            self.assertIsInstance(button, QPushButton)
            self.assertEqual(button.cursor().shape(), Qt.CursorShape.PointingHandCursor)
            self.assertEqual(button.text(), "")
            for width, height in ((220, 96), (96, 220)):
                with self.subTest(asset=name, size=(width, height)):
                    button.resize(width, height)
                    image = self.render(button)
                    actual = self.alpha_bounds(image)
                    scale = min(width / source.width(), height / source.height())
                    expected_x = (width - source.width() * scale) / 2 + original_bounds.x() * scale
                    expected_y = (height - source.height() * scale) / 2 + original_bounds.y() * scale
                    self.assertAlmostEqual(actual.x(), expected_x, delta=2)
                    self.assertAlmostEqual(actual.y(), expected_y, delta=2)
                    self.assertAlmostEqual(actual.width(), original_bounds.width() * scale, delta=2)
                    self.assertAlmostEqual(actual.height(), original_bounds.height() * scale, delta=2)
                    self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
                    self.assertEqual(image.pixelColor(width - 1, height - 1).alpha(), 0)
        header = SenyaSabiHeader()
        header.set_streak_text("12 Days")
        self.render(header)
        self.assertEqual(before, {name: hashlib.sha256((ASSETS / name).read_bytes()).digest()
                                  for name in names})

    def test_ancestor_button_styles_cannot_restore_default_rectangular_chrome(self):
        parent = QWidget()
        parent.resize(240, 160)
        parent.setStyleSheet("QPushButton { background: #ff00ff; border: 8px solid #ff00ff; }")
        for factory in (AssetButton, BackButton):
            with self.subTest(button=factory.__name__):
                button = factory(parent=parent)
                button.resize(180, 110)
                image = self.render(button)
                self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
                self.assertFalse(any(image.pixelColor(x, y).name() == "#ff00ff"
                                     for x, y in ((0, 0), (2, 55), (90, 2), (179, 109))))

    def test_home_and_statistics_streaks_update_from_service_and_default_to_zero(self):
        user = {"user_id": "header-user", "display_name": "Sam"}
        for cls, refresh_name, label_name in (
                (DashboardWindow, "refresh_home_stats", "streakValue"),
                (StatisticsDashboardWindow, "refresh_stats", "lblCurrentStreak")):
            with self.subTest(screen=cls.__name__), \
                    patch.object(auth_service, "get_current_user", return_value=user):
                zero = dashboard_service.DefaultDashboardRepository().get_dashboard_stats(None)
                seven = dashboard_service.DefaultDashboardRepository().get_dashboard_stats(None)
                seven["streaks"]["current_streak"] = 7
                window = cls()
                label = getattr(window.ui, label_name)
                self.assertIs(label, window.header.streak_label)
                self.assertEqual(label.text(), "0 Days")
                with patch.object(dashboard_service, "get_dashboard_stats", side_effect=[zero, seven]) as service:
                    window.show()
                    self.wait_for_data(window)
                    self.assertEqual(label.text(), "0 Days")
                    getattr(window, refresh_name)()
                    self.wait_for_data(window)
                    self.assertEqual(label.text(), "7 Days")
                    self.assertEqual(service.call_count, 2)
                    service.assert_called_with("header-user")
                window.close()

    def test_header_follows_fitted_canvas_through_letterboxing_resize_and_fullscreen(self):
        host = QWidget()
        canvas = QSize(1920, 1080)
        host.resize(canvas)
        header = SenyaSabiHeader(host)
        header.anchor_to_canvas(canvas)
        host._fitted_form = FittedForm(host)
        host.show()

        def assert_anchor():
            self.app.processEvents()
            scale = min(host.width() / canvas.width(), host.height() / canvas.height())
            canvas_left = (host.width() - canvas.width() * scale) / 2
            canvas_top = (host.height() - canvas.height() * scale) / 2
            canvas_right = canvas_left + canvas.width() * scale
            self.assertAlmostEqual(header.x() + header.width(), canvas_right - 32 * scale, delta=1)
            self.assertAlmostEqual(header.y(), canvas_top + 16 * scale, delta=1)
            self.assertAlmostEqual(header.width(), 511 * scale, delta=1)
            self.assertAlmostEqual(header.streak.width() / header.menu_button.width(), 406 / 111, delta=.08)
            self.assertAlmostEqual(header.streak.geometry().center().y(),
                                   header.menu_button.geometry().center().y(),
                                   delta=max(2, header.height() * .06))
            self.assertGreater(header.menu_button.x(), header.streak.x())
            self.assertTrue(host.rect().contains(header.geometry()))

        for size in ((1920, 1080), (1200, 900), (1600, 700), (900, 700)):
            with self.subTest(size=size):
                host.resize(*size)
                assert_anchor()
        host.showFullScreen()
        self.assertTrue(host.isFullScreen())
        assert_anchor()

    def test_hamburger_opens_existing_menu_and_keeps_camera_and_logout_actions(self):
        window = DashboardWindow()
        with patch.object(auth_service, "get_current_user", return_value=None):
            window.show()
            self.wait_for_data(window)
        self.assertIs(window.header.menu_button, window.ui.btnHamburger)
        self.assertIs(window.header.menu_button.menu(), window.logout_menu)
        opened = []

        def dismiss():
            opened.append(window.logout_menu.isVisible())
            window.logout_menu.close()

        QTimer.singleShot(30, dismiss)
        QTest.mouseClick(window.ui.btnHamburger, Qt.MouseButton.LeftButton)
        QTest.qWait(40)
        self.assertEqual(opened, [True])
        selected = []
        window.camera_settings_requested.connect(lambda: selected.append("camera"))
        window.logout_requested.connect(lambda: selected.append("logout"))
        window.camera_action.trigger()
        window.logout_action.trigger()
        self.assertEqual(selected, ["camera", "logout"])

    def test_optional_controls_use_same_shared_art_without_forcing_extra_controls(self):
        for back, streak, menu in ((False, True, True), (True, False, False), (True, False, True)):
            with self.subTest(back=back, streak=streak, menu=menu):
                header = SenyaSabiHeader(show_back=back, show_streak=streak, show_menu=menu)
                self.assertEqual(header.back_button is not None, back)
                self.assertEqual(header.streak_label is not None, streak)
                self.assertEqual(header.menu_button is not None, menu)
                if back:
                    self.assertIsInstance(header.back_button, BackButton)
                    callbacks = []
                    header.back_button.clicked.connect(lambda: callbacks.append("back"))
                    header.back_button.click()
                    self.assertEqual(callbacks, ["back"])
                header.set_streak_text("19 Days")
                if streak:
                    self.assertEqual(header.streak_label.text(), "19 Days")


if __name__ == "__main__":
    unittest.main()
