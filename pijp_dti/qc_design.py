# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pijp-dti.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(900, 589)
        MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        MainWindow.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("background-color: rgb(223, 230, 233);\n"
"")
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_type = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_type.sizePolicy().hasHeightForWidth())
        self.label_type.setSizePolicy(sizePolicy)
        self.label_type.setStyleSheet("color: rgb(0, 184, 148);\n"
"font: 81 13pt \"Open Sans\";")
        self.label_type.setObjectName("label_type")
        self.verticalLayout_3.addWidget(self.label_type, 0, QtCore.Qt.AlignHCenter)
        self.label_code = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_code.sizePolicy().hasHeightForWidth())
        self.label_code.setSizePolicy(sizePolicy)
        self.label_code.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.label_code.setStyleSheet("color: rgb(85, 85, 255);\n"
"font: 81 13pt \"Open Sans\";")
        self.label_code.setAlignment(QtCore.Qt.AlignCenter)
        self.label_code.setObjectName("label_code")
        self.verticalLayout_3.addWidget(self.label_code)
        self.label_status = QtWidgets.QLabel(self.centralwidget)
        self.label_status.setStyleSheet("color: rgb(85, 85, 255);\n"
"font: 81 9pt \"Open Sans\";")
        self.label_status.setText("")
        self.label_status.setObjectName("label_status")
        self.verticalLayout_3.addWidget(self.label_status, 0, QtCore.Qt.AlignHCenter)
        spacerItem1 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout_3.addItem(spacerItem1)
        self.button_open = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_open.sizePolicy().hasHeightForWidth())
        self.button_open.setSizePolicy(sizePolicy)
        self.button_open.setStyleSheet("background-color: rgb(178, 190, 195);\n"
"color: rgb(45, 52, 54);\n"
"font: 81 9pt \"Open Sans\";")
        self.button_open.setAutoRepeat(False)
        self.button_open.setFlat(False)
        self.button_open.setObjectName("button_open")
        self.verticalLayout_3.addWidget(self.button_open)
        spacerItem2 = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout_3.addItem(spacerItem2)
        self.button_skip = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_skip.sizePolicy().hasHeightForWidth())
        self.button_skip.setSizePolicy(sizePolicy)
        self.button_skip.setStyleSheet("background-color: rgb(178, 190, 195);\n"
"color: rgb(45, 52, 54);\n"
"font: 81 9pt \"Open Sans\";")
        self.button_skip.setObjectName("button_skip")
        self.verticalLayout_3.addWidget(self.button_skip)
        self.button_clear = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_clear.sizePolicy().hasHeightForWidth())
        self.button_clear.setSizePolicy(sizePolicy)
        self.button_clear.setStyleSheet("background-color: rgb(178, 190, 195);\n"
"color: rgb(45, 52, 54);\n"
"font: 81 9pt \"Open Sans\";")
        self.button_clear.setObjectName("button_clear")
        self.verticalLayout_3.addWidget(self.button_clear)
        self.button_hide = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_hide.sizePolicy().hasHeightForWidth())
        self.button_hide.setSizePolicy(sizePolicy)
        self.button_hide.setStyleSheet("background-color: rgb(178, 190, 195);\n"
"color: rgb(45, 52, 54);\n"
"font: 81 9pt \"Open Sans\";")
        self.button_hide.setObjectName("button_hide")
        self.verticalLayout_3.addWidget(self.button_hide)
        self.verticalLayout.addLayout(self.verticalLayout_3)
        spacerItem3 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem3)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.slider_opacity = QtWidgets.QSlider(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.slider_opacity.sizePolicy().hasHeightForWidth())
        self.slider_opacity.setSizePolicy(sizePolicy)
        self.slider_opacity.setStyleSheet("QSlider::groove:horizontal {\n"
"border: 1px solid #bbb;\n"
"background: white;\n"
"height: 10px;\n"
"border-radius: 4px;\n"
"}\n"
"\n"
"QSlider::sub-page:horizontal {\n"
"background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,\n"
"    stop: 0 #66e, stop: 1 #bbf);\n"
"background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,\n"
"    stop: 0 #bbf, stop: 1 #55f);\n"
"border: 1px solid #777;\n"
"height: 10px;\n"
"border-radius: 4px;\n"
"}\n"
"\n"
"QSlider::add-page:horizontal {\n"
"background: #fff;\n"
"border: 1px solid #777;\n"
"height: 10px;\n"
"border-radius: 4px;\n"
"}\n"
"\n"
"QSlider::handle:horizontal {\n"
"background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n"
"    stop:0 #eee, stop:1 #ccc);\n"
"border: 1px solid #777;\n"
"width: 13px;\n"
"margin-top: -2px;\n"
"margin-bottom: -2px;\n"
"border-radius: 4px;\n"
"}\n"
"\n"
"QSlider::handle:horizontal:hover {\n"
"background: qlineargradient(x1:0, y1:0, x2:1, y2:1,\n"
"    stop:0 #fff, stop:1 #ddd);\n"
"border: 1px solid #444;\n"
"border-radius: 4px;\n"
"}\n"
"\n"
"QSlider::sub-page:horizontal:disabled {\n"
"background: #bbb;\n"
"border-color: #999;\n"
"}\n"
"\n"
"QSlider::add-page:horizontal:disabled {\n"
"background: #eee;\n"
"border-color: #999;\n"
"}\n"
"\n"
"QSlider::handle:horizontal:disabled {\n"
"background: #eee;\n"
"border: 1px solid #aaa;\n"
"border-radius: 4px;\n"
"}")
        self.slider_opacity.setMaximum(100)
        self.slider_opacity.setSingleStep(20)
        self.slider_opacity.setProperty("value", 50)
        self.slider_opacity.setOrientation(QtCore.Qt.Horizontal)
        self.slider_opacity.setObjectName("slider_opacity")
        self.verticalLayout_2.addWidget(self.slider_opacity)
        self.label_opacity = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_opacity.sizePolicy().hasHeightForWidth())
        self.label_opacity.setSizePolicy(sizePolicy)
        self.label_opacity.setStyleSheet("color: rgb(85, 85, 255);\n"
"font: 81 9pt \"Open Sans\";")
        self.label_opacity.setAlignment(QtCore.Qt.AlignCenter)
        self.label_opacity.setObjectName("label_opacity")
        self.verticalLayout_2.addWidget(self.label_opacity)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        spacerItem4 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem4)
        self.line_comment = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line_comment.sizePolicy().hasHeightForWidth())
        self.line_comment.setSizePolicy(sizePolicy)
        self.line_comment.setStyleSheet("font: 81 9pt \"Open Sans\";")
        self.line_comment.setText("")
        self.line_comment.setObjectName("line_comment")
        self.verticalLayout.addWidget(self.line_comment)
        spacerItem5 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem5)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.button_pass = QtWidgets.QRadioButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_pass.sizePolicy().hasHeightForWidth())
        self.button_pass.setSizePolicy(sizePolicy)
        self.button_pass.setStyleSheet("color: rgb(0, 184, 148);\n"
"font: 81 11pt \"Open Sans\";")
        self.button_pass.setObjectName("button_pass")
        self.verticalLayout_4.addWidget(self.button_pass)
        self.button_edit = QtWidgets.QRadioButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_edit.sizePolicy().hasHeightForWidth())
        self.button_edit.setSizePolicy(sizePolicy)
        self.button_edit.setStyleSheet("color: rgb(85, 85, 255);\n"
"font: 81 11pt \"Open Sans\";")
        self.button_edit.setObjectName("button_edit")
        self.verticalLayout_4.addWidget(self.button_edit)
        self.button_fail = QtWidgets.QRadioButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_fail.sizePolicy().hasHeightForWidth())
        self.button_fail.setSizePolicy(sizePolicy)
        self.button_fail.setStyleSheet("color: rgb(214, 48, 49);\n"
"font: 81 11pt \"Open Sans\";")
        self.button_fail.setObjectName("button_fail")
        self.verticalLayout_4.addWidget(self.button_fail)
        self.verticalLayout.addLayout(self.verticalLayout_4)
        spacerItem6 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem6)
        self.button_submit = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_submit.sizePolicy().hasHeightForWidth())
        self.button_submit.setSizePolicy(sizePolicy)
        self.button_submit.setStyleSheet("background-color: rgb(0, 184, 148);\n"
"color: rgb(255, 255, 255);\n"
"font: 81 11pt \"Open Sans\";")
        self.button_submit.setObjectName("button_submit")
        self.verticalLayout.addWidget(self.button_submit)
        self.label_detect = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_detect.sizePolicy().hasHeightForWidth())
        self.label_detect.setSizePolicy(sizePolicy)
        self.label_detect.setStyleSheet("color: rgb(85, 85, 255);\n"
"font: 81 9pt \"Open Sans\";")
        self.label_detect.setObjectName("label_detect")
        self.verticalLayout.addWidget(self.label_detect, 0, QtCore.Qt.AlignHCenter)
        self.horizontalLayout.addLayout(self.verticalLayout)
        spacerItem7 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem7)
        self.image_frame = QtWidgets.QVBoxLayout()
        self.image_frame.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.image_frame.setObjectName("image_frame")
        self.horizontalLayout.addLayout(self.image_frame)
        spacerItem8 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem8)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "QC Tool"))
        self.label_type.setText(_translate("MainWindow", "QCType"))
        self.label_code.setText(_translate("MainWindow", "ScanCode"))
        self.button_open.setText(_translate("MainWindow", "Open Editor"))
        self.button_skip.setText(_translate("MainWindow", "Skip"))
        self.button_clear.setText(_translate("MainWindow", "Clear Edits"))
        self.button_hide.setText(_translate("MainWindow", "Hide"))
        self.label_opacity.setText(_translate("MainWindow", "Opacity:"))
        self.line_comment.setPlaceholderText(_translate("MainWindow", "Comment"))
        self.button_pass.setText(_translate("MainWindow", "Pass"))
        self.button_edit.setText(_translate("MainWindow", "Edit"))
        self.button_fail.setText(_translate("MainWindow", "Fail"))
        self.button_submit.setText(_translate("MainWindow", "Submit"))
        self.label_detect.setText(_translate("MainWindow", "Detecting edits..."))

