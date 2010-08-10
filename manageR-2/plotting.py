# -*- coding: utf-8 -*-

from PyQt4.QtCore import (QString, QStringList, SIGNAL, SLOT, QFileInfo,
                          Qt, QVariant, QObject, QModelIndex, QEvent, QSize, )
from PyQt4.QtGui import (QPixmap, QDialog, QLabel, QIcon, QTabWidget,
                         QToolButton, QAction, QWidget, QShortcut, QKeySequence,
                         QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton,
                         QAbstractItemView, QLineEdit, QGroupBox, QApplication,
                         QTableWidgetItem, QStyleOptionComboBox, QStyle, QPainter,
                         QDialogButtonBox, QTextEdit, QListView,QStackedWidget,
                         QComboBox,QListWidgetItem, QFileDialog, QItemDelegate, 
                         QGridLayout, QButtonGroup, QPen, QLayout, QPalette,
                         QStylePainter, QTreeView, QListWidget, QMessageBox,
                         QSpinBox, QDoubleSpinBox)

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

class PluginDialog(QDialog):

    def __init__(self, parent=None, name="Plugin"):
        QDialog.__init__(self, parent)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Apply|QDialogButtonBox.Close)
        applyButton = buttonBox.button(QDialogButtonBox.Apply)
        self.connect(applyButton, SIGNAL("clicked()"), self.apply)
        self.connect(buttonBox, SIGNAL("rejected()"), self.reject)

        self.contentsWidget = ListWidget()
        self.setWindowIcon(QIcon(":icon"))
        self.contentsWidget.setViewMode(QListView.IconMode)
        self.contentsWidget.setIconSize(QSize(76, 66))
        self.contentsWidget.setMovement(QListView.Static)
        self.contentsWidget.setFixedWidth(106)
        self.contentsWidget.setSpacing(12)
        self.contentsWidget.setVisible(False)

        mainButton = QListWidgetItem(self.contentsWidget)
        mainButton.setIcon(QIcon(":preferences-system.svg"))
        mainButton.setText("Input Data")
        mainButton.setTextAlignment(Qt.AlignHCenter)
        mainButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        self.connect(self.contentsWidget,
            SIGNAL("currentItemChanged(QListWidgetItem*, QListWidgetItem*)"),
            self.changePage)

        self.pagesWidget = StackedWidget()
        self.mainPage = QWidget()
        self.mainPage.setLayout(VBoxLayout())
        self.pagesWidget.addWidget(self.mainPage)

        self.configurePage = QWidget()
        self.configurePage.setLayout(VBoxLayout())

        self.plotPage = QWidget()
        self.plotPage.setLayout(VBoxLayout())

        #self.createIcons()
        self.contentsWidget.setCurrentRow(0)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(self.contentsWidget)
        horizontalLayout.addWidget(self.pagesWidget, 1)

        mainLayout = VBoxLayout()
        mainLayout.addLayout(horizontalLayout)
        mainLayout.addStretch(1)
        mainLayout.addSpacing(12)
        mainLayout.addWidget(buttonBox)
        
        self.setLayout(mainLayout)
        self.setWindowIcon(QIcon(":icon"))
        self.setWindowTitle("manageR - %s" % name)

    def addWidget(self, widget, page="main"):
        if page == "configure":
            self.contentsWidget.setVisible(True)
            if self.pagesWidget.indexOf(self.configurePage) < 0:
                self.pagesWidget.addWidget(self.configurePage)
                self.addIcon(page)
            self.configurePage.layout().addWidget(widget)
        elif page == "plotoptions":
            self.contentsWidget.setVisible(True)
            print self.pagesWidget.indexOf(self.plotPage)
            if self.pagesWidget.indexOf(self.plotPage) < 0:
                self.pagesWidget.addWidget(self.plotPage)
                self.addIcon(page)
            if isinstance(widget, PlotOptionsWidget):
                layout = self.plotPage.layout()
                layout.deleteLater()
                QApplication.sendPostedEvents(layout, QEvent.DeferredDelete)
                self.plotPage.setLayout(widget.layout())
            else:
                self.plotPage.layout().addWidget(widget)
        else: # main page
            self.mainPage.layout().addWidget(widget)

    def addIcon(self, page="main"):
        if page == "configure":
            configureButton = QListWidgetItem(self.contentsWidget)
            configureButton.setIcon(QIcon(":preferences-desktop.svg"))
            configureButton.setText("Configure")
            configureButton.setTextAlignment(Qt.AlignHCenter)
            configureButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        elif page == "plotoptions":
            plotButton = QListWidgetItem(self.contentsWidget)
            plotButton.setIcon(QIcon(":applications-graphics.svg"))
            plotButton.setText("Plot Options")
            plotButton.setTextAlignment(Qt.AlignHCenter)
            plotButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def changePage(self, current, previous):
        if not current:
            current = previous
        self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))

    def apply(self):
        text = QString()
        for widget in self.children():
            if not isinstance(widget, QDialogButtonBox):
                try:
                    text.append(widget.parameterValues())
                except Exception, err:
                    QMessageBox.warning(self, "manageR Plugin Error", str(err))
                    return
        QMessageBox.information(self, "Plugin Code", text)

