# -*- coding: utf-8 -*-
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from PyQt4.QtXml import *
#from PyQt4.QtSql import *
#from qgis.core import *
import sys, os, resources
from plugins_dialog import (SpinBox, DoubleSpinBox, ComboBox, CheckBox, LineEdit, 
                            ModelBuilderBox, VariableLineBox, VariableListBox,
                            AxesBox, MinMaxBox, PlotOptionsWidget, LineStyleBox,
                            BoundingBoxBox, PlotTypeBox, TitlesBox, ParametersBox,
                            PluginDialog, Widget, VariableComboBox, GridCheckBox)
CURRENTDIR = unicode(os.path.abspath(os.path.dirname(__file__)))

class PluginManager(QObject):
    def __init__(self, parent=None, path="."):
        self.parent = parent
        QObject.__init__(self)
        filters = QStringList(["*.xml"])
        dir = QDir(path)
        dir.setNameFilters(filters)
        self.files = dir.entryInfoList()

    def parseXmlFiles(self):
        reader = QXmlSimpleReader()
        handler = Handler()
        reader.setContentHandler(handler)
        reader.setErrorHandler(handler)
        self.structure = {}
        errors = False
        for file in self.files:
            tmp = QFile(file.absoluteFilePath())
            source = QXmlInputSource(tmp)
            handler.setDocumentStructure(self.structure)
            ok = reader.parse(source)
            if not ok:
                errors = True
            else:
                self.structure = handler.documentStructure()

    def createPlugins(self):
        for (cat, first) in self.structure.iteritems():
            if cat in ("__default__", ""):
                cat = "Plugins"
            menu = self.parent.menuBar()
            found = False
            for child in menu.findChildren(QMenu):
                title = child.title()
                title.remove("&")
                if title.trimmed() == cat.trimmed():
                    found = True
                    break
            if found:
                fst = child
            else:
                fst = menu.addMenu(cat)
            for (sub, second) in first.iteritems():
                if sub in ("__default__", ""):
                    snd = fst
                else:
                    snd = QMenu(sub, fst)
                    fst.addMenu(snd)
                    snd.setIcon(QIcon(":extension.svg"))
                for (tool, third) in second.iteritems():
                    icon = third.pop("icon", None)
                    self.createTool(tool, snd, third, icon)

    def run(self, name, data):
        dialog = PluginDialog(self.parent, name)
        structure = data.toPyObject()
        self.query = structure.pop(QString('query'), None)
        self.help = structure.pop(QString('help'), None)
        if self.query is None:
            QMessageBox.warning(self.parent, "manageR - Plugin Error",
            "Error building tool user interface")
            return
        page = "Main"
        for (page, rest) in structure.iteritems():
            if page == "__default__":
                page = "Main"
            column = "main"
            for (column, widgets) in rest.iteritems():
                if column == "__default__":
                    column = "main"
                for widget in widgets:
                    dialog.addWidget(self.createGuiItem(widget), page)
        self.connect(dialog, SIGNAL("pluginOutput(PyQt_PyObject)"), self.runCommand)
        self.connect(dialog, SIGNAL("helpRequested()"), self.runHelp)
        dialog.show()

    def runCommand(self, params):
        query = QString(self.query)
        if query.startsWith('"') or query.startsWith("'"):
            query = query[1:]
        if query.endsWith('"') or query.endsWith("'"):
            query = query[0:-1]
        for (key, value) in params.iteritems():
            try:
                query.replace("|%s|" % key, unicode(value))
            except ValueError:
                QMessageBox.warning(self.parent, "manageR - Plugin Error",
                "Error building command string")
        regexp = QRegExp(r",\s*(?=[,\)]\s*)")
        query.remove(regexp)
        self.emit(SIGNAL("emitCommands(QString)"), query)
        
    def runHelp(self):
        help = QString("?%s" % self.help)
        self.emit(SIGNAL("emitCommands(QString)"), help)

    def createTool(self, name, menu, data, icon=None):
        if not icon is None:
            icon = QIcon(os.path.join(CURRENTDIR,unicode(icon)))
        else:
            icon = QIcon(":system-run.svg")
        action = QAction(icon, name, self.parent)
        action.setData(QVariant(data))
        QObject.connect(action, SIGNAL("activated()"), lambda: self.run(name, action.data()))
        self.parent.addActions(menu, (action,))

    def createGuiItem(self, fields):
        try:
            type = fields[QString("type")]
        except KeyError:
            QMessageBox.warning(self.parent, "manageR - Plugin Error",
            "Widget missing 'type' field in plugin XML file")
            return
        widget = Widget()
        try:
            if type == "SpinBox":
                widget = SpinBox(fields[QString("id")], fields[QString("label")])
                widget.widget.setValue(int(fields[QString("default")]))
            elif type == "DoubleSpinBox":
                widget = DoubleSpinBox(fields[QString("id")], fields[QString("label")])
                widget.widget.setValue(float(fields[QString("default")]))
            elif type == "ComboBox":
                widget = ComboBox(fields[QString("id")], fields[QString("label")])
                widget.widget.addItems(fields[QString("default")].split(";"))
            elif type == "CheckBox":
                widget = CheckBox(fields[QString("id")], fields[QString("label")])
                if fields[QString("default")].toLower() == "true":
                    widget.setChecked(True)
                else:
                    widget.setChecked(False)
            elif type == "VariableComboBox":
                widget = VariableComboBox(fields[QString("id")])
            elif type == "VariableLineBox":
                widget = VariableLineBox(fields[QString("id")], fields[QString("label")])
            elif type == "VariableListBox":
                sep=","
                try:
                    sep = fields[QString("separator")]
                except KeyError:
                    pass
                widget = VariableListBox(fields[QString("id")], fields[QString("label")], sep)
            elif type == "AxesBox":
                ops = fields[QString("default")].split(";")
                logscale = False
                style = False
                if "logscale" in ops:
                    logscale = True
                if "style" in ops:
                    style = True
                widget = AxesBox(fields[QString("id")], logscale, style)
            elif type == "MinMaxBox":
                widget = MinMaxBox(fields[QString("id")])
            elif type == "GridCheckBox":
                widget = GridCheckBox(fields[QString("id")])
                if fields[QString("default")].toLower() == "true":
                    widget.widget.setChecked(True)
                else:
                    widget.setChecked(False)
            elif type == "PlotOptionsBox":
                ops = fields[QString("default")].split(";")
                box = False
                titles = False
                axes = False
                logscale = False
                style = False
                minmax = False
                if "logscale" in ops:
                    logscale = True
                if "style" in ops:
                    style = True
                if "titles" in ops:
                    titles = True
                if "axes" in ops:
                    axes = True
                if "box" in ops:
                    box = True
                if "minmax" in ops:
                    minmax = True
                widget = PlotOptionsWidget(fields[QString("id")], box, titles, axes, logscale, style, minmax)
            elif type == "LineStyleBox":
                widget = LineStyleBox(fields[QString("id")])
            elif type == "BoundingBoxBox":
                widget = BoundingBoxBox(fields[QString("id")])
            elif type == "PlotTypeBox":
                widget = PlotTypeBox(fields[QString("id")])
            elif type == "TitlesBox":
                widget = TitlesBox(fields[QString("id")])
            elif type == "ParametersBox":
                widget = ParametersBox()
            else: # default to line edit (LineEditBox)
                widget = LineEdit(fields[QString("id")], fields[QString("label")])
                widget.widget.setText(fields[QString("default")])
        except KeyError, e:
            QMessageBox.warning(self.parent, "manageR - Plugin Error",
            "Widget missing required field in plugin XML file:\n"
            +str(e))
            return
        return widget

