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

class PluginDialog(QDialog):

    def __init__(self, parent=None, name="Plugin"):
        QDialog.__init__(self, parent)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Help|QDialogButtonBox.Apply|QDialogButtonBox.Close)
        applyButton = buttonBox.button(QDialogButtonBox.Apply)
        helpButton = buttonBox.button(QDialogButtonBox.Help)
        self.connect(applyButton, SIGNAL("clicked()"), self.apply)
        self.connect(helpButton, SIGNAL("clicked()"), self.help)
        self.connect(buttonBox, SIGNAL("rejected()"), self.reject)
        self.params = {}
        self.treeView = None

        self.contentsWidget = ListWidget()
        self.setWindowIcon(QIcon(":icon"))
        self.contentsWidget.setViewMode(QListView.IconMode)
        self.contentsWidget.setIconSize(QSize(76, 66))
        self.contentsWidget.setMovement(QListView.Static)
        self.contentsWidget.setFixedWidth(106)
        self.contentsWidget.setSpacing(12)
        self.contentsWidget.setVisible(False)

        self.connect(self.contentsWidget,
            SIGNAL("currentItemChanged(QListWidgetItem*, QListWidgetItem*)"),
            self.changePage)

        self.pagesWidget = StackedWidget()
        #self.mainPage = Widget()
        #self.mainPage.setLayout(VBoxLayout())
        #self.pagesWidget.addWidget(self.mainPage)

        #self.createIcons()
        self.contentsWidget.setCurrentRow(0)

        horizontalLayout = HBoxLayout()
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
        
    def help(self):
        self.emit(SIGNAL("helpRequested()"))

    def parameters(self):
        return self.params

    def show(self):
        self.widgets = self.widgetsList()
        QDialog.show(self)

    def widgetsList(self):
        widgets = []
        pages = self.pagesWidget.children()
        pages.reverse()
        for child in pages:
            for widget in child.children():
                if issubclass(type(widget), QWidget):
                    try:
                        widgets.append(widget)
                    except Exception, err:
                        pass
        return widgets

    def addWidget(self, widget, page="Main"):
        items = self.contentsWidget.findItems(page,Qt.MatchExactly)
        if len(items) > 0:
            item = self.contentsWidget.row(items[0])
            item = self.pagesWidget.widget(item)
        else:
            item = self.addPage(page)
        if type(widget) in (VariableLineBox, VariableListBox, ModelBuilderBox):
            if self.treeView:
                widget.parent = self.treeView
                self.treeView.addWidget(widget)
            else:
                self.treeView = VariableTreeBox(-1)
                item.layout().addWidget(self.treeView)
                widget.parent = self.treeView
                self.treeView.addWidget(widget)
        else:
            item.layout().addWidget(widget)
        if self.pagesWidget.count() > 1:
            self.contentsWidget.setVisible(True)

    def addPage(self, name="Main"):
        page = Widget()
        page.setLayout(VBoxLayout())
        self.pagesWidget.insertWidget(0, page)
        self.addIcon(name)
        return page

    def addIcon(self, page="Main"):
        button = QListWidgetItem()
        if page == "Main":
            button.setIcon(QIcon(":preferences-system.svg"))
            button.setText("Main")
        elif page == "Configure":
            button.setIcon(QIcon(":preferences-desktop.svg"))
            button.setText("Configure")
        elif page == "PlotOptions":
            button.setIcon(QIcon(":applications-graphics.svg"))
            button.setText("Plot Options")
        else:
            button.setIcon(QIcon(":preferences-desktop.svg"))
            button.setText(page)
        button.setTextAlignment(Qt.AlignHCenter)
        button.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.contentsWidget.insertItem(0,button)

    def changePage(self, current, previous):
        if not current:
            current = previous
        self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))

    def apply(self):
        params = {}
        for widget in self.widgets:
                try:
                    params.update(widget.parameterValues())
                except Exception, err:
                    QMessageBox.warning(self, "manageR Plugin Error", str(err))
                    return
        self.params = params
        print self.params
        self.emit(SIGNAL("pluginOutput(PyQt_PyObject)"), self.params)

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

class ComboBox(QWidget):
    def __init__(self, id, text, **kwargs):
        QWidget.__init__(self)
        self.id = id
        self.widget = QComboBox(**kwargs)
        label = QLabel(text)
        hbox = HBoxLayout()
        hbox.addWidget(label)
        hbox.addStretch(1)
        hbox.addWidget(self.widget, alignment=Qt.AlignRight)
        self.setLayout(hbox)

    def parameterValues(self):
        return {self.id:self.widget.currentText()}

