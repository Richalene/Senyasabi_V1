# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login.ui'
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

class Ui_LoginPage(object):
    def setupUi(self, LoginPage):
        if not LoginPage.objectName():
            LoginPage.setObjectName(u"LoginPage")
        LoginPage.resize(1920, 1080)
        self.imageBg = QLabel(LoginPage)
        self.imageBg.setObjectName(u"imageBg")
        self.imageBg.setGeometry(QRect(0, 0, 1920, 1080))
        self.imageBg.setPixmap(QPixmap(u"../../resources/img/login_bg.png"))
        self.imageBg.setScaledContents(True)
        self.logoLabel = QLabel(LoginPage)
        self.logoLabel.setObjectName(u"logoLabel")
        self.logoLabel.setGeometry(QRect(870, 70, 135, 135))
        self.logoLabel.setPixmap(QPixmap(u"../../resources/img/ui/logo_black.png"))
        self.logoLabel.setScaledContents(True)
        self.titleLabel = QLabel(LoginPage)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setGeometry(QRect(870, 220, 840, 75))
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.subtitleLabel = QLabel(LoginPage)
        self.subtitleLabel.setObjectName(u"subtitleLabel")
        self.subtitleLabel.setGeometry(QRect(870, 305, 840, 35))
        self.subtitleLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.line = QFrame(LoginPage)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(870, 350, 840, 6))
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.emailLabel = QLabel(LoginPage)
        self.emailLabel.setObjectName(u"emailLabel")
        self.emailLabel.setGeometry(QRect(870, 390, 840, 30))
        self.emailInput = QLineEdit(LoginPage)
        self.emailInput.setObjectName(u"emailInput")
        self.emailInput.setGeometry(QRect(870, 430, 840, 88))
        self.emailInput.setClearButtonEnabled(False)
        self.passwordLabel = QLabel(LoginPage)
        self.passwordLabel.setObjectName(u"passwordLabel")
        self.passwordLabel.setGeometry(QRect(870, 540, 840, 30))
        self.passwordInput = QLineEdit(LoginPage)
        self.passwordInput.setObjectName(u"passwordInput")
        self.passwordInput.setGeometry(QRect(870, 580, 840, 88))
        self.passwordInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.passwordInput.setClearButtonEnabled(False)
        self.backButton = QPushButton(LoginPage)
        self.backButton.setObjectName(u"backButton")
        self.backButton.setGeometry(QRect(870, 715, 400, 88))
        self.backButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.continueButton = QPushButton(LoginPage)
        self.continueButton.setObjectName(u"continueButton")
        self.continueButton.setGeometry(QRect(1310, 715, 400, 88))
        self.continueButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.registerButton = QPushButton(LoginPage)
        self.registerButton.setObjectName(u"registerButton")
        self.registerButton.setGeometry(QRect(870, 830, 840, 40))
        self.registerButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.registerButton.setFlat(True)
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
        self.continueButton.raise_()
        self.registerButton.raise_()

        self.retranslateUi(LoginPage)

        self.continueButton.setDefault(True)


        QMetaObject.connectSlotsByName(LoginPage)
    # setupUi

    def retranslateUi(self, LoginPage):
        LoginPage.setWindowTitle(QCoreApplication.translate("LoginPage", u"SenyaSabi \u2014 Sign In", None))
        self.imageBg.setText("")
        self.logoLabel.setText("")
        self.titleLabel.setText(QCoreApplication.translate("LoginPage", u"Welcome Back!", None))
        self.subtitleLabel.setText(QCoreApplication.translate("LoginPage", u"Welcome back to SensyaSabi!", None))
        self.emailLabel.setText(QCoreApplication.translate("LoginPage", u"Your Email or Username", None))
        self.emailInput.setPlaceholderText(QCoreApplication.translate("LoginPage", u"Type Your Email or Username Here", None))
        self.passwordLabel.setText(QCoreApplication.translate("LoginPage", u"Your Password", None))
        self.passwordInput.setPlaceholderText(QCoreApplication.translate("LoginPage", u"Type Your Password Here", None))
        self.backButton.setText(QCoreApplication.translate("LoginPage", u"Go Back", None))
        self.continueButton.setText(QCoreApplication.translate("LoginPage", u"Sign In", None))
        self.registerButton.setText(QCoreApplication.translate("LoginPage", u"Don't have an account?  Sign Up", None))
    # retranslateUi

