# -*- coding: utf-8 -*-
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from PyQt4.QtXml import *
#from PyQt4.QtSql import *
from qgis.core import *
import sys, os, resources
from plugins_dialog import (SpinBox, DoubleSpinBox, ComboBox, CheckBox, LineEdit, 
                            ModelBuilderBox, SingleVariableBox, MultipleVariableBox,
                            AxesBox, MinMaxBox, PlotOptionsWidget, LineStyleBox,
                            BoundingBoxBox, PlotTypeBox, TitlesBox, ParametersBox,
                            PluginDialog, Widget)

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
            fst = self.parent.menuBar().addMenu(cat)
            for (sub, second) in first.iteritems():
                if sub in ("__default__", ""):
                    snd = fst
                else:
                    snd = QMenu(sub, fst)
                    fst.addMenu(snd)
                    #sub.setIcon(QIcon(":second-analysis-menu.svg"))
                for (tool, third) in second.iteritems():
                    self.createTool(tool, snd, third)

    def run(self, name, data):
        dialog = PluginDialog(self.parent, name)
        structure = data.toPyObject()
        self.query = structure.pop(QString('query'), None)
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
        dialog.show()

    def runCommand(self, params):
        query = self.query
        extras = QString()
        finals = QString()
        for (key, value) in params.iteritems():
            try:
                x = int(key)
                query.replace("|%s|" % x, value)
            except ValueError:
                QMessageBox.warning(self.parent, "manageR - Plugin Error",
                "Error building command string")
        # go through all params, starting with anything that has an id fields
        #     if it has a number, replace the number in the query text
        # next do everything else besides the extra parameters
        # then the extra parameters
        # then grid if it was there

    def createTool(self, name, menu, data):
        #action = QAction(QIcon(":analysis-tool.svg"), name, self.parent)
        action = QAction(name, self.parent)
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
        if type == "SpinBox":
            widget = SpinBox(fields[QString("id")], fields[QString("label")])
        elif type == "DoubleSpinBox":
            widget = DoubleSpinBox(fields[QString("id")], fields[QString("label")])
        elif type == "ComboBox":
            widget = ComboBox(fields[QString("id")], fields[QString("label")])
            widget.addItems(fields[QString("defaults")].split(";"))
        elif type == "CheckBox":
            widget = CheckBox(fields[QString("id")], fields[QString("label")])
            if fields[QString("default")].lowerCase() == "true":
                widget.setChecked(True)
            else:
                widget.setChecked(False)
        elif type == "ModelBuilderBox":
            widget = ModelBuilderBox(fields[QString("id")])
        elif type == "SingleVariableBox":
            widget = SingleVariableBox(fields[QString("id")], fields[QString("label")])
        elif type == "MultipleVariableBox":
            widget = MultipleVariableBox(fields[QString("id")], fields[QString("label")])
        elif type == "AxesBox":
            ops = fields[QString("default")].split(";")
            logscale = False
            style = False
            if "logscale" in ops:
                logscale = True
            if "style" in ops:
                style = True
            widget = AxesBox(logscale, style)
        elif type == "MinMaxBox":
            widget = MinMaxBox()
        elif type == "PlotOptionsBox":
            ops = fields[QString("default")].split(";")
            box = False
            titles = False
            axes = False
            logscale = False
            style = False
            minmax = False
            grid = False
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
            if "grid" in ops:
                grid = True
            widget = PlotOptionsWidget(box, titles, axes, logscale, style, minmax, grid)
        elif type == "LineStyleBox":
            widget = LineStyleBox()
        elif type == "BoundingBoxBox":
            widget = BoundingBoxBox()
        elif type == "PlotTypeBox":
            widget = PlotTypeBox()
        elif type == "TitlesBox":
            widget = TitlesBox()
        elif type == "ParametersBox":
            widget = ParametersBox()
        else: # default to line edit (LineEditBox)
            widget = LineEdit(fields[QString("id")], fields[QString("label")])
            widget.widget.setText(fields[QString("default")])
        return widget

class Handler(QXmlDefaultHandler):
    def __init__(self):
        QXmlDefaultHandler.__init__(self)
        self.struct = {}

    def fatalError(self, err):
        QMessageBox.warning(None, "manageR - XML Parsing Error",
            "Fatal error on line %s" % err.lineNumber()
            + ", column %s " % err.columnNumber()
            + ": %s" % err.message())
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
        elif name == "Query":
            self.inQuery = False
        elif name == "Page":
            self.inPage = False
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
            for i in range(attrs.count()):
                tmp = attrs.localName(i)
                if tmp == "name":
                    nm = attrs.value(i)
                elif tmp == "subcategory":
                    scat = attrs.value(i)
            self.currentSub = scat
            if not self.currentSub in self.struct[self.currentCat]:
                self.struct[self.currentCat][self.currentSub] = {}
            if len(nm) > 1:
                self.currentTool = nm
                self.struct[self.currentCat][self.currentSub][self.currentTool] = {}
        elif self.inTool:
            if name == "Help":
                tmp = ""
                for i in range(attrs.count()):
                    ln = attrs.localName(i)
                    val = attrs.value(i)
                    if ln == "name" and isinstance(val, QString) and len(val) > 0:
                        tmp = val
                self.helpTopic = tmp
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
