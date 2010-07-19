# -*- coding: utf-8 -*-

# rpy2 (R) imports
import rpy2.robjects as robjects

#PyQt imports
from PyQt4.QtCore import (Qt, SIGNAL, QStringList, QString, QDir, QSettings )
from PyQt4.QtGui import (QTreeWidget, QAbstractItemView, QAction, QVBoxLayout,
                         QMenu, QWidget, QListView, QIcon, QLineEdit, QToolButton,
                         QHBoxLayout, QTreeWidgetItem, QFileSystemModel, QCheckBox,
                         QTextEdit, QFileDialog, QDialog, QSpinBox, QLabel,
                         QApplication, QCursor, QInputDialog)
# local imports
import resources, os, sys
from environment import browseEnv

class RWidget(QWidget):

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        # initialise standard settings
        self.setMinimumSize(30,30)
        self.parent = parent

    def emitCommands(self, commands):
        if not len(commands) < 1:
            self.emit(SIGNAL("emitCommands(QString)"), commands)

class WorkingDirectoryWidget(RWidget):

    def __init__(self, parent=None, base="."):
        RWidget.__init__(self, parent)
        # initialise standard settings
        self.base = base

        self.currentEdit = QLineEdit(self)
        self.currentEdit.setToolTip("Current working directory")
        self.currentEdit.setWhatsThis("Current working directory")
        self.currentEdit.setText(self.base)

        self.setwdButton = QToolButton(self)
        self.setwdButton.setToolTip("Set working directory")
        self.setwdButton.setWhatsThis("Set working directory")
        self.setwdButton.setIcon(QIcon(":folder.svg"))
        self.setwdButton.setText("setwd")
        self.setwdButton.setAutoRaise(True)

        horiz = QHBoxLayout(self)
        horiz.addWidget(self.currentEdit)
        horiz.addWidget(self.setwdButton)
        self.connect(self.setwdButton, SIGNAL("clicked()"), self.browseToFolder)

    def getWorkingDir(self):
        command = unicode("getwd()")
        directory = robjects.r(command)[0]
        self.currentEdit.setText(directory)
        #self.emitCommands(command)

    def browseToFolder(self):
        directory = QFileDialog.getExistingDirectory(
        self, "Choose working directory",self.currentEdit.text(),
        (QFileDialog.ShowDirsOnly|QFileDialog.DontResolveSymlinks))
        if not directory.isEmpty():
            self.setWorkingDir(directory)
            self.currentEdit.setText(directory)

    def setWorkingDir(self, directory):
        command = unicode("setwd('%s')" % (directory))
        robjects.r(command)
        #self.emitCommands(command)

class ScratchPadWidget(RWidget):

    def __init__(self, parent):
        RWidget.__init__(self, parent)
        textEdit = QTextEdit(self)
        textEdit.setToolTip("Random text goes here")
        hbox = QHBoxLayout(self)
        hbox.addWidget(textEdit)
        self.setFocusProxy(textEdit)


