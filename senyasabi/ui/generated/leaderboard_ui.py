# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'leaderboard.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_Leaderboard(object):
    def setupUi(self, Leaderboard):
        if not Leaderboard.objectName():
            Leaderboard.setObjectName(u"Leaderboard")
        Leaderboard.resize(1276, 800)
        Leaderboard.setMinimumSize(QSize(800, 520))
        Leaderboard.setStyleSheet(u"\n"
"QWidget#Leaderboard { background-color: #C2D076; }\n"
"QFrame#titlePanel, QFrame#streakPanel, QFrame#leaderboardPanel {\n"
"    background-color: #F5E5CF;\n"
"    border: 2px solid #704833;\n"
"    border-radius: 18px;\n"
"}\n"
"QLabel { color: #0f3a0f; }\n"
"QLabel#titleLabel { font-size: 28px; font-weight: 800; }\n"
"QLabel#lblCurrentStreak { font-size: 19px; font-weight: 800; }\n"
"QLabel#columnHeader { color: #704833; font-size: 13px; font-weight: 700; }\n"
"QLabel.imagePlaceholder {\n"
"    background-color: #C2D076;\n"
"    border: 2px dashed #704833;\n"
"    border-radius: 28px;\n"
"    color: #704833;\n"
"    font-size: 20px;\n"
"}\n"
"QFrame#currentUserRow {\n"
"    background-color: #E3EAAE;\n"
"    border: 2px solid #704833;\n"
"    border-radius: 12px;\n"
"}\n"
"QPushButton {\n"
"    background-color: #0f3a0f;\n"
"    color: #F5E5CF;\n"
"    border: 1px solid #704833;\n"
"    border-radius: 10px;\n"
"    padding: 6px 12px;\n"
"    font-weight: 700;\n"
"}\n"
"QPushButton:hover { background-colo"
                        "r: #123f12; }\n"
"QPushButton#btnMenu { min-width: 36px; min-height: 32px; font-size: 18px; padding: 0; }\n"
"QPushButton#btnBack { background-color: transparent; color: #0f3a0f; }\n"
"   ")
        self.leaderboardPanel = QFrame(Leaderboard)
        self.leaderboardPanel.setObjectName(u"leaderboardPanel")
        self.leaderboardPanel.setEnabled(True)
        self.leaderboardPanel.setGeometry(QRect(50, 170, 1181, 601))
        self.leaderboardPanel.setFrameShape(QFrame.Shape.NoFrame)
        self.leaderboardPanelLayout = QVBoxLayout(self.leaderboardPanel)
        self.leaderboardPanelLayout.setSpacing(10)
        self.leaderboardPanelLayout.setObjectName(u"leaderboardPanelLayout")
        self.leaderboardPanelLayout.setContentsMargins(22, 18, 22, 18)
        self.columnsLayout = QHBoxLayout()
        self.columnsLayout.setObjectName(u"columnsLayout")
        self.columnsLayout.setContentsMargins(14, -1, 14, -1)
        self.rankHeader = QLabel(self.leaderboardPanel)
        self.rankHeader.setObjectName(u"rankHeader")
        self.rankHeader.setMinimumSize(QSize(80, 26))
        self.rankHeader.setStyleSheet(u"color: #704833; font-size: 13px; font-weight: 700;")

        self.columnsLayout.addWidget(self.rankHeader)

        self.usernameHeader = QLabel(self.leaderboardPanel)
        self.usernameHeader.setObjectName(u"usernameHeader")
        self.usernameHeader.setStyleSheet(u"color: #704833; font-size: 13px; font-weight: 700;")

        self.columnsLayout.addWidget(self.usernameHeader)

        self.columnsSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.columnsLayout.addItem(self.columnsSpacer)

        self.streakHeader = QLabel(self.leaderboardPanel)
        self.streakHeader.setObjectName(u"streakHeader")
        self.streakHeader.setMinimumSize(QSize(130, 26))
        self.streakHeader.setStyleSheet(u"color: #704833; font-size: 13px; font-weight: 700;")

        self.columnsLayout.addWidget(self.streakHeader)

        self.badgesHeader = QLabel(self.leaderboardPanel)
        self.badgesHeader.setObjectName(u"badgesHeader")
        self.badgesHeader.setMinimumSize(QSize(130, 26))
        self.badgesHeader.setStyleSheet(u"color: #704833; font-size: 13px; font-weight: 700;")

        self.columnsLayout.addWidget(self.badgesHeader)


        self.leaderboardPanelLayout.addLayout(self.columnsLayout)

        self.scrollLeaderboard = QScrollArea(self.leaderboardPanel)
        self.scrollLeaderboard.setObjectName(u"scrollLeaderboard")
        self.scrollLeaderboard.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollLeaderboard.setWidgetResizable(True)
        self.leaderboardContainer = QWidget()
        self.leaderboardContainer.setObjectName(u"leaderboardContainer")
        self.leaderboardContainer.setGeometry(QRect(0, 0, 1133, 523))
        self.leaderboardLayout = QVBoxLayout(self.leaderboardContainer)
        self.leaderboardLayout.setSpacing(10)
        self.leaderboardLayout.setObjectName(u"leaderboardLayout")
        self.leaderboardLayout.setContentsMargins(4, 4, 4, 4)
        self.scrollLeaderboard.setWidget(self.leaderboardContainer)

        self.leaderboardPanelLayout.addWidget(self.scrollLeaderboard)

        self.lblCurrentStreak = QLabel(Leaderboard)
        self.lblCurrentStreak.setObjectName(u"lblCurrentStreak")
        self.lblCurrentStreak.setGeometry(QRect(1090, 60, 50, 26))
        self.titleLabel = QLabel(Leaderboard)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setGeometry(QRect(50, 50, 189, 37))
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.btnBack = QPushButton(Leaderboard)
        self.btnBack.setObjectName(u"btnBack")
        self.btnBack.setGeometry(QRect(1130, 130, 68, 30))
        self.widget = QWidget(Leaderboard)
        self.widget.setObjectName(u"widget")
        self.backLayout = QHBoxLayout(self.widget)
        self.backLayout.setObjectName(u"backLayout")
        self.backLayout.setContentsMargins(0, 0, 0, 0)
        self.btnMenu = QPushButton(Leaderboard)
        self.btnMenu.setObjectName(u"btnMenu")
        self.btnMenu.setGeometry(QRect(1170, 60, 38, 34))

        self.retranslateUi(Leaderboard)

        QMetaObject.connectSlotsByName(Leaderboard)
    # setupUi

    def retranslateUi(self, Leaderboard):
        Leaderboard.setWindowTitle(QCoreApplication.translate("Leaderboard", u"Leaderboards \u2014 SenyaSabi", None))
        self.rankHeader.setText(QCoreApplication.translate("Leaderboard", u"RANK", None))
        self.usernameHeader.setText(QCoreApplication.translate("Leaderboard", u"USERNAME", None))
        self.streakHeader.setText(QCoreApplication.translate("Leaderboard", u"STREAK", None))
        self.badgesHeader.setText(QCoreApplication.translate("Leaderboard", u"BADGES", None))
        self.lblCurrentStreak.setText(QCoreApplication.translate("Leaderboard", u" Days", None))
        self.titleLabel.setText(QCoreApplication.translate("Leaderboard", u"Leaderboards", None))
        self.btnBack.setText(QCoreApplication.translate("Leaderboard", u"\u2190 Back", None))
        self.btnMenu.setText(QCoreApplication.translate("Leaderboard", u"\u2630", None))
    # retranslateUi

