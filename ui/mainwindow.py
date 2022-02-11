# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(839, 545)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.txtUserID = QtWidgets.QLabel(self.groupBox)
        self.txtUserID.setObjectName("txtUserID")
        self.horizontalLayout.addWidget(self.txtUserID)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setContentsMargins(-1, 6, -1, -1)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.txtGlobalName = QtWidgets.QLabel(self.groupBox)
        self.txtGlobalName.setText("")
        self.txtGlobalName.setObjectName("txtGlobalName")
        self.horizontalLayout_5.addWidget(self.txtGlobalName)
        self.verticalLayout_4.addLayout(self.horizontalLayout_5)
        self.cmdLogin = QtWidgets.QPushButton(self.groupBox)
        self.cmdLogin.setObjectName("cmdLogin")
        self.verticalLayout_4.addWidget(self.cmdLogin)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_4 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.cmdEmojis = QtWidgets.QPushButton(self.groupBox_4)
        self.cmdEmojis.setObjectName("cmdEmojis")
        self.verticalLayout_5.addWidget(self.cmdEmojis)
        self.verticalLayout.addWidget(self.groupBox_4)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox_3 = QtWidgets.QGroupBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_6 = QtWidgets.QLabel(self.groupBox_3)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_6.addWidget(self.label_6)
        self.txtFilter = QtWidgets.QTextEdit(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtFilter.sizePolicy().hasHeightForWidth())
        self.txtFilter.setSizePolicy(sizePolicy)
        self.txtFilter.setMinimumSize(QtCore.QSize(0, 30))
        self.txtFilter.setMaximumSize(QtCore.QSize(16777215, 32))
        self.txtFilter.setObjectName("txtFilter")
        self.horizontalLayout_6.addWidget(self.txtFilter)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)
        self.listRooms = QtWidgets.QListView(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listRooms.sizePolicy().hasHeightForWidth())
        self.listRooms.setSizePolicy(sizePolicy)
        self.listRooms.setAlternatingRowColors(True)
        self.listRooms.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.listRooms.setObjectName("listRooms")
        self.verticalLayout_3.addWidget(self.listRooms)
        self.verticalLayout_2.addWidget(self.groupBox_3)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 839, 24))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        self.actionExit.triggered.connect(MainWindow.close) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Bulk Matrix per-room displayname and avatar changer"))
        self.groupBox.setTitle(_translate("MainWindow", "Account:"))
        self.label.setText(_translate("MainWindow", "User ID:"))
        self.txtUserID.setText(_translate("MainWindow", "txtUserID"))
        self.label_5.setText(_translate("MainWindow", "Name:"))
        self.cmdLogin.setText(_translate("MainWindow", "Login as ..."))
        self.groupBox_4.setTitle(_translate("MainWindow", "Tools:"))
        self.cmdEmojis.setText(_translate("MainWindow", "Emojis"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Rooms:"))
        self.label_6.setText(_translate("MainWindow", "Search:"))
        self.txtFilter.setPlaceholderText(_translate("MainWindow", "RegExp filter"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
