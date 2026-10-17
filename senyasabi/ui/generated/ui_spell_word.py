# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'spell_word.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QWidget)

class Ui_SpellWord(object):
    def setupUi(self, SpellWord):
        if not SpellWord.objectName():
            SpellWord.setObjectName(u"SpellWord")
        SpellWord.resize(1306, 753)
        SpellWord.setStyleSheet(u"\n"
"QWidget#SpellWord {\n"
"    background-color: #0f1117;\n"
"}\n"
"QLabel#titleLabel {\n"
"    color: #ffffff;\n"
"    font-size: 32px;\n"
"    font-weight: 800;\n"
"    background: transparent;\n"
"}\n"
"QLabel#categoryLabel {\n"
"    color: #a87eed;\n"
"    font-size: 13px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 2px;\n"
"    background: transparent;\n"
"}\n"
"QLabel#subtitleLabel {\n"
"    color: #5a6080;\n"
"    font-size: 14px;\n"
"    letter-spacing: 1px;\n"
"    background: transparent;\n"
"}\n"
"QLabel#divider {\n"
"    background-color: #2a3150;\n"
"}\n"
"QPushButton#backBtn {\n"
"    background-color: transparent;\n"
"    color: #5a6080;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"    border: 1px solid #2a3150;\n"
"    border-radius: 8px;\n"
"    padding: 8px 18px;\n"
"}\n"
"QPushButton#backBtn:hover {\n"
"    color: #e8f4f8;\n"
"    border-color: #5a6080;\n"
"}\n"
"QScrollArea#scrollArea {\n"
"    border: none;\n"
"    background: transparent;\n"
"}\n"
"QWidget#scrollContents"
                        " {\n"
"    background: transparent;\n"
"}\n"
"   ")
        self.backBtn = QPushButton(SpellWord)
        self.backBtn.setObjectName(u"backBtn")
        self.backBtn.setGeometry(QRect(40, 32, 160, 36))
        self.categoryLabel = QLabel(SpellWord)
        self.categoryLabel.setObjectName(u"categoryLabel")
        self.categoryLabel.setGeometry(QRect(0, 100, 1306, 24))
        self.categoryLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.titleLabel = QLabel(SpellWord)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setGeometry(QRect(0, 126, 1306, 48))
        self.titleLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.subtitleLabel = QLabel(SpellWord)
        self.subtitleLabel.setObjectName(u"subtitleLabel")
        self.subtitleLabel.setGeometry(QRect(0, 178, 1306, 26))
        self.subtitleLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.divider = QLabel(SpellWord)
        self.divider.setObjectName(u"divider")
        self.divider.setGeometry(QRect(0, 216, 1306, 1))
        self.scrollArea = QScrollArea(SpellWord)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(QRect(0, 224, 1306, 516))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollContents = QWidget()
        self.scrollContents.setObjectName(u"scrollContents")
        self.scrollContents.setGeometry(QRect(0, 0, 1306, 516))
        self.scrollArea.setWidget(self.scrollContents)

        self.retranslateUi(SpellWord)

        QMetaObject.connectSlotsByName(SpellWord)
    # setupUi

    def retranslateUi(self, SpellWord):
        SpellWord.setWindowTitle(QCoreApplication.translate("SpellWord", u"Spell \u2014 Choose Word", None))
        self.backBtn.setText(QCoreApplication.translate("SpellWord", u"\u2190 Back", None))
        self.categoryLabel.setText(QCoreApplication.translate("SpellWord", u"GREETING", None))
        self.titleLabel.setText(QCoreApplication.translate("SpellWord", u"Choose a Word", None))
        self.subtitleLabel.setText(QCoreApplication.translate("SpellWord", u"You will fingerspell it letter by letter", None))
        self.divider.setText("")
    # retranslateUi