class DirectoryWidget(RWidget):

    def __init__(self, parent, base="."):
        RWidget.__init__(self, parent)
        self.base = base
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.model.setFilter(QDir.AllDirs|QDir.AllEntries|QDir.NoDotAndDotDot)
        #self.proxy = QSortFilterProxyModel(self)
        #self.proxy.setSourceModel(self.model)
        #self.proxy.setDynamicSortFilter(True)
        self.listView = QListView(self)
        self.listView.setModel(self.model)
        self.listView.setRootIndex(self.model.index(QDir.currentPath()))
        self.listView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lineEdit = QLineEdit(self)
        hiddenCheckbox = QCheckBox("Show hidden files", self)
        hiddenCheckbox.setChecked(False)
        #self.filterEdit = QLineEdit(self)
        #self.model.setNameFilters(QStringList(["*.R","*.Rdata",
                                               #"*.Rd","*.RData",
                                               #"*.csv","*.txt"]))
        self.actions = []

        upAction = QAction("&Up", self)
        upAction.setStatusTip("Move to parent directory")
        upAction.setToolTip("Move to parent directory")
        upAction.setIcon(QIcon(":go-up.svg"))
        upAction.setEnabled(True)
        self.actions.append(upAction)
        newAction = QAction("&New Directory", self)
        newAction.setStatusTip("Create new directory")
        newAction.setToolTip("Create new directory")
        newAction.setIcon(QIcon(":folder-new.svg"))
        newAction.setEnabled(True)
        self.actions.append(newAction)
        synchAction = QAction("&Synch", self)
        synchAction.setStatusTip("Synch with current working directory")
        synchAction.setToolTip("Synch with current working directory")
        synchAction.setIcon(QIcon(":go-jump.svg"))
        synchAction.setEnabled(True)
        self.actions.append(synchAction)
        rmAction = QAction("&Delete", self)
        rmAction.setStatusTip("Delete selected item")
        rmAction.setToolTip("delete selected item")
        rmAction.setIcon(QIcon(":edit-delete.svg"))
        rmAction.setEnabled(True)
        self.actions.append(rmAction)
        openAction = QAction("&Open", self)
        openAction.setStatusTip("Open selected R script")
        openAction.setToolTip("Open selected R script")
        openAction.setIcon(QIcon(":document-open.svg"))
        openAction.setEnabled(True)
        self.actions.append(openAction)
        loadAction = QAction("&Load", self)
        loadAction.setStatusTip("Load selected R data")
        loadAction.setToolTip("Load selected R data")
        loadAction.setIcon(QIcon(":document-open.svg"))
        loadAction.setEnabled(True)
        self.actions.append(loadAction)
        self.rootChanged()

        self.connect(newAction, SIGNAL("triggered()"), self.newFolder)
        self.connect(upAction, SIGNAL("triggered()"), self.upFolder)
        self.connect(synchAction, SIGNAL("triggered()"), self.synchFolder)
        self.connect(rmAction, SIGNAL("triggered()"), self.rmItem)
        self.connect(openAction, SIGNAL("triggered()"), self.openItem)
        self.connect(loadAction, SIGNAL("triggered()"), self.loadItem)
        self.connect(hiddenCheckbox, SIGNAL("stateChanged(int)"), self.toggleHidden)
        self.connect(self.listView, SIGNAL("activated(QModelIndex)"), self.cdFolder)
        self.connect(self.listView, SIGNAL("customContextMenuRequested(QPoint)"), self.customContext)
        self.connect(self.lineEdit, SIGNAL("returnPressed()"), self.gotoFolder)

        upButton = QToolButton()
        upButton.setDefaultAction(upAction)
        upButton.setAutoRaise(True)
        newButton = QToolButton()
        newButton.setDefaultAction(newAction)
        newButton.setAutoRaise(True)
        synchButton = QToolButton()
        synchButton.setDefaultAction(synchAction)
        synchButton.setAutoRaise(True)

        hbox = QHBoxLayout()
        hbox.addWidget(upButton)
        hbox.addWidget(synchButton)
        hbox.addWidget(newButton)
        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox)
        vbox.addWidget(self.lineEdit)
        vbox.addWidget(self.listView)
        vbox.addWidget(hiddenCheckbox)
        #vbox.addWidget(self.filterEdit)

    def toggleHidden(self, state):
        base = QDir.AllDirs|QDir.AllEntries|QDir.NoDotAndDotDot
        if state == Qt.Checked:
            self.model.setFilter(base|QDir.Hidden)
        else:
            self.model.setFilter(base)

    def gotoFolder(self):
        text = self.lineEdit.text()
        self.listView.setRootIndex(self.model.index(text, 0))

    def rootChanged(self):
        self.lineEdit.setText(self.model.filePath(self.listView.rootIndex()))

    def customContext(self, pos):
        index = self.listView.indexAt(pos)
        if not index.isValid():
            actions = self.actions[0:3]
        elif not self.model.isDir(index):
            info = self.model.fileInfo(index)
            suffix = info.suffix()
            if suffix in ("Rd","Rdata","RData"):
                actions = self.actions
                del actions[4]
            elif suffix == "R":
                actions = self.actions[0:-1]
            else:
                actions = self.actions[0:4]
        else:
            actions = self.actions
        menu = QMenu(self)
        for action in actions:
            menu.addAction(action)
        menu.exec_(self.listView.mapToGlobal(pos))

    def openItem(self):
        index = self.listView.currentIndex()
        self.emit(SIGNAL("openFileRequest(QString)"),
        self.model.filePath(index))

    def loadItem(self):
        index = self.listView.currentIndex()
        self.emit(SIGNAL("loadFileRequest(QString)"),
        self.model.filePath(index))

    def newFolder(self):
        text, ok = QInputDialog.getText(self,
            "New Folder", "Folder name:", QLineEdit.Normal,
            "new_folder")
        if ok:
            self.model.mkdir(self.listView.rootIndex(), text)

    def rmItem(self):
        index = self.listView.currentIndex()
        if index == self.listView.rootIndex():
            return
        yes = QMessageBox.question(self, "manageR Warning",
            "Are you sure you want to delete '%s'?" % self.model.fileName(index),
            QMessageBox.Yes|QMessageBox.Cancel)
        if not yes == QMessageBox.Yes:
            return
        if self.model.isDir(index):
            result = self.model.rmdir(index)
        else:
            result = self.model.remove(index)
        if not result:
            QMessageBox.warning(self, "manageR Error",
            "Unable to delete %s!" % self.model.fileName(index))

    def upFolder(self):
        self.listView.setRootIndex(self.model.parent(self.listView.rootIndex()))
        self.rootChanged()

    def cdFolder(self):
        indexes = self.listView.selectedIndexes()
        if len(indexes) < 1:
            return
        index = indexes[0]
        if self.model.isDir(index):
            self.listView.setRootIndex(index)
        self.rootChanged()
        self.listView.clearSelection()

    def synchFolder(self):
        text = robjects.r.getwd()[0]
        self.listView.setRootIndex(self.model.index(text, 0))
        self.rootChanged()

    # If possible, the QGIS version should also alow
    # users to load OGR/GDAL supported files from here using rgdal
    # NOTE: Add a filter line edit at the bottom of the widget
    # Buttons: Up, Forward, Back, New folder, Synch with R
    # Right click: New folder, Delete, Load data, Load script
    # NOTE: Also show file size, and date if possible

