# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'style_manager_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QCheckBox,
    QDialog, QDialogButtonBox, QFontComboBox, QFormLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_StyleManagerDialog(object):
    def setupUi(self, StyleManagerDialog):
        if not StyleManagerDialog.objectName():
            StyleManagerDialog.setObjectName(u"StyleManagerDialog")
        StyleManagerDialog.resize(700, 500)
        StyleManagerDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(StyleManagerDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.instructionLabel = QLabel(StyleManagerDialog)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.tabWidget = QTabWidget(StyleManagerDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.characterTab = QWidget()
        self.characterTab.setObjectName(u"characterTab")
        self.characterLayout = QVBoxLayout(self.characterTab)
        self.characterLayout.setObjectName(u"characterLayout")
        self.characterToolbarLayout = QHBoxLayout()
        self.characterToolbarLayout.setObjectName(u"characterToolbarLayout")
        self.addCharacterButton = QPushButton(self.characterTab)
        self.addCharacterButton.setObjectName(u"addCharacterButton")

        self.characterToolbarLayout.addWidget(self.addCharacterButton)

        self.removeCharacterButton = QPushButton(self.characterTab)
        self.removeCharacterButton.setObjectName(u"removeCharacterButton")
        self.removeCharacterButton.setEnabled(False)

        self.characterToolbarLayout.addWidget(self.removeCharacterButton)

        self.importCharactersButton = QPushButton(self.characterTab)
        self.importCharactersButton.setObjectName(u"importCharactersButton")

        self.characterToolbarLayout.addWidget(self.importCharactersButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.characterToolbarLayout.addItem(self.horizontalSpacer)


        self.characterLayout.addLayout(self.characterToolbarLayout)

        self.characterTable = QTableWidget(self.characterTab)
        if (self.characterTable.columnCount() < 4):
            self.characterTable.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.characterTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.characterTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.characterTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.characterTable.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.characterTable.setObjectName(u"characterTable")
        self.characterTable.setColumnCount(4)
        self.characterTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.characterTable.horizontalHeader().setVisible(True)
        self.characterTable.verticalHeader().setVisible(False)

        self.characterLayout.addWidget(self.characterTable)

        self.tabWidget.addTab(self.characterTab, "")
        self.styleTab = QWidget()
        self.styleTab.setObjectName(u"styleTab")
        self.styleLayout = QVBoxLayout(self.styleTab)
        self.styleLayout.setObjectName(u"styleLayout")
        self.styleToolbarLayout = QHBoxLayout()
        self.styleToolbarLayout.setObjectName(u"styleToolbarLayout")
        self.addStyleButton = QPushButton(self.styleTab)
        self.addStyleButton.setObjectName(u"addStyleButton")

        self.styleToolbarLayout.addWidget(self.addStyleButton)

        self.removeStyleButton = QPushButton(self.styleTab)
        self.removeStyleButton.setObjectName(u"removeStyleButton")
        self.removeStyleButton.setEnabled(False)

        self.styleToolbarLayout.addWidget(self.removeStyleButton)

        self.duplicateStyleButton = QPushButton(self.styleTab)
        self.duplicateStyleButton.setObjectName(u"duplicateStyleButton")
        self.duplicateStyleButton.setEnabled(False)

        self.styleToolbarLayout.addWidget(self.duplicateStyleButton)

        self.horizontalSpacer2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.styleToolbarLayout.addItem(self.horizontalSpacer2)


        self.styleLayout.addLayout(self.styleToolbarLayout)

        self.styleContentLayout = QHBoxLayout()
        self.styleContentLayout.setObjectName(u"styleContentLayout")
        self.styleListWidget = QListWidget(self.styleTab)
        self.styleListWidget.setObjectName(u"styleListWidget")
        self.styleListWidget.setMaximumSize(QSize(200, 16777215))

        self.styleContentLayout.addWidget(self.styleListWidget)

        self.stylePropertiesGroupBox = QGroupBox(self.styleTab)
        self.stylePropertiesGroupBox.setObjectName(u"stylePropertiesGroupBox")
        self.stylePropertiesLayout = QFormLayout(self.stylePropertiesGroupBox)
        self.stylePropertiesLayout.setObjectName(u"stylePropertiesLayout")
        self.styleNameLabel = QLabel(self.stylePropertiesGroupBox)
        self.styleNameLabel.setObjectName(u"styleNameLabel")

        self.stylePropertiesLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.styleNameLabel)

        self.styleNameLineEdit = QLineEdit(self.stylePropertiesGroupBox)
        self.styleNameLineEdit.setObjectName(u"styleNameLineEdit")

        self.stylePropertiesLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.styleNameLineEdit)

        self.fontFamilyLabel = QLabel(self.stylePropertiesGroupBox)
        self.fontFamilyLabel.setObjectName(u"fontFamilyLabel")

        self.stylePropertiesLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.fontFamilyLabel)

        self.fontFamilyComboBox = QFontComboBox(self.stylePropertiesGroupBox)
        self.fontFamilyComboBox.setObjectName(u"fontFamilyComboBox")

        self.stylePropertiesLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.fontFamilyComboBox)

        self.fontSizeLabel = QLabel(self.stylePropertiesGroupBox)
        self.fontSizeLabel.setObjectName(u"fontSizeLabel")

        self.stylePropertiesLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.fontSizeLabel)

        self.fontSizeSpinBox = QSpinBox(self.stylePropertiesGroupBox)
        self.fontSizeSpinBox.setObjectName(u"fontSizeSpinBox")
        self.fontSizeSpinBox.setMinimum(8)
        self.fontSizeSpinBox.setMaximum(72)
        self.fontSizeSpinBox.setValue(16)

        self.stylePropertiesLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.fontSizeSpinBox)

        self.fontColorLabel = QLabel(self.stylePropertiesGroupBox)
        self.fontColorLabel.setObjectName(u"fontColorLabel")

        self.stylePropertiesLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.fontColorLabel)

        self.fontColorLayout = QHBoxLayout()
        self.fontColorLayout.setObjectName(u"fontColorLayout")
        self.fontColorButton = QPushButton(self.stylePropertiesGroupBox)
        self.fontColorButton.setObjectName(u"fontColorButton")

        self.fontColorLayout.addWidget(self.fontColorButton)

        self.fontColorPreview = QLabel(self.stylePropertiesGroupBox)
        self.fontColorPreview.setObjectName(u"fontColorPreview")

        self.fontColorLayout.addWidget(self.fontColorPreview)


        self.stylePropertiesLayout.setLayout(3, QFormLayout.ItemRole.FieldRole, self.fontColorLayout)

        self.backgroundColorLabel = QLabel(self.stylePropertiesGroupBox)
        self.backgroundColorLabel.setObjectName(u"backgroundColorLabel")

        self.stylePropertiesLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.backgroundColorLabel)

        self.backgroundColorLayout = QHBoxLayout()
        self.backgroundColorLayout.setObjectName(u"backgroundColorLayout")
        self.backgroundColorButton = QPushButton(self.stylePropertiesGroupBox)
        self.backgroundColorButton.setObjectName(u"backgroundColorButton")

        self.backgroundColorLayout.addWidget(self.backgroundColorButton)

        self.backgroundColorPreview = QLabel(self.stylePropertiesGroupBox)
        self.backgroundColorPreview.setObjectName(u"backgroundColorPreview")

        self.backgroundColorLayout.addWidget(self.backgroundColorPreview)


        self.stylePropertiesLayout.setLayout(4, QFormLayout.ItemRole.FieldRole, self.backgroundColorLayout)

        self.boldLabel = QLabel(self.stylePropertiesGroupBox)
        self.boldLabel.setObjectName(u"boldLabel")

        self.stylePropertiesLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.boldLabel)

        self.boldCheckBox = QCheckBox(self.stylePropertiesGroupBox)
        self.boldCheckBox.setObjectName(u"boldCheckBox")

        self.stylePropertiesLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.boldCheckBox)

        self.italicLabel = QLabel(self.stylePropertiesGroupBox)
        self.italicLabel.setObjectName(u"italicLabel")

        self.stylePropertiesLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.italicLabel)

        self.italicCheckBox = QCheckBox(self.stylePropertiesGroupBox)
        self.italicCheckBox.setObjectName(u"italicCheckBox")

        self.stylePropertiesLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.italicCheckBox)


        self.styleContentLayout.addWidget(self.stylePropertiesGroupBox)


        self.styleLayout.addLayout(self.styleContentLayout)

        self.previewGroupBox = QGroupBox(self.styleTab)
        self.previewGroupBox.setObjectName(u"previewGroupBox")
        self.previewLayout = QVBoxLayout(self.previewGroupBox)
        self.previewLayout.setObjectName(u"previewLayout")
        self.stylePreviewLabel = QLabel(self.previewGroupBox)
        self.stylePreviewLabel.setObjectName(u"stylePreviewLabel")
        self.stylePreviewLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.previewLayout.addWidget(self.stylePreviewLabel)


        self.styleLayout.addWidget(self.previewGroupBox)

        self.tabWidget.addTab(self.styleTab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.buttonBox = QDialogButtonBox(StyleManagerDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Apply|QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(StyleManagerDialog)
        self.buttonBox.accepted.connect(StyleManagerDialog.accept)
        self.buttonBox.rejected.connect(StyleManagerDialog.reject)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(StyleManagerDialog)
    # setupUi

    def retranslateUi(self, StyleManagerDialog):
        StyleManagerDialog.setWindowTitle(QCoreApplication.translate("StyleManagerDialog", u"\u6837\u5f0f\u7ba1\u7406", None))
        self.instructionLabel.setText(QCoreApplication.translate("StyleManagerDialog", u"\u7ba1\u7406\u5b57\u5e55\u6837\u5f0f\u548c\u89d2\u8272\u989c\u8272\u914d\u7f6e\u3002\u53ef\u4ee5\u521b\u5efa\u3001\u7f16\u8f91\u548c\u5220\u9664\u6837\u5f0f\u6a21\u677f\u3002", None))
        self.addCharacterButton.setText(QCoreApplication.translate("StyleManagerDialog", u"\u6dfb\u52a0\u89d2\u8272", None))
        self.removeCharacterButton.setText(QCoreApplication.translate("StyleManagerDialog", u"\u5220\u9664\u89d2\u8272", None))
        self.importCharactersButton.setText(QCoreApplication.translate("StyleManagerDialog", u"\u4ece\u5267\u672c\u5bfc\u5165\u89d2\u8272", None))
        ___qtablewidgetitem = self.characterTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("StyleManagerDialog", u"\u89d2\u8272\u540d\u79f0", None));
        ___qtablewidgetitem1 = self.characterTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("StyleManagerDialog", u"\u989c\u8272\u9884\u89c8", None));
        ___qtablewidgetitem2 = self.characterTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("StyleManagerDialog", u"\u989c\u8272\u503c", None));
        ___qtablewidgetitem3 = self.characterTable.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("StyleManagerDialog", u"\u53f0\u8bcd\u6570\u91cf", None));
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.characterTab), QCoreApplication.translate("StyleManagerDialog", u"\u89d2\u8272\u989c\u8272", None))
        self.addStyleButton.setText(QCoreApplication.translate("StyleManagerDialog", u"\u6dfb\u52a0\u6837\u5f0f", None))
        self.removeStyleButton.setText(QCoreApplication.translate("StyleManagerDialog", u"\u5220\u9664\u6837\u5f0f", None))
        self.duplicateStyleButton.setText(QCoreApplication.translate("StyleManagerDialog", u"\u590d\u5236\u6837\u5f0f", None))
        self.stylePropertiesGroupBox.setTitle(QCoreApplication.translate("StyleManagerDialog", u"\u6837\u5f0f\u5c5e\u6027", None))
        self.styleNameLabel.setText(QCoreApplication.translate("StyleManagerDialog", u"\u6837\u5f0f\u540d\u79f0\uff1a", None))
        self.fontFamilyLabel.setText(QCoreApplication.translate("StyleManagerDialog", u"\u5b57\u4f53\uff1a", None))
        self.fontSizeLabel.setText(QCoreApplication.translate("StyleManagerDialog", u"\u5b57\u4f53\u5927\u5c0f\uff1a", None))
        self.fontColorLabel.setText(QCoreApplication.translate("StyleManagerDialog", u"\u5b57\u4f53\u989c\u8272\uff1a", None))
        self.fontColorButton.setText(QCoreApplication.translate("StyleManagerDialog", u"\u9009\u62e9\u989c\u8272", None))
        self.fontColorPreview.setText(QCoreApplication.translate("StyleManagerDialog", u"\u9884\u89c8", None))
        self.fontColorPreview.setStyleSheet(QCoreApplication.translate("StyleManagerDialog", u"QLabel { border: 1px solid gray; padding: 5px; }", None))
        self.backgroundColorLabel.setText(QCoreApplication.translate("StyleManagerDialog", u"\u80cc\u666f\u989c\u8272\uff1a", None))
        self.backgroundColorButton.setText(QCoreApplication.translate("StyleManagerDialog", u"\u9009\u62e9\u989c\u8272", None))
        self.backgroundColorPreview.setText(QCoreApplication.translate("StyleManagerDialog", u"\u9884\u89c8", None))
        self.backgroundColorPreview.setStyleSheet(QCoreApplication.translate("StyleManagerDialog", u"QLabel { border: 1px solid gray; padding: 5px; }", None))
        self.boldLabel.setText(QCoreApplication.translate("StyleManagerDialog", u"\u7c97\u4f53\uff1a", None))
        self.italicLabel.setText(QCoreApplication.translate("StyleManagerDialog", u"\u659c\u4f53\uff1a", None))
        self.previewGroupBox.setTitle(QCoreApplication.translate("StyleManagerDialog", u"\u6837\u5f0f\u9884\u89c8", None))
        self.stylePreviewLabel.setText(QCoreApplication.translate("StyleManagerDialog", u"\u8fd9\u662f\u4e00\u6bb5\u793a\u4f8b\u5b57\u5e55\u6587\u672c\uff0c\u7528\u4e8e\u9884\u89c8\u6837\u5f0f\u6548\u679c\u3002", None))
        self.stylePreviewLabel.setStyleSheet(QCoreApplication.translate("StyleManagerDialog", u"QLabel { border: 1px solid gray; padding: 10px; min-height: 40px; }", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.styleTab), QCoreApplication.translate("StyleManagerDialog", u"\u5b57\u5e55\u6837\u5f0f", None))
    # retranslateUi