class ComboBox(QComboBox):
    def __init__(self, param, **kwargs):
        QComboBox.__init__(self, **kwargs)
        self.param = QString(param)

    def parameterValues(self):
        text = self.param
        if not text.isEmpty():
            text = QString(", %s=" % text)
        text.append(self.currentText())
        return text

class SpinBox(QSpinBox):
    def __init__(self, param=""):
        QSpinBox.__init__(self)
        self.param = QString(param)

    def parameterValues(self):
        text = self.param
        if not text.isEmpty():
            text = QString(", %s=" % text)
        text.append(self.value())
        return text

class CheckBox(QCheckBox):
    def __init__(self, param, **kwargs):
        QCheckBox.__init__(self, **kwargs)
        self.param = QString(param)

    def parameterValues(self):
        text = self.param
        if self.isChecked():
            value = "TRUE"
        else:
            value = "FALSE"
        if not text.isEmpty():
            text = QString(", %s=" % text)
        text.append(value)
        return text

class DoubleSpinBox(QDoubleSpinBox):
    def __init__(self, param=""):
        QDoubleSpinBox.__init__(self)
        self.param = QString(param)

    def parameterValues(self):
        text = self.param
        if not text.isEmpty():
            text = QString(", %s=" % text)
        text.append(self.value())
        return text

class LineEdit(QLineEdit):
    def __init__(self, param=""):
        QLineEdit.__init__(self)
        self.param = QString(param)

    def parameterValues(self):
        text = self.param
        if not text.isEmpty():
            text = QString(", %s=" % text)
        text.append(self.text())
        return text

class HBoxLayout(QHBoxLayout):
    def __init__(self):
        QHBoxLayout.__init__(self)

    def parameterValues(self):
        return QString()

class VBoxLayout(QVBoxLayout):
    def __init__(self):
        QVBoxLayout.__init__(self)

    def parameterValues(self):
        return QString()

class GridLayout(QGridLayout):
    def __init__(self):
        QGridLayout.__init__(self)

    def parameterValues(self):
        return QString()

class ListWidget(QListWidget):
    def __init__(self):
        QListWidget.__init__(self)

    def parameterValues(self):
        return QString()

class StackedWidget(QStackedWidget):
    def __init__(self):
        QStackedWidget.__init__(self)

    def parameterValues(self):
        return QString()

