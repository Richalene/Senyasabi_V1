"""Firefly module map; content comes from existing module definitions."""
from pathlib import Path
import re

from PySide6.QtCore import Qt, Signal, QRect, QSize, QPointF
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QWidget, QPushButton, QLabel, QFrame,
                              QVBoxLayout, QGraphicsDropShadowEffect)
from screens.main_menu.alphabet_menu import LESSON_LETTERS
from screens.main_menu.word_menu import _load_categories
from screens.navigation import BackButton, install_page_menu
from backend.content_service import ALPHABET, get_modules

ROOT = Path(__file__).resolve().parents[2]
# Positions are canvas fractions, independent of desktop resolution.
# Trajectory along horizontal branch leading to golden walnut cache matching reference mockup
POSITIONS = (
    (.140, .650),  # 1: Numbers
    (.255, .820),  # 2: Family Members
    (.360, .580),  # 3: Basic Communication (crest)
    (.470, .780),  # 4: Days of the Week
    (.590, .590),  # 5: Months of the Year (crest)
    (.705, .710),  # 6: Action Words (approaching golden walnuts)
)
ALPHABET_POSITION = (.050, .908)
DISPLAY_TITLES = {ALPHABET: "FSL Alphabet"}

def _build_nodes():
    modules = sorted(get_modules(), key=lambda m: m.module_code != ALPHABET)  # alphabet first
    words = [m for m in modules if m.module_code != ALPHABET]
    if len(words) > len(POSITIONS):
        raise ValueError(f"{len(words)} word modules but only {len(POSITIONS)} map positions")
    nodes = []
    for module in modules:
        x, y = (ALPHABET_POSITION if module.module_code == ALPHABET
                else POSITIONS[words.index(module)])
        lessons = len(module.lessons)
        nodes.append(dict(
            module_code=module.module_code,
            title=DISPLAY_TITLES.get(module.module_code, module.title),
            description=f"{lessons} lesson{'s' if lessons != 1 else ''}",
            count=len(module.signs), x=x, y=y))
    return nodes

MODULE_NODES = _build_nodes()


class FireflyButton(QPushButton):
    hovered = Signal(object, bool)

    def enterEvent(self, event):
        self.graphicsEffect().setEnabled(True)
        self.hovered.emit(self, True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.graphicsEffect().setEnabled(False)
        self.hovered.emit(self, False)
        super().leaveEvent(event)


class DashedTrailOverlay(QWidget):
    """Draws the glowing dashed flight path connecting the fireflies along the tree branch."""
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
        pts = [QPointF(node["x"] * w, node["y"] * h) for node in MODULE_NODES]
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
        self.background = self._ui.findChild(QLabel, "bgLabel")
        if self.background is None:
            self.background = QLabel(self._ui)
        self.background.setPixmap(QPixmap(str(ROOT / "resources/img/mod_tree.png")))
        self.background.setScaledContents(True)
        self.background.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.background.lower()

        self.trail_overlay = DashedTrailOverlay(self._ui)
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
        icon = QIcon(str(ROOT / "resources/img/ui/firefly.png"))
        self.buttons = []
        for number, node in enumerate(MODULE_NODES,1):
            button = FireflyButton(self._ui)
            button.setProperty("class", "moduleFirefly")
            button.setProperty("module_code", node["module_code"])
            button.setAccessibleName(f'Module {number}: {node["title"]}')
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setIcon(icon)
            if icon.isNull():
                button.setText('●')
                button.setStyleSheet('color: #e7bd42; font-size: 32px; border: none; background: transparent;')
            glow = QGraphicsDropShadowEffect(button)
            glow.setColor(QColor(255,206,66,190))
            glow.setOffset(0,0)
            glow.setEnabled(False)
            button.setGraphicsEffect(glow)
            button.hovered.connect(self.hover_node)
            button.clicked.connect(lambda checked=False, code=node["module_code"]: self.choose(code))
            self.buttons.append(button)
        # Bottom Level Badge matching Wireframe Pages 27, 28, 36, 54, 55, 64, 65
        self.level_badge = QLabel("Level 1/4", self._ui)
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
        layout.setContentsMargins(16,12,16,12)
        self.popup_title = QLabel()
        self.popup_title.setProperty("class","modulePopupTitle")
        self.popup_detail = QLabel()
        self.popup_detail.setProperty("class","modulePopupDescription")
        for child in (self.popup_title,self.popup_detail):
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
        button.graphicsEffect().setEnabled(True)
        number = self.buttons.index(button)
        node = MODULE_NODES[number]
        self.popup_title.setText(f'Module {number+1}: {node["title"]}')
        self.popup_detail.setText(f'{node["description"]}\n{node["count"]} Signs')
        self.position_popup()
        self.popup.show()
        self.popup.raise_()

    def position_popup(self):
        if self.active_node is None:
            return
        self.popup.setFixedWidth(min(290,self._ui.width()))
        self.popup.adjustSize()
        button = self.active_node
        x = button.x()+button.width()+12
        if x+self.popup.width()>self._ui.width():
            x = button.x()-self.popup.width()-12
        self.popup.move(max(0,min(x,self._ui.width()-self.popup.width())),
                        max(0,min(button.y(),self._ui.height()-self.popup.height())))

    def clear_hover(self):
        if self.active_node is not None:
            self.active_node.graphicsEffect().setEnabled(False)
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
        size = max(35, round(125 * scale))
        for button,node in zip(self.buttons,MODULE_NODES):
            button.setGeometry(round(node["x"]*width-size/2),round(node["y"]*height-size/2),size,size)
            button.setIconSize(QSize(size,size))
            button.graphicsEffect().setBlurRadius(max(12,32*scale))
            button.raise_()
        if hasattr(self, "level_badge"):
            bw, bh = round(210 * scale), round(46 * scale)
            self.level_badge.setGeometry((width - bw) // 2, round(height * 0.88), bw, bh)
            self.level_badge.raise_()
        self.popup.raise_()
        self.position_popup()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.fit()

    def hideEvent(self,event):
        self.clear_hover()
        super().hideEvent(event)
