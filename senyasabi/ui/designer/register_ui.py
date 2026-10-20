# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'register.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QWidget)

class Ui_RegisterPage(object):
    def setupUi(self, RegisterPage):
        if not RegisterPage.objectName():
            RegisterPage.setObjectName(u"RegisterPage")
        RegisterPage.resize(1920, 1080)
        self.imageBg = QLabel(RegisterPage)
        self.imageBg.setObjectName(u"imageBg")
        self.imageBg.setGeometry(QRect(0, 0, 1920, 1080))
        self.imageBg.setPixmap(QPixmap(u"../../resources/img/login_bg.png"))
        self.imageBg.setScaledContents(True)
        self.logoLabel = QLabel(RegisterPage)
        self.logoLabel.setObjectName(u"logoLabel")
        self.logoLabel.setGeometry(QRect(870, 70, 135, 135))
        self.logoLabel.setPixmap(QPixmap(u"../../resources/img/ui/logo_black.png"))
        self.logoLabel.setScaledContents(True)
        self.titleLabel = QLabel(RegisterPage)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setGeometry(QRect(870, 220, 840, 75))
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.subtitleLabel = QLabel(RegisterPage)
        self.subtitleLabel.setObjectName(u"subtitleLabel")
        self.subtitleLabel.setGeometry(QRect(870, 305, 840, 35))
        self.subtitleLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.line = QFrame(RegisterPage)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(870, 350, 840, 6))
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.emailLabel = QLabel(RegisterPage)
        self.emailLabel.setObjectName(u"emailLabel")
        self.emailLabel.setGeometry(QRect(870, 390, 840, 30))
        self.emailInput = QLineEdit(RegisterPage)
        self.emailInput.setObjectName(u"emailInput")
        self.emailInput.setGeometry(QRect(870, 430, 840, 88))
        self.emailInput.setClearButtonEnabled(False)
        self.passwordLabel = QLabel(RegisterPage)
        self.passwordLabel.setObjectName(u"passwordLabel")
        self.passwordLabel.setGeometry(QRect(870, 540, 840, 30))
        self.passwordInput = QLineEdit(RegisterPage)
        self.passwordInput.setObjectName(u"passwordInput")
        self.passwordInput.setGeometry(QRect(870, 580, 840, 88))
        self.passwordInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.passwordInput.setClearButtonEnabled(False)
        self.backButton = QPushButton(RegisterPage)
        self.backButton.setObjectName(u"backButton")
        self.backButton.setGeometry(QRect(870, 715, 400, 88))
        self.backButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.createAccountButton = QPushButton(RegisterPage)
        self.createAccountButton.setObjectName(u"createAccountButton")
        self.createAccountButton.setGeometry(QRect(1310, 715, 400, 88))
        self.createAccountButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.signInButton = QPushButton(RegisterPage)
        self.signInButton.setObjectName(u"signInButton")
        self.signInButton.setGeometry(QRect(870, 830, 840, 40))
        self.signInButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.signInButton.setFlat(True)
        self.imageBg.raise_()
        self.logoLabel.raise_()
        self.titleLabel.raise_()
        self.subtitleLabel.raise_()
        self.line.raise_()
        self.emailLabel.raise_()
        self.emailInput.raise_()
        self.passwordLabel.raise_()
        self.passwordInput.raise_()
        self.backButton.raise_()
        self.createAccountButton.raise_()
        self.signInButton.raise_()

        self.retranslateUi(RegisterPage)

        self.createAccountButton.setDefault(True)


        QMetaObject.connectSlotsByName(RegisterPage)
    # setupUi

    def retranslateUi(self, RegisterPage):
        RegisterPage.setWindowTitle(QCoreApplication.translate("RegisterPage", u"SenyaSabi \u2014 Create Account", None))
        self.imageBg.setText("")
        self.logoLabel.setText("")
        self.titleLabel.setText(QCoreApplication.translate("RegisterPage", u"Get Started", None))
        self.subtitleLabel.setText(QCoreApplication.translate("RegisterPage", u"Welcome to SensyaSabi \u2014 Shall we begin?", None))
        self.emailLabel.setText(QCoreApplication.translate("RegisterPage", u"Your Email", None))
        self.emailInput.setPlaceholderText(QCoreApplication.translate("RegisterPage", u"Type Your Email Here", None))
        self.passwordLabel.setText(QCoreApplication.translate("RegisterPage", u"Create New Password", None))
        self.passwordInput.setPlaceholderText(QCoreApplication.translate("RegisterPage", u"Password must include 1 uppercase letter and a number", None))
        self.backButton.setText(QCoreApplication.translate("RegisterPage", u"Go Back", None))
        self.createAccountButton.setText(QCoreApplication.translate("RegisterPage", u"Sign Up", None))
        self.signInButton.setText(QCoreApplication.translate("RegisterPage", u"Have an account already?  Sign In", None))
    # retranslateUi

