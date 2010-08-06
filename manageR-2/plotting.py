# -*- coding: utf-8 -*-

from PyQt4.QtCore import (QString, QStringList, SIGNAL, SLOT, QFileInfo,
                          Qt, QVariant, QObject, QModelIndex, QEvent)
from PyQt4.QtGui import (QPixmap, QDialog, QLabel, QIcon, QTabWidget,
                         QToolButton, QAction, QWidget, QShortcut, QKeySequence,
                         QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton,
                         QAbstractItemView, QLineEdit, QGroupBox, QApplication,
                         QTableWidgetItem, QStyleOptionComboBox, QStyle, QPainter,
                         QDialogButtonBox, QTextEdit, QListView,QStackedWidget,
                         QComboBox,QListWidgetItem, QFileDialog, QItemDelegate, 
                         QGridLayout, QButtonGroup, QPen, QLayout, QPalette,
                         QStylePainter, QTreeView, QListWidget)

import rpy2.robjects as robjects
import sys, os, resources
from environment import TreeModel

class LineStyleDelegate(QItemDelegate):

    def __init__(self, parent = None):
        QItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        data = index.model().data(index, Qt.UserRole)
        if data.isValid() and data.toPyObject() is not None:
            data = data.toPyObject()
            painter.save()
            rect = option.rect
            rect.adjust(+5, 0, -5, 0)
            pen = data
            painter.setPen(pen)
            middle = (rect.bottom() + rect.top()) / 2
            painter.drawLine(rect.left(), middle, rect.right(), middle)
            painter.restore()
        else:
            QItemDelegate.paint(self, painter, option, index)
            painter.drawLine(rect.left(), middle, rect.right(), middle)
            painter.restore()

class LineStyleComboBox(QComboBox):
    def __init__(self, parent = None):
        QComboBox.__init__(self, parent)

    def paintEvent(self, e):
        data = self.itemData(self.currentIndex(), Qt.UserRole)
        if data.isValid() and data.toPyObject() is not None:
            data = data.toPyObject()
            p = QStylePainter(self)
            p.setPen(self.palette().color(QPalette.Text))
            opt = QStyleOptionComboBox()
            self.initStyleOption(opt)
            p.drawComplexControl(QStyle.CC_ComboBox, opt)
            painter = QPainter(self)
            painter.save()
            rect = p.style().subElementRect(QStyle.SE_ComboBoxFocusRect, opt, self)
            rect.adjust(+5, 0, -5, 0)
            pen = data
            painter.setPen(pen)
            middle = (rect.bottom() + rect.top()) / 2
            painter.drawLine(rect.left(), middle, rect.right(), middle)
            painter.restore()
        else:
            QComboBox.paintEvent(self, e)

class TreeComboBox(QComboBox):
    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)
        self.skipNextHide = False
        self.setView(QTreeView(self))
        self.view().viewport().installEventFilter(self)

    def eventFilter(self, object, event):
        if (event.type() == QEvent.MouseButtonPress and object == self.view().viewport()):
            mouseEvent = event
            index = self.view().indexAt(mouseEvent.pos())
            if not self.view().visualRect(index).contains(mouseEvent.pos()):
                self.skipNextHide = True
        return False

    def hidePopup(self):
        self.setCurrentIndex(self.view().currentIndex().row())
        if self.skipNextHide:
            self.skipNextHide = False
        else:
            QComboBox.hidePopup(self)

