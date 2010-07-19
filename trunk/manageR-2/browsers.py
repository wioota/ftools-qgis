# -*- coding: utf-8 -*-

from PyQt4.QtCore import (QString, QStringList, QUrl, SIGNAL, SLOT, QFileInfo,
                          QEventLoop, Qt, QVariant, QRegExp, QObject)
from PyQt4.QtGui import (QPixmap, QDialog, QLabel, QIcon, QTextBrowser, QTabWidget,
                         QToolButton, QAction, QWidget, QShortcut, QKeySequence,
                         QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton,
                         QAbstractItemView, QListWidget, QTableWidget, QTextDocument,
                         QLineEdit, QGroupBox, QApplication, QTableWidgetItem,
                         QDialogButtonBox, QTextEdit, )
from PyQt4.QtNetwork import QHttp

import rpy2.robjects as robjects
import sys, os
from multiprocessing import Process, Queue, Lock, Pipe

class AboutBrowser(QDialog):
    def __init__(self, parent=None, version=0.1, license="", currentdir="."):
        QDialog.__init__(self, parent)
        iconLabel = QLabel()
        icon = QPixmap(":logo.png")
        iconLabel.setPixmap(icon)
        nameLabel = QLabel(
            "<font size=8 color=#0066CC>&nbsp;<b>manageR</b></font>")
        versionLabel = QLabel(
            "<font color=#0066CC>%s on %s<br>manageR %s</font>" % (
            robjects.r.version[12][0], sys.platform, version))
        aboutBrowser = QTextBrowser()
        aboutBrowser.setOpenExternalLinks(True)
        aboutBrowser.setHtml(
            "<h3>Interface to the R statistical programming environment</h3>"
            "Copyright &copy; 2009-2010 Carson J. Q. Farmer"
            "<br/>Carson.Farmer@gmail.com"
            "<br/><a href='http://www.ftools.ca/manageR'>http://www.ftools.ca/manageR</a>")
        licenseBrowser = QTextBrowser()
        licenseBrowser.setOpenExternalLinks(True)
        licenseBrowser.setHtml((license.replace("\n\n", "<p>").replace("(C)", "&copy;")))
        helpBrowser = QTextBrowser()
        helpBrowser.setOpenExternalLinks(True)
        helpBrowser.setHtml(
            "<center><h2>manageR version %s documentation</h2></center>"
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
            "Hold down <tt>Shift</tt> when pressing movement keys to select the text moved over.<br>" % (version, currentdir))

        tabWidget = QTabWidget()
        tabWidget.addTab(aboutBrowser, "&About")
        tabWidget.addTab(licenseBrowser, "&License")
        tabWidget.addTab(helpBrowser, "&Help")

        layout = QVBoxLayout(self)
        hbox = QHBoxLayout()
        hbox.addWidget(iconLabel)
        hbox.addWidget(nameLabel)
        hbox.addStretch()
        hbox.addWidget(versionLabel)
        layout.addLayout(hbox)
        layout.addWidget(tabWidget)

        self.setMinimumSize(min(self.width(),
            int(QApplication.desktop().availableGeometry().width() / 2)),
            int(QApplication.desktop().availableGeometry().height() / 2))
        self.setWindowTitle("manageR - About")

class RMirrorBrowser(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        kwargs = {"local.only":False}
        m = robjects.r.getCRANmirrors(all=False, **kwargs)
        names = QStringList(list(m.rx('Name')[0]))
        urls = list(m.rx('URL')[0])
        self.links = dict(zip(names, urls))
        names = QStringList(names)
        self.setWindowTitle("manageR - Choose CRAN Mirror")
        self.setWindowIcon(QIcon(":icon.png"))
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
        self.setWindowIcon(QIcon(":icon.png"))
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
                    #self.started = False
                    #self.killTimer(e.timerId())
                    #if self.closeCheckbox.isChecked():
                        #self.reject()
            except EOFError:
                pass
        #else:
            #self.killTimer(e.timerId())
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
            print url
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
                if data.toString().trimmed().isEmpty():
                    fileName = QFileInfo(
                    name.toLocalFile()).fileName()
                    data = QTextBrowser.loadResource(self, type, QUrl(fileName))
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
        homeAction.setIcon(QIcon(":go-home.svg"))
        homeButton.setDefaultAction(homeAction)
        homeAction.setEnabled(True)
        homeButton.setAutoRaise(True)

        backwardButton = QToolButton(self)
        backwardAction = QAction("&Back", self)
        backwardAction.setToolTip("Move to previous page")
        backwardAction.setWhatsThis("Move to previous page")
        backwardAction.setIcon(QIcon(":go-previous.svg"))
        backwardButton.setDefaultAction(backwardAction)
        backwardAction.setEnabled(False)
        backwardButton.setAutoRaise(True)

        forwardButton = QToolButton(self)
        forwardAction = QAction("&Forward", self)
        forwardAction.setToolTip("Move to next page")
        forwardAction.setWhatsThis("Move to next page")
        forwardAction.setIcon(QIcon(":go-next.svg"))
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
