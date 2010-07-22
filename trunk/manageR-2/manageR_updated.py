#!/usr/bin/env python
# -*- coding: utf-8 -*-

#TODO: Make sure errors are always on a single line

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
import complete, resources, converters
from widgets import *
from browsers import *
from config import ConfigDialog

# rpy2 (R) imports
import rpy2
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc

from qgis.core import (QgsApplication, QgsMapLayer,QgsProviderRegistry,
                       QgsVectorLayer, )
from qgis.gui import QgsEncodingFileDialog
import qgis.utils

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

    def __init__(self, parent=None, iface=None, console=True, sidepanel=True):
        QMainWindow.__init__(self, parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowIcon(QIcon(":icon.png"))
        self.iface = iface
        fontfamily = QSettings().value("manageR/fontfamily", "DejaVu Sans Mono").toString()
        fontsize = QSettings().value("manageR/fontsize", 10).toInt()[0]
        tabwidth = QSettings().value("manageR/tabwidth", 4).toInt()[0]
        autobracket = QSettings().value("manageR/bracketautocomplete", True).toBool()
        autopopup = QSettings().value("manageR/enableautocomplete", True).toBool()

        font = QFont(fontfamily, fontsize)
        self.setFont(font)
        self.setMinimumSize(50, 50)
        self.startTimer(30)
        self.main = BaseFrame(self, tabwidth, autobracket, autopopup, sidepanel, console)
        if QSettings().value("manageR/enablehighlighting", True).toBool():
            backcolor = QColor(QSettings().value("manageR/backgroundfontcolor", "#FFFFFF").toString())
            fontcolor = QColor(QSettings().value("manageR/normalfontcolor", "#000000").toString())
            palette = QPalette(backcolor)
            palette.setColor(QPalette.Active, QPalette.Base, backcolor)
            palette.setColor(QPalette.Active, QPalette.WindowText, QColor(fontcolor))
            palette.setColor(QPalette.Inactive, QPalette.WindowText, QColor(fontcolor))
            self.main.setPalette(palette)
            self.highlighter = Highlighter(self.main.editor())
        if console:
            self.setWindowTitle("manageR")
            if QSettings().value("manageR/remembergeometry", True).toBool():
                width = QSettings().value("manageR/consolewidth", 50).toInt()[0]
                height = QSettings().value("manageR/consoleheight", 50).toInt()[0]
                x = QSettings().value("manageR/consolex", 0).toInt()[0]
                y = QSettings().value("manageR/consoley", 0).toInt()[0]
                self.resize(width, height)
                self.move(x, y)
            self.main.editor().setCheckSyntax(False)
            data = QMimeData()
            data.setText(WELCOME)
            self.main.editor().insertFromMimeData(data)
            self.main.editor().setCheckSyntax(True)
            self.main.editor().setHistory(HISTORY)
            prompts = (QSettings().value("manageR/beforeinput", ">").toString(),
                QSettings().value("manageR/afteroutput", "+").toString())
            self.main.editor().setPrompt(*prompts)
            self.prepareEnvironment()
            QShortcut(QKeySequence("Ctrl+L"), self, self.importMapLayer)
            QShortcut(QKeySequence("Ctrl+T"), self, self.importMapTable)
            QShortcut(QKeySequence("Ctrl+M"), self, self.exportCanvasLayer)
            QShortcut(QKeySequence("Ctrl+E"), self, self.exportFileLayer)
        else:
            if QSettings().value("manageR/remembergeometry", True).toBool():
                width = QSettings().value("manageR/windowwidth", 50).toInt()[0]
                height = QSettings().value("manageR/windowheight", 50).toInt()[0]
                x = QSettings().value("manageR/windowx", 0).toInt()[0]
                y = QSettings().value("manageR/windowy", 0).toInt()[0]
                self.resize(width, height)
                self.move(x, y)
            self.setWindowTitle("editR - untitled")
            self.columnCountLabel = QLabel("Column 1")
            self.statusBar().addPermanentWidget(self.columnCountLabel)
            self.lineCountLabel = QLabel("Line 1 of 1")
            self.statusBar().addPermanentWidget(self.lineCountLabel)
            self.connect(self.main.editor(), SIGNAL("cursorPositionChanged()"),
                self.updateIndicators)
            self.connect(self.main.editor().document(), SIGNAL("blockCountChanged(int)"),
                self.updateIndicators)
            self.main.editor().setPlainText(QSettings().value("manageR/newfile", "").toString())
        self.setCentralWidget(self.main)
        self.paths = QStringList(os.path.join(CURRENTDIR, "doc", "html"))
        self.createFileActions(console)
        self.createEditActions(console)
        self.createActionActions(console)
        self.createWorkspaceActions(console)
        self.createWindowActions(console)
        self.createDockWigets(console)
        self.createHelpActions(console)
        self.restoreState(QSettings().value("manageR/toolbars").toByteArray())
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
            self.connect(workspaceWidget, SIGNAL("emitCommands(QString)"), self.main.editor().acceptCommands)
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
                QKeySequence.New, "document-new", "Open empty R script")
            fileOpenAction = self.createAction("&Open...", self.fileOpen,
                QKeySequence.Open, "document-open", "Open existing R script")
            self.addActions(fileMenu, (fileNewAction, fileOpenAction, None, ))
        else:
            fileOpenAction = self.createAction("&Open...", self.fileOverwrite,
                QKeySequence.Open, "document-open", "Open existing R script")
            fileSaveAction = self.createAction("&Save", self.fileSave,
                QKeySequence.Save, "document-save", "Save R script")
            fileSaveAsAction = self.createAction("Save &As...",
                self.fileSaveAs, QKeySequence.SaveAs,
                "document-save-as", "Save R script as...")
            fileCloseAction = self.createAction("&Close", self.fileClose,
                QKeySequence.Close, "process-stop",
                "Close this editR window")
            self.addActions(fileMenu, (fileOpenAction, fileSaveAction,
                fileSaveAsAction, None, fileCloseAction,))
        if console:
            fileConfigureAction = self.createAction("Config&ure...",
                self.fileConfigure, "Ctrl+Shift+P",
                "preferences-desktop", "Configure manageR")
            fileQuitAction = self.createAction("&Quit", self.fileQuit,
                "Ctrl+Q", "system-shutdown", "Quit manageR")
            self.addActions(fileMenu, (fileConfigureAction, None,
                fileQuitAction,))

    def createEditActions(self, console=True, autocomplete=True):
        editMenu = self.menuBar().addMenu("&Edit")
        if not console:
            editUndoAction = self.createAction("&Undo", self.main.editor().undo,
                QKeySequence.Undo, "edit-undo",
                "Undo last editing action")
            editRedoAction = self.createAction("&Redo", self.main.editor().redo,
                QKeySequence.Redo, "edit-redo",
                "Redo last editing action")
            self.addActions(editMenu, (editUndoAction, editRedoAction, None))
        editCopyAction = self.createAction("&Copy", self.main.editor().copy,
            QKeySequence.Copy, "edit-copy", "Copy text to clipboard")
        editCutAction = self.createAction("Cu&t", self.main.editor().cut,
            QKeySequence.Cut, "edit-cut", "Cut text to clipboard")
        editPasteAction = self.createAction("&Paste",
            self.main.editor().paste, QKeySequence.Paste, "edit-paste",
            "Paste text from clipboard")
        editSelectAllAction = self.createAction("Select &All",
            self.main.editor().selectAll, QKeySequence.SelectAll,
            "edit-select-all", "Select all")
        self.addActions(editMenu, (editCopyAction, editCutAction,
            editPasteAction, editSelectAllAction, None))
        if autocomplete:
            editCompleteAction = self.createAction("Com&plete",
                self.main.completer().suggest, icon="help-faq",
                tip="Initiate autocomplete suggestions")
            self.addActions(editMenu, (editCompleteAction, None,))
        editFindNextAction = self.createAction("&Find",
            self.main.toggleSearch, QKeySequence.Find,
            "edit-find", "Find text")
        self.addActions(editMenu, (editFindNextAction,))
        if not console:
            editReplaceNextAction = self.createAction("&Replace",
                self.main.toggleReplace, QKeySequence.Replace,
                "edit-find-replace", "Replace text")
            editGotoLineAction =  self.createAction("&Go to line",
                self.main.editor().gotoLine, "Ctrl+G", "go-bottom",
                "Move cursor to line")
            editIndentRegionAction = self.createAction("&Indent Region",
                self.main.editor().indentRegion, "Ctrl+I", "format-indent-more",
                "Indent the selected text or the current line")
            editUnindentRegionAction = self.createAction(
                "Unin&dent Region", self.main.editor().unindentRegion,
                "Ctrl+Shift+I", "format-indent-less",
                "Unindent the selected text or the current line")
            editCommentRegionAction = self.createAction("C&omment Region",
                self.main.editor().commentRegion, "Ctrl+D", "list-add",
                "Comment out the selected text or the current line")
            editUncommentRegionAction = self.createAction(
                "Uncomment Re&gion", self.main.editor().uncommentRegion,
                "Ctrl+Shift+D", "list-remove",
                "Uncomment the selected text or the current line")
            self.addActions(editMenu, (editReplaceNextAction, None,
                editGotoLineAction, editIndentRegionAction, editUnindentRegionAction,
                editCommentRegionAction, editUncommentRegionAction,))

    def createActionActions(self, console=True):
        actionMenu = self.menuBar().addMenu("&Action")
        if not console:
            actionRunAction = self.createAction("E&xecute",
                self.send, "Ctrl+Return", "utilities-terminal",
                "Execute the (selected) text in the manageR console")
            actionSourceAction = self.createAction("Run S&cript",
                self.source,"", "system-run",
                "Run the current EditR script")
            self.addActions(actionMenu, (actionRunAction, actionSourceAction, None,))
        else:
            actionShowPrevAction = self.createAction(
                "Show Previous Command", self.main.editor().previous,
                "Up", "go-up", "Show previous command")
            actionShowNextAction = self.createAction(
                "Show Next Command", self.main.editor().next,
                "Down", "go-down", "Show next command")
            self.addActions(actionMenu, (actionShowPrevAction,
                actionShowNextAction,))

    def createWorkspaceActions(self, console=True):
        if console:
            workspaceMenu = self.menuBar().addMenu("Wo&rkspace")
            workspaceLoadAction = self.createAction(
                "&Load R workspace", self.openWorkspace,
                "Ctrl+W", "system-file-manager",
                "Load R workspace")
            workspaceSaveAction = self.createAction(
                "&Save R workspace", self.saveWorkspace,
                "Ctrl+Shift+W", "document-save",
                "Save R workspace")
            workspaceDataAction = self.createAction(
                "Load R &data", self.openData,
                "Ctrl+D", "package-x-generic",
                "Load R data")
            workspaceLibraryAction = self.createAction("Library &browser",
                self.libraryBrowser, "Ctrl+H", icon="help-contents",
                tip="Browse R package library")
            workspaceRepositoryAction = self.createAction("&Install packages",
                self.repositoryBrowser, icon="system-software-install",
                tip="Install R packages")
            self.addActions(workspaceMenu, (workspaceLoadAction,
                workspaceSaveAction, workspaceDataAction, None,
                workspaceLibraryAction, workspaceRepositoryAction,))

    def createHelpActions(self, console=True):
        helpMenu = self.menuBar().addMenu("&Help")
        helpSearchAction = self.createAction("&Help", self.helpBrowser,
            QKeySequence.HelpContents, icon="help-browser",
            tip="Commands help")
        helpAboutAction = self.createAction("&About", self.helpAbout,
            icon="help-about", tip="About manageR")
        self.addActions(helpMenu, (helpSearchAction, helpAboutAction,))

    def createWindowActions(self, console=True):
        if console:
            self.windowMenu = self.menuBar().addMenu("&Window")
            self.connect(self.windowMenu, SIGNAL("aboutToShow()"),
                 self.updateWindowMenu)

    def prepareEnvironment(self):
        folder = QSettings().value("manageR/setwd", ".").toString()
        commands = QSettings().value("manageR/consolestartup", "").toString()
        load = QSettings().value("manageR/loadenvironment", True).toBool()
        robjects.r.setwd(unicode(folder))
        robjects.r(unicode(commands))
        if load:
            self.openWorkspace(path=QString(".RData"), filter = QString(".RData"), visible=False)
            self.main.editor().history().loadHistory()

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
        action.setIcon(QIcon(":utilities-terminal.svg"))
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
            action.setIcon(QIcon(":preferences-system-windows.svg"))

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
            action.setIcon(QIcon(":%s.svg" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            if param is not None:
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
        browser = AboutBrowser(self, VERSION, LICENSE, CURRENTDIR)
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

    def openWorkspace(self, path=None, filter="R workspace (*.RData)", visible=True):
        self.openData(path, filter, visible)

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

    def openData(self, path=None, filter=None, visible=True):
        command = ""
        if filter is None:
            filter = "R data (*.Rdata *.Rda *.RData);;All files (*)"
        if path is None:
            path = QFileDialog.getOpenFileName(self,
                            "manageR - Open Data File",
                            unicode(robjects.r.getwd()[0]),
                            filter)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if not path == "":
            path = QDir(path).absolutePath()
            command = "load(file='%s')" % unicode(path)
            if visible:
                try:
                    self.execute(command)
                except Exception, err:
                    QMessageBox.warning(self, "manageR - Load Error",
                    "Unable to load data file %s!\n%s" % (path,err))
            else:
                try:
                    robjects.r.load(file=unicode(path))
                except Exception, e:
                    #raise Exception(str(e))
                    pass
            self.statusBar().showMessage("Loaded R Data %s" % path, 5000)
        QApplication.restoreOverrideCursor()

    def fileConfigure(self):
        browser = ConfigDialog(self)
        browser.exec_()

    def fileNew(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        window = MainWindow(self, iface=None, console=False)
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
            backup = "%s%s" % (path, QSettings().value("manageR/backupsuffix", "~").toString())
            ok = True
            if QFile.exists(backup):
                ok = QFile.remove(backup)
                if not ok:
                    QMessageBox.information(self,
                            "editR - Save Warning",
                            "Failed to remove existing backup file %s" % backup)
            if ok:
                # Must use copy rather than rename to preserve file
                # permissions; could use rename on Windows though
                if not QFile.copy(path, backup):
                    QMessageBox.information(self,
                            "editR - Save Warning",
                            "Failed to save backup file %s" % backup)
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
        self.close()

    def fileQuit(self):
        windows = QApplication.findChildren(self, MainWindow)
        for window in windows:
            if not window == self:
                window.close()
        QSettings().setValue("manageR/toolbars", self.saveState())
        self.close()

    def closeEvent(self, event):
        if self.main.editor().document().isModified():
            if self.windowTitle() == "manageR":
                reply = QMessageBox.question(self, "manageR - Quit",
                "Save workspace image?",
                QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
                if reply == QMessageBox.Cancel:
                    event.ignore()
                    return
                if reply == QMessageBox.Save:
                    self.saveWorkspace(path=".RData")
                    self.main.editor().history().saveHistory()
                try:
                    robjects.r('graphics.off()')
                except:
                    try:
                      for i in list(robjects.r('dev.list()')):
                        robjects.r('dev.next()')
                        robjects.r('dev.off()')
                    except:
                      pass
            else:
                reply = QMessageBox.question(self,
                            "editR - Unsaved Changes",
                            "Save unsaved changes in %s" % self.windowTitle().remove("editR - "),
                            QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
                if reply == QMessageBox.Save:
                    self.fileSave()
                elif reply == QMessageBox.Cancel:
                    event.ignore()
                    return
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

    def importMapTable(self, layer=None):
        self.importMapLayer(layer, geom=False)
        return True

    def exportCanvasLayer(self):
        pass

    def exportFileLayer(self):
        pass

    def importMapLayer(self, layer=None, geom=True):
        if layer is None:
            if not self.iface is None:
                layer = self.iface.mapCanvas().currentLayer()
            if layer is None:
                filters = QgsProviderRegistry.instance().fileVectorFilters()
                dialog = QgsEncodingFileDialog(self, "manageR - Open Vector File",
                    unicode(robjects.r.getwd()[0]), filters)
                if not dialog.exec_() == QDialog.Accepted:
                    return False
                files = dialog.selectedFiles()
                file = files.first().trimmed()
                encoding = dialog.encoding()
                base = QFileInfo(file).completeBaseName()
                layer = QgsVectorLayer(file.trimmed(), base, 'ogr')
        elif isinstance(layer, int):
            layer =  iface.mapCanvas().layer(layer)
        else:
            QMessageBox.warning(self, "manageR - Import Error",
                "Unable to determine layer for import")
            return False
        if not robjects.r.require('sp')[0]:
            QMessageBox.warning(self, "manageR - Import Error",
                "Missing R package 'sp', please install via install.packages()"
                "or Workspace > Install Packages")
            return False
        if layer.type() == QgsMapLayer.VectorLayer:
            try:
                if layer.selectedFeatureCount() < 1:
                    if robjects.r.require('rgdal'):
                        return converters.qOGRVectorDataFrame(layer, geom)
                    robjects.r['print']("An error occured while attempting to "
                    "speed up import by using 'RGDAL' package (%s)\n" 
                    "Using internal conversion utilities instead...\n" % unicode(e))
                return converters.qQGISVectorDataFrame(layer, geom)
            except Exception, e:
                QMessageBox.warning(self, "manageR - Import Error",
                    "Unable to import layer:\n%s" % unicode(e))
                return False
        elif layer.type() == QgsMapLayer.RasterLayer:
            if QSettigns().value("manageR/useraster", True).toBool():
                package = 'raster'
            else:
                package = 'rgdal'
            try:
                return converters.qRasterDataFrameObject(layer, package)
            except Exception, e:
                QMessageBox.warning(self, "manageR - Import Error",
                    "Unable to import layer:\n%s" % unicode(e))
                return False
        else:
            QMessageBox.warning(self, "manageR - Import Error",
                "Unknown spatial data type, unable to import layer into manageR")
            return False
        return True
        
            
        
#------------------------------------------------------------------------------#
#-------------------------- Main Console and Editor ---------------------------#
#------------------------------------------------------------------------------#

class PlainTextEdit(QPlainTextEdit):
    OUTPUT,INPUT,CONTINUE,SYNTAX,ERROR = range(5)

    def __init__(self, parent=None, tabwidth=4, autobracket=True):
        QPlainTextEdit.__init__(self, parent)
        self.__tabwidth = tabwidth
        self.__parent = parent
        self.__autobracket = autobracket
        self.__checkSyntax = True
        self.__suspended = False
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
                    cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor)
                    text = cursor.selectedText().trimmed()
                    if not text.isEmpty():
                        self.emit(SIGNAL("requestSuggestion(int)"), 1)
                        pass
                    else:
                        self.insertPlainText(indent)
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
                cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
                insert = ""
                if event.key() == Qt.Key_ParenLeft and \
                    cursor.selectedText().trimmed().isEmpty():
                    insert = QString(Qt.Key_ParenRight)
                elif event.key() == Qt.Key_BracketLeft and \
                    cursor.selectedText().trimmed().isEmpty():
                    insert = QString(Qt.Key_BracketRight)
                elif event.key() == Qt.Key_BraceLeft and \
                    cursor.selectedText().trimmed().isEmpty():
                    insert = QString(Qt.Key_BraceRight)
                cursor = self.textCursor()
                cursor.insertText("%s%s" % (QString(event.key()),insert))
                if not insert == "":
                    cursor.movePosition(QTextCursor.PreviousCharacter,
                    QTextCursor.MoveAnchor)
                self.setTextCursor(cursor)
            else:
                QPlainTextEdit.keyPressEvent(self, event)
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
        pos2 = block.position()
        block = block.previous()
        pos1 = self.textCursor().position()
        while block.isValid():
            try:
                if not block.userData().data() == PlainTextEdit.CONTINUE:
                    break
            except: # this means there is no user data, assume ok
                break
            if not block.text().trimmed().isEmpty():
                command.prepend("%s\n" % block.text())
            pos2 = block.position()
            block = block.previous()
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

    def suspendHighlighting(self):
        self.__suspended = True

    def resumeHighlighting(self):
        self.__suspended = False

    def isHighlightingSuspended(self):
        return self.__suspended

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
                        pixmap = QPixmap(":dialog-warning.svg")
                    else:
                        pixmap = QPixmap(":dialog-error.svg")
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
            actions = [[QIcon(":edit-copy.svg"),
                        "Copy", self.copy, QKeySequence(QKeySequence.Copy)],
                       [QIcon(":edit-select-all.svg"),
                        "Select all", self.selectAll,
                        QKeySequence(QKeySequence.SelectAll)],
                       [QIcon(":logo.svg"),
                        "Function keywords", self.insertParameters,
                        QKeySequence("Ctrl+P")],
                       [QIcon(":edit-paste.svg"),
                        "Paste", self.paste,
                        QKeySequence(QKeySequence.Paste)],
                       [QIcon(":edit-cut.svg"),
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
        self.setPrompt(*prompts)
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
                if not self.tabChangesFocus():
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
                self.printOutput([block.userData().extra().replace("\n", "").append("\n")])
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
                string.append(QString(output))
                output = self.pipeEnd.recv()
        except EOFError:
            pass
        self.printOutput(list(string))
        return True

    def acceptCommands(self, commands):
        mime = QMimeData()
        if not QString(commands).endsWith("\n"):
            commands += "\n"
        mime.setText(commands)
        self.insertFromMimeData(mime)

    def printOutput(self, output):
        error = False
        
        if len(output) > 0:
            for line in output:
                if not line == "":
                    if line.startsWith("Error") or error:
                        error = True
                        line = QString("Error: %s\n" % line.split(":",
                        QString.SkipEmptyParts)[1:].join("").trimmed())
                        self.textCursor().block().setUserData(
                            UserData(PlainTextEdit.ERROR, QString("Error")))
                    else:
                        self.suspendHighlighting()
                        self.textCursor().block().setUserData(
                            UserData(PlainTextEdit.OUTPUT, QString("Output")))
                    line = QString(line)
                    line.replace('\xe2\x9c\x93', "").replace('\xe2\x80\x98', "'").replace('\xe2\x80\x99', "'")
                    self.insertPlainText(line)
        #self.textCursor().block().setUserData(
            #UserData(PlainTextEdit.OUTPUT, QString("Output")))
        self.resumeHighlighting()
        self.ensureCursorVisible()

    def mousePressEvent(self, e):
        cursor = self.textCursor()
        if e.button() == Qt.RightButton:
            actions = [[QIcon(":edit-copy.svg"),
                        "Copy", self.copy, QKeySequence(QKeySequence.Copy)],
                       [QIcon(":edit-select-all.svg"),
                        "Select all", self.selectAll,
                        QKeySequence(QKeySequence.SelectAll)],
                       [QIcon(":logo.png"),
                        "Function keywords", self.insertParameters,
                        QKeySequence("Ctrl+P")],
                       [QIcon(":edit-paste.svg"),
                        "Paste", self.paste,
                        QKeySequence(QKeySequence.Paste)],
                       [QIcon(":edit-cut.svg"),
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
                    if curr.data() in (PlainTextEdit.OUTPUT, PlainTextEdit.ERROR):
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
        self.closeButton.setIcon(QIcon(":process-stop.svg"))
        self.closeButton.setToolTip("Close search bar")
        self.closeButton.setAutoRaise(True)
        self.searchEdit = QLineEdit(self)
        self.searchEdit.setToolTip("Find text")
        self.nextButton = QToolButton(self)
        self.nextButton.setText("Next")
        self.nextButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.nextButton.setIcon(QIcon(":go-next.svg"))
        self.nextButton.setToolTip("Find next")
        self.nextButton.setAutoRaise(True)
        self.previousButton = QToolButton(self)
        self.previousButton.setToolTip("Find previous")
        self.previousButton.setText("Prev")
        self.previousButton.setIcon(QIcon(":go-previous.svg"))
        self.previousButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.previousButton.setAutoRaise(True)
        self.wholeCheckbox = QCheckBox()
        self.wholeCheckbox.setText("Whole words")
        self.caseCheckbox = QCheckBox()
        self.caseCheckbox.setText("Case sensitive")
        # add search elements to widget

        vbox = QVBoxLayout(self)
        hbox = QHBoxLayout()
        hbox.addWidget(self.closeButton)
        hbox.addWidget(findLabel)
        hbox.addWidget(self.searchEdit)
        hbox.addWidget(self.previousButton)
        hbox.addWidget(self.nextButton)
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.wholeCheckbox)
        hbox.addWidget(self.caseCheckbox)
        vbox.addLayout(hbox)

        # create replace elements
        self.replaceLabel = QLabel("Replace:")
        self.replaceLabel.setMaximumWidth(80)
        self.replaceEdit = QLineEdit(self)
        self.replaceEdit.setToolTip("Replace text")
        self.replaceButton = QToolButton(self)
        self.replaceButton.setText("Replace")
        self.replaceButton.setToolTip("Replace text")
        self.replaceButton.setAutoRaise(True)
        self.allButton = QToolButton(self)
        self.allButton.setToolTip("Replace all")
        self.allButton.setText("Replace all")
        self.allButton.setAutoRaise(True)
        # add replace elements to widget
        hbox = QHBoxLayout()
        hbox.addWidget(self.replaceLabel)
        hbox.addWidget(self.replaceEdit)
        hbox.addWidget(self.replaceButton)
        hbox.addWidget(self.allButton)
        vbox.addLayout(hbox)
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
        if not self.isVisible():
            self.show(False)
            self.setFocus(True)
        elif self.replaceLabel.isVisible():
            self.hideReplace()
        elif not self.hasFocus():
            self.setFocus(True)
        else:
            self.editor.setFocus(True)

    def toggleReplace(self):
        text = self.editor.textCursor().selectedText()
        if not text.isEmpty():
            self.searchEdit.setText(text)
            if self.isVisible():
                return
        if not self.replaceLabel.isVisible():
            self.show(True)
            self.setFocus(True)
        elif not self.hasFocus():
            self.setFocus(True)
        else:
            self.editor.setFocus(True)

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
            self.editor.setFocus(True)
        elif e.key() == Qt.Key_Tab:
            self.focusNextChild()

class CompletePopup(QObject):

    def __init__(self, parent, delay=1000, minchars=3, active=True):
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
        self.popup.setWindowFlags(Qt.Popup)
        self.popup.setFocusPolicy(Qt.NoFocus)
        self.popup.setFocusProxy(self.editor)
        self.connect(self.popup, SIGNAL("itemClicked(QTreeWidgetItem*, int)"),
                  self.doneCompletion)
        self.currentItem = ""
        if active:
            self.timer = QTimer(self)
            self.timer.setSingleShot(True)
            if isinstance(delay,int):
                self.timer.setInterval(delay)
            else:
                self.timer.setInterval(1000)
            self.connect(self.timer, SIGNAL("timeout()"), self.suggest, minchars)
            self.connect(self.editor, SIGNAL("textChanged()"), self.startTimer)
        else:
            self.timer = None

    def startTimer(self):
        if not self.timer is None:
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

    def showCompletion(self, choices):
        if len(choices) < 1:
            return
        if not self.timer is None:
            active = self.timer.isActive()
        else:
            active = True
        if len(choices) == 1 and active:
            self.replaceCurrentWord(choices[0])
            self.preventSuggest()
            self.emit(SIGNAL("doneCompletion(QString, QString)"),
            QString(unicode(choices[0])),QString())
            return
        pal = self.editor.palette()
        color = pal.color(QPalette.Disabled,
                          QPalette.WindowText)
        self.popup.setUpdatesEnabled(False)
        self.popup.clear()
        for i in sorted(choices):
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

    def doneCompletion(self):
        if not self.timer is None:
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
        if not self.timer is None:
            self.timer.stop()

    def suggest(self, minchars=1):
        block = self.editor.textCursor().block()
        text = block.text()
        if len(text) < minchars:
            return
        command = self.editor.currentCommand(block)
        linebuffer = command[0]
        if QString(linebuffer).trimmed().isEmpty():
            return
        cursor = command[1]
        token, start, end = complete.guessTokenFromLine(linebuffer, cursor)
        if len(token) < minchars:
            return
        self.move = len(token)
        comps = complete.completeToken(linebuffer, token, start, end)
        self.showCompletion(comps)

    #def getCurrentWord(self):
        #textCursor = self.editor.textCursor()
        #textCursor.movePosition(QTextCursor.StartOfWord, QTextCursor.KeepAnchor)
        #currentWord = textCursor.selectedText()
        #textCursor.setPosition(textCursor.anchor(), QTextCursor.MoveAnchor)
        #return currentWord

    def replaceCurrentWord(self, word):
        textCursor = self.editor.textCursor()
        textCursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, self.move)
        textCursor.removeSelectedText()
        textCursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        sel = textCursor.selectedText()
        if not word[-1] == sel and not sel.isEmpty():
            textCursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor)
        self.editor.setTextCursor(textCursor)
        self.editor.insertPlainText(word)


class BaseFrame(QFrame):

    def __init__(self, parent=None, tabwidth=4, autobracket=True,
                 autopopup=True, sidepanel=True, console=True):
        QFrame.__init__(self, parent)
        if console:
            self.edit = RConsole(self, tabwidth, autobracket)
        else:
            self.edit = REditor(self, tabwidth,autobracket)
        self.searchBar = SearchBar(self.edit, (not console))
        delay = QSettings().value("manageR/delay", 1000).toInt()[0]
        chars = QSettings().value("manageR/minimumchars", 3).toInt()[0]
        self.completePopup = CompletePopup(self.edit, delay, chars, autopopup)
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
#--------------------- Data structures and utilities --------------------------#
#------------------------------------------------------------------------------#

class Highlighter(QSyntaxHighlighter):

    Rules = []
    Formats = {}

    def __init__(self, parent=None):
        QSyntaxHighlighter.__init__(self, parent)
        #self.parent = parent
        if isinstance(parent, QPlainTextEdit):
            self.setDocument(parent.document())
        self.initializeFormats()
        Highlighter.Rules.append((QRegExp(
                r"[a-zA-Z_]+[a-zA-Z_\.0-9]*(?=[\s]*[(])"), "keyword"))
        #Highlighter.Rules.append((QRegExp(
                #"|".join([r"\b%s\b" % keyword for keyword in KEYWORDS])),
                #"keyword"))
        builtins = ["array", "character", "complex", "data.frame", "double",
                    "factor", "function", "integer", "list", "logical",
                    "matrix", "numeric", "vector", "numeric"]
        Highlighter.Rules.append((QRegExp(
                "|".join([r"\b%s\b" % builtin for builtin in builtins])),
                "builtin"))
        #Highlighter.Rules.append((QRegExp(
                #r"[a-zA-Z_\.][0-9a-zA-Z_\.]*[\s]*=(?=([^=]|$))"), "inbrackets"))
        constants = ["Inf", "NA", "NaN", "NULL", "TRUE", "FALSE"]
        Highlighter.Rules.append((QRegExp(
                "|".join([r"\b%s\b" % constant
                for constant in constants])), "constant"))
        Highlighter.Rules.append((QRegExp(
                r"\b[+-]?[0-9]+[lL]?\b"
                r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
                r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
                "number"))
        Highlighter.Rules.append((QRegExp(r"[\)\(]+|[\{\}]+|[][]+"),
                "delimiter"))
        Highlighter.Rules.append((QRegExp(
                r"[<]{1,2}\-"
                r"|\-[>]{1,2}"
                r"|=(?!=)"
                r"|\$"
                r"|\@"), "assignment"))
        Highlighter.Rules.append((QRegExp(
                r"([\+\-\*/\^\:\$~!&\|=>@^])([<]{1,2}\-|\-[>]{1,2})"
                r"|([<]{1,2}\-|\-[>]{1,2})([\+\-\*/\^\:\$~!&\|=<@])"
                r"|([<]{3}|[>]{3})"
                r"|([\+\-\*/\^\:\$~&\|@^])="
                r"|=([\+\-\*/\^\:\$~!<>&\|@^])"
                #r"|(\+|\-|\*|/|<=|>=|={1,2}|\!=|\|{1,2}|&{1,2}|:{1,3}|\^|@|\$|~){2,}"
                ),
                "syntax"))
        self.stringRe = QRegExp("(\'[^\']*\'|\"[^\"]*\")")
        self.stringRe.setMinimal(True)
        Highlighter.Rules.append((self.stringRe, "string"))
        Highlighter.Rules.append((QRegExp(r"#.*"), "comment"))
        Highlighter.Rules.append((QRegExp(r"^Error.*"), "error"))
        self.multilineSingleStringRe = QRegExp(r"""'(?!")""")
        self.multilineDoubleStringRe = QRegExp(r'''"(?!')''')
        self.bracketBothExpression = QRegExp(r"[\(\)]")
        self.bracketStartExpression = QRegExp(r"\(")
        self.bracketEndExpression = QRegExp(r"\)")

    def initializeFormats(self):
        baseFormat = QTextCharFormat()
        baseFormat.setFontFamily(QSettings().value("manageR/fontfamily", "DejaVu Sans Mono").toString())
        baseFormat.setFontPointSize(QSettings().value("manageR/fontsize", 10).toInt()[0])
        for name in ("normal", "keyword", "builtin", "constant",
                "delimiter", "comment", "string", "number", "error",
                "assignment", "syntax"):
            format = QTextCharFormat(baseFormat)
            format.setForeground(
                            QColor(QSettings().value("manageR/%sfontcolor" % name).toString()))
            if name == "syntax":
                format.setFontUnderline(QSettings().value("manageR/%sfontunderline" % name).toBool())
            else:
                if QSettings().value("manageR/%sfontbold" % name).toBool():
                    format.setFontWeight(QFont.Bold)
            format.setFontItalic(QSettings().value("manageR/%sfontitalic" % name).toBool())
            Highlighter.Formats[name] = format

        format = QTextCharFormat(baseFormat)
        if QSettings().value("manageR/assignmentfontbold").toBool():
            format.setFontWeight(QFont.Bold)
        format.setForeground(QColor(QSettings().value("manageR/assignmentfontcolor").toString()))
        format.setFontItalic(QSettings().value("manageR/%sfontitalic" % name).toBool())
        Highlighter.Formats["inbrackets"] = format

    def highlightBlock(self, text):
        NORMAL, MULTILINESINGLE, MULTILINEDOUBLE, ERROR = range(4)
        INBRACKETS, INBRACKETSSINGLE, INBRACKETSDOUBLE = range(4,7)

        textLength = text.length()
        prevState = self.previousBlockState()

        cursor = self.parent().textCursor()
        block = cursor.block()

        self.setFormat(0, textLength, Highlighter.Formats["normal"])

        if self.parent().isHighlightingSuspended():
            return

        for regex, format in Highlighter.Rules:
            i = regex.indexIn(text)
            while i >= 0:
                length = regex.matchedLength()
                self.setFormat(i, length, Highlighter.Formats[format])
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
                self.setFormat(startIndex + i, bracketLength, Highlighter.Formats[format])
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
                self.setFormat(0, i + 1, Highlighter.Formats["string"])
            elif i > -1 and not text.contains("#"):
                self.setCurrentBlockState(state)
                self.setFormat(i, text.length(), Highlighter.Formats["string"])

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
                self.append(QString(line))
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
    app.setWindowIcon(QIcon(":icon.png"))
    QgsApplication.setPrefixPath('/usr/local', True)
    QgsApplication.initQgis()
    #app.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))
    window = MainWindow(parent=None, iface=None, console=True)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()