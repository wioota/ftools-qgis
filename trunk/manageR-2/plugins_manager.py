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
                            RadioGroupBox, GroupBox, RadioGroupBox, VBoxLayout, 
                            HBoxLayout)
CURRENTDIR = unicode(os.path.abspath(os.path.dirname(__file__)))

class ToolsCollection:
    def __init__(self, category="__default__"):
        self.__tools__ = []
        self.__category__ = QString(category)
        
    def addTool(self, tool):
        if isinstance(tool, Tool):
            self.__tools__.append(tool)
        else:
            raise Exception("Error: Expected type Tool")
            
    def tools(self):
        return self.__tools__
        
    def setCategory(self, category):
        if isinstance(category, QString):
            self.__category__ = category
        else:
            raise Exception("Error: Expected type QString")

    def category(self):
        return self.__category__
        
    def currentTool(self):
        return self.__tools__[-1]

class Tool:
    def __init__(self, name="__default__", query=None,
                       help=None, icon=None, dialog=None):
        self.__query__ = None
        self.__help__ = None
        if dialog is None:
            self.__dialog__ = Dialog()
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

    def setDialog(self, dialog):
        if not isinstance(dialog, Dialog):
            raise TypeError("Error: Expected type list")
        self.__dialog__ = dialog
        
    def dialog(self):
        return self.__dialog__
        
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

class Dialog:
    def __init__(self):
        self.__pages__ = []

    def pages(self):
        return self.__pages__
        
    def addPage(self, page):
        self.__pages__.append(page)
        
    def insertPage(self, index, page):
        self.__pages__.insert(index, page)

class Page:
    def __init__(self, name="__default__", parent=None):
        self.__name__ = name
        self.__items__ = []
        self.__parent__ = parent
        
    def parent(self):
        return self.__parent__
        
    def name(self):
        return self.__name__

    def items(self):
        return self.__items__
        
    def addItem(self, item):
        self.__items__.append(item)
        
class Group:
    def __init__(self, name="__default__", checkable=False, parent=None):
        self.__name__ = name
        self.__parent__ = parent
        self.__checkable__ = checkable
        self.__id__ = 0
        self.__items__ = []
        
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
        
    def addItem(self, item):
        self.__items__.append(item)
        
    def items(self):
        return self.__items__
        
class Layout:
    ROWS, COLUMNS = range(2)
    def __init__(self, type=0, parent=None):
        self.__items__ = []
        self.__parent__ = parent
#        if not parent is None:
#            self.__id__ = parent.id()+1
#        else:
#            self.__id__ = 0
        self.__type__ = type
        
    def setType(self, type):
        if type in range(2):
            self.__type__ = type
            
    def type(self):
        return self.__type__

#    def id(self):
#        return self.__id__
        
    def parent(self):
        return self.__parent__
        
    def addItem(self, item):
        self.__items__.append(item)
        
    def items(self):
        return self.__items__
        
class Widget:
    def __init__(self, attibutes={}):
        self.__attributes__ = attributes
        
    def attributes(self):
        return self.__attributes__
        
    def setAttributes(self, attributes):
        if isinstance(attributes, dict):
            self.__attributes__ = attributes
        else:
            raise Exception("Error: Expected type dict")

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
        self.structure = []
        errors = False
        for file in self.files:
            tmp = QFile(file.absoluteFilePath())
            source = QXmlInputSource(tmp)
            ok = reader.parse(source)
            if not ok:
                errors = True
            else:
                self.structure.append(handler.documentStructure())

    def createPlugins(self):
        for collection in self.structure:
            main = self.parent().menuBar()
            menu = None
            # check to see if we already have a menu by this name
            for child in main.findChildren(QMenu):
                title = child.title()
                title.remove("&")
                if title.trimmed() == collection.category().trimmed():
                    menu = child
                    break
            if menu is None:
                menu = main.addMenu(collection.category())
            for tool in collection.tools():
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
        gui = tool.dialog()
        for page in gui.pages():
            dialog.addPage(page.name())
            for item in page.items():
                dialog.addItem(self.recursiveGuiBuilder(item))
        self.connect(dialog, SIGNAL("pluginOutput(PyQt_PyObject)"), self.runCommand)
        self.connect(dialog, SIGNAL("helpRequested()"), self.runHelp)
        dialog.show()
        
    def recursiveGuiBuilder(self, item):
        if not isinstance(item, Widget):
            widget = self.createGuiItem(item)
            for i in item.items():
                widget.addItem(self.recursiveGuiBuilder(i))
        else:
            widget = self.createGuiItem(item)
        return widget

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

    def createGuiItem(self, item):
        if isinstance(item, Layout):
            if item.type() == Layout.COLUMNS:
                return HBoxLayout()
            else:
                return VBoxLayout()
        elif isinstance(item, Group):
            if item.isCheckable():
                return GroupCheckBox(id=item.id(), title=item.name())
            else:
                return GroupBox(title=item.name())
        elif isinstance(item, Widget):
            attributes = item.attributes()
            type = attribtues["type"]
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
                return widget
            except KeyError, e:
                QMessageBox.warning(self.parent(), "manageR - Plugin Error",
                "Widget missing required field in plugin XML file:\n"
                +str(e))
                return

