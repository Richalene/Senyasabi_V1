# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'spell_lesson.ui'
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

class Ui_SpellLesson(object):
    def setupUi(self, SpellLesson):
        if not SpellLesson.objectName():
            SpellLesson.setObjectName(u"SpellLesson")
        SpellLesson.resize(1306, 753)
        SpellLesson.setStyleSheet(u"\n"
"QWidget#SpellLesson {\n"
"    background-color: #0f1117;\n"
"}\n"
"QLabel#lessonTitle {\n"
"    color: #e8f4f8;\n"
"    font-size: 14px;\n"
"    font-weight: 600;\n"
"    letter-spacing: 2px;\n"
"}\n"
"QLabel#wordDisplay {\n"
"    color: #5a6080;\n"
"    font-size: 13px;\n"
"    letter-spacing: 1px;\n"
"}\n"
"QLabel#currentLetterLabel {\n"
"    color: #ffffff;\n"
"    font-size: 80px;\n"
"    font-weight: 800;\n"
"}\n"
"QLabel#letterSubtitle {\n"
"    color: #a87eed;\n"
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
"    padding"
                        ": 8px 20px;\n"
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
"QLabel#holdBarBg {\n"
"    background-color: #1a1f2e;\n"
"    border-radius: 5px;\n"
"}\n"
"QLabel#holdBarFill {\n"
"    background-color: #a87eed;\n"
"    border-radius: 5px;\n"
"}\n"
"QLabel#predictionLabel {\n"
"    color: #5a6080;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"}\n"
"QPushButton#skipBtn {\n"
"    background-color: #1a1f2e;\n"
"    color: #7ecfed;\n"
"    font-size: 13px;\n"
"    font-weight: 600;\n"
"    border: 1px solid #2a3150;\n"
"    border-radius: 8px;\n"
"    padding: 8px 18px;\n"
"}\n"
"QPushButton#skipBtn:hover {\n"
"    background-color: #212840;\n"
"}\n"
"QPushButton#backBtn {\n"
"    background-color: transparent;\n"
"    color: #5a6080;\n"
"    font-size: 13px;\n"
"    font-weight: 500;\n"
"    border: 1px soli"
                        "d #2a3150;\n"