class ModelBuilderBox(QGroupBox):

    def __init__(self, param="", type="both", model=None):
        # types can be single, multiple, or both
        # default is both
        QGroupBox.__init__(self)
        if model is None:
            model = TreeModel()
        if not type in ("single", "multiple", "both"):
            type = "both"
        self.setTitle("Choose Variables")
        self.setToolTip("<p>Select variables for analysis</p>")
        self.param = param

        layout = HBoxLayout()
        self.variableTreeView = QTreeView()
        self.variableTreeView.setModel(model)
        self.variableTreeView.setToolTip("Select variables from here")
        self.variableTreeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.variableTreeView.installEventFilter(self)
        layout.addWidget(self.variableTreeView)
        box = VBoxLayout()
        self.dependentLineEdit = QLineEdit()
        if type == "single":
            dependentText = "Select variable"
        else:
            dependentText = "Depenent variable"
        self.dependentLineEdit.setToolTip(dependentText)
        self.dependentLineEdit.setReadOnly(True)
        dependentLabel = QLabel("%s:" % dependentText)
        dependentLabel.setBuddy(self.dependentLineEdit)
        self.dependentButton = QToolButton()
        self.dependentButton.setToolTip("Select variable")
        self.dependentButton.setIcon(QIcon(":go-next.svg"))
        self.connect(self.dependentButton, SIGNAL("clicked()"), self.moveDependent)
        self.connect(self.dependentLineEdit, SIGNAL("textChanged(QString)"),
            self.switchButton)
        vbox = VBoxLayout()
        vbox.addWidget(dependentLabel)
        hbox = HBoxLayout()
        hbox.addWidget(self.dependentButton)
        hbox.addWidget(self.dependentLineEdit)
        vbox.addLayout(hbox)
        box.addLayout(vbox)
        if not type in ("single", "both"):
            self.dependentLineEdit.setVisible(False)
            self.dependentButton.setEnabled(False)
            self.dependentButton.setVisible(False)
            self.dependentLabel.setEnabled(False)
            dependentLabel.setVisible(False)
            dependentLabel.setEnabled(False)
        if type == "multiple":
            independentText = "Select variable(s)"
        else:
            independentText = "Independent variable(s)"
        self.independentList = QListWidget()
        self.independentList.setToolTip("List of available variables")
        self.independentList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.independentList.installEventFilter(self)
        independentLabel = QLabel("%s:" % independentText)
        independentLabel.setBuddy(self.independentList)
        self.independentButton = QToolButton()
        self.independentButton.setToolTip("Specify variable(s)")
        self.independentButton.setIcon(QIcon(":go-next.svg"))
        self.connect(self.independentButton, SIGNAL("clicked()"), self.moveIndependent)
        vbox = VBoxLayout()
        vbox.addWidget(independentLabel)
        hbox = HBoxLayout()
        hbox.addWidget(self.independentButton)
        hbox.addWidget(self.independentList)
        vbox.addLayout(hbox)
        box.addLayout(vbox)
        layout.addLayout(box)
        if not type in ("multiple", "both"):
            self.independentList.setEnabled(False)
            self.independentList.setVisible(False)
            self.independentButton.setEnabled(False)
            self.independentButton.setVisible(False)
            independentLabel.setEnabled(False)
            independentLabel.setVisible(False)
        self.setLayout(layout)

    def eventFilter(self, object, event):
        if event.type() == QEvent.FocusIn:
            if object == self.variableTreeView or \
            object == self.independentList:
                self.switchButton()
        return False

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

    def parameterValues(self):
        ind = QString()
        dep = QString()
        visdep = self.dependentLineEdit.isVisible()
        visind = self.independentList.isVisible()
        if visind:
            self.independentList.selectAll()
            items = self.independentList.selectedItems()
            first = True
            for item in items:
                if first:
                    tmp = QString()
                    first = False
                else:
                    tmp = QString("+")
                ind.append(" %s %s" % (tmp, item.text()))
        dep = self.dependentLineEdit.text()
        if (dep.isEmpty() and visdep) or \
           (ind.isEmpty() and visind):
            raise Exception("Error: Insufficient number of input variables")
        if visdep and visind:
            text = QString("formula=%s ~%s" % (dep, ind))
        elif visdep and not visind:
            text = QString("%s=%s" % (self.param, dep))
        elif not visdep and visind:
            text = QString("%s=%s" % (self.param, ind))
        else:
            text = QString() # this shouldn't happen
        return text

