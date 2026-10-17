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
from PySide6.QtWidgets import (QApplication, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_LoginPage(object):
    def setupUi(self, LoginPage):
        if not LoginPage.objectName():
            LoginPage.setObjectName(u"LoginPage")
        LoginPage.resize(720, 560)
        self.pageLayout = QVBoxLayout(LoginPage)
        self.pageLayout.setObjectName(u"pageLayout")
        self.pageLayout.setContentsMargins(180, 64, 180, 64)
        self.titleLabel = QLabel(LoginPage)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setAlignment(Qt.AlignCenter)

        self.pageLayout.addWidget(self.titleLabel)

        self.subtitleLabel = QLabel(LoginPage)
        self.subtitleLabel.setObjectName(u"subtitleLabel")
        self.subtitleLabel.setAlignment(Qt.AlignCenter)

        self.pageLayout.addWidget(self.subtitleLabel)

        self.topSpacer = QSpacerItem(20, 24, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.pageLayout.addItem(self.topSpacer)

        self.emailLabel = QLabel(LoginPage)
        self.emailLabel.setObjectName(u"emailLabel")

        self.pageLayout.addWidget(self.emailLabel)

        self.emailInput = QLineEdit(LoginPage)
        self.emailInput.setObjectName(u"emailInput")
        self.emailInput.setClearButtonEnabled(True)

        self.pageLayout.addWidget(self.emailInput)

        self.passwordLabel = QLabel(LoginPage)
        self.passwordLabel.setObjectName(u"passwordLabel")

        self.pageLayout.addWidget(self.passwordLabel)

        self.passwordInput = QLineEdit(LoginPage)
        self.passwordInput.setObjectName(u"passwordInput")
        self.passwordInput.setEchoMode(QLineEdit.Password)
        self.passwordInput.setClearButtonEnabled(True)

        self.pageLayout.addWidget(self.passwordInput)

        self.continueButton = QPushButton(LoginPage)
        self.continueButton.setObjectName(u"continueButton")

        self.pageLayout.addWidget(self.continueButton)

        self.registerButton = QPushButton(LoginPage)
        self.registerButton.setObjectName(u"registerButton")

        self.pageLayout.addWidget(self.registerButton)

        self.bottomSpacer = QSpacerItem(20, 24, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.pageLayout.addItem(self.bottomSpacer)


        self.retranslateUi(LoginPage)

        self.continueButton.setDefault(True)


        QMetaObject.connectSlotsByName(LoginPage)
    # setupUi

    def retranslateUi(self, LoginPage):
        LoginPage.setWindowTitle(QCoreApplication.translate("LoginPage", u"SenyaSabi \u2014 Sign In", None))
        self.titleLabel.setText(QCoreApplication.translate("LoginPage", u"Welcome to SenyaSabi", None))
        self.subtitleLabel.setText(QCoreApplication.translate("LoginPage", u"Sign in to continue", None))
        self.emailLabel.setText(QCoreApplication.translate("LoginPage", u"Username or email", None))
        self.emailInput.setPlaceholderText(QCoreApplication.translate("LoginPage", u"Enter your username or email", None))
        self.passwordLabel.setText(QCoreApplication.translate("LoginPage", u"Password", None))
        self.passwordInput.setPlaceholderText(QCoreApplication.translate("LoginPage", u"Enter your password", None))
        self.continueButton.setText(QCoreApplication.translate("LoginPage", u"Continue to home", None))
        self.registerButton.setText(QCoreApplication.translate("LoginPage", u"Create an account", None))
    # retranslateUi

