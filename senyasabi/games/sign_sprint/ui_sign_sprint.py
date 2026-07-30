# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sign_sprint.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
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
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_SignSprint(object):
    def setupUi(self, SignSprint):
        if not SignSprint.objectName():
            SignSprint.setObjectName(u"SignSprint")
        SignSprint.resize(1920, 1080)
        self.centralwidget = QWidget(SignSprint)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setPixmap(QPixmap(u"../../resources/img/SIGNSPRINTHOW.png"))
        self.label.setScaledContents(True)

        self.verticalLayout.addWidget(self.label)

        SignSprint.setCentralWidget(self.centralwidget)

        self.retranslateUi(SignSprint)

        QMetaObject.connectSlotsByName(SignSprint)
    # setupUi

    def retranslateUi(self, SignSprint):
        SignSprint.setWindowTitle(QCoreApplication.translate("SignSprint", u"Sign Sprint", None))
        self.label.setText("")
    # retranslateUi

