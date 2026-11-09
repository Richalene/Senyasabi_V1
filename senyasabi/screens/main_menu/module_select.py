"""Firefly module map; content comes from existing module definitions."""
from pathlib import Path
import random
import re

from PySide6.QtCore import (QEasingCurve, Qt, QParallelAnimationGroup,
                            QPauseAnimation, QPointF, QPropertyAnimation,
                            QRect, QRectF, QSize, QSequentialAnimationGroup, Signal)
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QWidget, QPushButton, QLabel, QFrame, QVBoxLayout,
                              QGraphicsDropShadowEffect)
from backend.content_service import get_words_for_module
from screens.main_menu.alphabet_menu import LESSON_LETTERS
from screens.main_menu.word_menu import _load_categories
from screens.navigation import BackButton, install_page_menu
from backend.content_service import ALPHABET, get_modules

try:
    from backend.paths import get_base_dir
    ROOT = get_base_dir()
except ImportError:
    ROOT = Path(__file__).resolve().parents[2]
# Positions are canvas fractions, independent of desktop resolution.
# Trajectory along horizontal branch leading to golden walnut cache matching reference mockup
POSITIONS = (
    (.140, .650),  # 2: Numbers
    (.255, .820),  # 3: Family Members
    (.360, .580),  # 4: Basic Communication (Greetings + Survival)
    (.470, .780),  # 5: Days of the Week
    (.590, .590),  # 6: Months of the Year (placeholder)
    (.705, .710),  # 7: Action Words (placeholder)
)
FIREFLY_SIZE_RANGE = (120, 280)
FIREFLY_HIT_TARGET = 90
FIREFLY_ROTATION_RANGE = (12.0, 35.0)
FIREFLY_X_JITTER = 0.035
FIREFLY_Y_JITTER = 0.07
FIREFLY_MIN_X_SPACING = 0.08
MODULE_NODES: list[dict[str, str | int | float | bool]] = [
    dict(
        module_code="alphabet",
        title="FSL Alphabet",
        description="Learn the FSL alphabet",
        count=sum(map(len, LESSON_LETTERS.values())),
        x=.050,
        y=.908,
    ),
    dict(
        module_code="number",
        title="Numbers",
        description="Lesson coming soon",
        count=0,
        coming_soon=True,
        x=POSITIONS[0][0],
        y=POSITIONS[0][1],
    ),
    dict(
        module_code="family",
        title="Family Members",
        description="Lesson coming soon",
        count=0,
        coming_soon=True,
        x=POSITIONS[1][0],
        y=POSITIONS[1][1],
    ),
    dict(
        module_code="communication",
        title="Basic Communication",
        description="Lesson coming soon",
        count=0,
        coming_soon=True,
        x=POSITIONS[2][0],
        y=POSITIONS[2][1],
    ),
    dict(
        module_code="days",
        title="Days of the Week",
        description="Lesson coming soon",
        count=0,
        coming_soon=True,
        x=POSITIONS[3][0],
        y=POSITIONS[3][1],
    ),
    dict(
        module_code="calendar",
        title="Months of the Year",
        description="Lesson coming soon",
        count=0,
        coming_soon=True,
        x=POSITIONS[4][0],
        y=POSITIONS[4][1],
    ),
    dict(
        module_code="actions",
        title="Action Words",
        description="Lesson coming soon",
        count=0,
        coming_soon=True,
        x=POSITIONS[5][0],
        y=POSITIONS[5][1],
    ),
]


class FireflyButton(QPushButton):
    hovered = Signal(object, bool)

    def enterEvent(self, event):
        self.hovered.emit(self, True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered.emit(self, False)
        super().leaveEvent(event)


class FireflySprite(QLabel):
    def __init__(self, pixmap, angle, parent=None):
        super().__init__(parent)
        self._pixmap = pixmap
        self.angle = angle
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, event):
        if self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        center_x = self.width() / 2
        center_y = self.height() / 2
        painter.translate(center_x, center_y)
        painter.rotate(self.angle)
        target = QRectF(-center_x, -center_y, self.width(), self.height())
        painter.drawPixmap(target, self._pixmap, QRectF(self._pixmap.rect()))


