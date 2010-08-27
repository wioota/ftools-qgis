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
                            PluginDialog, Widget, VariableComboBox, GridCheckBox,
                            RadioGroupBox)
CURRENTDIR = unicode(os.path.abspath(os.path.dirname(__file__)))

class Page:
    def __init__(self, name="Main", parent=None):
        self.__name__ = name
        self.__columns__ = []
        self.__parent__ = parent
        
    def parent(self):
        return self.__parent__
        
    def name(self):
        return self.__name__

    def columns(self):
        return self.__columns__
        
    def addColumn(self, column):
        self.__columns__.append(column)
        
    def widgets(self):
        widgets = []
        for column in self.columns():
            for group in column.groups():
                for widget in group:
                    widgets.append(widget)
        return widgets
        
class Group:
    def __init__(self, name="__default__", parent=None):
        self.__name__ = name
        self.__parent__ = parent
        self.__checkable__ = False
        self.__id__ = -1
        self.__widgets__ = []
        
    def parent(self):
        return self.__parent__
        
    def name(self):
        return self.__name__
        
    def setName(self, name):
        if isinstance(name, QString):
            self.__name__ = name
            
    def id(self):
        return self.__id__
        
    def setId(self, id):
        if isinstance(id, QString):
            self.__id__ = id
        
    def setCheckable(self, checkable):
        if isinstance(checkable, bool):
            self.__checkable__ = checkable
        else:
            self.__checkable__ = False
            
    def isCheckable(self):
        return self.__checkable__
        
    def addWidget(self, widget):
        self.__widgets__.append(widget)
        
    def widgets(self):
        return self.__widgets__
        
class Column:
    def __init__(self, name="__default__", parent=None):
        self.__groups__ = []
        self.__parent__ = parent
        if not parent is None:
            self.__id__ = parent.id()+1
        else:
            self.__id__ = 0
        
    def id(self):
        return self.__id__
        
    def parent(self):
        return self.__parent__
        
    def addGroup(self, group):
        self.__groups__.append(group)
        
    def groups(self):
        return self.__groups__

class Tool:
    def __init__(self, name="__default__", query=None,
                       help=None, icon=None, gui=None):
        self.__query__ = None
        self.__help__ = None
        if gui is None:
            self.__gui__ = []
        self.__name__ = name
        self.__sub__= None
        self.__icon__ = QIcon(":system-run.svg")
        
    def setName(self, name):
        if not isinstance(name, QString):
            raise TypeError("Error: Expected type QString")
        self.__name__ = name
        
    def name(self):
        return self.__name__
        
    def setIcon(self, icon):
        if not isinstance(icon, QString):
            raise TypeError("Error: Expected type QString")
        self.__icon__ = icon.trimmed()
        
    def icon(self):
        return self.__icon__

    def setGui(self, gui):
        if not isinstance(gui, list):
            raise TypeError("Error: Expected type list")
        self.__gui__ = gui
        
    def gui(self):
        return self.__gui__
        
    def setQuery(self, query):
        if not isinstance(query, QString):
            raise TypeError("Error: Expected type QString")
        self.__query__ = query.trimmed()
            
    def query(self):
        return self.__query__
        
    def setHelp(self, help):
        if not isinstance(help, QString):
            raise TypeError("Error: Expected type QString")
        self.__help__ = help.trimmed()
            
    def help(self):
        return self.__help__
        
    def setSubcategory(self, sub):
        if not isinstance(sub, QString):
            raise TypeError("Error: Expected type QString")
        self.__sub__ = sub.trimmed()
            
    def subcategory(self):
        return self.__sub__

