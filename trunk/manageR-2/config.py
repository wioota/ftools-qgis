# -*- coding: utf-8 -*-

# PyQt imports
from PyQt4.QtGui import (QDialog, QListWidget, QListWidgetItem, QStackedWidget,
                         QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QSpinBox,
                         QPushButton, QListWidget, QWidget, QCheckBox, QFontComboBox,
                         QFont, QApplication, QIcon, QListView, QGroupBox, QLineEdit,
                         QPlainTextEdit, QFontMetrics, QPixmap, QColor, QColorDialog,
                         )
from PyQt4.QtCore import (SIGNAL, SLOT, QString, QSettings, QVariant, QSize, Qt,)

# generic Python imports
import sys, os

# config specific imports
import resources

class ConfigDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.contentsWidget = QListWidget()
        self.contentsWidget.setViewMode(QListView.IconMode)
        self.contentsWidget.setIconSize(QSize(96, 84))
        self.contentsWidget.setMovement(QListView.Static)
        self.contentsWidget.setMaximumWidth(128)
        self.contentsWidget.setSpacing(12)

        self.pagesWidget = QStackedWidget()
        self.pagesWidget.addWidget(GeneralPage())
        self.pagesWidget.addWidget(HighlightingPage())
        self.pagesWidget.addWidget(ConsolePage())

        closeButton = QPushButton("Close")

        self.createIcons()
        self.contentsWidget.setCurrentRow(0)

        self.connect(closeButton, SIGNAL("clicked()"), self, SLOT("close()"))

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(self.contentsWidget)
        horizontalLayout.addWidget(self.pagesWidget, 1)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(closeButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(horizontalLayout)
        mainLayout.addStretch(1)
        mainLayout.addSpacing(12)
        mainLayout.addLayout(buttonsLayout)
        self.setLayout(mainLayout)

        self.setWindowTitle("Configure manageR")

    def createIcons(self):
        generalButton = QListWidgetItem(self.contentsWidget)
        generalButton.setIcon(QIcon(":preferences-system.svg"))
        generalButton.setText("General")
        generalButton.setTextAlignment(Qt.AlignHCenter)
        generalButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        highlightingButton = QListWidgetItem(self.contentsWidget)
        highlightingButton.setIcon(QIcon(":applications-graphics.png"));
        highlightingButton.setText("Highlighting")
        highlightingButton.setTextAlignment(Qt.AlignHCenter)
        highlightingButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        consoleButton = QListWidgetItem(self.contentsWidget)
        consoleButton.setIcon(QIcon(":utilities-terminal-32.png"))
        consoleButton.setText("Console")
        consoleButton.setTextAlignment(Qt.AlignHCenter)
        consoleButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        editorButton = QListWidgetItem(self.contentsWidget)
        editorButton.setIcon(QIcon(":accessories-text-editor.png"));
        editorButton.setText("Editor")
        editorButton.setTextAlignment(Qt.AlignHCenter)
        editorButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        self.connect(self.contentsWidget,
                SIGNAL("currentItemChanged(QListWidgetItem*, QListWidgetItem*)"),
                self.changePage)

    def changePage(self, current, previous):
        if not current:
            current = previous
        self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))

