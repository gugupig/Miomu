# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_console_full.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QTabWidget, QTableView, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1469, 961)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutMain = QVBoxLayout(self.centralwidget)
        self.verticalLayoutMain.setObjectName(u"verticalLayoutMain")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.editTab = QWidget()
        self.editTab.setObjectName(u"editTab")
        self.verticalLayoutEdit = QVBoxLayout(self.editTab)
        self.verticalLayoutEdit.setObjectName(u"verticalLayoutEdit")
        self.verticalLayoutEdit.setContentsMargins(0, 0, 0, 0)
        self.toolbarLayout = QHBoxLayout()
        self.toolbarLayout.setObjectName(u"toolbarLayout")
        self.loadScriptButton = QPushButton(self.editTab)
        self.loadScriptButton.setObjectName(u"loadScriptButton")

        self.toolbarLayout.addWidget(self.loadScriptButton)

        self.saveScriptButton = QPushButton(self.editTab)
        self.saveScriptButton.setObjectName(u"saveScriptButton")
        self.saveScriptButton.setEnabled(False)

        self.toolbarLayout.addWidget(self.saveScriptButton)

        self.addCueButton = QPushButton(self.editTab)
        self.addCueButton.setObjectName(u"addCueButton")
        self.addCueButton.setEnabled(False)

        self.toolbarLayout.addWidget(self.addCueButton)

        self.deleteCueButton = QPushButton(self.editTab)
        self.deleteCueButton.setObjectName(u"deleteCueButton")
        self.deleteCueButton.setEnabled(False)

        self.toolbarLayout.addWidget(self.deleteCueButton)

        self.duplicateCueButton = QPushButton(self.editTab)
        self.duplicateCueButton.setObjectName(u"duplicateCueButton")
        self.duplicateCueButton.setEnabled(False)

        self.toolbarLayout.addWidget(self.duplicateCueButton)

        self.refreshPhonemesButton = QPushButton(self.editTab)
        self.refreshPhonemesButton.setObjectName(u"refreshPhonemesButton")
        self.refreshPhonemesButton.setEnabled(False)

        self.toolbarLayout.addWidget(self.refreshPhonemesButton)

        self.addLanguageButton = QPushButton(self.editTab)
        self.addLanguageButton.setObjectName(u"addLanguageButton")
        self.addLanguageButton.setEnabled(False)

        self.toolbarLayout.addWidget(self.addLanguageButton)

        self.removeLanguageButton = QPushButton(self.editTab)
        self.removeLanguageButton.setObjectName(u"removeLanguageButton")
        self.removeLanguageButton.setEnabled(False)

        self.toolbarLayout.addWidget(self.removeLanguageButton)

        self.manageStylesButton = QPushButton(self.editTab)
        self.manageStylesButton.setObjectName(u"manageStylesButton")
        self.manageStylesButton.setEnabled(False)

        self.toolbarLayout.addWidget(self.manageStylesButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.toolbarLayout.addItem(self.horizontalSpacer)


        self.verticalLayoutEdit.addLayout(self.toolbarLayout)

        self.scriptView = QTableView(self.editTab)
        self.scriptView.setObjectName(u"scriptView")
        self.scriptView.setAlternatingRowColors(True)
        self.scriptView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.scriptView.setShowGrid(True)
        self.scriptView.setSortingEnabled(False)

        self.verticalLayoutEdit.addWidget(self.scriptView)

        self.verticalLayoutEdit.setStretch(0, 1)
        self.verticalLayoutEdit.setStretch(1, 4)
        self.tabWidget.addTab(self.editTab, "")
        self.theaterTab = QWidget()
        self.theaterTab.setObjectName(u"theaterTab")
        self.verticalLayoutTheater = QVBoxLayout(self.theaterTab)
        self.verticalLayoutTheater.setObjectName(u"verticalLayoutTheater")
        self.theaterToolbarLayout = QHBoxLayout()
        self.theaterToolbarLayout.setObjectName(u"theaterToolbarLayout")
        self.loadScriptTheaterButton = QPushButton(self.theaterTab)
        self.loadScriptTheaterButton.setObjectName(u"loadScriptTheaterButton")

        self.theaterToolbarLayout.addWidget(self.loadScriptTheaterButton)

        self.syncFromEditButton = QPushButton(self.theaterTab)
        self.syncFromEditButton.setObjectName(u"syncFromEditButton")
        self.syncFromEditButton.setEnabled(False)

        self.theaterToolbarLayout.addWidget(self.syncFromEditButton)

        self.filterByCharacterButton = QPushButton(self.theaterTab)
        self.filterByCharacterButton.setObjectName(u"filterByCharacterButton")
        self.filterByCharacterButton.setEnabled(False)

        self.theaterToolbarLayout.addWidget(self.filterByCharacterButton)

        self.languageComboBox = QComboBox(self.theaterTab)
        self.languageComboBox.addItem("")
        self.languageComboBox.setObjectName(u"languageComboBox")
        self.languageComboBox.setEnabled(False)

        self.theaterToolbarLayout.addWidget(self.languageComboBox)

        self.manageCharacterColorsButton = QPushButton(self.theaterTab)
        self.manageCharacterColorsButton.setObjectName(u"manageCharacterColorsButton")
        self.manageCharacterColorsButton.setEnabled(False)

        self.theaterToolbarLayout.addWidget(self.manageCharacterColorsButton)

        self.horizontalSpacerTheater = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.theaterToolbarLayout.addItem(self.horizontalSpacerTheater)


        self.verticalLayoutTheater.addLayout(self.theaterToolbarLayout)

        self.controlLayout = QHBoxLayout()
        self.controlLayout.setObjectName(u"controlLayout")
        self.verticalLayoutLogArea = QVBoxLayout()
        self.verticalLayoutLogArea.setObjectName(u"verticalLayoutLogArea")
        self.logAreaLabel = QLabel(self.theaterTab)
        self.logAreaLabel.setObjectName(u"logAreaLabel")

        self.verticalLayoutLogArea.addWidget(self.logAreaLabel)

        self.logTextEdit = QTextEdit(self.theaterTab)
        self.logTextEdit.setObjectName(u"logTextEdit")
        self.logTextEdit.setMaximumSize(QSize(300, 16777215))
        self.logTextEdit.setReadOnly(True)

        self.verticalLayoutLogArea.addWidget(self.logTextEdit)


        self.controlLayout.addLayout(self.verticalLayoutLogArea)

        self.theaterMainLayout = QVBoxLayout()
        self.theaterMainLayout.setObjectName(u"theaterMainLayout")
        self.theaterTable = QTableView(self.theaterTab)
        self.theaterTable.setObjectName(u"theaterTable")
        self.theaterTable.setAlternatingRowColors(True)
        self.theaterTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.theaterTable.setShowGrid(True)
        self.theaterTable.setSortingEnabled(False)

        self.theaterMainLayout.addWidget(self.theaterTable)

        self.theaterControlsLayout = QHBoxLayout()
        self.theaterControlsLayout.setObjectName(u"theaterControlsLayout")
        self.startButton = QPushButton(self.theaterTab)
        self.startButton.setObjectName(u"startButton")
        self.startButton.setEnabled(False)

        self.theaterControlsLayout.addWidget(self.startButton)

        self.pauseButton = QPushButton(self.theaterTab)
        self.pauseButton.setObjectName(u"pauseButton")
        self.pauseButton.setEnabled(False)

        self.theaterControlsLayout.addWidget(self.pauseButton)

        self.stopButton = QPushButton(self.theaterTab)
        self.stopButton.setObjectName(u"stopButton")
        self.stopButton.setEnabled(False)

        self.theaterControlsLayout.addWidget(self.stopButton)

        self.showSubtitleButton = QPushButton(self.theaterTab)
        self.showSubtitleButton.setObjectName(u"showSubtitleButton")
        self.showSubtitleButton.setEnabled(False)

        self.theaterControlsLayout.addWidget(self.showSubtitleButton)

        self.showDebugButton = QPushButton(self.theaterTab)
        self.showDebugButton.setObjectName(u"showDebugButton")

        self.theaterControlsLayout.addWidget(self.showDebugButton)

        self.horizontalSpacerControls = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.theaterControlsLayout.addItem(self.horizontalSpacerControls)


        self.theaterMainLayout.addLayout(self.theaterControlsLayout)


        self.controlLayout.addLayout(self.theaterMainLayout)


        self.verticalLayoutTheater.addLayout(self.controlLayout)

        self.tabWidget.addTab(self.theaterTab, "")

        self.verticalLayoutMain.addWidget(self.tabWidget)

        self.logLabel = QLabel(self.centralwidget)
        self.logLabel.setObjectName(u"logLabel")

        self.verticalLayoutMain.addWidget(self.logLabel)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setSizeGripEnabled(True)
        self.progressBar = QProgressBar(self.statusbar)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setGeometry(QRect(0, 0, 100, 30))
        self.progressBar.setVisible(False)
        self.progressBar.setTextVisible(False)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Miomu - \u5267\u672c\u5bf9\u9f50\u63a7\u5236\u53f0", None))
        self.loadScriptButton.setText(QCoreApplication.translate("MainWindow", u"\u52a0\u8f7d\u5267\u672c", None))
        self.saveScriptButton.setText(QCoreApplication.translate("MainWindow", u"\u4fdd\u5b58\u5267\u672c", None))
        self.addCueButton.setText(QCoreApplication.translate("MainWindow", u"\u6dfb\u52a0\u53f0\u8bcd", None))
        self.deleteCueButton.setText(QCoreApplication.translate("MainWindow", u"\u5220\u9664\u53f0\u8bcd", None))
        self.duplicateCueButton.setText(QCoreApplication.translate("MainWindow", u"\u590d\u5236\u53f0\u8bcd", None))
        self.refreshPhonemesButton.setText(QCoreApplication.translate("MainWindow", u"\u5237\u65b0\u97f3\u7d20", None))
        self.addLanguageButton.setText(QCoreApplication.translate("MainWindow", u"\u6dfb\u52a0\u8bed\u8a00", None))
        self.removeLanguageButton.setText(QCoreApplication.translate("MainWindow", u"\u79fb\u9664\u8bed\u8a00", None))
        self.manageStylesButton.setText(QCoreApplication.translate("MainWindow", u"\u7ba1\u7406\u6837\u5f0f", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.editTab), QCoreApplication.translate("MainWindow", u"\u7f16\u8f91\u6a21\u5f0f", None))
        self.loadScriptTheaterButton.setText(QCoreApplication.translate("MainWindow", u"\u52a0\u8f7d\u5267\u672c", None))
        self.syncFromEditButton.setText(QCoreApplication.translate("MainWindow", u"\u540c\u6b65\u7f16\u8f91\u6a21\u5f0f\u6570\u636e", None))
        self.filterByCharacterButton.setText(QCoreApplication.translate("MainWindow", u"\u6309\u89d2\u8272\u7b5b\u9009", None))
        self.languageComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"\u539f\u59cb\u8bed\u8a00", None))

        self.manageCharacterColorsButton.setText(QCoreApplication.translate("MainWindow", u"\u7ba1\u7406\u89d2\u8272\u989c\u8272", None))
        self.logAreaLabel.setText(QCoreApplication.translate("MainWindow", u"\u65e5\u5fd7\u533a\u57df\uff1a", None))
        self.startButton.setText(QCoreApplication.translate("MainWindow", u"\u5f00\u59cb\u5bf9\u9f50", None))
        self.pauseButton.setText(QCoreApplication.translate("MainWindow", u"\u6682\u505c", None))
        self.stopButton.setText(QCoreApplication.translate("MainWindow", u"\u505c\u6b62", None))
        self.showSubtitleButton.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793a\u5b57\u5e55\u7a97\u53e3", None))
        self.showDebugButton.setText(QCoreApplication.translate("MainWindow", u"\u8c03\u8bd5\u7a97\u53e3", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.theaterTab), QCoreApplication.translate("MainWindow", u"\u5267\u573a\u6a21\u5f0f", None))
        self.logLabel.setText(QCoreApplication.translate("MainWindow", u"\u5c31\u7eea", None))
    # retranslateUi

