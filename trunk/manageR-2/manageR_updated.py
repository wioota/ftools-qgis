#!/usr/bin/env python
# -*- coding: utf-8 -*-

LICENSE = '''manageR - Interface to the R statistical programming language

Copyright (C) 2009-2010 Carson J. Q. Farmer

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public Licence as published by the Free Software
Foundation; either version 2 of the Licence, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public Licence for more details.

You should have received a copy of the GNU General Public Licence along with
this program (see LICENSE file in install directory); if not, write to the Free
Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.

Portions of the Console and EditR window, as well as several background
funtions are based on the Sandbox python gui of Mark Summerfield.
  Copyright (C) 2007-9 Mark Summerfield. All rights reserved.
  Released under the terms of the GNU General Public License.
The 'plugin' functinality is based largely on the PostGisTools plugin of
Mauricio de Paulo.
  Copyright (C) 2009 Mauricio de Paulo. All rights reserved.
  Released under the terms of the GNU General Public License.
manageR makes extensive use of rpy2 (Laurent Gautier) to communicate with R.
  Copyright (C) 2008-9 Laurent Gautier.
  Rpy2 may be used under the terms of the GNU General Public License.
'''

# general python imports  
import os, re, sys, platform, base64
from xml.dom import minidom
from multiprocessing import Process, Queue, Lock, Pipe

# PyQt imports
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import QHttp

# extra resources
import resources
import complete

# rpy2 (R) imports
import rpy2
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc

# constants
CURRENTDIR = unicode(os.path.abspath(os.path.dirname(__file__)))
VERSION = "2.0.0"
WELCOME = unicode("Welcome to manageR version %s\n"
"Copyright (C) 2009-2010 Carson J. Q. Farmer\n\n"
"manageR is free software and comes with ABSOLUTELY NO WARRANTY."
"You can redistribute it and/or modify it under the terms of "
"the GNU Lesser General Public License version 2.1 (or later) "
"as published by the Free Software Foundation.\n\n"
"Currently running %s\n\n" % (VERSION, robjects.r.version[12][0]))

