#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import os
import re
import sys
import resources

from PyQt4.QtCore import (PYQT_VERSION_STR, QByteArray, QDir, QEvent,
        QFile, QFileInfo, QIODevice, QPoint, QProcess, QRegExp,
        QSettings, QString, QT_VERSION_STR, QTextStream, QThread,
        QTimer, QUrl, QVariant, Qt, SIGNAL, QStringList, QMimeData)
from PyQt4.QtGui import (QAction, QApplication, QButtonGroup, QCheckBox,
        QColor, QColorDialog, QComboBox, QCursor, QDesktopServices,
        QDialog, QDialogButtonBox, QFileDialog, QFont, QFontComboBox,
        QFontMetrics, QGridLayout, QHBoxLayout, QIcon, QInputDialog,
        QKeySequence, QLabel, QLineEdit, QListWidget, QMainWindow,
        QMessageBox, QPixmap, QPushButton, QRadioButton,
        QRegExpValidator, QShortcut, QSpinBox, QSplitter,
        QSyntaxHighlighter, QTabWidget, QTextBrowser, QTextCharFormat,
        QTextCursor, QTextDocument, QTextEdit, QToolTip, QVBoxLayout,
        QWidget, QDockWidget, QToolButton, QSpacerItem, QSizePolicy,
        QPalette, QSplashScreen)

try:
  import rpy2.robjects as robjects
#  import rpy2.rinterface as rinterface
except ImportError:
  QMessageBox.warning( None , "manageR", "Unable to load manageR: Required package rpy2 was unable to load"
  + "\nPlease ensure that both R, and the corresponding version of Rpy2 are correctly installed.")

__version__ = "0.9.11"
__license__ = """<font color=green>\
Copyright &copy; 2008-9 Carson J. Q. Farmer. All rights reserved.</font>

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation, version 2 of the License, or version 3 of the
License or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
<i>without any warranty</i>; without even the implied warranty of
<i>merchantability</i> or <i>fitness for a particular purpose</i>. 
See the <a href="http://www.gnu.org/licenses/">GNU General Public
License</a> for more details."""

__welcomestring__ = """Welcome to manageR %s
QGIS interface to the R statistical analysis program
Copyright (C) 2009  Carson Farmer 
Licensed under the terms of GNU GPL 2\nmanageR is free software; 
you can redistribute it and/or modify it under the terms of 
the GNU General Public License as published by the Free Software Foundation; 
either version 2 of the License, or (at your option) any later version.
Currently running %s""" % (__version__,robjects.r.version[12][0])

KEYWORDS = ["break", "else", "for", "if", "in", "next", "repeat", 
            "return", "switch", "try", "while", "print", "return",
            "not", "library", "attach", "detach", "ls", "as"]

BUILTINS = ["array", "character", "complex", "data.frame", "double", 
            "factor", "function", "integer", "list", "logical", 
            "matrix", "numeric", "vector"] 

CONSTANTS = ["Inf", "NA", "NaN", "NULL", "TRUE", "FALSE"]

TIMEOUT = 5000
ICONS = {}
PIXMAPS = {}
Config = {}
CAT = {} # Completions And Tooltips
MIN_COMPLETION_LEN = 3
MAX_TOOLTIP_LEN = 1000
FROM_IMPORT_RE = re.compile(r"from\s+([\w.]+)\s+import\s+(.*)")
WORDS = set()
WORD_RE = re.compile(r"[\W+.]")
MIN_WORD_LEN = 3
MAX_WORD_LEN = 64
CATABLE_LINE_RE = QRegExp(r"\b(?:import|def|class)\s+")
CLASS_OR_DEF_RE = re.compile(r"(class|def) ([^\W(:]+)[:(]")


def trimQString(qstr, trimText):
    while qstr.startsWith(trimText):
        qstr = qstr.mid(len(trimText))
    while qstr.endsWith(trimText):
        qstr.chop(len(trimText))
    return qstr


def loadConfig():
    def setDefaultString(name, default):
        value = settings.value(name).toString()
        if value.isEmpty():
            value = default
        Config[name] = value

    settings = QSettings()
    for name in ("window", "console"):
        Config["%swidth" % name] = settings.value("%swidth" % name,
                QVariant(QApplication.desktop()
                         .availableGeometry().width() / 2)).toInt()[0]
        Config["%sheight" % name] = settings.value("%sheight" % name,
                QVariant(QApplication.desktop()
                         .availableGeometry().height() / 2)).toInt()[0]
        Config["%sy" % name] = settings.value("%sy" % name,
                QVariant(0)).toInt()[0]
    Config["toolbars"] = settings.value("toolbars").toByteArray()
    Config["consolex"] = settings.value("consolex",
                                      QVariant(0)).toInt()[0]
    Config["windowx"] = settings.value("windowx",
            QVariant(QApplication.desktop()
                            .availableGeometry().width() / 2)).toInt()[0]
    Config["remembergeometry"] = settings.value("remembergeometry",
            QVariant(True)).toBool()
    #Config["startwithConsole"] = settings.value("startwithConsole",
            #QVariant(True)).toBool()
    #Config["showwindowinfo"] = settings.value("showwindowinfo",
            #QVariant(True)).toBool()
    setDefaultString("newfile", "")
    Config["backupsuffix"] = settings.value("backupsuffix",
            QVariant(".bak")).toString()
    setDefaultString("beforeinput", ">")
    setDefaultString("afteroutput", "+")
    Config["cwd"] = settings.value("cwd", QVariant(".")).toString()
    #Config["tooltipsize"] = settings.value("tooltipsize",
            #QVariant(150)).toInt()[0]
    #Config["maxlinestoscan"] = settings.value("maxlinestoscan",
            #QVariant(5000)).toInt()[0]
    #Config["pythondocpath"] = settings.value("pythondocpath", 
            #QVariant("http://docs.python.org")).toString()
    #Config["autohidefinddialog"] = settings.value("autohidefinddialog",
            #QVariant(True)).toBool()
    Config["findcasesensitive"] = settings.value("findcasesensitive",
            QVariant(False)).toBool()
    Config["findwholewords"] = settings.value("findwholewords",
            QVariant(False)).toBool()
    Config["tabwidth"] = settings.value("tabwidth",
            QVariant(4)).toInt()[0]
    Config["fontfamily"] = settings.value("fontfamily",
            QVariant("Bitstream Vera Sans Mono")).toString()
    Config["fontsize"] = settings.value("fontsize",
            QVariant(10)).toInt()[0]
    for name, color, bold, italic in (
            ("normal", "#000000", False, False),
            ("keyword", "#000080", True, False),
            ("builtin", "#0000A0", False, False),
            ("constant", "#0000C0", False, False),
            ("delimiter", "#0000E0", False, False),
            ("comment", "#007F00", False, True),
            ("string", "#808000", False, False),
            ("number", "#924900", False, False),
            ("error", "#FF0000", False, False),
            ("assignment", "#50621A", False, False)):
        Config["%sfontcolor" % name] = settings.value(
                "%sfontcolor" % name, QVariant(color)).toString()
        Config["%sfontbold" % name] = settings.value(
                "%sfontbold" % name, QVariant(bold)).toBool()
        Config["%sfontitalic" % name] = settings.value(
                "%sfontitalic" % name, QVariant(italic)).toBool()
    setDefaultString("backgroundcolor", "#FFFFFF")
    setDefaultString("delay", 5000)
    setDefaultString("consolestartup", "")

def saveConfig():
    settings = QSettings()
    for key, value in Config.items():
        settings.setValue(key, QVariant(value))

def checkForCAT(line):
    # We can't use CAT to keep track of which modules we have processed.
    # This is because if the user does "import os", one of the names we
    # will get is "os.path", which then goes into CAT; so if later the
    # user did "import os.path", the name "os.path" will already be in
    # CAT (from the "import os") and wouldn't be looked for. So we keep
    # a separate dictionary of modules that we've done in MODULES.
    line = line.strip()
    if line.startswith("import "):
        line = line[len("import "):]
        for mname in [mname.strip() for mname in line.split(",")]:
            if not MODULES.get(mname, False):
                # We have not done this one
                _updateCAT(mname)
    else:
        match = FROM_IMPORT_RE.match(line)
        if match:
            if match.group(1) == "__future__" or not match.group(2):
                return
            for name in [x for x in
                         match.group(2).replace(",", " ").split()]:
                mname = "%s.%s" % (match.group(1), name)
                if not MODULES.get(mname, False):
                    # We have not done this one
                    _updateCAT(mname)
                i = mname.rfind(".")
                while i > -1:
                    mname = mname[:i]
                    if not MODULES.get(mname, False):
                        # We have not done this one
                        _updateCAT(mname)
                    i = mname.rfind(".")
        else:
            for word in WORD_RE.split(line):
                if (not word or
                    len(word) < MIN_WORD_LEN or
                    len(word) > MAX_WORD_LEN or
                    word in CAT or word in WORDS):
                    continue
                WORDS.add(word)


def _updateCAT(mname):
    try:
        MODULES[mname] = True
        CAT.setdefault(mname, {})
        WORDS.discard(mname)
        module = __import__(mname)
        components = []
        if "." in mname:
            for component in mname.split(".")[1:]:
                module = getattr(module, component)
                components.append(component)
        for aname in dir(module):
            if aname.startswith("_"):
                continue
            fullname = "%s.%s" % (mname, aname)
            CAT.setdefault(fullname, "")
            WORDS.discard(fullname)
            CAT.setdefault(aname, "")
            WORDS.discard(aname)
            for component in components:
                CAT.setdefault("%s.%s" % (component, aname), "")
                WORDS.discard("%s.%s" % (component, aname))
            # PyQt4 classes don't have docstrings
            if not mname.startswith(("Qt", "PyQt4")):
                try:
                    tip = eval("sys.modules['%s'].%s.__doc__" % (
                                mname, aname))
                    if tip is not None:
                        tip = (tip[:MAX_TOOLTIP_LEN].strip()
                               .replace("\n\n", "<p>"))
                        CAT[fullname] = tip
                        if CAT[aname] == "":    # First one (i.e., builtin)
                            CAT[aname] = tip    # wins
                        for component in components: # Last one wins
                            CAT["%s.%s" % (component, aname)] = tip
                except:
                    pass
            try:
                for bname in eval("dir(sys.modules['%s'].%s)" % (
                        mname, aname)):
                    if bname.startswith("_"):
                        continue
                    cname = "%s.%s" % (fullname, bname)
                    CAT.setdefault(cname, "")
                    WORDS.discard(cname)
                    # PyQt4 classes don't have docstrings
                    if not mname.startswith(("Qt", "PyQt4")):
                        tip = None
                        try:
                            tip = eval(
                                    "sys.modules['%s'].%s.%s.__doc__" % (
                                    mname, aname, bname))
                        except:
                            pass
                        if tip is None:
                            try:
                                tip = eval(
                                        "sys.modules['%s'].%s.__doc__" % (
                                        mname, aname))
                            except:
                                pass
                        if tip is not None:
                            tip = (tip[:MAX_TOOLTIP_LEN].strip()
                                   .replace("\n\n", "<p>"))
                            CAT[cname] = tip
            except:
                pass
    except:
        pass


