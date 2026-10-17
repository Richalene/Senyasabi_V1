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
"QPushButton#backBtn { background: #FFF7D6; color: #69452F; border: 1px solid #879D25; border-radius: 16px; font-size: 22px; font-weight: 700; }\n"
"QLabel#titleLabel { background: transparent; color: #69452F; font-size: 40px; font-weight: 800; }\n"
"QLabel#levelLabel { background: #FFF7D6; color: #69452F; border-radius: 18px; font-size: 24px; font-weight: 700; }\n"
"QPushButton[class=\"moduleFirefly\"] { background: transparent; border: none; padding: 0px; }\n"
"QFrame[class=\"modulePopup\"] { background: #FFF7D6; border: 2px solid #879D25; border-radius: 16px; }\n"
"QLabel[class=\"modulePopupTitle\"] { color: #69452F; font-size: 16px; font-weight: 700; background: transparent; border: none; }\n"
"QLabel[class=\"modulePopupDescription\"] { color: #7A6045; font-size: 13px; background: transparent; border: none; }\n"
"  ")
        self.backBtn = QPushButton(ModuleSelect)
        self.backBtn.setObjectName(u"backBtn")
        self.backBtn.setGeometry(QRect(60, 40, 170, 60))
        self.backBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.titleLabel = QLabel(ModuleSelect)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setGeometry(QRect(300, 35, 1150, 70))
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.levelLabel = QLabel(ModuleSelect)
        self.levelLabel.setObjectName(u"levelLabel")
        self.levelLabel.setGeometry(QRect(1620, 40, 230, 60))
        self.levelLabel.setAlignment(Qt.AlignCenter)

        self.retranslateUi(ModuleSelect)

        QMetaObject.connectSlotsByName(ModuleSelect)
    # setupUi

    def retranslateUi(self, ModuleSelect):
        ModuleSelect.setWindowTitle(QCoreApplication.translate("ModuleSelect", u"SenyaSabi ? Module Map", None))
        self.backBtn.setText(QCoreApplication.translate("ModuleSelect", u"? Back", None))
        self.titleLabel.setText(QCoreApplication.translate("ModuleSelect", u"Start Learning", None))
        self.levelLabel.setText(QCoreApplication.translate("ModuleSelect", u"Level 1/4", None))
    # retranslateUi

