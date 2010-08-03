# -*- coding: utf-8 -*-

from PyQt4.QtCore import (QString, QStringList, QUrl, SIGNAL, SLOT, QFileInfo,
                          QEventLoop, Qt, QVariant, QRegExp, QObject, QSize, )
from PyQt4.QtGui import (QPixmap, QDialog, QLabel, QIcon, QTextBrowser, QTabWidget,
                         QToolButton, QAction, QWidget, QShortcut, QKeySequence,
                         QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton,
                         QAbstractItemView, QListWidget, QTableWidget, QTextDocument,
                         QLineEdit, QGroupBox, QApplication, QTableWidgetItem,
                         QDialogButtonBox, QTextEdit, QListView,QStackedWidget,
                         QComboBox,QListWidgetItem, QFileDialog, QLayout, QGridLayout,
                         QButtonGroup, QItemDelegate, QPen, QStylePainter, QPalette,
                         QStyleOptionComboBox, QStyle, QPainter, )
from PyQt4.QtNetwork import QHttp

import rpy2.robjects as robjects
import sys, os, resources

class GroupBox(QGroupBox):

    def __init__(self, text, parent=None):
        QGroupBox.__init__(self, text, parent)
        self.connect(self, SIGNAL("toggled(bool)"), self.toggleFlat)

    def toggleFlat(self, toggled):
        self.setFlat(not toggled)

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


class PlottingDialog(QDialog):

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle("manageR - Plotting")
        self.setWindowIcon(QIcon(":icon"))
        vbox = QVBoxLayout()
        vbox.addWidget(self.createTitleWidget())
        vbox.addWidget(self.createLineChooser())
        vbox.addWidget(self.createBoundingBoxWidget())
        vbox.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(vbox)

    def createLineChooser(self):
        lineCheckBox = QCheckBox("Show line")
        hbox = QHBoxLayout()
        widget = QWidget()
        penStyleComboBox = LineStyleComboBox()
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
        hbox.addWidget(lineCheckBox)
        hbox.addWidget(penStyleComboBox)
        widget.setLayout(hbox)
        return widget

    def createBoundingBoxWidget(self):
        buttonGroup = QButtonGroup(self)
        hbox = QHBoxLayout()
        widget = QWidget()
        id = 0
        self.outlineButton = QToolButton()
        self.outlineButton.setIcon(QIcon(":custom-chart-outline.svg"))
        self.outlineButton.setCheckable(True)
        self.outlineButton.setChecked(True)
        buttonGroup.addButton(self.outlineButton, id)
        hbox.addWidget(self.outlineButton)
        id += 1
        self.lshapeButton = QToolButton()
        self.lshapeButton.setIcon(QIcon(":custom-chart-l-shape.svg"))
        self.lshapeButton.setCheckable(True)
        buttonGroup.addButton(self.lshapeButton, id)
        hbox.addWidget(self.lshapeButton)
        id += 1
        self.sevenshapeButton = QToolButton()
        self.sevenshapeButton.setIcon(QIcon(":custom-chart-7-shape.svg"))
        self.sevenshapeButton.setCheckable(True)
        buttonGroup.addButton(self.sevenshapeButton, id)
        hbox.addWidget(self.sevenshapeButton)
        id += 1
        self.cshapeButton = QToolButton()
        self.cshapeButton.setIcon(QIcon(":custom-chart-c-shape.svg"))
        self.cshapeButton.setCheckable(True)
        buttonGroup.addButton(self.cshapeButton, id)
        hbox.addWidget(self.cshapeButton)
        id += 1
        self.ushapeButton = QToolButton()
        self.ushapeButton.setCheckable(True)
        self.ushapeButton.setIcon(QIcon(":custom-chart-u-shape.svg"))
        buttonGroup.addButton(self.ushapeButton, id)
        hbox.addWidget(self.ushapeButton)
        id += 1
        self.bracketshapeButton = QToolButton()
        self.bracketshapeButton.setIcon(QIcon(":custom-chart-]-shape.svg"))
        self.bracketshapeButton.setCheckable(True)
        buttonGroup.addButton(self.bracketshapeButton, id)
        hbox.addWidget(self.bracketshapeButton)
        widget.setLayout(hbox)
        widget.setVisible(False)

        vbox = QVBoxLayout()
        vbox.addWidget(widget)
        groupBox = GroupBox("Adjust bounding box")
        groupBox.setCheckable(True)
        groupBox.setChecked(False)
        groupBox.setFlat(True)
        groupBox.setLayout(vbox)
        self.connect(groupBox, SIGNAL("toggled(bool)"), widget.setVisible)
        return groupBox

    def createTitleWidget(self):
        titleCheckBox = QCheckBox("Custom titles and axes")
        titleCheckBox.setChecked(False)
        titleGroup = QWidget()
        gbox = QGridLayout()
        self.mainLineEdit = QLineEdit()
        label = QLabel("Main title:")
        label.setBuddy(self.mainLineEdit)
        gbox.addWidget(label,0,0)
        gbox.addWidget(self.mainLineEdit,0,1)

        self.subLineEdit = QLineEdit()
        label = QLabel("Sub title:")
        label.setBuddy(self.subLineEdit)
        gbox.addWidget(label,1,0)
        gbox.addWidget(self.subLineEdit,1,1)

        self.xlabLineEdit = QLineEdit()
        label = QLabel("X label:")
        label.setBuddy(self.xlabLineEdit)
        gbox.addWidget(label,2,0)
        gbox.addWidget(self.xlabLineEdit,2,1)

        self.ylabLineEdit = QLineEdit()
        label = QLabel("Y label:")
        label.setBuddy(self.ylabLineEdit)
        gbox.addWidget(label,3,0)
        gbox.addWidget(self.ylabLineEdit,3,1)

        titleGroup.setLayout(gbox)
        titleGroup.hide()

        groupBox = GroupBox("Custom titles and axes")
        groupBox.setCheckable(True)
        groupBox.setChecked(False)
        groupBox.setFlat(True)
        self.connect(groupBox, SIGNAL("toggled(bool)"), titleGroup.setVisible)
        self.connect(groupBox, SIGNAL("toggled(bool)"), groupBox.toggleFlat)
        vbox = QVBoxLayout()
        #vbox.addWidget(groupBox)
        vbox.addWidget(titleGroup)
        groupBox.setLayout(vbox)
        #vbox.setSizeConstraint(QLayout.SetFixedSize)
        return groupBox



def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    window = PlottingDialog()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()