class HelpForm(QDialog):

    def __init__(self, parent=None):
        super(HelpForm, self).__init__(parent)
        self.setAttribute(Qt.WA_GroupLeader)
        self.setAttribute(Qt.WA_DeleteOnClose)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(
u"""
<center><h2>manageR %s documentation</h2>
<h3>Interface to the R statistical programming environment</h3>
<h4>Copyright &copy; 2009 Carson J.Q. Farmer
<br/>carson.farmer@gmail.com
<br/><a href='http://www.ftools.ca/manageR'>www.ftools.ca/manageR</a></h4></center>
<h4>Description:</h4>
<b>manageR</b> adds comprehensive statistical capabilities to <b>Quantum GIS</b> by 
loosely coupling <b>QGIS</b> with the R statistical programming environment.
<h4>Features:</h4>
<ul><li>Perform complex statistical analysis functions on raster, vector and spatial database formats</li>
<li>Use the R statistical environment to graph, plot, and map spatial and aspatial data from within <b>QGIS</b></li>
<li>Export R (sp) vector layers directly to <b>QGIS</b> map canvas as <b>QGIS</b> vector layers</li>
<li>Read <b>QGIS</b> vector layers directly from map canvas as R (sp) vector layers, allowing analysis to be carried out on any vector format supported by <b>QGIS</b></li>
<li>Perform all available R commands from within <b>QGIS</b>, including multi-line commands</li>
<li>Visualise R commands clearly and cleanly using any one of the four included syntax highlighting themes</li>
<li>Create, edit, and save R scripts for complex statistical and computational operations</li></ul>
<h4>Usage:</h4>
<ul><li><tt>Ctrl+L</tt> : Import selected <b>l</b>ayer</li>
<li><tt>Ctrl+T</tt> : Import attribute <b>t</b>able of selected layer</li>
<li><tt>Ctrl+M</tt> : Export R layer to <b>m</b>ap canvas</li>
<li><tt>Ctrl+D</tt> : Export R layer to <b>d</b>isk</li>
<li><tt>Ctrl+Return</tt> : Send (selected) commands from <b>EditR</b> window to <b>manageR</b> console</li>
<h4>Details:</h4>
<p>
Use <tt>Ctrl+L</tt> to import the currently selected layer in the <b>QGIS</b> 
layer list into the <b>manageR</b> environment. To import only the attribute 
table of the selected layer, use <tt>Ctrl+T</tt>. Exporting R layers 
from the <b>manageR</b> environment is done via <tt>Ctrl-M</tt> and <tt>Ctrl-D</tt>, 
where M signifies exporting to the map canvas, and D signifies exporting to disk. 
Multi-line R commands will automatically be recognised by the <b>manageR</b> 
console, however, to manaully enter multi-line commands, use the <tt>Shift</tt> 
modifier when typing <tt>Return</tt> to signify continuation of command on the 
following line.
</p>
<p>
Use <tt>Ctrl+R</tt> to send commands from the an <b>EditR</b> window to the <b>manageR</b> 
console. If <b>EditR</b> window contains selected text, only this text will be sent 
to the <b>manageR</b> console, otherwise, all text is sent. The <b>EditR</b> window 
also contains tools for creating, loading, and saving R scripts, as well as 
basic functionality such as undo, redo, cut, copy, and paste. These tools are also 
available via standard keyboard shortcuts (e.g. <tt>Ctrl+C</tt> to copy text) and 
are outlined in detail in the <tt>Key bindings</tt> section.
</p>
<h4>Additional tools:</h4>
<p>
If enabled, command completion suggestions are automatically shown after %d seconds 
based on the current work. This can also be manually activated using <b>Ctrl+Space</b>. 
In addition, a tooltip will appear if one is available for the selected command.
Autocompletion and tooltips are available for R functions and commands within 
libraries that are automatically loaded by R, or <b>manageR</b> (see the
File\N{RIGHTWARDS ARROW}Configure dialog's At Startup tab), as well as any additional 
libraries loaded after the <b>manageR</b> session has started. (This makes loading 
libraries with many builtin functions or additional libraries slightly longer than 
in a normal R session). It is possible to turn off autocompletion by unchecking 
File\N{RIGHTWARDS ARROW}Configure dialog's General tab's enable autocompletion checkbox.
</p>
<p>
A Find and Replace toolbar is available for both the <b>manageR</b> console and <b>EditR</b> 
window (the replace functionality is only available in <b>EditR</b>). To search for 
the next occurrence of the text or phrase in the 'Find toolbar', type <tt>Enter</tt> 
or click the 'Next' button. Conversely, click the 'Previous' button to search backwards. To 
replace text as it is found, simply type the replacement text in the 'Replace' line edit, 
click 'Replace'. To replace all occurances of the found text, click 'Replace all'. All 
searches can be refined by using the 'Case sensitive' and 'Whole words' check boxes.
</p>
Key bindings:
<ul>
<li><b>\N{UPWARDS ARROW}</b> In the <b>manageR</b> console, show the previous command
from the command history. In the <b>EditR</b> windows, move up one line.
<li><b>\N{DOWNWARDS ARROW}</b> In the <b>manageR</b> console, show the next command
from the command history. In the <b>EditR</b> windows, move down one line.
<li><b>\N{LEFTWARDS ARROW}</b> Move the cursor left one character
<li><b>Ctrl+\N{LEFTWARDS ARROW}</b> Move the cursor left one word
<li><b>\N{RIGHTWARDS ARROW}</b> Move the cursor right one character
<li><b>Ctrl+\N{RIGHTWARDS ARROW}</b> Move the cursor right one word
<li><b>Ctrl+]</b> Indent the selected text (or the current line) by %d spaces
<li><b>Ctrl+[</b> Unindent the selected text (or the current line) by %d spaces
<li><b>Ctrl+A</b> Select all the text
<li><b>Backspace</b> Delete the character to the left of the cursor
<li><b>Ctrl+C</b> In the <b>manageR</b> console, if the cursor is in the command line, clear
current command(s), otherwise copy the selected text to the clipboard (same for <b>EditR</b> 
windows.
<li><b>Delete</b> Delete the character to the right of the cursor
<li><b>End</b> Move the cursor to the end of the line
<li><b>Ctrl+End</b> Move the cursor to the end of the file
<li><b>Ctrl+Return</b> In an <b>EditR</b> window, execute the (selected) code/text
<li><b>Ctrl+F</b> Pop up the Find toolbar
<li><b>Ctrl+R</b> In an <b>EditR</b> window, pop up the Find and Replace toolbar
<li><b>Home</b> Move the cursor to the beginning of the line
<li><b>Ctrl+Home</b> Move the cursor to the beginning of the file
<li><b>Ctrl+K</b> Delete to the end of the line
<li><b>Ctrl+H</b> Pop up the 'Goto line' dialog
<li><b>Ctrl+B</b> Go to the matching ([{&lt; or &gt;}]). The matcher looks
at the character preceding the cursor, and if it is a match character the
cursor moves so that the matched character precedes the cursor. If no
suitable character is preceding the cursor, but there is a suitable
character following the cursor, the cursor will advance one character (so
that the match character now precedes it), and works as just described.
(In other words the matching is after\N{LEFT RIGHT ARROW}after.)
<li><b>Ctrl+N</b> Open a new editor window
<li><b>Ctrl+O</b> Open a file open dialog to open an R script
<li><b>Ctrl+Space</b> Pop up a list of possible completions for
the current word. Use the up and down arrow keys and the page up and page
up keys (or the mouse) to navigate; click <b>Enter</b> to accept a
completion or <b>Esc</b> to cancel.
<li><b>PageUp</b> Move up one screen
<li><b>PageDown</b> Move down one screen
<li><b>Ctrl+Q</b> Terminate manageR; prompting to save any unsaved changes
for every <b>EditR</b> window for which this is necessary. If the user cancels
any save unsaved changes message box, manageR will not terminate.
<li><b>Ctrl+S</b> Save the current file
<li><b>Ctrl+V</b> Paste the clipboard's text
<li><b>Ctrl+W</b> Close the current file; prompting to save any unsaved
changes if necessary
<li><b>Ctrl+X</b> Cut the selected text to the clipboard
<li><b>Ctrl+Z</b> Undo the last editing action
<li><b>Ctrl+Shift+Z</b> Redo the last editing action
</ul>
Hold down <b>Shift</b> when pressing movement keys to select the text moved over.
<br>
Press <b>Esc</b> to close this window.
""" % (__version__, 5000,#Config["delay"], 
      Config["tabwidth"], Config["tabwidth"]))
        layout = QVBoxLayout()
        layout.setMargin(0)
        layout.addWidget(browser)
        self.setLayout(layout)
        self.resize(500, 500)
        QShortcut(QKeySequence("Escape"), self, self.close)
        self.setWindowTitle("manageR - Help")


class RFinder(QWidget):

    def __init__(self, parent, document):
        QWidget.__init__(self, parent)
        # initialise standard settings
        self.document = document
        grid = QGridLayout(self )
        self.edit = QLineEdit(self)
        font = QFont(Config["fontfamily"], Config["fontsize"])
        font.setFixedPitch( True )
        find_label = QLabel( "Find:")
        self.edit.setFont(font)
        self.edit.setToolTip("Find text")
        self.next = QToolButton(self)
        self.next.setText("Next")
        self.next.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.next.setIcon(QIcon(":mActionNext.png"))
        self.next.setToolTip("Find next")
        self.previous = QToolButton( self )
        self.previous.setToolTip("Find previous")
        self.previous.setText("Previous")
        self.previous.setIcon(QIcon(":mActionPrevious.png"))
        self.previous.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.whole_words = QCheckBox()
        self.whole_words.setText("Whole words only")
        self.case_sensitive = QCheckBox()
        self.case_sensitive.setText("Case sensitive")
        find_horiz = QHBoxLayout()
        find_horiz.addWidget(find_label)
        find_horiz.addWidget(self.edit)
        find_horiz.addWidget(self.previous)
        find_horiz.addWidget(self.next)
        options_horiz = QHBoxLayout()
        options_horiz.addWidget(self.whole_words)
        options_horiz.addWidget(self.case_sensitive)
        options_horiz.insertSpacing(0,40)
        grid.addLayout(options_horiz, 0, 2, 1, 1)
        grid.addLayout(find_horiz, 1, 0, 1, 3)
        self.replace_label = QLabel("Replace:")
        self.replace_edit = QLineEdit(self)
        self.replace_edit.setFont(font)
        self.replace_edit.setToolTip("Replace text")
        self.replace = QToolButton(self)
        self.replace.setText("Replace")
        self.replace.setToolTip("Replace text")
        self.replace_all = QToolButton(self)
        self.replace_all.setToolTip("Replace all")
        self.replace_all.setText("Replace all")
        replace_horiz = QHBoxLayout()
        replace_horiz.addWidget(self.replace_label)
        replace_horiz.addWidget(self.replace_edit)
        replace_horiz.addWidget(self.replace)
        replace_horiz.addWidget(self.replace_all)
        grid.addLayout(replace_horiz, 2, 0, 1, 3)
        self.setFocusProxy(self.edit)
        self.setVisible(False)
        
        self.connect(self.next, SIGNAL("clicked()"), self.findNext)
        self.connect(self.previous, SIGNAL("clicked()"), self.findPrevious)
        self.connect(self.replace, SIGNAL("clicked()"), self.replaceNext)
        self.connect(self.edit, SIGNAL("returnPressed()"), self.findNext)
        self.connect(self.replace_all, SIGNAL("clicked()"), self.replaceAll)
    
    def find(self, forward):
        if not self.document:
            return False
        text = QString(self.edit.text())
        found = False
        if text == "":
            return False
        else:
            flags = QTextDocument.FindFlag()
            if self.whole_words.isChecked():
                flags = (flags|QTextDocument.FindWholeWords)
            if self.case_sensitive.isChecked():
                flags = (flags|QTextDocument.FindCaseSensitively)
            if not forward:
                flags = (flags|QTextDocument.FindBackward)
                fromPos = self.document.toPlainText().length() - 1
            else:
                fromPos = 0
            if not self.document.find(text, flags):
                cursor = QTextCursor(self.document.textCursor())
                selection = cursor.hasSelection()
                if selection:
                    start = cursor.selectionStart()
                    end = cursor.selectionEnd()
                else:
                    pos = cursor.position()
                cursor.setPosition(fromPos)
                self.document.setTextCursor(cursor)
                if not self.document.find(text, flags):
                    if selection:
                        cursor.setPosition(start, QTextCursor.MoveAnchor)
                        cursor.setPosition(end, QTextCursor.KeepAnchor)
                    else:
                        cursor.setPosition(pos)
                    self.document.setTextCursor(cursor)
                    return False
                elif selection:
                    cursor = QTextCursor(self.document.textCursor())
                    if start == cursor.selectionStart():
                        return False
        return True
          
    def findNext(self):
        return self.find(True)
      
    def findPrevious(self):
        return self.find(False)
          
    def showReplace(self):
        self.replace_edit.setVisible(True)
        self.replace.setVisible(True)
        self.replace_all.setVisible(True)
        self.replace_label.setVisible(True)

    def hideReplace(self):
        self.replace_edit.setVisible(False)
        self.replace.setVisible(False)
        self.replace_all.setVisible(False)
        self.replace_label.setVisible(False)

    def replaceNext(self):
        cursor = QTextCursor(self.document.textCursor())
        selection = cursor.hasSelection()
        if selection:
            text = QString(cursor.selectedText())
            current = QString(self.edit.text())
            replace = QString(self.replace_edit.text())
            if text == current:
                cursor.insertText(replace)
                cursor.select(QTextCursor.WordUnderCursor)
        else:
            return self.findNext()
        self.findNext()
        return True

    def replaceAll( self ):
        while self.findNext():
            self.replaceText()
        self.replaceText()