class GeneralPage(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        settings = QSettings()
        monofont = QFont(settings.value("manageR/fontfamily", "DejaVu Sans Mono").toString(),
        settings.value("manageR/fontsize", 10).toInt()[0])
        self.rememberGeometryCheckBox = QCheckBox("&Remember geometry")
        self.rememberGeometryCheckBox.setToolTip("<p>Check this to make "
                "manageR remember the size and position of the console "
                "window and one editR window.</p>")
        self.rememberGeometryCheckBox.setChecked(settings.value("manageR/remembergeometry", True).toBool())

        self.tabWidthSpinBox = QSpinBox()
        self.tabWidthSpinBox.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.tabWidthSpinBox.setRange(2, 20)
        self.tabWidthSpinBox.setSuffix(" spaces")
        self.tabWidthSpinBox.setFont(monofont)
        self.tabWidthSpinBox.setValue(settings.value("manageR/tabwidth", 4).toInt()[0])
        self.tabWidthSpinBox.setToolTip("<p>Specify the number of "
                "spaces that a single tab should span.</p>")
        tabWidthLabel = QLabel("&Tab width:")
        tabWidthLabel.setBuddy(self.tabWidthSpinBox)

        self.fontComboBox = QFontComboBox()
        self.fontComboBox.setCurrentFont(monofont)
        self.fontComboBox.setFont(monofont)
        self.fontComboBox.setToolTip("<p>Specify the font family for "
                "the manageR console and all EditR windows.</p>")
        fontLabel = QLabel("&Font:")
        fontLabel.setBuddy(self.fontComboBox)

        self.fontSpinBox = QSpinBox()
        self.fontSpinBox.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.fontSpinBox.setRange(6, 20)
        self.fontSpinBox.setSuffix(" pt")
        self.fontSpinBox.setFont(monofont)
        self.fontSpinBox.setValue(settings.value("manageR/fontsize", 10).toInt()[0])
        self.fontSpinBox.setToolTip("<p>Specify the font size for  "
                "the manageR console, and all EditR windows.</p>")

        self.timeoutSpinBox = QSpinBox()
        self.timeoutSpinBox.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.timeoutSpinBox.setRange(0, 20000)
        self.timeoutSpinBox.setFont(monofont)
        self.timeoutSpinBox.setSingleStep(100)
        self.timeoutSpinBox.setSuffix(" ms")
        self.timeoutSpinBox.setValue(settings.value("manageR/delay", 500).toInt()[0])
        self.timeoutSpinBox.setToolTip("<p>Specify the time (in milliseconds) "
                "to wait before displaying the autocomplete popup when a set of "
                "possible matches are found.</p>")
        timeoutLabel = QLabel("Popup time delay:")
        timeoutLabel.setBuddy(self.timeoutSpinBox)

        self.mincharsSpinBox = QSpinBox()
        self.mincharsSpinBox.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.mincharsSpinBox.setRange(1, 100)
        self.mincharsSpinBox.setFont(monofont)
        self.mincharsSpinBox.setSuffix(" chars")
        self.mincharsSpinBox.setValue(settings.value("manageR/minimumchars", 3).toInt()[0])
        self.mincharsSpinBox.setToolTip("<p>Specify the minimum number of characters "
                "that must be typed before displaying the autocomplete popup when a "
                "set of possible matches are found.</p>")
        mincharsLabel = QLabel("Minimum word size:")
        mincharsLabel.setBuddy(self.mincharsSpinBox)

        self.autocompleteCheckBox = QCheckBox("Enable autocomplete/tooltips")
        self.autocompleteCheckBox.setToolTip("<p>Check this to enable "
                "autocompletion of R commands.</p>")
        self.autocompleteCheckBox.setChecked(settings.value("manageR/enableautocomplete", True).toBool())

        self.autocompleteBrackets = QCheckBox("Enable auto-insert of brackets/parentheses")
        self.autocompleteBrackets.setToolTip("<p>Check this to enable "
                "auto-insert of brackets and parentheses when typing R functions and commands.</p>")
        self.autocompleteBrackets.setChecked(settings.value("manageR/bracketautocomplete", True).toBool())

        vbox = QVBoxLayout()
        grid = QGridLayout()
        grid.addWidget(self.rememberGeometryCheckBox,0,0,1,3)
        grid.addWidget(fontLabel,1,0,1,1)
        grid.addWidget(self.fontComboBox,1,1,1,1)
        grid.addWidget(self.fontSpinBox,1,2,1,1)
        grid.addWidget(tabWidthLabel,2,0,1,1)
        grid.addWidget(self.tabWidthSpinBox,2,2,1,1,Qt.AlignRight)
        vbox.addLayout(grid)

        gbox = QGroupBox("Autocompletion")
        grid = QGridLayout()
        grid.addWidget(timeoutLabel,0,0,1,1)
        grid.addWidget(self.timeoutSpinBox,0,1,1,1,Qt.AlignRight)
        grid.addWidget(mincharsLabel,1,0,1,1)
        grid.addWidget(self.mincharsSpinBox,1,1,1,1,Qt.AlignRight)
        grid.addWidget(self.autocompleteCheckBox,2,0,1,2)
        grid.addWidget(self.autocompleteBrackets,3,0,1,2)
        gbox.setLayout(grid)

        vbox.addWidget(gbox)
        self.setLayout(vbox)

class ConsolePage(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        settings = QSettings()
        monofont = QFont(settings.value("manageR/fontfamily", "DejaVu Sans Mono").toString(),
        settings.value("manageR/fontsize", 10).toInt()[0])
        
        self.inputLineEdit = QLineEdit(settings.value("manageR/beforeinput", ">").toString())
        self.inputLineEdit.setMaxLength(3)
        self.inputLineEdit.setFont(monofont)
        self.inputLineEdit.setToolTip(
                "<p>Specify the prompt (e.g. '>') that will be "
                "displayed each time the console is ready for input.</p>")
        inputPromptLabel = QLabel("&Input prompt:")
        inputPromptLabel.setBuddy(self.inputLineEdit)

        self.outputLineEdit = QLineEdit(settings.value("manageR/afteroutput", "+").toString())
        self.outputLineEdit.setMaxLength(3)
        self.outputLineEdit.setFont(monofont)
        self.outputLineEdit.setToolTip(
                "<p>Specify the prompt (e.g. '+') that will "
                "be displayed each time further input to "
                "the console is required.</p>")
        outputPromptLabel = QLabel("&Continuation prompt:")
        outputPromptLabel.setBuddy(self.outputLineEdit)

        self.workingFolderLineEdit = QLineEdit(settings.value("manageR/setwd", ".").toString())
        self.workingFolderLineEdit.setFont(monofont)
        workingFolderLabel = QLabel("&Default working directory:")
        workingFolderLabel.setBuddy(self.workingFolderLineEdit)
        self.workingFolderLineEdit.setToolTip(
                "<p>Specify the default working directory for "
                "the manageR console. Setting this to blank, or "
                "'.', will use the current Python working directory. "
                "Changes made here only take effect when manageR is next started.</p>")

        self.useRasterPackage = QCheckBox("Use 'raster' package for importing rasters")
        self.useRasterPackage.setToolTip(
                "<p>Check this to make manageR use the 'raster' "
                "package for loading raster layers</p>")
        self.useRasterPackage.setChecked(settings.value("manageR/useraster", True).toBool())

        gbox = QGroupBox("&At startup")
        editor = QPlainTextEdit(self)
        editor.setPlainText(settings.value("manageR/consolestartup", "").toString())
        editor.setTabChangesFocus(True)
        editor.document().setDefaultFont(monofont)
        #Highlighter(editor.document())
        vbox = QVBoxLayout()
        vbox.addWidget(editor)
        vbox.addWidget(QLabel("<font color=green><i><p>manageR executes the lines above "
                 "whenever the R interpreter is started.<br/>"
                 "Use them to add custom functions and/or load "
                 "libraries or additional tools.<br/>"
                 "Changes made here only take effect when manageR is next run."))
        gbox.setLayout(vbox)

        grid = QGridLayout()
        grid.addWidget(inputPromptLabel,0,0,1,1)
        grid.addWidget(self.inputLineEdit,0,1,1,1,Qt.AlignRight)
        grid.addWidget(outputPromptLabel,1,0,1,1)
        grid.addWidget(self.outputLineEdit,1,1,1,1,Qt.AlignRight)
        grid.addWidget(workingFolderLabel,2,0,1,1)
        grid.addWidget(self.workingFolderLineEdit,2,1,1,1)
        grid.addWidget(self.useRasterPackage,3,0,1,2)
        grid.addWidget(gbox,4,0,1,2)
        self.setLayout(grid)

class HighlightingPage(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        settings = QSettings()
        monofont = QFont(settings.value("manageR/fontfamily", "DejaVu Sans Mono").toString(),
        settings.value("manageR/fontsize", 10).toInt()[0])
        fm = QFontMetrics(monofont)
        self.highlightingCheckBox = QCheckBox("Enable syntax highlighting")
        self.highlightingCheckBox.setToolTip("<p>Check this to enable "
                "syntax highlighting in the console and EditR windows."
                "Changes made here only take effect when manageR is next run.</p>")
        self.highlightingCheckBox.setChecked(settings.value("manageR/enablehighlighting", True).toBool())
        minButtonWidth = 0
        minWidth = 0
        label = QLabel("Background:")
        label.setMinimumWidth(minWidth)
        color = settings.value("manageR/backgroundcolor", "#FFFFFF").toString()
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(color))
        colorButton = QPushButton("&0 Color...")
        colorButton.setIcon(QIcon(pixmap))
        minButtonWidth = max(minButtonWidth, 10+pixmap.width()+fm.width(colorButton.text()))

        #self.colors["background"] = [Config["backgroundcolor"], None]
        #self.colors["background"][1] = colorButton
        self.connect(colorButton, SIGNAL("clicked()"),
            lambda button=colorButton, name="background": self.setColor(button, name))

        gbox = QGridLayout()
        gbox.addWidget(self.highlightingCheckBox, 0,0,1,3)
        gbox.addWidget(label,2,0,1,1)
        gbox.addWidget(colorButton,2,3,1,1)
        count = 1
        #labels = []
        #buttons = []
        for name, labelText in (("normal", "Normal:"), ("keyword", "Keywords:"),
                                ("builtin", "Builtins:"), ("constant", "Constants:"),
                                ("delimiter", "Delimiters:"), ("comment", "Comments:"),
                                ("string", "Strings:"), ("number", "Numbers:"),
                                ("error", "Errors:"), ("assignment", "Assignment operator:"),
                                ("syntax", "Syntax errors:")):
            label = QLabel(labelText)
            #labels.append(label)
            if name == "syntax":
                boldCheckBox = QCheckBox("Underline")
                boldCheckBox.setChecked(settings.value("manageR/%sfontunderline" % name, False).toBool())
            else:
                boldCheckBox = QCheckBox("Bold")
                boldCheckBox.setChecked(settings.value("manageR/%sfontbold" % name, False).toBool())
            #self.boldCheckBoxes[name] = boldCheckBox
            italicCheckBox = QCheckBox("Italic")
            italicCheckBox.setChecked(settings.value("manageR/%sfontitalic" % name, False).toBool())
            #self.italicCheckBoxes[name] = italicCheckBox
            #self.colors[name] = [Config["%sfontcolor" % name], None]
            if count <= 9:
                colorButton = QPushButton("&%d Color..." % count)
            else:
                colorButton = QPushButton("&%s Color..." % labelText[0])
            count += 1
            pixmap.fill(QColor(settings.value("manageR/%sfontcolor" % name).toString()))
            colorButton.setIcon(QIcon(pixmap))
            minButtonWidth = max(minButtonWidth, 10 + pixmap.width()+fm.width(colorButton.text()))
            #buttons.append(colorButton)
            #self.colors[name][1] = colorButton
            gbox.addWidget(label,count+2,0,1,1)
            gbox.addWidget(boldCheckBox,count+2,1,1,1)
            gbox.addWidget(italicCheckBox,count+2,2,1,1)
            gbox.addWidget(colorButton,count+2,3,1,1)
            self.connect(colorButton, SIGNAL("clicked()"),
                lambda button=colorButton, name=name: self.setColor(button, name))

        self.setLayout(gbox)

    def setColor(self, button, name):
        settings = QSettings()
        color = QColorDialog.getColor(
            QColor(settings.value("manageR/%sfontcolor" % name, "#FFFFFF").toString()), self)
        if color is not None:
            settings.setValue("manageR/%sfontcolor" % name, color.name())
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(color.name()))
            button.setIcon(QIcon(pixmap))

def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    app.setOrganizationName("manageR")
    app.setOrganizationDomain("ftools.ca")
    app.setApplicationName("manageR")
    app.setWindowIcon(QIcon(":mActionIcon.png"))
    app.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))
    dialog = ConfigDialog(None)
    dialog.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()