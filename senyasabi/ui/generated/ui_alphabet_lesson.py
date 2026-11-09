# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'alphabet_lesson.ui'
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

class Ui_AlphabetLesson(object):
    def setupUi(self, AlphabetLesson):
        if not AlphabetLesson.objectName():
            AlphabetLesson.setObjectName(u"AlphabetLesson")
        AlphabetLesson.resize(1306, 753)
        AlphabetLesson.setStyleSheet(u"\n"
"QWidget#AlphabetLesson {\n"
"    background-color: #0f1117;\n"
"}\n"
"QLabel#lessonTitle {\n"
"    color: #e8f4f8;\n"
"    font-size: 15px;\n"
"    font-weight: 600;\n"
"    letter-spacing: 2px;\n"
"}\n"
"QLabel#letterDisplay {\n"
"    color: #ffffff;\n"
"    font-size: 96px;\n"
"    font-weight: 800;\n"
"}\n"
"QLabel#letterSubtitle {\n"
"    color: #7ecfed;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"    letter-spacing: 3px;\n"
"}\n"
"QLabel#refImageLabel {\n"
"    background-color: #1a1f2e;\n"
"    border: 2px solid #2a3150;\n"
"    border-radius: 16px;\n"
"}\n"
"QLabel#cameraLabel {\n"
"    background-color: #111520;\n"
"    border: 2px solid #2a3150;\n"
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
"QLabel#progressLabel {\n"
"    color: #5a6080;\n"
"    font-size: 13px;\n"
"    font-weig"
                        "ht: 500;\n"
"    letter-spacing: 1px;\n"
"}\n"
"QLabel#holdBarBg {\n"
"    background-color: #1a1f2e;\n"
"    border-radius: 5px;\n"
"}\n"
"QLabel#holdBarFill {\n"
"    background-color: #7ecfed;\n"
"    border-radius: 5px;\n"
"}\n"
"QPushButton#nextBtn {\n"
"    background-color: #7ecfed;\n"
"    color: #0f1117;\n"
"    font-size: 14px;\n"
"    font-weight: 700;\n"
"    letter-spacing: 1px;\n"
"    border: none;\n"
"    border-radius: 10px;\n"
"    padding: 10px 28px;\n"
"}\n"
"QPushButton#nextBtn:hover {\n"
"    background-color: #a8dff5;\n"
"}\n"
"QPushButton#nextBtn:disabled {\n"
"    background-color: #2a3150;\n"
"    color: #3a4060;\n"
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
"QLabel#scoreLabel {\n"
"    color: #5a6"
                        "080;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"}\n"
