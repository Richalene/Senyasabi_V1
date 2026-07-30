# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fingerspell_quest.ui'
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

class Ui_FingerspellQuest(object):
    def setupUi(self, FingerspellQuest):
        if not FingerspellQuest.objectName():
            FingerspellQuest.setObjectName(u"FingerspellQuest")
        FingerspellQuest.resize(1920, 1080)
        self.centralwidget = QWidget(FingerspellQuest)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setPixmap(QPixmap(u"../../resources/img/FINGERSPELLQUESTHOW.png"))
        self.label.setScaledContents(True)

        self.verticalLayout.addWidget(self.label)

        FingerspellQuest.setCentralWidget(self.centralwidget)

        self.retranslateUi(FingerspellQuest)

        QMetaObject.connectSlotsByName(FingerspellQuest)
    # setupUi

    def retranslateUi(self, FingerspellQuest):
        FingerspellQuest.setWindowTitle(QCoreApplication.translate("FingerspellQuest", u"Fingerspell Quest", None))
        self.label.setText("")
    # retranslateUi