class HistoryWidget(RWidget):

    class ListView(QListView):
        def __init__(self, parent):
            QListView.__init__(self, parent)
            self.setAlternatingRowColors(True)
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.setSelectionMode(QAbstractItemView.ExtendedSelection)

        def mousePressEvent(self, event):
            item = self.indexAt(event.globalPos())
            if not item and event.button() == Qt.LeftButton:
                self.setSelection(QRect(), QItemSelectionModel.Clear)
            QListView.mousePressEvent(self, event)

        def selectionChanged(self, new, old):
            self.emit(SIGNAL("selectionChanged()"))
            QListView.selectionChanged(self, new, old)

    def __init__(self, parent):
        RWidget.__init__(self, parent)
        self.parent = parent
        self.commandList = self.ListView(self)
        self.commandList.setToolTip("Right click item to view options")
        self.commandList.setWhatsThis("List of previous commands")

        self.copyAction = QAction("&Copy command(s)", self)
        self.copyAction.setStatusTip("Copy the selected command(s) to the clipboard")
        self.copyAction.setToolTip("Copy the selected command(s) to the clipboard")
        self.copyAction.setIcon(QIcon(":edit-copy.svg"))
        self.copyAction.setEnabled(False)

        self.selectAction = QAction("Select &all", self)
        self.selectAction.setStatusTip("Select all commands")
        self.selectAction.setToolTip("Select all commands")
        self.selectAction.setIcon(QIcon(":edit-select-all.svg"))

        self.runAction = QAction("&Run command(s)", self)
        self.runAction.setStatusTip("Run the selected command(s) in the console")
        self.runAction.setToolTip("Run the selected command(s) in the console")
        self.runAction.setIcon(QIcon(":utilities-terminal.svg"))
        self.runAction.setEnabled(False)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.commandList)

        self.connect(self.copyAction, SIGNAL("triggered()"), self.copy)
        #self.connect(self.insertAction, SIGNAL("triggered()"), self.insert)
        self.connect(self.runAction, SIGNAL("triggered()"), self.run)
        #self.connect(self.clearAction, SIGNAL("triggered()"), self.clear)
        self.connect(self.selectAction, SIGNAL("triggered()"), self.selectAll)
        self.connect(self.commandList, SIGNAL("doubleClicked(QModelIndex)"),
        self.doubleClicked)
        self.connect(self.commandList, SIGNAL("selectionChanged()"), self.selectionChanged)

    def setModel(self, model):
        self.commandList.setModel(model)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(self.runAction)
        menu.addAction(self.copyAction)
        menu.addAction(self.selectAction)
        menu.exec_(event.globalPos())

    def selectionChanged(self):
        count = len(self.commandList.selectedIndexes())
        if count > 0:
            self.runAction.setEnabled(True)
            self.copyAction.setEnabled(True)
        else:
            self.runAction.setEnabled(False)
            self.copyAction.setEnabled(False)

    def copy(self):
        commands = QString()
        selected = self.commandList.selectedIndexes()
        count = 1
        for index in selected:
            if count == len(selected):
                commands.append(self.commandList.model().data(index, Qt.DisplayRole))
            else:
                commands.append(self.commandList.model().data(index, Qt.DisplayRole)+"\n")
            count += 1
        clipboard = QApplication.clipboard()
        clipboard.setText(commands, QClipboard.Clipboard)

    def run(self):
        commands = QString()
        selected = self.commandList.selectedIndexes()
        count = 1
        for index in selected:
            if count == len(selected):
                commands.append(self.commandList.model().data(index, Qt.DisplayRole))
            else:
                commands.append(self.commandList.model().data(index, Qt.DisplayRole)+"\n")
            count += 1
        self.runCommands(commands)

    def selectAll(self):
        self.commandList.selectAll()

    def runCommands(self, commands):
        if not commands.isEmpty():
            self.emitCommands(commands)

    def doubleClicked(self, index):
        self.runCommands(
        self.commandList.model().data(
        index, Qt.DisplayRole))
        self.parent.setFocus(Qt.MouseFocusReason)

