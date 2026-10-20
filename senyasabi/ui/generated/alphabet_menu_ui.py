# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'alphabet_menu.ui'
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

class Ui_AlphabetMenu(object):
    def setupUi(self, AlphabetMenu):
        if not AlphabetMenu.objectName():
            AlphabetMenu.setObjectName(u"AlphabetMenu")
        AlphabetMenu.resize(1920, 1080)
        AlphabetMenu.setStyleSheet(u"\n"
"QWidget#AlphabetMenu {\n"
"    background-color: #C2D076;\n"
"}\n"
"QLabel#titleLabel {\n"
"    color: #F5E5CF;\n"
"    font-size: 36px;\n"
"    font-weight: 800;\n"
"}\n"
"QLabel#subtitleLabel {\n"
"    color: #C2D076;\n"
"    font-size: 15px;\n"
"    font-weight: 400;\n"
"    letter-spacing: 1px;\n"
"}\n"
"QLabel#divider {\n"
"    background-color: #704833;\n"
"}\n"
"QPushButton#learnBtn {\n"
"    background-color: #0f3a0f;\n"
"    color: #F5E5CF;\n"
"    font-size: 20px;\n"
"    font-weight: 700;\n"
"    border: 2px solid #704833;\n"
"    border-radius: 20px;\n"
"    text-align: left;\n"
"    padding: 32px 40px;\n"
"}\n"
"QPushButton#learnBtn:hover {\n"
"    background-color: #123f12;\n"
"    border-color: #C2D076;\n"
"}\n"
"QPushButton#spellBtn {\n"
"    background-color: #0f3a0f;\n"
"    color: #F5E5CF;\n"
"    font-size: 20px;\n"
"    font-weight: 700;\n"
"    border: 2px solid #704833;\n"
"    border-radius: 20px;\n"
"    text-align: left;\n"
"    padding: 32px 40px;\n"
"}\n"
"QPushButton#spellBtn:"
                        "hover {\n"
"    background-color: #123f12;\n"
"    border-color: #704833;\n"
"}\n"
"QPushButton#backBtn {\n"
"    background-color: transparent;\n"
"    color: #C2D076;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"    border: 1px solid #704833;\n"
"    border-radius: 8px;\n"
"    padding: 8px 18px;\n"
"}\n"
"QPushButton#backBtn:hover {\n"
"    color: #F5E5CF;\n"
"    border-color: #C2D076;\n"
"}\n"
"QLabel#learnIcon {\n"
"    color: #C2D076;\n"
"    font-size: 48px;\n"
"}\n"
"QLabel#spellIcon {\n"
"    color: #704833;\n"
"    font-size: 48px;\n"
"}\n"
"QLabel#learnDesc {\n"
"    color: #C2D076;\n"
"    font-size: 13px;\n"
"    font-weight: 400;\n"
"}\n"
"QLabel#spellDesc {\n"
"    color: #C2D076;\n"
"    font-size: 13px;\n"
"    font-weight: 400;\n"
"}\n"
"QLabel#learnTag {\n"
"    color: #C2D076;\n"
"    font-size: 11px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2px;\n"
"}\n"
"QLabel#spellTag {\n"
"    color: #704833;\n"
"    font-size: 11px;\n"
"    font-weight: 700;\n"
"    letter-spacing:"
                        " 2px;\n"
"}\n"
"   ")
        self.backBtn = QPushButton(AlphabetMenu)
        self.backBtn.setObjectName(u"backBtn")
        self.backBtn.setGeometry(QRect(40, 32, 140, 36))
        self.backBtn.setStyleSheet(u"color: rgb(0, 0, 0);")
        self.subtitleLabel = QLabel(AlphabetMenu)
        self.subtitleLabel.setObjectName(u"subtitleLabel")
        self.subtitleLabel.setGeometry(QRect(0, 182, 1306, 28))
        self.subtitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.divider = QLabel(AlphabetMenu)
        self.divider.setObjectName(u"divider")
        self.divider.setGeometry(QRect(453, 228, 400, 1))
        self.learnBtn = QPushButton(AlphabetMenu)
        self.learnBtn.setObjectName(u"learnBtn")
        self.learnBtn.setGeometry(QRect(183, 270, 420, 280))
        self.learnBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.learnTag = QLabel(AlphabetMenu)
        self.learnTag.setObjectName(u"learnTag")
        self.learnTag.setGeometry(QRect(223, 390, 340, 22))
        self.learnTag.setStyleSheet(u"color: #C2D076; font-size: 11px; font-weight: 700; letter-spacing: 2px; background: transparent;")
        self.learnTitle = QLabel(AlphabetMenu)
        self.learnTitle.setObjectName(u"learnTitle")
        self.learnTitle.setGeometry(QRect(223, 416, 340, 36))
        self.learnTitle.setStyleSheet(u"color: #F5E5CF; font-size: 22px; font-weight: 700; background: transparent;")
        self.spellBtn = QPushButton(AlphabetMenu)
        self.spellBtn.setObjectName(u"spellBtn")
        self.spellBtn.setGeometry(QRect(703, 270, 420, 280))
        self.spellBtn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.spellTag = QLabel(AlphabetMenu)
        self.spellTag.setObjectName(u"spellTag")
        self.spellTag.setGeometry(QRect(743, 390, 340, 22))
        self.spellTag.setStyleSheet(u"color: #704833; font-size: 11px; font-weight: 700; letter-spacing: 2px; background: transparent;")
        self.spellTitle = QLabel(AlphabetMenu)
        self.spellTitle.setObjectName(u"spellTitle")
        self.spellTitle.setGeometry(QRect(743, 416, 340, 36))
        self.spellTitle.setStyleSheet(u"color: #F5E5CF; font-size: 22px; font-weight: 700; background: transparent;")
        self.spellDesc = QLabel(AlphabetMenu)
        self.spellDesc.setObjectName(u"spellDesc")
        self.spellDesc.setGeometry(QRect(743, 456, 340, 60))
        self.spellDesc.setStyleSheet(u"color: #C2D076; font-size: 13px; background: transparent;")

        self.retranslateUi(AlphabetMenu)

        QMetaObject.connectSlotsByName(AlphabetMenu)
    # setupUi

    def retranslateUi(self, AlphabetMenu):
        AlphabetMenu.setWindowTitle(QCoreApplication.translate("AlphabetMenu", u"FSL Alphabet", None))
        self.backBtn.setText(QCoreApplication.translate("AlphabetMenu", u"\u2190 Back to Menu", None))
        self.subtitleLabel.setText(QCoreApplication.translate("AlphabetMenu", u"Choose a mode to get started", None))
        self.divider.setText("")
        self.learnBtn.setText("")
        self.learnTag.setText(QCoreApplication.translate("AlphabetMenu", u"LEARN MODE", None))
        self.learnTitle.setText(QCoreApplication.translate("AlphabetMenu", u"Alphabet Lessons", None))
        self.spellBtn.setText("")
        self.spellTag.setText(QCoreApplication.translate("AlphabetMenu", u"SPELL MODE", None))
        self.spellTitle.setText(QCoreApplication.translate("AlphabetMenu", u"Spell Words", None))
        self.spellDesc.setText(QCoreApplication.translate("AlphabetMenu", u"Fingerspell words letter by letter", None))
    # retranslateUi

