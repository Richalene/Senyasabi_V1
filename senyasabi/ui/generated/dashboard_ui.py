# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dashboard.ui'
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
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_Dashboard(object):
    def setupUi(self, Dashboard):
        if not Dashboard.objectName():
            Dashboard.setObjectName(u"Dashboard")
        Dashboard.resize(1439, 782)
        Dashboard.setMinimumSize(QSize(800, 480))
        Dashboard.setStyleSheet(u"\n"
"QWidget#Dashboard { background-color: #C2D076; }\n"
"QFrame#titlePanel, QFrame#streakPanel, QFrame#statCard, QFrame#chartPanel {\n"
"    background-color: #F5E5CF;\n"
"    border: 2px solid #704833;\n"
"    border-radius: 18px;\n"
"}\n"
"QLabel { color: #0f3a0f; }\n"
"QLabel#titleLabel { font-size: 28px; font-weight: 800; }\n"
"QLabel#lblCurrentStreak { font-size: 19px; font-weight: 800; }\n"
"QLabel#statTitle { font-size: 13px; font-weight: 700; }\n"
"QLabel#lblLessonsCompleted, QLabel#lblTotalQuizScore, QLabel#lblModuleCount,\n"
"QLabel#lblLatestBadge, QLabel#lblMinigamesCompleted, QLabel#lblLeaderboardRank {\n"
"    color: #704833;\n"
"    font-size: 22px;\n"
"    font-weight: 800;\n"
"}\n"
"QLabel#imgStatsChart {\n"
"    background-color: #E8D7BA;\n"
"    border: 2px dashed #704833;\n"
"    border-radius: 12px;\n"
"    color: #704833;\n"
"    font-size: 13px;\n"
"}\n"
"QLabel.imagePlaceholder {\n"
"    background-color: #C2D076;\n"
"    border: 2px dashed #704833;\n"
"    border-radius: 40px;\n"
"    "
                        "color: #704833;\n"
"    font-size: 10px;\n"
"}\n"
"QPushButton {\n"
"    background-color: #0f3a0f;\n"
"    color: #F5E5CF;\n"
"    border: 1px solid #704833;\n"
"    border-radius: 10px;\n"
"    padding: 6px 12px;\n"
"    font-weight: 700;\n"
"}\n"
"QPushButton:hover { background-color: #123f12; border-color: #704833; }\n"
"QPushButton#btnMenu { min-width: 36px; min-height: 32px; font-size: 18px; padding: 0; }\n"
"QPushButton#btnBack { background-color: transparent; color: #0f3a0f; }\n"
"QPushButton#btnLeaderboard { background-color: #704833; padding: 5px 8px; }\n"
"   ")
        self.streakPanel = QFrame(Dashboard)
        self.streakPanel.setObjectName(u"streakPanel")
        self.streakPanel.setGeometry(QRect(1090, 50, 118, 38))
        self.streakPanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.streakLayout = QHBoxLayout(self.streakPanel)
        self.streakLayout.setObjectName(u"streakLayout")
        self.streakLayout.setContentsMargins(10, 4, 10, 4)
        self.streakIcon = QLabel(self.streakPanel)
        self.streakIcon.setObjectName(u"streakIcon")

        self.streakLayout.addWidget(self.streakIcon)

        self.lblCurrentStreak = QLabel(self.streakPanel)
        self.lblCurrentStreak.setObjectName(u"lblCurrentStreak")

        self.streakLayout.addWidget(self.lblCurrentStreak)

        self.btnMenu = QPushButton(Dashboard)
        self.btnMenu.setObjectName(u"btnMenu")
        self.btnMenu.setGeometry(QRect(1330, 70, 38, 34))
        self.btnBack = QPushButton(Dashboard)
        self.btnBack.setObjectName(u"btnBack")
        self.btnBack.setGeometry(QRect(1300, 160, 68, 30))
        self.quizCard = QFrame(Dashboard)
        self.quizCard.setObjectName(u"quizCard")
        self.quizCard.setGeometry(QRect(720, 230, 224, 150))
        self.quizCard.setMinimumSize(QSize(170, 150))
        self.quizCard.setFrameShape(QFrame.Shape.NoFrame)
        self.quizCardLayout = QVBoxLayout(self.quizCard)
        self.quizCardLayout.setSpacing(4)
        self.quizCardLayout.setObjectName(u"quizCardLayout")
        self.quizImage = QLabel(self.quizCard)
        self.quizImage.setObjectName(u"quizImage")
        self.quizImage.setMinimumSize(QSize(54, 54))
        self.quizImage.setMaximumSize(QSize(54, 54))
        self.quizImage.setStyleSheet(u"background-color: #C2D076; border: 2px dashed #704833; border-radius: 27px; color: #704833; font-size: 9px;")
        self.quizImage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.quizCardLayout.addWidget(self.quizImage)

        self.quizTitle = QLabel(self.quizCard)
        self.quizTitle.setObjectName(u"quizTitle")

        self.quizCardLayout.addWidget(self.quizTitle)

        self.lblTotalQuizScore = QLabel(self.quizCard)
        self.lblTotalQuizScore.setObjectName(u"lblTotalQuizScore")

        self.quizCardLayout.addWidget(self.lblTotalQuizScore)

        self.lessonsCard = QFrame(Dashboard)
        self.lessonsCard.setObjectName(u"lessonsCard")
        self.lessonsCard.setGeometry(QRect(380, 220, 224, 150))
        self.lessonsCard.setMinimumSize(QSize(170, 150))
        self.lessonsCard.setFrameShape(QFrame.Shape.NoFrame)
        self.lessonsCardLayout = QVBoxLayout(self.lessonsCard)
        self.lessonsCardLayout.setSpacing(4)
        self.lessonsCardLayout.setObjectName(u"lessonsCardLayout")
        self.lessonsImage = QLabel(self.lessonsCard)
        self.lessonsImage.setObjectName(u"lessonsImage")
        self.lessonsImage.setMinimumSize(QSize(54, 54))
        self.lessonsImage.setMaximumSize(QSize(54, 54))
        self.lessonsImage.setStyleSheet(u"background-color: #C2D076; border: 2px dashed #704833; border-radius: 27px; color: #704833; font-size: 9px;")
        self.lessonsImage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lessonsCardLayout.addWidget(self.lessonsImage)

        self.lessonsTitle = QLabel(self.lessonsCard)
        self.lessonsTitle.setObjectName(u"lessonsTitle")

        self.lessonsCardLayout.addWidget(self.lessonsTitle)

        self.lblLessonsCompleted = QLabel(self.lessonsCard)
        self.lblLessonsCompleted.setObjectName(u"lblLessonsCompleted")

        self.lessonsCardLayout.addWidget(self.lblLessonsCompleted)

        self.lessonsCompletedCaption = QLabel(self.lessonsCard)
        self.lessonsCompletedCaption.setObjectName(u"lessonsCompletedCaption")

        self.lessonsCardLayout.addWidget(self.lessonsCompletedCaption)

        self.modulesCard = QFrame(Dashboard)
        self.modulesCard.setObjectName(u"modulesCard")
        self.modulesCard.setGeometry(QRect(1140, 220, 224, 150))
        self.modulesCard.setMinimumSize(QSize(170, 150))
        self.modulesCard.setFrameShape(QFrame.Shape.NoFrame)
        self.modulesCardLayout = QVBoxLayout(self.modulesCard)
        self.modulesCardLayout.setSpacing(4)
        self.modulesCardLayout.setObjectName(u"modulesCardLayout")
        self.modulesImage = QLabel(self.modulesCard)
        self.modulesImage.setObjectName(u"modulesImage")
        self.modulesImage.setMinimumSize(QSize(54, 54))
        self.modulesImage.setMaximumSize(QSize(54, 54))
        self.modulesImage.setStyleSheet(u"background-color: #C2D076; border: 2px dashed #704833; border-radius: 27px; color: #704833; font-size: 9px;")
        self.modulesImage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.modulesCardLayout.addWidget(self.modulesImage)

        self.modulesTitle = QLabel(self.modulesCard)
        self.modulesTitle.setObjectName(u"modulesTitle")

        self.modulesCardLayout.addWidget(self.modulesTitle)

        self.lblModuleCount = QLabel(self.modulesCard)
        self.lblModuleCount.setObjectName(u"lblModuleCount")

        self.modulesCardLayout.addWidget(self.lblModuleCount)

        self.leaderboardCard = QFrame(Dashboard)
        self.leaderboardCard.setObjectName(u"leaderboardCard")
        self.leaderboardCard.setEnabled(True)
        self.leaderboardCard.setGeometry(QRect(1160, 500, 224, 171))
        self.leaderboardCard.setMinimumSize(QSize(170, 150))
        self.leaderboardCard.setFrameShape(QFrame.Shape.NoFrame)
        self.leaderboardCardLayout = QVBoxLayout(self.leaderboardCard)
        self.leaderboardCardLayout.setSpacing(4)
        self.leaderboardCardLayout.setObjectName(u"leaderboardCardLayout")
        self.leaderboardImage = QLabel(self.leaderboardCard)
        self.leaderboardImage.setObjectName(u"leaderboardImage")
        self.leaderboardImage.setMinimumSize(QSize(54, 54))
        self.leaderboardImage.setMaximumSize(QSize(54, 54))
        self.leaderboardImage.setStyleSheet(u"background-color: #779DC4; border: 2px dashed #704833; border-radius: 27px; color: #704833; font-size: 9px;")
        self.leaderboardImage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.leaderboardCardLayout.addWidget(self.leaderboardImage)

        self.leaderboardTitle = QLabel(self.leaderboardCard)
        self.leaderboardTitle.setObjectName(u"leaderboardTitle")

        self.leaderboardCardLayout.addWidget(self.leaderboardTitle)

        self.lblLeaderboardRank = QLabel(self.leaderboardCard)
        self.lblLeaderboardRank.setObjectName(u"lblLeaderboardRank")

        self.leaderboardCardLayout.addWidget(self.lblLeaderboardRank)

        self.btnLeaderboard = QPushButton(self.leaderboardCard)
        self.btnLeaderboard.setObjectName(u"btnLeaderboard")

        self.leaderboardCardLayout.addWidget(self.btnLeaderboard)

        self.minigamesCard = QFrame(Dashboard)
        self.minigamesCard.setObjectName(u"minigamesCard")
        self.minigamesCard.setGeometry(QRect(710, 480, 170, 150))
        self.minigamesCard.setMinimumSize(QSize(170, 150))
        self.minigamesCard.setFrameShape(QFrame.Shape.NoFrame)
        self.minigamesCardLayout = QVBoxLayout(self.minigamesCard)
        self.minigamesCardLayout.setSpacing(4)
        self.minigamesCardLayout.setObjectName(u"minigamesCardLayout")
        self.minigamesImage = QLabel(self.minigamesCard)
        self.minigamesImage.setObjectName(u"minigamesImage")
        self.minigamesImage.setMinimumSize(QSize(54, 54))
        self.minigamesImage.setMaximumSize(QSize(54, 54))
        self.minigamesImage.setStyleSheet(u"background-color: #77A86B; border: 2px dashed #704833; border-radius: 27px; color: #704833; font-size: 9px;")
        self.minigamesImage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.minigamesCardLayout.addWidget(self.minigamesImage)

        self.minigamesTitle = QLabel(self.minigamesCard)
        self.minigamesTitle.setObjectName(u"minigamesTitle")

        self.minigamesCardLayout.addWidget(self.minigamesTitle)

        self.lblMinigamesCompleted = QLabel(self.minigamesCard)
        self.lblMinigamesCompleted.setObjectName(u"lblMinigamesCompleted")

        self.minigamesCardLayout.addWidget(self.lblMinigamesCompleted)

        self.minigamesCompletedCaption = QLabel(self.minigamesCard)
        self.minigamesCompletedCaption.setObjectName(u"minigamesCompletedCaption")

        self.minigamesCardLayout.addWidget(self.minigamesCompletedCaption)

        self.titlePanel = QFrame(Dashboard)
        self.titlePanel.setObjectName(u"titlePanel")
        self.titlePanel.setGeometry(QRect(23, 17, 224, 57))
        self.titlePanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.titleLayout = QVBoxLayout(self.titlePanel)
        self.titleLayout.setObjectName(u"titleLayout")
        self.titleLayout.setContentsMargins(20, 8, 20, 8)
        self.titleLabel = QLabel(self.titlePanel)
        self.titleLabel.setObjectName(u"titleLabel")

        self.titleLayout.addWidget(self.titleLabel)

        self.chartPanel = QFrame(Dashboard)
        self.chartPanel.setObjectName(u"chartPanel")
        self.chartPanel.setGeometry(QRect(23, 398, 260, 295))
        self.chartPanel.setMinimumSize(QSize(260, 0))
        self.chartPanel.setMaximumSize(QSize(280, 16777215))
        self.chartPanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.chartLayout = QVBoxLayout(self.chartPanel)
        self.chartLayout.setSpacing(8)
        self.chartLayout.setObjectName(u"chartLayout")
        self.chartLayout.setContentsMargins(12, 12, 12, 12)
        self.imgStatsChart = QLabel(self.chartPanel)
        self.imgStatsChart.setObjectName(u"imgStatsChart")
        self.imgStatsChart.setMinimumSize(QSize(220, 245))
        self.imgStatsChart.setScaledContents(True)
        self.imgStatsChart.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.chartLayout.addWidget(self.imgStatsChart)

        self.legendLayout = QHBoxLayout()
        self.legendLayout.setSpacing(10)
        self.legendLayout.setObjectName(u"legendLayout")
        self.legendDot1 = QLabel(self.chartPanel)
        self.legendDot1.setObjectName(u"legendDot1")
        self.legendDot1.setMinimumSize(QSize(12, 12))
        self.legendDot1.setMaximumSize(QSize(12, 12))
        self.legendDot1.setStyleSheet(u"background-color: #704833; border-radius: 6px;")

        self.legendLayout.addWidget(self.legendDot1)

        self.legendDot2 = QLabel(self.chartPanel)
        self.legendDot2.setObjectName(u"legendDot2")
        self.legendDot2.setMinimumSize(QSize(12, 12))
        self.legendDot2.setMaximumSize(QSize(12, 12))
        self.legendDot2.setStyleSheet(u"background-color: #E6A04B; border-radius: 6px;")

        self.legendLayout.addWidget(self.legendDot2)

        self.legendDot3 = QLabel(self.chartPanel)
        self.legendDot3.setObjectName(u"legendDot3")
        self.legendDot3.setMinimumSize(QSize(12, 12))
        self.legendDot3.setMaximumSize(QSize(12, 12))
        self.legendDot3.setStyleSheet(u"background-color: #77A86B; border-radius: 6px;")

        self.legendLayout.addWidget(self.legendDot3)

        self.legendDot4 = QLabel(self.chartPanel)
        self.legendDot4.setObjectName(u"legendDot4")
        self.legendDot4.setMinimumSize(QSize(12, 12))
        self.legendDot4.setMaximumSize(QSize(12, 12))
        self.legendDot4.setStyleSheet(u"background-color: #779DC4; border-radius: 6px;")

        self.legendLayout.addWidget(self.legendDot4)

        self.legendDot5 = QLabel(self.chartPanel)
        self.legendDot5.setObjectName(u"legendDot5")
        self.legendDot5.setMinimumSize(QSize(12, 12))
        self.legendDot5.setMaximumSize(QSize(12, 12))
        self.legendDot5.setStyleSheet(u"background-color: #C96F67; border-radius: 6px;")

        self.legendLayout.addWidget(self.legendDot5)

        self.legendDot6 = QLabel(self.chartPanel)
        self.legendDot6.setObjectName(u"legendDot6")
        self.legendDot6.setMinimumSize(QSize(12, 12))
        self.legendDot6.setMaximumSize(QSize(12, 12))
        self.legendDot6.setStyleSheet(u"background-color: #A98BC4; border-radius: 6px;")

        self.legendLayout.addWidget(self.legendDot6)

        self.legendSpacer = QSpacerItem(20, 12, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.legendLayout.addItem(self.legendSpacer)


        self.chartLayout.addLayout(self.legendLayout)

        self.badgeCard = QFrame(Dashboard)
        self.badgeCard.setObjectName(u"badgeCard")
        self.badgeCard.setGeometry(QRect(380, 450, 170, 150))
        self.badgeCard.setMinimumSize(QSize(170, 150))
        self.badgeCard.setFrameShape(QFrame.Shape.NoFrame)
        self.badgeImage = QLabel(self.badgeCard)
        self.badgeImage.setObjectName(u"badgeImage")
        self.badgeImage.setGeometry(QRect(9, 9, 54, 54))
        self.badgeImage.setMinimumSize(QSize(54, 54))
        self.badgeImage.setMaximumSize(QSize(54, 54))
        self.badgeImage.setStyleSheet(u"background-color: #E6A04B; border: 2px dashed #704833; border-radius: 27px; color: #704833; font-size: 9px;")
        self.badgeImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badgeTitle = QLabel(self.badgeCard)
        self.badgeTitle.setObjectName(u"badgeTitle")
        self.badgeTitle.setGeometry(QRect(9, 67, 67, 16))
        self.lblLatestBadge = QLabel(self.badgeCard)
        self.lblLatestBadge.setObjectName(u"lblLatestBadge")
        self.lblLatestBadge.setGeometry(QRect(9, 106, 138, 30))

        self.retranslateUi(Dashboard)

        QMetaObject.connectSlotsByName(Dashboard)
    # setupUi

    def retranslateUi(self, Dashboard):
        Dashboard.setWindowTitle(QCoreApplication.translate("Dashboard", u"My Statistics \u2014 SenyaSabi", None))
        self.streakIcon.setText(QCoreApplication.translate("Dashboard", u"\U0001f525", None))
        self.lblCurrentStreak.setText(QCoreApplication.translate("Dashboard", u"67 Days", None))
        self.btnMenu.setText(QCoreApplication.translate("Dashboard", u"\u2630", None))
        self.btnBack.setText(QCoreApplication.translate("Dashboard", u"\u2190 Back", None))
        self.quizImage.setText(QCoreApplication.translate("Dashboard", u"image", None))
        self.quizTitle.setText(QCoreApplication.translate("Dashboard", u"Total Quiz Score", None))
        self.lblTotalQuizScore.setText(QCoreApplication.translate("Dashboard", u"67", None))
        self.lessonsImage.setText(QCoreApplication.translate("Dashboard", u"image", None))
        self.lessonsTitle.setText(QCoreApplication.translate("Dashboard", u"Lessons", None))
        self.lblLessonsCompleted.setText(QCoreApplication.translate("Dashboard", u"2/7", None))
        self.lessonsCompletedCaption.setText(QCoreApplication.translate("Dashboard", u"Completed", None))
        self.modulesImage.setText(QCoreApplication.translate("Dashboard", u"image", None))
        self.modulesTitle.setText(QCoreApplication.translate("Dashboard", u"Modules", None))
        self.lblModuleCount.setText(QCoreApplication.translate("Dashboard", u"7", None))
        self.leaderboardImage.setText(QCoreApplication.translate("Dashboard", u"image", None))
        self.leaderboardTitle.setText(QCoreApplication.translate("Dashboard", u"Leaderboard", None))
        self.lblLeaderboardRank.setText(QCoreApplication.translate("Dashboard", u"#3", None))
        self.btnLeaderboard.setText(QCoreApplication.translate("Dashboard", u"View", None))
        self.minigamesImage.setText(QCoreApplication.translate("Dashboard", u"image", None))
        self.minigamesTitle.setText(QCoreApplication.translate("Dashboard", u"Minigames", None))
        self.lblMinigamesCompleted.setText(QCoreApplication.translate("Dashboard", u"37", None))
        self.minigamesCompletedCaption.setText(QCoreApplication.translate("Dashboard", u"Completed", None))
        self.titleLabel.setText(QCoreApplication.translate("Dashboard", u"My Statistics", None))
        self.imgStatsChart.setText(QCoreApplication.translate("Dashboard", u"Chart image placeholder", None))
        self.legendDot1.setText("")
        self.legendDot2.setText("")
        self.legendDot3.setText("")
        self.legendDot4.setText("")
        self.legendDot5.setText("")
        self.legendDot6.setText("")
        self.badgeImage.setText(QCoreApplication.translate("Dashboard", u"badge", None))
        self.badgeTitle.setText(QCoreApplication.translate("Dashboard", u"Latest Badge", None))
        self.lblLatestBadge.setText(QCoreApplication.translate("Dashboard", u"Latest Badge", None))
    # retranslateUi

