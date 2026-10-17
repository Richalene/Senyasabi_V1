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

ROOT = Path(__file__).resolve().parents[2]
# Positions are canvas fractions, independent of desktop resolution.
POSITIONS = ((.29,.74), (.71,.74), (.24,.60), (.76,.60), (.29,.46),
             (.71,.46), (.24,.32), (.76,.32), (.33,.19), (.67,.19))
MODULE_NODES = [dict(module_code="alphabet", title="FSL Alphabet",
                     description="Learn the FSL alphabet", count=sum(map(len, LESSON_LETTERS.values())),
                     x=.50, y=.86)] + [
    dict(module_code=code, title=code.title(), description="Learn FSL words and phrases",
         count=len(words), x=position[0], y=position[1])
    for (code, words), position in zip(_load_categories().items(), POSITIONS)
]


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


class BranchBackground(QLabel):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#916237"), max(2, self.width()/1920*12))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        def point(x, y): return QPointF(x*self.width(), y*self.height())
        painter.drawLine(point(.5,.94), point(.5,.18))
        for node in MODULE_NODES[1:]:
            painter.drawLine(point(.5,min(.88,node["y"]+.085)), point(node["x"],node["y"]))


class ModuleSelectWidget(QWidget):
    go_back = Signal()
    module_chosen = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui = QUiLoader().load(str(ROOT / "ui/designer/module_select.ui"), self)
        if self._ui is None:
            raise RuntimeError("Unable to load module_select.ui")
        self.setWindowTitle("SenyaSabi ? Module Map")
        # This screen owns proportional fitting, including its dynamic overlays.
        self._fitted_form = self
        self.resize(1306,735)
        self.background = BranchBackground(self._ui)
        self.background.setPixmap(QPixmap(str(ROOT / "resources/img/bgempty.png")))
        self.background.setScaledContents(True)
        self.background.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.background.lower()
        self._fixed = [(child, child.geometry(), child.styleSheet())
                       for child in self._ui.findChildren(QWidget)
                       if child is not self.background]
        self._base_style = self._ui.styleSheet()
        self.back_button = self._ui.findChild(QPushButton,"backBtn")
        self.back_button.clicked.connect(self.go_back)
        icon = QIcon(str(ROOT / "resources/img/ui/firefly.png"))
        if icon.isNull():
            raise RuntimeError("Missing resources/img/ui/firefly.png")
        self.buttons = []
        for number, node in enumerate(MODULE_NODES,1):
            button = FireflyButton(self._ui)
            button.setProperty("class", "moduleFirefly")
            button.setProperty("module_code", node["module_code"])
            button.setAccessibleName(f'Module {number}: {node["title"]}')
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setIcon(icon)
            glow = QGraphicsDropShadowEffect(button)
            glow.setColor(QColor(255,206,66,190))
            glow.setOffset(0,0)
            glow.setEnabled(False)
            button.setGraphicsEffect(glow)
            button.hovered.connect(self.hover_node)
            button.clicked.connect(lambda checked=False, code=node["module_code"]: self.choose(code))
            self.buttons.append(button)
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
        self._ui.setStyleSheet(re.sub(r"(\d+)px",lambda m:f"{max(1,round(int(m[1])*scale))}px",self._base_style))
        for child,rect,_ in self._fixed:
            child.setGeometry(QRect(round(rect.x()*scale),round(rect.y()*scale),
                                    round(rect.width()*scale),round(rect.height()*scale)))
        size = max(30,round(115*scale))
        for button,node in zip(self.buttons,MODULE_NODES):
            button.setGeometry(round(node["x"]*width-size/2),round(node["y"]*height-size/2),size,size)
            button.setIconSize(QSize(size,size))
            button.graphicsEffect().setBlurRadius(max(12,32*scale))
        self.position_popup()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.fit()

    def hideEvent(self,event):
        self.clear_hover()
        super().hideEvent(event)
