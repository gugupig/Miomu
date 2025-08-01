# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'character_filter_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialog,
    QDialogButtonBox, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_CharacterFilterDialog(object):
    def setupUi(self, CharacterFilterDialog):
        if not CharacterFilterDialog.objectName():
            CharacterFilterDialog.setObjectName(u"CharacterFilterDialog")
        CharacterFilterDialog.resize(400, 300)
        CharacterFilterDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(CharacterFilterDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.instructionLabel = QLabel(CharacterFilterDialog)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.toolbarLayout = QHBoxLayout()
        self.toolbarLayout.setObjectName(u"toolbarLayout")
        self.selectAllButton = QPushButton(CharacterFilterDialog)
        self.selectAllButton.setObjectName(u"selectAllButton")

        self.toolbarLayout.addWidget(self.selectAllButton)

        self.selectNoneButton = QPushButton(CharacterFilterDialog)
        self.selectNoneButton.setObjectName(u"selectNoneButton")

        self.toolbarLayout.addWidget(self.selectNoneButton)

        self.invertSelectionButton = QPushButton(CharacterFilterDialog)
        self.invertSelectionButton.setObjectName(u"invertSelectionButton")

        self.toolbarLayout.addWidget(self.invertSelectionButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.toolbarLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.toolbarLayout)

        self.characterListWidget = QListWidget(CharacterFilterDialog)
        self.characterListWidget.setObjectName(u"characterListWidget")
        self.characterListWidget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        self.verticalLayout.addWidget(self.characterListWidget)

        self.statusLayout = QHBoxLayout()
        self.statusLayout.setObjectName(u"statusLayout")
        self.statusLabel = QLabel(CharacterFilterDialog)
        self.statusLabel.setObjectName(u"statusLabel")

        self.statusLayout.addWidget(self.statusLabel)

        self.horizontalSpacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.statusLayout.addItem(self.horizontalSpacer2)


        self.verticalLayout.addLayout(self.statusLayout)

        self.buttonBox = QDialogButtonBox(CharacterFilterDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(CharacterFilterDialog)
        self.buttonBox.accepted.connect(CharacterFilterDialog.accept)
        self.buttonBox.rejected.connect(CharacterFilterDialog.reject)

        QMetaObject.connectSlotsByName(CharacterFilterDialog)
    # setupUi

    def retranslateUi(self, CharacterFilterDialog):
        CharacterFilterDialog.setWindowTitle(QCoreApplication.translate("CharacterFilterDialog", u"\u6309\u89d2\u8272\u7b5b\u9009\u53f0\u8bcd", None))
        self.instructionLabel.setText(QCoreApplication.translate("CharacterFilterDialog", u"\u9009\u62e9\u8981\u663e\u793a\u7684\u89d2\u8272\uff0c\u53d6\u6d88\u9009\u62e9\u7684\u89d2\u8272\u5c06\u88ab\u9690\u85cf\uff1a", None))
        self.selectAllButton.setText(QCoreApplication.translate("CharacterFilterDialog", u"\u5168\u9009", None))
        self.selectNoneButton.setText(QCoreApplication.translate("CharacterFilterDialog", u"\u5168\u4e0d\u9009", None))
        self.invertSelectionButton.setText(QCoreApplication.translate("CharacterFilterDialog", u"\u53cd\u9009", None))
        self.statusLabel.setText(QCoreApplication.translate("CharacterFilterDialog", u"\u5171 0 \u4e2a\u89d2\u8272\uff0c\u5df2\u9009\u62e9 0 \u4e2a", None))
    # retranslateUi

