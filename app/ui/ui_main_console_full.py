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

# 导入我们的多选组件
try:
    from app.ui.multi_select_combo import MultiSelectComboBox
    _USE_MULTI_SELECT = True
except ImportError:
    _USE_MULTI_SELECT = False

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

        # 使用多选下拉菜单替换原来的单选下拉菜单
        if _USE_MULTI_SELECT:
            self.languageComboBox = MultiSelectComboBox(self.theaterTab)
            self.languageComboBox.setPlaceholderText("选择投屏语言...")
        else:
            self.languageComboBox = QComboBox(self.theaterTab)
            self.languageComboBox.addItem("")
        self.languageComboBox.setObjectName(u"languageComboBox")
        # 初始时启用，运行时根据数据状态动态控制
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
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Miomu - 剧本对齐控制台", None))
        self.loadScriptButton.setText(QCoreApplication.translate("MainWindow", u"加载剧本", None))
        self.saveScriptButton.setText(QCoreApplication.translate("MainWindow", u"保存剧本", None))
        self.addCueButton.setText(QCoreApplication.translate("MainWindow", u"添加台词", None))
        self.deleteCueButton.setText(QCoreApplication.translate("MainWindow", u"删除台词", None))
        self.duplicateCueButton.setText(QCoreApplication.translate("MainWindow", u"复制台词", None))
        self.refreshPhonemesButton.setText(QCoreApplication.translate("MainWindow", u"刷新音素", None))
        self.addLanguageButton.setText(QCoreApplication.translate("MainWindow", u"添加语言", None))
        self.removeLanguageButton.setText(QCoreApplication.translate("MainWindow", u"移除语言", None))
        self.manageStylesButton.setText(QCoreApplication.translate("MainWindow", u"管理样式", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.editTab), QCoreApplication.translate("MainWindow", u"编辑模式", None))
        self.loadScriptTheaterButton.setText(QCoreApplication.translate("MainWindow", u"加载剧本", None))
        self.syncFromEditButton.setText(QCoreApplication.translate("MainWindow", u"同步编辑模式数据", None))
        self.filterByCharacterButton.setText(QCoreApplication.translate("MainWindow", u"按角色筛选", None))
        
        # 根据组件类型设置文本
        if _USE_MULTI_SELECT and hasattr(self.languageComboBox, 'setPlaceholderText'):
            self.languageComboBox.setPlaceholderText(QCoreApplication.translate("MainWindow", u"选择投屏语言...", None))
        elif hasattr(self.languageComboBox, 'setItemText'):
            self.languageComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"投屏语言", None))

        self.manageCharacterColorsButton.setText(QCoreApplication.translate("MainWindow", u"管理角色颜色", None))
        self.logAreaLabel.setText(QCoreApplication.translate("MainWindow", u"日志区域：", None))
        self.startButton.setText(QCoreApplication.translate("MainWindow", u"开始对齐", None))
        self.pauseButton.setText(QCoreApplication.translate("MainWindow", u"暂停", None))
        self.stopButton.setText(QCoreApplication.translate("MainWindow", u"停止", None))
        self.showSubtitleButton.setText(QCoreApplication.translate("MainWindow", u"显示字幕窗口", None))
        self.showDebugButton.setText(QCoreApplication.translate("MainWindow", u"调试窗口", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.theaterTab), QCoreApplication.translate("MainWindow", u"剧场模式", None))
        self.logLabel.setText(QCoreApplication.translate("MainWindow", u"就绪", None))
    # retranslateUi

