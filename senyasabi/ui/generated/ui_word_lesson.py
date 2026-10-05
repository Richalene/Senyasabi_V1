# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'word_lesson.ui'
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

class Ui_WordLesson(object):
    def setupUi(self, WordLesson):
        if not WordLesson.objectName():
            WordLesson.setObjectName(u"WordLesson")
        WordLesson.resize(1306, 753)
        WordLesson.setStyleSheet(u"\n"
"QWidget#WordLesson {\n"
"    background-color: #0f1117;\n"
"}\n"
"QLabel#lessonTitle {\n"
"    color: #e8f4f8;\n"
"    font-size: 15px;\n"
"    font-weight: 600;\n"
"    letter-spacing: 2px;\n"
"}\n"
"QLabel#progressLabel {\n"
"    color: #5a6080;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"    letter-spacing: 1px;\n"
"}\n"
"QLabel#scoreLabel {\n"
"    color: #5a6080;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"}\n"
"QLabel#divider {\n"
"    background-color: #2a3150;\n"
"}\n"
"QLabel#wordDisplay {\n"
"    color: #ffffff;\n"
"    font-size: 32px;\n"
"    font-weight: 800;\n"
"}\n"
"QLabel#wordSubtitle {\n"
"    color: #5ecf8a;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"    letter-spacing: 3px;\n"
"}\n"
"QLabel#refImageLabel {\n"
"    background-color: #1a1f2e;\n"
"    border: 2px solid #2a3150;\n"
"    border-radius: 16px;\n"
"    color: #3a4060;\n"
"    font-size: 14px;\n"
"}\n"
"QLabel#cameraLabel {\n"
"    background-color: #111520;\n"
"    border: 2px solid #2a3150;\n"
""
                        "    border-radius: 16px;\n"
"    color: #3a4060;\n"
"    font-size: 14px;\n"
"}\n"
"QLabel#feedbackLabel {\n"
"    font-size: 18px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 1px;\n"
"    border-radius: 10px;\n"
"    padding: 8px 20px;\n"
"}\n"
"QLabel#holdBarBg {\n"
"    background-color: #1a1f2e;\n"
"    border-radius: 5px;\n"
"}\n"
"QLabel#holdBarFill {\n"
"    background-color: #5ecf8a;\n"
"    border-radius: 5px;\n"
"}\n"
"QLabel#predictionLabel {\n"
"    color: #5a6080;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"}\n"
"QLabel#camStatusDot {\n"
"    border-radius: 5px;\n"
"}\n"
"QPushButton#skipBtn {\n"
"    background-color: #7ecfed;\n"
"    color: #0f1117;\n"
"    font-size: 14px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 1px;\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"    padding: 10px 28px;\n"
"}\n"
"QPushButton#skipBtn:hover {\n"
"    background-color: #a8dff5;\n"
"}\n"
"QPushButton#backBtn {\n"
"    background-color: transparent;\n"
"    color: #5a6080;\n"
"    "
                        "font-size: 13px;\n"
