# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
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

class Ui_main(object):
    def setupUi(self, main):
        if not main.objectName():
            main.setObjectName(u"main")
        main.resize(1920, 1080)
        main.setMinimumSize(QSize(1920, 1080))
        main.setMaximumSize(QSize(1920, 1080))
        main.setStyleSheet(u"QWidget#main { background-color: #c2d076; font-family: \"Segoe UI\"; }")
        self.imageBg = QLabel(main)
        self.imageBg.setObjectName(u"imageBg")
        self.imageBg.setGeometry(QRect(0, 0, 1920, 1080))
        self.imageBg.setStyleSheet(u"background: transparent;")
        self.imageBg.setPixmap(QPixmap(u"../../resources/img/home_bg.png"))
        self.imageBg.setScaledContents(True)
        self.welcomeLabel = QLabel(main)
        self.welcomeLabel.setObjectName(u"welcomeLabel")
        self.welcomeLabel.setGeometry(QRect(70, 45, 800, 55))
        self.welcomeLabel.setStyleSheet(u"font-size: 38px; font-weight: 800; color: #5c3b28; background: transparent; font-family: \"Cherry Bomb One\", \"Segoe UI\";")
        self.subtitleLabel = QLabel(main)
        self.subtitleLabel.setObjectName(u"subtitleLabel")
        self.subtitleLabel.setGeometry(QRect(72, 104, 800, 35))
        self.subtitleLabel.setStyleSheet(u"font-size: 20px; font-weight: 600; color: #6e4e37; background: transparent;")
        self.streakCard = QFrame(main)
        self.streakCard.setObjectName(u"streakCard")
        self.streakCard.setGeometry(QRect(1500, 40, 200, 60))
        self.streakValue = QLabel(self.streakCard)
        self.streakValue.setObjectName(u"streakValue")
        self.streakValue.setGeometry(QRect(0, 0, 50, 20))
        self.btnHamburger = QPushButton(main)
        self.btnHamburger.setObjectName(u"btnHamburger")
        self.btnHamburger.setGeometry(QRect(1750, 40, 50, 50))
        self.btnStartLearning = QPushButton(main)
        self.btnStartLearning.setObjectName(u"btnStartLearning")
        self.btnStartLearning.setGeometry(QRect(880, 180, 500, 215))
        self.btnStartLearning.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnStartLearning.setStyleSheet(u"\n"
"QPushButton#btnStartLearning {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/button_start.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"QPushButton#btnStartLearning:hover {\n"
"    border-image: url(senyasabi/resources/img/ui/button_start_hover.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"    ")
        self.lblStartLearningText = QLabel(self.btnStartLearning)
        self.lblStartLearningText.setObjectName(u"lblStartLearningText")
        self.lblStartLearningText.setGeometry(QRect(45, 25, 410, 155))
        self.lblStartLearningText.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 46px; color: #5c3b28; background: transparent;")
        self.lblStartLearningText.setAlignment(Qt.AlignCenter)
        self.btnMinigames = QPushButton(main)
        self.btnMinigames.setObjectName(u"btnMinigames")
        self.btnMinigames.setGeometry(QRect(1360, 220, 400, 175))
        self.btnMinigames.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnMinigames.setStyleSheet(u"\n"
"QPushButton#btnMinigames {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/button_mg.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"QPushButton#btnMinigames:hover {\n"
"    border-image: url(senyasabi/resources/img/ui/button_mg_hover.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"QPushButton#btnMinigames QLabel#lblMinigamesText {\n"
"    color: #729b1e;\n"
"}\n"
"QPushButton#btnMinigames:hover QLabel#lblMinigamesText {\n"
"    color: #5c3b28;\n"
"}\n"
"    ")
        self.lblMinigamesText = QLabel(self.btnMinigames)
        self.lblMinigamesText.setObjectName(u"lblMinigamesText")
        self.lblMinigamesText.setGeometry(QRect(35, 25, 330, 115))
        self.lblMinigamesText.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 38px; background: transparent;")
        self.lblMinigamesText.setAlignment(Qt.AlignCenter)
        self.statusLineLeft = QFrame(main)
        self.statusLineLeft.setObjectName(u"statusLineLeft")
        self.statusLineLeft.setGeometry(QRect(960, 455, 215, 4))
        self.statusLineLeft.setStyleSheet(u"border: none; border-top: 3px dashed #75553d;")
        self.lblMyStatusTitle = QLabel(main)
        self.lblMyStatusTitle.setObjectName(u"lblMyStatusTitle")
        self.lblMyStatusTitle.setGeometry(QRect(1190, 425, 230, 55))
        self.lblMyStatusTitle.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 32px; color: #5c3b28; background: transparent;")
        self.lblMyStatusTitle.setAlignment(Qt.AlignCenter)
        self.statusLineRight = QFrame(main)
        self.statusLineRight.setObjectName(u"statusLineRight")
        self.statusLineRight.setGeometry(QRect(1435, 455, 315, 4))
        self.statusLineRight.setStyleSheet(u"border: none; border-top: 3px dashed #75553d;")
        self.btnLessonsCompleted = QPushButton(main)
        self.btnLessonsCompleted.setObjectName(u"btnLessonsCompleted")
        self.btnLessonsCompleted.setGeometry(QRect(955, 515, 210, 204))
        self.btnLessonsCompleted.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLessonsCompleted.setStyleSheet(u"\n"
"QPushButton#btnLessonsCompleted {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/db_lessoncomplete.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"QPushButton#btnLessonsCompleted:hover {\n"
"    transform: scale(1.02);\n"
"}\n"
"    ")
        self.lblLessonsCompleted = QLabel(self.btnLessonsCompleted)
        self.lblLessonsCompleted.setObjectName(u"lblLessonsCompleted")
        self.lblLessonsCompleted.setGeometry(QRect(15, 65, 180, 75))
        self.lblLessonsCompleted.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 40px; font-weight: bold; color: #5c3b28; background: transparent;")
        self.lblLessonsCompleted.setAlignment(Qt.AlignCenter)
        self.btnModule = QPushButton(main)
        self.btnModule.setObjectName(u"btnModule")
        self.btnModule.setGeometry(QRect(1160, 580, 245, 240))
        self.btnModule.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnModule.setStyleSheet(u"\n"
"QPushButton#btnModule {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/db_module.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"    ")
        self.lblModule = QLabel(self.btnModule)
        self.lblModule.setObjectName(u"lblModule")
        self.lblModule.setGeometry(QRect(25, 95, 195, 100))
        self.lblModule.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 72px; font-weight: bold; color: #5c3b28; background: transparent;")
        self.lblModule.setAlignment(Qt.AlignCenter)
        self.btnLatestBadge = QPushButton(main)
        self.btnLatestBadge.setObjectName(u"btnLatestBadge")
        self.btnLatestBadge.setGeometry(QRect(955, 735, 210, 206))
        self.btnLatestBadge.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLatestBadge.setStyleSheet(u"\n"
"QPushButton#btnLatestBadge {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/db_badges.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"    ")
        self.lblLatestBadgeIcon = QLabel(self.btnLatestBadge)
        self.lblLatestBadgeIcon.setObjectName(u"lblLatestBadgeIcon")
        self.lblLatestBadgeIcon.setGeometry(QRect(55, 50, 100, 105))
        self.lblLatestBadgeIcon.setStyleSheet(u"background: transparent;")
        self.lblLatestBadgeIcon.setScaledContents(True)
        self.lblLatestBadgeValue = QLabel(self.btnLatestBadge)
        self.lblLatestBadgeValue.setObjectName(u"lblLatestBadgeValue")
        self.lblLatestBadgeValue.setGeometry(QRect(0, 0, 0, 0))
        self.lblLatestBadgeValue.setVisible(False)
        self.btnLeaderboardRank = QPushButton(main)
        self.btnLeaderboardRank.setObjectName(u"btnLeaderboardRank")
        self.btnLeaderboardRank.setGeometry(QRect(1385, 515, 290, 365))
        self.btnLeaderboardRank.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLeaderboardRank.setStyleSheet(u"\n"
"QPushButton#btnLeaderboardRank {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(senyasabi/resources/img/ui/db_leaderboards.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"    ")
        self.lblLeaderboardRank = QLabel(self.btnLeaderboardRank)
        self.lblLeaderboardRank.setObjectName(u"lblLeaderboardRank")
        self.lblLeaderboardRank.setGeometry(QRect(45, 235, 200, 55))
        self.lblLeaderboardRank.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 34px; color: #fdfae5; background: transparent;")
        self.lblLeaderboardRank.setAlignment(Qt.AlignCenter)

        self.retranslateUi(main)

        QMetaObject.connectSlotsByName(main)
    # setupUi

    def retranslateUi(self, main):
        main.setWindowTitle(QCoreApplication.translate("main", u"SenyaSabi \u2014 Home", None))
        self.welcomeLabel.setText(QCoreApplication.translate("main", u"Welcome Back, Learner!", None))
        self.subtitleLabel.setText(QCoreApplication.translate("main", u"Let's proceed where we left off", None))
        self.streakValue.setText(QCoreApplication.translate("main", u"0 Days", None))
        self.btnHamburger.setText("")
        self.lblStartLearningText.setText(QCoreApplication.translate("main", u"Start\n"
"learning", None))
        self.lblMinigamesText.setText(QCoreApplication.translate("main", u"Minigames", None))
        self.lblMyStatusTitle.setText(QCoreApplication.translate("main", u"MyStatus", None))
        self.lblLessonsCompleted.setText(QCoreApplication.translate("main", u"2/7", None))
        self.lblModule.setText(QCoreApplication.translate("main", u"7", None))
        self.lblLatestBadgeValue.setText("")
        self.lblLeaderboardRank.setText(QCoreApplication.translate("main", u"#3", None))
    # retranslateUi

