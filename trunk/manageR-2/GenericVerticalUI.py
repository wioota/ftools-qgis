# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
import rpy2.robjects as robjects

VECTORTYPES = ["SpatialPointsDataFrame",
               "SpatialPolygonsDataFrame", 
               "SpatialLinesDataFrame"]
RASTERTYPES = ["SpatialGridDataFrame",
               "SpatialPixelsDataFrame"]

"""Usage:
from PyQt4 import QtCore, QtGui 
from GenericVerticalUI import GenericVerticalUI
class GenericNewDialog(QtGui.QDialog):
    def __init__(self): 
        QtGui.QDialog.__init__(self) 
        # Set up the user interface from Designer. 
        self.ui = GenericVerticalUI ()
        interface=[["label combobox","comboBox","a;b;c;d","false"   ] , ["label spinbox","doubleSpinBox","10","false"   ] ]
        self.ui.setupUi(self,interface) 
"""


class GenericVerticalUI(object):
    """Generic class of user interface. It sets a vertical list of Labels and Boxes"""
    def newBox(self, ParentClass, parameters, top, labelwidth):
        """Defines a new set of Label and a box that can be a ComboBox, LineEdit, TextEdit or DoubleSpinBox."""
        widgetType=parameters[1]
        #check if there are default values:
        if len(parameters)>2:
            default=parameters[2]
        else:
            default=""
        #setting the right type of widget
        height=26
        name="widget"+str(len(self.widgets)) #combobox counter
        if widgetType=="comboBox":
            self.widgets.append(QtGui.QComboBox(ParentClass))
            self.widgets[-1].addItems(default.split(';'))
        elif widgetType=="spComboBox":
            self.widgets.append(QtGui.QComboBox(ParentClass))
            splist = []
            sptypes = default.split(';')
            splayers = currentRObjects()
            for sptype in sptypes:
                for layer in splayers.keys():
                    if splayers[layer] == sptype:
                        splist.append(layer)
            self.widgets[-1].addItems(splist)
        elif widgetType=="doubleSpinBox":
            self.widgets.append(QtGui.QDoubleSpinBox(ParentClass))
            self.widgets[-1].valueFromText(default)
        elif widgetType=="textEdit":
            self.widgets.append(QtGui.QTextEdit(ParentClass))
            self.widgets[-1].setPlainText(default)
            height=116
            self.top+=90
        else:
            #if unknown assumes lineEdit
            self.widgets.append(QtGui.QLineEdit(ParentClass))
            self.widgets[-1].setText(default)
                
        #draw the Box
        self.widgets[-1].setGeometry(QtCore.QRect(labelwidth+20, top, 300, height))
        self.widgets[-1].setObjectName(name)
        #draw the Label
        name="label"+str(len(self.labels)) #textEdit counter
        self.labels.append(QtGui.QLabel(ParentClass))
        self.labels[-1].setGeometry(QtCore.QRect(10, top+10, labelwidth, 17))
        self.labels[-1].setObjectName(name)
        self.labels[-1].setText(QtGui.QApplication.translate(ParentClass.objectName(), 
        parameters[0], None, QtGui.QApplication.UnicodeUTF8))

    def setupUi(self, ParentClass,itemlist):
        """Sets up all the UI. itemlist must have at least a list of lists containing: 
        [label,widgetType, defaultValues,notNull ]"""
        ParentClass.setObjectName("ParentClass")
        #discover what is the length of the biggest label in chars, and if is there any textEdit
        labelwidth=3
        textedits=0
        #sets widget counters to 0
        self.exists={"spComboBox":0, "comboBox":0, "textEdit":0, 
                     "doubleSpinBox":0, "lineEdit":0,  "label":0}
        for item in itemlist:
            if labelwidth<len(item[0]):
                if item[1]=="textEdit":
                    textedits+=1
                labelwidth=len(item[0])
        labelwidth*=8 #convert to units
        self.widgets=[] #Every widget is going to be stored here.
        self.labels=[] #Every label is going to be stored here.
        self.top=10
        for item in itemlist: #draw a pair of label and box for every item in the list
            self.newBox(ParentClass, item, self.top, labelwidth)
            self.top+=30
        ParentClass.resize(labelwidth+330, self.top+40) #sets window size to fit everyone including the button box
        #drawing the "Ok/Cancel" button
        self.buttonBox = QtGui.QDialogButtonBox(ParentClass)
        self.buttonBox.setGeometry(QtCore.QRect(0, self.top, labelwidth+180, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")        
        #QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), ParentClass.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), ParentClass.reject)
        QtCore.QMetaObject.connectSlotsByName(ParentClass)
        self.retranslateUi(ParentClass)
        
    def retranslateUi(self, ParentClass):
        ParentClass.setWindowTitle(QtGui.QApplication.translate(ParentClass.objectName(), "Generic Vertical User Interface", None, QtGui.QApplication.UnicodeUTF8))
        #self.label.setText(QtGui.QApplication.translate("ParentClass", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))

# This is used whenever we check for sp objects in manageR
def currentRObjects():
    ls_ = robjects.conversion.ri2py(
    robjects.rinterface.globalEnv.get('ls',wantFun=True))
    class_ = robjects.conversion.ri2py(
    robjects.rinterface.globalEnv.get('class',wantFun=True))
    dev_list_ = robjects.conversion.ri2py(
    robjects.rinterface.globalEnv.get('dev.list',wantFun=True))
    getwd_ = robjects.conversion.ri2py(
    robjects.rinterface.globalEnv.get('getwd',wantFun=True))
    layers = {}
    graphics = {}
    for item in ls_():
        check = class_(robjects.r[item])[0]
        layers[unicode(item)] = check
    return layers