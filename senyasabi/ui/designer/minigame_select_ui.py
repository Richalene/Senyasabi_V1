# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'minigame_select.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QSizePolicy,
    QWidget)

class Ui_MinigameSelect(object):
    def setupUi(self, MinigameSelect):
        if not MinigameSelect.objectName():
            MinigameSelect.setObjectName(u"MinigameSelect")
        MinigameSelect.resize(1920, 1080)
        MinigameSelect.setStyleSheet(u"\n"
"QWidget#MinigameSelect { background-color: #C2D076; font-family: \"Segoe UI\"; }\n"
"   ")
        self.imageBg = QLabel(MinigameSelect)
        self.imageBg.setObjectName(u"imageBg")
        self.imageBg.setGeometry(QRect(0, 0, 1920, 1080))
        self.imageBg.setPixmap(QPixmap(u"../../resources/img/gen_bg.png"))
        self.imageBg.setScaledContents(True)
        self.titleLabel = QLabel(MinigameSelect)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setGeometry(QRect(660, 170, 600, 90))
        self.titleLabel.setStyleSheet(u"font-family: \"Cherry Bomb One\", \"Segoe UI\"; font-size: 64px; font-weight: bold; color: #5C3B28; background: transparent;")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btnBack = QPushButton(MinigameSelect)
        self.btnBack.setObjectName(u"btnBack")
        self.btnBack.setGeometry(QRect(1810, 150, 74, 74))
        self.btnBack.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnSprint = QPushButton(MinigameSelect)
        self.btnSprint.setObjectName(u"btnSprint")
        self.btnSprint.setGeometry(QRect(400, 340, 530, 242))
        self.btnSprint.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnSprint.setStyleSheet(u"\n"
"QPushButton#btnSprint {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(../../resources/img/ui/button_16.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"QPushButton#btnSprint:hover {\n"
"    transform: scale(1.02);\n"
"}\n"
"    ")
        self.starSprint1 = QLabel(self.btnSprint)
        self.starSprint1.setObjectName(u"starSprint1")
        self.starSprint1.setGeometry(QRect(85, 99, 44, 44))
        self.starSprint1.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starSprint1.setScaledContents(True)
        self.lblSprintText = QLabel(self.btnSprint)
        self.lblSprintText.setObjectName(u"lblSprintText")
        self.lblSprintText.setGeometry(QRect(160, 65, 310, 110))
        self.lblSprintText.setStyleSheet(u"font-family: \"Segoe UI\", sans-serif; font-size: 34px; font-weight: 700; color: #5C3B28; background: transparent;")
        self.lblSprintText.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.btnQuest = QPushButton(MinigameSelect)
        self.btnQuest.setObjectName(u"btnQuest")
        self.btnQuest.setGeometry(QRect(990, 340, 522, 237))
        self.btnQuest.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnQuest.setStyleSheet(u"\n"
"QPushButton#btnQuest {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(../../resources/img/ui/button_17.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"QPushButton#btnQuest:hover {\n"
"    transform: scale(1.02);\n"
"}\n"
"    ")
        self.starQuest1 = QLabel(self.btnQuest)
        self.starQuest1.setObjectName(u"starQuest1")
        self.starQuest1.setGeometry(QRect(75, 72, 44, 44))
        self.starQuest1.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starQuest1.setScaledContents(True)
        self.starQuest2 = QLabel(self.btnQuest)
        self.starQuest2.setObjectName(u"starQuest2")
        self.starQuest2.setGeometry(QRect(75, 124, 44, 44))
        self.starQuest2.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starQuest2.setScaledContents(True)
        self.lblQuestText = QLabel(self.btnQuest)
        self.lblQuestText.setObjectName(u"lblQuestText")
        self.lblQuestText.setGeometry(QRect(150, 65, 320, 110))
        self.lblQuestText.setStyleSheet(u"font-family: \"Segoe UI\", sans-serif; font-size: 34px; font-weight: 700; color: #5C3B28; background: transparent;")
        self.lblQuestText.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.btnDetective = QPushButton(MinigameSelect)
        self.btnDetective.setObjectName(u"btnDetective")
        self.btnDetective.setGeometry(QRect(690, 630, 530, 242))
        self.btnDetective.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnDetective.setStyleSheet(u"\n"
"QPushButton#btnDetective {\n"
"    background: transparent;\n"
"    border: none;\n"
"    border-image: url(../../resources/img/ui/button_16.png) 0 0 0 0 stretch stretch;\n"
"}\n"
"QPushButton#btnDetective:hover {\n"
"    transform: scale(1.02);\n"
"}\n"
"    ")
        self.starDet1 = QLabel(self.btnDetective)
        self.starDet1.setObjectName(u"starDet1")
        self.starDet1.setGeometry(QRect(80, 114, 40, 40))
        self.starDet1.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starDet1.setScaledContents(True)
        self.starDet2 = QLabel(self.btnDetective)
        self.starDet2.setObjectName(u"starDet2")
        self.starDet2.setGeometry(QRect(76, 80, 40, 40))
        self.starDet2.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starDet2.setScaledContents(True)
        self.starDet3 = QLabel(self.btnDetective)
        self.starDet3.setObjectName(u"starDet3")
        self.starDet3.setGeometry(QRect(116, 104, 40, 40))
        self.starDet3.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starDet3.setScaledContents(True)
        self.lblDetectiveText = QLabel(self.btnDetective)
        self.lblDetectiveText.setObjectName(u"lblDetectiveText")
        self.lblDetectiveText.setGeometry(QRect(180, 65, 310, 110))
        self.lblDetectiveText.setStyleSheet(u"font-family: \"Segoe UI\", sans-serif; font-size: 34px; font-weight: 700; color: #5C3B28; background: transparent;")
        self.lblDetectiveText.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.retranslateUi(MinigameSelect)

        QMetaObject.connectSlotsByName(MinigameSelect)
    # setupUi

    def retranslateUi(self, MinigameSelect):
        MinigameSelect.setWindowTitle(QCoreApplication.translate("MinigameSelect", u"SenyaSabi \u2014 MiniGames", None))
        self.imageBg.setText("")
        self.titleLabel.setText(QCoreApplication.translate("MinigameSelect", u"MiniGames", None))
        self.btnBack.setText("")
        self.lblSprintText.setText(QCoreApplication.translate("MinigameSelect", u"Sign\n"
"Sprint", None))
        self.lblQuestText.setText(QCoreApplication.translate("MinigameSelect", u"FingerSpell\n"
"Quest", None))
        self.lblDetectiveText.setText(QCoreApplication.translate("MinigameSelect", u"Sign\n"
"Detective", None))
    # retranslateUi

