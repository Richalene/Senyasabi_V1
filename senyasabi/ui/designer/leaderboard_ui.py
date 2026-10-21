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
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

class Ui_Leaderboard(object):
    def setupUi(self, Leaderboard):
        if not Leaderboard.objectName():
            Leaderboard.setObjectName(u"Leaderboard")
        Leaderboard.resize(1920, 1080)
        self.imageBg = QLabel(Leaderboard)
        self.imageBg.setObjectName(u"imageBg")
        self.imageBg.setGeometry(QRect(0, 0, 1920, 1080))
        self.imageBg.setPixmap(QPixmap(u"../../resources/img/gen_bg.png"))
        self.imageBg.setScaledContents(True)
        self.cloudBg = QLabel(Leaderboard)
        self.cloudBg.setObjectName(u"cloudBg")
        self.cloudBg.setGeometry(QRect(105, 80, 560, 180))
        self.cloudBg.setPixmap(QPixmap(u"../../resources/img/ui/cloud.png"))
        self.cloudBg.setScaledContents(True)
        self.titleLabel = QLabel(Leaderboard)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setGeometry(QRect(110, 90, 550, 160))
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btnBack = QPushButton(Leaderboard)
        self.btnBack.setObjectName(u"btnBack")
        self.btnBack.setGeometry(QRect(1770, 180, 74, 74))
        self.btnBack.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnBack.setFlat(True)
        self.scrollLeaderboard = QScrollArea(Leaderboard)
        self.scrollLeaderboard.setObjectName(u"scrollLeaderboard")
        self.scrollLeaderboard.setGeometry(QRect(90, 300, 1740, 720))
        self.scrollLeaderboard.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollLeaderboard.setWidgetResizable(True)
        self.leaderboardContainer = QWidget()
        self.leaderboardContainer.setObjectName(u"leaderboardContainer")
        self.leaderboardContainer.setGeometry(QRect(0, 0, 1740, 720))
        self.leaderboardLayout = QVBoxLayout(self.leaderboardContainer)
        self.leaderboardLayout.setSpacing(18)
        self.leaderboardLayout.setObjectName(u"leaderboardLayout")
        self.leaderboardLayout.setContentsMargins(0, 0, 10, 10)
        self.scrollLeaderboard.setWidget(self.leaderboardContainer)
        self.lblCurrentStreak = QLabel(Leaderboard)
        self.lblCurrentStreak.setObjectName(u"lblCurrentStreak")
        self.lblCurrentStreak.setGeometry(QRect(0, 0, 0, 0))
        self.btnMenu = QPushButton(Leaderboard)
        self.btnMenu.setObjectName(u"btnMenu")
        self.btnMenu.setGeometry(QRect(0, 0, 0, 0))
        self.imageBg.raise_()
        self.cloudBg.raise_()
        self.titleLabel.raise_()
        self.btnBack.raise_()
        self.scrollLeaderboard.raise_()

        self.retranslateUi(Leaderboard)

        QMetaObject.connectSlotsByName(Leaderboard)
    # setupUi

    def retranslateUi(self, Leaderboard):
        Leaderboard.setWindowTitle(QCoreApplication.translate("Leaderboard", u"Leaderboards \u2014 SenyaSabi", None))
        self.imageBg.setText("")
        self.cloudBg.setText("")
        self.titleLabel.setText(QCoreApplication.translate("Leaderboard", u"Leaderboards", None))
        self.btnBack.setText("")
        self.lblCurrentStreak.setText("")
        self.btnMenu.setText("")
    # retranslateUi

