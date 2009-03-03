# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'frmVoronoi.ui'
#
# Created: Fri Feb 13 01:11:25 2009
#      by: PyQt4 UI code generator 4.4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(392, 202)
        Dialog.setSizeGripEnabled(True)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label_7 = QtGui.QLabel(Dialog)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 0, 0, 1, 4)
        self.inShape = QtGui.QComboBox(Dialog)
        self.inShape.setObjectName("inShape")
        self.gridLayout.addWidget(self.inShape, 1, 0, 1, 4)
        self.label = QtGui.QLabel(Dialog)
        self.label.setEnabled(False)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 1, 1, 2)
        self.spnBuffer = QtGui.QSpinBox(Dialog)
        self.spnBuffer.setEnabled(False)
        self.spnBuffer.setMinimum(10)
        self.spnBuffer.setMaximum(100)
        self.spnBuffer.setProperty("value", QtCore.QVariant(10))
        self.spnBuffer.setObjectName("spnBuffer")
        self.gridLayout.addWidget(self.spnBuffer, 2, 3, 1, 1)
        self.label_6 = QtGui.QLabel(Dialog)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 3, 0, 1, 4)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setObjectName("hboxlayout")
        self.outShape = QtGui.QLineEdit(Dialog)
        self.outShape.setReadOnly(True)
        self.outShape.setObjectName("outShape")
        self.hboxlayout.addWidget(self.outShape)
        self.outTool = QtGui.QToolButton(Dialog)
        self.outTool.setObjectName("outTool")
        self.hboxlayout.addWidget(self.outTool)
        self.gridLayout.addLayout(self.hboxlayout, 4, 0, 1, 4)
        self.progressBar = QtGui.QProgressBar(Dialog)
        self.progressBar.setProperty("value", QtCore.QVariant(24))
        self.progressBar.setTextVisible(False)
        self.progressBar.setObjectName("progressBar")
        self.gridLayout.addWidget(self.progressBar, 5, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 5, 2, 1, 2)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Create Voronoi Polygons", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("Dialog", "Input point shapefile:", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Surrounding buffer region:", None, QtGui.QApplication.UnicodeUTF8))
        self.spnBuffer.setSuffix(QtGui.QApplication.translate("Dialog", "%", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("Dialog", "Output polygon shapefile:", None, QtGui.QApplication.UnicodeUTF8))
        self.outTool.setText(QtGui.QApplication.translate("Dialog", "Browse", None, QtGui.QApplication.UnicodeUTF8))

