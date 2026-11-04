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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_LessonSelect(object):
    def setupUi(self, LessonSelect):
        if not LessonSelect.objectName():
            LessonSelect.setObjectName(u"LessonSelect")
        LessonSelect.resize(1920, 1080)
        LessonSelect.setStyleSheet(u"\n"
"QWidget#LessonSelect { background: #C2D076; }\n"
"QLabel { background: transparent; color: #72513D; }\n"
"QLabel#moduleTitle { font-size: 28px; font-weight: 800; }\n"
"QLabel[class=\"sectionTitle\"] { font-size: 24px; font-weight: 700; }\n"
"QLabel#streakLabel { background: #FFF6D2; border-radius: 16px; padding: 8px 16px; }\n"
"QFrame#divider { border: none; border-left: 3px dotted #FFF6D2; }\n"
"QPushButton { color: #754B3B; font-weight: 600; }\n"
"QPushButton[class=\"lessonButton\"] { background: #FFF6D2; border: 2px solid #E7DCA8; border-radius: 24px; font-size: 16px; padding: 10px 24px; min-height: 32px; }\n"
"QPushButton[class=\"lessonButton\"]:hover { background: #FFF0B8; border-color: #D5B957; }\n"
"QPushButton[class=\"minigameButton\"] { background: #FFFDE0; border: none; border-radius: 30px; font-size: 16px; padding: 14px 22px; min-height: 50px; }\n"
"QPushButton[class=\"minigameButton\"]:hover { background: #FFF2B8; }\n"
"QPushButton#backBtn, QPushButton#menuBtn { background: #FFF6D2; border: no"
                        "ne; border-radius: 14px; padding: 10px 18px; }\n"
"QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }\n"
"  ")
        self.rootLayout = QVBoxLayout(LessonSelect)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(45, 28, 45, 28)
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setObjectName(u"headerLayout")
        self.moduleTitle = QLabel(LessonSelect)
        self.moduleTitle.setObjectName(u"moduleTitle")

        self.headerLayout.addWidget(self.moduleTitle)

        self.headerSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.headerLayout.addItem(self.headerSpacer)

        self.streakLabel = QLabel(LessonSelect)
        self.streakLabel.setObjectName(u"streakLabel")

        self.headerLayout.addWidget(self.streakLabel)

        self.menuBtn = QPushButton(LessonSelect)
        self.menuBtn.setObjectName(u"menuBtn")

        self.headerLayout.addWidget(self.menuBtn)

        self.backBtn = QPushButton(LessonSelect)
        self.backBtn.setObjectName(u"backBtn")

        self.headerLayout.addWidget(self.backBtn)


        self.rootLayout.addLayout(self.headerLayout)

        self.sectionsLayout = QHBoxLayout()
        self.sectionsLayout.setObjectName(u"sectionsLayout")
        self.lessonScroll = QScrollArea(LessonSelect)
        self.lessonScroll.setObjectName(u"lessonScroll")
        self.lessonScroll.setWidgetResizable(True)
        self.lessonContainer = QWidget()
        self.lessonContainer.setObjectName(u"lessonContainer")
        self.lessonLayout = QVBoxLayout(self.lessonContainer)
        self.lessonLayout.setObjectName(u"lessonLayout")
        self.lessonScroll.setWidget(self.lessonContainer)

        self.sectionsLayout.addWidget(self.lessonScroll)

        self.divider = QFrame(LessonSelect)
        self.divider.setObjectName(u"divider")
        self.divider.setMinimumSize(QSize(20, 0))

        self.sectionsLayout.addWidget(self.divider)

        self.gameContainer = QWidget(LessonSelect)
        self.gameContainer.setObjectName(u"gameContainer")
        self.gameLayout = QVBoxLayout(self.gameContainer)
        self.gameLayout.setObjectName(u"gameLayout")
        self.gameLayout.setContentsMargins(0, 0, 0, 0)

        self.sectionsLayout.addWidget(self.gameContainer)

        self.sectionsLayout.setStretch(0, 1)
        self.sectionsLayout.setStretch(2, 1)

        self.rootLayout.addLayout(self.sectionsLayout)


        self.retranslateUi(LessonSelect)

        QMetaObject.connectSlotsByName(LessonSelect)
    # setupUi

    def retranslateUi(self, LessonSelect):
        self.moduleTitle.setText(QCoreApplication.translate("LessonSelect", u"FSL Alphabet", None))
        self.streakLabel.setText(QCoreApplication.translate("LessonSelect", u"0 Days", None))
        self.menuBtn.setText(QCoreApplication.translate("LessonSelect", u"?", None))
        self.backBtn.setText(QCoreApplication.translate("LessonSelect", u"? Back", None))
        pass
    # retranslateUi