class DashedTrailOverlay(QWidget):
    """Draws the glowing dashed flight path connecting the fireflies along the tree branch."""
    def __init__(self, parent=None, node_layout: list[tuple[float, float, int]] | None = None):
        super().__init__(parent)
        self.node_layout: list[tuple[float, float, int]] = node_layout or [
            (float(node["x"]), float(node["y"]), FIREFLY_SIZE_RANGE[0])
            for node in MODULE_NODES
        ]

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        # Rich gold-amber dashed flight trail
        pen = QPen(QColor(210, 165, 85, 230), max(2.5, 4.0 * (w / 1920)))
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([3, 4])
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        # Connect nodes from bottom-left through each module to the golden walnut cache
        pts = [QPointF(x * w, y * h) for x, y, _ in self.node_layout]
        # Append golden walnut destination
        pts.append(QPointF(0.789 * w, 0.633 * h))

        if len(pts) >= 2:
            path.moveTo(pts[0])
            for i in range(len(pts) - 1):
                p0 = pts[i]
                p1 = pts[i + 1]
                dx = (p1.x() - p0.x()) * 0.55
                # Alternate vertical control offsets for a natural wavy flight pattern
                dy = -35 * (h / 1080) if (i % 2 == 0) else 35 * (h / 1080)
                c1 = QPointF(p0.x() + dx, p0.y() + dy)
                c2 = QPointF(p1.x() - dx, p1.y() - dy)
                path.cubicTo(c1, c2, p1)
            painter.drawPath(path)