class MainWindow(QMainWindow):

    def __init__(self, parent=None, console=True, tabwidth=4,
                 autobracket=True, autopopup=True, sidepanel=True):
        QMainWindow.__init__(self, parent)
        #super(MainWindow, self).__init__(parent)
        self.setWindowIcon(QIcon(":mActionIcon"))
        font = QFont("DejaVu Sans Mono",10)
        self.setFont(font)
        self.setMinimumSize(50, 50)
        self.startTimer(30)
        self.main = BaseFrame(self, tabwidth, autobracket,
                              autopopup, sidepanel, console)
        if console:
            self.setWindowTitle("manageR")
            self.main.editor().setCheckSyntax(False)
            data = QMimeData()
            data.setText(WELCOME)
            self.main.editor().insertFromMimeData(data)
            #self.main.editor().insertPlainText("\n")
            self.main.editor().setCheckSyntax(True)
            self.main.editor().setHistory(HISTORY)
            #QShortcut(QKeySequence("F5"), self, self.fileNew)
            #QShortcut(QKeySequence("F6"), self, self.fileOpen)
            #QShortcut(QKeySequence("F7"), self, self.openData)
        else:
            self.setWindowTitle("editR - untitled")
            self.columnCountLabel = QLabel("Column 1")
            self.statusBar().addPermanentWidget(self.columnCountLabel)
            self.lineCountLabel = QLabel("Line 1 of 1")
            self.statusBar().addPermanentWidget(self.lineCountLabel)
            self.connect(self.main.editor(), SIGNAL("cursorPositionChanged()"),
                self.updateIndicators)
            self.connect(self.main.editor().document(), SIGNAL("blockCountChanged(int)"),
                self.updateIndicators)
            #QShortcut(QKeySequence("F5"), self, self.fileSave)
        self.setCentralWidget(self.main)
        self.paths = QStringList(os.path.join(CURRENTDIR, "icons"))
        self.createFileActions(console)
        self.createEditActions(console)
        self.createActionActions(console)
        self.createWorkspaceActions(console)
        self.createWindowActions(console)
        self.createDockWigets(console)
        self.createHelpActions(console)

        #QShortcut(QKeySequence("F1"), self, self.helpBrowser)
        #QShortcut(QKeySequence("F2"), self, self.repositoryBrowser)
        #QShortcut(QKeySequence("F3"), self, self.searchBar)
        #QShortcut(QKeySequence("F4"), self, self.libraryBrowser)
        self.statusBar().showMessage("Ready", 5000)

    def createDockWigets(self, console=True):
        if console:
            widgets = []
            historyWidget = HistoryWidget(self.main.editor())
            historyWidget.setModel(HISTORY)
            historyDockWidget = QDockWidget("Command History", self)
            historyDockWidget.setObjectName("historyDockWidget")
            historyDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
            historyDockWidget.setWidget(historyWidget)
            self.addDockWidget(Qt.RightDockWidgetArea, historyDockWidget)
            self.connect(historyWidget, SIGNAL("emitCommands(QString)"), self.main.editor().acceptCommands)
            widgets.append(historyDockWidget)

            cwdWidget = WorkingDirectoryWidget(self,robjects.r('getwd()')[0])
            cwdDockWidget = QDockWidget("Working Directory", self)
            cwdDockWidget.setObjectName("cwdDockWidget")
            cwdDockWidget.setAllowedAreas(Qt.TopDockWidgetArea|Qt.BottomDockWidgetArea)
            cwdDockWidget.setWidget(cwdWidget)
            self.addDockWidget(Qt.TopDockWidgetArea, cwdDockWidget)
            self.connect(self.main.editor(), SIGNAL("commandComplete()"), cwdWidget.getWorkingDir)
            self.connect(cwdWidget, SIGNAL("emitCommands(QString)"), self.main.editor().acceptCommands)
            widgets.append(cwdDockWidget)

            workspaceWidget = WorkspaceWidget(self.main.editor())
            workspaceDockWidget = QDockWidget("Workspace Manager", self)
            workspaceDockWidget.setObjectName("workspaceDockWidget")
            workspaceDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
            workspaceDockWidget.setWidget(workspaceWidget)
            self.addDockWidget(Qt.RightDockWidgetArea, workspaceDockWidget)
            widgets.append(workspaceDockWidget)

            directoryWidget = DirectoryWidget(self)
            directoryDockWidget = QDockWidget("Directory Browser", self)
            directoryDockWidget.setObjectName("directoryDockWidget")
            directoryDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
            directoryDockWidget.setWidget(directoryWidget)
            self.addDockWidget(Qt.LeftDockWidgetArea, directoryDockWidget)
            self.connect(directoryWidget, SIGNAL("openFileRequest(QString)"), self.fileOpen)
            self.connect(directoryWidget, SIGNAL("loadFileRequest(QString)"), self.openData)
            widgets.append(directoryDockWidget)

            scratchPadWidget = ScratchPadWidget(self)
            scratchPadDockWidget = QDockWidget("Scratch Pad", self)
            scratchPadDockWidget.setObjectName("scratchPadDockWidget")
            scratchPadDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
            scratchPadDockWidget.setWidget(scratchPadWidget)
            self.addDockWidget(Qt.LeftDockWidgetArea, scratchPadDockWidget)
            widgets.append(scratchPadDockWidget)

            self.tabifyDockWidget(historyDockWidget, workspaceDockWidget)
            self.tabifyDockWidget(scratchPadDockWidget, directoryDockWidget)

            viewMenu = self.menuBar().addMenu("&View")
            for widget in widgets:
                #text = widget.windowTitle()
                action = widget.toggleViewAction()
                viewMenu.addAction(action)

    def createFileActions(self, console=True):
        fileMenu = self.menuBar().addMenu("&File")
        if console:
            fileNewAction = self.createAction("&New", self.fileNew,
                QKeySequence.New, "mActionFileNew", "Open empty R script")
            fileOpenAction = self.createAction("&Open...", self.fileOpen,
                QKeySequence.Open, "mActionFileOpen", "Open existing R script")
            self.addActions(fileMenu, (fileNewAction, fileOpenAction, None, ))
        else:
            fileOpenAction = self.createAction("&Open...", self.fileOverwrite,
                QKeySequence.Open, "mActionFileOpen", "Open existing R script")
            fileSaveAction = self.createAction("&Save", self.fileSave,
                QKeySequence.Save, "mActionFileSave", "Save R script")
            fileSaveAsAction = self.createAction("Save &As...",
                self.fileSaveAs, QKeySequence.SaveAs,
                "mActionFileSaveAs", "Save R script as...")
            fileCloseAction = self.createAction("&Close", self.fileClose,
                QKeySequence.Close, "mActionFileClose",
                "Close this editR window")
            self.addActions(fileMenu, (fileOpenAction, fileSaveAction,
                fileSaveAsAction, None, fileCloseAction,))
        if console:
            fileConfigureAction = self.createAction("Config&ure...",
                self.fileConfigure, QKeySequence.Preferences,
                "mActionFileConfigure", "Configure manageR")
            fileQuitAction = self.createAction("&Quit", self.fileQuit,
                QKeySequence.Quit, "mActionFileQuit", "Quit manageR")
            self.addActions(fileMenu, (fileConfigureAction, None,
                fileQuitAction,))

    def createEditActions(self, console=True, autocomplete=True):
        editMenu = self.menuBar().addMenu("&Edit")
        if not console:
            editUndoAction = self.createAction("&Undo", self.main.editor().undo,
                QKeySequence.Undo, "mActionEditUndo",
                "Undo last editing action")
            editRedoAction = self.createAction("&Redo", self.main.editor().redo,
                QKeySequence.Redo, "mActionEditRedo",
                "Redo last editing action")
            self.addActions(editMenu, (editUndoAction, editRedoAction, None))
        editCopyAction = self.createAction("&Copy", self.main.editor().copy,
            QKeySequence.Copy, "mActionEditCopy", "Copy text to clipboard")
        editCutAction = self.createAction("Cu&t", self.main.editor().cut,
            QKeySequence.Cut, "mActionEditCut", "Cut text to clipboard")
        editPasteAction = self.createAction("&Paste",
            self.main.editor().paste, QKeySequence.Paste, "mActionEditPaste",
            "Paste text from clipboard")
        editSelectAllAction = self.createAction("Select &All",
            self.main.editor().selectAll, QKeySequence.SelectAll,
            "mActionEditSelectAll", "Select all")
        self.addActions(editMenu, (editCopyAction, editCutAction,
            editPasteAction, editSelectAllAction, None))
        if autocomplete:
            editCompleteAction = self.createAction("Com&plete",
                self.main.completer().suggest, "TAB", "mActionEditComplete",
                "Initiate autocomplete suggestions")
            self.addActions(editMenu, (editCompleteAction, None,))
        editFindNextAction = self.createAction("&Find",
            self.main.toggleSearch, QKeySequence.Find,
            "mActionEditFindNext", "Find text")
        self.addActions(editMenu, (editFindNextAction,))
        if not console:
            editReplaceNextAction = self.createAction("&Replace",
                self.main.toggleReplace, QKeySequence.Replace,
                "mActionEditReplaceNext", "Replace text")
            editGotoLineAction =  self.createAction("&Go to line",
                self.main.editor().gotoLine, "Ctrl+G", "mActionEditGotoLine",
                "Move cursor to line")
            editIndentRegionAction = self.createAction("&Indent Region",
                self.main.editor().indentRegion, "Tab", "mActionEditIndent",
                "Indent the selected text or the current line")
            editUnindentRegionAction = self.createAction(
                "Unin&dent Region", self.main.editor().unindentRegion,
                "Shift+Tab", "mActionEditUnindent",
                "Unindent the selected text or the current line")
            editCommentRegionAction = self.createAction("C&omment Region",
                self.main.editor().commentRegion, "Ctrl+D", "mActionEditComment",
                "Comment out the selected text or the current line")
            editUncommentRegionAction = self.createAction(
                "Uncomment Re&gion", self.main.editor().uncommentRegion,
                "Ctrl+Shift+D", "mActionEditUncomment",
                "Uncomment the selected text or the current line")
            self.addActions(editMenu, (editReplaceNextAction, None,
                editGotoLineAction, editIndentRegionAction, editUnindentRegionAction,
                editCommentRegionAction, editUncommentRegionAction,))

    def createActionActions(self, console=True):
        actionMenu = self.menuBar().addMenu("&Action")
        if not console:
            actionRunAction = self.createAction("E&xecute",
                self.send, "Ctrl+Return", "mActionRun",
                "Execute the (selected) text in the manageR console")
            actionSourceAction = self.createAction("Run S&cript",
                self.source,"", "mActionSource",
                "Run the current EditR script")
            self.addActions(actionMenu, (actionRunAction, actionSourceAction, None,))
        else:
            actionShowPrevAction = self.createAction(
                "Show Previous Command", self.main.editor().previous,
                "Up", "mActionPrevious", "Show previous command")
            actionShowNextAction = self.createAction(
                "Show Next Command", self.main.editor().next,
                "Down", "mActionNext", "Show next command")
            self.addActions(actionMenu, (actionShowPrevAction,
                actionShowNextAction,))

    def createWorkspaceActions(self, console=True):
        if console:
            workspaceMenu = self.menuBar().addMenu("Wo&rkspace")
            workspaceLoadAction = self.createAction(
                "Load R workspace", self.openWorkspace,
                "Ctrl+W", "mActionWorkspaceLoad",
                "Load R workspace")
            workspaceSaveAction = self.createAction(
                "Save R workspace", self.saveWorkspace,
                "Ctrl+Shift+W", "mActionWorkspaceSave",
                "Save R workspace")
            workspaceDataAction = self.createAction(
                "Load R data", self.openData,
                "Ctrl+D", "mActionWorkspaceData",
                "Load R data")
            workspaceLibraryAction = self.createAction("&Library browser",
                self.libraryBrowser, "Ctrl+H", icon="mActionHelpHelp",
                tip="Browse R package library")
            workspaceRepositoryAction = self.createAction("&Install packages",
                self.repositoryBrowser, icon="mActionHelpHelp",
                tip="Install R packages")
            self.addActions(workspaceMenu, (workspaceLoadAction,
                workspaceSaveAction, workspaceDataAction, None,
                workspaceLibraryAction, workspaceRepositoryAction,))

    def createHelpActions(self, console=True):
        helpMenu = self.menuBar().addMenu("&Help")
        helpSearchAction = self.createAction("&Help", self.helpBrowser,
            QKeySequence.HelpContents, icon="mActionHelpHelp",
            tip="Commands help")
        helpAboutAction = self.createAction("&About", self.helpAbout,
            "F1", icon="mActionIcon", tip="About manageR")
        self.addActions(helpMenu, (helpSearchAction, helpAboutAction,))

    def createWindowActions(self, console=True):
        if console:
            self.windowMenu = self.menuBar().addMenu("&Window")
            self.connect(self.windowMenu, SIGNAL("aboutToShow()"),
                 self.updateWindowMenu)

    def updateIndicators(self):
        lines = self.main.editor().document().blockCount()
        cursor = self.main.editor().textCursor()
        self.columnCountLabel.setText("Column %d" % (cursor.columnNumber()+1))
        if lines == 0:
            text = "(empty)"
        else:
            text = "Line %d of %d " % (cursor.blockNumber()+1, lines)
        self.lineCountLabel.setText(text)

    def updateWindowMenu(self):
        self.windowMenu.clear()
        action = self.windowMenu.addAction("&Console", self.raise_)
        action.setData(QVariant(long(id(self))))
        action.setIcon(QIcon(":mActionConsole.png"))
        i = 1
        menu = self.windowMenu
        windows = QApplication.findChildren(self, MainWindow)
        for window in windows:
            text = window.windowTitle()
            if i == 10:
                self.windowMenu.addSeparator()
                menu = menu.addMenu("&More")
            accel = ""
            if i < 10:
                accel = "&%d " % i
            elif i < 36:
                accel = "&%c " % chr(i + ord("@") - 9)
            text = "%s%s" % (accel, text)
            i += 1
            action = menu.addAction(text, window.raise_)
            action.setData(QVariant(long(id(window))))
            action.setIcon(QIcon(":mActionWindow.png"))

    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()",
                     param=None):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            if param is not None:
                print action, signal, slot, param
                self.connect(action, SIGNAL(signal), slot, param)
            else:
                self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def timerEvent(self, e):
        try:
            robjects.rinterface.process_revents()
        except:
            pass

    def libraryBrowser(self):
        browser = RLibraryBrowser(self, self.paths)
        browser.show()

    def helpBrowser(self):
        browser = RHelpBrowser(self, self.paths)
        browser.show()

    def helpAbout(self):
        browser = AboutBrowser(self)
        browser.exec_()

    def repositoryBrowser(self, mirror=None):
        if mirror is None:
            if robjects.r.getOption('repos')[0] == "@CRAN@":
                mirrorBrowser = RMirrorBrowser(self)
                if not mirrorBrowser.exec_():
                    return
        browser = RRepositoryBrowser(self)
        browser.exec_()

    def saveWorkspace(self, path=None, filter="R workspace (*.RData)"):
        self.saveData(path, filter)

    def openWorkspace(self, path=None, filter="R workspace (*.RData)"):
        self.openData(path, filter)

    def saveData(self, path=None, objects="ls(all=TRUE)", filter=None):
        command = ""
        if filter is None:
            filter = "R data (*.Rdata *.Rda *.RData)"
        if path is None:
            path = QFileDialog.getSaveFileName(self,
                            "manageR - Save Data File",
                            unicode(robjects.r.getwd()[0]), filter)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if not path.isEmpty():
            path = QDir(path).absolutePath()
            command = "save(file='%s', list=%s)" % (unicode(path),unicode(objects))
            try:
                self.execute(command)
            except Exception, err:
                QMessageBox.warning(self, "manageR - Save Error",
                "Unable to save data file %s!\n%s" % (path,err))
            self.statusBar().showMessage("Saved R Data %s" % path, 5000)
        QApplication.restoreOverrideCursor()

    def openData(self, path=None, filter=None):
        command = ""
        if filter is None:
            filter = "R data (*.Rdata *.Rda *.RData);;All files (*)"
        if path is None:
            path = QFileDialog.getOpenFileName(self,
                            "manageR - Open Data File",
                            unicode(robjects.r.getwd()[0]),
                            filter)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if not path.isEmpty():
            path = QDir(path).absolutePath()
            command = "load(file='%s')" % unicode(path)
            try:
                self.execute(command)
            except Exception, err:
                QMessageBox.warning(self, "manageR - Load Error",
                "Unable to load data file %s!\n%s" % (path,err))
            self.statusBar().showMessage("Loaded R Data %s" % path, 5000)
        QApplication.restoreOverrideCursor()

    def fileConfigure(self):
        pass

    def fileNew(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        window = MainWindow(self, False)
        self.connect(window, SIGNAL("requestExecuteCommands(QString)"),
            self.main.editor().acceptCommands)
        window.show()
        self.statusBar().showMessage("New script", 5000)
        QApplication.restoreOverrideCursor()

    def fileOverwrite(self, path=None):
        if path is None:
            path = QFileDialog.getOpenFileName(self,
                            "manageR - Open File",
                            unicode(robjects.r.getwd()[0]),
                            "R scripts (*.R);;All files (*)")
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if not path.isEmpty():
            # To prevent opening the same file twice
            windows = QApplication.findChildren(self, MainWindow)
            for window in windows:
                if window.windowTitle() == "editR - %s" % path:
                    window.show()
                    window.activateWindow()
                    window.raise_()
                    self.statusBar().showMessage("Showing %s" % path, 5000)
                    QApplication.restoreOverrideCursor()
                    return
        if self.main.editor().document().isModified():
            QApplication.restoreOverrideCursor()
            reply = QMessageBox.question(self,
                        "editR - Unsaved Changes",
                        "Save unsaved changes in %s" % self.windowTitle().remove("editR - "),
                        QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            if reply == QMessageBox.Save:
                self.fileSave()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
                QApplication.restoreOverrideCursor()
        self.fileLoad(path)
        QApplication.restoreOverrideCursor()

    def fileOpen(self, path=None):
        if path is None:
            path = QFileDialog.getOpenFileName(self,
                            "manageR - Open File",
                            unicode(robjects.r.getwd()[0]),
                            "R scripts (*.R);;All files (*)")
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if not path.isEmpty():
            # To prevent opening the same file twice
            windows = QApplication.findChildren(self, MainWindow)
            for window in windows:
                if window.windowTitle() == "editR - %s" % path:
                    window.show()
                    window.activateWindow()
                    window.raise_()
                    QApplication.restoreOverrideCursor()
                    self.statusBar().showMessage("Showing %s" % path, 5000)
                    QApplication.restoreOverrideCursor()
                    return
            window = MainWindow(self, False)
            self.connect(window, SIGNAL("requestExecuteCommands(QString)"),
                self.main.editor().acceptCommands)
            window.fileLoad(path)
            window.show()
        self.statusBar().showMessage("Opened %s" % path, 5000)
        QApplication.restoreOverrideCursor()

    def fileSave(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        path = self.windowTitle().remove("editR - ")
        if path == "untitled":
            QApplication.restoreOverrideCursor()
            return self.fileSaveAs()
        path = QDir(path).absolutePath()
        if QFile.exists(path):
            backup = "%s.backup" % path
            ok = True
            if QFile.exists(backup):
                ok = QFile.remove(backup)
                if not ok:
                    QMessageBox.information(self,
                            "editR - Save Warning",
                            "Failed to remove existing backup file %s")
            if ok:
                # Must use copy rather than rename to preserve file
                # permissions; could use rename on Windows though
                if not QFile.copy(path, backup):
                    QMessageBox.information(self,
                            "editR - Save Warning",
                            "Failed to save backup file %s")
        fh = None
        try:
            try:
                fh = QFile(path)
                if not fh.open(QIODevice.WriteOnly):
                    raise IOError, unicode(fh.errorString())
                stream = QTextStream(fh)
                stream.setCodec("UTF-8")
                stream << self.main.editor().toPlainText()
                self.main.editor().document().setModified(False)
                self.setWindowModified(False)
                self.setWindowTitle("editR - %s" % path)
                self.statusBar().showMessage("Saved %s" % path, 5000)
            except (IOError, OSError), e:
                QMessageBox.warning(self, "editR - Save Error",
                        "Failed to save %s: %s" % (path, e))
        finally:
            if fh is not None:
                fh.close()
        QApplication.restoreOverrideCursor()
        return True

    def fileSaveAs(self, path=None):
        if path is None:
            path = QFileDialog.getSaveFileName(self,
                   "editR - Save File As",
                   "untitled", "R scripts (*.R)")
        if not path.isEmpty():
            self.setWindowTitle("editR - %s" % QDir(path).absolutePath())
            return self.fileSave()
        return False

    def fileLoad(self, path=""):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        fh = None
        try:
            try:
                fh = QFile(path)
                if not fh.open(QIODevice.ReadOnly):
                    raise IOError, unicode(fh.errorString())
                stream = QTextStream(fh)
                stream.setCodec("UTF-8")
                text = stream.readAll()
                self.main.editor().setPlainText(text)
                self.main.editor().document().setModified(False)
            except (IOError, OSError), err:
                QMessageBox.warning(self, "editR - Load Error",
                        "Failed to load %s: %s" % (path,err))
        finally:
            if fh is not None:
                fh.close()
        self.main.editor().document().setModified(False)
        self.setWindowModified(False)
        self.setWindowTitle("editR - %s" % path)
        QApplication.restoreOverrideCursor()

    def fileClose(self):
        self.fileQuit()

    def fileQuit(self):
        self.close()
        del self

    def closeEvent(self, event):
        if self.main.editor().document().isModified():
            reply = QMessageBox.question(self,
                        "editR - Unsaved Changes",
                        "Save unsaved changes in %s" % self.windowTitle().remove("editR - "),
                        QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
            if reply == QMessageBox.Save:
                self.fileSave()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        self.fileQuit()
        event.accept()

    def source(self):
        self.fileSave()
        commands = 'source("%s")' % self.windowTitle().remove("editR - ")
        self.emit(SIGNAL("requestExecuteCommands(QString)"), commands)

    def send(self):
        commands = self.main.editor().textCursor().selectedText()
        if commands.isEmpty():
            commands = self.main.editor().toPlainText()
        self.execute(commands)

    def execute(self, commands):
        if not commands.isEmpty():
            commands.replace(u'\u2029',"\n")
            self.emit(SIGNAL("requestExecuteCommands(QString)"), commands)
        
#------------------------------------------------------------------------------#
#-------------------------- Main Console and Editor ---------------------------#
#------------------------------------------------------------------------------#

class PlainTextEdit(QPlainTextEdit):
    OUTPUT,INPUT,CONTINUE,SYNTAX = range(4)

    def __init__(self, parent=None, tabwidth=4, autobracket=True):
        QPlainTextEdit.__init__(self, parent)
        self.__tabwidth = tabwidth
        self.__parent = parent
        self.__autobracket = autobracket
        self.__checkSyntax = True
        #self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setFrameShape(QTextEdit.NoFrame)
        self.setAcceptDrops(False)
        self.connect(self, SIGNAL("cursorPositionChanged()"),
        self.positionChanged)

    def keyPressEvent(self, event):
        indent = " "*self.__tabwidth
        cursor = self.textCursor()
        if event.key() == Qt.Key_Tab:
            if not self.tabChangesFocus():
                if not cursor.hasSelection():
                    cursor.insertText(indent)
                    self.setTextCursor(cursor)
                else:
                    self.indentRegion()
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
            insert = "\n"
            line = cursor.block().text()
            if line.startsWith(indent):
                for c in line:
                    if c == " ":
                        insert += " "
                    else:
                        break
            self.entered()
            cursor.insertText(insert)
            self.setTextCursor(cursor)
        elif event.key() in (Qt.Key_ParenLeft,
                             Qt.Key_BracketLeft,
                             Qt.Key_BraceLeft):
            if self.__autobracket:
                cursor.movePosition(QTextCursor.NextCharacter,
                    QTextCursor.KeepAnchor)
                insert = ""
                if event.key() == Qt.Key_ParenLeft and \
                    not cursor.selectedText() == QString(Qt.Key_ParenRight):
                    insert = QString(Qt.Key_ParenRight)
                elif event.key() == Qt.Key_BracketLeft and \
                    not cursor.selectedText() == QString(Qt.Key_BracketRight):
                    insert = QString(Qt.Key_BracketRight)
                elif event.key() == Qt.Key_BraceLeft and \
                    not cursor.selectedText() == QString(Qt.Key_BraceRight):
                    insert = QString(Qt.Key_BraceRight)
                cursor = self.textCursor()
                cursor.insertText("%s%s" % (QString(event.key()),insert))
                if not insert == "":
                    cursor.movePosition(QTextCursor.PreviousCharacter,
                    QTextCursor.MoveAnchor)
                self.setTextCursor(cursor)
        elif event.key() in (Qt.Key_QuoteDbl,
                             Qt.Key_Apostrophe):
            if self.__autobracket:
                cursor.movePosition(QTextCursor.NextCharacter,
                    QTextCursor.KeepAnchor)
                insert = ""
                if event.key() == Qt.Key_QuoteDbl and \
                    not cursor.selectedText() == QString(Qt.Key_QuoteDbl):
                    insert = QString(Qt.Key_QuoteDbl)
                elif event.key() == Qt.Key_Apostrophe and \
                    not cursor.selectedText() == QString(Qt.Key_Apostrophe):
                    insert = QString(Qt.Key_Apostrophe)
                cursor = self.textCursor()
                cursor.insertText("%s%s" % (QString(event.key()),insert))
                if not insert == "":
                    cursor.movePosition(QTextCursor.PreviousCharacter,
                    QTextCursor.MoveAnchor)
                self.setTextCursor(cursor)
        else:
            QPlainTextEdit.keyPressEvent(self, event)

    def positionChanged(self):
        self.highlight()

    def highlight(self):
        extraSelections = []
        self.setExtraSelections(extraSelections)
        format = QTextCharFormat()
        format.setBackground(QColor(Qt.yellow).lighter(160))
        firstselection = QTextEdit.ExtraSelection()
        firstselection.format = format
        secondselection = QTextEdit.ExtraSelection()
        secondselection.format = format
        doc = self.document()
        cursor = self.textCursor()
        beforeCursor = QTextCursor(cursor)

        cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        brace = cursor.selectedText()

        beforeCursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
        beforeBrace = beforeCursor.selectedText()

        if ((brace != "{") and \
            (brace != "}") and \
            (brace != "[") and \
            (brace != "]") and \
            (brace != "(") and \
            (brace != ")")):
            if ((beforeBrace == "{") or \
                (beforeBrace == "}") or \
                (beforeBrace == "[") or \
                (beforeBrace == "]") or \
                (beforeBrace == "(") or \
                (beforeBrace == ")")):
                cursor = beforeCursor
                brace = cursor.selectedText();
            else:
                return

        #format = QTextCharFormat()
        #format.setForeground(Qt.red)
        #format.setFontWeight(QFont.Bold)

        if ((brace == "{") or (brace == "}")):
            openBrace = "{"
            closeBrace = "}"
        elif ((brace == "[") or (brace == "]")):
            openBrace = "["
            closeBrace = "]"
        elif ((brace == "(") or (brace == ")")):
            openBrace = "("
            closeBrace = ")"

        if (brace == openBrace):
            cursor1 = doc.find(closeBrace, cursor)
            cursor2 = doc.find(openBrace, cursor)
            if (cursor2.isNull()):
                firstselection.cursor.clearSelection()
                firstselection.cursor = cursor
                if (not cursor1.isNull()):
                    extraSelections.append(firstselection)
                #self.setExtraSelections(extraSelections)
                secondselection.cursor.clearSelection()
                secondselection.cursor = cursor1
                extraSelections.append(secondselection)
                self.setExtraSelections(extraSelections)
            else:
                while (cursor1.position() > cursor2.position()):
                    cursor1 = doc.find(closeBrace, cursor1)
                    cursor2 = doc.find(openBrace, cursor2)
                    if (cursor2.isNull()):
                        break
                firstselection.cursor.clearSelection()
                firstselection.cursor = cursor
                if (not cursor1.isNull()):
                    extraSelections.append(firstselection)
                #self.setExtraSelections(extraSelections)
                secondselection.cursor.clearSelection()
                secondselection.cursor = cursor1
                extraSelections.append(secondselection)
                self.setExtraSelections(extraSelections)

        else:
            if (brace == closeBrace):
                cursor1 = doc.find(openBrace, cursor, QTextDocument.FindBackward)
                cursor2 = doc.find(closeBrace, cursor, QTextDocument.FindBackward)
                if (cursor2.isNull()):
                    firstselection.cursor.clearSelection()
                    firstselection.cursor = cursor
                    if (not cursor1.isNull()):
                        #cursor.mergeCharFormat(syntaxformat)
                    #else:
                        extraSelections.append(firstselection)
                   # self.setExtraSelections(extraSelections)
                    secondselection.cursor.clearSelection()
                    secondselection.cursor = cursor1
                    extraSelections.append(secondselection)
                    self.setExtraSelections(extraSelections)
                else:
                    while (cursor1.position() < cursor2.position()):
                        cursor1 = doc.find(openBrace, cursor1,
                                           QTextDocument.FindBackward)
                        cursor2 = doc.find(closeBrace, cursor2,
                                           QTextDocument.FindBackward)
                        if (cursor2.isNull()):
                            break
                    firstselection.cursor.clearSelection()
                    firstselection.cursor = cursor
                    if (not cursor1.isNull()):
                        #cursor.mergeCharFormat(syntaxformat)
                    #else:
                        extraSelections.append(firstselection)
                    #self.setExtraSelections(extraSelections)
                    secondselection.cursor.clearSelection()
                    secondselection.cursor = cursor1
                    extraSelections.append(secondselection)
                    self.setExtraSelections(extraSelections)

    def event(self, e):
        if e.type() == QEvent.ToolTip:
            userCursor = self.textCursor()
            cursor = self.cursorForPosition(e.pos())
            if cursor.position() > min([userCursor.position(), userCursor.anchor()]) and \
                cursor.position() < max([userCursor.position(), userCursor.anchor()]) and \
                userCursor.hasSelection():
                word = userCursor.selectedText()
            else:
                cursor.select(QTextCursor.WordUnderCursor)
                word = cursor.selectedText()
            if not word.isEmpty():
                try:
                    args = QString(str(robjects.r(
                        'do.call(argsAnywhere, list("%s"))' % word)))
                    args = args.remove("NULL").replace(QRegExp(r'^function'), word)
                    args = args.trimmed().split("\n",QString.SkipEmptyParts).join("\n")
                except:
                    args = QString()
                if not args.isEmpty():
                    QToolTip.showText(e.globalPos(), args)
        return QPlainTextEdit.event(self, e)

    def lastLine(self):
        line = QString()
        block = self.textCursor().block().previous()
        return block.text()

    def setCheckSyntax(self, check=True):
        self.__checkSyntax = check

    def isCheckingSyntax(self):
        return self.__checkSyntax

    def checkSyntax(self, command, block=None, tag=True):
        command = unicode(command)
        if block is None:
            block = self.textCursor().block()
        if not self.isCheckingSyntax():
            if tag: block.setUserData(UserData(PlainTextEdit.OUTPUT, QString("Output")))
            return PlainTextEdit.OUTPUT
        try:
            robjects.r.parse(text=command)
        except robjects.rinterface.RRuntimeError, err:
            err = QString(unicode(err))
            if err.contains("unexpected end of input"):
                if tag: block.setUserData(UserData(PlainTextEdit.CONTINUE, QString("Continue")))
                return PlainTextEdit.CONTINUE # line continuation
            err = err.split(":", QString.SkipEmptyParts)[1:].join(" ").prepend("Error:")
            if tag: block.setUserData(UserData(PlainTextEdit.SYNTAX, err))
            return PlainTextEdit.SYNTAX # invalid syntax
        if tag: block.setUserData(UserData(PlainTextEdit.INPUT, QString("Input")))
        return PlainTextEdit.INPUT # valid syntax

    def insertFromMimeData(self, source):
        if source.hasText():
            #self.blockSignals(True)
            cursor = self.textCursor()
            cursor.beginEditBlock()
            lines = QStringList()
            lines = source.text().split("\n")
            # might be good to add the \n back in after the split
            tot = len(lines)-1
            for count, line in enumerate(lines):
                newSource = QMimeData()
                if count < tot:
                    line += "\n"
                newSource.setText(line)
                QPlainTextEdit.insertFromMimeData(self, newSource)
                if count < tot:
                    self.entered()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            #self.blockSignals(False)

    def entered(self):
        pass

    def currentCommand(self, block):
        command = QString(block.text())
        block = block.previous()
        pos1 = self.textCursor().position()
        pos2 = block.position()
        while block.isValid():
            try:
                if not block.userData().data() == PlainTextEdit.CONTINUE:
                    break
            except: # this means there is no user data, assume ok
                break
            command.prepend("\n%s" % block.text())
            block = block.previous()
            pos2 = block.position()
        return (command, pos1-pos2)

    def insertParameters(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText().remove(")").remove("(")
        cursor.clearSelection()
        if not word.isEmpty():
            args = QString(str(robjects.r(
                'do.call(argsAnywhere, list("%s"))' % word
                ))).remove("NULL").replace(
                QRegExp(r'^function'), "").remove("\n").trimmed()
            if not args.isEmpty():
                self.setTextCursor(cursor)
                self.insertPlainText(args)

class REditor(PlainTextEdit):

    def __init__(self, parent=None, tabwidth=4, autobracket=True):
        PlainTextEdit.__init__(self, parent, tabwidth, autobracket)
        self.connect(self, SIGNAL("cursorPositionChanged()"), self.textChanged)
        self.__tabwidth=tabwidth
        self.__autobracket=autobracket

    def gotoLine(self):
        cursor = self.textCursor()
        lino, ok = QInputDialog.getInteger(self,
                            "Goto line","Goto line:",cursor.blockNumber()+1,
                            1, self.document().blockCount())
        if ok:
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down,
                    QTextCursor.MoveAnchor, lino-1)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

    def indentRegion(self):
        self.walkTheLines(True, " "*self.__tabwidth)

    def unindentRegion(self):
        self.walkTheLines(False, " "*self.__tabwidth)

    def commentRegion(self):
        self.walkTheLines(True, "# ")

    def uncommentRegion(self):
        self.walkTheLines(False, "# ")

    def walkTheLines(self, insert, text):
        userCursor = self.textCursor()
        userCursor.beginEditBlock()
        start = userCursor.position()
        end = userCursor.anchor()
        if start > end:
            start, end = end, start
        block = self.document().findBlock(start)
        while block.isValid():
            cursor = QTextCursor(block)
            cursor.movePosition(QTextCursor.StartOfBlock)
            if insert:
                cursor.clearSelection()
                cursor.insertText(text)
            else:
                # also look for lines with leading whitespace
                regex = QRegExp(r"^\s*%s" % text)
                if block.text().contains(regex):
                    cursor = self.document().find(text, cursor)
                    if cursor.selectedText() == text:
                        cursor.removeSelectedText()
            block = block.next()
            if block.position() > end:
                break
        userCursor.endEditBlock()

    def updateSidepanel(self, panel, event):
        metrics = self.fontMetrics()
        line = self.document().findBlock(
        self.textCursor().position()).blockNumber() + 1

        block = self.firstVisibleBlock()
        count = block.blockNumber()
        painter = QPainter(panel)
        painter.fillRect(event.rect(), self.palette().base())

        # Iterate over all visible text blocks in the document.
        while block.isValid():
            count += 1
            top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
            # Check if the position of the block is out side of the visible
            # area.
            if not block.isVisible() or top >= event.rect().bottom():
                break
            # Draw the line number right justified at the position of the line
            rect = QRect(0, top, panel.width(), metrics.height())
            try:
                if block.userData().data() == PlainTextEdit.SYNTAX:
                    if block == self.textCursor().block():
                        pixmap = QPixmap(":mActionWarning.png")
                    else:
                        pixmap = QPixmap(":mActionError.png")
                    painter.drawPixmap(rect, pixmap)
                else:
                    painter.drawText(rect, Qt.AlignRight, unicode(count))
            except:
                painter.drawText(rect, Qt.AlignRight, unicode(count))
            block = block.next()
        painter.end()

    def mousePressEvent(self, e):
        cursor = self.textCursor()
        if e.button() == Qt.RightButton:
            actions = [[QIcon(":mActionEditCopy.png"),
                        "Copy", self.copy, QKeySequence(QKeySequence.Copy)],
                       [QIcon(":mActionEditSelectAll.png"),
                        "Select all", self.selectAll,
                        QKeySequence(QKeySequence.SelectAll)],
                       [QIcon(":mActionLogo.png"),
                        "Function keywords", self.insertParameters,
                        QKeySequence("Ctrl+P")],
                       [QIcon(":mActionEditPaste.png"),
                        "Paste", self.paste,
                        QKeySequence(QKeySequence.Paste)],
                       [QIcon(":mActionEditCut.png"),
                        "Cut", self.cut, QKeySequence(QKeySequence.Cut)]]
            menu = QMenu()
            if not cursor.hasSelection():
                actions = actions[1:]
            for args in actions:
                menu.addAction(*args)
            menu.exec_(e.globalPos())
        PlainTextEdit.mousePressEvent(self, e)

    def textChanged(self):
        self.checkSyntax(self.currentCommand(self.textCursor().block())[0])

class RConsole(PlainTextEdit):

    def __init__(self, parent=None, tabwidth=4, autobracket=True, prompts=(">","+")):
        PlainTextEdit.__init__(self, parent, tabwidth, autobracket)
        self.setUndoRedoEnabled(False)
        self.setPrompt(prompts[0],prompts[1])
        self.__HIST = History()
        self.__started = False
        self.__tabwidth = tabwidth

    def setHistory(self, history):
        self.__HIST = history

    def history(self):
        return self.__HIST

    def previous(self):
        self.navigateHistory(True)

    def next(self):
        self.navigateHistory(False)

    def navigateHistory(self, up=True):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        self.setTextCursor(cursor)
        if up:
            self.insertPlainText(self.history().previous())
        else:
            self.insertPlainText(self.history().next())

    def setPrompt(self, newPrompt=">", altPrompt="+"):
        self.defaultPrompt = newPrompt
        self.alternatePrompt = altPrompt
        self.currentPrompt = self.defaultPrompt

    def keyPressEvent(self, e):
        cursor = self.textCursor()
        if not self.isCursorInEditionZone():
            if e.modifiers() == Qt.ControlModifier or \
                e.modifiers() == Qt.MetaModifier:
                if e.key() == Qt.Key_C:
                    PlainTextEdit.keyPressEvent(self, e)
            else:
                cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
                self.setTextCursor(cursor)
        else:
            if e.key() == Qt.Key_C and (e.modifiers() == Qt.ControlModifier or \
                e.modifiers() == Qt.MetaModifier):
                self.cancel()
            elif e.key() == Qt.Key_Backspace:
                if not cursor.hasSelection() and cursor.atBlockStart():
                    return
                PlainTextEdit.keyPressEvent(self, e)
            elif e.key() == Qt.Key_Tab:
                if not cursor.hasSelection():
                    cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor)
                    text = cursor.selectedText().trimmed()
                    if not text.isEmpty():
                        self.emit(SIGNAL("requestSuggestion(int)"), 1)
                    else:
                        self.insertPlainText(" "*self.__tabwidth)
            elif e.key() == Qt.Key_Return:
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
                self.setTextCursor(cursor)
                self.insertPlainText("\n")
                self.entered()
            elif e.key() == Qt.Key_Down:
                self.navigateHistory(False)
            elif e.key() == Qt.Key_Up:
                self.navigateHistory(True)
            elif e.key() == Qt.Key_Left:
                if cursor.atBlockStart():
                    return
                PlainTextEdit.keyPressEvent(self, e)
            elif e.key() == Qt.Key_Home:
                if e.modifiers() == Qt.ShiftModifier:
                    cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
                else:
                    cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.MoveAnchor)
                self.setTextCursor(cursor)
            elif e.key() == Qt.Key_End:
                if e.modifiers() == Qt.ShiftModifier:
                    cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                else:
                    cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.MoveAnchor)
                self.setTextCursor(cursor)
            else:
                PlainTextEdit.keyPressEvent(self, e)
        self.ensureCursorVisible()

    def cancel(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        cursor.block().setUserData(UserData(PlainTextEdit.INPUT))
        self.setTextCursor(cursor)
        self.insertPlainText("\n")

    def entered(self):
        block = self.textCursor().block().previous()
        command = self.currentCommand(block)[0]
        check = self.checkSyntax(command, block)
        if not check == PlainTextEdit.OUTPUT:
            if not self.lastLine().isEmpty():
                self.history().update(QStringList(self.lastLine()))
            if check == PlainTextEdit.INPUT:
                self.run(command)
            elif check == PlainTextEdit.SYNTAX and block.userData().hasExtra():
                self.printOutput(block.userData().extra())
            self.emit(SIGNAL("commandComplete()"))
        return True

    def cut(self):
        if self.isCursorInEditionZone() and self.isAnchorInEditionZone():
            PlainTextEdit.cut(self)

    def run(self, command):
        lock = Lock()
        self.pipeStart, self.pipeEnd = Pipe()
        try:
            run(command, lock, self.pipeStart)
        except:
            return False
        try:
            output = self.pipeEnd.recv()
            string = QStringList()
            while not output is None:
                string.append(output)
                output = self.pipeEnd.recv()
        except EOFError:
            pass
        self.printOutput(string)
        return True

    def acceptCommands(self, commands):
        mime = QMimeData()
        if not QString(commands).endsWith("\n"):
            commands += "\n"
        mime.setText(commands)
        self.insertFromMimeData(mime)

    def printOutput(self, output):
        if not output.isEmpty():
            for line in output:
                if not line.isEmpty():
                    if line.startsWith("Error"):
                        line = line.split(":",
                        QString.SkipEmptyParts)[1:].join(" ").prepend("Error:")
                    self.textCursor().block().setUserData(
                    UserData(PlainTextEdit.OUTPUT, QString("Output")))
                    self.insertPlainText(line)
        #self.textCursor().block().setUserData(
            #UserData(PlainTextEdit.OUTPUT, QString("Output")))
        self.ensureCursorVisible()

    def mousePressEvent(self, e):
        cursor = self.textCursor()
        if e.button() == Qt.RightButton:
            actions = [[QIcon(":mActionEditCopy.png"),
                        "Copy", self.copy, QKeySequence(QKeySequence.Copy)],
                       [QIcon(":mActionEditSelectAll.png"),
                        "Select all", self.selectAll,
                        QKeySequence(QKeySequence.SelectAll)],
                       [QIcon(":mActionLogo.png"),
                        "Function keywords", self.insertParameters,
                        QKeySequence("Ctrl+P")],
                       [QIcon(":mActionEditPaste.png"),
                        "Paste", self.paste,
                        QKeySequence(QKeySequence.Paste)],
                       [QIcon(":mActionEditCut.png"),
                        "Cut", self.cut, QKeySequence(QKeySequence.Cut)]]
            menu = QMenu()
            if self.isCursorInEditionZone():
                if cursor.hasSelection() and self.isAnchorInEditionZone():
                    for kwargs in actions:
                        menu.addAction(*kwargs)
                elif cursor.hasSelection() and not self.isAnchorInEditionZone():
                    for kwargs in actions[0:3]:
                        menu.addAction(*kwargs)
                else:
                    for kwargs in actions[1:4]:
                        menu.addAction(*kwargs)
            else:
                if cursor.hasSelection():
                    for kwargs in actions[0:2]:
                        menu.addAction(*kwargs)
            menu.exec_(e.globalPos())
        PlainTextEdit.mousePressEvent(self, e)

    def isCursorInEditionZone(self):
        return self.textCursor().position() >= self.document().lastBlock().position()

    def isAnchorInEditionZone(self):
        return self.textCursor().anchor() >= self.document().lastBlock().position()

    def updateSidepanel(self, panel, event):
        metrics = self.fontMetrics()
        block = self.firstVisibleBlock()
        count = block.blockNumber()
        painter = QPainter(panel)
        painter.fillRect(event.rect(), self.palette().base())
        while block.isValid():
            count += 1
            prompt = self.defaultPrompt
            prev = block.previous().userData()
            curr = block.userData()
            try:
                if not curr is None:
                    if curr.data() == PlainTextEdit.OUTPUT:
                        prompt = QString(" ")
                if not prev is None:
                    if prev.data() == PlainTextEdit.CONTINUE: # continuation prompt
                        prompt = self.alternatePrompt
            except:
                pass
            top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
            rect = QRect(0, top, panel.width(), metrics.height())
            if not block.isVisible() or top >= event.rect().bottom():
                break
            rect = QRect(0, top, panel.width(), metrics.height())
            painter.drawText(rect, Qt.AlignRight, unicode(prompt))
            block = block.next()
        painter.end()

class SidePanel(QWidget):

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        self.parent = parent
        self.adjustWidth(1)
        #self.setFocusProxy(parent)

    def paintEvent(self, event):
        self.parent.updateSidepanel(self, event)
        QWidget.paintEvent(self, event)

    def adjustWidth(self, count):
        if count < 10:
            count += 10
        width = self.fontMetrics().width(unicode(count))
        if self.width() != width:
            self.setFixedWidth(width)

    def updateContents(self, rect, scroll):
        if scroll:
            self.scroll(0, scroll)
        else:
            # It would be nice to do
            self.update(0, rect.y(), self.width(), rect.height())
            # But we can't because it will not remove the bold on the
            # current line if word wrap is enabled and a new block is
            # selected.
            #self.update()

    def event(self, e):
        if e.type() == QEvent.ToolTip:
            cursor = self.parent.cursorForPosition(QPoint(0,e.y()))
            block = cursor.block()
            data = block.userData()
            try:
                if data.hasExtra(): # normally only do this if we have a syntax error
                    #output = QString(data.extra()).split(":",
                    #QString.SkipEmptyParts)[1:].join(" ").prepend("Error:")
                    QToolTip.showText(e.globalPos(), data.extra())
            except:
                pass
        return QWidget.event(self, e)

class SearchBar(QWidget):

    def __init__(self, parent, replace=True):
        QWidget.__init__(self, parent)
        # get a reference to the input document
        # Note: might not be the same as parent
        self.editor = parent
        self.document = self.editor.document()
        self.allowReplace = replace
        # create search elements
        findLabel = QLabel("Find:")
        findLabel.setMaximumWidth(50)
        self.closeButton = QToolButton(self)
        self.closeButton.setText("Close")
        self.closeButton.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.closeButton.setIcon(QIcon(":mActionFileClose.png"))
        self.closeButton.setToolTip("Close search bar")
        self.searchEdit = QLineEdit(self)
        self.searchEdit.setToolTip("Find text")
        self.nextButton = QToolButton(self)
        self.nextButton.setText("Next")
        self.nextButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.nextButton.setIcon(QIcon(":mActionNext.png"))
        self.nextButton.setToolTip("Find next")
        self.previousButton = QToolButton(self)
        self.previousButton.setToolTip("Find previous")
        self.previousButton.setText("Previous")
        self.previousButton.setIcon(QIcon(":mActionPrevious.png"))
        self.previousButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.wholeCheckbox = QCheckBox()
        self.wholeCheckbox.setText("Whole words")
        self.caseCheckbox = QCheckBox()
        self.caseCheckbox.setText("Case sensitive")
        # add search elements to widget
        grid = QGridLayout(self)
        grid.addWidget(findLabel,1,0,1,1)
        grid.addWidget(self.searchEdit, 1,1,1,2)
        grid.addWidget(self.closeButton, 0,0,1,1)
        grid.addWidget(self.nextButton, 1,3,1,1)
        grid.addWidget(self.previousButton, 1,4,1,1)
        grid.addWidget(self.wholeCheckbox, 0,3,1,1)
        grid.addWidget(self.caseCheckbox, 0,4,1,1)
        # create replace elements
        self.replaceLabel = QLabel("Replace:")
        self.replaceLabel.setMaximumWidth(80)
        self.replaceEdit = QLineEdit(self)
        self.replaceEdit.setToolTip("Replace text")
        self.replaceButton = QToolButton(self)
        self.replaceButton.setText("Replace")
        self.replaceButton.setToolTip("Replace text")
        self.allButton = QToolButton(self)
        self.allButton.setToolTip("Replace all")
        self.allButton.setText("Replace all")
        # add replace elements to widget
        grid.addWidget(self.replaceLabel, 2, 0, 1, 1)
        grid.addWidget(self.replaceEdit, 2, 1, 1, 2)
        grid.addWidget(self.replaceButton, 2, 3, 1, 1)
        grid.addWidget(self.allButton, 2, 4, 1, 1)
        self.setFocusProxy(self.searchEdit)
        self.hide()
        # setup connections
        self.connect(self.nextButton, SIGNAL("clicked()"), self.findNext)
        self.connect(self.previousButton, SIGNAL("clicked()"), self.findPrevious)
        self.connect(self.replaceButton, SIGNAL("clicked()"), self.replaceNext)
        self.connect(self.searchEdit, SIGNAL("returnPressed()"), self.findNext)
        self.connect(self.allButton, SIGNAL("clicked()"), self.replaceAll)
        self.connect(self.closeButton, SIGNAL("clicked()"), self.hide)

    def toggleFind(self):
        text = self.editor.textCursor().selectedText()
        if not text.isEmpty():
            self.searchEdit.setText(text)
            if self.isVisible():
                return
        if not self.isVisible():
            self.show(False)
        else:
            self.hide()

    def toggleReplace(self):
        text = self.editor.textCursor().selectedText()
        if not text.isEmpty():
            self.searchEdit.setText(text)
            if self.isVisible():
                return
        if not self.isVisible():
            self.show(True)
        else:
            self.hide()

    def show(self, replace=False):
        self.setVisible(True)
        if replace and self.allowReplace:
            self.showReplace()
        else:
            self.hideReplace()

    def hide(self):
        self.setVisible(False)

    def find(self, forward):
        if not self.document:
            return False
        text = QString(self.searchEdit.text())
        found = False
        if text == "":
            return False
        else:
            flags = QTextDocument.FindFlag()
            if self.wholeCheckbox.isChecked():
                flags = (flags|QTextDocument.FindWholeWords)
            if self.caseCheckbox.isChecked():
                flags = (flags|QTextDocument.FindCaseSensitively)
            if not forward:
                flags = (flags|QTextDocument.FindBackward)

            cursor = QTextCursor(self.editor.textCursor())
            tmpcursor = QTextCursor(cursor)
            cursor = self.document.find(text, cursor, flags)
            if cursor.isNull():
                cursor = tmpcursor
                if forward:
                    cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor)
                else:
                    cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
                cursor = self.document.find(text, cursor, flags)
                if not cursor.isNull():
                    self.editor.setTextCursor(cursor)
                    return True
                return False
            else:
                self.editor.setTextCursor(cursor)
                return True
        return False

    def findNext(self):
        return self.find(True)

    def findPrevious(self):
        return self.find(False)

    def showReplace(self):
        self.replaceEdit.setVisible(True)
        self.replaceButton.setVisible(True)
        self.allButton.setVisible(True)
        self.replaceLabel.setVisible(True)

    def hideReplace(self):
        self.replaceEdit.setVisible(False)
        self.replaceButton.setVisible(False)
        self.allButton.setVisible(False)
        self.replaceLabel.setVisible(False)

    def replaceNext(self):
        cursor = QTextCursor(self.editor.textCursor())
        selection = cursor.hasSelection()
        if selection:
            text = QString(cursor.selectedText())
            current = QString(self.searchEdit.text())
            replace = QString(self.replaceEdit.text())
            if text == current:
                cursor.insertText(replace)
                cursor.select(QTextCursor.WordUnderCursor)
        else:
            return self.findNext()
        self.findNext()
        return True

    def replaceAll(self):
        while self.findNext():
            self.replaceNext()
        self.replaceNext()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.parent.setFocus()

class CompletePopup(QObject):

    def __init__(self, parent, delay=500, minchars=3):
        QObject.__init__(self, parent)
        self.editor = parent
        self.popup = QTreeWidget()
        self.popup.setColumnCount(1)
        self.popup.setUniformRowHeights(True)
        self.popup.setRootIsDecorated(False)
        self.popup.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.popup.setSelectionBehavior(QTreeWidget.SelectRows)
        self.popup.setFrameStyle(QFrame.Box|QFrame.Plain)
        self.popup.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.popup.header().hide()
        self.popup.installEventFilter(self)
        self.popup.setMouseTracking(True)
        self.connect(self.popup, SIGNAL("itemClicked(QTreeWidgetItem*, int)"),
                     self.doneCompletion)
        self.popup.setWindowFlags(Qt.Popup)
        self.popup.setFocusPolicy(Qt.NoFocus)
        self.popup.setFocusProxy(self.editor)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        if isinstance(delay,int):
            self.timer.setInterval(delay)
        else:
            self.timer.setInterval(500)
        self.currentItem = ""
        #self.DICT = Dictionary()
        self.connect(self.timer, SIGNAL("timeout()"), self.suggest, minchars)
        self.connect(self.editor, SIGNAL("textChanged()"), self.startTimer)

    #def setDictionary(self, dictionary):
        #self.DICT = dictionary

    def startTimer(self):
        self.timer.start()

    def eventFilter(self, obj, ev):
        if not obj == self.popup:
            return False
        if ev.type() == QEvent.MouseButtonPress:
            self.popup.hide()
            self.editor.setFocus()
            return True
        if ev.type() == QEvent.KeyPress:
            consumed = False
            key = ev.key()
            if key == Qt.Key_Enter or \
            key == Qt.Key_Return:
                self.doneCompletion()
                consumed = True
            elif key == Qt.Key_Escape:
                self.editor.setFocus()
                self.popup.hide()
                consumed = True
            elif key == Qt.Key_Up or \
            key == Qt.Key_Down or \
            key == Qt.Key_Home or \
            key == Qt.Key_End or \
            key == Qt.Key_PageUp or \
            key == Qt.Key_PageDown:
                pass
            else:
                self.editor.setFocus()
                self.editor.event(ev)
                self.popup.hide()
            return consumed
        return False

    def showCompletion(self, choices, start, end):
        if len(choices) < 1:
            return

        pal = self.editor.palette()
        color = pal.color(QPalette.Disabled,
                          QPalette.WindowText)
        self.popup.setUpdatesEnabled(False)
        self.popup.clear()
        for i in choices:
            item = QTreeWidgetItem(self.popup)
            #item.setText(0, i.split(":")[0].simplified())
            item.setText(0, i)
            try:
                item.setData(0, Qt.StatusTipRole, QVariant(i))
                #QVariant(i.split(":")[1].simplified()))
            except:
                pass
        self.popup.setCurrentItem(self.popup.topLevelItem(0))
        self.popup.resizeColumnToContents(0)
        self.popup.adjustSize()
        self.popup.setUpdatesEnabled(True)

        h = self.popup.sizeHintForRow(0)*min([7, len(choices)])+3
        self.popup.resize(self.popup.width(), h)

        self.popup.move(self.editor.mapToGlobal(self.editor.cursorRect().bottomRight()))
        self.popup.setFocus()
        self.popup.show()
        self.start = start
        self.end = end

    def doneCompletion(self):
        self.timer.stop()
        self.popup.hide()
        self.editor.setFocus()
        item = self.popup.currentItem()
        #self.editor.parent.statusBar().showMessage(
        #item.data(0, Qt.StatusTipRole).toString().\
        #replace("function", item.text(0)))
        if item:
            self.replaceCurrentWord(item.text(0))
            self.preventSuggest()
            self.setCurrentItem(item)
            self.emit(SIGNAL("doneCompletion(QString, QString)"),
            QString(unicode(item.text(0))),QString())

    def setCurrentItem(self, item):
        self.currentItem = item

    def currentItem(self):
        return self.currentItem

    def preventSuggest(self):
        self.timer.stop()

    def suggest(self, minchars=3):
        block = self.editor.textCursor().block()
        text = block.text()
        if len(text) < minchars:
            return
        command = self.editor.currentCommand(block)
        linebuffer = command[0]
        if QString(linebuffer).trimmed().isEmpty():
            return
        cursor = command[1]
        token, start, end = complete.guessTokenFromLine(linebuffer, cursor-1)
        if len(token) < minchars:
            return
        comps = complete.completeToken(linebuffer, token, start, end)
        self.showCompletion(comps, start, end)

    #def getCurrentWord(self):
        #textCursor = self.editor.textCursor()
        #textCursor.movePosition(QTextCursor.StartOfWord, QTextCursor.KeepAnchor)
        #currentWord = textCursor.selectedText()
        #textCursor.setPosition(textCursor.anchor(), QTextCursor.MoveAnchor)
        #return currentWord

    def replaceCurrentWord(self, word):
        textCursor = self.editor.textCursor()
        textCursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, self.end-self.start)
        textCursor.removeSelectedText()
        self.editor.setTextCursor(textCursor)
        self.editor.insertPlainText(word)


