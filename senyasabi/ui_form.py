# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QSizePolicy,
    QWidget)

class Ui_main(object):
    def setupUi(self, main):
        if not main.objectName():
            main.setObjectName(u"main")
        main.resize(1306, 753)
        self.bg = QLabel(main)
        self.bg.setObjectName(u"bg")
        self.bg.setGeometry(QRect(0, 0, 1311, 761))
        self.bg.setPixmap(QPixmap(u"resources/img/bgempty.png"))
        self.bg.setScaledContents(True)
        self.signSprint = QPushButton(main)
        self.signSprint.setObjectName(u"signSprint")
        self.signSprint.setGeometry(QRect(579, 363, 321, 151))
        self.signSprint.setStyleSheet(u"background:transparent;")
        self.EIP = QPushButton(main)
        self.EIP.setObjectName(u"EIP")
        self.EIP.setGeometry(QRect(590, 530, 321, 151))
        self.EIP.setStyleSheet(u"background:transparent;")
        self.signDetective = QPushButton(main)
        self.signDetective.setObjectName(u"signDetective")
        self.signDetective.setGeometry(QRect(940, 520, 321, 151))
        self.signDetective.setStyleSheet(u"background:transparent;")
        self.fingerspellQuest = QPushButton(main)
        self.fingerspellQuest.setObjectName(u"fingerspellQuest")
        self.fingerspellQuest.setGeometry(QRect(940, 360, 321, 151))
        self.fingerspellQuest.setStyleSheet(u"background:transparent;")
        self.alphabetBtn = QPushButton(main)
        self.alphabetBtn.setObjectName(u"alphabetBtn")
        self.alphabetBtn.setGeometry(QRect(580, 140, 321, 151))
        self.alphabetBtn.setStyleSheet(u"background-color: rgb(85, 85, 0);")

        self.retranslateUi(main)

        QMetaObject.connectSlotsByName(main)
    # setupUi

    def retranslateUi(self, main):
        main.setWindowTitle(QCoreApplication.translate("main", u"main", None))
        self.bg.setText("")
        self.signSprint.setText("")
        self.EIP.setText("")
        self.signDetective.setText("")
        self.fingerspellQuest.setText("")
        self.alphabetBtn.setText(QCoreApplication.translate("main", u"FSL Alphabet", None))
    # retranslateUi

