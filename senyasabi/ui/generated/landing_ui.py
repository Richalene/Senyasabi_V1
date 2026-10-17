# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'landing.ui'
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

class Ui_Landing(object):
    def setupUi(self, Landing):
        if not Landing.objectName():
            Landing.setObjectName(u"Landing")
        Landing.resize(1440, 900)
        Landing.setMinimumSize(QSize(1440, 900))
        Landing.setMaximumSize(QSize(1440, 900))
        self.imgBackground = QLabel(Landing)
        self.imgBackground.setObjectName(u"imgBackground")
        self.imgBackground.setGeometry(QRect(0, 0, 1440, 900))
        self.imgBackground.setStyleSheet(u"background-color: #C2D076; border: 2px dashed #704833; color: #704833; font-size: 18px;")
        self.imgBackground.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btnLogin = QPushButton(Landing)
        self.btnLogin.setObjectName(u"btnLogin")
        self.btnLogin.setGeometry(QRect(1190, 30, 190, 64))
        self.btnLogin.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLogin.setStyleSheet(u"QPushButton { background: transparent; border: none; color: transparent; } QPushButton:hover { background: rgba(255,255,255,24); border: 1px solid rgba(112,72,51,80); border-radius: 10px; }")
        self.btnLogin.setFlat(True)
        self.btnGetStarted = QPushButton(Landing)
        self.btnGetStarted.setObjectName(u"btnGetStarted")
        self.btnGetStarted.setGeometry(QRect(500, 635, 440, 100))
        self.btnGetStarted.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnGetStarted.setStyleSheet(u"QPushButton { background: transparent; border: none; color: transparent; } QPushButton:hover { background: rgba(255,255,255,24); border: 1px solid rgba(112,72,51,80); border-radius: 14px; }")
        self.btnGetStarted.setFlat(True)
        self.btnLearnMore = QPushButton(Landing)
        self.btnLearnMore.setObjectName(u"btnLearnMore")
        self.btnLearnMore.setGeometry(QRect(520, 748, 400, 72))
        self.btnLearnMore.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLearnMore.setStyleSheet(u"QPushButton { background: transparent; border: none; color: transparent; } QPushButton:hover { background: rgba(255,255,255,24); border: 1px solid rgba(112,72,51,80); border-radius: 12px; }")
        self.btnLearnMore.setFlat(True)

        self.retranslateUi(Landing)

        QMetaObject.connectSlotsByName(Landing)
    # setupUi

    def retranslateUi(self, Landing):
        Landing.setWindowTitle(QCoreApplication.translate("Landing", u"SenyaSabi", None))
        self.imgBackground.setText(QCoreApplication.translate("Landing", u"Full-window Figma background image placeholder", None))
        self.btnLogin.setText("")
#if QT_CONFIG(accessibility)
        self.btnLogin.setAccessibleName(QCoreApplication.translate("Landing", u"Log in", None))
#endif // QT_CONFIG(accessibility)
        self.btnGetStarted.setText("")
#if QT_CONFIG(accessibility)
        self.btnGetStarted.setAccessibleName(QCoreApplication.translate("Landing", u"Get Started Today", None))
#endif // QT_CONFIG(accessibility)
        self.btnLearnMore.setText("")
#if QT_CONFIG(accessibility)
        self.btnLearnMore.setAccessibleName(QCoreApplication.translate("Landing", u"Learn More", None))
#endif // QT_CONFIG(accessibility)
    # retranslateUi