class PluginManager(QObject):
    def __init__(self, parent=None, path="."):
        QObject.__init__(self, parent)
        filters = QStringList(["*.xml"])
        dir = QDir(path)
        self.path = path
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
        for (cat, tools) in self.structure.iteritems():
            main = self.parent().menuBar()
            menu = None
            # check to see if we already have a menu by this name
            for child in main.findChildren(QMenu):
                title = child.title()
                title.remove("&")
                if title.trimmed() == cat.trimmed():
                    menu = child
                    break
            if menu is None:
                menu = main.addMenu(cat)
            for tool in tools:
                sub = tool.subcategory()
                # check to see if we already have a (sub)menu by this name
                for child in menu.findChildren(QMenu):
                    title = child.title()
                    title.remove("&")
                    if title.trimmed() == sub:
                        sub = child
                        break
                if sub is None:
                    sub = menu
                elif isinstance(sub, QString):
                    sub = menu.addMenu(sub)
                    sub.setIcon(QIcon(":extension.svg"))
                self.createTool(tool, sub)

    def run(self, tool):
        dialog = PluginDialog(self.parent(), tool.name())
        self.query = tool.query()
        self.help = tool.help()
        if self.query is None:
            QMessageBox.warning(self.parent(), "manageR - Plugin Error",
            "Error building tool user interface")
            return
        for page in tool.gui():
            dialog.addPage(page.name())
            print page.name()
            for column in page.columns():
                print column.id()
                dialog.addColumn(column.id())
                for group in column.groups():
                    print group.name()
                    if group.isCheckable():
                        dialog.addGroup(group.id(), group.name(), group.isCheckable())
                    else:
                        dialog.addGroup(name=group.name())
                    for widget in group.widgets():
                        print widget[QString("type")]
                        dialog.addWidget(self.createGuiItem(widget))
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
                QMessageBox.warning(self.parent(), "manageR - Plugin Error",
                "Error building command string")
        regexp = QRegExp(r",\s*(?=[,\)]\s*)")
        query.remove(regexp)
        self.emit(SIGNAL("emitCommands(QString)"), query)
        
    def runHelp(self):
        help = QString("?%s" % self.help)
        self.emit(SIGNAL("emitCommands(QString)"), help)

    def createTool(self, tool, menu):
        icon = tool.icon()
        if not isinstance(icon, QIcon):
            icon = QIcon(os.path.join(unicode(self.path), unicode(icon)))
        action = QAction(icon, tool.name(), self.parent())
        action.setData(QVariant(tool))
        QObject.connect(action, SIGNAL("activated()"), lambda: self.run(tool))
        self.parent().addActions(menu, (action,))

    def createGuiItem(self, fields):
        try:
            type = fields[QString("type")]
        except KeyError:
            QMessageBox.warning(self.parent(), "manageR - Plugin Error",
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
            elif type == "RadioGroupBox":
                ops = fields[QString("default")].split(";")
                widget = RadioGroupBox(fields[QString("id")])
                widget.setTitle(fields[QString("label")])
                for subwidget in ops:
                    widget.addButton(subwidget)
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
            QMessageBox.warning(self.parent(), "manageR - Plugin Error",
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
            "Error encountered when building '%s' tool!\n" % self.currentTool.name()
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
        self.inGroup = False
        self.currentGroup = Group()
        self.currentColumn = Column()
        self.currentPage = Page()
        self.currentColumn.addGroup(self.currentGroup)
        self.currentPage.addColumn(self.currentColumn)
        self.currentTool = Tool()
        self.currentTool.gui().append(self.currentPage)
        self.currentCat = QString("Plugins")
        return True

    def setDocumentStructure(self, structure):
        self.struct = structure

    def documentStructure(self):
        return self.struct

    def endElement(self, str1, str2, name):
        if name == "RTool":
            self.inTool = False
            self.struct[self.currentCat].append(self.currentTool)
        elif name == "Query":
            self.inQuery = False
        elif name == "Page":
            self.inPage = False
            self.currentTool.gui().append(self.currentPage)
            self.currentPage = self.currentPage.parent()
        elif name == "Group":
            self.inGroup = False
            self.currentColumn.addGroup(self.currentGroup)
            self.currentGroup = self.currentGroup.parent()
        elif name == "Column":
            self.inColumn = False
            self.currentPage.addColumn(self.currentColumn)
            self.currentColumn = self.currentColumn.parent()
        return True

    def characters(self, chars):
        if self.inQuery:
            self.currentTool.setQuery(chars)
        return True

    def startElement(self, str1, str2, name, attrs):
        if name == "manageRTools":
            for i in range(attrs.count()):
                if attrs.localName(i) == "category" and not attrs.value(i).isEmpty():
                    self.currentCat = attrs.value(i)
                    break
            if not self.currentCat in self.struct:
                self.struct[self.currentCat] = []
        elif name == "RTool":
            self.inTool = True
            tool = Tool()
            for i in range(attrs.count()):
                tmp = attrs.localName(i)
                if tmp == "name":
                    tool.setName(attrs.value(i))
                elif tmp == "subcategory":
                    tool.setSubcategory(attrs.value(i))
                elif tmp == "icon":
                    tool.setIcon(attrs.value(i))
            self.currentGroup = Group()
            self.currentPage = Page()
            self.currentColumn = Column()
            self.currentPage.addColumn(self.currentColumn)
            self.currentColumn.addGroup(self.currentGroup)
            self.currentTool = tool
            self.currentTool.gui().append(self.currentPage)
        elif self.inTool:
            if name == "Help":
                for i in range(attrs.count()):
                    if attrs.localName(i) == "name" and not attrs.value(i).isEmpty():
                        self.currentTool.setHelp(attrs.value(i))
                        break
            elif name == "Query":
                self.inQuery = True
            elif name == "Page":
                if self.inPage:
                    raise Exception("Error: Cannot have nested pages in plugin GUIs")
                self.inPage = True
                for i in range(attrs.count()):
                    if attrs.localName(i) == "name" and not attrs.value(i).isEmpty():
                        self.currentPage = Page(attrs.value(i), self.currentPage)
                        break
                self.currentColumn = Column()
                self.currentPage.addColumn(self.currentColumn)
                self.currentGroup = Group()
                self.currentColumn.addGroup(self.currentGroup)
            elif name == "Column":
                if self.inColumn:
                    raise Exception("Error: Cannot have nested columns in plugin GUIs")
                if self.inGroup:
                    raise Exception("Error: Cannot have columns inside groups")
                self.inColumn = True
                self.currentColumn = Column(parent=self.currentColumn)
                self.currentGroup = Group()
                self.currentColumn.addGroup(self.currentGroup)
            elif name == "Group":
                self.inGroup = True
                group = Group(parent=self.currentGroup)
                for i in range(attrs.count()):
                    if attrs.localName(i) == "name" and not attrs.value(i).isEmpty():
                        group.setName(attrs.value(i))
                    if attrs.localName(i) == "id" and not attrs.value(i).isEmpty():
                        group.setId(attrs.value(i))
                    if attrs.localName(i) == "checkable" and not attrs.value(i).isEmpty():
                        if attrs.value(i) == "true":
                            group.setCheckable(True)
                self.currentGroup = group
            elif name == "Widget":
                widget = { QString("id")     : QString("0"),
                           QString("label")  : QString(""),
                           QString("type")   : QString("lineEdit"),
                           QString("default"): QString("") }
                for i in range(attrs.count()):
                    widget[attrs.localName(i)] = attrs.value(i)
                self.currentGroup.addWidget(widget)
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
