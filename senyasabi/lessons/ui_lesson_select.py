# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'lesson_select.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QSizePolicy,
    QWidget)

class Ui_LessonSelect(object):
    def setupUi(self, LessonSelect):
        if not LessonSelect.objectName():
            LessonSelect.setObjectName(u"LessonSelect")
        LessonSelect.resize(1306, 753)
        LessonSelect.setStyleSheet(u"\n"
"QWidget#LessonSelect {\n"
"    background-color: #0f1117;\n"
"}\n"
"QLabel#titleLabel {\n"
"    color: #ffffff;\n"
"    font-size: 32px;\n"
"    font-weight: 800;\n"
"}\n"
"QLabel#subtitleLabel {\n"
"    color: #5a6080;\n"
"    font-size: 14px;\n"
"    letter-spacing: 1px;\n"
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
"QPushButton#lesson1Btn, QPushButton#lesson2Btn, QPushButton#lesson3Btn,\n"
"QPushButton#lesson4Btn, QPushButton#lesson5Btn {\n"
"    background-color: #1a1f2e;\n"
"    color: #ffffff;\n"
"    font-size: 18px;\n"
"    font-weight: 700;\n"
"    border: 2px solid #2a3150;\n"
"    border-radius: 16px;\n"
"    padding: 0px;\n"
"}\n"
"QPushButton#lesson1Btn:hover { background-color: #212840; border-color: #7ec"
                        "fed; }\n"
"QPushButton#lesson2Btn:hover { background-color: #212840; border-color: #7ecfed; }\n"
"QPushButton#lesson3Btn:hover { background-color: #212840; border-color: #7ecfed; }\n"
"QPushButton#lesson4Btn:hover { background-color: #212840; border-color: #7ecfed; }\n"
"QPushButton#lesson5Btn:hover { background-color: #212840; border-color: #7ecfed; }\n"
"   ")
        self.backBtn = QPushButton(LessonSelect)
        self.backBtn.setObjectName(u"backBtn")
        self.backBtn.setGeometry(QRect(40, 32, 160, 36))
        self.titleLabel = QLabel(LessonSelect)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setGeometry(QRect(0, 110, 1306, 50))
        self.titleLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.subtitleLabel = QLabel(LessonSelect)
        self.subtitleLabel.setObjectName(u"subtitleLabel")
        self.subtitleLabel.setGeometry(QRect(0, 166, 1306, 28))
        self.subtitleLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.lesson1Btn = QPushButton(LessonSelect)
        self.lesson1Btn.setObjectName(u"lesson1Btn")
        self.lesson1Btn.setGeometry(QRect(63, 240, 210, 300))
        self.lesson1Btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lesson2Btn = QPushButton(LessonSelect)
        self.lesson2Btn.setObjectName(u"lesson2Btn")
        self.lesson2Btn.setGeometry(QRect(313, 240, 210, 300))
        self.lesson2Btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lesson3Btn = QPushButton(LessonSelect)
        self.lesson3Btn.setObjectName(u"lesson3Btn")
        self.lesson3Btn.setGeometry(QRect(563, 240, 210, 300))
        self.lesson3Btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lesson4Btn = QPushButton(LessonSelect)
        self.lesson4Btn.setObjectName(u"lesson4Btn")
        self.lesson4Btn.setGeometry(QRect(813, 240, 210, 300))
        self.lesson4Btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lesson5Btn = QPushButton(LessonSelect)
        self.lesson5Btn.setObjectName(u"lesson5Btn")
        self.lesson5Btn.setGeometry(QRect(1063, 240, 210, 300))
        self.lesson5Btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.retranslateUi(LessonSelect)

        QMetaObject.connectSlotsByName(LessonSelect)
    # setupUi

    def retranslateUi(self, LessonSelect):
        LessonSelect.setWindowTitle(QCoreApplication.translate("LessonSelect", u"Choose a Lesson", None))
        self.backBtn.setText(QCoreApplication.translate("LessonSelect", u"\u2190 Back", None))
        self.titleLabel.setText(QCoreApplication.translate("LessonSelect", u"Choose a Lesson", None))
        self.subtitleLabel.setText(QCoreApplication.translate("LessonSelect", u"Each lesson covers a group of letters", None))
        self.lesson1Btn.setText("")
        self.lesson2Btn.setText("")
        self.lesson3Btn.setText("")
        self.lesson4Btn.setText("")
        self.lesson5Btn.setText("")
    # retranslateUi