class Handler(QXmlDefaultHandler):
    def __init__(self):
        QXmlDefaultHandler.__init__(self)
        self.collection = ToolsCollection()
        self.currentItem = None

    def fatalError(self, err):
        QMessageBox.warning(None, "manageR - XML Parsing Error",
            "Error encountered when building '%s' tool!\n" % self.collection.currentTool().name()
            + "There was a problem with the XML file for "
            + "the '%s' category:\n" % self.collection.category()
            + "    Fatal error on line %s" % err.lineNumber()
            + ", column %s (%s)\n" % (err.columnNumber(), err.message())
            + "Some plugin tools and menus have been ignored.")
        return False

#    def startDocument(self):
#        self.inTool = False
#        self.inQuery = False
#        self.inPage = False
#        self.inGroup = False
#        self.inColumn = False
#        self.inRow = False
#        self.currentGroup = Group()
#        self.currentColumn = Column()
#        self.currentPage = Page()
#        self.currentColumn.addGroup(self.currentGroup)
#        self.currentPage.addColumn(self.currentColumn)
#        self.currentTool = Tool()
#        self.currentTool.gui().append(self.currentPage)
#        self.currentCat = QString("Plugins")
#        return True

    def documentStructure(self):
        return self.collection

    def endElement(self, str1, str2, name):
        if name == "RTool":
            self.inTool = False
        elif name == "Dialog":
            self.inDialog = False
        elif name == "Query":
            self.inQuery = False
        elif name == "Page":
            self.inPage = False
        elif name  in ("Group", "Columns", "Rows"):
            self.currentItem = self.currentItem.parent()
        return True

    def characters(self, chars):
        if self.inQuery:
            self.collection.currentTool().setQuery(chars)
        return True

    def startElement(self, str1, str2, name, attrs):
        if name == "manageRTools":
            self.collection = ToolsCollection()
            for i in range(attrs.count()):
                if attrs.localName(i) == "category" and not attrs.value(i).isEmpty():
                    self.collection.setCategory(attrs.value(i))
                    break
            self.inTool = False
            self.inQuery = False
            self.currentItem = None
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
            self.collection.addTool(tool)
            self.inDialog = False
            self.inQuery = False
            self.currentItem = None
        elif self.inTool:
            if name == "Help":
                for i in range(attrs.count()):
                    if attrs.localName(i) == "name" and not attrs.value(i).isEmpty():
                        self.collection.currentTool().setHelp(attrs.value(i))
                        break
                self.currentItem = None
            elif name == "Query":
                if self.inQuery:
                    raise Exception("Error: Nested queries not allowed")
                self.inQuery = True
                self.currentItem = None
            elif name == "Dialog":
                if self.inDialog:
                    raise Exception("Error: Nested dialogs not allowed")
                self.inDialog = True
                self.collection.currentTool().setDialog(Dialog())
                self.inPage = True
                page = Page()
                self.collection.currentTool().dialog().addPage(page)
                self.currentItem = page
            elif self.inDialog:
                if name == "Page":
                    if self.inPage:
                        raise Exception("Error: Nested pages not allowed")
                    self.inPage = True
                    for i in range(attrs.count()):
                        if attrs.localName(i) == "name" and not attrs.value(i).isEmpty():
                            page = Page(attrs.value(i), self.currentItem)
                            self.collection.currentTool().dialog().addPage(page)
                            break
                    self.currentItem = page
                elif name == "Columns":
                    item = Layout(type=Layout.COLUMNS, parent=self.currentItem)
                    self.currentItem.addItem(item)
                    self.currentItem = item
                elif name == "Rows":
                    item = Layout(type=Layout.ROWS, parent=self.currentItem)
                    self.currentItem.addItem(item)
                    self.currentItem = item
                elif name == "Group":
                    item = Group(parent=self.currentItem)
                    for i in range(attrs.count()):
                        if attrs.localName(i) == "name" and not attrs.value(i).isEmpty():
                            item.setName(attrs.value(i))
                        if attrs.localName(i) == "id" and not attrs.value(i).isEmpty():
                            item.setId(attrs.value(i))
                        if attrs.localName(i) == "checkable" and not attrs.value(i).isEmpty():
                            if attrs.value(i) == "true":
                                item.setCheckable(True)
                    self.currentItem.addItem(item)
                    self.currentItem = item
                elif name == "Widget":
                    item = { QString("id")     : QString("0"),
                               QString("label")  : QString(""),
                               QString("type")   : QString("lineEdit"),
                               QString("default"): QString("") }
                    for i in range(attrs.count()):
                        item[attrs.localName(i)] = attrs.value(i)
                    self.currentItem.addItem(item)
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
