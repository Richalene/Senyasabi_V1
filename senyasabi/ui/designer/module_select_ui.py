# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'module_select.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QSizePolicy,
    QWidget)

class Ui_ModuleSelect(object):
    def setupUi(self, ModuleSelect):
        if not ModuleSelect.objectName():
            ModuleSelect.setObjectName(u"ModuleSelect")
        ModuleSelect.resize(1920, 1080)
        ModuleSelect.setStyleSheet(u"\n"
"QWidget#ModuleSelect { background: #C2D076; }\n"
"QPushButton#backBtn { background: transparent; border: none; }\n"
"QLabel#logoLabel { background: transparent; }\n"
"QPushButton[class=\"moduleFirefly\"] { background: transparent; border: none; padding: 0px; }\n"
"QFrame[class=\"modulePopup\"] { background: #FFF7D6; border: 2px solid #879D25; border-radius: 16px; }\n"
"QLabel[class=\"modulePopupTitle\"] { color: #69452F; font-size: 16px; font-weight: 700; background: transparent; border: none; }\n"
"QLabel[class=\"modulePopupDescription\"] { color: #7A6045; font-size: 13px; background: transparent; border: none; }\n"
"   ")
        self.bgLabel = QLabel(ModuleSelect)
        self.bgLabel.setObjectName(u"bgLabel")
        self.bgLabel.setGeometry(QRect(0, 0, 1920, 1080))
        self.bgLabel.setPixmap(QPixmap(u"../../resources/img/mod_tree.png"))
        self.bgLabel.setScaledContents(True)
        self.logoLabel = QLabel(ModuleSelect)
        self.logoLabel.setObjectName(u"logoLabel")
        self.logoLabel.setGeometry(QRect(40, 25, 330, 128))
        self.logoLabel.setPixmap(QPixmap(u"../../resources/img/ui/senyasabi_logo_header.png"))
        self.logoLabel.setScaledContents(True)
        self.backBtn = QPushButton(ModuleSelect)
        self.backBtn.setObjectName(u"backBtn")
        self.backBtn.setGeometry(QRect(1800, 40, 68, 68))
        self.backBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        icon = QIcon()
        icon.addFile(u"../../resources/img/ui/mod_back_btn.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.backBtn.setIcon(icon)
        self.backBtn.setIconSize(QSize(68, 68))
        self.walnutPileLabel = QLabel(ModuleSelect)
        self.walnutPileLabel.setObjectName(u"walnutPileLabel")
        self.walnutPileLabel.setGeometry(QRect(1368, 548, 290, 272))
        self.walnutPileLabel.setPixmap(QPixmap(u"../../resources/img/ui/WALNUTS.png"))
        self.walnutPileLabel.setScaledContents(True)

        self.retranslateUi(ModuleSelect)

        QMetaObject.connectSlotsByName(ModuleSelect)
    # setupUi

    def retranslateUi(self, ModuleSelect):
        ModuleSelect.setWindowTitle(QCoreApplication.translate("ModuleSelect", u"SenyaSabi \u2014 Module Map", None))
        self.bgLabel.setText("")
        self.logoLabel.setText("")
        self.backBtn.setText("")
        self.walnutPileLabel.setText("")
    # retranslateUi