"QLabel#camStatusDot {\n"
"    border-radius: 5px;\n"
"}\n"
"   ")
        self.lessonTitle = QLabel(AlphabetLesson)
        self.lessonTitle.setObjectName(u"lessonTitle")
        self.lessonTitle.setGeometry(QRect(40, 24, 400, 28))
        self.progressLabel = QLabel(AlphabetLesson)
        self.progressLabel.setObjectName(u"progressLabel")
        self.progressLabel.setGeometry(QRect(40, 56, 300, 22))
        self.scoreLabel = QLabel(AlphabetLesson)
        self.scoreLabel.setObjectName(u"scoreLabel")
        self.scoreLabel.setGeometry(QRect(1100, 24, 166, 28))
        self.scoreLabel.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.backBtn = QPushButton(AlphabetLesson)
        self.backBtn.setObjectName(u"backBtn")
        self.backBtn.setGeometry(QRect(1100, 56, 166, 32))
        self.divider = QLabel(AlphabetLesson)
        self.divider.setObjectName(u"divider")
        self.divider.setGeometry(QRect(0, 96, 1306, 1))
        self.divider.setStyleSheet(u"background-color: #2a3150;")
        self.letterDisplay = QLabel(AlphabetLesson)
        self.letterDisplay.setObjectName(u"letterDisplay")
        self.letterDisplay.setGeometry(QRect(80, 115, 200, 120))
        self.letterDisplay.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.letterSubtitle = QLabel(AlphabetLesson)
        self.letterSubtitle.setObjectName(u"letterSubtitle")
        self.letterSubtitle.setGeometry(QRect(83, 230, 300, 22))
        self.refImageLabel = QLabel(AlphabetLesson)
        self.refImageLabel.setObjectName(u"refImageLabel")
        self.refImageLabel.setGeometry(QRect(60, 265, 500, 380))
        self.refImageLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.refImageLabel.setScaledContents(False)
        self.cameraLabel = QLabel(AlphabetLesson)
        self.cameraLabel.setObjectName(u"cameraLabel")
        self.cameraLabel.setGeometry(QRect(620, 115, 626, 470))
        self.cameraLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.camStatusDot = QLabel(AlphabetLesson)
        self.camStatusDot.setObjectName(u"camStatusDot")
        self.camStatusDot.setGeometry(QRect(624, 119, 10, 10))
        self.camStatusDot.setStyleSheet(u"background-color: #e05252; border-radius: 5px;")
        self.holdBarBg = QLabel(AlphabetLesson)
        self.holdBarBg.setObjectName(u"holdBarBg")
        self.holdBarBg.setGeometry(QRect(620, 598, 626, 10))
        self.holdBarFill = QLabel(AlphabetLesson)
        self.holdBarFill.setObjectName(u"holdBarFill")
        self.holdBarFill.setGeometry(QRect(620, 598, 0, 10))
        self.feedbackLabel = QLabel(AlphabetLesson)
        self.feedbackLabel.setObjectName(u"feedbackLabel")
        self.feedbackLabel.setGeometry(QRect(620, 620, 626, 46))
        self.feedbackLabel.setAlignment(Qt.AlignHCenter|Qt.AlignVCenter)
        self.feedbackLabel.setStyleSheet(u"color: transparent; background-color: transparent;")
        self.nextBtn = QPushButton(AlphabetLesson)
        self.nextBtn.setObjectName(u"nextBtn")
        self.nextBtn.setGeometry(QRect(1060, 680, 186, 44))
        self.nextBtn.setEnabled(True)
        self.predictionLabel = QLabel(AlphabetLesson)
        self.predictionLabel.setObjectName(u"predictionLabel")
        self.predictionLabel.setGeometry(QRect(620, 680, 300, 44))
        self.predictionLabel.setStyleSheet(u"color: #5a6080; font-size: 13px; font-weight: 500;")

        self.retranslateUi(AlphabetLesson)

        QMetaObject.connectSlotsByName(AlphabetLesson)
    # setupUi

    def retranslateUi(self, AlphabetLesson):
        AlphabetLesson.setWindowTitle(QCoreApplication.translate("AlphabetLesson", u"FSL Alphabet Lesson", None))
        self.lessonTitle.setText(QCoreApplication.translate("AlphabetLesson", u"FSL ALPHABET \u2014 LESSON 1", None))
        self.progressLabel.setText(QCoreApplication.translate("AlphabetLesson", u"Letter 1 of 6", None))
        self.scoreLabel.setText(QCoreApplication.translate("AlphabetLesson", u"Score: 0 / 6", None))
        self.backBtn.setText(QCoreApplication.translate("AlphabetLesson", u"\u2190 Back to Menu", None))
        self.divider.setText("")
        self.letterDisplay.setText(QCoreApplication.translate("AlphabetLesson", u"A", None))
        self.letterSubtitle.setText(QCoreApplication.translate("AlphabetLesson", u"SIGN THIS LETTER", None))
        self.refImageLabel.setText(QCoreApplication.translate("AlphabetLesson", u"Reference image", None))
        self.cameraLabel.setText(QCoreApplication.translate("AlphabetLesson", u"Camera starting...", None))
        self.camStatusDot.setText("")
        self.holdBarBg.setText("")
        self.holdBarFill.setText("")
        self.feedbackLabel.setText("")
        self.nextBtn.setText(QCoreApplication.translate("AlphabetLesson", u"Skip \u2192", None))
        self.predictionLabel.setText(QCoreApplication.translate("AlphabetLesson", u"Waiting for hand...", None))
    # retranslateUi