class AxesBox(QGroupBox):

    def __init__(self, logscale=False, style=True):
        QGroupBox.__init__(self)
        self.setTitle("Control Axes")
        self.setToolTip("<p>Control if/how axes are drawn</p>")
        self.xAxisCheckBox = QCheckBox("Show X axis")
        self.xAxisCheckBox.setChecked(True)
        self.yAxisCheckBox = QCheckBox("Show Y axis")
        self.yAxisCheckBox.setChecked(True)
        hbox = HBoxLayout()
        hbox.addWidget(self.xAxisCheckBox)
        hbox.addWidget(self.yAxisCheckBox)
        vbox = VBoxLayout()
        vbox.addLayout(hbox)
        if logscale:
            self.xLogCheckBox = QCheckBox("Logarithmic X axis")
            self.yLogCheckBox = QCheckBox("Logarithmic Y axis")
            hbox = HBoxLayout()
            hbox.addWidget(self.xLogCheckBox)
            hbox.addWidget(self.yLogCheckBox)
            vbox.addLayout(hbox)
        if style:
            self.directionComboBox = QComboBox()
            self.directionComboBox.addItems(["Parallel to axis",
                                             "Horizontal",
                                             "Perpendicualr to axis",
                                             "Vertical"])
            directionLabel = QLabel("Axis label style:")
            directionLabel.setBuddy(self.directionComboBox)
            hbox = HBoxLayout()
            hbox.addWidget(directionLabel)
            hbox.addWidget(self.directionComboBox)
            vbox.addLayout(hbox)
        self.setLayout(vbox)

    def parameterValues(self):
        text = QString()
        if not self.xAxisCheckBox.isChecked():
            text.append(", xaxt='n'")
        if not self.yAxisCheckBox.isChecked():
            text.append(", yaxt='n'")
        logx = self.xLogCheckBox.isChecked()
        logy = self.yLogCheckBox.isChecked()
        if logx or logy:
            text.append(", log='")
            if logx:
                text.append("x")
            if logy:
                text.append("y")
            text.append("'")
        direction = self.directionComboBox.currentIndex()
        if direction > 0:
            text.append(", las=%s" % direction)
        return text


class MinMaxBox(QGroupBox):

    def __init__(self, logscale=False):
        QGroupBox.__init__(self)
        self.setTitle("Adjust scale (min and max)")
        self.setToolTip("<p>Adjust scale (range) of axes "
                            "(leave unchecked to use defaults)</p>")
        self.setCheckable(True)
        self.setChecked(False)
        self.xMinLineEdit = QLineEdit()
        self.xMinLineEdit.setToolTip("<p>Specify minimum X value "
                                "(leave blank to use default)</p>")
        xMinLabel = QLabel("X Min:")
        xMinLabel.setBuddy(self.xMinLineEdit)
        self.xMaxLineEdit = QLineEdit()
        self.xMaxLineEdit.setToolTip("<p>Specify maximum X value "
                                "(leave blank to use default)</p>")
        xMaxLabel = QLabel("X Max:")
        xMaxLabel.setBuddy(self.xMaxLineEdit)
        self.yMinLineEdit = QLineEdit()
        self.yMinLineEdit.setToolTip("<p>Specify minimum Y value "
                                "(leave blank to use default)</p>")
        yMinLabel = QLabel("Y Min:")
        yMinLabel.setBuddy(self.yMinLineEdit)
        self.yMaxLineEdit = QLineEdit()
        self.yMaxLineEdit.setToolTip("<p>Specify maximum Y value "
                                "(leave blank to use default)</p>")
        yMaxLabel = QLabel("Y Max:")
        yMaxLabel.setBuddy(self.yMaxLineEdit)
        vbox = VBoxLayout()
        hbox = HBoxLayout()
        hbox.addWidget(xMinLabel)
        hbox.addWidget(self.xMinLineEdit)
        vbox.addLayout(hbox)
        hbox = HBoxLayout()
        hbox.addWidget(xMaxLabel)
        hbox.addWidget(self.xMaxLineEdit)
        vbox.addLayout(hbox)
        box = HBoxLayout()
        box.addLayout(vbox)
        vbox = VBoxLayout()
        hbox = HBoxLayout()
        hbox.addWidget(yMinLabel)
        hbox.addWidget(self.yMinLineEdit)
        vbox.addLayout(hbox)
        hbox = HBoxLayout()
        hbox.addWidget(yMaxLabel)
        hbox.addWidget(self.yMaxLineEdit)
        vbox.addLayout(hbox)
        box.addLayout(vbox)
        self.setLayout(box)

    def parameterValues(self):
        text = QString()
        if self.isChecked():
            xlim1 = self.xMinLineEdit.text()
            xlim2 = self.xMaxLineEdit.text()
            ylim1 = self.yMinLineEdit.text()
            ylim2 = self.yMaxLineEdit.text()
            if (not xlim1.isEmpty() == xlim2.isEmpty()) or \
               (not ylim1.isEmpty() == ylim2.isEmpty()):
                raise Exception("Error: Both min and max values must be specified")
            if not xlim1.isEmpty(): # if one isn't empty, then neither are
                text.append(", xlim=c(%s,%s)" % (xlim1, xlim2))
            if not ylim1.isEmpty(): # if one isn't empty, then neither are
                text.append(", ylim=c(%s,%s)" % (ylim1, ylim2))
        return text