class SpinBox(QWidget):
    def __init__(self, id, text, **kwargs):
        QWidget.__init__(self)
        self.id = id
        self.widget = QSpinBox(**kwargs)
        label = QLabel(text)
        hbox = HBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.widget)
        self.setLayout(hbox)

    def parameterValues(self):
        return {self.id:self.widget.value()}

class CheckBox(QCheckBox):
    def __init__(self, id, text, **kwargs):
        QCheckBox.__init__(self)
        self.id = id
        self.setText(text)

    def parameterValues(self):
        if self.isChecked():
            value = "TRUE"
        else:
            value = "FALSE"
        return {self.id:value}

class DoubleSpinBox(QWidget):
    def __init__(self, id, text, **kwargs):
        QWidget.__init__(self)
        self.id = id
        self.widget = QDoubleSpinBox(**kwargs)
        label = QLabel(text)
        hbox = HBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.widget)
        self.setLayout(hbox)
        self.widget.setMaximum(999999999)
        self.widget.setMinimum(-999999999)

    def parameterValues(self):
        return {self.id:self.widget.value()}

class LineEdit(QWidget):
    def __init__(self, id, text, **kwargs):
        QWidget.__init__(self, **kwargs)
        self.id = id
        self.widget = QLineEdit(**kwargs)
        label = QLabel(text)
        hbox = HBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.widget)
        self.setLayout(hbox)

    def parameterValues(self):
        return {self.id:self.widget.text()}

class HBoxLayout(QHBoxLayout):
    def __init__(self, *args, **kwargs):
        QHBoxLayout.__init__(self, *args, **kwargs)

    def parameterValues(self):
        return None

class VBoxLayout(QVBoxLayout):
    def __init__(self, *args, **kwargs):
        QVBoxLayout.__init__(self, *args, **kwargs)

    def parameterValues(self):
        return None

class GridLayout(QGridLayout):
    def __init__(self, *args, **kwargs):
        QGridLayout.__init__(self, *args, **kwargs)

    def parameterValues(self):
        return None

class ListWidget(QListWidget):
    def __init__(self, *args, **kwargs):
        QListWidget.__init__(self, *args, **kwargs)

    def parameterValues(self):
        return None

class StackedWidget(QStackedWidget):
    def __init__(self, *args, **kwargs):
        QStackedWidget.__init__(self, *args, **kwargs)

    def parameterValues(self):
        return None
    
class Widget(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

    def parameterValues(self):
        return None

class VariableTreeBox(QGroupBox):

    class VariableTreeButton(QToolButton):
        def __init__(self, *args, **kwargs):
            QToolButton.__init__(self, *args, **kwargs)
            baseIcon = QIcon(":go-next.svg")
            secondIcon = QIcon(":go-previous.svg")
            self.__icons__ = [baseIcon, secondIcon]
            self.setIcon(baseIcon)
            
        def switchIcon(self):
            self.__icons__.reverse()
            self.setIcon(self.__icons__[0])
            
    def __init__(self, id, model=None):
        QGroupBox.__init__(self)
        if model is None:
            model = TreeModel()
        self.setTitle("Choose Variables")
        self.setToolTip("<p>Select variables for analysis</p>")
        self.id = id
        self.pairs = {}

        layout = HBoxLayout()
        self.variableTreeView = QTreeView()
        self.variableTreeView.setModel(model)
        self.variableTreeView.setToolTip("Select variables from here")
        self.variableTreeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.variableTreeView.installEventFilter(self)
        layout.addWidget(self.variableTreeView)
        self.widgetsLayout = VBoxLayout()
        layout.addLayout(self.widgetsLayout)
        self.setLayout(layout)
        
    def addWidget(self, widget):
        hbox = HBoxLayout()
        button = self.VariableTreeButton()
        button.setToolTip("Specify variable")
        self.connect(button, SIGNAL("clicked()"), self.move)
        widget.widget.installEventFilter(self)
        hbox.addWidget(button)
        hbox.addWidget(widget)
        self.widgetsLayout.addLayout(hbox)
        self.widgetsLayout.addStretch()
        self.pairs[button] = widget

    def eventFilter(self, object, event):
        if event.type() == QEvent.FocusIn:
            self.switchButton(object)
        return False

    def move(self):
        sender = self.sender()
        receiver = self.pairs[sender]
        path = QString()
        if isinstance(receiver, VariableLineBox):
            if receiver.widget.text().isEmpty():
                indexes = self.variableTreeView.selectedIndexes()
                if len(indexes) < 1:
                    return
                path = self.variableTreeView.model().parentTree(indexes[0])
            sender.switchIcon()
            receiver.widget.setText(path)
        elif isinstance(receiver, VariableListBox):
            add = self.variableTreeView.hasFocus()
            if add:
                indexes = self.variableTreeView.selectedIndexes()
                paths = [self.variableTreeView.model().parentTree(index) for index in indexes if index.column() == 0]
                receiver.widget.addItems(paths)
            else:
                indexes = receiver.widget.selectedItems()
                for index in indexes:
                    item = receiver.widget.takeItem(receiver.widget.row(index))
                    del item

    def switchButton(self, sender):
        if not isinstance(sender, QLineEdit):
            for key, value in self.pairs.iteritems():
                if value.widget == sender:
                    key.setIcon(QIcon(":go-previous.svg"))
                else:
                    key.setIcon(QIcon(":go-next.svg"))

    def parameterValues(self):
        params = {}
        for button, widget in self.pairs.iteritems():
            params.update(widget.parameterValues())
        return params

class ModelBuilderBox(QWidget):
    def __init__(self, id, parent=None):
        QWidget.__init__(self)
        self.dependent = VariableLineBox(id, "Dependant variable")
        self.independent = VariableListBox(id, "Independant variable(s)")
        parent.addWidget(dependent)
        parent.addWidget(independent)
        self.id = id
        
    def parameterValues(self):
        dep = self.dependent.parameterValues().values()[0]
        ind = self.independent.parameterValues().values()[0].replace(",", " + ")
        params = {self.id:"%s ~%s" % (dep, ind)}
        return params

class VariableLineBox(QWidget):
    def __init__(self, id, text):
        QWidget.__init__(self)
        self.widget = QLineEdit()
        self.widget.setToolTip(text)
        self.widget.setReadOnly(True)
        label = QLabel(text)
        label.setBuddy(self.widget)
        vbox = VBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.widget)
        self.setLayout(vbox)
        self.id = id
        
    def parameterValues(self):
        var = self.widget.text()
        if var.isEmpty():
            raise Exception("Error: Missing input variable")
        params = {self.id:var}
        return params

