# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/emojieditor.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_EmojiEditor(object):
    def setupUi(self, EmojiEditor):
        EmojiEditor.setObjectName("EmojiEditor")
        EmojiEditor.resize(400, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(EmojiEditor)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.menuBar = QtWidgets.QMenuBar(EmojiEditor)
        self.menuBar.setObjectName("menuBar")
        self.menuFile = QtWidgets.QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        self.verticalLayout.addWidget(self.menuBar)
        self.scrollArea = QtWidgets.QScrollArea(EmojiEditor)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 400, 274))
        self.scrollAreaWidgetContents.setAutoFillBackground(True)
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.actionImport_append = QtWidgets.QAction(EmojiEditor)
        self.actionImport_append.setObjectName("actionImport_append")
        self.actionImport_overwrite = QtWidgets.QAction(EmojiEditor)
        self.actionImport_overwrite.setObjectName("actionImport_overwrite")
        self.actionExport = QtWidgets.QAction(EmojiEditor)
        self.actionExport.setObjectName("actionExport")
        self.actionClose = QtWidgets.QAction(EmojiEditor)
        self.actionClose.setObjectName("actionClose")
        self.menuFile.addAction(self.actionImport_append)
        self.menuFile.addAction(self.actionImport_overwrite)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExport)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionClose)
        self.menuBar.addAction(self.menuFile.menuAction())

        self.retranslateUi(EmojiEditor)
        self.actionClose.triggered.connect(EmojiEditor.accept) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(EmojiEditor)

    def retranslateUi(self, EmojiEditor):
        _translate = QtCore.QCoreApplication.translate
        EmojiEditor.setWindowTitle(_translate("EmojiEditor", "Emoji editor"))
        self.menuFile.setTitle(_translate("EmojiEditor", "File"))
        self.actionImport_append.setText(_translate("EmojiEditor", "Import (append)"))
        self.actionImport_overwrite.setText(_translate("EmojiEditor", "Import (overwrite)"))
        self.actionExport.setText(_translate("EmojiEditor", "Export"))
        self.actionClose.setText(_translate("EmojiEditor", "Close"))