class ModuleSelectWidget(QWidget):
    go_back = Signal()
    module_chosen = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = QUiLoader().load(str(ROOT / "ui/designer/module_select.ui"), self)
        if self._ui is None:
            raise RuntimeError("Unable to load module_select.ui")
        self.setWindowTitle("SenyaSabi — Module Map")
        # This screen owns proportional fitting, including its dynamic overlays.
        self._fitted_form = self
        self.resize(1306,735)
        rng = random.Random()
        self.node_layout: list[tuple[float, float, int]] = []
        previous_x = 0.0
        for node in MODULE_NODES:
            visual_size = rng.randint(*FIREFLY_SIZE_RANGE)
            x = float(node["x"]) + rng.uniform(-FIREFLY_X_JITTER, FIREFLY_X_JITTER)
            y = float(node["y"]) + rng.uniform(-FIREFLY_Y_JITTER, FIREFLY_Y_JITTER)
            x = max(x, previous_x + FIREFLY_MIN_X_SPACING)
            x = min(x, 0.72)
            previous_x = x
            x_margin = visual_size / (2 * 1920)
            y_margin = visual_size / (2 * 1080)
            self.node_layout.append((
                min(max(x, x_margin), 1 - x_margin),
                min(max(y, y_margin), 1 - y_margin),
                visual_size,
            ))
        rotated_indices = set(rng.sample(
            range(len(MODULE_NODES)), k=max(1, len(MODULE_NODES) // 2)
        ))
        self.firefly_angles = [
            rng.uniform(*FIREFLY_ROTATION_RANGE) * rng.choice((-1, 1))
            if index in rotated_indices else 0.0
            for index in range(len(MODULE_NODES))
        ]
        self._intro_animation = None
        background = self._ui.findChild(QLabel, "bgLabel")
        if background is None:
            background = QLabel(self._ui)
        self.background = background
        self.background.setPixmap(QPixmap(str(ROOT / "resources/img/mod_tree.png")))
        self.background.setScaledContents(True)
        self.background.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.background.lower()

        self.trail_overlay = DashedTrailOverlay(self._ui, self.node_layout)
        self.trail_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.trail_overlay.show()

        self.logo = self._ui.findChild(QLabel, "logoLabel")
        if self.logo is not None:
            self.logo.setPixmap(QPixmap(str(ROOT / "resources/img/ui/senyasabi_logo_header.png")))
            self.logo.setScaledContents(True)

        self.walnut_pile = self._ui.findChild(QLabel, "walnutPileLabel")
        if self.walnut_pile is not None:
            self.walnut_pile.setPixmap(QPixmap(str(ROOT / "resources/img/ui/WALNUTS.png")))
            self.walnut_pile.setScaledContents(True)

        self.back_button = self._ui.findChild(QPushButton, "backBtn")
        if self.back_button is not None:
            self.back_button.setIcon(QIcon(str(ROOT / "resources/img/ui/mod_back_btn.png")))
            self.back_button.clicked.connect(self.go_back)
        self._fixed = [(child, child.geometry(), child.styleSheet())
                       for child in self._ui.findChildren(QWidget)
                       if child is not self.background]
        self._base_style = self._ui.styleSheet()
        install_page_menu(self, canvas_size=QSize(1920, 1080))
        firefly_pixmap = QPixmap(str(ROOT / "resources/img/ui/firefly.png"))
        self.buttons = []
        self.firefly_visuals = []
        for number, node in enumerate(MODULE_NODES,1):
            button = FireflyButton(self._ui)
            button.setProperty("class", "moduleFirefly")
            button.setProperty("noHoverBounce", True)
            button.setProperty("module_code", node["module_code"])
            button.setProperty("coming_soon", bool(node.get("coming_soon", False)))
            desc = "Lesson coming soon" if node.get("coming_soon") else node["description"]
            button.setAccessibleName(f'Module {number}: {node["title"]}')
            button.setToolTip("")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if firefly_pixmap.isNull():
                button.setText('●')
                button.setStyleSheet('color: #e7bd42; font-size: 32px; border: none; background: transparent;')
            visual = FireflySprite(firefly_pixmap, self.firefly_angles[number - 1], self._ui)
            glow = QGraphicsDropShadowEffect(visual)
            glow.setColor(QColor(255,206,66,190))
            glow.setOffset(0,0)
            glow.setEnabled(False)
            visual.setGraphicsEffect(glow)
            self.firefly_visuals.append(visual)
            button.hovered.connect(self.hover_node)
            button.clicked.connect(lambda checked=False, code=node["module_code"]: self.choose(code))
            self.buttons.append(button)
        # Bottom Level Badge matching Wireframe Pages 27, 28, 36, 54, 55, 64, 65
        self.level_badge = QLabel("Level 1/7", self._ui)
        self.level_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.level_badge.setStyleSheet(
            "background-color: #FFFDF0; "
            "color: #555555; "
            "border: 2px solid #D6DFA0; "
            "border-radius: 20px; "
            "font-family: 'Segoe UI', sans-serif; "
            "font-size: 18px; "
            "font-style: italic; "
            "font-weight: 500;"
        )
        self.level_badge.show()

        self.popup = QFrame(self._ui)
        self.popup.setProperty("class", "modulePopup")
        self.popup.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout = QVBoxLayout(self.popup)
        layout.setContentsMargins(16, 12, 16, 12)
        self.popup_title = QLabel()
        self.popup_title.setProperty("class", "modulePopupTitle")
        self.popup_detail = QLabel()
        self.popup_detail.setProperty("class", "modulePopupDescription")
        for child in (self.popup_title, self.popup_detail):
            child.setTextFormat(Qt.TextFormat.PlainText)
            child.setWordWrap(True)
            layout.addWidget(child)
        self.popup.hide()
        self.active_node = None
        self.fit()

    def choose(self, code):
        self.clear_hover()
        self.module_chosen.emit(code)

    def hover_node(self, button, entered):
        if not entered:
            if self.active_node is button:
                self.clear_hover()
            return
        self.clear_hover()
        self.active_node = button
        self.firefly_visuals[self.buttons.index(button)].graphicsEffect().setEnabled(True)
        number = self.buttons.index(button)
        node = MODULE_NODES[number]
        self.popup_title.setText(f'Module {number + 1}: {node["title"]}')
        self.popup_detail.setText(
            "Lesson coming soon" if node.get("coming_soon")
            else f'{node["description"]}\n{node["count"]} Signs'
        )
        self.position_popup()
        self.popup.show()
        self.level_badge.raise_()
        self.popup.raise_()

    def position_popup(self):
        if self.active_node is None:
            return
        self.popup.setFixedWidth(min(290, self._ui.width()))
        self.popup.adjustSize()
        button = self.active_node
        x = button.x() + button.width() + 12
        if x + self.popup.width() > self._ui.width():
            x = button.x() - self.popup.width() - 12
        self.popup.move(
            max(0, min(x, self._ui.width() - self.popup.width())),
            max(0, min(button.y(), self._ui.height() - self.popup.height())),
        )

    def clear_hover(self):
        if self.active_node is not None:
            index = self.buttons.index(self.active_node)
            self.firefly_visuals[index].graphicsEffect().setEnabled(False)
        self.active_node = None
        self.popup.hide()

    def fit(self):
        if not hasattr(self,"buttons"):
            return
        scale = min(self.width()/1920,self.height()/1080)
        width,height = round(1920*scale),round(1080*scale)
        self._ui.setGeometry((self.width()-width)//2,(self.height()-height)//2,width,height)
        self.background.setGeometry(self._ui.rect())
        self.background.lower()
        if hasattr(self, "trail_overlay"):
            self.trail_overlay.setGeometry(self._ui.rect())
            self.trail_overlay.raise_()
        self._ui.setStyleSheet(re.sub(r"(\d+)px",lambda m:f"{max(1,round(int(m[1])*scale))}px",self._base_style))
        for child,rect,_ in self._fixed:
            if child is not getattr(self, "trail_overlay", None):
                child.setGeometry(QRect(round(rect.x()*scale),round(rect.y()*scale),
                                        round(rect.width()*scale),round(rect.height()*scale)))
                child.raise_()
        if hasattr(self, "walnut_pile") and self.walnut_pile is not None:
            self.walnut_pile.raise_()
        for button, visual, (x, y, base_size) in zip(
                self.buttons, self.firefly_visuals, self.node_layout):
            visual_size = max(35, round(base_size * scale))
            center_x = round(x * width)
            center_y = round(y * height)
            visual.setGeometry(
                center_x - visual_size // 2, center_y - visual_size // 2,
                visual_size, visual_size,
            )
            visual.raise_()
            hit_size = max(35, round(FIREFLY_HIT_TARGET * scale))
            button.setGeometry(
                center_x - hit_size // 2, center_y - hit_size // 2,
                hit_size, hit_size,
            )
            visual.graphicsEffect().setBlurRadius(max(12, 36 * scale))
            button.raise_()
        if hasattr(self, "level_badge"):
            self.level_badge.raise_()
        self.popup.raise_()
        self.position_popup()

    def play_intro(self, direction="forward"):
        self.stop_intro()
        self.fit()
        group = QParallelAnimationGroup(self)
        direction_sign = -1 if direction == "forward" else 1
        for index, (visual, button) in enumerate(zip(self.firefly_visuals, self.buttons)):
            target = visual.geometry()
            start_size = max(22, round(target.width() * 0.48))
            previous = self.node_layout[max(0, index - 1)]
            x, y, _ = self.node_layout[index]
            if index == 0:
                dx, dy = direction_sign * 24, 0
            else:
                dx = (previous[0] - x) * target.width() * 0.22 * direction_sign
                dy = (previous[1] - y) * target.height() * 0.22 * direction_sign
            start = QRect(
                round(target.center().x() - start_size / 2 + dx),
                round(target.center().y() - start_size / 2 + dy),
                start_size,
                start_size,
            )
            button.setGeometry(start)

            button.setEnabled(False)
            sequence = QSequentialAnimationGroup()
            sequence.addAnimation(QPauseAnimation(index * 45))
            movement = QPropertyAnimation(visual, b"geometry")
            movement.setDuration(300)
            movement.setStartValue(start)
            movement.setEndValue(target)
            movement.setEasingCurve(QEasingCurve.Type.OutCubic)
            sequence.addAnimation(movement)
            group.addAnimation(sequence)

        self._intro_animation = group

        def finish_intro():
            if self._intro_animation is group:
                self._intro_animation = None
            for button in self.buttons:
                button.setEnabled(True)
            group.deleteLater()

        group.finished.connect(finish_intro)
        group.start()

    def stop_intro(self):
        animation, self._intro_animation = self._intro_animation, None
        if animation is not None:
            animation.stop()
            animation.deleteLater()
        for button in self.buttons:
            button.setEnabled(True)

    def resizeEvent(self,event):
        if self._intro_animation is not None:
            self.stop_intro()
        super().resizeEvent(event)
        self.fit()

    def hideEvent(self,event):
        self.stop_intro()
        self.clear_hover()
        super().hideEvent(event)