class Handler(QXmlDefaultHandler):
    def __init__(self):
        QXmlDefaultHandler.__init__(self)
        self.struct = {}

    def fatalError(self, err):
        QMessageBox.warning(None, "manageR - XML Parsing Error",
            "Error encountered when building '%s' tool!\n" % self.currentTool
            + "There was a problem with the XML file for "
            + "the '%s' category:\n" % self.currentCat
            + "    Fatal error on line %s" % err.lineNumber()
            + ", column %s (%s)\n" % (err.columnNumber(), err.message())
            + "Some plugin tools and menus have been ignored.")
        return False

    def startDocument(self):
        self.inTool = False
        self.inQuery = False
        self.inPage = False
        self.currentPage = "__default__"
        self.currentTool = "__default__"
        self.currentCat = "__default__"
        self.currentSub = "__default__"
        self.currentColumn = "__default__"
        return True

    def setDocumentStructure(self, structure):
        self.struct = structure

    def documentStructure(self):
        return self.struct

    def endElement(self, str1, str2, name):
        if name == "RTool":
            self.inTool = False
            self.currentTool = "__default__"
        elif name == "Query":
            self.inQuery = False
        elif name == "Page":
            self.inPage = False
            self.currentPage = "__default__"
        return True

    def characters(self, chars):
        if self.inQuery:
            self.struct[self.currentCat][self.currentSub][self.currentTool].update({"query":chars})
        return True

    def startElement(self, str1, str2, name, attrs):
        if name == "manageRTools":
            cat = ""
            for i in range(attrs.count()):
                if attrs.localName(i) == "category":
                    cat = attrs.value(i)
            self.currentCat = cat
            if not self.currentCat in self.struct:
                self.struct[self.currentCat] = {}
        elif name == "RTool":
            self.inTool = True
            nm = "__default__"
            scat = "__default__"
            icn = None
            for i in range(attrs.count()):
                tmp = attrs.localName(i)
                if tmp == "name":
                    nm = attrs.value(i)
                elif tmp == "subcategory":
                    scat = attrs.value(i)
                elif tmp == "icon":
                    icn = attrs.value(i)
            self.currentSub = scat
            if not self.currentSub in self.struct[self.currentCat]:
                self.struct[self.currentCat][self.currentSub] = {}
            if len(nm) > 1:
                self.currentTool = nm
                self.struct[self.currentCat][self.currentSub][self.currentTool] = {}
                self.struct[self.currentCat][self.currentSub][self.currentTool].update({"icon":icn})
        elif self.inTool:
            if name == "Help":
                tmp = ""
                for i in range(attrs.count()):
                    ln = attrs.localName(i)
                    val = attrs.value(i)
                    if ln == "name" and isinstance(val, QString) and len(val) > 0:
                        tmp = val
                self.struct[self.currentCat][self.currentSub][self.currentTool].update({"help":tmp})
            elif name == "Query":
                self.inQuery = True
            elif name == "Page":
                if self.inPage:
                    raise Exception("Error: Cannot have nested pages in plugin GUIs")
                self.inPage = True
                tmp = "__default__"
                for i in range(attrs.count()):
                    ln = attrs.localName(i)
                    val = attrs.value(i)
                    if ln == "name" and isinstance(val, QString) and len(val) > 0:
                        tmp = val
                self.currentPage = tmp
                if not self.currentPage in self.struct[self.currentCat][self.currentSub][self.currentTool]:
                    self.struct[self.currentCat][self.currentSub][self.currentTool][self.currentPage] = {}
            elif name == "Column":
                self.inColumn = True
                tmp = "__default__"
                for i in range(attrs.count()):
                    ln = attrs.localName(i)
                    val = attrs.value(i)
                    if ln == "name" and isinstance(val, QString) and len(val) > 0:
                        tmp = val
                self.currentColumn = tmp
                if not self.currentColumn in self.struct[self.currentCat][self.currentSub][self.currentTool][self.currentPage]:
                    self.struct[self.currentCat][self.currentSub][self.currentTool][self.currentPage][self.currentColumn] = []
            elif name == "Widget":
                # each tool stores a list of dicts that describe the individual widgets
                # query is also a dict, with a single key:pair {'query':'plot(|1|)'}
                wid = { QString("id")     : QString("0"),
                        QString("label")  : QString(""),
                        QString("type")   : QString("lineEdit"),
                        QString("default"): QString("") }
                for i in range(attrs.count()):
                    wid[attrs.localName(i)] = attrs.value(i)
                try:
                    self.struct[self.currentCat][self.currentSub][self.currentTool][self.currentPage][self.currentColumn].append(wid)
                except KeyError:
                    try:
                        self.struct[self.currentCat][self.currentSub][self.currentTool][self.currentPage][self.currentColumn] = [wid]
                    except KeyError:
                        self.struct[self.currentCat][self.currentSub][self.currentTool][self.currentPage] = {self.currentColumn:[wid]}
        return True


def main():
    app = QApplication(sys.argv)
    #if not sys.platform.startswith(("linux", "win")):
        #app.setCursorFlashTime(0)
    #robjects.r.load(".RData")
    window = QMainWindow(None)
    window.show()
    filters = QStringList(["*.xml"])
    dir = QDir(".")
    dir.setNameFilters(filters)
    files = dir.entryList(QDir.Readable|QDir.Files)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
