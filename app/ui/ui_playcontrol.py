# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'player.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QTabWidget, QTextBrowser,
    QToolButton, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1024, 768)
        self.gridLayout_main = QGridLayout(MainWindow)
        self.gridLayout_main.setObjectName(u"gridLayout_main")
        self.left_panel = QFrame(MainWindow)
        self.left_panel.setObjectName(u"left_panel")
        self.left_panel.setMinimumSize(QSize(200, 0))
        self.left_panel.setMaximumSize(QSize(250, 16777215))
        self.left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.left_panel.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.left_panel)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.initialNreset = QPushButton(self.left_panel)
        self.initialNreset.setObjectName(u"initialNreset")

        self.verticalLayout.addWidget(self.initialNreset)

        self.startAligner = QPushButton(self.left_panel)
        self.startAligner.setObjectName(u"startAligner")

        self.verticalLayout.addWidget(self.startAligner)

        self.showAllscrenns = QPushButton(self.left_panel)
        self.showAllscrenns.setObjectName(u"showAllscrenns")

        self.verticalLayout.addWidget(self.showAllscrenns)

        self.hideSubtitle = QPushButton(self.left_panel)
        self.hideSubtitle.setObjectName(u"hideSubtitle")

        self.verticalLayout.addWidget(self.hideSubtitle)

        self.horizontalLayout_audio = QHBoxLayout()
        self.horizontalLayout_audio.setObjectName(u"horizontalLayout_audio")
        self.label_audio_source = QLabel(self.left_panel)
        self.label_audio_source.setObjectName(u"label_audio_source")

        self.horizontalLayout_audio.addWidget(self.label_audio_source)

        self.comboBox_audio_source = QComboBox(self.left_panel)
        self.comboBox_audio_source.setObjectName(u"comboBox_audio_source")

        self.horizontalLayout_audio.addWidget(self.comboBox_audio_source)

        self.placeholder_1 = QPushButton(self.left_panel)
        self.placeholder_1.setObjectName(u"placeholder_1")

        self.horizontalLayout_audio.addWidget(self.placeholder_1)


        self.verticalLayout.addLayout(self.horizontalLayout_audio)

        self.horizontalLayout_stt = QHBoxLayout()
        self.horizontalLayout_stt.setObjectName(u"horizontalLayout_stt")
        self.label_STT_engine = QLabel(self.left_panel)
        self.label_STT_engine.setObjectName(u"label_STT_engine")

        self.horizontalLayout_stt.addWidget(self.label_STT_engine)

        self.comboBox_STT_engine = QComboBox(self.left_panel)
        self.comboBox_STT_engine.setObjectName(u"comboBox_STT_engine")

        self.horizontalLayout_stt.addWidget(self.comboBox_STT_engine)

        self.placeholder_2 = QPushButton(self.left_panel)
        self.placeholder_2.setObjectName(u"placeholder_2")

        self.horizontalLayout_stt.addWidget(self.placeholder_2)


        self.verticalLayout.addLayout(self.horizontalLayout_stt)

        self.verticalSpacer_left = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_left)


        self.gridLayout_main.addWidget(self.left_panel, 0, 0, 1, 1)

        self.right_panel = QFrame(MainWindow)
        self.right_panel.setObjectName(u"right_panel")
        self.right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.right_panel.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.right_panel)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.textBrowser_status = QTextBrowser(self.right_panel)
        self.textBrowser_status.setObjectName(u"textBrowser_status")
        self.textBrowser_status.setMaximumSize(QSize(16777215, 100))

        self.verticalLayout_2.addWidget(self.textBrowser_status)

        self.textBrowser_log = QTextBrowser(self.right_panel)
        self.textBrowser_log.setObjectName(u"textBrowser_log")

        self.verticalLayout_2.addWidget(self.textBrowser_log)


        self.gridLayout_main.addWidget(self.right_panel, 0, 1, 1, 1)

        self.screen_tabs = QTabWidget(MainWindow)
        self.screen_tabs.setObjectName(u"screen_tabs")
        self.screen_1 = QWidget()
        self.screen_1.setObjectName(u"screen_1")
        self.verticalLayout_tab1 = QVBoxLayout(self.screen_1)
        self.verticalLayout_tab1.setObjectName(u"verticalLayout_tab1")
        self.horizontalLayout_tab_top_1 = QHBoxLayout()
        self.horizontalLayout_tab_top_1.setObjectName(u"horizontalLayout_tab_top_1")
        self.activate_screen_1 = QCheckBox(self.screen_1)
        self.activate_screen_1.setObjectName(u"activate_screen_1")

        self.horizontalLayout_tab_top_1.addWidget(self.activate_screen_1)

        self.activate_2nd_lang_1 = QCheckBox(self.screen_1)
        self.activate_2nd_lang_1.setObjectName(u"activate_2nd_lang_1")

        self.horizontalLayout_tab_top_1.addWidget(self.activate_2nd_lang_1)

        self.hideCharname_1 = QCheckBox(self.screen_1)
        self.hideCharname_1.setObjectName(u"hideCharname_1")

        self.horizontalLayout_tab_top_1.addWidget(self.hideCharname_1)

        self.screen_AsignTo_1 = QLabel(self.screen_1)
        self.screen_AsignTo_1.setObjectName(u"screen_AsignTo_1")

        self.horizontalLayout_tab_top_1.addWidget(self.screen_AsignTo_1)

        self.comboBox_screen_assign_1 = QComboBox(self.screen_1)
        self.comboBox_screen_assign_1.setObjectName(u"comboBox_screen_assign_1")

        self.horizontalLayout_tab_top_1.addWidget(self.comboBox_screen_assign_1)

        self.pushButton_showscreen_1 = QPushButton(self.screen_1)
        self.pushButton_showscreen_1.setObjectName(u"pushButton_showscreen_1")

        self.horizontalLayout_tab_top_1.addWidget(self.pushButton_showscreen_1)


        self.verticalLayout_tab1.addLayout(self.horizontalLayout_tab_top_1)

        self.lang_subtabs_1 = QTabWidget(self.screen_1)
        self.lang_subtabs_1.setObjectName(u"lang_subtabs_1")
        self.sub_lang_1_1 = QWidget()
        self.sub_lang_1_1.setObjectName(u"sub_lang_1_1")
        self.verticalLayout_subtab1 = QVBoxLayout(self.sub_lang_1_1)
        self.verticalLayout_subtab1.setObjectName(u"verticalLayout_subtab1")
        self.gridLayout_subtab_1_1 = QGridLayout()
        self.gridLayout_subtab_1_1.setObjectName(u"gridLayout_subtab_1_1")
        self.label_lang_1_1 = QLabel(self.sub_lang_1_1)
        self.label_lang_1_1.setObjectName(u"label_lang_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.label_lang_1_1, 0, 0, 1, 1)

        self.comboBox_lang_1_1 = QComboBox(self.sub_lang_1_1)
        self.comboBox_lang_1_1.setObjectName(u"comboBox_lang_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.comboBox_lang_1_1, 0, 1, 1, 1)

        self.checkBox_audio_source_1_1 = QCheckBox(self.sub_lang_1_1)
        self.checkBox_audio_source_1_1.setObjectName(u"checkBox_audio_source_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.checkBox_audio_source_1_1, 0, 2, 1, 1)

        self.comboBox_audio_source_1_1 = QComboBox(self.sub_lang_1_1)
        self.comboBox_audio_source_1_1.setObjectName(u"comboBox_audio_source_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.comboBox_audio_source_1_1, 0, 3, 1, 1)

        self.label_font_1_1 = QLabel(self.sub_lang_1_1)
        self.label_font_1_1.setObjectName(u"label_font_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.label_font_1_1, 1, 0, 1, 1)

        self.comboBox_font_1_1 = QComboBox(self.sub_lang_1_1)
        self.comboBox_font_1_1.setObjectName(u"comboBox_font_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.comboBox_font_1_1, 1, 1, 1, 1)

        self.label_size_1_1 = QLabel(self.sub_lang_1_1)
        self.label_size_1_1.setObjectName(u"label_size_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.label_size_1_1, 1, 2, 1, 1)

        self.comboBox_size_1_1 = QComboBox(self.sub_lang_1_1)
        self.comboBox_size_1_1.setObjectName(u"comboBox_size_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.comboBox_size_1_1, 1, 3, 1, 1)

        self.label_font_color = QLabel(self.sub_lang_1_1)
        self.label_font_color.setObjectName(u"label_font_color")

        self.gridLayout_subtab_1_1.addWidget(self.label_font_color, 2, 0, 1, 1)

        self.comboBox_font_color_1_1 = QComboBox(self.sub_lang_1_1)
        self.comboBox_font_color_1_1.setObjectName(u"comboBox_font_color_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.comboBox_font_color_1_1, 2, 1, 1, 1)

        self.label_bg_color_1_1 = QLabel(self.sub_lang_1_1)
        self.label_bg_color_1_1.setObjectName(u"label_bg_color_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.label_bg_color_1_1, 2, 2, 1, 1)

        self.comboBox_bg_color = QComboBox(self.sub_lang_1_1)
        self.comboBox_bg_color.setObjectName(u"comboBox_bg_color")

        self.gridLayout_subtab_1_1.addWidget(self.comboBox_bg_color, 2, 3, 1, 1)

        self.label_position_1_1 = QLabel(self.sub_lang_1_1)
        self.label_position_1_1.setObjectName(u"label_position_1_1")

        self.gridLayout_subtab_1_1.addWidget(self.label_position_1_1, 3, 0, 1, 1)

        self.frame_dpad_1_1 = QFrame(self.sub_lang_1_1)
        self.frame_dpad_1_1.setObjectName(u"frame_dpad_1_1")
        self.frame_dpad_1_1.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_dpad_1_1.setFrameShadow(QFrame.Shadow.Plain)
        self.gridLayout_dpad = QGridLayout(self.frame_dpad_1_1)
        self.gridLayout_dpad.setObjectName(u"gridLayout_dpad")
        self.toolButton_up_1_1 = QToolButton(self.frame_dpad_1_1)
        self.toolButton_up_1_1.setObjectName(u"toolButton_up_1_1")
        self.toolButton_up_1_1.setArrowType(Qt.ArrowType.UpArrow)

        self.gridLayout_dpad.addWidget(self.toolButton_up_1_1, 0, 1, 1, 1)

        self.toolButton_left_1_1 = QToolButton(self.frame_dpad_1_1)
        self.toolButton_left_1_1.setObjectName(u"toolButton_left_1_1")
        self.toolButton_left_1_1.setArrowType(Qt.ArrowType.LeftArrow)

        self.gridLayout_dpad.addWidget(self.toolButton_left_1_1, 1, 0, 1, 1)

        self.toolButton_center_1_1 = QToolButton(self.frame_dpad_1_1)
        self.toolButton_center_1_1.setObjectName(u"toolButton_center_1_1")

        self.gridLayout_dpad.addWidget(self.toolButton_center_1_1, 1, 1, 1, 1)

        self.toolButton_right_1_1 = QToolButton(self.frame_dpad_1_1)
        self.toolButton_right_1_1.setObjectName(u"toolButton_right_1_1")
        self.toolButton_right_1_1.setArrowType(Qt.ArrowType.RightArrow)

        self.gridLayout_dpad.addWidget(self.toolButton_right_1_1, 1, 2, 1, 1)

        self.toolButton_down_1_1 = QToolButton(self.frame_dpad_1_1)
        self.toolButton_down_1_1.setObjectName(u"toolButton_down_1_1")
        self.toolButton_down_1_1.setArrowType(Qt.ArrowType.DownArrow)

        self.gridLayout_dpad.addWidget(self.toolButton_down_1_1, 2, 1, 1, 1)


        self.gridLayout_subtab_1_1.addWidget(self.frame_dpad_1_1, 4, 0, 1, 2)


        self.verticalLayout_subtab1.addLayout(self.gridLayout_subtab_1_1)

        self.verticalSpacer_subtab_1_1 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_subtab1.addItem(self.verticalSpacer_subtab_1_1)

        self.lang_subtabs_1.addTab(self.sub_lang_1_1, "")
        self.sub_lang_1_2 = QWidget()
        self.sub_lang_1_2.setObjectName(u"sub_lang_1_2")
        self.verticalLayout_subtab2 = QVBoxLayout(self.sub_lang_1_2)
        self.verticalLayout_subtab2.setObjectName(u"verticalLayout_subtab2")
        self.gridLayout_subtab_1_2 = QGridLayout()
        self.gridLayout_subtab_1_2.setObjectName(u"gridLayout_subtab_1_2")
        self.label_lang_1_2 = QLabel(self.sub_lang_1_2)
        self.label_lang_1_2.setObjectName(u"label_lang_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.label_lang_1_2, 0, 0, 1, 1)

        self.comboBox_lang_1_2 = QComboBox(self.sub_lang_1_2)
        self.comboBox_lang_1_2.setObjectName(u"comboBox_lang_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.comboBox_lang_1_2, 0, 1, 1, 1)

        self.checkBox_audio_source_1_2 = QCheckBox(self.sub_lang_1_2)
        self.checkBox_audio_source_1_2.setObjectName(u"checkBox_audio_source_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.checkBox_audio_source_1_2, 0, 2, 1, 1)

        self.comboBox_subtab_1_2 = QComboBox(self.sub_lang_1_2)
        self.comboBox_subtab_1_2.setObjectName(u"comboBox_subtab_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.comboBox_subtab_1_2, 0, 3, 1, 1)

        self.label_font_1_2 = QLabel(self.sub_lang_1_2)
        self.label_font_1_2.setObjectName(u"label_font_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.label_font_1_2, 1, 0, 1, 1)

        self.comboBox_font_1_2 = QComboBox(self.sub_lang_1_2)
        self.comboBox_font_1_2.setObjectName(u"comboBox_font_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.comboBox_font_1_2, 1, 1, 1, 1)

        self.label_size_1_2 = QLabel(self.sub_lang_1_2)
        self.label_size_1_2.setObjectName(u"label_size_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.label_size_1_2, 1, 2, 1, 1)

        self.comboBox_size_1_2 = QComboBox(self.sub_lang_1_2)
        self.comboBox_size_1_2.setObjectName(u"comboBox_size_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.comboBox_size_1_2, 1, 3, 1, 1)

        self.label_font_color_1_2 = QLabel(self.sub_lang_1_2)
        self.label_font_color_1_2.setObjectName(u"label_font_color_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.label_font_color_1_2, 2, 0, 1, 1)

        self.comboBox_font_color_1_2 = QComboBox(self.sub_lang_1_2)
        self.comboBox_font_color_1_2.setObjectName(u"comboBox_font_color_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.comboBox_font_color_1_2, 2, 1, 1, 1)

        self.label_bg_color_1_2 = QLabel(self.sub_lang_1_2)
        self.label_bg_color_1_2.setObjectName(u"label_bg_color_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.label_bg_color_1_2, 2, 2, 1, 1)

        self.comboBox_bg_color_1_2 = QComboBox(self.sub_lang_1_2)
        self.comboBox_bg_color_1_2.setObjectName(u"comboBox_bg_color_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.comboBox_bg_color_1_2, 2, 3, 1, 1)

        self.label_position_1_2 = QLabel(self.sub_lang_1_2)
        self.label_position_1_2.setObjectName(u"label_position_1_2")

        self.gridLayout_subtab_1_2.addWidget(self.label_position_1_2, 3, 0, 1, 1)

        self.frame_dpad_1_2 = QFrame(self.sub_lang_1_2)
        self.frame_dpad_1_2.setObjectName(u"frame_dpad_1_2")
        self.frame_dpad_1_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_dpad_1_2.setFrameShadow(QFrame.Shadow.Plain)
        self.gridLayout_dpad_2 = QGridLayout(self.frame_dpad_1_2)
        self.gridLayout_dpad_2.setObjectName(u"gridLayout_dpad_2")
        self.toolButton_up_2 = QToolButton(self.frame_dpad_1_2)
        self.toolButton_up_2.setObjectName(u"toolButton_up_2")
        self.toolButton_up_2.setArrowType(Qt.ArrowType.UpArrow)

        self.gridLayout_dpad_2.addWidget(self.toolButton_up_2, 0, 1, 1, 1)

        self.toolButton_left_1_2 = QToolButton(self.frame_dpad_1_2)
        self.toolButton_left_1_2.setObjectName(u"toolButton_left_1_2")
        self.toolButton_left_1_2.setArrowType(Qt.ArrowType.LeftArrow)

        self.gridLayout_dpad_2.addWidget(self.toolButton_left_1_2, 1, 0, 1, 1)

        self.toolButton_center_1_2 = QToolButton(self.frame_dpad_1_2)
        self.toolButton_center_1_2.setObjectName(u"toolButton_center_1_2")

        self.gridLayout_dpad_2.addWidget(self.toolButton_center_1_2, 1, 1, 1, 1)

        self.toolButton_right_1_2 = QToolButton(self.frame_dpad_1_2)
        self.toolButton_right_1_2.setObjectName(u"toolButton_right_1_2")
        self.toolButton_right_1_2.setArrowType(Qt.ArrowType.RightArrow)

        self.gridLayout_dpad_2.addWidget(self.toolButton_right_1_2, 1, 2, 1, 1)

        self.toolButton_down_1_2 = QToolButton(self.frame_dpad_1_2)
        self.toolButton_down_1_2.setObjectName(u"toolButton_down_1_2")
        self.toolButton_down_1_2.setArrowType(Qt.ArrowType.DownArrow)

        self.gridLayout_dpad_2.addWidget(self.toolButton_down_1_2, 2, 1, 1, 1)


        self.gridLayout_subtab_1_2.addWidget(self.frame_dpad_1_2, 4, 0, 1, 2)


        self.verticalLayout_subtab2.addLayout(self.gridLayout_subtab_1_2)

        self.verticalSpacer_subtab_1_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_subtab2.addItem(self.verticalSpacer_subtab_1_2)

        self.lang_subtabs_1.addTab(self.sub_lang_1_2, "")

        self.verticalLayout_tab1.addWidget(self.lang_subtabs_1)

        self.screen_tabs.addTab(self.screen_1, "")
        self.screen_2 = QWidget()
        self.screen_2.setObjectName(u"screen_2")
        self.verticalLayout_tab2 = QVBoxLayout(self.screen_2)
        self.verticalLayout_tab2.setObjectName(u"verticalLayout_tab2")
        self.horizontalLayout_tab_top_2 = QHBoxLayout()
        self.horizontalLayout_tab_top_2.setObjectName(u"horizontalLayout_tab_top_2")
        self.activate_screen_2 = QCheckBox(self.screen_2)
        self.activate_screen_2.setObjectName(u"activate_screen_2")

        self.horizontalLayout_tab_top_2.addWidget(self.activate_screen_2)

        self.activate_2nd_lang_2 = QCheckBox(self.screen_2)
        self.activate_2nd_lang_2.setObjectName(u"activate_2nd_lang_2")

        self.horizontalLayout_tab_top_2.addWidget(self.activate_2nd_lang_2)

        self.hideCharname_2 = QCheckBox(self.screen_2)
        self.hideCharname_2.setObjectName(u"hideCharname_2")

        self.horizontalLayout_tab_top_2.addWidget(self.hideCharname_2)

        self.screen_AsignTo_2 = QLabel(self.screen_2)
        self.screen_AsignTo_2.setObjectName(u"screen_AsignTo_2")

        self.horizontalLayout_tab_top_2.addWidget(self.screen_AsignTo_2)

        self.comboBox_screen_assign_2 = QComboBox(self.screen_2)
        self.comboBox_screen_assign_2.setObjectName(u"comboBox_screen_assign_2")

        self.horizontalLayout_tab_top_2.addWidget(self.comboBox_screen_assign_2)

        self.pushButton_showscreen_2 = QPushButton(self.screen_2)
        self.pushButton_showscreen_2.setObjectName(u"pushButton_showscreen_2")

        self.horizontalLayout_tab_top_2.addWidget(self.pushButton_showscreen_2)


        self.verticalLayout_tab2.addLayout(self.horizontalLayout_tab_top_2)

        self.lang_subtabs_2 = QTabWidget(self.screen_2)
        self.lang_subtabs_2.setObjectName(u"lang_subtabs_2")
        self.sub_lang_2_1 = QWidget()
        self.sub_lang_2_1.setObjectName(u"sub_lang_2_1")
        self.verticalLayout_subtab3 = QVBoxLayout(self.sub_lang_2_1)
        self.verticalLayout_subtab3.setObjectName(u"verticalLayout_subtab3")
        self.gridLayout_subtab_2_1 = QGridLayout()
        self.gridLayout_subtab_2_1.setObjectName(u"gridLayout_subtab_2_1")
        self.label_lang_2_1 = QLabel(self.sub_lang_2_1)
        self.label_lang_2_1.setObjectName(u"label_lang_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.label_lang_2_1, 0, 0, 1, 1)

        self.comboBox_lang_2_1 = QComboBox(self.sub_lang_2_1)
        self.comboBox_lang_2_1.setObjectName(u"comboBox_lang_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.comboBox_lang_2_1, 0, 1, 1, 1)

        self.checkBox_subtab_2_1 = QCheckBox(self.sub_lang_2_1)
        self.checkBox_subtab_2_1.setObjectName(u"checkBox_subtab_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.checkBox_subtab_2_1, 0, 2, 1, 1)

        self.comboBox_subtab_2_1 = QComboBox(self.sub_lang_2_1)
        self.comboBox_subtab_2_1.setObjectName(u"comboBox_subtab_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.comboBox_subtab_2_1, 0, 3, 1, 1)

        self.label_font_2_1 = QLabel(self.sub_lang_2_1)
        self.label_font_2_1.setObjectName(u"label_font_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.label_font_2_1, 1, 0, 1, 1)

        self.comboBox_font_2_1 = QComboBox(self.sub_lang_2_1)
        self.comboBox_font_2_1.setObjectName(u"comboBox_font_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.comboBox_font_2_1, 1, 1, 1, 1)

        self.label_size_2_1 = QLabel(self.sub_lang_2_1)
        self.label_size_2_1.setObjectName(u"label_size_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.label_size_2_1, 1, 2, 1, 1)

        self.comboBox_size_2_1 = QComboBox(self.sub_lang_2_1)
        self.comboBox_size_2_1.setObjectName(u"comboBox_size_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.comboBox_size_2_1, 1, 3, 1, 1)

        self.label_font_color_2_1 = QLabel(self.sub_lang_2_1)
        self.label_font_color_2_1.setObjectName(u"label_font_color_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.label_font_color_2_1, 2, 0, 1, 1)

        self.comboBox_font_color_2_1 = QComboBox(self.sub_lang_2_1)
        self.comboBox_font_color_2_1.setObjectName(u"comboBox_font_color_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.comboBox_font_color_2_1, 2, 1, 1, 1)

        self.label_bg_color_2_1 = QLabel(self.sub_lang_2_1)
        self.label_bg_color_2_1.setObjectName(u"label_bg_color_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.label_bg_color_2_1, 2, 2, 1, 1)

        self.comboBox_bg_color_2_1 = QComboBox(self.sub_lang_2_1)
        self.comboBox_bg_color_2_1.setObjectName(u"comboBox_bg_color_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.comboBox_bg_color_2_1, 2, 3, 1, 1)

        self.label_position_2_1 = QLabel(self.sub_lang_2_1)
        self.label_position_2_1.setObjectName(u"label_position_2_1")

        self.gridLayout_subtab_2_1.addWidget(self.label_position_2_1, 3, 0, 1, 1)

        self.frame_dpad_2_1 = QFrame(self.sub_lang_2_1)
        self.frame_dpad_2_1.setObjectName(u"frame_dpad_2_1")
        self.frame_dpad_2_1.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_dpad_2_1.setFrameShadow(QFrame.Shadow.Plain)
        self.gridLayout_dpad_2_1 = QGridLayout(self.frame_dpad_2_1)
        self.gridLayout_dpad_2_1.setObjectName(u"gridLayout_dpad_2_1")
        self.toolButton_up_2_1 = QToolButton(self.frame_dpad_2_1)
        self.toolButton_up_2_1.setObjectName(u"toolButton_up_2_1")
        self.toolButton_up_2_1.setArrowType(Qt.ArrowType.UpArrow)

        self.gridLayout_dpad_2_1.addWidget(self.toolButton_up_2_1, 0, 1, 1, 1)

        self.toolButton_left_2_1 = QToolButton(self.frame_dpad_2_1)
        self.toolButton_left_2_1.setObjectName(u"toolButton_left_2_1")
        self.toolButton_left_2_1.setArrowType(Qt.ArrowType.LeftArrow)

        self.gridLayout_dpad_2_1.addWidget(self.toolButton_left_2_1, 1, 0, 1, 1)

        self.toolButton_center_2_1 = QToolButton(self.frame_dpad_2_1)
        self.toolButton_center_2_1.setObjectName(u"toolButton_center_2_1")

        self.gridLayout_dpad_2_1.addWidget(self.toolButton_center_2_1, 1, 1, 1, 1)

        self.toolButton_right_2_1 = QToolButton(self.frame_dpad_2_1)
        self.toolButton_right_2_1.setObjectName(u"toolButton_right_2_1")
        self.toolButton_right_2_1.setArrowType(Qt.ArrowType.RightArrow)

        self.gridLayout_dpad_2_1.addWidget(self.toolButton_right_2_1, 1, 2, 1, 1)

        self.toolButton_down_2_1 = QToolButton(self.frame_dpad_2_1)
        self.toolButton_down_2_1.setObjectName(u"toolButton_down_2_1")
        self.toolButton_down_2_1.setArrowType(Qt.ArrowType.DownArrow)

        self.gridLayout_dpad_2_1.addWidget(self.toolButton_down_2_1, 2, 1, 1, 1)


        self.gridLayout_subtab_2_1.addWidget(self.frame_dpad_2_1, 4, 0, 1, 2)


        self.verticalLayout_subtab3.addLayout(self.gridLayout_subtab_2_1)

        self.verticalSpacer_subtab_2_1 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_subtab3.addItem(self.verticalSpacer_subtab_2_1)

        self.lang_subtabs_2.addTab(self.sub_lang_2_1, "")
        self.sub_lang_2_2 = QWidget()
        self.sub_lang_2_2.setObjectName(u"sub_lang_2_2")
        self.verticalLayout_subtab4 = QVBoxLayout(self.sub_lang_2_2)
        self.verticalLayout_subtab4.setObjectName(u"verticalLayout_subtab4")
        self.gridLayout_subtab_2_2 = QGridLayout()
        self.gridLayout_subtab_2_2.setObjectName(u"gridLayout_subtab_2_2")
        self.label_lang_2_2 = QLabel(self.sub_lang_2_2)
        self.label_lang_2_2.setObjectName(u"label_lang_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.label_lang_2_2, 0, 0, 1, 1)

        self.comboBox_lang_2_2 = QComboBox(self.sub_lang_2_2)
        self.comboBox_lang_2_2.setObjectName(u"comboBox_lang_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.comboBox_lang_2_2, 0, 1, 1, 1)

        self.checkBox_subtab_2_2 = QCheckBox(self.sub_lang_2_2)
        self.checkBox_subtab_2_2.setObjectName(u"checkBox_subtab_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.checkBox_subtab_2_2, 0, 2, 1, 1)

        self.comboBox_subtab_2_2 = QComboBox(self.sub_lang_2_2)
        self.comboBox_subtab_2_2.setObjectName(u"comboBox_subtab_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.comboBox_subtab_2_2, 0, 3, 1, 1)

        self.label_font_2_2 = QLabel(self.sub_lang_2_2)
        self.label_font_2_2.setObjectName(u"label_font_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.label_font_2_2, 1, 0, 1, 1)

        self.comboBox_font_2_2 = QComboBox(self.sub_lang_2_2)
        self.comboBox_font_2_2.setObjectName(u"comboBox_font_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.comboBox_font_2_2, 1, 1, 1, 1)

        self.label_size_2_2 = QLabel(self.sub_lang_2_2)
        self.label_size_2_2.setObjectName(u"label_size_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.label_size_2_2, 1, 2, 1, 1)

        self.comboBox_size_2_2 = QComboBox(self.sub_lang_2_2)
        self.comboBox_size_2_2.setObjectName(u"comboBox_size_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.comboBox_size_2_2, 1, 3, 1, 1)

        self.label_font_color_2_2 = QLabel(self.sub_lang_2_2)
        self.label_font_color_2_2.setObjectName(u"label_font_color_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.label_font_color_2_2, 2, 0, 1, 1)

        self.comboBox_font_color_2_2 = QComboBox(self.sub_lang_2_2)
        self.comboBox_font_color_2_2.setObjectName(u"comboBox_font_color_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.comboBox_font_color_2_2, 2, 1, 1, 1)

        self.label_bg_color_2_2 = QLabel(self.sub_lang_2_2)
        self.label_bg_color_2_2.setObjectName(u"label_bg_color_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.label_bg_color_2_2, 2, 2, 1, 1)

        self.comboBox_bg_color_2_2 = QComboBox(self.sub_lang_2_2)
        self.comboBox_bg_color_2_2.setObjectName(u"comboBox_bg_color_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.comboBox_bg_color_2_2, 2, 3, 1, 1)

        self.label_position_2_2 = QLabel(self.sub_lang_2_2)
        self.label_position_2_2.setObjectName(u"label_position_2_2")

        self.gridLayout_subtab_2_2.addWidget(self.label_position_2_2, 3, 0, 1, 1)

        self.frame_dpad_2_2 = QFrame(self.sub_lang_2_2)
        self.frame_dpad_2_2.setObjectName(u"frame_dpad_2_2")
        self.frame_dpad_2_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_dpad_2_2.setFrameShadow(QFrame.Shadow.Plain)
        self.gridLayout_dpad_2_2 = QGridLayout(self.frame_dpad_2_2)
        self.gridLayout_dpad_2_2.setObjectName(u"gridLayout_dpad_2_2")
        self.toolButton_up_2_2 = QToolButton(self.frame_dpad_2_2)
        self.toolButton_up_2_2.setObjectName(u"toolButton_up_2_2")
        self.toolButton_up_2_2.setArrowType(Qt.ArrowType.UpArrow)

        self.gridLayout_dpad_2_2.addWidget(self.toolButton_up_2_2, 0, 1, 1, 1)

        self.toolButton_left_2_2 = QToolButton(self.frame_dpad_2_2)
        self.toolButton_left_2_2.setObjectName(u"toolButton_left_2_2")
        self.toolButton_left_2_2.setArrowType(Qt.ArrowType.LeftArrow)

        self.gridLayout_dpad_2_2.addWidget(self.toolButton_left_2_2, 1, 0, 1, 1)

        self.toolButton_center_2_2 = QToolButton(self.frame_dpad_2_2)
        self.toolButton_center_2_2.setObjectName(u"toolButton_center_2_2")

        self.gridLayout_dpad_2_2.addWidget(self.toolButton_center_2_2, 1, 1, 1, 1)

        self.toolButton_right_2_2 = QToolButton(self.frame_dpad_2_2)
        self.toolButton_right_2_2.setObjectName(u"toolButton_right_2_2")
        self.toolButton_right_2_2.setArrowType(Qt.ArrowType.RightArrow)

        self.gridLayout_dpad_2_2.addWidget(self.toolButton_right_2_2, 1, 2, 1, 1)

        self.toolButton_down_2_2 = QToolButton(self.frame_dpad_2_2)
        self.toolButton_down_2_2.setObjectName(u"toolButton_down_2_2")
        self.toolButton_down_2_2.setArrowType(Qt.ArrowType.DownArrow)

        self.gridLayout_dpad_2_2.addWidget(self.toolButton_down_2_2, 2, 1, 1, 1)


        self.gridLayout_subtab_2_2.addWidget(self.frame_dpad_2_2, 4, 0, 1, 2)


        self.verticalLayout_subtab4.addLayout(self.gridLayout_subtab_2_2)

        self.verticalSpacer_subtab_2_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_subtab4.addItem(self.verticalSpacer_subtab_2_2)

        self.lang_subtabs_2.addTab(self.sub_lang_2_2, "")

        self.verticalLayout_tab2.addWidget(self.lang_subtabs_2)

        self.screen_tabs.addTab(self.screen_2, "")
        self.screen_3 = QWidget()
        self.screen_3.setObjectName(u"screen_3")
        self.verticalLayout_tab3 = QVBoxLayout(self.screen_3)
        self.verticalLayout_tab3.setObjectName(u"verticalLayout_tab3")
        self.horizontalLayout_tab3_top = QHBoxLayout()
        self.horizontalLayout_tab3_top.setObjectName(u"horizontalLayout_tab3_top")
        self.activate_screen_3 = QCheckBox(self.screen_3)
        self.activate_screen_3.setObjectName(u"activate_screen_3")

        self.horizontalLayout_tab3_top.addWidget(self.activate_screen_3)

        self.activate_2nd_lang_3 = QCheckBox(self.screen_3)
        self.activate_2nd_lang_3.setObjectName(u"activate_2nd_lang_3")

        self.horizontalLayout_tab3_top.addWidget(self.activate_2nd_lang_3)

        self.hideCharname_3 = QCheckBox(self.screen_3)
        self.hideCharname_3.setObjectName(u"hideCharname_3")

        self.horizontalLayout_tab3_top.addWidget(self.hideCharname_3)

        self.label_tab3_assign = QLabel(self.screen_3)
        self.label_tab3_assign.setObjectName(u"label_tab3_assign")

        self.horizontalLayout_tab3_top.addWidget(self.label_tab3_assign)

        self.comboBox_screen_assign_3 = QComboBox(self.screen_3)
        self.comboBox_screen_assign_3.setObjectName(u"comboBox_screen_assign_3")

        self.horizontalLayout_tab3_top.addWidget(self.comboBox_screen_assign_3)

        self.pushButton_showscreen_3 = QPushButton(self.screen_3)
        self.pushButton_showscreen_3.setObjectName(u"pushButton_showscreen_3")

        self.horizontalLayout_tab3_top.addWidget(self.pushButton_showscreen_3)


        self.verticalLayout_tab3.addLayout(self.horizontalLayout_tab3_top)

        self.lang_subtabs_3 = QTabWidget(self.screen_3)
        self.lang_subtabs_3.setObjectName(u"lang_subtabs_3")
        self.sub_lang_3_1 = QWidget()
        self.sub_lang_3_1.setObjectName(u"sub_lang_3_1")
        self.verticalLayout_subtab5 = QVBoxLayout(self.sub_lang_3_1)
        self.verticalLayout_subtab5.setObjectName(u"verticalLayout_subtab5")
        self.gridLayout_subtab_3_1 = QGridLayout()
        self.gridLayout_subtab_3_1.setObjectName(u"gridLayout_subtab_3_1")
        self.label_lang_3_1 = QLabel(self.sub_lang_3_1)
        self.label_lang_3_1.setObjectName(u"label_lang_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.label_lang_3_1, 0, 0, 1, 1)

        self.comboBox_lang_3_1 = QComboBox(self.sub_lang_3_1)
        self.comboBox_lang_3_1.setObjectName(u"comboBox_lang_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.comboBox_lang_3_1, 0, 1, 1, 1)

        self.checkBox_subtab_3_1 = QCheckBox(self.sub_lang_3_1)
        self.checkBox_subtab_3_1.setObjectName(u"checkBox_subtab_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.checkBox_subtab_3_1, 0, 2, 1, 1)

        self.comboBox_subtab_3_1 = QComboBox(self.sub_lang_3_1)
        self.comboBox_subtab_3_1.setObjectName(u"comboBox_subtab_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.comboBox_subtab_3_1, 0, 3, 1, 1)

        self.label_font_3_1 = QLabel(self.sub_lang_3_1)
        self.label_font_3_1.setObjectName(u"label_font_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.label_font_3_1, 1, 0, 1, 1)

        self.comboBox_font_3_1 = QComboBox(self.sub_lang_3_1)
        self.comboBox_font_3_1.setObjectName(u"comboBox_font_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.comboBox_font_3_1, 1, 1, 1, 1)

        self.label_size_3_1 = QLabel(self.sub_lang_3_1)
        self.label_size_3_1.setObjectName(u"label_size_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.label_size_3_1, 1, 2, 1, 1)

        self.comboBox_size_3_1 = QComboBox(self.sub_lang_3_1)
        self.comboBox_size_3_1.setObjectName(u"comboBox_size_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.comboBox_size_3_1, 1, 3, 1, 1)

        self.label_font_color_3_1 = QLabel(self.sub_lang_3_1)
        self.label_font_color_3_1.setObjectName(u"label_font_color_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.label_font_color_3_1, 2, 0, 1, 1)

        self.comboBox_font_color_3_1 = QComboBox(self.sub_lang_3_1)
        self.comboBox_font_color_3_1.setObjectName(u"comboBox_font_color_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.comboBox_font_color_3_1, 2, 1, 1, 1)

        self.label_bg_color_3_1 = QLabel(self.sub_lang_3_1)
        self.label_bg_color_3_1.setObjectName(u"label_bg_color_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.label_bg_color_3_1, 2, 2, 1, 1)

        self.comboBox_bg_color_3_1 = QComboBox(self.sub_lang_3_1)
        self.comboBox_bg_color_3_1.setObjectName(u"comboBox_bg_color_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.comboBox_bg_color_3_1, 2, 3, 1, 1)

        self.label_position_3_1 = QLabel(self.sub_lang_3_1)
        self.label_position_3_1.setObjectName(u"label_position_3_1")

        self.gridLayout_subtab_3_1.addWidget(self.label_position_3_1, 3, 0, 1, 1)

        self.frame_dpad_3_1 = QFrame(self.sub_lang_3_1)
        self.frame_dpad_3_1.setObjectName(u"frame_dpad_3_1")
        self.frame_dpad_3_1.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_dpad_3_1.setFrameShadow(QFrame.Shadow.Plain)
        self.gridLayout_dpad_3_1 = QGridLayout(self.frame_dpad_3_1)
        self.gridLayout_dpad_3_1.setObjectName(u"gridLayout_dpad_3_1")
        self.toolButton_up_3_1 = QToolButton(self.frame_dpad_3_1)
        self.toolButton_up_3_1.setObjectName(u"toolButton_up_3_1")
        self.toolButton_up_3_1.setArrowType(Qt.ArrowType.UpArrow)

        self.gridLayout_dpad_3_1.addWidget(self.toolButton_up_3_1, 0, 1, 1, 1)

        self.toolButton_left_3_1 = QToolButton(self.frame_dpad_3_1)
        self.toolButton_left_3_1.setObjectName(u"toolButton_left_3_1")
        self.toolButton_left_3_1.setArrowType(Qt.ArrowType.LeftArrow)

        self.gridLayout_dpad_3_1.addWidget(self.toolButton_left_3_1, 1, 0, 1, 1)

        self.toolButton_center_3_1 = QToolButton(self.frame_dpad_3_1)
        self.toolButton_center_3_1.setObjectName(u"toolButton_center_3_1")

        self.gridLayout_dpad_3_1.addWidget(self.toolButton_center_3_1, 1, 1, 1, 1)

        self.toolButton_right_3_1 = QToolButton(self.frame_dpad_3_1)
        self.toolButton_right_3_1.setObjectName(u"toolButton_right_3_1")
        self.toolButton_right_3_1.setArrowType(Qt.ArrowType.RightArrow)

        self.gridLayout_dpad_3_1.addWidget(self.toolButton_right_3_1, 1, 2, 1, 1)

        self.toolButton_down_3_1 = QToolButton(self.frame_dpad_3_1)
        self.toolButton_down_3_1.setObjectName(u"toolButton_down_3_1")
        self.toolButton_down_3_1.setArrowType(Qt.ArrowType.DownArrow)

        self.gridLayout_dpad_3_1.addWidget(self.toolButton_down_3_1, 2, 1, 1, 1)


        self.gridLayout_subtab_3_1.addWidget(self.frame_dpad_3_1, 4, 0, 1, 2)


        self.verticalLayout_subtab5.addLayout(self.gridLayout_subtab_3_1)

        self.verticalSpacer_subtab_3_1 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_subtab5.addItem(self.verticalSpacer_subtab_3_1)

        self.lang_subtabs_3.addTab(self.sub_lang_3_1, "")
        self.sub_lang_3_2 = QWidget()
        self.sub_lang_3_2.setObjectName(u"sub_lang_3_2")
        self.verticalLayout_subtab6 = QVBoxLayout(self.sub_lang_3_2)
        self.verticalLayout_subtab6.setObjectName(u"verticalLayout_subtab6")
        self.gridLayout_subtab_3_2 = QGridLayout()
        self.gridLayout_subtab_3_2.setObjectName(u"gridLayout_subtab_3_2")
        self.label_lang_3_2 = QLabel(self.sub_lang_3_2)
        self.label_lang_3_2.setObjectName(u"label_lang_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.label_lang_3_2, 0, 0, 1, 1)

        self.comboBox_lang_3_2 = QComboBox(self.sub_lang_3_2)
        self.comboBox_lang_3_2.setObjectName(u"comboBox_lang_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.comboBox_lang_3_2, 0, 1, 1, 1)

        self.checkBox_subtab_3_2 = QCheckBox(self.sub_lang_3_2)
        self.checkBox_subtab_3_2.setObjectName(u"checkBox_subtab_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.checkBox_subtab_3_2, 0, 2, 1, 1)

        self.comboBox_subtab_3_2 = QComboBox(self.sub_lang_3_2)
        self.comboBox_subtab_3_2.setObjectName(u"comboBox_subtab_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.comboBox_subtab_3_2, 0, 3, 1, 1)

        self.label_font_3_2 = QLabel(self.sub_lang_3_2)
        self.label_font_3_2.setObjectName(u"label_font_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.label_font_3_2, 1, 0, 1, 1)

        self.comboBox_font_3_2 = QComboBox(self.sub_lang_3_2)
        self.comboBox_font_3_2.setObjectName(u"comboBox_font_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.comboBox_font_3_2, 1, 1, 1, 1)

        self.label_size_3_2 = QLabel(self.sub_lang_3_2)
        self.label_size_3_2.setObjectName(u"label_size_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.label_size_3_2, 1, 2, 1, 1)

        self.comboBox_size_3_2 = QComboBox(self.sub_lang_3_2)
        self.comboBox_size_3_2.setObjectName(u"comboBox_size_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.comboBox_size_3_2, 1, 3, 1, 1)

        self.label_font_color_3_2 = QLabel(self.sub_lang_3_2)
        self.label_font_color_3_2.setObjectName(u"label_font_color_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.label_font_color_3_2, 2, 0, 1, 1)

        self.comboBox_font_color_3_2 = QComboBox(self.sub_lang_3_2)
        self.comboBox_font_color_3_2.setObjectName(u"comboBox_font_color_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.comboBox_font_color_3_2, 2, 1, 1, 1)

        self.label_bg_color_3_2 = QLabel(self.sub_lang_3_2)
        self.label_bg_color_3_2.setObjectName(u"label_bg_color_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.label_bg_color_3_2, 2, 2, 1, 1)

        self.comboBox_bg_color_3_2 = QComboBox(self.sub_lang_3_2)
        self.comboBox_bg_color_3_2.setObjectName(u"comboBox_bg_color_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.comboBox_bg_color_3_2, 2, 3, 1, 1)

        self.label_position_3_2 = QLabel(self.sub_lang_3_2)
        self.label_position_3_2.setObjectName(u"label_position_3_2")

        self.gridLayout_subtab_3_2.addWidget(self.label_position_3_2, 3, 0, 1, 1)

        self.frame_dpad_3_2 = QFrame(self.sub_lang_3_2)
        self.frame_dpad_3_2.setObjectName(u"frame_dpad_3_2")
        self.frame_dpad_3_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_dpad_3_2.setFrameShadow(QFrame.Shadow.Plain)
        self.gridLayout_dpad_3_2 = QGridLayout(self.frame_dpad_3_2)
        self.gridLayout_dpad_3_2.setObjectName(u"gridLayout_dpad_3_2")
        self.toolButton_up_3_2 = QToolButton(self.frame_dpad_3_2)
        self.toolButton_up_3_2.setObjectName(u"toolButton_up_3_2")
        self.toolButton_up_3_2.setArrowType(Qt.ArrowType.UpArrow)

        self.gridLayout_dpad_3_2.addWidget(self.toolButton_up_3_2, 0, 1, 1, 1)

        self.toolButton_left_3_2 = QToolButton(self.frame_dpad_3_2)
        self.toolButton_left_3_2.setObjectName(u"toolButton_left_3_2")
        self.toolButton_left_3_2.setArrowType(Qt.ArrowType.LeftArrow)

        self.gridLayout_dpad_3_2.addWidget(self.toolButton_left_3_2, 1, 0, 1, 1)

        self.toolButton_center_3_2 = QToolButton(self.frame_dpad_3_2)
        self.toolButton_center_3_2.setObjectName(u"toolButton_center_3_2")

        self.gridLayout_dpad_3_2.addWidget(self.toolButton_center_3_2, 1, 1, 1, 1)

        self.toolButton_right_3_2 = QToolButton(self.frame_dpad_3_2)
        self.toolButton_right_3_2.setObjectName(u"toolButton_right_3_2")
        self.toolButton_right_3_2.setArrowType(Qt.ArrowType.RightArrow)

        self.gridLayout_dpad_3_2.addWidget(self.toolButton_right_3_2, 1, 2, 1, 1)

        self.toolButton_down_3_2 = QToolButton(self.frame_dpad_3_2)
        self.toolButton_down_3_2.setObjectName(u"toolButton_down_3_2")
        self.toolButton_down_3_2.setArrowType(Qt.ArrowType.DownArrow)

        self.gridLayout_dpad_3_2.addWidget(self.toolButton_down_3_2, 2, 1, 1, 1)


        self.gridLayout_subtab_3_2.addWidget(self.frame_dpad_3_2, 4, 0, 1, 2)


        self.verticalLayout_subtab6.addLayout(self.gridLayout_subtab_3_2)

        self.verticalSpacer_subtab_3_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_subtab6.addItem(self.verticalSpacer_subtab_3_2)

        self.lang_subtabs_3.addTab(self.sub_lang_3_2, "")

        self.verticalLayout_tab3.addWidget(self.lang_subtabs_3)

        self.screen_tabs.addTab(self.screen_3, "")

        self.gridLayout_main.addWidget(self.screen_tabs, 1, 0, 1, 2)


        self.retranslateUi(MainWindow)

        self.lang_subtabs_1.setCurrentIndex(0)
        self.lang_subtabs_2.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"App UI", None))
        self.initialNreset.setText(QCoreApplication.translate("MainWindow", u"\u521d\u59cb\u5316/\u91cd\u7f6e", None))
        self.startAligner.setText(QCoreApplication.translate("MainWindow", u"\u5f00\u59cb\u5bf9\u9f50", None))
        self.showAllscrenns.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793a\u6240\u6709\u5b57\u5e55\u7a97\u53e3", None))
        self.hideSubtitle.setText(QCoreApplication.translate("MainWindow", u"\u906e\u853d\u5b57\u5e55", None))
        self.label_audio_source.setText(QCoreApplication.translate("MainWindow", u"\u97f3\u9891\u6e90", None))
        self.placeholder_1.setText(QCoreApplication.translate("MainWindow", u"Button", None))
        self.label_STT_engine.setText(QCoreApplication.translate("MainWindow", u"STT\u5f15\u64ce", None))
        self.placeholder_2.setText(QCoreApplication.translate("MainWindow", u"Button", None))
        self.textBrowser_status.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Microsoft YaHei UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:'Segoe UI';\">SYSTEM STATUS AREA (\u52a8\u6001\u6587\u5b57\u6846)</span></p></body></html>", None))
        self.textBrowser_log.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Microsoft YaHei UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:'Segoe UI';\">SYSTEM LOG AREA</span></p></body></html>", None))
        self.activate_screen_1.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u6d3b\u5c4f\u5e55", None))
        self.activate_2nd_lang_1.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u6d3b\u7b2c\u4e8c\u8bed\u8a00", None))
        self.hideCharname_1.setText(QCoreApplication.translate("MainWindow", u"\u9690\u85cf\u89d2\u8272\u540d", None))
        self.screen_AsignTo_1.setText(QCoreApplication.translate("MainWindow", u"\u6b64\u5c4f\u5e55\u5206\u914d\u7ed9:", None))
        self.pushButton_showscreen_1.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793a\u5c4f\u5e55", None))
        self.label_lang_1_1.setText(QCoreApplication.translate("MainWindow", u"\u8bed\u8a00", None))
        self.checkBox_audio_source_1_1.setText(QCoreApplication.translate("MainWindow", u"\u97f3\u9891\u6e90", None))
        self.label_font_1_1.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53:", None))
        self.label_size_1_1.setText(QCoreApplication.translate("MainWindow", u"\u5c3a\u5bf8", None))
        self.label_font_color.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53\u989c\u8272", None))
        self.label_bg_color_1_1.setText(QCoreApplication.translate("MainWindow", u"\u80cc\u666f\u989c\u8272", None))
        self.label_position_1_1.setText(QCoreApplication.translate("MainWindow", u"\u4f4d\u7f6e\u5fae\u8c03", None))
        self.toolButton_up_1_1.setText(QCoreApplication.translate("MainWindow", u"\u25b2", None))
        self.toolButton_left_1_1.setText(QCoreApplication.translate("MainWindow", u"\u25c4", None))
        self.toolButton_center_1_1.setText(QCoreApplication.translate("MainWindow", u"B", None))
        self.toolButton_right_1_1.setText(QCoreApplication.translate("MainWindow", u"\u25ba", None))
        self.toolButton_down_1_1.setText(QCoreApplication.translate("MainWindow", u"\u25bc", None))
        self.lang_subtabs_1.setTabText(self.lang_subtabs_1.indexOf(self.sub_lang_1_1), QCoreApplication.translate("MainWindow", u"\u8bed\u8a001", None))
        self.label_lang_1_2.setText(QCoreApplication.translate("MainWindow", u"\u8bed\u8a00", None))
        self.checkBox_audio_source_1_2.setText(QCoreApplication.translate("MainWindow", u"\u97f3\u9891\u6e90", None))
        self.label_font_1_2.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53:", None))
        self.label_size_1_2.setText(QCoreApplication.translate("MainWindow", u"\u5c3a\u5bf8", None))
        self.label_font_color_1_2.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53\u989c\u8272", None))
        self.label_bg_color_1_2.setText(QCoreApplication.translate("MainWindow", u"\u80cc\u666f\u989c\u8272", None))
        self.label_position_1_2.setText(QCoreApplication.translate("MainWindow", u"\u4f4d\u7f6e\u5fae\u8c03", None))
        self.toolButton_up_2.setText(QCoreApplication.translate("MainWindow", u"\u25b2", None))
        self.toolButton_left_1_2.setText(QCoreApplication.translate("MainWindow", u"\u25c4", None))
        self.toolButton_center_1_2.setText(QCoreApplication.translate("MainWindow", u"B", None))
        self.toolButton_right_1_2.setText(QCoreApplication.translate("MainWindow", u"\u25ba", None))
        self.toolButton_down_1_2.setText(QCoreApplication.translate("MainWindow", u"\u25bc", None))
        self.lang_subtabs_1.setTabText(self.lang_subtabs_1.indexOf(self.sub_lang_1_2), QCoreApplication.translate("MainWindow", u"\u8bed\u8a002", None))
        self.screen_tabs.setTabText(self.screen_tabs.indexOf(self.screen_1), QCoreApplication.translate("MainWindow", u"\u5c4f\u5e551", None))
        self.activate_screen_1.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u6d3b\u5c4f\u5e55", None))
        self.activate_2nd_lang_1.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u6d3b\u7b2c\u4e8c\u8bed\u8a00", None))
        self.hideCharname_1.setText(QCoreApplication.translate("MainWindow", u"\u9690\u85cf\u89d2\u8272\u540d", None))
        self.screen_AsignTo_1.setText(QCoreApplication.translate("MainWindow", u"\u6b64\u5c4f\u5e55\u5206\u914d\u7ed9:", None))
        self.pushButton_showscreen_1.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793a\u5c4f\u5e55", None))
        self.activate_screen_2.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u6d3b\u5c4f\u5e55", None))
        self.activate_2nd_lang_2.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u6d3b\u7b2c\u4e8c\u8bed\u8a00", None))
        self.hideCharname_2.setText(QCoreApplication.translate("MainWindow", u"\u9690\u85cf\u89d2\u8272\u540d", None))
        self.screen_AsignTo_2.setText(QCoreApplication.translate("MainWindow", u"\u6b64\u5c4f\u5e55\u5206\u914d\u7ed9:", None))
        self.pushButton_showscreen_2.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793a\u5c4f\u5e55", None))
        self.label_lang_2_1.setText(QCoreApplication.translate("MainWindow", u"\u8bed\u8a00", None))
        self.checkBox_subtab_2_1.setText(QCoreApplication.translate("MainWindow", u"Check Box", None))
        self.label_font_2_1.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53:", None))
        self.label_size_2_1.setText(QCoreApplication.translate("MainWindow", u"\u5c3a\u5bf8", None))
        self.label_font_color_2_1.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53\u989c\u8272", None))
        self.label_bg_color_2_1.setText(QCoreApplication.translate("MainWindow", u"\u80cc\u666f\u989c\u8272", None))
        self.label_position_2_1.setText(QCoreApplication.translate("MainWindow", u"\u4f4d\u7f6e\u5fae\u8c03", None))
        self.toolButton_up_2_1.setText(QCoreApplication.translate("MainWindow", u"\u25b2", None))
        self.toolButton_left_2_1.setText(QCoreApplication.translate("MainWindow", u"\u25c4", None))
        self.toolButton_center_2_1.setText(QCoreApplication.translate("MainWindow", u"B", None))
        self.toolButton_right_2_1.setText(QCoreApplication.translate("MainWindow", u"\u25ba", None))
        self.toolButton_down_2_1.setText(QCoreApplication.translate("MainWindow", u"\u25bc", None))
        self.lang_subtabs_2.setTabText(self.lang_subtabs_2.indexOf(self.sub_lang_2_1), QCoreApplication.translate("MainWindow", u"\u8bed\u8a001", None))
        self.label_lang_2_2.setText(QCoreApplication.translate("MainWindow", u"\u8bed\u8a00", None))
        self.checkBox_subtab_2_2.setText(QCoreApplication.translate("MainWindow", u"Check Box", None))
        self.label_font_2_2.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53:", None))
        self.label_size_2_2.setText(QCoreApplication.translate("MainWindow", u"\u5c3a\u5bf8", None))
        self.label_font_color_2_2.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53\u989c\u8272", None))
        self.label_bg_color_2_2.setText(QCoreApplication.translate("MainWindow", u"\u80cc\u666f\u989c\u8272", None))
        self.label_position_2_2.setText(QCoreApplication.translate("MainWindow", u"\u4f4d\u7f6e\u5fae\u8c03", None))
        self.toolButton_up_2_2.setText(QCoreApplication.translate("MainWindow", u"\u25b2", None))
        self.toolButton_left_2_2.setText(QCoreApplication.translate("MainWindow", u"\u25c4", None))
        self.toolButton_center_2_2.setText(QCoreApplication.translate("MainWindow", u"B", None))
        self.toolButton_right_2_2.setText(QCoreApplication.translate("MainWindow", u"\u25ba", None))
        self.toolButton_down_2_2.setText(QCoreApplication.translate("MainWindow", u"\u25bc", None))
        self.lang_subtabs_2.setTabText(self.lang_subtabs_2.indexOf(self.sub_lang_2_2), QCoreApplication.translate("MainWindow", u"\u8bed\u8a002", None))
        self.screen_tabs.setTabText(self.screen_tabs.indexOf(self.screen_2), QCoreApplication.translate("MainWindow", u"\u5c4f\u5e552", None))
        self.activate_screen_3.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u6d3b\u5c4f\u5e55", None))
        self.activate_2nd_lang_3.setText(QCoreApplication.translate("MainWindow", u"\u6fc0\u6d3b\u7b2c\u4e8c\u8bed\u8a00", None))
        self.hideCharname_3.setText(QCoreApplication.translate("MainWindow", u"\u9690\u85cf\u89d2\u8272\u540d", None))
        self.label_tab3_assign.setText(QCoreApplication.translate("MainWindow", u"\u6b64\u5c4f\u5e55\u5206\u914d\u7ed9:", None))
        self.comboBox_screen_assign_3.setCurrentText("")
        self.pushButton_showscreen_3.setText(QCoreApplication.translate("MainWindow", u"\u663e\u793a\u5c4f\u5e55", None))
        self.label_lang_3_1.setText(QCoreApplication.translate("MainWindow", u"\u8bed\u8a00", None))
        self.checkBox_subtab_3_1.setText(QCoreApplication.translate("MainWindow", u"Check Box", None))
        self.label_font_3_1.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53:", None))
        self.label_size_3_1.setText(QCoreApplication.translate("MainWindow", u"\u5c3a\u5bf8", None))
        self.label_font_color_3_1.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53\u989c\u8272", None))
        self.label_bg_color_3_1.setText(QCoreApplication.translate("MainWindow", u"\u80cc\u666f\u989c\u8272", None))
        self.label_position_3_1.setText(QCoreApplication.translate("MainWindow", u"\u4f4d\u7f6e\u5fae\u8c03", None))
        self.toolButton_up_3_1.setText(QCoreApplication.translate("MainWindow", u"\u25b2", None))
        self.toolButton_left_3_1.setText(QCoreApplication.translate("MainWindow", u"\u25c4", None))
        self.toolButton_center_3_1.setText(QCoreApplication.translate("MainWindow", u"B", None))
        self.toolButton_right_3_1.setText(QCoreApplication.translate("MainWindow", u"\u25ba", None))
        self.toolButton_down_3_1.setText(QCoreApplication.translate("MainWindow", u"\u25bc", None))
        self.lang_subtabs_3.setTabText(self.lang_subtabs_3.indexOf(self.sub_lang_3_1), QCoreApplication.translate("MainWindow", u"\u8bed\u8a001", None))
        self.label_lang_3_2.setText(QCoreApplication.translate("MainWindow", u"\u8bed\u8a00", None))
        self.checkBox_subtab_3_2.setText(QCoreApplication.translate("MainWindow", u"Check Box", None))
        self.label_font_3_2.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53:", None))
        self.label_size_3_2.setText(QCoreApplication.translate("MainWindow", u"\u5c3a\u5bf8", None))
        self.label_font_color_3_2.setText(QCoreApplication.translate("MainWindow", u"\u5b57\u4f53\u989c\u8272", None))
        self.label_bg_color_3_2.setText(QCoreApplication.translate("MainWindow", u"\u80cc\u666f\u989c\u8272", None))
        self.label_position_3_2.setText(QCoreApplication.translate("MainWindow", u"\u4f4d\u7f6e\u5fae\u8c03", None))
        self.toolButton_up_3_2.setText(QCoreApplication.translate("MainWindow", u"\u25b2", None))
        self.toolButton_left_3_2.setText(QCoreApplication.translate("MainWindow", u"\u25c4", None))
        self.toolButton_center_3_2.setText(QCoreApplication.translate("MainWindow", u"B", None))
        self.toolButton_right_3_2.setText(QCoreApplication.translate("MainWindow", u"\u25ba", None))
        self.toolButton_down_3_2.setText(QCoreApplication.translate("MainWindow", u"\u25bc", None))
        self.lang_subtabs_3.setTabText(self.lang_subtabs_3.indexOf(self.sub_lang_3_2), QCoreApplication.translate("MainWindow", u"\u8bed\u8a002", None))
        self.screen_tabs.setTabText(self.screen_tabs.indexOf(self.screen_3), QCoreApplication.translate("MainWindow", u"\u5c4f\u5e553", None))
    # retranslateUi