class RHighlighter(QSyntaxHighlighter):

    Rules = []
    Formats = {}

    def __init__(self, parent=None):
        super(RHighlighter, self).__init__(parent)
        self.parent = parent
        self.initializeFormats()

        RHighlighter.Rules.append((QRegExp(
                "|".join([r"\b%s\b" % keyword for keyword in KEYWORDS])),
                "keyword"))
        RHighlighter.Rules.append((QRegExp(
                "|".join([r"\b%s\b" % builtin for builtin in BUILTINS])),
                "builtin"))
        RHighlighter.Rules.append((QRegExp(
                "|".join([r"\b%s\b" % constant
                for constant in CONSTANTS])), "constant"))
        RHighlighter.Rules.append((QRegExp(
                r"\b[+-]?[0-9]+[lL]?\b"
                r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
                r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
                "number"))
        RHighlighter.Rules.append((QRegExp(
                r"(<){1,2}-"), "assignment"))
        RHighlighter.Rules.append((QRegExp(r"[\)\(]+|[\{\}]+|[][]+"),
                "delimiter"))
        RHighlighter.Rules.append((QRegExp(r"#.*"), "comment"))
        stringRe = QRegExp(r"""(?:'[^']*'|"[^"]*")""")
        stringRe.setMinimal(True)
        RHighlighter.Rules.append((stringRe, "string"))
        self.stringRe = QRegExp(r"""(:?"["]".*"["]"|'''.*''')""")
        self.stringRe.setMinimal(True)
        RHighlighter.Rules.append((self.stringRe, "string"))
        self.multilineSingleStringRe = QRegExp(r"""'(?!")""")
        self.multilineDoubleStringRe = QRegExp(r'''"(?!')''')

    @staticmethod
    def initializeFormats():
        baseFormat = QTextCharFormat()
        baseFormat.setFontFamily(Config["fontfamily"])
        baseFormat.setFontPointSize(Config["fontsize"])
        for name in ("normal", "keyword", "builtin", "constant",
                "delimiter", "comment", "string", "number", "error",
                "assignment"):
            format = QTextCharFormat(baseFormat)
            format.setForeground(
                            QColor(Config["%sfontcolor" % name]))
            if Config["%sfontbold" % name]:
                format.setFontWeight(QFont.Bold)
            format.setFontItalic(Config["%sfontitalic" % name])
            RHighlighter.Formats[name] = format

    def highlightBlock(self, text):
        NORMAL, MULTILINESINGLE, MULTILINEDOUBLE, ERROR = range(4)

        textLength = text.length()
        prevState = self.previousBlockState()

        self.setFormat(0, textLength,
                       RHighlighter.Formats["normal"])

        if text.startsWith("Error: "):
            self.setCurrentBlockState(ERROR)
            self.setFormat(0, textLength,
                           RHighlighter.Formats["error"])
            return
        if (prevState == ERROR and
            not (text.startsWith(Config["beforeinput"]) or text.startsWith("#"))):
            self.setCurrentBlockState(ERROR)
            self.setFormat(0, textLength,
                           RHighlighter.Formats["error"])
            return

        for regex, format in RHighlighter.Rules:
            i = regex.indexIn(text)
            while i >= 0:
                length = regex.matchedLength()
                self.setFormat(i, length,
                               RHighlighter.Formats[format])
                i = regex.indexIn(text, i + length)

        self.setCurrentBlockState(NORMAL)

        if text.indexOf(self.stringRe) != -1:
            return
        # This is fooled by triple quotes inside single quoted strings
        for i, state in ((text.indexOf(self.multilineSingleStringRe),
                          MULTILINESINGLE),
                         (text.indexOf(self.multilineDoubleStringRe),
                          MULTILINEDOUBLE)):
            if self.previousBlockState() == state:
                if i == -1:
                    i = text.length()
                    self.setCurrentBlockState(state)
                self.setFormat(0, i + 1,     
                               RHighlighter.Formats["string"])
            elif i > -1:
                self.setCurrentBlockState(state)
                self.setFormat(i, text.length(),
                               RHighlighter.Formats["string"])

    def rehighlight(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QSyntaxHighlighter.rehighlight(self)
        QApplication.restoreOverrideCursor()


class REditor(QTextEdit):
    def __init__(self, parent, tabwidth=4):
        super(REditor, self).__init__(parent)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.indent = 0
        self.tabwidth = tabwidth
        self.completionListWidget = None
        self.prefix = ""
        self.classes = set()
        self.defs = set()
        self.completionOffset = QFontMetrics(
                    self.font()).width("x")

    def event(self, event):
        indent = " " * self.tabwidth
        if event.type() == QEvent.KeyPress:
            #if event.key() == Qt.Key_Backspace:
                #line = self.currentLine()
                #if len(line) >= tabwidth and line.endsWith(indent):
                    #userCursor = self.textCursor()
                    #for _ in range(tabwidth):
                        #userCursor.deletePreviousChar()
                    #self.indent = max(0, self.indent - 1)
                    #return True
            if event.key() == Qt.Key_Tab:
                if not self.tabChangesFocus():
                    cursor = self.textCursor()
                    cursor.movePosition(
                            QTextCursor.PreviousCharacter,
                            QTextCursor.KeepAnchor)
                    if cursor.selectedText().trimmed().isEmpty():
                        cursor = self.textCursor()
                        cursor.insertText(indent)
                    #else:
                        #self.complete()
                    return True
                # else leave for base class to handle
            elif event.key() in (Qt.Key_Enter,
                                 Qt.Key_Return):
                userCursor = self.textCursor()
                cursor = QTextCursor(userCursor)
                cursor.movePosition(QTextCursor.End)
                insert = "\n"
                cursor = QTextCursor(userCursor)
                cursor.movePosition(QTextCursor.StartOfLine)
                cursor.movePosition(QTextCursor.EndOfLine,
                                    QTextCursor.KeepAnchor)
                line = cursor.selectedText()
                if line.startsWith(indent):
                    for c in line:
                        if c == " ":
                            insert += " "
                        else:
                            break
                userCursor.insertText(insert)
                return True
                # Fall through to let the base class handle the movement
            self.gotoMatching()
        return QTextEdit.event(self, event)

    def gotoLine(self):
        cursor = self.textCursor()
        lino, ok = QInputDialog.getInteger(self,
                            "editR - Goto line",
                            "Goto line:", cursor.blockNumber() + 1,
                            1, self.document().blockCount())
        if ok:
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down,
                    QTextCursor.MoveAnchor, lino - 1)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()


    def gotoMatching(self):
        # move the cursor to the matching ()[]<>{} or do nothing
        newfrmt = QTextCharFormat()
        newfrmt.setFontWeight(QFont.Bold)
        OPEN = "([<{"
        CLOSE = ")]>}"
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.PreviousCharacter,
                            QTextCursor.KeepAnchor)
        c = unicode(cursor.selectedText())
        if c not in OPEN + CLOSE:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.NextCharacter,
                                QTextCursor.KeepAnchor)
            c = unicode(cursor.selectedText())
            if c in OPEN + CLOSE:
                #self.setTextCursor(cursor)
                cursor.mergeCharFormat(newfrmt)
            else:
                return
        i = OPEN.find(c)
        if i > -1:
            movement = QTextCursor.NextCharacter
            stack = 0
            target = CLOSE[i]
        else:
            i = CLOSE.find(c)
            if i == -1:
                return
            movement = QTextCursor.PreviousCharacter
            stack = -1
            target = OPEN[i]
        cursor = self.textCursor()
        while (not (movement == QTextCursor.NextCharacter and
                    cursor.atEnd()) and
               not (movement == QTextCursor.PreviousCharacter and
                    cursor.atStart())):
            cursor.clearSelection()
            cursor.movePosition(movement, QTextCursor.KeepAnchor)
            x = unicode(cursor.selectedText())
            if not x:
                break
            if x == c:
                stack += 1
            elif x == target:
                if stack == 0:
                    cursor.mergeCharFormat(newfrmt)
                    cursor.clearSelection()
                    if movement == QTextCursor.PreviousCharacter:
                        cursor.movePosition(
                                QTextCursor.NextCharacter)
                    #self.setTextCursor(cursor)
                    
                    break
                else:
                    stack -= 1

    def execute(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            commands = cursor.selectedText().replace(u"\u2029", "\n")
        else:
            commands = self.toPlainText()
        if not commands.isEmpty():
            mime = QMimeData()
            mime.setText(commands)
            MainWindow.Console.editor.insertFromMimeData(mime)
            MainWindow.Console.editor.execute(commands)

    def indentRegion(self):
        self._walkTheLines(True, " " * self.tabwidth)


    def unindentRegion(self):
        self._walkTheLines(False, " " * self.tabwidth)


    def commentRegion(self):
        self._walkTheLines(True, "# ")


    def uncommentRegion(self):
        self._walkTheLines(False, "# ")


    def _walkTheLines(self, insert, text):
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
                cursor.insertText(text)
            else:
                cursor.movePosition(QTextCursor.NextCharacter,
                        QTextCursor.KeepAnchor, len(text))
                if cursor.selectedText() == text:
                    cursor.removeSelectedText()
            block = block.next()
            if block.position() > end:
                break
        userCursor.endEditBlock()

    def complete(self):
        pass


class RConsole(QTextEdit):
    def __init__(self, parent):
        super(RConsole, self).__init__(parent)
        # initialise standard settings
        self.setTextInteractionFlags( Qt.TextEditorInteraction)
        self.setAcceptDrops(False)
        self.setMinimumSize(30, 30)
        self.parent = parent
        #self.setTextFont()
        self.setUndoRedoEnabled(False)
        self.setAcceptRichText(False)
        #self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        #self.scrollbar = self.verticalScrollBar()
        self.highlighter = RHighlighter(self.document())
        # initialise required variables
        self.history = QStringList()
        self.historyIndex = 0
        self.runningCommand = QString()
        # prepare prompt
        self.reset()
        self.setPrompt(Config["beforeinput"]+" ", Config["afteroutput"]+" ")
        self.cursor = self.textCursor()
        #QObject.connect( self, SIGNAL( "textChanged()" ), self.moveToEnd )

    def reset(self):
        # clear all contents
        self.clear()
        # init attributes
        self.runningCommand.clear()
        self.historyIndex = 0
        self.history.clear()

    def setPrompt(self, newPrompt = "> ", 
        alternatePrompt = "+ ", display = False):
        self.defaultPrompt = newPrompt
        self.alternatePrompt = alternatePrompt
        self.currentPrompt = self.defaultPrompt
        self.currentPromptLength = len(self.currentPrompt)
        if display:
            self.displayPrompt()

    def switchPrompt(self, default = True):
        if default:
            self.currentPrompt = self.defaultPrompt
        else:
            self.currentPrompt = self.alternatePrompt
        self.currentPromptLength = len(self.currentPrompt)

    def displayPrompt( self ):
        self.runningCommand.clear()
        self.append(self.currentPrompt)
        self.moveCursor(QTextCursor.End, QTextCursor.MoveAnchor)

    def keyPressEvent(self, e):
        self.cursor = self.textCursor()
        # if the cursor isn't in the edition zone, don't do anything except Ctrl+C
        if not self.isCursorInEditionZone():
            if e.modifiers() == Qt.ControlModifier or \
                e.modifiers() == Qt.MetaModifier:
                if e.key() == Qt.Key_C or e.key() == Qt.Key_A:
                    QTextEdit.keyPressEvent( self, e )
            else:
                # all other keystrokes get sent to the input line
                self.cursor.movePosition( QTextCursor.End, QTextCursor.MoveAnchor )
        else:
            # if Ctrl + C is pressed, then undo the current command
            if e.key() == Qt.Key_C and ( e.modifiers() == Qt.ControlModifier or \
                e.modifiers() == Qt.MetaModifier ) and not self.cursor.hasSelection():
                self.runningCommand.clear()
                self.switchPrompt( True )
                self.displayPrompt()
                MainWindow.Console.statusBar().clearMessage() # this is not very generic, better way to do this?
              # if Return is pressed, then perform the commands
            elif e.key() == Qt.Key_Return:
                command = self.currentCommand()
                check = self.runningCommand.split("\n").last()
                if not self.runningCommand.isEmpty():
                    if not command == check:
                        self.runningCommand.append( command )
                        self.updateHistory( command )
                else:
                    if not command.isEmpty():
                        self.runningCommand = command
                        self.updateHistory( command )
                    else:
                        self.switchPrompt( True )
                        self.displayPrompt()
                if e.modifiers() == Qt.ShiftModifier or \
                    not self.checkBrackets(self.runningCommand):
                    self.switchPrompt(False)
                    self.cursor.insertText("\n"+self.currentPrompt)
                    self.runningCommand.append( "\n")
                else:
                    if not self.runningCommand.isEmpty():
                        command=self.runningCommand
                    self.execute(command)
                    self.runningCommand.clear()
                    self.switchPrompt(True)
                    #self.displayPrompt()
                self.cursor.movePosition( QTextCursor.End, QTextCursor.MoveAnchor )
                self.moveToEnd()
              # if Up or Down is pressed
            elif e.key() == Qt.Key_Down:
                self.showPrevious()
            elif e.key() == Qt.Key_Up:
                self.showNext()
              # if backspace is pressed, delete until we get to the prompt
            elif e.key() == Qt.Key_Backspace:
                if not self.cursor.hasSelection() and \
                    self.cursor.columnNumber() == self.currentPromptLength:
                    return
                QTextEdit.keyPressEvent( self, e )
              # if the left key is pressed, move left until we get to the prompt
            elif e.key() == Qt.Key_Left and \
                self.cursor.position() > self.document().lastBlock().position() + \
                self.currentPromptLength:
                if e.modifiers() == Qt.ShiftModifier:
                    anchor = QTextCursor.KeepAnchor
                else:
                    anchor = QTextCursor.MoveAnchor
                if ( e.modifiers() == Qt.ControlModifier or \
                e.modifiers() == Qt.MetaModifier ):
                    self.cursor.movePosition( QTextCursor.WordLeft, anchor )
                else:
                    self.cursor.movePosition( QTextCursor.Left, anchor )
              # use normal operation for right key
            elif e.key() == Qt.Key_Right:
                if e.modifiers() == Qt.ShiftModifier:
                    anchor = QTextCursor.KeepAnchor
                else:
                    anchor = QTextCursor.MoveAnchor
                if ( e.modifiers() == Qt.ControlModifier or \
                e.modifiers() == Qt.MetaModifier ):
                    self.cursor.movePosition( QTextCursor.WordRight, anchor )
                else:
                    self.cursor.movePosition( QTextCursor.Right, anchor )
              # if home is pressed, move cursor to right of prompt
            elif e.key() == Qt.Key_Home:
                if e.modifiers() == Qt.ShiftModifier:
                    anchor = QTextCursor.KeepAnchor
                else:
                    anchor = QTextCursor.MoveAnchor
                self.cursor.movePosition( QTextCursor.StartOfBlock, anchor, 1 )
                self.cursor.movePosition( QTextCursor.Right, anchor, self.currentPromptLength )
              # use normal operation for end key
            elif e.key() == Qt.Key_End:
                if e.modifiers() == Qt.ShiftModifier:
                    anchor = QTextCursor.KeepAnchor
                else:
                    anchor = QTextCursor.MoveAnchor
                self.cursor.movePosition(QTextCursor.EndOfBlock, anchor, 1)
                # use normal operation for all remaining keys
            else:
                QTextEdit.keyPressEvent(self, e)
        self.setTextCursor(self.cursor)
        self.ensureCursorVisible()

    def showPrevious(self):
        if self.historyIndex < len( self.history ) and not self.history.isEmpty():
            self.cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.MoveAnchor)
            self.cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
            self.cursor.removeSelectedText()
            self.cursor.insertText(self.currentPrompt)
            self.historyIndex += 1
            if self.historyIndex == len(self.history):
                self.insertPlainText("")
            else:
                self.insertPlainText(self.history[self.historyIndex])

    def showNext(self):
        if  self.historyIndex > 0 and not self.history.isEmpty():
            self.cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.MoveAnchor)
            self.cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
            self.cursor.removeSelectedText()
            self.cursor.insertText(self.currentPrompt)
            self.historyIndex -= 1
            if self.historyIndex == len(self.history):
                self.insertPlainText("")
            else:
                self.insertPlainText(self.history[self.historyIndex])


    def checkBrackets(self, command):
        s = str(command)
        s = filter(lambda x: x in '()[]{}"\'', s)
        s = s.replace ("'''", "'")
        s = s.replace ('"""', '"')
        instring = False
        brackets = {'(':')', '[':']', '{':'}', '"':'"', '\'':'\''}
        stack = []
        
        while len(s):
            if not instring:
                if s[0] in ')]}':
                    if stack and brackets[stack[-1]]==s[0]:
                        del stack[ -1 ]
                    else:
                        return False
                elif s[ 0 ] in '"\'':
                    if stack and brackets[stack[-1]]==s[0]:
                        del stack[-1]
                        instring = False
                    else:
                        stack.append(s[0])
                        instring = True
                else:
                    stack.append(s[0])
            else:
                if s[0] in '"\'' and stack and brackets[stack[-1]] == s[0]:
                    del stack[-1]
                    instring = False
            s = s[1:]
        return len(stack)==0

    def mousePressEvent(self, e):
        self.cursor = self.textCursor()
        if e.button() == Qt.LeftButton:
            QTextEdit.mousePressEvent(self, e)
        elif (not self.isCursorInEditionZone() or \
            (self.isCursorInEditionZone() and \
            not self.isAnchorInEditionZone())) and \
            e.button() == Qt.RightButton:
            QTextEdit.mousePressEvent(self, e)
            menu = self.createStandardContextMenu()
            actions = menu.actions()
            keep = [3,6,12]
            count = 0
            for action in keep:
                menu.removeAction(actions[action])
            menu.exec_(e.globalPos())
        else:
            QTextEdit.mousePressEvent(self, e)
        
    def moveToEnd( self ):
        cursor = self.textCursor()
        cursor.movePosition( QTextCursor.End, 
        QTextCursor.MoveAnchor )
        self.setTextCursor( cursor )
        self.emit(SIGNAL("textChanged()"))

    def insertFromMimeData(self, source):
        self.cursor = self.textCursor()
        self.cursor.movePosition(QTextCursor.End, 
        QTextCursor.MoveAnchor, 1)
        self.setTextCursor(self.cursor)
        if source.hasText():
            pastList = QStringList()
            pasteList = source.text().split("\n")
            if len(pasteList) > 1:
                self.runningCommand.append(source.text())
            for line in pasteList:
                self.updateHistory(line)
        newSource = QMimeData()
        newSource.setText(source.text().replace("\n",
        "\n"+self.alternatePrompt))
        QTextEdit.insertFromMimeData(self, newSource)

    def cut(self):
        if not self.isCursorInEditionZone() or \
        (self.isCursorInEditionZone() and \
        not self.isAnchorInEditionZone()):
            return
        else:
            QTextEdit.cut(self)

    def delete(self):
        if not self.isCursorInEditionZone() or \
        (self.isCursorInEditionZone() and \
        not self.isAnchorInEditionZone()):
            return
        else:
            QTextEdit.delete(self)
    
    def currentCommand( self ):
        block = self.cursor.block()
        text = block.text()
        return text.right( text.length()-self.currentPromptLength )

    def appendText(self, out_text):
        if not out_text == "":
            self.append(out_text)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        self.setTextCursor(cursor)

    def isCursorInEditionZone( self ):
        cursor = self.textCursor()
        pos = cursor.position()
        block = self.document().lastBlock()
        last = block.position() + self.currentPromptLength
        return pos >= last
      
    def isAnchorInEditionZone( self ):
        cursor = self.textCursor()
        pos = cursor.anchor()
        block = self.document().lastBlock()
        last =  block.position() + self.currentPromptLength
        return pos >= last

    def updateHistory(self, command):
        if not command == "":
            self.history.append(command)
            self.historyIndex = len(self.history)

    def insertPlainText( self, text ):
        if self.isCursorInEditionZone():
          QTextEdit.insertPlainText(self, text)

    def execute(self, text):
        MainWindow.Console.statusBar().showMessage("Running...")
        #highlighting = True
        #sinking = False
        if not text.trimmed() == "":
            try:
                if ( text.startsWith( 'quit(' ) or text.startsWith( 'q(' ) ) \
                and text.count( ")" ) == 1:
                    self.commandError( "System exit from manageR not allowed, close dialog manually" )
                else:
                    output_text = QString()
                    def write( output ):
                        if not QString( output ).startsWith( "Error" ):
                            output_text.append( unicode(output, 'utf-8') )
                        if output_text.length() >= 50000 and output_text[ -1 ] == "\n":
                            self.commandOutput( output_text )
                            output_text.clear()
                    robjects.rinterface.setWriteConsole( write )
                    def read( prompt ):
                        input = "\n"
                        return input
                    robjects.rinterface.setReadConsole( read )
                    try:
                        try_ = robjects.r[ "try" ]
                        parse_ = robjects.r[ "parse" ]
                        paste_ = robjects.r[ "paste" ]
                        seq_along_ = robjects.r[ "seq_along" ]
                        withVisible_ = robjects.r[ "withVisible" ]
                        class_ = robjects.r[ "class" ]
                        result =  try_(parse_(text=paste_(unicode(text))), silent=True)
                        exprs = result
                        result = None
                        for i in list(seq_along_(exprs)):
                            ei = exprs[i-1]
                            try:
                                result =  try_( withVisible_( ei ), silent=True )
                            except robjects.rinterface.RRuntimeError, rre:
                                self.commandError( str( rre ) )
                                self.commandComplete()
                                return
                            visible = result.r["visible"][0][0]
                            if visible:
                                if class_( result.r["value"][0] )[0] == "help_files_with_topic" or \
                                    class_( result.r["value"][0] )[0] == "hsearch":
                                    self.helpTopic( result.r["value"][0], class_( result.r["value"][0] )[0] )
                                elif not str(result.r["value"][0]) == "NULL":
                                    robjects.r['print'](result.r["value"][0])
                            else:
                                #self.emit( SIGNAL( "newObjectCreated( PyQt_PyObject )" ), self.updateRObjects() )
                                pass
                    except robjects.rinterface.RRuntimeError, rre:
                        # this fixes error output to look more like R's output
                        self.commandError( "Error: " + str(rre).split(":")[1].strip() )
                        self.commandComplete()
                        return
                    if not output_text.isEmpty():
                        self.commandOutput( output_text )
            except Exception, err:
                self.commandError( str( err ) )
                self.commandComplete()
                return
            self.commandComplete()
        MainWindow.Console.statusBar().clearMessage()

    def helpTopic(self, topic, search):
        if search == "hsearch":
            dialog = searchDialog( self, topic )
        else:
            dialog = helpDialog( self, topic )
        dialog.setWindowModality( Qt.NonModal )
        dialog.setModal( False )
        dialog.show()
        MainWindow.Console.statusBar().showMessage("Help dialog opened", 5000)
        return

    def commandError(self, error):
        self.appendText(unicode(error))
        # Emit a signal here?
                
    def commandOutput( self, output ):
        self.appendText(unicode(output))
        # Emit a signal here?
        
    def commandComplete( self ):
        self.switchPrompt()
        self.displayPrompt()
        MainWindow.Console.statusBar().showMessage("Complete!", 5000)
        # Also should emit a signal here

    def complete(self):
        pass

    def gotoMatching(self):
        # move the cursor to the matching ()[]<>{} or do nothing
        newfrmt = QTextCharFormat()
        newfrmt.setFontWeight(QFont.Bold)
        OPEN = "([<{"
        CLOSE = ")]>}"
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.PreviousCharacter,
                            QTextCursor.KeepAnchor)
        c = unicode(cursor.selectedText())
        if c not in OPEN + CLOSE:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.NextCharacter,
                                QTextCursor.KeepAnchor)
            c = unicode(cursor.selectedText())
            if c in OPEN + CLOSE:
                self.setTextCursor(cursor)
            else:
                return
        i = OPEN.find(c)
        if i > -1:
            movement = QTextCursor.NextCharacter
            stack = 0
            target = CLOSE[i]
        else:
            i = CLOSE.find(c)
            if i == -1:
                return
            movement = QTextCursor.PreviousCharacter
            stack = -1
            target = OPEN[i]
        cursor = self.textCursor()
        while (not (movement == QTextCursor.NextCharacter and
                    cursor.atEnd()) and
               not (movement == QTextCursor.PreviousCharacter and
                    cursor.atStart())):
            cursor.clearSelection()
            cursor.movePosition(movement, QTextCursor.KeepAnchor)
            x = unicode(cursor.selectedText())
            if not x:
                break
            if x == c:
                stack += 1
            elif x == target:
                if stack == 0:
                    cursor.clearSelection()
                    if movement == QTextCursor.PreviousCharacter:
                        cursor.movePosition(
                                QTextCursor.NextCharacter)
                    self.setTextCursor(cursor)
                    break
                else:
                    stack -= 1