"    border-radius: 8px;\n"
"    padding: 8px 18px;\n"
"}\n"
"QPushButton#backBtn:hover {\n"
"    color: #e8f4f8;\n"
"    border-color: #5a6080;\n"
"}\n"
"QLabel#tilesArea {\n"
"    background: transparent;\n"
"}\n"
"QLabel#camStatusDot {\n"
"    border-radius: 5px;\n"
"}\n"
"   ")
        self.lessonTitle = QLabel(SpellLesson)
        self.lessonTitle.setObjectName(u"lessonTitle")
        self.lessonTitle.setGeometry(QRect(40, 24, 500, 28))
        self.progressLabel = QLabel(SpellLesson)
        self.progressLabel.setObjectName(u"progressLabel")
        self.progressLabel.setGeometry(QRect(40, 56, 300, 22))
        self.scoreLabel = QLabel(SpellLesson)
        self.scoreLabel.setObjectName(u"scoreLabel")
        self.scoreLabel.setGeometry(QRect(1100, 24, 166, 28))
        self.scoreLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.backBtn = QPushButton(SpellLesson)
        self.backBtn.setObjectName(u"backBtn")
        self.backBtn.setGeometry(QRect(1100, 56, 166, 32))
        self.divider = QLabel(SpellLesson)
        self.divider.setObjectName(u"divider")
        self.divider.setGeometry(QRect(0, 96, 1306, 1))
        self.divider.setStyleSheet(u"background-color: #2a3150;")
        self.tilesArea = QLabel(SpellLesson)
        self.tilesArea.setObjectName(u"tilesArea")
        self.tilesArea.setGeometry(QRect(60, 108, 500, 60))
        self.currentLetterLabel = QLabel(SpellLesson)
        self.currentLetterLabel.setObjectName(u"currentLetterLabel")
        self.currentLetterLabel.setGeometry(QRect(90, 640, 160, 100))
        self.currentLetterLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.letterSubtitle = QLabel(SpellLesson)
        self.letterSubtitle.setObjectName(u"letterSubtitle")
        self.letterSubtitle.setGeometry(QRect(80, 620, 300, 22))
        self.refImageLabel = QLabel(SpellLesson)
        self.refImageLabel.setObjectName(u"refImageLabel")
        self.refImageLabel.setGeometry(QRect(50, 110, 500, 481))
        self.refImageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cameraLabel = QLabel(SpellLesson)
        self.cameraLabel.setObjectName(u"cameraLabel")
        self.cameraLabel.setGeometry(QRect(620, 115, 626, 470))
        self.cameraLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camStatusDot = QLabel(SpellLesson)
        self.camStatusDot.setObjectName(u"camStatusDot")
        self.camStatusDot.setGeometry(QRect(624, 119, 10, 10))
        self.camStatusDot.setStyleSheet(u"background-color: #e05252; border-radius: 5px;")
        self.holdBarBg = QLabel(SpellLesson)
        self.holdBarBg.setObjectName(u"holdBarBg")
        self.holdBarBg.setGeometry(QRect(620, 598, 626, 10))
        self.holdBarFill = QLabel(SpellLesson)
        self.holdBarFill.setObjectName(u"holdBarFill")
        self.holdBarFill.setGeometry(QRect(620, 598, 0, 10))
        self.feedbackLabel = QLabel(SpellLesson)
        self.feedbackLabel.setObjectName(u"feedbackLabel")
        self.feedbackLabel.setGeometry(QRect(620, 620, 626, 46))
        self.feedbackLabel.setStyleSheet(u"color: transparent; background-color: transparent;")
        self.feedbackLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.predictionLabel = QLabel(SpellLesson)
        self.predictionLabel.setObjectName(u"predictionLabel")
        self.predictionLabel.setGeometry(QRect(620, 680, 300, 44))
        self.skipBtn = QPushButton(SpellLesson)
        self.skipBtn.setObjectName(u"skipBtn")
        self.skipBtn.setGeometry(QRect(1060, 680, 186, 44))

        self.retranslateUi(SpellLesson)

        QMetaObject.connectSlotsByName(SpellLesson)
    # setupUi

    def retranslateUi(self, SpellLesson):
        SpellLesson.setWindowTitle(QCoreApplication.translate("SpellLesson", u"Spell Mode", None))
        self.lessonTitle.setText(QCoreApplication.translate("SpellLesson", u"SPELL MODE \u2014 GOOD MORNING", None))
        self.progressLabel.setText(QCoreApplication.translate("SpellLesson", u"Letter 1 of 11", None))
        self.scoreLabel.setText(QCoreApplication.translate("SpellLesson", u"Score: 0 / 11", None))
        self.backBtn.setText(QCoreApplication.translate("SpellLesson", u"\u2190 Back", None))
        self.divider.setText("")
        self.tilesArea.setText("")
        self.currentLetterLabel.setText(QCoreApplication.translate("SpellLesson", u"G", None))
        self.letterSubtitle.setText(QCoreApplication.translate("SpellLesson", u"SIGN THIS LETTER", None))
        self.refImageLabel.setText(QCoreApplication.translate("SpellLesson", u"Reference image", None))
        self.cameraLabel.setText(QCoreApplication.translate("SpellLesson", u"Camera starting...", None))
        self.camStatusDot.setText("")
        self.holdBarBg.setText("")
        self.holdBarFill.setText("")
        self.feedbackLabel.setText("")
        self.predictionLabel.setText(QCoreApplication.translate("SpellLesson", u"Waiting for hand...", None))
        self.skipBtn.setText(QCoreApplication.translate("SpellLesson", u"Skip letter \u2192", None))
    # retranslateUi

