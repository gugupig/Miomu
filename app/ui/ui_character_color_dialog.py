# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'character_color_dialog.ui'
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
    QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_CharacterColorDialog(object):
    def setupUi(self, CharacterColorDialog):
        if not CharacterColorDialog.objectName():
            CharacterColorDialog.setObjectName(u"CharacterColorDialog")
        CharacterColorDialog.resize(600, 400)
        CharacterColorDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(CharacterColorDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.instructionLabel = QLabel(CharacterColorDialog)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.toolbarLayout = QHBoxLayout()
        self.toolbarLayout.setObjectName(u"toolbarLayout")
        self.addCharacterButton = QPushButton(CharacterColorDialog)
        self.addCharacterButton.setObjectName(u"addCharacterButton")

        self.toolbarLayout.addWidget(self.addCharacterButton)

        self.removeCharacterButton = QPushButton(CharacterColorDialog)
        self.removeCharacterButton.setObjectName(u"removeCharacterButton")
        self.removeCharacterButton.setEnabled(False)

        self.toolbarLayout.addWidget(self.removeCharacterButton)

        self.resetColorsButton = QPushButton(CharacterColorDialog)
        self.resetColorsButton.setObjectName(u"resetColorsButton")

        self.toolbarLayout.addWidget(self.resetColorsButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.toolbarLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.toolbarLayout)

        self.characterColorTable = QTableWidget(CharacterColorDialog)
        if (self.characterColorTable.columnCount() < 3):
            self.characterColorTable.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.characterColorTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.characterColorTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.characterColorTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        self.characterColorTable.setObjectName(u"characterColorTable")
        self.characterColorTable.setColumnCount(3)
        self.characterColorTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.characterColorTable.setShowGrid(True)
        self.characterColorTable.setSortingEnabled(False)
        self.characterColorTable.horizontalHeader().setVisible(True)
        self.characterColorTable.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.characterColorTable)

        self.previewLayout = QHBoxLayout()
        self.previewLayout.setObjectName(u"previewLayout")
        self.previewLabel = QLabel(CharacterColorDialog)
        self.previewLabel.setObjectName(u"previewLabel")

        self.previewLayout.addWidget(self.previewLabel)

        self.previewTextLabel = QLabel(CharacterColorDialog)
        self.previewTextLabel.setObjectName(u"previewTextLabel")

        self.previewLayout.addWidget(self.previewTextLabel)

        self.horizontalSpacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.previewLayout.addItem(self.horizontalSpacer2)


        self.verticalLayout.addLayout(self.previewLayout)

        self.buttonBox = QDialogButtonBox(CharacterColorDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(CharacterColorDialog)
        self.buttonBox.accepted.connect(CharacterColorDialog.accept)
        self.buttonBox.rejected.connect(CharacterColorDialog.reject)

        QMetaObject.connectSlotsByName(CharacterColorDialog)
    # setupUi

    def retranslateUi(self, CharacterColorDialog):
        CharacterColorDialog.setWindowTitle(QCoreApplication.translate("CharacterColorDialog", u"\u89d2\u8272\u989c\u8272\u7ba1\u7406", None))
        self.instructionLabel.setText(QCoreApplication.translate("CharacterColorDialog", u"\u4e3a\u6bcf\u4e2a\u89d2\u8272\u8bbe\u7f6e\u53f0\u8bcd\u663e\u793a\u989c\u8272\u3002\u53cc\u51fb\u989c\u8272\u65b9\u5757\u53ef\u4ee5\u4fee\u6539\u989c\u8272\u3002", None))
        self.addCharacterButton.setText(QCoreApplication.translate("CharacterColorDialog", u"\u6dfb\u52a0\u89d2\u8272", None))
        self.removeCharacterButton.setText(QCoreApplication.translate("CharacterColorDialog", u"\u5220\u9664\u89d2\u8272", None))
        self.resetColorsButton.setText(QCoreApplication.translate("CharacterColorDialog", u"\u91cd\u7f6e\u9ed8\u8ba4\u989c\u8272", None))
        ___qtablewidgetitem = self.characterColorTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("CharacterColorDialog", u"\u89d2\u8272\u540d\u79f0", None));
        ___qtablewidgetitem1 = self.characterColorTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("CharacterColorDialog", u"\u989c\u8272\u9884\u89c8", None));
        ___qtablewidgetitem2 = self.characterColorTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("CharacterColorDialog", u"\u989c\u8272\u503c", None));
        self.previewLabel.setText(QCoreApplication.translate("CharacterColorDialog", u"\u6548\u679c\u9884\u89c8\uff1a", None))
        self.previewTextLabel.setText(QCoreApplication.translate("CharacterColorDialog", u"\u793a\u4f8b\u53f0\u8bcd\u6587\u672c", None))
        self.previewTextLabel.setStyleSheet(QCoreApplication.translate("CharacterColorDialog", u"QLabel { padding: 5px; border: 1px solid gray; background-color: white; }", None))
    # retranslateUi