class BaseFrame(QFrame):

    def __init__(self, parent=None, tabwidth=4, autobracket=True,
                 autopopup=True, sidepanel=True, console=True):
        QFrame.__init__(self, parent)
        if console:
            self.edit = RConsole(self)
        else:
            self.edit = REditor(self)
        self.searchBar = SearchBar(self.edit, (not console))
        self.completePopup = CompletePopup(self.edit)
        if autopopup:
            self.connect(self.completePopup,
            SIGNAL("doneCompletion(QString, QString)"), self.doneCompletion)
            self.connect(self.edit,
            SIGNAL("requestSuggestion(int)"), self.completer().suggest)

        self.sidePanel = SidePanel(self.edit)
        if sidepanel:
            self.connect(self.edit, SIGNAL("blockCountChanged(int)"),
                self.sidePanel.adjustWidth)
            self.connect(self.edit, SIGNAL("updateRequest(QRect, int)"),
                self.sidePanel.updateContents)
        hbox = QHBoxLayout()
        hbox.addWidget(self.sidePanel)
        hbox.addWidget(self.edit)
        if console:
            hbox.setSpacing(0)
        else:
            hbox.setSpacing(2)
        hbox.setMargin(0)
        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox)
        vbox.addWidget(self.searchBar)
        self.setFocusProxy(self.edit)

    def toggleSearch(self):
        self.search().toggleFind()

    def toggleReplace(self):
        self.search().toggleReplace()

    def doneCompletion(self, word, extra):
        self.emit(SIGNAL("doneCompletion(QString, QString)"), word, extra)

    def editor(self):
        return self.edit

    def completer(self):
        return self.completePopup

    def panel(self):
        return self.sidePanel

    def search(self):
        return self.searchBar