class WorkspaceWidget(RWidget):

    class TreeWidget(QTreeWidget):
        def __init__(self, parent):
            QTreeWidget.__init__(self, parent)
            self.setAlternatingRowColors(True)
            self.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.setSelectionMode(QAbstractItemView.SingleSelection)

        def mousePressEvent(self, event):
            item = self.itemAt(event.globalPos())
            if not item and event.button() == Qt.LeftButton:
                self.clearSelection()
            QTreeWidget.mousePressEvent(self, event)

        def selectionChanged(self, new, old):
            self.emit(SIGNAL("itemSelectionChanged()"))
            QTreeWidget.selectionChanged(self, new, old)

    def __init__(self, parent=None):
        RWidget.__init__(self, parent)
        self.workspaceTree = self.TreeWidget(self)
        self.workspaceTree.setColumnCount(3)
        self.workspaceTree.setHeaderLabels(QStringList(["Name", "Type", "Size", "Memory"]))

        self.levelSpinBox = QSpinBox()
        self.levelSpinBox.setRange(0,99)
        self.levelSpinBox.setSuffix(" level(s)")
        self.levelSpinBox.setValue(0)
        levelLabel = QLabel("Depth of object recursion:")
        self.levelSpinBox.setToolTip("<p>Specify depth of recursion "
                "for individual objects. Use zero (0) to display "
                "full recursion.</p>")
        levelLabel.setBuddy(self.levelSpinBox)
        self.levelSpinBox.setValue(QSettings().value("manageR/recursion", 0).toInt()[0])

        self.actions = []
        self.refreshAction = QAction("Re&fresh variables", self)
        self.refreshAction.setToolTip("Refresh environment browser")
        self.refreshAction.setWhatsThis("Refresh environment browser")
        self.refreshAction.setIcon(QIcon(":view-refresh.svg"))
        self.refreshAction.setEnabled(True)
        self.actions.append(self.refreshAction)

        self.loadAction = QAction("&Load data", self)
        self.loadAction.setToolTip("Load R variable(s) from file")
        self.loadAction.setWhatsThis("Load R variable(s) from file")
        self.loadAction.setIcon(QIcon(":package-x-generic.svg"))
        self.loadAction.setEnabled(True)
        self.actions.append(self.loadAction)

        self.exportAction = QAction("Export to &file", self)
        self.exportAction.setToolTip("Export data to file")
        self.exportAction.setWhatsThis("Export data to file")
        self.exportAction.setIcon(QIcon(":document-save.svg"))
        self.exportAction.setEnabled(False)
        self.actions.append(self.exportAction)

        self.saveAction = QAction("&Save variable", self)
        self.saveAction.setToolTip("Save R variable to file")
        self.saveAction.setWhatsThis("Save R variable to file")
        self.saveAction.setIcon(QIcon(":document-save.svg"))
        self.saveAction.setEnabled(False)
        self.actions.append(self.saveAction)

        self.methodAction = QAction("&Print available methods", self)
        self.methodAction.setToolTip("Print available methods for object class")
        self.methodAction.setWhatsThis("Print available methods for object class")
        self.methodAction.setIcon(QIcon(":dialog-information.svg"))
        self.methodAction.setEnabled(False)
        self.actions.append(self.methodAction)

        self.attributeAction = QAction("Print object &attributes", self)
        self.attributeAction.setToolTip("Print available attributes for object class")
        self.attributeAction.setWhatsThis("Print available attributes for object class")
        self.attributeAction.setIcon(QIcon(":dialog-question.svg"))
        self.attributeAction.setEnabled(False)
        self.actions.append(self.attributeAction)

        self.rmAction = QAction("&Remove", self)
        self.rmAction.setToolTip("Remove selected variable")
        self.rmAction.setWhatsThis("Removed selected variable")
        self.rmAction.setIcon(QIcon(":edit-delete.svg"))
        self.rmAction.setEnabled(False)
        self.actions.append(self.rmAction)

        vbox = QVBoxLayout(self)
        hbox = QHBoxLayout()
        hbox.addWidget(levelLabel)
        hbox.addWidget(self.levelSpinBox)
        vbox.addLayout(hbox)
        vbox.addWidget(self.workspaceTree)

        self.variables = dict()
        self.connect(self.rmAction, SIGNAL("triggered()"), self.removeVariable)
        self.connect(self.exportAction, SIGNAL("triggered()"), self.exportVariable)
        self.connect(self.saveAction, SIGNAL("triggered()"), self.saveVariable)
        self.connect(self.loadAction, SIGNAL("triggered()"), self.loadRVariable)
        self.connect(self.methodAction, SIGNAL("triggered()"), self.printMethods)
        self.connect(self.refreshAction, SIGNAL("triggered()"), self.updateVariables)
        self.connect(self.attributeAction, SIGNAL("triggered()"), self.printAttributes)
        self.connect(self.workspaceTree, SIGNAL("itemSelectionChanged()"), self.selectionChanged)
        self.updateVariables()
        self.connect(self.levelSpinBox, SIGNAL("valueChanged(int)"), self.saveSettings)

    def saveSettings(self, value):
        QSettings().setValue("manageR/recursion", value)

    def mousePressEvent(self, event):
        item = self.workspaceTree.itemAt(event.globalPos())
        if not item and event.button() == Qt.LeftButton:
            self.workspaceTree.clearSelection()
        RWidget.mousePressEvent(self, event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(self.refreshAction)
        menu.addSeparator()
        for action in self.actions[1:]:
            menu.addAction(action)
        menu.exec_(event.globalPos())

    def selectionChanged(self):
        items = self.workspaceTree.selectedItems()
        if len(items) < 1:
            for action in self.actions[2:]:
                action.setEnabled(False)
        else:
            for action in self.actions[2:]:
                action.setEnabled(True)

    def printMethods(self):
        items = self.workspaceTree.selectedItems()
        if len(items) < 1:
            return False
        itemName, itemType = self.getVariableInfo(items[0])
        self.runCommand('methods(class=%s)' % (itemType,))

    def printAttributes(self):
        items = self.workspaceTree.selectedItems()
        if len(items) < 1:
            return False
        tree = self.variablePath(items[0])
        self.runCommand('names(attributes(%s))' % tree)

    def removeVariable(self):
        items = self.workspaceTree.selectedItems()
        if len(items) < 1:
            return False
        item = items[0]
        tree = self.variablePath(item)
        command = "rm(%s)" % tree
        if item.parent():
            command = "%s <- NULL" % tree
        self.runCommand(command)
        self.updateVariables()

    def exportVariable(self):
        items = self.workspaceTree.selectedItems()
        if len(items) < 1:
            return False
        tree = self.variablePath(items[0])
        fd = QFileDialog(self.parent, "Save data to file", str(robjects.r.getwd()),
        "Comma separated (*.csv);;Text file (*.txt);;All files (*.*)")
        fd.setAcceptMode(QFileDialog.AcceptSave)
        if not fd.exec_() == QDialog.Accepted:
            return False
        files = fd.selectedFiles()
        selectedFile = files.first()
        if selectedFile.length() == 0:
            return False
        suffix = QString(fd.selectedNameFilter())
        index1 = suffix.lastIndexOf("(")+2
        index2 = suffix.lastIndexOf(")")
        suffix = suffix.mid(index1, index2-index1)
        if not selectedFile.endsWith(suffix):
            selectedFile.append(suffix)
        command = QString('write.table(%s, file = "%s",' % (tree, selectedFile))
        command.append(QString('append = FALSE, quote = TRUE, sep = ",", eol = "\\n", na = "NA"'))
        command.append(QString(', dec = ".", row.names = FALSE, col.names = TRUE, qmethod = "escape")'))
        self.runCommand(command)

    def saveVariable(self):
        items = self.workspaceTree.selectedItems()
        if len(items) < 1:
            return False
        parent = item[0].parent()
        name = items[0].text(0)
        while parent:
            name = parent.text(0)
            parent = parent.parent()
        fd = QFileDialog(self.parent, "Save data to file",
        str(robjects.r.getwd()[0]), "R data file (*.Rdata)")
        fd.setAcceptMode(QFileDialog.AcceptSave)
        if not fd.exec_() == QDialog.Accepted:
            return False
        files = fd.selectedFiles()
        selectedFile = files.first()
        if selectedFile.length() == 0:
            return False
        suffix = QString(fd.selectedNameFilter())
        index1 = suffix.lastIndexOf("(")+2
        index2 = suffix.lastIndexOf(")")
        suffix = suffix.mid(index1, index2-index1)
        if not selectedFile.endsWith(suffix):
            selectedFile.append(suffix)
        commands = QString('save(%s, file="%s")' % (name,selectedFile))
        self.runCommand(commands)

    def loadRVariable(self):
        fd = QFileDialog(self.parent, "Load R variable(s) from file",
        str(robjects.r.getwd()[0]), "R data (*.Rdata);;All files (*.*)")
        fd.setAcceptMode(QFileDialog.AcceptOpen)
        fd.setFileMode(QFileDialog.ExistingFile)
        if fd.exec_() == QDialog.Rejected:
            return False
        files = fd.selectedFiles()
        selectedFile = files.first()
        if selectedFile.length() == 0:
            return False
        self.runCommand(QString('load("%s")' % (selectedFile)))
        self.updateVariables()

    def getVariableInfo(self, item):
        item_name = item.text(0)
        item_type = item.text(1)
        return (item_name, item_type)

    def variablePath(self, item):
        name = item.text(0)
        name.remove("[[").remove("]]")
        parent = item.parent()
        #pname = parent.text(0)
        names = []
        while parent:
            tmp = parent.text(0)
            tmp.remove("[[").remove("]]")
            names.insert(0,tmp)
            parent = parent.parent()
        names.append(name)
        path = [ "[['%s']]" % name if not name.startsWith("@") else unicode(name) for name in names[1:]]
        return unicode(names[0])+str.join("", path)

    def runCommand(self, command):
        if not command == "":
            self.emitCommands(command)

    def updateVariables(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.workspaceTree.clear()
        data = browseEnv(self.levelSpinBox.value())
        for node in data:
            self.showRecurse(node, self.workspaceTree)
        QApplication.restoreOverrideCursor()
        return True

    def showRecurse(self, node, parent):
        a = QTreeWidgetItem(parent)
        a.setText(0, QString(node.name()))
        a.setText(1, QString(node.className()))
        a.setText(2, QString(node.dimensions()))
        a.setText(3, QString(node.memory()))
        if not node.hasChildren():
            return
        else:
            for j in node.children():
                self.showRecurse(j, a)
        return True