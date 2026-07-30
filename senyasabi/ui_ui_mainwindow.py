# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_mainwindow.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QWidget)

class Ui_SenyaSabi(object):
    def setupUi(self, SenyaSabi):
        if not SenyaSabi.objectName():
            SenyaSabi.setObjectName(u"SenyaSabi")
        SenyaSabi.resize(1495, 946)
        self.centralwidget = QWidget(SenyaSabi)
        self.centralwidget.setObjectName(u"centralwidget")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(0, 0, 1920, 1080))
        self.label.setMinimumSize(QSize(1920, 1080))
        self.label.setPixmap(QPixmap(u"resources/img/Frame 6.png"))
        self.label.setScaledContents(True)
        self.startButton = QPushButton(self.centralwidget)
        self.startButton.setObjectName(u"startButton")
        self.startButton.setGeometry(QRect(170, 810, 401, 101))
        self.startButton.setStyleSheet(u"background:transparent;")
        SenyaSabi.setCentralWidget(self.centralwidget)

        self.retranslateUi(SenyaSabi)

        QMetaObject.connectSlotsByName(SenyaSabi)
    # setupUi

    def retranslateUi(self, SenyaSabi):
        SenyaSabi.setWindowTitle(QCoreApplication.translate("SenyaSabi", u"MainWindow", None))
        self.label.setText("")
        self.label.setProperty(u"bg img", "")
        self.startButton.setText("")
    # retranslateUi