#------------------------------------------------------------------------------#
#---------------------------- Browsers and Dialogs ----------------------------#
#------------------------------------------------------------------------------#


class AboutBrowser(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        iconLabel = QLabel()
        icon = QPixmap(":mActionLogo.png")
        iconLabel.setPixmap(icon)
        nameLabel = QLabel(
            "<font size=8 color=#0066CC>&nbsp;<b>manageR</b></font>")
        versionLabel = QLabel(
            "<font color=#0066CC>%s on %s<br>manageR %s</font>" % (
            robjects.r.version[12][0], sys.platform, VERSION))
        aboutBrowser = QTextBrowser()
        aboutBrowser.setOpenExternalLinks(True)
        aboutBrowser.setHtml(
            "<h3>Interface to the R statistical programming environment</h3>"
            "Copyright &copy; 2009-2010 Carson J. Q. Farmer"
            "<br/>Carson.Farmer@gmail.com"
            "<br/><a href='http://www.ftools.ca/manageR'>http://www.ftools.ca/manageR</a>")
        licenseBrowser = QTextBrowser()
        licenseBrowser.setOpenExternalLinks(True)
        licenseBrowser.setHtml((LICENSE.replace("\n\n", "<p>").replace("(C)", "&copy;"))) 
        helpBrowser = QTextBrowser()
        helpBrowser.setOpenExternalLinks(False)
        helpBrowser.setHtml(
            "<center><h2>manageR version %s documentation</h2>"
            "<h3>Interface to the R statistical programming environment</h3>"
            "<h4>Copyright &copy; 2009 Carson J.Q. Farmer"
            "<br/>carson.farmer@gmail.com"
            "<br/><a href='http://www.ftools.ca/manageR'>www.ftools.ca/manageR</a></h4></center>"
            "<h4>Description:</h4>"
            "<b>manageR</b> adds comprehensive statistical capabilities to ..."
            "<h4>Features:</h4>"
            "<ul><li>Syntax highlighting</li><li>Minimal R script editor</li><li>Code checking/debuging</li>"
            "<li>Extensible GUI for common R functions</li>"
            "<li>Aides in building complex R scripts via an integrated console and editor</li>"
            "<li>Tools and widgets for exploring the R workspace, history, file system, working directory, "
            "plotting devices, library, help system, and online package repository</li></ul>"
            "<h4>Usage:</h4>"
            "<p>Use <tt>Ctrl+Return</tt> to send commands from an <b>EditR</b> window to the <b>manageR</b>"
            "console. If an <b>EditR</b> window contains selected text, only this text will be sent"
            "to the <b>manageR</b> console, otherwise, all text is sent. The <b>EditR</b> window"
            "also contains tools for creating, loading, editing, and saving R scripts. The suite of"
            "available tools is outlined in detail in the <b>Key bindings</b> section.</p>"
            "<p><i>Autocompletion</i><br>"
            "If enabled, command completion suggestions are automatically shown after a given time interval"
            "based on the current work. This can also be manually activated using <b>Ctrl+Space</b>."
            "In addition, a tooltip will appear if one is available for the selected command."
            "It is possible to turn off autocompletion (and tooltips)"
            "by unchecking File &rarr; Configure &rarr;"
            "General tab &rarr; Enable autocompletion.</p>"
            "<p><i>Search and Replace</i><br>"
            "A Search and Replace toolbar is available for both the <b>manageR</b> console and <b>EditR</b>"
            "window (the replace functionality is only available in <b>EditR</b>). When activated (see"
            "<b>Key Bindings</b> section below), if any text is selected in the parent dialog, this text"
            "will be placed in the 'Find toolbar' for searching. To search for"
            "the next occurrence of the text or phrase in the toolbar, type <tt>Enter</tt>"
            "or click the 'Next' button. Conversely, click the 'Previous' button to search backwards. To"
            "replace text as it is found, simply type the replacement text in the 'Replace' line edit and"
            "click 'Replace'. To replace all occurrences of the found text, click 'Replace all'. All"
            "searches can be refined by using the 'Case sensitive' and 'Whole words' check boxes.</p>"
            "<p><i>Workspace Manager</i></i><br>"
            "The Workspace Tree displays the name, type, and dimentions f all currently loaded variables "
            "in your global R environment (globalEnv). From here, it is possible to remove, save, and load "
            "R variables, as well as export R variables to file.</p>"
            "<p><i>Graphic Device Manager</i><br>"
            "The graphic devices table stores the ID and device type of all current R graphic devices. From here,"
            "it is possible to refresh the list of graphic devices, create a new empty graphic window, and remove"
            "existing devices. In addition, it is possible to export the selected graphic device to file in both raster"
            "and vector formats.</p>"
            "<p><i>History Manager</i><br>"
            "The command history displays a list of all previously executed commands (including commands loaded from a"
            ".RHistory file). From here it is possible to run a command in the <b>manageR</b> console by"
            "double clicking an item. Similarly, multiple commands can be selected, and copied"
            "using the popup menu. Individual commands can be selected or unselected simply by"
            "clicking on them using the left mouse button. To run all selected commands, right click anywhere within"
            "the command history widget, and select run from the popup menu.</p>"
            "<p><i>Working Directory Browser</i><br>"
            "The working directory widget is a simple toolbar to help browse to different working directories, making it"
            "simple to change the current R working directory.</p>"
            "<p><i>File System Browser</i><br>"
            "The file system browser widget is a simple tool to help browse to different directories, making it"
            "simple to view, load, delete, and manage your folders.</p>"
            "<p><i>Analysis</i><br>"
            "<b>manageR</b> supports simple plugins which help to streamline tedious R functions by providing a"
            "plugin framework for creating simple graphical user interfaces (GUI) to commonly used R functions."
            "These functions can be specified using an XML ('tools.xml') file stored in the <b>manageR</b>"
            "installation folder (%s). The format of the XML file should be as follows:"
            "<font color=green><i>"
            "<pre>&lt;?xml version='1.0'?&gt;"
            "&lt;manageRTools&gt;<br>"
            "  &lt;RTool name='Insert random R commands' query='|1|'&gt;<br>"
            "    &lt;Parameter label='R commands:' type='textEdit' default='ls()' notnull='true'/&gt;<br>"
            "  &lt;/RTool&gt;<br>"
            "&lt;manageRTools&gt;</i></font></pre>"
            "where each RTool specifies a unique R function. In the above example, the GUI will consist of a simple"
            "dialog with a text editing region to input user-defined R commands, and an OK and CLOSE button. When"
            "OK is clicked, the R commands in the text editing region will be run, and when CLOSE is clicked,"
            "the dialog will be closed. In the example above, query is set to <tt>|1|</tt>, which means take the"
            "output from the first parameter, and place here. In other words, in this case the entire query is"
            "equal to whatever is input into the text editing region (default here is <tt>ls()</tt>). Other GUI"
            "parameters that may be entered include:"
            "<ul><li>comboBox: Drop-down list box</li><li>doubleSpinBox: Widget for entering numerical values</li>"
            "<li>textEdit: Text editing region</li>"
            "<li>spComboBox: Combobox widget for displaying a dropdown list of variables (e.g. numeric,"
            "data.frame, Spatial*DataFrame)</li>"
            "<li>spListWidget: Widget for displaying lists of variables (e.g. numeric, data.frame, Spatial*DataFrame)</li>"
            "<li>helpString: Non-graphical parameter that is linked to the help button on the dialog"
            "(can use 'topic:help_topic' or custom html based help text)</li></ul>"
            "Default values for all of the above GUI parameters can be specified in the XML file, using semi-colons"
            "to separate multiple options. For the spComboBox, the default string should specify the type(s) of"
            "variables to display (e.g. numeric;data,frame;SpatialPointsDataFrame)."
            "<b>manageR</b> comes with several default R GUI functions which can be used as examples for creating"
            "custom R functions.</p>"
            "<h4>Key bindings:</h4>"
            "<ul>"
            "<li><tt>&uarr;</tt> : In the <b>manageR</b> console, show the previous command"
            "from the command history. In the <b>EditR</b> windows, move up one line."
            "<li><tt>&darr;</tt> : In the <b>manageR</b> console, show the next command"
            "from the command history. In the <b>EditR</b> windows, move down one line."
            "<li><tt>&larr;</tt> : Move the cursor left one character"
            "<li><tt>Ctrl+&larr;</tt> : Move the cursor left one word"
            "<li><tt>&rarr;</tt> : Move the cursor right one character"
            "<li><tt>Ctrl+&rarr;</tt> : Move the cursor right one word"
            "<li><tt>Tab</tt> : Indent the selected text (or the current line)"
            "<li><tt>Shift+Tab</tt> : Unindent the selected text (or the current line)"
            "<li><tt>Ctrl+A</tt> : Select all the text"
            "<li><tt>Backspace</tt> : Delete the character to the left of the cursor"
            "<li><tt>Ctrl+C</tt> : In the <b>manageR</b> console, if the cursor is in the command line, clear"
            "current command(s), otherwise copy the selected text to the clipboard (same for <b>EditR</b>"
            "windows."
            "<li><tt>Delete</tt> : Delete the character to the right of the cursor"
            "<li><tt>End</tt> : Move the cursor to the end of the line"
            "<li><tt>Ctrl+End</tt> : Move the cursor to the end of the file"
            "<li><tt>Ctrl+Return</tt> : In an <b>EditR</b> window, execute the (selected) code/text"
            "<li><tt>Ctrl+F</tt> : Pop up the Find toolbar"
            "<li><tt>Ctrl+R</tt> : In an <b>EditR</b> window, pop up the Find and Replace toolbar"
            "<li><tt>Home</tt> : Move the cursor to the beginning of the line"
            "<li><tt>Ctrl+Home</tt> : Move the cursor to the beginning of the file"
            "<li><tt>Ctrl+K</tt> : Delete to the end of the line"
            "<li><tt>Ctrl+G</tt> : Pop up the 'Goto line' dialog"
            "<li><tt>Ctrl+N</tt> : Open a new editor window"
            "<li><tt>Ctrl+O</tt> : Open a file open dialog to open an R script"
            "<li><tt>Ctrl+Space</tt> : Pop up a list of possible completions for"
            "the current word. Use the up and down arrow keys and the page up and page"
            "up keys (or the mouse) to navigate; click <tt>Enter</tt> to accept a"
            "completion or <tt>Esc</tt> to cancel."
            "<li><tt>PageUp</tt> : Move up one screen"
            "<li><tt>PageDown</tt> : Move down one screen"
            "<li><tt>Ctrl+Q</tt> : Terminate manageR; prompting to save any unsaved changes"
            "for every <b>EditR</b> window for which this is necessary. If the user cancels"
            "any 'save unsaved changes' message box, manageR will not terminate."
            "<li><tt>Ctrl+S</tt> : Save the current file"
            "<li><tt>Ctrl+V</tt> : Paste the clipboards text"
            "<li><tt>Ctrl+W</tt> : Close the current file; prompting to save any unsaved"
            "changes if necessary"
            "<li><tt>Ctrl+X</tt> : Cut the selected text to the clipboard"
            "<li><tt>Ctrl+Z</tt> : Undo the last editing action"
            "<li><tt>Ctrl+Shift+Z</tt> : Redo the last editing action</ul>"
            "Hold down <tt>Shift</tt> when pressing movement keys to select the text moved over.<br>" % (VERSION, CURRENTDIR))

        tabWidget = QTabWidget()
        tabWidget.addTab(aboutBrowser, "&About")
        tabWidget.addTab(licenseBrowser, "&License")
        tabWidget.addTab(helpBrowser, "&Help")
        okButton = QPushButton("OK")

        layout = QVBoxLayout(self)
        hbox = QHBoxLayout()
        hbox.addWidget(iconLabel)
        hbox.addWidget(nameLabel)
        hbox.addStretch()
        hbox.addWidget(versionLabel)
        layout.addLayout(hbox)
        layout.addWidget(tabWidget)
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(okButton)
        hbox.addStretch()
        layout.addLayout(hbox)

        self.setMinimumSize(min(self.width(),
            int(QApplication.desktop().availableGeometry().width() / 2)),
            int(QApplication.desktop().availableGeometry().height() / 2))
        self.connect(okButton, SIGNAL("clicked()"), self.accept)
        self.setWindowTitle("manageR - About")

class RMirrorBrowser(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        m = robjects.r.getCRANmirrors(all=False, local_only=False)
        names = QStringList(list(m.rx('Name')[0]))
        urls = list(m.rx('URL')[0])
        self.links = dict(zip(names, urls))
        names = QStringList(names)
        self.setWindowTitle("manageR - Choose CRAN Mirror")
        self.setWindowIcon(QIcon(":mActionIcon"))
        self.links = dict(zip(names, urls))
        self.currentMirror = None
        self.mirrorList = QListWidget(self)
        self.mirrorList.setAlternatingRowColors(True)
        self.mirrorList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mirrorList.setSortingEnabled(True)
        self.mirrorList.setSelectionMode(QAbstractItemView.SingleSelection)
        self.mirrorList.setToolTip("Double-click to select mirror location")
        self.mirrorList.setWhatsThis("List of CRAN mirrors")
        self.mirrorList.insertItems(0, names)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.mirrorList)
        vbox.addWidget(buttonBox)

        self.connect(buttonBox, SIGNAL("accepted()"), self.accept)
        self.connect(buttonBox, SIGNAL("rejected()"), self.reject)
        self.connect(self.mirrorList,
            SIGNAL("itemDoubleClicked(QListWidgetItem*)"), self.accept)

    def currentMirror(self):
        return robjects.r("getOption('repos')")[0]

    def setCurrentMirror(self, mirror):
        robjects.r("options('repos'='%s')" % mirror)

    def accept(self):
        items = self.mirrorList.selectedItems()
        if len(items) > 0:
            name = items[0].text()
            url = self.links[name]
            self.setCurrentMirror(url)
            QDialog.accept(self)
        else:
            QMessageBox.warning(self, "manageR - Warning",
                "Please choose a valid CRAN mirror")

class RRepositoryBrowser(QDialog):
  
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        mirror = robjects.r.getOption('repos')
        contrib_url = robjects.r.get('contrib.url', mode='function')
        available_packages = robjects.r.get('available.packages', mode='function')
        self.setWindowTitle("manageR - Install R Packages")
        self.setWindowIcon(QIcon(":mActionIcon"))
        p = available_packages()
        self.names = QStringList(p.rownames)
        self.parent = parent
        self.packageList = QListWidget(self)
        self.packageList.setAlternatingRowColors(True)
        self.packageList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.packageList.setSortingEnabled(True)
        self.packageList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.packageList.setToolTip("Select packages to install")
        self.packageList.setWhatsThis("List of packages available on CRAN")
        self.packageList.insertItems(0, self.names)
        self.dependCheckbox = QCheckBox(self)
        self.dependCheckbox.setText("Install all dependencies")
        self.dependCheckbox.setChecked(True)
        self.closeCheckbox = QCheckBox(self)
        self.closeCheckbox.setText("Close dialog on completion")
        self.closeCheckbox.setChecked(False)
        filterEdit = QLineEdit(self)
        filterLabel = QLabel("Filter packages", self)
        self.outputEdit = QTextEdit(self)
        self.outputEdit.setReadOnly(True)
        self.outputEdit.setVisible(False)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Apply|QDialogButtonBox.Close)
        self.buttonBox.addButton("Details >>", QDialogButtonBox.ActionRole)
        vbox = QVBoxLayout(self)
        hbox = QHBoxLayout()
        hbox.addWidget(filterLabel)
        hbox.addWidget(filterEdit)
        vbox.addLayout(hbox)
        vbox.addWidget(self.dependCheckbox)
        vbox.addWidget(self.packageList)
        vbox.addWidget(self.closeCheckbox)
        vbox.addWidget(self.outputEdit)
        vbox.addWidget(self.buttonBox)
        self.started = False
        self.setMinimumSize(80,50)

        self.connect(filterEdit, SIGNAL("textChanged(QString)"), self.filterPackages)
        #self.connect(self.buttonBox, SIGNAL("rejected()"), self.reject)
        self.connect(self.buttonBox, SIGNAL("clicked(QAbstractButton*)"), self.buttonClicked)

    def buttonClicked(self, button):
        if button.text() == "Details >>":
            self.showDetails()
            button.setText("Details <<")
        elif button.text() == "Details <<":
            self.hideDetails()
            button.setText("Details >>")
        elif self.buttonBox.standardButton(button) == QDialogButtonBox.Apply:
            self.installPackages()
        else:
            self.reject()

    def showDetails(self):
        self.outputEdit.setVisible(True)

    def hideDetails(self):
        self.outputEdit.setVisible(False)

    def filterPackages(self, text):
        self.packageList.clear()
        self.packageList.insertItems(0, self.names.filter(QRegExp(r"^%s" % text)))
        firstItem = self.packageList.item(0)
        if firstItem.text().startsWith(text):
            self.packageList.setCurrentItem(firstItem)
        else:
            self.packageList.clearSelection()

    def currentPackages(self):
        return [unicode(item.text()) for item in self.packageList.selectedItems()]

    def installPackages(self):
        pkgs = self.currentPackages()
        count = len(pkgs)
        if count < 1:
            QMessageBox.warning(self, "manageR - Warning",
            "Please choose at least one valid package")
            return False
        pkgs = QStringList(pkgs).join("','")
        checked = self.dependCheckbox.isChecked()
        if checked: depends = "TRUE"
        else: depends = "FALSE"
        lock = Lock()
        self.pipeStart, self.pipeEnd = Pipe()
        self.p = Process(target = run, args = (
        "install.packages(c('%s'), dependencies=%s)" % (pkgs, depends),
        lock, self.pipeStart))
        self.p.start()
        self.startTimer(30)
        self.started = True
        return True

    def timerEvent(self, e):
        if self.started:
            try:
                output = self.pipeEnd.recv()
                if not output is None:
                    self.printOutput(output)
                else:
                    self.p.join()
                    self.started = False
                    self.killTimer(e.timerId())
                    if self.closeCheckbox.isChecked():
                        self.reject()
            except EOFError:
                pass
        else:
            self.killTimer(e.timerId())
        QApplication.processEvents()

    def printOutput(self, output):
        self.outputEdit.insertPlainText(output)
        self.outputEdit.ensureCursorVisible()

