# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'expression_in_motion.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_ExpressionInMotion(object):
    def setupUi(self, ExpressionInMotion):
        if not ExpressionInMotion.objectName():
            ExpressionInMotion.setObjectName(u"ExpressionInMotion")
        ExpressionInMotion.resize(1920, 1080)
        self.centralwidget = QWidget(ExpressionInMotion)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        ExpressionInMotion.setCentralWidget(self.centralwidget)

        self.retranslateUi(ExpressionInMotion)

        QMetaObject.connectSlotsByName(ExpressionInMotion)
    # setupUi

    def retranslateUi(self, ExpressionInMotion):
        ExpressionInMotion.setWindowTitle(QCoreApplication.translate("ExpressionInMotion", u"Expression in Motion", None))
        self.label.setText(QCoreApplication.translate("ExpressionInMotion", u"Expression in Motion Game", None))
    # retranslateUi

