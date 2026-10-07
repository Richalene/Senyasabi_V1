# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'welcome.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_Welcome(object):
    def setupUi(self, Welcome):
        if not Welcome.objectName():
            Welcome.setObjectName(u"Welcome")
        Welcome.resize(1440, 900)
        Welcome.setMinimumSize(QSize(1440, 900))
        Welcome.setMaximumSize(QSize(1440, 900))
        self.imgBackground = QLabel(Welcome)
        self.imgBackground.setObjectName(u"imgBackground")
        self.imgBackground.setGeometry(QRect(0, 0, 1440, 900))
        self.imgBackground.setStyleSheet(u"")
        self.imgBackground.setFrameShape(QFrame.Shape.NoFrame)
        self.imgBackground.setPixmap(QPixmap(u"../resources/img/welcome.png"))
        self.imgBackground.setScaledContents(True)
        self.imgBackground.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btnContinue = QPushButton(Welcome)
        self.btnContinue.setObjectName(u"btnContinue")
        self.btnContinue.setGeometry(QRect(680, 690, 111, 111))
        icon = QIcon()
        icon.addFile(u"../resources/img/ui/nextbtn.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btnContinue.setIcon(icon)
        self.btnContinue.setIconSize(QSize(111, 111))
        self.btnContinue.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnContinue.setStyleSheet(u"QPushButton { background: transparent; border: none; color: transparent; } QPushButton:hover { background: rgba(255,255,255,24); border: 1px solid rgba(112,72,51,80); border-radius: 12px; }")
        self.btnContinue.setFlat(True)

        self.retranslateUi(Welcome)

        QMetaObject.connectSlotsByName(Welcome)
    # setupUi

    def retranslateUi(self, Welcome):
        Welcome.setWindowTitle(QCoreApplication.translate("Welcome", u"SenyaSabi", None))
        self.imgBackground.setText("")
#if QT_CONFIG(accessibility)
        self.btnContinue.setAccessibleName(QCoreApplication.translate("Welcome", u"Continue", None))
#endif // QT_CONFIG(accessibility)
        self.btnContinue.setText("")
    # retranslateUi