class ConfigForm(QDialog):

    def __init__(self, parent=None):
        super(ConfigForm, self).__init__(parent)

        self.highlightingChanged = False
        fm = QFontMetrics(self.font())
        monofont = QFont(Config["fontfamily"], Config["fontsize"])
        pixmap = QPixmap(16, 16)
        self.colors = {}
        self.boldCheckBoxes = {}
        self.italicCheckBoxes = {}
        self.completionCheckBoxes = {}
        self.editors = {}

        generalWidget = QWidget()
        self.rememberGeometryCheckBox = QCheckBox(
                "&Remember Geometry")
        self.rememberGeometryCheckBox.setToolTip("<p>Check this to make "
                "manageR remember the size and position of the Console "
                "window and one editR window")
        self.rememberGeometryCheckBox.setChecked(
                Config["remembergeometry"])
        self.autoHideFindDlgCheckBox = QCheckBox(
                "Automati&cally Hide the Find and Replace dialog")
        self.backupLineEdit = QLineEdit(Config["backupsuffix"])
        self.backupLineEdit.setToolTip("<p>If nonempty, a backup will be "
                "kept with the given suffix. If empty, no backup will be "
                "made.")
        regex = QRegExp(r"[~.].*")
        self.backupLineEdit.setValidator(QRegExpValidator(regex, self))
        self.backupLineEdit.setFont(monofont)
        backupLabel = QLabel("&Backup suffix:")
        backupLabel.setBuddy(self.backupLineEdit)
        regex = QRegExp(r"*")
        self.inputLineEdit = QLineEdit(Config["beforeinput"])
        self.inputLineEdit.setValidator(QRegExpValidator(regex, self))
        self.inputLineEdit.setInputMask("x" * 40)
        self.inputLineEdit.setFont(monofont)
        inputPromptLabel = QLabel("&Input Prompt:")
        inputPromptLabel.setBuddy(self.inputLineEdit)
        self.outputLineEdit = QLineEdit(Config["afteroutput"])
        self.outputLineEdit.setValidator(QRegExpValidator(regex, self))
        self.outputLineEdit.setInputMask("x" * 40)
        self.outputLineEdit.setFont(monofont)
        outputPromptLabel = QLabel("&Output Prompt:")
        outputPromptLabel.setBuddy(self.outputLineEdit)
        self.cwdLineEdit = QLineEdit(Config["cwd"])
        cwdLabel = QLabel("Working &Directory:")
        cwdLabel.setBuddy(self.cwdLineEdit)
        self.tabWidthSpinBox = QSpinBox()
        self.tabWidthSpinBox.setAlignment(Qt.AlignVCenter|
                                          Qt.AlignRight)
        self.tabWidthSpinBox.setRange(2, 20)
        self.tabWidthSpinBox.setSuffix(" spaces")
        self.tabWidthSpinBox.setValue(Config["tabwidth"])
        tabWidthLabel = QLabel("&Tab width:")
        tabWidthLabel.setBuddy(self.tabWidthSpinBox)
        minWidth = 0
        for label in (backupLabel, inputPromptLabel, outputPromptLabel,
                cwdLabel, tabWidthLabel):
            minWidth = max(minWidth, fm.width(label.text()))
        for label in (backupLabel, inputPromptLabel, outputPromptLabel,
                cwdLabel, tabWidthLabel):
            label.setMinimumWidth(minWidth)
        vbox = QVBoxLayout()
        vbox.addWidget(self.rememberGeometryCheckBox)
        hbox = QHBoxLayout()
        hbox.addWidget(backupLabel)
        hbox.addWidget(self.backupLineEdit)
        hbox.addStretch()
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(inputPromptLabel)
        hbox.addWidget(self.inputLineEdit)
        hbox.addStretch()
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(outputPromptLabel)
        hbox.addWidget(self.outputLineEdit)
        hbox.addStretch()
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(cwdLabel)
        hbox.addWidget(self.cwdLineEdit)
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(tabWidthLabel)
        hbox.addWidget(self.tabWidthSpinBox)
        hbox.addStretch()
        vbox.addLayout(hbox)
        generalWidget.setLayout(vbox)

        highlightingWidget = QWidget()
        self.fontComboBox = QFontComboBox()
        self.fontComboBox.setCurrentFont(monofont)
        fontLabel = QLabel("&Font:")
        fontLabel.setBuddy(self.fontComboBox)
        self.fontSpinBox = QSpinBox()
        self.fontSpinBox.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.fontSpinBox.setRange(6, 20)
        self.fontSpinBox.setSuffix(" pt")
        self.fontSpinBox.setValue(Config["fontsize"])
        minButtonWidth = 0
        minWidth = 0
        label = QLabel("Background:")
        #minWidth = max(minWidth, fm.width(label.text())) + 175
        label.setMinimumWidth(minWidth)
        minWidth = 0
        color = Config["backgroundcolor"]
        pixmap.fill(QColor(color))
        colorButton = QPushButton("&0 Color...")
        minButtonWidth = max(minButtonWidth,
        10 + pixmap.width() + fm.width(colorButton.text()))
        colorButton.setIcon(QIcon(pixmap))
        self.colors["background"] = [Config["backgroundcolor"], None]
        self.colors["background"][1] = colorButton
        self.connect(colorButton, SIGNAL("clicked()"),
        lambda name="background": self.setColor("background"))

        gbox = QGridLayout()
        #hbox = QHBoxLayout()
        gbox.addWidget(fontLabel,0,0,1,1)
        gbox.addWidget(self.fontComboBox,0,1,1,2)
        gbox.addWidget(self.fontSpinBox,0,3,1,1)
        #hbox.addStretch()
        #vbox.addLayout(hbox)
        #hbox = QHBoxLayout()
        gbox.addWidget(label,1,0,1,1)
        gbox.addWidget(colorButton,1,3,1,1)
        #hbox.addStretch()
        #vbox.addLayout(hbox)
        count = 1
        labels = []
        buttons = []
        for name, labelText in (("normal", "Normal:"),
                ("keyword", "Keywords:"), ("builtin", "Builtins:"),
                ("constant", "Constants:"), ("delimiter", "Delimiters:"),
                ("comment", "Comments:"), ("string", "Strings:"),
                ("number", "Numbers:"), ("error", "Errors:"),
                ("assignment", "Assignment operator:")):
            label = QLabel(labelText)
            #minWidth = max(minWidth, fm.width(label.text()))
            labels.append(label)
            boldCheckBox = QCheckBox("Bold")
            boldCheckBox.setChecked(Config["%sfontbold" % name])
            self.boldCheckBoxes[name] = boldCheckBox
            italicCheckBox = QCheckBox("Italic")
            italicCheckBox.setChecked(Config["%sfontitalic" % name])
            self.italicCheckBoxes[name] = italicCheckBox
            self.colors[name] = [Config["%sfontcolor" % name], None]
            pixmap.fill(QColor(self.colors[name][0]))
            if count <= 9:
                colorButton = QPushButton("&%d Color..." % count)
            elif name == "assignment":
                colorButton = QPushButton("&Q Color...")
            else:
                colorButton = QPushButton("Color...")
            count += 1
            minButtonWidth = max(minButtonWidth,
                    10 + pixmap.width() + fm.width(colorButton.text()))
            buttons.append(colorButton)
            colorButton.setIcon(QIcon(pixmap))
            self.colors[name][1] = colorButton
            #hbox = QHBoxLayout()
            gbox.addWidget(label,count+1,0,1,1)
            gbox.addWidget(boldCheckBox,count+1,1,1,1)
            gbox.addWidget(italicCheckBox,count+1,2,1,1)
            gbox.addWidget(colorButton,count+1,3,1,1)
            #hbox.addStretch()
            #vbox.addLayout(hbox)
            self.connect(colorButton, SIGNAL("clicked()"),
                        lambda name=name: self.setColor(name))
        #for label in labels:
            #label.setMinimumWidth(minWidth)
        #for button in buttons:
            #button.setMinimumWidth(minButtonWidth)
        #vbox.addStretch()
        highlightingWidget.setLayout(gbox)

        tabWidget = QTabWidget()
        tabWidget.addTab(generalWidget, "&General")
        tabWidget.addTab(highlightingWidget, "&Highlighting")

        for name, label, msg in (
                ("newfile", "On &New File",
                 "<font color=green><i>The text here is automatically "
                 "inserted into new R scripts.<br>It may be convenient to add "
                 "your standard libraries and copyright notice here."),
                ("consolestartup", "&At Startup",
                 "<font color=green><i>manageR executes the lines above "
                 "whenever the R interpreter is started.<br>"
                 "Use them to add convenience, e.g.</font>"
                 "</i><br/><b>library(rgdal)"
                 "<br/>library(spdep)</b>"
                 "<br/><font color=green><i>"
                 "Changes made here only take "
                 "effect when manageR is next run.</font>")):
            editor = REditor(self)
            editor.setPlainText(Config[name])
            editor.setTabChangesFocus(True)
            RHighlighter(editor.document())
            vbox = QVBoxLayout()
            vbox.addWidget(editor, 1)
            vbox.addWidget(QLabel(msg))
            widget = QWidget()
            widget.setLayout(vbox)
            tabWidget.addTab(widget, label)
            self.editors[name] = editor

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|
                                           QDialogButtonBox.Cancel)
        layout = QVBoxLayout()
        layout.addWidget(tabWidget)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

        self.connect(buttonBox, SIGNAL("accepted()"), self.accept)
        self.connect(buttonBox, SIGNAL("rejected()"), self.reject)

        self.setWindowTitle("manageR - Configure")


    def updateUi(self):
        pass # TODO validation, e.g., valid Consolestartup, etc.

    def setColor(self, which):
        color = QColorDialog.getColor(
                        QColor(self.colors[which][0]), self)
        if color is not None:
            self.colors[which][0] = color.name()
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(color.name()))
            self.colors[which][1].setIcon(QIcon(pixmap))

    def accept(self):
        Config["remembergeometry"] = (self.rememberGeometryCheckBox
                                      .isChecked())
        #Config["showwindowinfo"] = self.showWindowInfoCheckBox.isChecked()
        #Config["autohidefinddialog"] = (self.autoHideFindDlgCheckBox
                                        #.isChecked())
        Config["backupsuffix"] = self.backupLineEdit.text()
        Config["beforeinput"] = self.inputLineEdit.text()
        Config["afteroutput"] = self.outputLineEdit.text()
        Config["cwd"] = self.cwdLineEdit.text()
        for name in ("consolestartup", "newfile"):
            Config[name] = unicode(self.editors[name].toPlainText())
        Config["tabwidth"] = self.tabWidthSpinBox.value()
        #Config["tooltipsize"] = self.toolTipSizeSpinBox.value()
        family = self.fontComboBox.currentFont().family()
        if Config["fontfamily"] != family:
            self.highlightingChanged = True
            Config["fontfamily"] = family
        size = self.fontSpinBox.value()
        if Config["fontsize"] != size:
            self.highlightingChanged = True
            Config["fontsize"] = size
        for name in ("normal", "keyword", "builtin", "constant",
                "delimiter", "comment", "string", "number", "error",
                "assignment"):
            bold = self.boldCheckBoxes[name].isChecked()
            if Config["%sfontbold" % name] != bold:
                self.highlightingChanged = True
                Config["%sfontbold" % name] = bold
            italic = self.italicCheckBoxes[name].isChecked()
            if Config["%sfontitalic" % name] != italic:
                self.highlightingChanged = True
                Config["%sfontitalic" % name] = italic
            color = self.colors[name][0]
            if Config["%sfontcolor" % name] != color:
                self.highlightingChanged = True
                Config["%sfontcolor" % name] = color
        color = self.colors["background"][0]
        if Config["backgroundcolor"] != color:
            self.highlightingChanged = True
            Config["backgroundcolor"] = color
        QDialog.accept(self)