class GridCheckBox(QCheckBox):

    def __init__(self):
        QCheckBox.__init__(self)
        self.setText("Add grid to plot")
        self.setToolTip("<p>Check to add grid to plot</p>")

    def parameterValues(self):
        text = QString()
        if self.isChecked():
            text = "grid()"
        return text

class TreeComboBox(QGroupBox):

    def __init__(self, model=None):
        QGroupBox.__init__(self)
        self.setTitle("Input data")
        self.setToolTip("<p>Select input dataset for plotting</p>")
        if model is None:
            model = TreeModel()
        self.comboBox = TreeComboBox()
        treeView = QTreeView(comboBox)
        treeView.header().hide()

        self.comboBox.setModel(model)
        self.comboBox.setView(treeView)
        treeView.hideColumn(1)
        treeView.hideColumn(2)
        treeView.hideColumn(3)
        treeView.viewport().installEventFilter(comboBox)
        label = QLabel("Input data")
        hbox = HBoxLayout()
        hbox.addWidget(comboBox)
        self.setLayout(hbox)

    def parameterValues(self):
        return self.comboBox.currentText()
        

class PlotOptionsWidget(QWidget):

    def __init__(self, box=True, titles=True, axes=False,
                 log=False, minmax=False, grid=False):
        QWidget.__init__(self)
        vbox = VBoxLayout()
        if titles:
            vbox.addWidget(TitlesBox())
        if box:
            vbox.addWidget(BoundingBoxBox())
        if axes:
            vbox.addWidget(AxesBox(log))
        if minmax:
            vbox.addWidget(MinMaxBox())
        if grid:
            vbox.addWidget(GridCheckBox())
        self.setLayout(vbox)

    def parameterValues(self):
        text = QString()
        for widget in self.children():
            #if not isinstance(widget, QDialogButtonBox) and \
               #not issubclass(type(widget), QLayout):
            text.append(widget.parameterValues())
        return text

class LineStyleBox(QGroupBox):

    def __init__(self, model=None):
        QGroupBox.__init__(self)
        self.setTitle("Adjust line style")
        self.setToolTip("<p>Adjust line style (leave "
                            "unchecked to use default)</p>")
        hbox = HBoxLayout()
        self.penStyleComboBox = LineStyleComboBox()
        self.penStyleComboBox.setToolTip("Choose line style")
        self.penStyleComboBox.addItem("solid", QPen(Qt.black, 2, Qt.SolidLine))
        self.penStyleComboBox.addItem("dashed", QPen(Qt.black, 2, Qt.DashLine))
        self.penStyleComboBox.addItem("dotted", QPen(Qt.black, 2, Qt.DotLine))
        self.penStyleComboBox.addItem("dotdash", QPen(Qt.black, 2, Qt.DashDotLine))
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        pen.setStyle(Qt.CustomDashLine)
        pen.setDashPattern([5, 2, 5, 2])
        self.penStyleComboBox.addItem("twodash", pen)
        pen.setDashPattern([3, 2, 5, 2])
        self.penStyleComboBox.addItem("twodash", pen)
        self.penStyleComboBox.addItem("none", QPen(Qt.black, 2, Qt.NoPen))
        delegate = LineStyleDelegate(self)
        self.penStyleComboBox.setItemDelegate(delegate)
        hbox.addWidget(self.penStyleComboBox)
        self.setCheckable(True)
        self.setChecked(False)
        self.setLayout(hbox)

    def parameterValues(self):
        text = QString()
        if self.isChecked():
            text.append(", lty='%s'" % self.penStyleComboBox.currentText())
        return text