"    font-weight: 500;\n"
"    border: 1px solid #2a3150;\n"
"    border-radius: 8px;\n"
"    padding: 8px 18px;\n"
"}\n"
"QPushButton#backBtn:hover {\n"
"    color: #e8f4f8;\n"
"    border-color: #5a6080;\n"
"}\n"
"   ")
        self.lessonTitle = QLabel(WordLesson)
        self.lessonTitle.setObjectName(u"lessonTitle")
        self.lessonTitle.setGeometry(QRect(40, 24, 600, 28))
        self.progressLabel = QLabel(WordLesson)
        self.progressLabel.setObjectName(u"progressLabel")
        self.progressLabel.setGeometry(QRect(40, 56, 300, 22))
        self.scoreLabel = QLabel(WordLesson)
        self.scoreLabel.setObjectName(u"scoreLabel")
        self.scoreLabel.setGeometry(QRect(1100, 24, 166, 28))
        self.scoreLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.backBtn = QPushButton(WordLesson)
        self.backBtn.setObjectName(u"backBtn")
        self.backBtn.setGeometry(QRect(1100, 56, 166, 32))
        self.divider = QLabel(WordLesson)
        self.divider.setObjectName(u"divider")
        self.divider.setGeometry(QRect(0, 96, 1306, 1))
        self.divider.setStyleSheet(u"background-color: #2a3150;")
        self.wordDisplay = QLabel(WordLesson)
        self.wordDisplay.setObjectName(u"wordDisplay")
        self.wordDisplay.setGeometry(QRect(50, 630, 540, 60))
        self.wordDisplay.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.wordDisplay.setWordWrap(True)
        self.wordSubtitle = QLabel(WordLesson)
        self.wordSubtitle.setObjectName(u"wordSubtitle")
        self.wordSubtitle.setGeometry(QRect(50, 610, 300, 22))
        self.refImageLabel = QLabel(WordLesson)
        self.refImageLabel.setObjectName(u"refImageLabel")
        self.refImageLabel.setGeometry(QRect(50, 170, 500, 420))
        self.refImageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cameraLabel = QLabel(WordLesson)
        self.cameraLabel.setObjectName(u"cameraLabel")
        self.cameraLabel.setGeometry(QRect(610, 170, 626, 470))
        self.cameraLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camStatusDot = QLabel(WordLesson)
        self.camStatusDot.setObjectName(u"camStatusDot")
        self.camStatusDot.setGeometry(QRect(624, 119, 10, 10))
        self.camStatusDot.setStyleSheet(u"background-color: #e05252; border-radius: 5px;")
        self.holdBarBg = QLabel(WordLesson)
        self.holdBarBg.setObjectName(u"holdBarBg")
        self.holdBarBg.setGeometry(QRect(610, 660, 626, 10))
        self.holdBarFill = QLabel(WordLesson)
        self.holdBarFill.setObjectName(u"holdBarFill")
        self.holdBarFill.setGeometry(QRect(620, 598, 0, 10))
        self.feedbackLabel = QLabel(WordLesson)
        self.feedbackLabel.setObjectName(u"feedbackLabel")
        self.feedbackLabel.setGeometry(QRect(620, 620, 626, 46))
        self.feedbackLabel.setStyleSheet(u"color:transparent; background-color:transparent;")
        self.feedbackLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.predictionLabel = QLabel(WordLesson)
        self.predictionLabel.setObjectName(u"predictionLabel")
        self.predictionLabel.setGeometry(QRect(620, 680, 400, 44))
        self.skipBtn = QPushButton(WordLesson)
        self.skipBtn.setObjectName(u"skipBtn")
        self.skipBtn.setGeometry(QRect(1060, 680, 186, 44))

        self.retranslateUi(WordLesson)

        QMetaObject.connectSlotsByName(WordLesson)
    # setupUi

    def retranslateUi(self, WordLesson):
        WordLesson.setWindowTitle(QCoreApplication.translate("WordLesson", u"Word Lesson", None))
        self.lessonTitle.setText(QCoreApplication.translate("WordLesson", u"WORD LESSON \u2014 GREETING", None))
        self.progressLabel.setText(QCoreApplication.translate("WordLesson", u"Word 1 of 10", None))
        self.scoreLabel.setText(QCoreApplication.translate("WordLesson", u"Score: 0 / 10", None))
        self.backBtn.setText(QCoreApplication.translate("WordLesson", u"\u2190 Back", None))
        self.divider.setText("")
        self.wordDisplay.setText(QCoreApplication.translate("WordLesson", u"GOOD MORNING", None))
        self.wordSubtitle.setText(QCoreApplication.translate("WordLesson", u"SIGN THIS WORD", None))
        self.refImageLabel.setText(QCoreApplication.translate("WordLesson", u"\U0001f4f9  Video coming soon", None))
        self.cameraLabel.setText(QCoreApplication.translate("WordLesson", u"Camera starting...", None))
        self.camStatusDot.setText("")
        self.holdBarBg.setText("")
        self.holdBarFill.setText("")
        self.feedbackLabel.setText("")
        self.predictionLabel.setText(QCoreApplication.translate("WordLesson", u"Waiting for hand...", None))
        self.skipBtn.setText(QCoreApplication.translate("WordLesson", u"Skip \u2192", None))
    # retranslateUi

