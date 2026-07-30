# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'menuwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QSizePolicy, QWidget, QVBoxLayout


class Ui_MenuWindow(object):
    def setupUi(self, MenuWindow):
        if not MenuWindow.objectName():
            MenuWindow.setObjectName("MenuWindow")
        MenuWindow.resize(1500, 900)

        self.centralwidget = QWidget(MenuWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")

        self.titleLabel = QLabel(self.centralwidget)
        self.titleLabel.setObjectName("titleLabel")
        self.titleLabel.setText("Choose a Game")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.verticalLayout.addWidget(self.titleLabel)

        self.signSprintButton = QPushButton(self.centralwidget)
        self.signSprintButton.setObjectName("signSprintButton")
        self.signSprintButton.setText("Sign Sprint")
        self.verticalLayout.addWidget(self.signSprintButton)

        self.fingerspellQuestButton = QPushButton(self.centralwidget)
        self.fingerspellQuestButton.setObjectName("fingerspellQuestButton")
        self.fingerspellQuestButton.setText("Fingerspell Quest")
        self.verticalLayout.addWidget(self.fingerspellQuestButton)

        self.expressionInMotionButton = QPushButton(self.centralwidget)
        self.expressionInMotionButton.setObjectName("expressionInMotionButton")
        self.expressionInMotionButton.setText("Expression in Motion")
        self.verticalLayout.addWidget(self.expressionInMotionButton)

        self.signDetectiveButton = QPushButton(self.centralwidget)
        self.signDetectiveButton.setObjectName("signDetectiveButton")
        self.signDetectiveButton.setText("Sign Detective")
        self.verticalLayout.addWidget(self.signDetectiveButton)

        MenuWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MenuWindow)
        QMetaObject.connectSlotsByName(MenuWindow)

    def retranslateUi(self, MenuWindow):
        MenuWindow.setWindowTitle(QCoreApplication.translate("MenuWindow", "Menu", None))
        self.titleLabel.setText(QCoreApplication.translate("MenuWindow", "Choose a Game", None))
        self.signSprintButton.setText(QCoreApplication.translate("MenuWindow", "Sign Sprint", None))
        self.fingerspellQuestButton.setText(QCoreApplication.translate("MenuWindow", "Fingerspell Quest", None))
        self.expressionInMotionButton.setText(QCoreApplication.translate("MenuWindow", "Expression in Motion", None))
        self.signDetectiveButton.setText(QCoreApplication.translate("MenuWindow", "Sign Detective", None))