class BoundingBoxBox(QGroupBox):

    def __init__(self, model=None):
        QGroupBox.__init__(self)
        self.setTitle("Adjust bounding box")
        self.setToolTip("<p>Adjust plot bounding box (leave "
                            "unchecked to use default)</p>")
        self.setCheckable(True)
        self.setChecked(False)
        self.buttonGroup = QButtonGroup(self)
        self.buttonNames = []
        hbox = HBoxLayout()
        id = 0
        button = QToolButton()
        button.setToolTip("Outline")
        self.buttonNames.append("o")
        button.setIcon(QIcon(":custom-chart-outline.svg"))
        button.setCheckable(True)
        button.setChecked(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("L shape")
        self.buttonNames.append("l")
        button.setIcon(QIcon(":custom-chart-l-shape.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("7 shape")
        self.buttonNames.append("7")
        button.setIcon(QIcon(":custom-chart-7-shape.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("C shape")
        self.buttonNames.append("c")
        button.setIcon(QIcon(":custom-chart-c-shape.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("U shape")
        self.buttonNames.append("u")
        button.setCheckable(True)
        button.setIcon(QIcon(":custom-chart-u-shape.svg"))
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("] shape")
        self.buttonNames.append("]")
        button.setIcon(QIcon(":custom-chart-]-shape.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("None")
        self.buttonNames.append("n")
        button.setIcon(QIcon())
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)

        self.setLayout(hbox)

    def parameterValues(self):
        text = QString()
        if self.isChecked():
            text.append(", bty='%s'" % self.buttonNames[self.buttonGroup.checkedId()])
        return text

class PlotTypeBox(QGroupBox):

    def __init__(self, model=None):
        QGroupBox.__init__(self)
        self.setTitle("Adjust plot type")
        self.setToolTip("<p>Adjust plot type (leave "
                            "unchecked to use default)</p>")
        self.setCheckable(True)
        self.setChecked(False)
        self.buttonGroup = QButtonGroup(self)
        self.buttonNames = []
        hbox = HBoxLayout()
        id = 0
        button = QToolButton()
        button.setToolTip("Points")
        self.buttonNames.append("p")
        button.setIcon(QIcon(":custom-chart-point.svg"))
        button.setCheckable(True)
        button.setChecked(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Lines")
        self.buttonNames.append("l")
        button.setIcon(QIcon(":custom-chart-line.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Both")
        self.buttonNames.append("b")
        button.setIcon(QIcon(":custom-chart-both.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Overplotted")
        self.buttonNames.append("o")
        button.setIcon(QIcon(":custom-chart-overplotted.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Histogram")
        self.buttonNames.append("h")
        button.setIcon(QIcon(":custom-chart-hist.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Stair steps")
        self.buttonNames.append("s")
        button.setIcon(QIcon(":custom-chart-stairs.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("No plotting")
        self.buttonNames.append("n")
        button.setIcon(QIcon())
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)

        self.setLayout(hbox)

    def parameterValues(self):
        text = QString()
        if self.isChecked():
            text.append(", type='%s'" % self.buttonNames[self.buttonGroup.checkedId()])
        return text

class TitlesBox(QGroupBox):

    def __init__(self, model=None):
        QGroupBox.__init__(self)
        self.setTitle("Custom titles and axis labels")
        self.setToolTip("<p>Specify custom plot titles "
                        "and axis labels (leave unchecked to use defaults</p>")
        self.setCheckable(True)
        self.setChecked(False)
        gbox = GridLayout()
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

        vbox = VBoxLayout()
        self.setLayout(gbox)


    def parameterValues(self):
        text = QString()
        if self.isChecked():
            text.append(", main='%s', sub='%s', xlab='%s', ylab='%s'" %
                (self.mainLineEdit.text(),self.subLineEdit.text(),
                 self.xlabLineEdit.text(),self.ylabLineEdit.text()))
        return text

class ParametersBox(QGroupBox):

    def __init__(self, model=None):
        QGroupBox.__init__(self)
        self.setTitle("Additional parameters")
        self.setToolTip("<p>Add/adjust plotting parameters</p>")
        self.setCheckable(True)
        self.setChecked(False)
        hbox = HBoxLayout()
        self.parameterLineEdit = QLineEdit()
        self.parameterLineEdit.setToolTip("<p>Enter additional (comma separated) "
                                      "parameter=value pairs here</p>")
        hbox.addWidget(parameterLineEdit)
        self.setLayout(hbox)

    def parameterValues(self):
        text = QString()
        if self.isChecked():
            text.append(", %s" % self.parameterLineEdit.text())
        return text

def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    robjects.r.load("random_graph.RData")
    window = PluginDialog(None, "Test")
    window.addWidget(ModelBuilderBox())
    window.addWidget(PlotOptionsWidget(True, True, True, True, True, True), "plotoptions")
    window.addWidget(CheckBox("x", text="Some text goes here"), "configure")
    window.addWidget(CheckBox("Some more text goes here"), "configure")
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()