class RHelpBrowser(QDialog):
    def __init__(self, parent=None, paths=None):
        QDialog.__init__(self, parent)
        QShortcut(QKeySequence("Escape"), self, self.reject)
        self.setWindowTitle("manageR - Help Browser")
        self.resize(500, 500)
        port = robjects.r('tools:::httpdPort')[0]
        if not port > 0:
            robjects.r('tools::startDynamicHelp()')
            port = robjects.r('tools:::httpdPort')[0]
        host = "localhost"
        home = "/doc/html/Search.html"
        self.htmlBrowser = HtmlBrowser(self, host, port, home, paths)
        self.checkboxes = []
        self.titleCheckbox = QCheckBox("Help page titles", self)
        self.titleCheckbox.setChecked(True)
        self.checkboxes.append(self.titleCheckbox)
        self.keywordsCheckbox = QCheckBox("Keywords", self)
        self.keywordsCheckbox.setChecked(True)
        self.checkboxes.append(self.keywordsCheckbox)
        self.aliasCheckbox = QCheckBox("Object names", self)
        self.aliasCheckbox.setChecked(True)
        self.checkboxes.append(self.aliasCheckbox)
        self.conceptCheckbox = QCheckBox("Concepts", self)
        self.conceptCheckbox.setChecked(False)
        self.checkboxes.append(self.conceptCheckbox)
        self.exactCheckbox = QCheckBox("Exact match", self)
        self.exactCheckbox.setChecked(False)
        self.checkboxes.append(self.exactCheckbox)
        self.searchButton = QPushButton("Search", self)
        self.searchEdit = QLineEdit(self)
        self.htmlBrowser.setSource(QUrl(home))

        vbox = QVBoxLayout(self)
        hbox = QHBoxLayout()
        hbox.addWidget(self.searchEdit)
        hbox.addWidget(self.searchButton)
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addStretch()
        for checkbox in self.checkboxes[0:3]:
            hbox.addWidget(checkbox)
        hbox.addStretch()
        parameters = QGroupBox("Search Parameters")
        parameters.setLayout(hbox)
        vbox.addWidget(parameters)
        hbox = QHBoxLayout()
        hbox.addStretch()
        for checkbox in self.checkboxes[3:]:
            hbox.addWidget(checkbox)
        hbox.addStretch()
        vbox.addLayout(hbox)
        vbox.addWidget(self.htmlBrowser)

        self.connect(self.searchButton, SIGNAL("clicked()"), self.search)
        self.connect(self.searchEdit, SIGNAL("returnPressed()"), self.search)

    def search(self):
        name = self.searchEdit.text()
        if not name.isEmpty():
            searchString = "Search?name=%s" % name
            if self.titleCheckbox.isChecked():
                searchString += "&title=1"
            if self.keywordsCheckbox.isChecked():
                searchString += "&keyword=1"
            if self.aliasCheckbox.isChecked():
                searchString += "&alias=1"
            if self.conceptCheckbox.isChecked():
                searchString += "&concept=1"
            if self.exactCheckbox.isChecked():
                searchString += "&exact=1"
            self.htmlBrowser.setSource(QUrl(searchString))