class VariableListBox(QWidget):
    def __init__(self, id, text, sep=","):
        QWidget.__init__(self)
        self.widget = QListWidget()
        self.widget.setToolTip(text)
        self.widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        label = QLabel(text)
        label.setBuddy(self.widget)
        vbox = VBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.widget)
        self.setLayout(vbox)
        self.id = id
        self.sep = sep
        
    def parameterValues(self):
        self.widget.selectAll()
        items = self.widget.selectedItems()
        first = True
        var = QString()
        for item in items:
            if first:
                var.append(item.text())
                first = False
            else:
                var.append("%s%s" % (self.sep, item.text()))
        if var.isEmpty():
            raise Exception("Error: Insufficient number of input variables")
        params = {self.id:var}
        return params

class AxesBox(QGroupBox):

    def __init__(self, id, logscale=False, style=True):
        QGroupBox.__init__(self)
        self.setTitle("Control Axes")
        self.setToolTip("<p>Control if/how axes are drawn</p>")
        self.xAxisCheckBox = QCheckBox("Show X axis")
        self.xAxisCheckBox.setChecked(True)
        self.yAxisCheckBox = QCheckBox("Show Y axis")
        self.yAxisCheckBox.setChecked(True)
        self.id = id
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
        params = QString()
        try:
            if not self.xAxisCheckBox.isChecked():
                params.append(", xaxt='n'")
            if not self.yAxisCheckBox.isChecked():
                params.append(", yaxt='n'")
        except:
            pass
        try:
            logx = self.xLogCheckBox.isChecked()
            logy = self.yLogCheckBox.isChecked()
            if logx or logy:
                tmp = QString()
                if logx:
                    tmp.append("x")
                if logy:
                    tmp.append("y")
                params.append(", log='%s'" % tmp)
        except:
            pass
        try:
            direction = self.directionComboBox.currentIndex()
            if direction > 0:
                params.append(", las=%s" % str(direction))
        except:
            pass
        return {self.id:params}

class MinMaxBox(QGroupBox):

    def __init__(self, id):
        QGroupBox.__init__(self)
        self.id = id
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
        params = QString()
        if self.isChecked():
            xlim1 = self.xMinLineEdit.text()
            xlim2 = self.xMaxLineEdit.text()
            ylim1 = self.yMinLineEdit.text()
            ylim2 = self.yMaxLineEdit.text()
            if (not xlim1.isEmpty() == xlim2.isEmpty()) or \
               (not ylim1.isEmpty() == ylim2.isEmpty()):
                raise Exception("Error: Both min and max values must be specified")
            if not xlim1.isEmpty(): # if one isn't empty, then neither are
                params.append(", xlim=c(%s,%s)" % (xlim1, xlim2))
            if not ylim1.isEmpty(): # if one isn't empty, then neither are
                params.append(", ylim=c(%s,%s)" % (ylim1, ylim2))
        return {self.id:params}

