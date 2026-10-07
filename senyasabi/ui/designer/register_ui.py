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
from PySide6.QtWidgets import (QApplication, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_RegisterPage(object):
    def setupUi(self, RegisterPage):
        if not RegisterPage.objectName():
            RegisterPage.setObjectName(u"RegisterPage")
        RegisterPage.resize(720, 740)
        self.pageLayout = QVBoxLayout(RegisterPage)
        self.pageLayout.setObjectName(u"pageLayout")
        self.pageLayout.setContentsMargins(180, 48, 180, 48)
        self.titleLabel = QLabel(RegisterPage)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setAlignment(Qt.AlignCenter)

        self.pageLayout.addWidget(self.titleLabel)

        self.subtitleLabel = QLabel(RegisterPage)
        self.subtitleLabel.setObjectName(u"subtitleLabel")
        self.subtitleLabel.setAlignment(Qt.AlignCenter)

        self.pageLayout.addWidget(self.subtitleLabel)

        self.topSpacer = QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.pageLayout.addItem(self.topSpacer)

        self.usernameLabel = QLabel(RegisterPage)
        self.usernameLabel.setObjectName(u"usernameLabel")

        self.pageLayout.addWidget(self.usernameLabel)

        self.usernameInput = QLineEdit(RegisterPage)
        self.usernameInput.setObjectName(u"usernameInput")
        self.usernameInput.setClearButtonEnabled(True)

        self.pageLayout.addWidget(self.usernameInput)

        self.nameLabel = QLabel(RegisterPage)
        self.nameLabel.setObjectName(u"nameLabel")

        self.pageLayout.addWidget(self.nameLabel)

        self.nameInput = QLineEdit(RegisterPage)
        self.nameInput.setObjectName(u"nameInput")
        self.nameInput.setClearButtonEnabled(True)

        self.pageLayout.addWidget(self.nameInput)

        self.emailLabel = QLabel(RegisterPage)
        self.emailLabel.setObjectName(u"emailLabel")

        self.pageLayout.addWidget(self.emailLabel)

        self.emailInput = QLineEdit(RegisterPage)
        self.emailInput.setObjectName(u"emailInput")
        self.emailInput.setClearButtonEnabled(True)

        self.pageLayout.addWidget(self.emailInput)

        self.passwordLabel = QLabel(RegisterPage)
        self.passwordLabel.setObjectName(u"passwordLabel")

        self.pageLayout.addWidget(self.passwordLabel)

        self.passwordInput = QLineEdit(RegisterPage)
        self.passwordInput.setObjectName(u"passwordInput")
        self.passwordInput.setEchoMode(QLineEdit.Password)
        self.passwordInput.setClearButtonEnabled(True)

        self.pageLayout.addWidget(self.passwordInput)

        self.confirmPasswordLabel = QLabel(RegisterPage)
        self.confirmPasswordLabel.setObjectName(u"confirmPasswordLabel")

        self.pageLayout.addWidget(self.confirmPasswordLabel)

        self.confirmPasswordInput = QLineEdit(RegisterPage)
        self.confirmPasswordInput.setObjectName(u"confirmPasswordInput")
        self.confirmPasswordInput.setEchoMode(QLineEdit.Password)
        self.confirmPasswordInput.setClearButtonEnabled(True)

        self.pageLayout.addWidget(self.confirmPasswordInput)

        self.createAccountButton = QPushButton(RegisterPage)
        self.createAccountButton.setObjectName(u"createAccountButton")

        self.pageLayout.addWidget(self.createAccountButton)

        self.signInButton = QPushButton(RegisterPage)
        self.signInButton.setObjectName(u"signInButton")

        self.pageLayout.addWidget(self.signInButton)

        self.bottomSpacer = QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.pageLayout.addItem(self.bottomSpacer)


        self.retranslateUi(RegisterPage)

        self.createAccountButton.setDefault(True)


        QMetaObject.connectSlotsByName(RegisterPage)
    # setupUi

    def retranslateUi(self, RegisterPage):
        RegisterPage.setWindowTitle(QCoreApplication.translate("RegisterPage", u"SenyaSabi \u2014 Create Account", None))
        self.titleLabel.setText(QCoreApplication.translate("RegisterPage", u"Create your account", None))
        self.subtitleLabel.setText(QCoreApplication.translate("RegisterPage", u"Enter your details to get started", None))
        self.usernameLabel.setText(QCoreApplication.translate("RegisterPage", u"Username", None))
        self.usernameInput.setPlaceholderText(QCoreApplication.translate("RegisterPage", u"Choose a username", None))
        self.nameLabel.setText(QCoreApplication.translate("RegisterPage", u"Display name (optional)", None))
        self.nameInput.setPlaceholderText(QCoreApplication.translate("RegisterPage", u"Enter your name", None))
        self.emailLabel.setText(QCoreApplication.translate("RegisterPage", u"Email", None))
        self.emailInput.setPlaceholderText(QCoreApplication.translate("RegisterPage", u"Enter your email address", None))
        self.passwordLabel.setText(QCoreApplication.translate("RegisterPage", u"Password", None))
        self.passwordInput.setPlaceholderText(QCoreApplication.translate("RegisterPage", u"Create a password", None))
        self.confirmPasswordLabel.setText(QCoreApplication.translate("RegisterPage", u"Confirm password", None))
        self.confirmPasswordInput.setPlaceholderText(QCoreApplication.translate("RegisterPage", u"Enter your password again", None))
        self.createAccountButton.setText(QCoreApplication.translate("RegisterPage", u"Create account", None))
        self.signInButton.setText(QCoreApplication.translate("RegisterPage", u"Back to sign in", None))
    # retranslateUi