class RLibraryBrowser(QDialog):

    def __init__(self, parent=None, paths=None):
        QDialog.__init__(self, parent)
        QShortcut(QKeySequence("Escape"), self, self.reject)
        self.setWindowTitle("manageR - Library Browser")
        self.resize(500, 500)
        port = robjects.r('tools:::httpdPort')[0]
        if not port > 0:
            robjects.r('tools::startDynamicHelp()')
            port = robjects.r('tools:::httpdPort')[0]
        robjects.r("""make.packages.html()""")
        host = "localhost"
        home = "/doc/html/packages.html"
        #splitter = QSplitter(self)
        #splitter.setOrientation(Qt.Vertical)
        #splitter.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        labels = QStringList(["Loaded", "Package",
                              "Title",  "Path"])
        self.parent = parent
        self.home = home
        self.packageTable = QTableWidget(0, 4, self)
        self.htmlViewer = HtmlBrowser(self, host, port, home, paths)
        #splitter.addWidget(self.packageTable)
        #splitter.addWidget(self.htmlViewer)
        vbox = QVBoxLayout(self)
        #hbox.addWidget(splitter)
        vbox.addWidget(self.packageTable)
        vbox.addWidget(self.htmlViewer)
        self.packageTable.setHorizontalHeaderLabels(labels)
        self.packageTable.setShowGrid(True)
        self.packageTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.packageTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.packageTable.setAlternatingRowColors(True)
        self.updatePackages()
        self.connect(self.packageTable,
            SIGNAL("itemChanged(QTableWidgetItem*)"), self.loadPackage)
        self.connect(self.packageTable,
            SIGNAL("itemDoubleClicked(QTableWidgetItem*)"), self.showPackage)

    def setSource(self, source):
        self.htmlViewer.setSource(source)

    def showPackage(self, item):
        row = item.row()
        tmp = self.packageTable.item(row, 1)
        package = tmp.text()
        home = QUrl(self.home)
        curr = QUrl("../../library/%s/html/00Index.html" % package)
        self.htmlViewer.setSource(home.resolved(curr))

    def loadPackage(self, item):
        row = item.row()
        tmp = self.packageTable.item(row, 1)
        package = tmp.text()
        if item.checkState() == Qt.Checked:
            command = "library(%s)" % package
        else:
            command = "detach('package:%s')" % package
        robjects.r(command)
        #self.emit(SIGNAL(...(command)

    def updatePackages(self):
        library_ = robjects.r.get('library', mode='function')
        packages_ = robjects.r.get('.packages', mode='function')
        loaded = list(packages_())
        packages = list(library_()[1])
        length = len(packages)
        self.packageTable.clearContents()
        #self.table.setRowCount(length/3)
        packageList = []
        for i in range(length/3):
            package = unicode(packages[i])
            if not package in packageList:
                packageList.append(package)
                self.packageTable.setRowCount(len(packageList))
                item = QTableWidgetItem("Loaded")
                item.setFlags(
                Qt.ItemIsUserCheckable|Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                if package in loaded:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                self.packageTable.setItem(i, 0, item)
                item = QTableWidgetItem(unicode(packages[i]))
                item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                self.packageTable.setItem(i, 1, item)
                item = QTableWidgetItem(unicode(packages[i+(2*(length/3))]))
                item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                self.packageTable.setItem(i, 2, item)
                item = QTableWidgetItem(unicode(packages[i+(length/3)]))
                item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                self.packageTable.setItem(i, 3, item)
        self.packageTable.resizeColumnsToContents()

class HtmlBrowser(QWidget):

    class HtmlViewer(QTextBrowser):

        def __init__(self, parent=None, host="localhost", port=5432,
                     home="index.html", paths=None):
            QTextBrowser.__init__(self, parent)
            self.http = QHttp()
            self.http.setHost(host, port)
            home = QUrl(home)
            self.base = home
            self.html = QString()
            self.setOpenLinks(True)
            if not paths is None:
                self.setSearchPaths(paths)
            self.connect(self.http, SIGNAL("done(bool)"), self.getData)
            self.anchor = QString()
            self.setSource(home)

        def setSource(self, url):
            url = self.source().resolved(url)
            QTextBrowser.setSource(self, url)

        def loadResource(self, type, name):
            ret = QVariant()
            name.setFragment(QString())
            if type == QTextDocument.HtmlResource:
                loop = QEventLoop()
                self.connect(self.http, SIGNAL("done(bool)"), loop, SLOT("quit()"))
                self.http.get(name.toString())
                loop.exec_(QEventLoop.AllEvents|QEventLoop.WaitForMoreEvents)
                data = QVariant(QString(self.html))
            else:
                fileName = QFileInfo(
                name.toLocalFile()).fileName()
                data = QTextBrowser.loadResource(self, type, QUrl(fileName))
            return data

        def getData(self, error):
            if error:
                self.html = self.http.errorString()
            else:
                self.html = self.http.readAll()

    def __init__(self, parent=None, host="localhost", port=5432,
                 home="index.html", paths=None):
        QWidget.__init__(self, parent)
        self.parent = parent
        self.viewer = self.HtmlViewer(self.parent, host, port, home, paths)
        homeButton = QToolButton(self)
        homeAction = QAction("&Home", self)
        homeAction.setToolTip("Return to start page")
        homeAction.setWhatsThis("Return to start page")
        homeAction.setIcon(QIcon(":mActionHome.png"))
        homeButton.setDefaultAction(homeAction)
        homeAction.setEnabled(True)
        homeButton.setAutoRaise(True)

        backwardButton = QToolButton(self)
        backwardAction = QAction("&Back", self)
        backwardAction.setToolTip("Move to previous page")
        backwardAction.setWhatsThis("Move to previous page")
        backwardAction.setIcon(QIcon(":mActionBack.png"))
        backwardButton.setDefaultAction(backwardAction)
        backwardAction.setEnabled(False)
        backwardButton.setAutoRaise(True)

        forwardButton = QToolButton(self)
        forwardAction = QAction("&Forward", self)
        forwardAction.setToolTip("Move to next page")
        forwardAction.setWhatsThis("Move to next page")
        forwardAction.setIcon(QIcon(":mActionForward.png"))
        forwardButton.setDefaultAction(forwardAction)
        forwardAction.setEnabled(False)
        forwardButton.setAutoRaise(True)

        vert = QVBoxLayout(self)
        horiz = QHBoxLayout()
        horiz.addStretch()
        horiz.addWidget(backwardButton)
        horiz.addWidget(homeButton)
        horiz.addWidget(forwardButton)
        horiz.addStretch()
        vert.addLayout(horiz)
        vert.addWidget(self.viewer)
        self.connect(self.viewer, SIGNAL("forwardAvailable(bool)"), forwardAction.setEnabled)
        self.connect(self.viewer, SIGNAL("backwardAvailable(bool)"), backwardAction.setEnabled)
        self.connect(homeAction, SIGNAL("triggered()"), self.home)
        self.connect(backwardAction, SIGNAL("triggered()"), self.backward)
        self.connect(forwardAction, SIGNAL("triggered()"), self.forward)

    def home(self):
        self.viewer.home()
        #self.viewer.setSource(QUrl("/doc/html/Search?name=plot&title=1&keyword=1&alias=1&concept=1&exact=1"))

    def backward(self):
        self.viewer.backward()

    def forward(self):
        self.viewer.forward()

    def setSource(self, url):
        self.viewer.setSource(url)

#------------------------------------------------------------------------------#
#------------------------- Console Widgets and Tools --------------------------#
#------------------------------------------------------------------------------#

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
        self.setwdButton.setIcon(QIcon(":mActionWorkingSet.png"))
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
        upAction.setIcon(QIcon(":mActionPrevious.png"))
        upAction.setEnabled(True)
        self.actions.append(upAction)
        newAction = QAction("&New Directory", self)
        newAction.setStatusTip("Create new directory")
        newAction.setToolTip("Create new directory")
        newAction.setIcon(QIcon(":mActionFileOpen.png"))
        newAction.setEnabled(True)
        self.actions.append(newAction)
        synchAction = QAction("&Synch", self)
        synchAction.setStatusTip("Synch with current working directory")
        synchAction.setToolTip("Synch with current working directory")
        synchAction.setIcon(QIcon(":mActionGraphicRefresh.png"))
        synchAction.setEnabled(True)
        self.actions.append(synchAction)
        rmAction = QAction("&Delete", self)
        rmAction.setStatusTip("Delete selected item")
        rmAction.setToolTip("delete selected item")
        rmAction.setIcon(QIcon(":mActionFileClose.png"))
        rmAction.setEnabled(True)
        self.actions.append(rmAction)
        openAction = QAction("&Open", self)
        openAction.setStatusTip("Open selected R script")
        openAction.setToolTip("Open selected R script")
        openAction.setIcon(QIcon(":mActionFileOpen.png"))
        openAction.setEnabled(True)
        self.actions.append(openAction)
        loadAction = QAction("&Load", self)
        loadAction.setStatusTip("Load selected R data")
        loadAction.setToolTip("Load selected R data")
        loadAction.setIcon(QIcon(":mActionFileLoad.png"))
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
        newButton = QToolButton()
        newButton.setDefaultAction(newAction)
        synchButton = QToolButton()
        synchButton.setDefaultAction(synchAction)

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
        self.copyAction.setIcon(QIcon(":mActionEditCopy.png"))
        self.copyAction.setEnabled(False)

        self.selectAction = QAction("Select &all", self)
        self.selectAction.setStatusTip("Select all commands")
        self.selectAction.setToolTip("Select all commands")
        self.selectAction.setIcon(QIcon(":mActionEditSelectAll.png"))

        self.runAction = QAction("&Run command(s)", self)
        self.runAction.setStatusTip("Run the selected command(s) in the console")
        self.runAction.setToolTip("Run the selected command(s) in the console")
        self.runAction.setIcon(QIcon(":mActionRun.png"))
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
        self.workspaceTree.setHeaderLabels(QStringList(["Name", "Type", "Size"]))
        self.actions = []
        self.refreshAction = QAction("Re&fresh variables", self)
        self.refreshAction.setToolTip("Refresh environment browser")
        self.refreshAction.setWhatsThis("Refresh environment browser")
        self.refreshAction.setIcon(QIcon(":mActionGraphicRefresh.png"))
        self.refreshAction.setEnabled(True)
        self.actions.append(self.refreshAction)

        self.loadAction = QAction("&Load variable", self)
        self.loadAction.setToolTip("Load R variable(s) from file")
        self.loadAction.setWhatsThis("Load R variable(s) from file")
        self.loadAction.setIcon(QIcon(":mActionFileOpen.png"))
        self.loadAction.setEnabled(True)
        self.actions.append(self.loadAction)
        
        self.exportAction = QAction("Export to &file", self)
        self.exportAction.setToolTip("Export data to file")
        self.exportAction.setWhatsThis("Export data to file")
        self.exportAction.setIcon(QIcon(":mActionActionFile.png"))
        self.exportAction.setEnabled(False)
        self.actions.append(self.exportAction)

        self.saveAction = QAction("&Save variable", self)
        self.saveAction.setToolTip("Save R variable to file")
        self.saveAction.setWhatsThis("Save R variable to file")
        self.saveAction.setIcon(QIcon(":mActionFileSave.png"))
        self.saveAction.setEnabled(False)
        self.actions.append(self.saveAction)

        self.methodAction = QAction("&Print available methods", self)
        self.methodAction.setToolTip("Print available methods for object class")
        self.methodAction.setWhatsThis("Print available methods for object class")
        self.methodAction.setIcon(QIcon(":mActionQuestion.png"))
        self.methodAction.setEnabled(False)
        self.actions.append(self.methodAction)

        self.attributeAction = QAction("Print object &attributes", self)
        self.attributeAction.setToolTip("Print available attributes for object class")
        self.attributeAction.setWhatsThis("Print available attributes for object class")
        self.attributeAction.setIcon(QIcon(":mActionQuestion.png"))
        self.attributeAction.setEnabled(False)
        self.actions.append(self.attributeAction)

        self.rmAction = QAction("&Remove", self)
        self.rmAction.setToolTip("Remove selected variable")
        self.rmAction.setWhatsThis("Removed selected variable")
        self.rmAction.setIcon(QIcon(":mActionFileRemove.png"))
        self.rmAction.setEnabled(False)
        self.actions.append(self.rmAction)
        
        vbox = QVBoxLayout(self)
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
        itemName, itemType = self.getVariableInfo(items[0])
        self.runCommand('names(attributes(%s))' % (itemName,))

    def removeVariable(self):
        items = self.workspaceTree.selectedItems()
        if len(items) < 1:
            return False
        itemName, itemType = self.getVariableInfo(items[0])
        self.runCommand('rm(%s)' % (itemName,))
        self.updateVariables()

    def exportVariable(self):
        items = self.workspaceTree.selectedItems()
        if len(items) < 1:
            return False
        parents = []
        parent = items[0].parent()
        while parent:
            parents.append(parent.text(0))
            item = parent
            parent = item.parent()
        itemName, itemType = self.getVariableInfo(item)
        fd = QFileDialog(self.parent, "Save data to file", "", \
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
        command = QString('write.table(%s, file = "%s",' % (itemName, selectedFile))
        command.append(QString('append = FALSE, quote = TRUE, sep = ",", eol = "\\n", na = "NA"'))
        command.append(QString(', dec = ".", row.names = FALSE, col.names = TRUE, qmethod = "escape")'))
        self.runCommand(command)

    def saveVariable(self):
        items = self.workspaceTree.selectedItems()
        if len(items) < 1:
            return False
        parents = []
        parent = items[0].parent()
        while parent:
            parents.append(parent.text(0))
            item = parent
            parent = item.parent()
        itemName, itemType = self.getVariableInfo(item)
        fd = QFileDialog(self.parent, "Save data to file", "", \
        "R data file (*.Rda)")
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
        commands = QString('save(%s, file="%s")' % (itemName,selectedFile))
        self.runCommand(commands)

    def loadRVariable(self):
        fd = QFileDialog(self.parent, "Load R variable(s) from file", "",
        "R data (*.Rda);;All files (*.*)")
        fd.setAcceptMode(QFileDialog.AcceptOpen)
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

    def runCommand(self, command):
        if not commands.isEmpty():
            self.emitCommands(command)

    def updateVariables(self):
        #self.workspaceTree.clear()
        data = self.browseEnv()
        try:
            numofroots = list(data[0])[0]
        except:
            return False
        rootitems = list(data[1])
        names = list(data[2])
        types = list(data[3])
        dims = list(data[4])
        container = list(data[5])
        parentid = list(data[6])
        itemspercontainer = list(data[7])
        ids = list(data[8])
        def which(L, value):
            i = -1
            tmp = []
            try:
                while 1:
                    i = L.index(value, i+1)
                    tmp.append(i)
            except ValueError:
                pass
            return tmp

        for i in range(int(numofroots)):
            iid = rootitems[i]-1
            items = self.workspaceTree.findItems(QString(names[int(iid)]), Qt.MatchExactly, 0)
            if len([True for j in items if not j.parent()]) < 1: # check if a top level item matches
                a = QTreeWidgetItem(self.workspaceTree)
                a.setText(0, QString(names[int(iid)]))
                a.setText(1, QString(types[int(iid)]))
                a.setText(2, QString(dims[int(iid)]))
            else:
                count = 0
                while items[count].parent():
                    count+=1
                a = items[count-1]
                a.takeChildren()
            if container[i]:
                subitems = which(parentid, i+1)
                for id in subitems:
                    b = QTreeWidgetItem(a)
                    b.setText(0, QString(names[id]))
                    b.setText(1, QString(types[id]))
                    b.setText(2, QString(dims[id]))


    def browseEnv(self):
        parseEnv = robjects.r("""
        function ()
        {
            excludepatt = "^last\\\.warning"
            objlist <- ls(envir=.GlobalEnv)
            if (length(iX <- grep(excludepatt, objlist)))
                objlist <- objlist[-iX]
            n <- length(objlist)
            if (n == 0L) # do nothing!
                return(invisible())

            str1 <- function(obj) {
                md <- mode(obj)
                lg <- length(obj)
                objdim <- dim(obj)
                if (length(objdim) == 0L)
                    dim.field <- paste("length:", lg)
                else {
                    dim.field <- "dim:"
                    for (i in seq_along(objdim)) dim.field <- paste(dim.field,
                        objdim[i])
                    if (is.matrix(obj))
                        md <- "matrix"
                }
                obj.class <- oldClass(obj)
                if (!is.null(obj.class)) {
                    md <- obj.class[1L]
                    if (inherits(obj, "factor"))
                        dim.field <- paste("levels:", length(levels(obj)))
                }
                list(type = md, dim.field = dim.field)
            }
            N <- 0L
            M <- n
            IDS <- rep.int(NA, n)
            NAMES <- rep.int(NA, n)
            TYPES <- rep.int(NA, n)
            DIMS <- rep.int(NA, n)
            IsRoot <- rep.int(TRUE, n)
            Container <- rep.int(FALSE, n)
            ItemsPerContainer <- rep.int(0, n)
            ParentID <- rep.int(-1, n)
            for (objNam in objlist) {
                Spatial = FALSE
                N <- N + 1L
                obj <- get(objNam, envir = .GlobalEnv)
                if (!is.null(class(obj)) && inherits(obj, "Spatial")) {
                    tmpClass <- oldClass(obj)[1L]
                    obj <- obj@data
                    Spatial = TRUE
                }
                sOb <- str1(obj)
                IDS[N] <- N
                NAMES[N] <- objNam
                if (Spatial)
                    TYPES[N] <- tmpClass
                else
                    TYPES[N] <- sOb$type
                DIMS[N] <- sOb$dim.field
                if (is.recursive(obj) && !is.function(obj) && !is.environment(obj) &&
                    (lg <- length(obj))) {
                    Container[N] <- TRUE
                    ItemsPerContainer[N] <- lg
                    nm <- names(obj)
                    if (is.null(nm))
                        nm <- paste("[[", format(1L:lg), "]]", sep = "")
                    for (i in 1L:lg) {
                        M <- M + 1
                        ParentID[M] <- N
                        if (nm[i] == "")
                        nm[i] <- paste("[[", i, "]]", sep = "")
                        s.l <- str1(obj[[i]])
                        IDS <- c(IDS, M)
                        NAMES <- c(NAMES, nm[i])
                        TYPES <- c(TYPES, s.l$type)
                        DIMS <- c(DIMS, s.l$dim.field)
                    }
                }
                else if (!is.null(class(obj))) {
                    if (inherits(obj, "table")) {
                        obj.nms <- attr(obj, "dimnames")
                        lg <- length(obj.nms)
                        if (length(names(obj.nms)) > 0)
                        nm <- names(obj.nms)
                        else nm <- rep.int("", lg)
                        Container[N] <- TRUE
                        ItemsPerContainer[N] <- lg
                        for (i in 1L:lg) {
                        M <- M + 1L
                        ParentID[M] <- N
                        if (nm[i] == "")
                            nm[i] = paste("[[", i, "]]", sep = "")
                        md.l <- mode(obj.nms[[i]])
                        objdim.l <- dim(obj.nms[[i]])
                        if (length(objdim.l) == 0L)
                            dim.field.l <- paste("length:", length(obj.nms[[i]]))
                        else {
                            dim.field.l <- "dim:"
                            for (j in seq_along(objdim.l)) dim.field.l <- paste(dim.field.l,
                            objdim.l[i])
                        }
                        IDS <- c(IDS, M)
                        NAMES <- c(NAMES, nm[i])
                        TYPES <- c(TYPES, md.l)
                        DIMS <- c(DIMS, dim.field.l)
                        }
                    }
                    else if (inherits(obj, "mts")) {
                        nm <- dimnames(obj)[[2L]]
                        lg <- length(nm)
                        Container[N] <- TRUE
                        ItemsPerContainer[N] <- lg
                        for (i in 1L:lg) {
                        M <- M + 1L
                        ParentID[M] <- N
                        md.l <- mode(obj[[i]])
                        dim.field.l <- paste("length:", dim(obj)[1L])
                        md.l <- "ts"
                        IDS <- c(IDS, M)
                        NAMES <- c(NAMES, nm[i])
                        TYPES <- c(TYPES, md.l)
                        DIMS <- c(DIMS, dim.field.l)
                        }
                    }
                }
            }
            Container <- c(Container, rep.int(FALSE, M - N))
            IsRoot <- c(IsRoot, rep.int(FALSE, M - N))
            ItemsPerContainer <- c(ItemsPerContainer, rep.int(0, M -N))
            RootItems <- which(IsRoot)
            NumOfRoots <- length(RootItems)
            return (list(NumOfRoots, RootItems, NAMES,
                        TYPES, DIMS, Container, ParentID,
                        ItemsPerContainer, IDS))
        }""")
        try:
            return parseEnv()
        except Exception, err:
            print err
            return robjects.r("""list(1, 1, c("Error!"),
                        c("Missing package:"), c("'%s'"), c(F), 1,
                        1, 1)""" % str(err).split('"')[1])

#------------------------------------------------------------------------------#
#--------------------- Data structures and utilities --------------------------#
#------------------------------------------------------------------------------#

class Highlighter(QSyntaxHighlighter):

    Rules = []
    Formats = {}

    def __init__(self, parent=None):
        QSyntaxHighlighter.__init__(self, parent)
        self.parent = parent
        self.initializeFormats()
        RHighlighter.Rules.append((QRegExp(
            r"[a-zA-Z_]+[a-zA-Z_\.0-9]*(?=[\s]*[(])"), "keyword"))
        RHighlighter.Rules.append((QRegExp(
            "|".join([r"\b%s\b" % keyword for keyword in KEYWORDS])),
            "keyword"))
        RHighlighter.Rules.append((QRegExp(
            "|".join([r"\b%s\b" % builtin for builtin in BUILTINS])),
            "builtin"))
        #RHighlighter.Rules.append((QRegExp(
            #r"[a-zA-Z_\.][0-9a-zA-Z_\.]*[\s]*=(?=([^=]|$))"), "inbrackets"))
        RHighlighter.Rules.append((QRegExp(
            "|".join([r"\b%s\b" % constant
            for constant in CONSTANTS])), "constant"))
        RHighlighter.Rules.append((QRegExp(
            r"\b[+-]?[0-9]+[lL]?\b"
            r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
            r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
            "number"))
        RHighlighter.Rules.append((QRegExp(r"[\)\(]+|[\{\}]+|[][]+"),
            "delimiter"))
        RHighlighter.Rules.append((QRegExp(
            r"[<]{1,2}\-"
            r"|\-[>]{1,2}"
            r"|=(?!=)"
            r"|\$"
            r"|\@"), "assignment"))
        RHighlighter.Rules.append((QRegExp(
            r"([\+\-\*/\^\:\$~!&\|=>@^])([<]{1,2}\-|\-[>]{1,2})"
            r"|([<]{1,2}\-|\-[>]{1,2})([\+\-\*/\^\:\$~!&\|=<@])"
            r"|([<]{3}|[>]{3})"
            r"|([\+\-\*/\^\:\$~&\|@^])="
            r"|=([\+\-\*/\^\:\$~!<>&\|@^])"), "syntax"))
            #r"|(\+|\-|\*|/|<=|>=|={1,2}|\!=|\|{1,2}|&{1,2}|:{1,3}|\^|@|\$|~){2,}"

        self.stringRe = QRegExp("(\'[^\']*\'|\"[^\"]*\")")
        self.stringRe.setMinimal(True)
        RHighlighter.Rules.append((self.stringRe, "string"))
        RHighlighter.Rules.append((QRegExp(r"#.*"), "comment"))
        self.multilineSingleStringRe = QRegExp(r"""'(?!")""")
        self.multilineDoubleStringRe = QRegExp(r'''"(?!')''')
        self.bracketBothExpression = QRegExp(r"[\(\)]")
        self.bracketStartExpression = QRegExp(r"\(")
        self.bracketEndExpression = QRegExp(r"\)")

    def initializeFormats(self):
        baseFormat = QTextCharFormat()
        baseFormat.setFontFamily(Config["fontfamily"])
        baseFormat.setFontPointSize(Config["fontsize"])
        for name in ("normal", "keyword", "builtin", "constant",
                      "delimiter", "comment", "string", "number", "error",
                      "assignment", "syntax"):
            format = QTextCharFormat(baseFormat)
            format.setForeground(
                QColor(Config["%sfontcolor" % name]))
            if name == "syntax":
                format.setFontUnderline(Config["%sfontunderline" % name])
            else:
                if Config["%sfontbold" % name]:
                    format.setFontWeight(QFont.Bold)
            format.setFontItalic(Config["%sfontitalic" % name])
            RHighlighter.Formats[name] = format

        format = QTextCharFormat(baseFormat)
        if Config["assignmentfontbold"]:
            format.setFontWeight(QFont.Bold)
        format.setForeground(
            QColor(Config["assignmentfontcolor"]))
        format.setFontItalic(Config["%sfontitalic" % name])
        RHighlighter.Formats["inbrackets"] = format

    def highlightBlock(self, text):
        NORMAL, MULTILINESINGLE, MULTILINEDOUBLE, ERROR = range(4)
        INBRACKETS, INBRACKETSSINGLE, INBRACKETSDOUBLE = range(4,7)

        textLength = text.length()
        prevState = self.previousBlockState()

        self.setFormat(0, textLength, RHighlighter.Formats["normal"])

        for regex, format in RHighlighter.Rules:
            i = regex.indexIn(text)
            while i >= 0:
                length = regex.matchedLength()
                self.setFormat(i, length, RHighlighter.Formats[format])
                i = regex.indexIn(text, i + length)
        self.setCurrentBlockState(NORMAL)

        startIndex = 0
        startCount = 0
        endCount = 0
        endIndex = 0
        if not self.previousBlockState() >= 4:
            startIndex = self.bracketStartExpression.indexIn(text)
        while startIndex >= 0:
            startCount += 1
            endIndex = self.bracketBothExpression.indexIn(text, startIndex+1)
            bracket = self.bracketBothExpression.cap()
            if endIndex == -1 or bracket == "(":
                self.setCurrentBlockState(self.currentBlockState() + 4)
                length = text.length() - startIndex
            elif bracket == ")":
                endCount += 1
                tmpEndIndex = endIndex
                while tmpEndIndex >= 0:
                    tmpLength = self.bracketBothExpression.matchedLength()
                    tmpEndIndex = self.bracketBothExpression.indexIn(text, tmpEndIndex + tmpLength)
                    bracket = self.bracketBothExpression.cap()
                    if tmpEndIndex >= 0:
                        if bracket == ")":
                            endIndex = tmpEndIndex
                            endCount += 1
                        else:
                            startCount += 1
                if startCount > endCount:
                    self.setCurrentBlockState(self.currentBlockState() + 4)
                length = endIndex - startIndex + self.bracketBothExpression.matchedLength() + 1

            bracketText = text.mid(startIndex, length+1)
            regex = QRegExp(r"[a-zA-Z_\.][0-9a-zA-Z_\.]*[\s]*=(?=([^=]|$))")
            format = "inbrackets"
            i = regex.indexIn(bracketText)
            while i >= 0:
                bracketLength = regex.matchedLength()
                self.setFormat(startIndex + i, bracketLength, RHighlighter.Formats[format])
                length = length + bracketLength
                i = regex.indexIn(bracketText, i + bracketLength)
            startIndex = self.bracketStartExpression.indexIn(text, startIndex + length)

        if text.indexOf(self.stringRe) != -1:
            return
        for i, state in ((text.indexOf(self.multilineSingleStringRe),
                          MULTILINESINGLE),
                        (text.indexOf(self.multilineDoubleStringRe),
                          MULTILINEDOUBLE)):
            if (self.previousBlockState() == state or \
            self.previousBlockState() == state + 4) and \
            not text.contains("#"):
                if i == -1:
                    i = text.length()
                    self.setCurrentBlockState(state)
                self.setFormat(0, i + 1, RHighlighter.Formats["string"])
            elif i > -1 and not text.contains("#"):
                self.setCurrentBlockState(state)
                self.setFormat(i, text.length(), RHighlighter.Formats["string"])

    def rehighlight(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QSyntaxHighlighter.rehighlight(self)
        QApplication.restoreOverrideCursor()

class UserData(QTextBlockUserData):

    def __init__(self, data=None, extra=None):
        QTextBlockUserData.__init__(self)
        self.__data = data
        self.__extra = extra

    def setData(self, data):
        self.__data = data

    def data(self):
        return self.__data

    def setExtra(self, extra):
        self.__extra = extra

    def extra(self):
        return self.__extra

    def hasExtra(self):
        return not self.__extra is None

class Dictionary(QObject):

    def __init__(self, parent=None):
        QObject.__init__(self, None)
        self.DICT = {}

    def udpateItems(self, items):
        self.DICT.update(items)

    def setItems(self, items):
        self.DICT = items

    def keys(self):
        return self.DICT.keys()

    def values(self):
        return self.DICT.values()

    def value(self, key):
        return self.DICT[key]

    def items(self):
        return self.DICT

class History(QAbstractListModel):

    def __init__(self, parent=None, items=QStringList()):
        QAbstractListModel.__init__(self, None)
        self.__HIST = items
        self.__index = 0

    def update(self, items):
        if not items.isEmpty():
            rows = items.count()
            position = self.rowCount()
            self.insertRows(position, rows, QModelIndex())
            good = 0
            for count, item in enumerate(items):
                inda = self.index(position+count-1, 0)
                indb = self.index(position+count, 0)
                if (not QVariant(item) == self.data(inda, Qt.DisplayRole)) \
                or (self.rowCount()==0):
                    self.setData(indb, QVariant(item), Qt.EditRole)
                    good += 1
            if not good == count+1:
                self.removeRows(position+good, rows-good, QModelIndex())
            self.__index = self.rowCount()

    def history(self):
        return self.__HIST

    def rowCount(self, parent=QModelIndex()):
        return self.__HIST.count()

    def data(self, index, role):
        # index here is a QModelIndex
        if not index.isValid():
            return QVariant()
        if index.row() >= self.__HIST.count():
            return QVariant()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.__HIST[index.row()]
        else:
            return QVariant()

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return QAbstractItemModel.flags(self, index) | Qt.ItemIsEditable

    def setData(self, index, value, role):
        if index.isValid() and role == Qt.EditRole:
            self.__HIST.replace(index.row(), value.toString())
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
            return True
        return False

    def insertRows(self, position, rows, parent):
        self.beginInsertRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            self.__HIST.insert(position, "")
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent):
        self.beginRemoveRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            self.__HIST.removeAt(position)
        self.endRemoveRows()
        return True

    def currentIndex(self):
        return self.__index

    def currentItem(self):
        return self.__HIST[self.__index]

    def next(self):
        if self.currentIndex() < self.rowCount() and self.rowCount() > 0:
            self.__index += 1
        if self.currentIndex() == self.rowCount():
            return QString()
        else:
            return self.currentItem()

    def previous(self):
        if  self.currentIndex() > 0 and self.rowCount() > 0:
            self.__index -= 1
        if self.currentIndex() == self.rowCount():
            return QString()
        else:
            return self.currentItem()

    def loadHistory(self):
        try:
            fileInfo = QFileInfo()
            fileInfo.setFile(QDir(robjects.r['getwd']()[0]), ".Rhistory")
            fileFile = QFile(fileInfo.absoluteFilePath())
            if not fileFile.open(QIODevice.ReadOnly):
                return False
            inFile = QTextStream(fileFile)
            while not inFile.atEnd():
                line = QString(inFile.readLine())
                self.update(line)
        except:
            return False
        return True

    def saveHistory(self):
        try:
            fileInfo = QFileInfo()
            fileInfo.setFile(QDir(robjects.r['getwd']()[0]), ".Rhistory")
            outFile = open(fileInfo.filePath(), "w")
            for line in self.history():
                outFile.write(line+"\n")
            outFile.flush()
        except:
            return False
        return True

class OutputCatcher(QObject):

    def __init__(self, pipe):
        QObject.__init__(self, None)
        self.data = ""
        self.pipe = pipe

    def write(self, stuff):
        #self.data += stuff
        self.pipe.send(stuff)
        sys.__stdout__.write(stuff)

    def flush(self):
        #stuff = "\n".join(self.data)
        #sys.__stdout__.flush()
        pass

    def clear(self):
        self.data = ''

def run(command, lock, pipe):
    sys.stdout = sys.stderr = OutputCatcher(pipe)
    lock.acquire()
    try:
        robjects.r(unicode(command))
    except robjects.rinterface.RRuntimeError, err:
        pass
    lock.release()
    pipe.send(None)
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    pipe.close()


HISTORY = History()

def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    app.setOrganizationName("manageR")
    app.setOrganizationDomain("ftools.ca")
    app.setApplicationName("manageR")
    app.setWindowIcon(QIcon(":mActionIcon.png"))
    app.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))
    window = MainWindow(None, True)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()