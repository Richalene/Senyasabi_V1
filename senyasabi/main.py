# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path
from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import QApplication, QWidget
from ui_form import Ui_main

class main(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_main()
        self.ui.setupUi(self)

        image_path = Path(__file__).resolve().parent / "resources" / "img" / "menu.png"
        self.ui.bg.setPixmap(QPixmap(str(image_path)))
        self.ui.bg.setScaledContents(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = main()
    widget.show()
    sys.exit(app.exec())