class helpDialog( QDialog ):

    def __init__( self, parent, help_topic ):
        QDialog.__init__ ( self, parent )
        #initialise the display text edit
        display = QTextEdit( self )
        display.setReadOnly( True )
        #set the font style of the help display
        font = QFont( "Monospace" , 10, QFont.Normal )
        font.setFixedPitch( True )
        display.setFont( font )
        display.document().setDefaultFont( font )
        #initialise grid layout for dialog
        grid = QGridLayout( self )
        grid.addWidget( display )
        self.setWindowTitle( "manageR - Help" )
        help_file = QFile( unicode( help_topic[ 0 ] ) )
        #print help_topic
        help_file.open( QFile.ReadOnly )
        stream = QTextStream( help_file )
        help_string = QString( stream.readAll() )
        #workaround to remove the underline formatting that r uses
        help_string.remove("_")
        display.setPlainText( help_string )
        help_file.close()
        self.resize( 550, 400 )

class searchDialog( QDialog ):

  def __init__( self, parent, help_topic ):
      QDialog.__init__ ( self, parent )
      #initialise the display text edit
      display = QTextEdit( self )
      display.setReadOnly( True )
      #set the font style of the help display
      font = QFont( "Monospace" , 10, QFont.Normal )
      font.setFixedPitch( True )
      display.setFont( font )
      display.document().setDefaultFont( font )
      #initialise grid layout for dialog
      grid = QGridLayout( self )
      grid.addWidget( display )
      self.setWindowTitle( "manageR - Help Search" )
      #get help output from r 
      #note: help_topic should only contain the specific
      #      help topic (i.e. no brackets etc.)
      matches = help_topic.subset("matches")[0]
      #print [matches]
      fields = help_topic.subset("fields")[0]
      pattern = help_topic.subset("pattern")[0]
      fields_string = QString()
      for i in fields:
          fields_string.append( i + " or ")
      fields_string.chop( 3 )
      display_string = QString( "Help files with " + fields_string )
      display_string.append( "matching '" + pattern[0] + "' using " )
      display_string.append( "regular expression matching:\n\n" )
      nrows = robjects.r.nrow( matches )[0]
      ncols = robjects.r.ncol( matches )[0]
      for i in range( 1, nrows + 1 ):
            row = QString()
            pack = matches.subset( i, 3 )[0]
            row.append(pack)
            row.append("::")
            pack = matches.subset( i, 1 )[0]
            row.append(pack)
            row.append("\t\t")
            pack = matches.subset( i, 2 )[0]
            row.append(pack)
            row.append("\n")
            display_string.append( row )
      display.setPlainText( display_string )
      #help_file.close()
      self.resize( 550, 400 )