class PlottingDialog(QDialog):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle("manageR - Plotting")
        self.setWindowIcon(QIcon(":icon"))

        vbox = QVBoxLayout()
        #vbox.addWidget(self.createModelBuilderWidget())
        vbox.addWidget(self.createVariableSelectionWidget())
        vbox.addWidget(self.createPlotOptionsWidget(True, True, True, True, True, True))
        self.setLayout(vbox)

    def createPlotOptionsWidget(self, box=True, titles=True, axes=False,
                                log=False, minmax=False, grid=False):
        vbox = QVBoxLayout()
        if titles:
            vbox.addWidget(self.createTitlesWidget())
        if box:
            vbox.addWidget(self.createBoxWidget())
        if axes:
            vbox.addWidget(self.createAxesWidget(log))
        if minmax:
            vbox.addWidget(self.createMinMaxWidget())
        if grid:
            vbox.addWidget(self.createGridWidget())
        widget = QWidget()
        widget.setLayout(vbox)
        return widget

    def eventFilter(self, object, event):
        if event.type() == QEvent.FocusIn:
            if object == self.variableTreeView or \
            object == self.independentList:
                self.switchButton()
        return False

    def createModelBuilderWidget(self, advanced=False, model=None):
        return self.createVariableWidget(advanced, dependent=True, model=model)
        
    def createVariableSelectionWidget(self, model=None):
        return self.createVariableWidget(model=model)

    def createVariableWidget(self, advanced=False, dependent=False, model=None):
        if model is None:
            model = TreeModel()

        layout = QHBoxLayout()
        self.variableTreeView = QTreeView()
        self.variableTreeView.setModel(model)
        #self.variableTreeView.hideColumn(2)
        #self.variableTreeView.hideColumn(3)
        self.variableTreeView.setToolTip("Select model variables from here")
        self.variableTreeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #self.connect(self.variableTreeView, SIGNAL("entered(QModelIndex)"),
            #self.switchButton)
        #self.connect(self.variableTreeView, SIGNAL("activated(QModelIndex)"),
            #self.switchButton)
        self.variableTreeView.installEventFilter(self)
        layout.addWidget(self.variableTreeView)

        box = QVBoxLayout()
        if dependent:
            self.dependentLineEdit = QLineEdit()
            self.dependentLineEdit.setToolTip("Dependent variable")
            self.dependentLineEdit.setReadOnly(True)
            dependentLabel = QLabel("Dependent variable:")
            dependentLabel.setBuddy(self.dependentLineEdit)
            self.dependentButton = QToolButton()
            self.dependentButton.setToolTip("Specify dependent variable")
            self.dependentButton.setIcon(QIcon(":go-next.svg"))
            self.connect(self.dependentButton, SIGNAL("clicked()"), self.moveDependent)
            self.connect(self.dependentLineEdit, SIGNAL("textChanged(QString)"),
                self.switchButton)
            grid = QGridLayout()
            grid.addWidget(dependentLabel, 0,1)
            grid.addWidget(self.dependentLineEdit, 1,1)
            grid.addWidget(self.dependentButton, 1,0)
            box.addLayout(grid)
            independentTitle = QString("Independent variables:")
            independentText = QString("independent")
        else:
            independentTitle = QString("Selected Variables:")
            independentText = QString("selected")
        self.independentList = QListWidget()
        self.independentList.setToolTip("List of %s variables" % independentText)
        self.independentList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.independentList.installEventFilter(self)
        independentLabel = QLabel(independentTitle)
        independentLabel.setBuddy(self.independentList)
        self.independentButton = QToolButton()
        self.independentButton.setToolTip("Specify %s variables" % independentText)
        self.independentButton.setIcon(QIcon(":go-next.svg"))
        self.connect(self.independentButton, SIGNAL("clicked()"), self.moveIndependent)
        grid = QGridLayout()
        grid.addWidget(independentLabel, 0,1)
        grid.addWidget(self.independentList, 1,1)
        grid.addWidget(self.independentButton, 1,0)
        box.addLayout(grid)
        layout.addLayout(box)

        groupBox = QGroupBox("Select variables")
        groupBox.setToolTip("<p>Select variables for analysis</p>")
        groupBox.setLayout(layout)
        return groupBox

    def moveDependent(self):
        path = QString()
        if self.dependentLineEdit.text().isEmpty():
            indexes = self.variableTreeView.selectedIndexes()
            if len(indexes) < 1:
                return
            path = self.variableTreeView.model().parentTree(indexes[0])
        self.dependentLineEdit.setText(path)

    def moveIndependent(self):
        path = QString()
        add = self.variableTreeView.hasFocus()
        if add:
            indexes = self.variableTreeView.selectedIndexes()
            paths = [self.variableTreeView.model().parentTree(index) for index in indexes if index.column() == 0]
            self.independentList.addItems(paths)
        else:
            indexes = self.independentList.selectedItems()
            for index in indexes:
                item = self.independentList.takeItem(self.independentList.row(index))
                del item

    def switchButton(self, item=None):
        if isinstance(item, QString):
            if not item.isEmpty():
                self.dependentButton.setIcon(QIcon(":go-previous.svg"))
            else:
                self.dependentButton.setIcon(QIcon(":go-next.svg"))
        else:
            if self.independentList.hasFocus():
                self.independentButton.setIcon(QIcon(":go-previous.svg"))
            else:
                self.independentButton.setIcon(QIcon(":go-next.svg"))

    def createAxesWidget(self, logscale=False):
        xAxisCheckBox = QCheckBox("Show X axis")
        xAxisCheckBox.setChecked(True)
        yAxisCheckBox = QCheckBox("Show Y axis")
        yAxisCheckBox.setChecked(True)
        hbox = QHBoxLayout()
        hbox.addWidget(xAxisCheckBox)
        hbox.addWidget(yAxisCheckBox)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        if logscale:
            xLogCheckBox = QCheckBox("Logarithmic X axis")
            yLogCheckBox = QCheckBox("Logarithmic Y axis")
            hbox = QHBoxLayout()
            hbox.addWidget(xLogCheckBox)
            hbox.addWidget(yLogCheckBox)
            vbox.addLayout(hbox)
        groupBox = QGroupBox("Control Axes")
        groupBox.setToolTip("<p>Control if/how axes are drawn</p>")
        groupBox.setLayout(vbox)
        return groupBox

    def createMinMaxWidget(self):
        xMinLineEdit = QLineEdit()
        xMinLineEdit.setToolTip("<p>Specify minimum X value "
                                "(leave blank to use default)</p>")
        xMinLabel = QLabel("X Min:")
        xMinLabel.setBuddy(xMinLineEdit)
        xMaxLineEdit = QLineEdit()
        xMaxLineEdit.setToolTip("<p>Specify maximum X value "
                                "(leave blank to use default)</p>")
        xMaxLabel = QLabel("X Max:")
        xMaxLabel.setBuddy(xMaxLineEdit)
        yMinLineEdit = QLineEdit()
        yMinLineEdit.setToolTip("<p>Specify minimum Y value "
                                "(leave blank to use default)</p>")
        yMinLabel = QLabel("Y Min:")
        yMinLabel.setBuddy(yMinLineEdit)
        yMaxLineEdit = QLineEdit()
        yMaxLineEdit.setToolTip("<p>Specify maximum Y value "
                                "(leave blank to use default)</p>")
        yMaxLabel = QLabel("Y Max:")
        yMaxLabel.setBuddy(yMaxLineEdit)
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(xMinLabel)
        hbox.addWidget(xMinLineEdit)
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(xMaxLabel)
        hbox.addWidget(xMaxLineEdit)
        vbox.addLayout(hbox)
        box = QHBoxLayout()
        box.addLayout(vbox)
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(yMinLabel)
        hbox.addWidget(yMinLineEdit)
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(yMaxLabel)
        hbox.addWidget(yMaxLineEdit)
        vbox.addLayout(hbox)
        box.addLayout(vbox)
        groupBox = QGroupBox("Adjust scale (min and max)")
        groupBox.setToolTip("<p>Adjust scale (range) of axes "
                            "(leave unchecked to use defaults)</p>")
        groupBox.setCheckable(True)
        groupBox.setChecked(False)
        groupBox.setLayout(box)
        return groupBox

    def createGridWidget(self):
        gridCheckBox = QCheckBox("Add grid to plot")
        gridCheckBox.setToolTip("<p>Check to add grid to plot</p>")
        return gridCheckBox

    def createComboBoxWidget(self, model=None):
        if model is None:
            model = TreeModel()
        comboBox = TreeComboBox()
        treeView = QTreeView(comboBox)
        treeView.header().hide()
        #treeView.setModel(model)

        comboBox.setModel(model)
        comboBox.setView(treeView)
        treeView.hideColumn(1)
        treeView.hideColumn(2)
        treeView.hideColumn(3)
        treeView.viewport().installEventFilter(comboBox)
        label = QLabel("Input data")
        hbox = QHBoxLayout()
        hbox.addWidget(comboBox)
        groupBox = QGroupBox("Input data")
        groupBox.setToolTip("<p>Select input dataset for plotting</p>")
        groupBox.setLayout(hbox)
        return groupBox

    def createLineWidget(self):
        hbox = QHBoxLayout()
        penStyleComboBox = LineStyleComboBox()
        penStyleComboBox.setToolTip("Choose line style")
        penStyleComboBox.addItem("solid", QPen(Qt.black, 2, Qt.SolidLine))
        penStyleComboBox.addItem("dashed", QPen(Qt.black, 2, Qt.DashLine))
        penStyleComboBox.addItem("dotted", QPen(Qt.black, 2, Qt.DotLine))
        penStyleComboBox.addItem("dotdash", QPen(Qt.black, 2, Qt.DashDotLine))
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        pen.setStyle(Qt.CustomDashLine)
        pen.setDashPattern([5, 2, 5, 2])
        penStyleComboBox.addItem("twodash", pen)
        pen.setDashPattern([3, 2, 5, 2])
        penStyleComboBox.addItem("twodash", pen)
        penStyleComboBox.addItem("None", QPen(Qt.black, 2, Qt.NoPen))
        delegate = LineStyleDelegate(self)
        penStyleComboBox.setItemDelegate(delegate)
        hbox.addWidget(penStyleComboBox)
        groupBox = QGroupBox("Adjust line style")
        groupBox.setToolTip("<p>Adjust line style (leave "
                            "unchecked to use default)</p>")
        groupBox.setCheckable(True)
        groupBox.setChecked(False)
        groupBox.setLayout(hbox)
        return groupBox

    def createBoxWidget(self):
        buttonGroup = QButtonGroup(self)
        hbox = QHBoxLayout()
        id = 0
        button = QToolButton()
        button.setToolTip("Outline")
        button.setIcon(QIcon(":custom-chart-outline.svg"))
        button.setCheckable(True)
        button.setChecked(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("L shape")
        button.setIcon(QIcon(":custom-chart-l-shape.svg"))
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("7 shape")
        button.setIcon(QIcon(":custom-chart-7-shape.svg"))
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("C shape")
        button.setIcon(QIcon(":custom-chart-c-shape.svg"))
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("U shape")
        button.setCheckable(True)
        button.setIcon(QIcon(":custom-chart-u-shape.svg"))
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("] shape")
        button.setIcon(QIcon(":custom-chart-]-shape.svg"))
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("None")
        button.setIcon(QIcon())
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)

        groupBox = QGroupBox("Adjust bounding box")
        groupBox.setToolTip("<p>Adjust plot bounding box (leave "
                            "unchecked to use default)</p>")
        groupBox.setCheckable(True)
        groupBox.setChecked(False)
        groupBox.setLayout(hbox)
        return groupBox

    def createTypeWidget(self):
        buttonGroup = QButtonGroup(self)
        hbox = QHBoxLayout()
        id = 0
        button = QToolButton()
        button.setToolTip("Points")
        button.setIcon(QIcon(":custom-chart-point.svg"))
        button.setCheckable(True)
        button.setChecked(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Lines")
        button.setIcon(QIcon(":custom-chart-line.svg"))
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Both")
        button.setIcon(QIcon(":custom-chart-both.svg"))
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Overplotted")
        button.setIcon(QIcon(":custom-chart-overplotted.svg"))
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Histogram")
        button.setIcon(QIcon(":custom-chart-hist.svg"))
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Stair steps")
        button.setIcon(QIcon(":custom-chart-stairs.svg"))
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("No plotting")
        button.setIcon(QIcon())
        button.setCheckable(True)
        buttonGroup.addButton(button, id)
        hbox.addWidget(button)

        groupBox = QGroupBox("Adjust plot type")
        groupBox.setToolTip("<p>Adjust plot type (leave "
                            "unchecked to use default)</p>")
        groupBox.setCheckable(True)
        groupBox.setChecked(False)
        groupBox.setLayout(hbox)
        return groupBox

    def createTitlesWidget(self):
        gbox = QGridLayout()
        self.mainLineEdit = QLineEdit()
        self.mainLineEdit.setToolTip("<p>Specify text for title above "
                                     "plot (leave blank for no text)</p>")
        label = QLabel("Main title:")
        label.setBuddy(self.mainLineEdit)
        gbox.addWidget(label,0,0)
        gbox.addWidget(self.mainLineEdit,0,1)

        self.subLineEdit = QLineEdit()
        self.subLineEdit.setToolTip("<p>Specify text for title below "
                                     "plot (leave blank for no text)</p>")
        label = QLabel("Sub title:")
        label.setBuddy(self.subLineEdit)
        gbox.addWidget(label,1,0)
        gbox.addWidget(self.subLineEdit,1,1)

        self.xlabLineEdit = QLineEdit()
        self.xlabLineEdit.setToolTip("<p>Specify text for X axis (leave "
                                     "blank for no text)</p>")
        label = QLabel("X label:")
        label.setBuddy(self.xlabLineEdit)
        gbox.addWidget(label,2,0)
        gbox.addWidget(self.xlabLineEdit,2,1)

        self.ylabLineEdit = QLineEdit()
        self.ylabLineEdit.setToolTip("<p>Specify text for Y axis (leave "
                                     "blank for no text)</p>")
        label = QLabel("Y label:")
        label.setBuddy(self.ylabLineEdit)
        gbox.addWidget(label,3,0)
        gbox.addWidget(self.ylabLineEdit,3,1)

        groupBox = QGroupBox("Custom titles and axes")
        groupBox.setToolTip("<p>Specify custom plot titles "
                            "and axis labels (leave unchecked to use defaults</p>")
        groupBox.setCheckable(True)
        groupBox.setChecked(False)
        vbox = QVBoxLayout()
        groupBox.setLayout(gbox)
        return groupBox

    def createParametersWidget(self):
        groupBox = QGroupBox("Additional parameters")
        groupBox.setToolTip("Add/adjust plotting parameters")
        groupBox.setCheckable(True)
        groupBox.setChecked(False)
        hbox = QHBoxLayout()
        parameterLineEdit = QLineEdit()
        parameterLineEdit.setToolTip("<p>Enter additional (comma separated) "
                                      "parameter=value pairs here</p>")
        hbox.addWidget(parameterLineEdit)
        groupBox.setLayout(hbox)
        return groupBox

def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    robjects.r.load("random_graph.RData")
    print robjects.r.ls()
    window = PlottingDialog()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()