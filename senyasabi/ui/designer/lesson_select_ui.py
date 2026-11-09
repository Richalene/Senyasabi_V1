# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'lesson_select.ui'
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

class Ui_LessonSelect(object):
    def setupUi(self, LessonSelect):
        if not LessonSelect.objectName():
            LessonSelect.setObjectName(u"LessonSelect")
        LessonSelect.resize(1920, 1080)
        LessonSelect.setStyleSheet(u"\n"
"QWidget#LessonSelect { background-color: #C2D076; font-family: \"Segoe UI\"; }\n"
"   ")
        self.imageBg = QLabel(LessonSelect)
        self.imageBg.setObjectName(u"imageBg")
        self.imageBg.setGeometry(QRect(0, 0, 1920, 1080))
        self.imageBg.setPixmap(QPixmap(u"../../resources/img/gen_bg.png"))
        self.imageBg.setScaledContents(True)
        self.lblMyLessons = QLabel(LessonSelect)
        self.lblMyLessons.setObjectName(u"lblMyLessons")
        self.lblMyLessons.setGeometry(QRect(280, 180, 380, 70))
        self.lblMyLessons.setStyleSheet(u"font-family: \"Cherry Bomb One\", cursive, sans-serif; font-size: 46px; color: #4F3222; background: transparent;")
        self.lblMiniGames = QLabel(LessonSelect)
        self.lblMiniGames.setObjectName(u"lblMiniGames")
        self.lblMiniGames.setGeometry(QRect(1260, 180, 380, 70))
        self.lblMiniGames.setStyleSheet(u"font-family: \"Cherry Bomb One\", cursive, sans-serif; font-size: 46px; color: #4F3222; background: transparent;")
        self.btnBack = QPushButton(LessonSelect)
        self.btnBack.setObjectName(u"btnBack")
        self.btnBack.setGeometry(QRect(1810, 160, 68, 68))
        self.btnBack.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.divider = QFrame(LessonSelect)
        self.divider.setObjectName(u"divider")
        self.divider.setGeometry(QRect(956, 240, 8, 720))
        self.divider.setStyleSheet(u"border: 2px dashed #C8DA86;")
        self.divider.setFrameShape(QFrame.Shape.VLine)
        self.btnLesson1 = QPushButton(LessonSelect)
        self.btnLesson1.setObjectName(u"btnLesson1")
        self.btnLesson1.setGeometry(QRect(180, 300, 500, 92))
        self.btnLesson1.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLesson1.setStyleSheet(u"\n"
"QPushButton {\n"
"  background-color: #FFFDF0;\n"
"  border: 4px solid #FFFFFF;\n"
"  border-radius: 42px;\n"
"  color: #4F3222;\n"
"  font-family: 'Segoe UI', sans-serif;\n"
"  font-size: 28px;\n"
"  font-weight: 600;\n"
"}\n"
"QPushButton:hover {\n"
"  background-color: #FFF3BD;\n"
"}\n"
"    ")
        self.btnLesson2 = QPushButton(LessonSelect)
        self.btnLesson2.setObjectName(u"btnLesson2")
        self.btnLesson2.setGeometry(QRect(300, 415, 500, 92))
        self.btnLesson2.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLesson2.setStyleSheet(u"\n"
"QPushButton {\n"
"  background-color: #FFFDF0;\n"
"  border: 4px solid #FFFFFF;\n"
"  border-radius: 42px;\n"
"  color: #4F3222;\n"
"  font-family: 'Segoe UI', sans-serif;\n"
"  font-size: 28px;\n"
"  font-weight: 600;\n"
"}\n"
"QPushButton:hover {\n"
"  background-color: #FFF3BD;\n"
"}\n"
"    ")
        self.btnLesson3 = QPushButton(LessonSelect)
        self.btnLesson3.setObjectName(u"btnLesson3")
        self.btnLesson3.setGeometry(QRect(180, 530, 500, 92))
        self.btnLesson3.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLesson3.setStyleSheet(u"\n"
"QPushButton {\n"
"  background-color: #FFFDF0;\n"
"  border: 4px solid #FFFFFF;\n"
"  border-radius: 42px;\n"
"  color: #4F3222;\n"
"  font-family: 'Segoe UI', sans-serif;\n"
"  font-size: 28px;\n"
"  font-weight: 600;\n"
"}\n"
"QPushButton:hover {\n"
"  background-color: #FFF3BD;\n"
"}\n"
"    ")
        self.btnLesson4 = QPushButton(LessonSelect)
        self.btnLesson4.setObjectName(u"btnLesson4")
        self.btnLesson4.setGeometry(QRect(300, 645, 500, 92))
        self.btnLesson4.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLesson4.setStyleSheet(u"\n"
"QPushButton {\n"
"  background-color: #FFFDF0;\n"
"  border: 4px solid #FFFFFF;\n"
"  border-radius: 42px;\n"
"  color: #4F3222;\n"
"  font-family: 'Segoe UI', sans-serif;\n"
"  font-size: 28px;\n"
"  font-weight: 600;\n"
"}\n"
"QPushButton:hover {\n"
"  background-color: #FFF3BD;\n"
"}\n"
"    ")
        self.btnLesson5 = QPushButton(LessonSelect)
        self.btnLesson5.setObjectName(u"btnLesson5")
        self.btnLesson5.setGeometry(QRect(180, 760, 500, 92))
        self.btnLesson5.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnLesson5.setStyleSheet(u"\n"
"QPushButton {\n"
"  background-color: #FFFDF0;\n"
"  border: 4px solid #FFFFFF;\n"
"  border-radius: 42px;\n"
"  color: #4F3222;\n"
"  font-family: 'Segoe UI', sans-serif;\n"
"  font-size: 28px;\n"
"  font-weight: 600;\n"
"}\n"
"QPushButton:hover {\n"
"  background-color: #FFF3BD;\n"
"}\n"
"    ")
        self.btnSprint = QPushButton(LessonSelect)
        self.btnSprint.setObjectName(u"btnSprint")
        self.btnSprint.setGeometry(QRect(1020, 340, 380, 150))
        self.btnSprint.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnSprint.setStyleSheet(u"\n"
"QPushButton {\n"
"  background-color: #FFFDF0;\n"
"  border: 4px solid #FFFFFF;\n"
"  border-radius: 46px;\n"
"  color: #4F3222;\n"
"  font-family: 'Segoe UI', sans-serif;\n"
"  font-size: 26px;\n"
"  font-weight: 600;\n"
"  padding-left: 50px;\n"
"}\n"
"QPushButton:hover {\n"
"  background-color: #FFF3BD;\n"
"}\n"
"    ")
        self.starSprint = QLabel(self.btnSprint)
        self.starSprint.setObjectName(u"starSprint")
        self.starSprint.setGeometry(QRect(45, 52, 42, 42))
        self.starSprint.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starSprint.setScaledContents(True)
        self.btnQuest = QPushButton(LessonSelect)
        self.btnQuest.setObjectName(u"btnQuest")
        self.btnQuest.setGeometry(QRect(1460, 340, 380, 150))
        self.btnQuest.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnQuest.setStyleSheet(u"\n"
"QPushButton {\n"
"  background-color: #FFFDF0;\n"
"  border: 4px solid #FFFFFF;\n"
"  border-radius: 46px;\n"
"  color: #4F3222;\n"
"  font-family: 'Segoe UI', sans-serif;\n"
"  font-size: 26px;\n"
"  font-weight: 600;\n"
"  padding-left: 50px;\n"
"}\n"
"QPushButton:hover {\n"
"  background-color: #FFF3BD;\n"
"}\n"
"    ")
        self.starQuest1 = QLabel(self.btnQuest)
        self.starQuest1.setObjectName(u"starQuest1")
        self.starQuest1.setGeometry(QRect(45, 34, 40, 40))
        self.starQuest1.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starQuest1.setScaledContents(True)
        self.starQuest2 = QLabel(self.btnQuest)
        self.starQuest2.setObjectName(u"starQuest2")
        self.starQuest2.setGeometry(QRect(45, 78, 40, 40))
        self.starQuest2.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starQuest2.setScaledContents(True)
        self.btnExpression = QPushButton(LessonSelect)
        self.btnExpression.setObjectName(u"btnExpression")
        self.btnExpression.setGeometry(QRect(1020, 560, 380, 150))
        self.btnExpression.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnExpression.setStyleSheet(u"\n"
"QPushButton {\n"
"  background-color: #FFFDF0;\n"
"  border: 4px solid #FFFFFF;\n"
"  border-radius: 46px;\n"
"  color: #4F3222;\n"
"  font-family: 'Segoe UI', sans-serif;\n"
"  font-size: 26px;\n"
"  font-weight: 600;\n"
"  padding-left: 50px;\n"
"}\n"
"QPushButton:hover {\n"
"  background-color: #FFF3BD;\n"
"}\n"
"    ")
        self.starExpr1 = QLabel(self.btnExpression)
        self.starExpr1.setObjectName(u"starExpr1")
        self.starExpr1.setGeometry(QRect(45, 34, 40, 40))
        self.starExpr1.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starExpr1.setScaledContents(True)
        self.starExpr2 = QLabel(self.btnExpression)
        self.starExpr2.setObjectName(u"starExpr2")
        self.starExpr2.setGeometry(QRect(45, 78, 40, 40))
        self.starExpr2.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starExpr2.setScaledContents(True)
        self.btnDetective = QPushButton(LessonSelect)
        self.btnDetective.setObjectName(u"btnDetective")
        self.btnDetective.setGeometry(QRect(1460, 560, 380, 150))
        self.btnDetective.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnDetective.setStyleSheet(u"\n"
"QPushButton {\n"
"  background-color: #FFFDF0;\n"
"  border: 4px solid #FFFFFF;\n"
"  border-radius: 46px;\n"
"  color: #4F3222;\n"
"  font-family: 'Segoe UI', sans-serif;\n"
"  font-size: 26px;\n"
"  font-weight: 600;\n"
"  padding-left: 50px;\n"
"}\n"
"QPushButton:hover {\n"
"  background-color: #FFF3BD;\n"
"}\n"
"    ")
        self.starDet1 = QLabel(self.btnDetective)
        self.starDet1.setObjectName(u"starDet1")
        self.starDet1.setGeometry(QRect(38, 30, 38, 38))
        self.starDet1.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starDet1.setScaledContents(True)
        self.starDet2 = QLabel(self.btnDetective)
        self.starDet2.setObjectName(u"starDet2")
        self.starDet2.setGeometry(QRect(74, 30, 38, 38))
        self.starDet2.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starDet2.setScaledContents(True)
        self.starDet3 = QLabel(self.btnDetective)
        self.starDet3.setObjectName(u"starDet3")
        self.starDet3.setGeometry(QRect(38, 74, 38, 38))
        self.starDet3.setPixmap(QPixmap(u"../../resources/img/ui/star.png"))
        self.starDet3.setScaledContents(True)
        self.btnQuiz = QPushButton(LessonSelect)
        self.btnQuiz.setObjectName(u"btnQuiz")
        self.btnQuiz.setGeometry(QRect(260, 930, 460, 74))
        self.btnQuiz.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btnQuiz.setStyleSheet(u"\n"
"QPushButton {\n"
"  background-color: #BFD379;\n"
"  border: 4px solid #FFFFFF;\n"
"  border-radius: 34px;\n"
"  color: #4F3222;\n"
"  font-family: 'Segoe UI', sans-serif;\n"
"  font-size: 26px;\n"
"  font-weight: 700;\n"
"}\n"
"QPushButton:hover {\n"
"  background-color: #ADC362;\n"
"}\n"
"    ")

        self.retranslateUi(LessonSelect)

        QMetaObject.connectSlotsByName(LessonSelect)
    # setupUi

    def retranslateUi(self, LessonSelect):
        LessonSelect.setWindowTitle(QCoreApplication.translate("LessonSelect", u"SenyaSabi \u2014 Lessons + MiniGames", None))
        self.imageBg.setText("")
        self.lblMyLessons.setText(QCoreApplication.translate("LessonSelect", u"My Lessons", None))
        self.lblMiniGames.setText(QCoreApplication.translate("LessonSelect", u"MiniGames", None))
        self.btnBack.setText("")
        self.btnLesson1.setText(QCoreApplication.translate("LessonSelect", u"Lesson 1", None))
        self.btnLesson2.setText(QCoreApplication.translate("LessonSelect", u"Lesson 2", None))
        self.btnLesson3.setText(QCoreApplication.translate("LessonSelect", u"Lesson 3", None))
        self.btnLesson4.setText(QCoreApplication.translate("LessonSelect", u"Lesson 4", None))
        self.btnLesson5.setText(QCoreApplication.translate("LessonSelect", u"Lesson 5", None))
        self.btnSprint.setText(QCoreApplication.translate("LessonSelect", u"Sign\n"
"Sprint", None))
        self.btnQuest.setText(QCoreApplication.translate("LessonSelect", u"FingerSpell\n"
"Quest", None))
        self.btnExpression.setText(QCoreApplication.translate("LessonSelect", u"Expression\n"
"in Motion", None))
        self.btnDetective.setText(QCoreApplication.translate("LessonSelect", u"Sign\n"
"Detective", None))
        self.btnQuiz.setText(QCoreApplication.translate("LessonSelect", u"Module Quiz", None))
    # retranslateUi