class MainWindow(QMainWindow):

    NextId = 1
    Instances = set()
    Console = None
    Toolbars = {}

    def __init__(self, filename=QString(), isConsole=True,
                 parent=None):
        super(MainWindow, self).__init__(parent)
        MainWindow.Instances.add(self)
        self.setWindowTitle("manageR[*]")
        if isConsole:
            pixmap = QPixmap( ":splash.png" )
            splash = QSplashScreen(pixmap)
            splash.show()
            QApplication.processEvents()
            self.setAttribute(Qt.WA_DeleteOnClose)
            splash.showMessage( "Loading R interpreter", \
            (Qt.AlignBottom|Qt.AlignHCenter), Qt.white )
            self.editor = RConsole(self)
            MainWindow.Console = self
            self.editor.append( __welcomestring__ )
            self.editor.displayPrompt()
            self.editor.setFocus(Qt.ActiveWindowFocusReason)
            splash.showMessage( "Checking manageR configuration", \
            (Qt.AlignBottom|Qt.AlignHCenter), Qt.white )
        else:
            self.editor = REditor(self)

        palette = QPalette(QColor(Config["backgroundcolor"]))
        palette.setColor(QPalette.Active, QPalette.Base, QColor(Config["backgroundcolor"]))
        self.editor.setPalette(palette)
        self.editor.setTextColor(QColor(Config["normalfontcolor"]))
        self.setCentralWidget(self.editor)
        self.highlighter = RHighlighter( self.editor )
        self.finder = RFinder( self, self.editor )
        self.finderDockWidget = QDockWidget( "Find and Replace Toolbar", self )          
        self.finderDockWidget.setObjectName( "findReplace" )
        self.finderDockWidget.setAllowedAreas( Qt.BottomDockWidgetArea)
        self.finderDockWidget.setWidget( self.finder )
        self.setCorner( Qt.BottomRightCorner, Qt.BottomDockWidgetArea )
        self.addDockWidget( Qt.BottomDockWidgetArea, self.finderDockWidget )

        if isConsole:
            splash.showMessage( "Creating menus and toolbars", \
            (Qt.AlignBottom|Qt.AlignHCenter), Qt.white )

        fileNewAction = self.createAction("&New File", self.fileNew,
                QKeySequence.New, "mActionFileNew", "Create a R script")
        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                QKeySequence.Open, "mActionFileOpen",
                "Open an existing R script")
        if not isConsole:
            fileSaveAction = self.createAction("&Save", self.fileSave,
                    QKeySequence.Save, "mActionFileSave", "Save R script")
            fileSaveAsAction = self.createAction("Save &As...",
                    self.fileSaveAs, icon="mActionFileSaveAs",
                    tip="Save R script using a new filename")
            fileCloseAction = self.createAction("&Close", self.close,
                    QKeySequence.Close, "mActionFileClose",
                    "Close this editR window")
        fileSaveAllAction = self.createAction("Save A&ll",
                self.fileSaveAll, icon="mActionFileSaveAll",
                tip="Save all R scripts")
        fileConfigureAction = self.createAction("Config&ure...",
                self.fileConfigure, icon="mActionFileConfigure",
                tip="Configure manageR")
        fileQuitAction = self.createAction("&Quit", self.fileQuit,
                "Ctrl+Q", "mActionFileQuit", "Close manageR")
        editUndoAction = self.createAction("&Undo", self.editor.undo,
                QKeySequence.Undo, "mActionEditUndo",
                "Undo last editing action")
        editRedoAction = self.createAction("&Redo", self.editor.redo,
                QKeySequence.Redo, "mActionEditRedo",
                "Redo last editing action")
        editCopyAction = self.createAction("&Copy", self.editor.copy,
                QKeySequence.Copy, "mActionEditCopy",
                "Copy text to clipboard")
        editCutAction = self.createAction("Cu&t", self.editor.cut,
                QKeySequence.Cut, "mActionEditCut",
                "Cut text to clipboard")
        editPasteAction = self.createAction("&Paste",
                self.editor.paste, QKeySequence.Paste, "mActionEditPaste",
                "Paste from clipboard")
        editSelectAllAction = self.createAction("Select &All",
                self.editor.selectAll, QKeySequence.SelectAll,
                "mActionEditSelectAll", "Select all text")
        editCompleteAction = self.createAction("Com&plete",
                self.editor.complete, "Ctrl+Space", "mActionEditComplete",
                "Initiate autocomplete suggestions")
        editFindNextAction = self.createAction("&Find",
                self.toggleFind, QKeySequence.Find,
                "mActionEditFindNext",
                "Find the next occurrence of the given text")
        if not isConsole:
            editReplaceNextAction = self.createAction("&Replace",
                    self.toggleFind, QKeySequence.Replace,
                    "mActionEditReplaceNext",
                    "Replace the next occurrence of the given text")
            editIndentRegionAction = self.createAction("&Indent Region",
                    self.editor.indentRegion, "Ctrl+]", "mActionEditIndent",
                    "Indent the selected text or the current line")
            editUnindentRegionAction = self.createAction(
                    "Unin&dent Region", self.editor.unindentRegion,
                    "Ctrl+[", "mActionEditUnindent",
                    "Unindent the selected text or the current line")
            editCommentRegionAction = self.createAction("C&omment Region",
                    self.editor.commentRegion, icon="mActionEditComment",
                    tip=("Comment out the selected text or the "
                         "current line"))
            editUncommentRegionAction = self.createAction(
                    "Uncomment Re&gion", self.editor.uncommentRegion,
                    icon="mActionEditUncomment",
                    tip="Uncomment the selected text or the current line")
            actionRunAction = self.createAction("E&xecute",
                    self.editor.execute, "Ctrl+Return", "mActionRun",
                    "Execute the (selected) text in the manageR console")
            #actionRunAction.setShortcuts([QKeySequence("Ctrl+Enter"),
                    #QKeySequence("Ctrl+Return")])
        else:
            actionShowPrevAction = self.createAction(
                    "Show Previous Command", self.editor.showNext,
                    "Up", "mActionPrevious",
                    ("Show previous command"))
            actionShowNextAction = self.createAction(
                    "Show Next Command", self.editor.showPrevious,
                    "Down", "mActionNext",
                    ("Show next command"))
        helpHelpAction = self.createAction("&Help", self.helpHelp,
                QKeySequence.HelpContents, icon="mActionHelpHelp",
                tip="Commands help")
        helpAboutAction = self.createAction("&About", self.helpAbout,
                icon="mActionIcon", tip="About manageR")

        fileMenu = self.menuBar().addMenu("&File")
        self.addActions(fileMenu, (fileNewAction,))
        #if not isConsole:
            #self.addActions(fileMenu, (fileNewConsoleAction,))
        self.addActions(fileMenu, (fileOpenAction,))
        if not isConsole:
            self.addActions(fileMenu, (fileSaveAction, fileSaveAsAction))
        self.addActions(fileMenu, (fileSaveAllAction, None,
                fileConfigureAction, None,))
        if not isConsole:
            self.addActions(fileMenu, (fileCloseAction,))
        self.addActions(fileMenu, (fileQuitAction,))

        editMenu = self.menuBar().addMenu("&Edit")
        self.addActions(editMenu, (editUndoAction, editRedoAction, None,
                editCopyAction, editCutAction, editPasteAction,
                editSelectAllAction, None, editCompleteAction))
        
        self.addActions(editMenu, (editFindNextAction,))
        if not isConsole:
            self.addActions(editMenu, (editReplaceNextAction, 
                None, editIndentRegionAction,
                editUnindentRegionAction, editCommentRegionAction,
                editUncommentRegionAction))
        self.gotoMenu = self.menuBar().addMenu("&Goto")
        self.addActions(self.gotoMenu, (self.createAction("&Matching",
                self.editor.gotoMatching, "Ctrl+B", "mActionGotoMatching",
                "Move the cursor to the matching parenthesis"),))
        if not isConsole:
            self.addActions(self.gotoMenu, (self.createAction("&Line...",
                    self.editor.gotoLine, "Ctrl+H", "mActionGotoLine",
                    "Move the cursor to the given line"),))

        actionMenu = self.menuBar().addMenu("&Action")
        if not isConsole:
            self.addActions(actionMenu, (actionRunAction,))
        else:
            self.addActions(actionMenu, (actionShowPrevAction, 
                actionShowNextAction,))
        viewMenu = self.menuBar().addMenu("&View")
        self.windowMenu = self.menuBar().addMenu("&Window")
        self.connect(self.windowMenu, SIGNAL("aboutToShow()"),
                     self.updateWindowMenu)
        helpMenu = self.menuBar().addMenu("&Help")
        self.addActions(helpMenu, (helpHelpAction, helpAboutAction,))

        self.fileToolbar = self.addToolBar("File Toolbar")
        self.fileToolbar.setObjectName("FileToolbar")
        MainWindow.Toolbars[self.fileToolbar] = None
        self.addActions(self.fileToolbar, (fileNewAction, fileOpenAction))
        if not isConsole:
            self.addActions(self.fileToolbar, (fileSaveAction,))
        self.editToolbar = self.addToolBar("Edit Toolbar")
        self.editToolbar.setObjectName("EditToolbar")
        MainWindow.Toolbars[self.editToolbar] = None
        self.addActions(self.editToolbar, (editUndoAction, editRedoAction,
                None, editCopyAction, editCutAction, editPasteAction,
                None, editFindNextAction,))
        if not isConsole:
            self.addActions(self.editToolbar, (editReplaceNextAction, None,
                    editIndentRegionAction, editUnindentRegionAction,
                    editCommentRegionAction, editUncommentRegionAction))
        self.actionToolbar = self.addToolBar("Action Toolbar")
        self.actionToolbar.setObjectName("ActionToolbar")
        MainWindow.Toolbars[self.actionToolbar] = None
        if not isConsole:
            self.addActions(self.actionToolbar, (actionRunAction,))
        else:
            self.addActions(self.actionToolbar, (None, actionShowPrevAction, 
                actionShowNextAction))
        for toolbar in (self.fileToolbar, self.editToolbar,
                        self.actionToolbar):
            action = viewMenu.addAction("&%s" % toolbar.windowTitle())
            self.connect(action, SIGNAL("toggled(bool)"),
                         self.toggleToolbars)
            action.setCheckable(True)
            MainWindow.Toolbars[toolbar] = action
        action = self.finderDockWidget.toggleViewAction()
        self.connect(action, SIGNAL("toggled(bool)"), self.toggleToolbars)
        action.setCheckable(True)
        viewMenu.addAction( action )
        MainWindow.Toolbars[self.finderDockWidget] = action
        if isConsole:
            self.finderDockWidget.setWindowTitle("Find Toolbar")
            self.finder.hideReplace()
        self.connect(self, SIGNAL("destroyed(QObject*)"),
                     MainWindow.updateInstances)

        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.showMessage("Ready", 5000)
        if not isConsole:
            self.columnCountLabel = QLabel("(empty)")
            status.addPermanentWidget(self.columnCountLabel)
            self.lineCountLabel = QLabel("(empty)")
            status.addPermanentWidget(self.lineCountLabel)
            self.connect(self.editor,
                         SIGNAL("cursorPositionChanged()"),
                         self.updateIndicators)
            self.connect(self.editor.document(),
                         SIGNAL("blockCountChanged(int)"),
                         self.updateIndicators)
        else:
            splash.showMessage( "Adjusting window size", \
            (Qt.AlignBottom|Qt.AlignHCenter), Qt.white )
        if Config["remembergeometry"]:
            if isConsole:
                self.resize(Config["consolewidth"], Config["consoleheight"])
                self.move(Config["consolex"], Config["consoley"])
            else:
                self.resize(Config["windowwidth"],
                            Config["windowheight"])
                if int(isConsole) + len(MainWindow.Instances) <= 2:
                    self.move(Config["windowx"], Config["windowy"])

        self.restoreState(Config["toolbars"])

        self.filename = QString("")
        if isConsole:
            splash.showMessage( "Setting toolbar status", \
            (Qt.AlignBottom|Qt.AlignHCenter), Qt.white )
            self.setWindowTitle("manageR")
        else:
            self.filename = filename
            if self.filename.isEmpty():
                while QFileInfo(QString("untitled%d.R" %
                                            MainWindow.NextId)).exists():
                    MainWindow.NextId += 1
                self.filename = QString("untitled%d.R" %
                                               MainWindow.NextId)
                self.editor.setText(Config["newfile"])
                self.editor.moveCursor(QTextCursor.End)
                self.editor.document().setModified(False)
                self.setWindowModified(False)
                self.setWindowTitle("editR - %s[*]" % self.filename)
            else:
                self.loadFile()
            self.connect(self.editor, SIGNAL("textChanged()"),
                         self.updateDirty)
        if isConsole:
            splash.showMessage( "Ready!", \
            (Qt.AlignBottom|Qt.AlignHCenter), Qt.white )
            splash.finish( self )
        QTimer.singleShot(0, self.updateToolbars)
        self.startTimer( 50 )

    def timerEvent(self, e):
        try:
            robjects.rinterface.process_revents()
        except:
            pass

    def toggleFind(self):
        title = self.sender().text()
        toolbar = MainWindow.Toolbars[self.finderDockWidget]
        if not toolbar.isChecked():
            toolbar.setChecked(True)
        if title == "&Replace":
            self.finder.showReplace()
        else:
            self.finder.hideReplace()

    @staticmethod
    def updateInstances(qobj):
        MainWindow.Instances = set([window for window
                in MainWindow.Instances if isAlive(window)])
        if MainWindow.Console is not None and not isAlive(MainWindow.Console):
            MainWindow.Console = None


    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)


    def updateDirty(self):
        self.setWindowModified(self.editor.document().isModified())


    def updateIndicators(self):
        lines = self.editor.document().blockCount()
        cursor = self.editor.textCursor()
        self.columnCountLabel.setText("Column %d" % (
                cursor.columnNumber() + 1))
        if lines == 0:
            text = "(empty)"
        else:
            text = "Line %d of %d " % (cursor.blockNumber() + 1, lines)
        self.lineCountLabel.setText(text)


    def updateToolbars(self):
        for toolbar, action in MainWindow.Toolbars.items():
            action.setChecked(toolbar.isVisible())


    def toggleToolbars(self, on):
        title = self.sender().text()
        for toolbar, action in MainWindow.Toolbars.items():
            if action.text() == title:
                toolbar.setVisible(on)
                action.setChecked(on)


    def closeEvent(self, event):
        if self == MainWindow.Console:
            if Config["remembergeometry"]:
                Config["consolewidth"] = self.width()
                Config["consoleheight"] = self.height()
                Config["consolex"] = self.x()
                Config["consoley"] = self.y()
            for window in MainWindow.Instances:
                if isAlive(window):
                    window.close()
        else:
            if self.editor.document().isModified():
                reply = QMessageBox.question(self,
                        "editR - Unsaved Changes",
                        "Save unsaved changes in %s" % self.filename,
                        QMessageBox.Save|QMessageBox.Discard|
                        QMessageBox.Cancel)
                if reply == QMessageBox.Save:
                    self.fileSave()
                elif reply == QMessageBox.Cancel:
                    event.ignore()
                    return
                # else accept and discard
            if Config["remembergeometry"]:
                Config["windowwidth"] = self.width()
                Config["windowheight"] = self.height()
                Config["windowx"] = self.x()
                Config["windowy"] = self.y()
            if self.finder is not None:
                Config["findcasesensitive"] = (self.finder
                        .case_sensitive.isChecked())
                Config["findwholewords"] = (self.finder
                        .whole_words.isChecked())
        Config["toolbars"] = self.saveState()
        #del MainWindow.Toolbars[self.fileToolbar]
        #del MainWindow.Toolbars[self.editToolbar]
        #del MainWindow.Toolbars[self.actionToolbar]
        event.accept()


    def fileConfigure(self):
        form = ConfigForm(self)
        if form.exec_():
            # Should only do this if the highlighting was actually
            # changed since it is computationally expensive.
            if form.highlightingChanged:
                font = QFont(Config["fontfamily"],
                                   Config["fontsize"])
                textcharformat = QTextCharFormat()
                textcharformat.setFont(font)
                RHighlighter.initializeFormats()
                for window in MainWindow.Instances:
                    if isAlive(window):
                        window.statusBar().showMessage("Rehighlighting...")
                        window.editor.setFont(font)
                        window.editor.textcharformat = (textcharformat)
                        window.editor.highlighter.rehighlight()
                        palette = QPalette(QColor(Config["backgroundcolor"]))
                        palette.setColor(QPalette.Active, 
                        QPalette.Base, QColor(Config["backgroundcolor"]))
                        window.editor.setPalette(palette)
                        window.statusBar().clearMessage()
            saveConfig()


    def fileQuit(self):
        QApplication.closeAllWindows()


    def fileNew(self):
        MainWindow(isConsole=False).show()

    def fileOpen(self):
        if not self.filename.isEmpty():
            path = QFileInfo(self.filename).path()
        else:
            path = "."
        filename = QFileDialog.getOpenFileName(self,
                        "manageR - Open File", path,
                        "R scripts (*.R)\nAll files (*)")
        if not filename.isEmpty():
            # To prevent opening the same file twice
            for window in MainWindow.Instances:
                if isAlive(window) and window != MainWindow.Console:
                    if window.filename == filename:
                        window.activateWindow()
                        window.raise_()
                        return
            if (MainWindow.Console != self and
                not self.editor.document().isModified() and
                self.filename.startsWith("untitled")):
                self.filename = filename
                self.loadFile()
            else:
                MainWindow(filename, isConsole=False).show()


    def loadFile(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        fh = None
        try:
            try:
                fh = QFile(self.filename)
                if not fh.open(QIODevice.ReadOnly):
                    raise IOError, unicode(fh.errorString())
                stream = QTextStream(fh)
                stream.setCodec("UTF-8")
                text = stream.readAll()
                self.editor.setPlainText(text)
                self.editor.document().setModified(False)
            except (IOError, OSError), e:
                QMessageBox.warning(self, "manageR - Load Error",
                        "Failed to load %s: %s" % (self.filename, e))
        finally:
            if fh is not None:
                fh.close()
            QApplication.restoreOverrideCursor()
        self.editor.document().setModified(False)
        self.setWindowModified(False)
        self.setWindowTitle("editR - %s[*]" %
                            QFileInfo(self.filename).fileName())


    def fileSave(self):
        if self.filename.startsWith("untitled"):
            return self.fileSaveAs()
        if (not Config["backupsuffix"].isEmpty() and
            QFile.exists(self.filename)):
            backup = self.filename + Config["backupsuffix"]
            ok = True
            if QFile.exists(backup):
                ok = QFile.remove(backup)
                if not ok:
                    QMessageBox.information(self,
                            "editR - Save Warning",
                            "Failed to remove the old backup %s")
            if ok:
                # Must use copy rather than rename to preserve file
                # permissions; could use rename on Windows though
                if not QFile.copy(self.filename, backup):
                    QMessageBox.information(self,
                            "editR - Save Warning",
                            "Failed to save a backup %s")
        fh = None
        try:
            try:
                fh = QFile(self.filename)
                if not fh.open(QIODevice.WriteOnly):
                    raise IOError, unicode(fh.errorString())
                stream = QTextStream(fh)
                stream.setCodec("UTF-8")
                stream << self.editor.toPlainText()
                self.editor.document().setModified(False)
                self.setWindowModified(False)
                self.setWindowTitle("editR - %s[*]" %
                        QFileInfo(self.filename).fileName())
                self.statusBar().showMessage("Saved %s" % self.filename,
                        5000)
            except (IOError, OSError), e:
                QMessageBox.warning(self, "editR - Save Error",
                        "Failed to save %s: %s" % (self.filename, e))
        finally:
            if fh is not None:
                fh.close()
        return True


    def fileSaveAs(self):
        filename = QFileDialog.getSaveFileName(self,
                            "editR - Save File As",
                            self.filename, "R scripts (*.R)")
        if not filename.isEmpty():
            self.filename = filename
            return self.fileSave()
        return False


    def fileSaveAll(self):
        count = 0
        for window in MainWindow.Instances:
            if (isAlive(window) and window != MainWindow.Console and
                window.editor.document().isModified()):
                if window.fileSave():
                    count += 1
        self.statusBar().showMessage("Saved %d of %d files" % (
                count, len(MainWindow.Instances) -
                       int(MainWindow.Console is not None)), 5000)

    def updateWindowMenu(self):
        self.windowMenu.clear()
        console = MainWindow.Console
        if console is not None and isAlive(console):
            action = self.windowMenu.addAction("&Console", self.raiseWindow)
            action.setData(QVariant(long(id(console))))
            action.setIcon(QIcon(":mActionConsole.png"))
        if (hasattr(self.editor, "results") and
            self.editor.results is not None and
            self.editor.results.isVisible()):
            action = self.windowMenu.addAction("&Results",
                    self.editor.raiseResultsWindow)
            action.setIcon(QIcon(":mActionWindow.png"))
        i = 1
        menu = self.windowMenu
        for window in MainWindow.Instances:
            if window != console and isAlive(window):
                text = (window.windowTitle().replace("manageR - ", "")
                                            .replace("[*]", ""))
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
                action = menu.addAction(text, self.raiseWindow)
                action.setData(QVariant(long(id(window))))
                action.setIcon(QIcon(":mActionWindow.png"))


    def raiseWindow(self):
        action = self.sender()
        if not isinstance(action, QAction):
            return
        windowId = action.data().toLongLong()[0]
        for window in MainWindow.Instances:
            if isAlive(window) and id(window) == windowId:
                window.activateWindow()
                window.raise_()
                break


    def helpHelp(self):
        HelpForm(self).show()


    def helpAbout(self):
        iconLabel = QLabel()
        icon = QPixmap(":mActionLogo.png")
        iconLabel.setPixmap(icon)
        nameLabel = QLabel("<font size=8 color=#0066CC>&nbsp;"
                                 "<b>manageR</b></font>")
        versionLabel = QLabel("<font color=#0066CC>"
                "%s on %s<br>"
                "manageR %s</font>" % (
                robjects.r.version[12][0], sys.platform,
                __version__))
        aboutLabel = QTextBrowser()
        aboutLabel.setOpenExternalLinks(True)
        aboutLabel.setHtml("""\
<h3>Interface to the R statistical programming environment</h3>
<h4>Copyright &copy; 2009 Carson J. Q. Farmer
<br/>Carson.Farmer@gmail.com
<br/><a href='http://www.ftools.ca/manageR'>http://www.ftools.ca/manageR</a>
<br/>manageR adds comprehensive statistical capabilities to Quantum 
GIS by loosely coupling QGIS with the R statistical programming environment.
""")
        thanksLabel = QTextBrowser()
        thanksLabel.setOpenExternalLinks(True)
        thanksLabel.setHtml("""<ul>
<li>Agustin Lobo (Bug fixing)
<li>Mark Summerfield (Sandbox editor example)
</ul>""")
        licenseLabel = QTextBrowser()
        licenseLabel.setOpenExternalLinks(True)
        licenseLabel.setHtml((__license__.replace("\n\n", "<p>")
                                         .replace("(c)", "&copy;")))

        tabWidget = QTabWidget()
        tabWidget.addTab(aboutLabel, "&About")
        tabWidget.addTab(thanksLabel, "&Thanks to")
        tabWidget.addTab(licenseLabel, "&License")
        okButton = QPushButton("OK")

        layout = QVBoxLayout()
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

        dialog = QDialog(self)
        dialog.setLayout(layout)
        dialog.setMinimumSize(
            min(self.width(),
                int(QApplication.desktop().availableGeometry()
                    .width() / 2)),
                int(QApplication.desktop().availableGeometry()
                    .height() / 2))
        self.connect(okButton, SIGNAL("clicked()"), dialog.accept)
        dialog.setWindowTitle("manageR - About")
        dialog.exec_()


def isAlive(qobj):
    import sip
    try:
        sip.unwrapinstance(qobj)
    except RuntimeError:
        return False
    return True


def main():
    if not hasattr(sys, "ps1"):
        sys.ps1 = ">>> "
    if not hasattr(sys, "ps2"):
        sys.ps2 = "... "
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    app.setOrganizationName("manageR")
    app.setOrganizationDomain("ftools.ca")
    app.setApplicationName("manageR")
    app.setWindowIcon(QIcon(":mActionIcon.png"))
    loadConfig()

    #for name in KEYWORDS + BUILTINS + CONSTANTS:
        #if len(name) >= MIN_COMPLETION_LEN and not name.startswith("_"):
            #CAT[name] = ""
            #try:
                #tip = eval("%s.__doc__" % name)
                #if tip is not None:
                    #CAT[name] = (tip[:MAX_TOOLTIP_LEN]
                                 #.strip().replace("\n\n", "<p>"))
            #except:
                #pass
    #for name in MODULES.keys():
        #CAT[name] = None

    if len(sys.argv) > 1:
        args = sys.argv[1:]
        if args[0] in ("-h", "--help"):
            args.pop(0)
            print """usage: manageR.py [-n|filenames]
-n or --new means start with new file
filenames   means start with the given files (which must have .R suffixes);
otherwise starts with new file or console
            depending on configuration
manageR requires Python 2.5 and PyQt 4.2 (or later versions)
For more information run the program and click
Help->About and Help->Help"""
            return
        if args and args[0] in ("-n", "--new"):
            args.pop(0)
            MainWindow().show()
        dir = QDir()
        for fname in args:
            if fname.endswith(".R"):
                MainWindow(dir.cleanPath(
                        dir.absoluteFilePath((fname)))).show()
    if not MainWindow.Instances:
        MainWindow(isConsole=True).show()

    app.exec_()
    saveConfig()


main()

### Ideas for improvements ##############################################
#
# - Make Indent & Unindent smarter, i.e., Indent should insert _up to_
#   tabwidth spaces to make the number of leading spaces an exact multiple
#   of tabwidth. Similarly, Unindent should remove _up to_ tabwidth
#   spaces on the same basis
# - Recent files handling
# - Add tooltips to all ConfigForm editing widgets & improve validation
# - Add tooltips to all main window actions that don't have any.
# - Goto menu. Use submenus to reflect the structure of the code, i.e.,
#   classes
#      Class1
#        Method1
#        Method2
#   functions
#       Func1
#       Func2
#          InnerFuncA
#   This should be doable when reading, but trickier to maintain when 
#   users add or change classes and defs since the right "parent" must be
#   found, and the name put in the right place in the tree
# - Robustness? catch exceptions better, etc.
# - Help? Handle help() in the console?
# - Tools menu? (modeless delete on close dialogs); e.g.,
#   Regular Expression Editor (similar to the one I wrote as an
#   example for TT); support multiple syntaxes, e.g., re, glob,
#   (fnmatch?), QRegExp, and QRegExp wildcard
# - i18n? use a custom dictionary-like function and keep all
#   translations in this same file; or embed .qm files in base64?
# - Autosave? If not zero auto saves every N seconds to
#   .sb$.self.filename. On close the .sb$. file is deleted after the
#   save. On open, if a .sb$. file exists, rename it self.filename#1 (or
#   2 or whatever to make it unique) and then give a warning to the user
#   that they may wish to diff against it. So we don't do recover as
#   such.
# - Make keyboard shortcuts customisable? (apart from the standard ones)
