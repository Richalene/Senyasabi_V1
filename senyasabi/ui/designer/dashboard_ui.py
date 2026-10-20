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
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_Dashboard(object):
    def setupUi(self, Dashboard):
        if not Dashboard.objectName():
            Dashboard.setObjectName(u"Dashboard")
        Dashboard.resize(1920, 1080)
        Dashboard.setMinimumSize(QSize(1920, 1080))
        Dashboard.setMaximumSize(QSize(1920, 1080))
        Dashboard.setStyleSheet(u"QWidget#Dashboard { background-color: #c2d076; font-family: \"Segoe UI\"; }")
        self.imageBg = QLabel(Dashboard)
        self.imageBg.setObjectName(u"imageBg")
        self.imageBg.setGeometry(QRect(0, 0, 1920, 1080))
        self.imageBg.setStyleSheet(u"background: transparent;")
        self.imageBg.setPixmap(QPixmap(u"../../resources/img/ui/dashboard_bg.png"))
        self.imageBg.setScaledContents(True)
        self.btnBack = QPushButton(Dashboard)
        self.btnBack.setObjectName(u"btnBack")
        self.btnBack.setGeometry(QRect(50, 40, 80, 80))
        self.titlePanel = QFrame(Dashboard)
        self.titlePanel.setObjectName(u"titlePanel")
        self.titlePanel.setGeometry(QRect(150, 40, 200, 50))
        self.streakPanel = QFrame(Dashboard)
        self.streakPanel.setObjectName(u"streakPanel")
        self.streakPanel.setGeometry(QRect(1400, 40, 200, 60))
        self.lblCurrentStreak = QLabel(self.streakPanel)
        self.lblCurrentStreak.setObjectName(u"lblCurrentStreak")
        self.lblCurrentStreak.setGeometry(QRect(0, 0, 50, 20))
        self.btnMenu = QPushButton(Dashboard)
        self.btnMenu.setObjectName(u"btnMenu")
        self.btnMenu.setGeometry(QRect(1750, 40, 50, 50))
        self.imgStatsChart = QLabel(Dashboard)
        self.imgStatsChart.setObjectName(u"imgStatsChart")
        self.imgStatsChart.setGeometry(QRect(180, 380, 400, 400))
        self.imgStatsChart.setStyleSheet(u"background: transparent;")
        self.cardLessons = QFrame(Dashboard)
        self.cardLessons.setObjectName(u"cardLessons")
        self.cardLessons.setGeometry(QRect(710, 150, 290, 270))
        self.cardLessons.setStyleSheet(u"\n"
"QFrame#cardLessons {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/les_prog_bg.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"    ")
        self.lblLessonsTop = QLabel(self.cardLessons)
        self.lblLessonsTop.setObjectName(u"lblLessonsTop")
        self.lblLessonsTop.setGeometry(QRect(25, 50, 240, 40))
        self.lblLessonsTop.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 28px; color: #5c3b28; background: transparent;")
        self.lblLessonsTop.setAlignment(Qt.AlignCenter)
        self.lblLessonsCompleted = QLabel(self.cardLessons)
        self.lblLessonsCompleted.setObjectName(u"lblLessonsCompleted")
        self.lblLessonsCompleted.setGeometry(QRect(25, 95, 240, 65))
        self.lblLessonsCompleted.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 48px; font-weight: bold; color: #5c3b28; background: transparent;")
        self.lblLessonsCompleted.setAlignment(Qt.AlignCenter)
        self.lblLessonsBottom = QLabel(self.cardLessons)
        self.lblLessonsBottom.setObjectName(u"lblLessonsBottom")
        self.lblLessonsBottom.setGeometry(QRect(25, 165, 240, 40))
        self.lblLessonsBottom.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 24px; color: #5c3b28; background: transparent;")
        self.lblLessonsBottom.setAlignment(Qt.AlignCenter)
        self.cardQuiz = QFrame(Dashboard)
        self.cardQuiz.setObjectName(u"cardQuiz")
        self.cardQuiz.setGeometry(QRect(1030, 120, 320, 220))
        self.cardQuiz.setStyleSheet(u"\n"
"QFrame#cardQuiz {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/quiz_scr_bg.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"    ")
        self.lblQuizTop = QLabel(self.cardQuiz)
        self.lblQuizTop.setObjectName(u"lblQuizTop")
        self.lblQuizTop.setGeometry(QRect(25, 35, 270, 35))
        self.lblQuizTop.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 24px; color: #5c3b28; background: transparent;")
        self.lblQuizTop.setAlignment(Qt.AlignCenter)
        self.lblTotalQuizScore = QLabel(self.cardQuiz)
        self.lblTotalQuizScore.setObjectName(u"lblTotalQuizScore")
        self.lblTotalQuizScore.setGeometry(QRect(25, 72, 270, 55))
        self.lblTotalQuizScore.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 44px; font-weight: bold; color: #5c3b28; background: transparent;")
        self.lblTotalQuizScore.setAlignment(Qt.AlignCenter)
        self.lblQuizBottom = QLabel(self.cardQuiz)
        self.lblQuizBottom.setObjectName(u"lblQuizBottom")
        self.lblQuizBottom.setGeometry(QRect(25, 130, 270, 35))
        self.lblQuizBottom.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 22px; color: #5c3b28; background: transparent;")
        self.lblQuizBottom.setAlignment(Qt.AlignCenter)
        self.cardModule = QFrame(Dashboard)
        self.cardModule.setObjectName(u"cardModule")
        self.cardModule.setGeometry(QRect(1030, 350, 325, 325))
        self.cardModule.setStyleSheet(u"\n"
"QFrame#cardModule {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/module_bg.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"    ")
        self.lblModuleTop = QLabel(self.cardModule)
        self.lblModuleTop.setObjectName(u"lblModuleTop")
        self.lblModuleTop.setGeometry(QRect(35, 60, 255, 50))
        self.lblModuleTop.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 34px; color: #5c3b28; background: transparent;")
        self.lblModuleTop.setAlignment(Qt.AlignCenter)
        self.lblModuleCount = QLabel(self.cardModule)
        self.lblModuleCount.setObjectName(u"lblModuleCount")
        self.lblModuleCount.setGeometry(QRect(35, 120, 255, 115))
        self.lblModuleCount.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 90px; font-weight: bold; color: #5c3b28; background: transparent;")
        self.lblModuleCount.setAlignment(Qt.AlignCenter)
        self.badgeCard = QFrame(Dashboard)
        self.badgeCard.setObjectName(u"badgeCard")
        self.badgeCard.setGeometry(QRect(710, 470, 290, 290))
        self.badgeCard.setStyleSheet(u"\n"
"QFrame#badgeCard {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/badge_bg.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"    ")
        self.badgeTitle = QLabel(self.badgeCard)
        self.badgeTitle.setObjectName(u"badgeTitle")
        self.badgeTitle.setGeometry(QRect(25, 32, 240, 35))
        self.badgeTitle.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 24px; color: #5c3b28; background: transparent;")
        self.badgeTitle.setAlignment(Qt.AlignCenter)
        self.badgeShieldImg = QLabel(self.badgeCard)
        self.badgeShieldImg.setObjectName(u"badgeShieldImg")
        self.badgeShieldImg.setGeometry(QRect(80, 75, 130, 135))
        self.badgeShieldImg.setStyleSheet(u"background: transparent;")
        self.badgeShieldImg.setPixmap(QPixmap(u"../../resources/img/ui/badge_shield.png"))
        self.badgeShieldImg.setScaledContents(True)
        self.lblLatestBadge = QLabel(self.badgeCard)
        self.lblLatestBadge.setObjectName(u"lblLatestBadge")
        self.lblLatestBadge.setGeometry(QRect(20, 220, 250, 40))
        self.lblLatestBadge.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 18px; color: #5c3b28; background: transparent;")
        self.lblLatestBadge.setAlignment(Qt.AlignCenter)
        self.cardMinigames = QFrame(Dashboard)
        self.cardMinigames.setObjectName(u"cardMinigames")
        self.cardMinigames.setGeometry(QRect(1055, 690, 275, 255))
        self.cardMinigames.setStyleSheet(u"\n"
"QFrame#cardMinigames {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/mg_scores_bg.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"    ")
        self.lblMgTop = QLabel(self.cardMinigames)
        self.lblMgTop.setObjectName(u"lblMgTop")
        self.lblMgTop.setGeometry(QRect(20, 35, 235, 35))
        self.lblMgTop.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 24px; color: #5c3b28; background: transparent;")
        self.lblMgTop.setAlignment(Qt.AlignCenter)
        self.lblMinigamesCompleted = QLabel(self.cardMinigames)
        self.lblMinigamesCompleted.setObjectName(u"lblMinigamesCompleted")
        self.lblMinigamesCompleted.setGeometry(QRect(20, 78, 235, 60))
        self.lblMinigamesCompleted.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 46px; font-weight: bold; color: #5c3b28; background: transparent;")
        self.lblMinigamesCompleted.setAlignment(Qt.AlignCenter)
        self.lblMgBottom = QLabel(self.cardMinigames)
        self.lblMgBottom.setObjectName(u"lblMgBottom")
        self.lblMgBottom.setGeometry(QRect(20, 145, 235, 35))
        self.lblMgBottom.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 20px; color: #5c3b28; background: transparent;")
        self.lblMgBottom.setAlignment(Qt.AlignCenter)
        self.btnLeaderboard = QPushButton(Dashboard)
        self.btnLeaderboard.setObjectName(u"btnLeaderboard")
        self.btnLeaderboard.setGeometry(QRect(1410, 320, 380, 460))
        self.btnLeaderboard.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLeaderboard.setStyleSheet(u"\n"
"QPushButton#btnLeaderboard {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/lead_brd_bg.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"    ")
        self.lblLeaderboardRank = QLabel(self.btnLeaderboard)
        self.lblLeaderboardRank.setObjectName(u"lblLeaderboardRank")
        self.lblLeaderboardRank.setGeometry(QRect(75, 300, 230, 55))
        self.lblLeaderboardRank.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 40px; color: #fdfae5; background: transparent;")
        self.lblLeaderboardRank.setAlignment(Qt.AlignCenter)
        self.lblLeaderboardBtn = QLabel(self.btnLeaderboard)
        self.lblLeaderboardBtn.setObjectName(u"lblLeaderboardBtn")
        self.lblLeaderboardBtn.setGeometry(QRect(75, 365, 230, 48))
        self.lblLeaderboardBtn.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 26px; color: #fdfae5; background: transparent;")
        self.lblLeaderboardBtn.setAlignment(Qt.AlignCenter)
        self.quizImage = QLabel(Dashboard)
        self.quizImage.setObjectName(u"quizImage")
        self.quizImage.setGeometry(QRect(0, 0, 0, 0))
        self.quizImage.setVisible(False)
        self.lessonsImage = QLabel(Dashboard)
        self.lessonsImage.setObjectName(u"lessonsImage")
        self.lessonsImage.setGeometry(QRect(0, 0, 0, 0))
        self.lessonsImage.setVisible(False)
        self.modulesImage = QLabel(Dashboard)
        self.modulesImage.setObjectName(u"modulesImage")
        self.modulesImage.setGeometry(QRect(0, 0, 0, 0))
        self.modulesImage.setVisible(False)
        self.leaderboardImage = QLabel(Dashboard)
        self.leaderboardImage.setObjectName(u"leaderboardImage")
        self.leaderboardImage.setGeometry(QRect(0, 0, 0, 0))
        self.leaderboardImage.setVisible(False)
        self.minigamesImage = QLabel(Dashboard)
        self.minigamesImage.setObjectName(u"minigamesImage")
        self.minigamesImage.setGeometry(QRect(0, 0, 0, 0))
        self.minigamesImage.setVisible(False)
        self.badgeImage = QLabel(Dashboard)
        self.badgeImage.setObjectName(u"badgeImage")
        self.badgeImage.setGeometry(QRect(0, 0, 0, 0))
        self.badgeImage.setVisible(False)
        self.legendDot1 = QFrame(Dashboard)
        self.legendDot1.setObjectName(u"legendDot1")
        self.legendDot1.setGeometry(QRect(0, 0, 0, 0))
        self.legendDot1.setVisible(False)
        self.legendDot2 = QFrame(Dashboard)
        self.legendDot2.setObjectName(u"legendDot2")
        self.legendDot2.setGeometry(QRect(0, 0, 0, 0))
        self.legendDot2.setVisible(False)
        self.legendDot3 = QFrame(Dashboard)
        self.legendDot3.setObjectName(u"legendDot3")
        self.legendDot3.setGeometry(QRect(0, 0, 0, 0))
        self.legendDot3.setVisible(False)
        self.legendDot4 = QFrame(Dashboard)
        self.legendDot4.setObjectName(u"legendDot4")
        self.legendDot4.setGeometry(QRect(0, 0, 0, 0))
        self.legendDot4.setVisible(False)
        self.legendDot5 = QFrame(Dashboard)
        self.legendDot5.setObjectName(u"legendDot5")
        self.legendDot5.setGeometry(QRect(0, 0, 0, 0))
        self.legendDot5.setVisible(False)
        self.legendDot6 = QFrame(Dashboard)
        self.legendDot6.setObjectName(u"legendDot6")
        self.legendDot6.setGeometry(QRect(0, 0, 0, 0))
        self.legendDot6.setVisible(False)

        self.retranslateUi(Dashboard)

        QMetaObject.connectSlotsByName(Dashboard)
    # setupUi

    def retranslateUi(self, Dashboard):
        Dashboard.setWindowTitle(QCoreApplication.translate("Dashboard", u"My Statistics \u2014 SenyaSabi", None))
        self.btnBack.setText("")
        self.lblCurrentStreak.setText(QCoreApplication.translate("Dashboard", u"0 Days", None))
        self.btnMenu.setText("")
        self.imgStatsChart.setText("")
        self.lblLessonsTop.setText(QCoreApplication.translate("Dashboard", u"Lessons", None))
        self.lblLessonsCompleted.setText(QCoreApplication.translate("Dashboard", u"2/7", None))
        self.lblLessonsBottom.setText(QCoreApplication.translate("Dashboard", u"Completed", None))
        self.lblQuizTop.setText(QCoreApplication.translate("Dashboard", u"Total Quiz", None))
        self.lblTotalQuizScore.setText(QCoreApplication.translate("Dashboard", u"67", None))
        self.lblQuizBottom.setText(QCoreApplication.translate("Dashboard", u"Scores", None))
        self.lblModuleTop.setText(QCoreApplication.translate("Dashboard", u"Module", None))
        self.lblModuleCount.setText(QCoreApplication.translate("Dashboard", u"7", None))
        self.badgeTitle.setText(QCoreApplication.translate("Dashboard", u"Latest Badge", None))
        self.lblLatestBadge.setText(QCoreApplication.translate("Dashboard", u"Level 1 Badge", None))
        self.lblMgTop.setText(QCoreApplication.translate("Dashboard", u"Minigames", None))
        self.lblMinigamesCompleted.setText(QCoreApplication.translate("Dashboard", u"57", None))
        self.lblMgBottom.setText(QCoreApplication.translate("Dashboard", u"Completed", None))
        self.lblLeaderboardRank.setText(QCoreApplication.translate("Dashboard", u"#3", None))
        self.lblLeaderboardBtn.setText(QCoreApplication.translate("Dashboard", u"Leaderboard", None))
    # retranslateUi

