# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'spell_category.ui'
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

class Ui_SpellCategory(object):
    def setupUi(self, SpellCategory):
        if not SpellCategory.objectName():
            SpellCategory.setObjectName(u"SpellCategory")
        SpellCategory.resize(1306, 753)
        SpellCategory.setStyleSheet(u"\n"
"QWidget#SpellCategory {\n"
"    background-color: #0f1117;\n"
"}\n"
"QLabel#titleLabel {\n"
"    color: #ffffff;\n"
"    font-size: 32px;\n"
"    font-weight: 800;\n"
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
"QWidget#scrollContents {\n"
"    background: transparent;\n"
"}\n"
"   ")
        self.backBtn = QPushButton(SpellCategory)
        self.backBtn.setObjectName(u"backBtn")
        self.backBtn.setGeometry(QRect(40, 32, 160, 36))
        self.titleLabel = QLabel(SpellCategory)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setGeometry(QRect(0, 100, 1306, 48))
        self.titleLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.subtitleLabel = QLabel(SpellCategory)
        self.subtitleLabel.setObjectName(u"subtitleLabel")
        self.subtitleLabel.setGeometry(QRect(0, 154, 1306, 26))
        self.subtitleLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.divider = QLabel(SpellCategory)
        self.divider.setObjectName(u"divider")
        self.divider.setGeometry(QRect(0, 192, 1306, 1))
        self.scrollArea = QScrollArea(SpellCategory)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(QRect(0, 200, 1306, 540))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollContents = QWidget()
        self.scrollContents.setObjectName(u"scrollContents")
        self.scrollContents.setGeometry(QRect(0, 0, 1306, 540))
        self.scrollArea.setWidget(self.scrollContents)

        self.retranslateUi(SpellCategory)

        QMetaObject.connectSlotsByName(SpellCategory)
    # setupUi

    def retranslateUi(self, SpellCategory):
        SpellCategory.setWindowTitle(QCoreApplication.translate("SpellCategory", u"Spell \u2014 Choose Category", None))
        self.backBtn.setText(QCoreApplication.translate("SpellCategory", u"\u2190 Back", None))
        self.titleLabel.setText(QCoreApplication.translate("SpellCategory", u"Spell a Word", None))
        self.subtitleLabel.setText(QCoreApplication.translate("SpellCategory", u"Choose a category", None))
        self.divider.setText("")
    # retranslateUi