class GridCheckBox(QCheckBox):

    def __init__(self, id):
        QCheckBox.__init__(self)
        self.setText("Add grid to plot")
        self.setToolTip("<p>Check to add grid to plot</p>")
        self.id = id

    def parameterValues(self):
        text = QString()
        if self.isChecked():
            text = "grid()"
        return {self.id:text}

class VariableComboBox(QGroupBox):

    def __init__(self, id, model=None):
        QGroupBox.__init__(self)
        self.setTitle("Input data")
        self.setToolTip("<p>Select input dataset for plotting</p>")
        self.id = id
        if model is None:
            model = TreeModel()
        self.comboBox = TreeComboBox()
        treeView = QTreeView(self.comboBox)
        treeView.header().hide()

        self.comboBox.setModel(model)
        self.comboBox.setView(treeView)
        treeView.hideColumn(1)
        treeView.hideColumn(2)
        treeView.hideColumn(3)
        treeView.viewport().installEventFilter(self.comboBox)
        label = QLabel("Input data")
        hbox = HBoxLayout()
        hbox.addWidget(self.comboBox)
        self.setLayout(hbox)

    def parameterValues(self):
        return {self.id:self.comboBox.currentText()}

class PlotOptionsWidget(QWidget):

    def __init__(self, id, box=True, titles=True, axes=False,
                 log=False, style=True, minmax=False):
        QWidget.__init__(self)
        vbox = VBoxLayout()
        self.id = id
        if titles:
            vbox.addWidget(TitlesBox(self.id))
        if box:
            vbox.addWidget(BoundingBoxBox(self.id))
        if axes:
            vbox.addWidget(AxesBox(self.id, log, style))
        if minmax:
            vbox.addWidget(MinMaxBox(self.id))
        self.setLayout(vbox)

    def parameterValues(self):
        params = QString()
        for widget in self.children():
            vals = widget.parameterValues()
            if not vals is None:
                params.append(QStringList(vals.values()).join(""))
        return {self.id:params}

class LineStyleBox(QGroupBox):

    def __init__(self, id, text=None):
        QGroupBox.__init__(self)
        self.id = id
        if text is None:
            self.setTitle("Adjust line style")
        else:
            self.setTitle(text)
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
        self.penStyleComboBox.addItem("blank", QPen(Qt.black, 2, Qt.NoPen))
        delegate = LineStyleDelegate(self)
        self.penStyleComboBox.setItemDelegate(delegate)
        hbox.addWidget(self.penStyleComboBox)
#        self.setCheckable(True)
#        self.setChecked(False)
        self.setLayout(hbox)

    def parameterValues(self):
        params = QString()
#        if self.isChecked():
        params = "%s" % str(self.penStyleComboBox.currentText())
        return {self.id:params}

class BoundingBoxBox(QGroupBox):

    def __init__(self, id):
        QGroupBox.__init__(self)
        self.id = id
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
        params = QString()
        if self.isChecked():
            params.append(", bty='%s'" % str(self.buttonNames[
                self.buttonGroup.checkedId()]))
        return {self.id:params}

class PlotTypeBox(QGroupBox):

    def __init__(self, id):
        QGroupBox.__init__(self)
        self.id = id
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
        params = QString()
        if self.isChecked():
            params = "'%s'" % str(self.buttonNames[
                self.buttonGroup.checkedId()])
        return {self.id:params}

class TitlesBox(QGroupBox):

    def __init__(self, id):
        QGroupBox.__init__(self)
        self.id = id
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
        params = QString()
        if self.isChecked():
            params.append(", main='%s'" % self.mainLineEdit.text())
            params.append(", sub='%s'" % self.subLineEdit.text())
            params.append(", xlab='%s'" % self.xlabLineEdit.text())
            params.append(", ylab='%s'" % self.ylabLineEdit.text())
        return {self.id:params}

class ParametersBox(QGroupBox):

    def __init__(self, id):
        QGroupBox.__init__(self)
        self.id = id
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
        params = QString()
        if self.isChecked():
            params = self.parameterLineEdit.text()
        return {self.id:params}

def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    robjects.r.load(".RData")
    window = PluginDialog(None)
    window.addWidget(ModelBuilderBox(0))
    window.addWidget(PlotTypeBox(), "main")
    window.addWidget(PlotOptionsWidget(True, True, True, True, True, True), "plotoptions")
    window.addWidget(CheckBox(id=1, text="Some text goes here"), "configure")
    window.addWidget(CheckBox(id=2, text="Some more text goes here"), "configure")
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
