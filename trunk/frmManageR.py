# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'frmManageR.ui'
#
# Created: Wed Jul 16 16:12:10 2008
#      by: PyQt4 UI code generator 4.3.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.WindowModal)
        Dialog.resize(QtCore.QSize(QtCore.QRect(0,0,562,573).size()).expandedTo(Dialog.minimumSizeHint()))
        Dialog.setSizeGripEnabled(True)

        self.gridlayout = QtGui.QGridLayout(Dialog)
        self.gridlayout.setObjectName("gridlayout")

        self.txtMain = QtGui.QTextEdit(Dialog)
        self.txtMain.setReadOnly(True)
        self.txtMain.setObjectName("txtMain")
        self.gridlayout.addWidget(self.txtMain,0,0,1,4)

        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName("hboxlayout")

        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setObjectName("hboxlayout1")

        self.inputArrow = QtGui.QLabel(Dialog)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.inputArrow.sizePolicy().hasHeightForWidth())
        self.inputArrow.setSizePolicy(sizePolicy)
        self.inputArrow.setObjectName("inputArrow")
        self.hboxlayout1.addWidget(self.inputArrow)

        self.txtInput = QtGui.QLineEdit(Dialog)
        self.txtInput.setObjectName("txtInput")
        self.hboxlayout1.addWidget(self.txtInput)
        self.hboxlayout.addLayout(self.hboxlayout1)

        self.btnMulti = QtGui.QToolButton(Dialog)
        self.btnMulti.setObjectName("btnMulti")
        self.hboxlayout.addWidget(self.btnMulti)
        self.gridlayout.addLayout(self.hboxlayout,1,0,1,4)

        self.hboxlayout2 = QtGui.QHBoxLayout()
        self.hboxlayout2.setObjectName("hboxlayout2")

        self.hboxlayout3 = QtGui.QHBoxLayout()
        self.hboxlayout3.setObjectName("hboxlayout3")

        self.multiArrow = QtGui.QLabel(Dialog)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.multiArrow.sizePolicy().hasHeightForWidth())
        self.multiArrow.setSizePolicy(sizePolicy)
        self.multiArrow.setObjectName("multiArrow")
        self.hboxlayout3.addWidget(self.multiArrow)

        self.txtMulti = QtGui.QTextEdit(Dialog)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtMulti.sizePolicy().hasHeightForWidth())
        self.txtMulti.setSizePolicy(sizePolicy)
        self.txtMulti.setObjectName("txtMulti")
        self.hboxlayout3.addWidget(self.txtMulti)
        self.hboxlayout2.addLayout(self.hboxlayout3)

        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setObjectName("vboxlayout")

        self.btnSingle = QtGui.QToolButton(Dialog)
        self.btnSingle.setObjectName("btnSingle")
        self.vboxlayout.addWidget(self.btnSingle)

        self.btnEntered = QtGui.QToolButton(Dialog)
        self.btnEntered.setObjectName("btnEntered")
        self.vboxlayout.addWidget(self.btnEntered)
        self.hboxlayout2.addLayout(self.vboxlayout)
        self.gridlayout.addLayout(self.hboxlayout2,2,0,1,4)

        self.vboxlayout1 = QtGui.QVBoxLayout()
        self.vboxlayout1.setObjectName("vboxlayout1")

        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName("label")
        self.vboxlayout1.addWidget(self.label)

        self.hboxlayout4 = QtGui.QHBoxLayout()
        self.hboxlayout4.setObjectName("hboxlayout4")

        self.inShape = QtGui.QComboBox(Dialog)
        self.inShape.setObjectName("inShape")
        self.hboxlayout4.addWidget(self.inShape)

        self.btnLoad = QtGui.QPushButton(Dialog)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnLoad.sizePolicy().hasHeightForWidth())
        self.btnLoad.setSizePolicy(sizePolicy)
        self.btnLoad.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.btnLoad.setAutoDefault(False)
        self.btnLoad.setObjectName("btnLoad")
        self.hboxlayout4.addWidget(self.btnLoad)

        self.btnData = QtGui.QPushButton(Dialog)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnData.sizePolicy().hasHeightForWidth())
        self.btnData.setSizePolicy(sizePolicy)
        self.btnData.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.btnData.setAutoDefault(False)
        self.btnData.setObjectName("btnData")
        self.hboxlayout4.addWidget(self.btnData)
        self.vboxlayout1.addLayout(self.hboxlayout4)
        self.gridlayout.addLayout(self.vboxlayout1,3,0,1,4)

        self.vboxlayout2 = QtGui.QVBoxLayout()
        self.vboxlayout2.setObjectName("vboxlayout2")

        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.vboxlayout2.addWidget(self.label_3)

        self.hboxlayout5 = QtGui.QHBoxLayout()
        self.hboxlayout5.setObjectName("hboxlayout5")

        self.outShape = QtGui.QComboBox(Dialog)
        self.outShape.setObjectName("outShape")
        self.hboxlayout5.addWidget(self.outShape)

        self.btnSave = QtGui.QPushButton(Dialog)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnSave.sizePolicy().hasHeightForWidth())
        self.btnSave.setSizePolicy(sizePolicy)
        self.btnSave.setObjectName("btnSave")
        self.hboxlayout5.addWidget(self.btnSave)

        self.btnExport = QtGui.QPushButton(Dialog)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnExport.sizePolicy().hasHeightForWidth())
        self.btnExport.setSizePolicy(sizePolicy)
        self.btnExport.setObjectName("btnExport")
        self.hboxlayout5.addWidget(self.btnExport)
        self.vboxlayout2.addLayout(self.hboxlayout5)
        self.gridlayout.addLayout(self.vboxlayout2,4,0,1,4)

        self.chkClear = QtGui.QCheckBox(Dialog)
        self.chkClear.setObjectName("chkClear")
        self.gridlayout.addWidget(self.chkClear,5,0,1,1)

        spacerItem = QtGui.QSpacerItem(261,28,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem,5,1,1,1)

        self.btnAbout = QtGui.QToolButton(Dialog)
        self.btnAbout.setObjectName("btnAbout")
        self.gridlayout.addWidget(self.btnAbout,5,2,1,1)

        self.btnClose = QtGui.QPushButton(Dialog)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnClose.sizePolicy().hasHeightForWidth())
        self.btnClose.setSizePolicy(sizePolicy)
        self.btnClose.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.btnClose.setAutoDefault(False)
        self.btnClose.setObjectName("btnClose")
        self.gridlayout.addWidget(self.btnClose,5,3,1,1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.txtMain,self.btnLoad)
        Dialog.setTabOrder(self.btnLoad,self.btnClose)
        Dialog.setTabOrder(self.btnClose,self.inShape)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "manageR", None, QtGui.QApplication.UnicodeUTF8))
        self.inputArrow.setText(QtGui.QApplication.translate("Dialog", ">", None, QtGui.QApplication.UnicodeUTF8))
        self.btnMulti.setToolTip(QtGui.QApplication.translate("Dialog", "switch to multi-line input", None, QtGui.QApplication.UnicodeUTF8))
        self.btnMulti.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.multiArrow.setText(QtGui.QApplication.translate("Dialog", ">", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSingle.setToolTip(QtGui.QApplication.translate("Dialog", "switch to single-line input", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSingle.setText(QtGui.QApplication.translate("Dialog", "‎...", None, QtGui.QApplication.UnicodeUTF8))
        self.btnEntered.setToolTip(QtGui.QApplication.translate("Dialog", "submit commands", None, QtGui.QApplication.UnicodeUTF8))
        self.btnEntered.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Load layer into R:", None, QtGui.QApplication.UnicodeUTF8))
        self.btnLoad.setToolTip(QtGui.QApplication.translate("Dialog", "load layer into R", None, QtGui.QApplication.UnicodeUTF8))
        self.btnLoad.setText(QtGui.QApplication.translate("Dialog", "Layer", None, QtGui.QApplication.UnicodeUTF8))
        self.btnData.setToolTip(QtGui.QApplication.translate("Dialog", "load vector attributes as data.frame", None, QtGui.QApplication.UnicodeUTF8))
        self.btnData.setText(QtGui.QApplication.translate("Dialog", "Data only", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "Save/export R object:", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSave.setToolTip(QtGui.QApplication.translate("Dialog", "save R layer to file", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSave.setText(QtGui.QApplication.translate("Dialog", "File", None, QtGui.QApplication.UnicodeUTF8))
        self.btnExport.setToolTip(QtGui.QApplication.translate("Dialog", "export R vector layer to map canvas", None, QtGui.QApplication.UnicodeUTF8))
        self.btnExport.setText(QtGui.QApplication.translate("Dialog", "Map canvas", None, QtGui.QApplication.UnicodeUTF8))
        self.chkClear.setText(QtGui.QApplication.translate("Dialog", "Clear R objects on close", None, QtGui.QApplication.UnicodeUTF8))
        self.btnAbout.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.btnClose.setToolTip(QtGui.QApplication.translate("Dialog", "close manageR", None, QtGui.QApplication.UnicodeUTF8))
        self.btnClose.setText(QtGui.QApplication.translate("Dialog", "Close", None, QtGui.QApplication.UnicodeUTF8))

