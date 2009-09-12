# -*- coding: utf-8 -*-
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from PyQt4.QtSql import *
from qgis.core import *
import os
from xml.dom import minidom

from GenericVerticalUI import GenericVerticalUI

class PluginManager: 
    def __init__(self, parent):#, iface):
        ## Save reference to the QGIS interface
        #self.iface = iface
        self.tools="/home/cfarmer/.qgis/python/plugins/manageR/tools.xml"
        self.parent = parent

    def makeCaller(self, n):
        return lambda: self.run(n)
    
    def createActions(self):  
        self.actionlist=[] #list of actions
        self.callerlist=[] #list of funcions to call run() with id parameter
        pluginsMenu = self.parent.menuBar().addMenu("&Plugins")
        
        #starting xml file reading
        if not self.tools is None:
            xmlfile=open(self.tools)
            dom=minidom.parse(xmlfile)
            tool=dom.firstChild.firstChild
            
            #loads every tool in the file
            while tool: 
                name= tool.getAttribute("name")
                # Create action that will start plugin configuration
                self.actionlist.append(QAction(QIcon("mActionPluginAction"), name, self.parent))
                #create a new funcion that calls run() with the id parameter
                self.callerlist.append(self.makeCaller(len(self.actionlist)-1)) 
                # connect the action to the run method
                QObject.connect(self.actionlist[-1], SIGNAL("activated()"), self.callerlist[-1]) 
                # Add toolbar button and menu item
                self.parent.addActions(pluginsMenu, (self.actionlist[-1],))
                tool=tool.nextSibling
            xmlfile.close()

    def runCommand(self, command):
        mime = QMimeData()
        mime.setText(command)
        self.parent.editor.moveToEnd()
        self.parent.editor.cursor.movePosition(
        QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        self.parent.editor.cursor.removeSelectedText()
        self.parent.editor.cursor.insertText(
        self.parent.editor.currentPrompt)
        self.parent.editor.insertFromMimeData(mime)
        self.parent.editor.entered()
    
    def start(self):
        #reads the info in the widgets and calls the sql command
        command = self.command
        for i,item in enumerate(self.dlg.ui.widgets):
            if type(item)==type(QTextEdit()):
                text=str(item.toPlainText())
            elif type(item)==type(QLineEdit()):
                text=str(item.text())
            elif type(item)==type(QDoubleSpinBox()):
                text=str(item.value())
            elif type(item)==type(QComboBox()):
                text=str(item.currentText())
            else:
                text="Error loading widget."
            command = command.replace("["+str(i+1)+"]",text)
        self.runCommand(command)

    def getTool(self,toolid):
        """Reads the xml file looking for the tool with toolid 
        and returns it's commands and the parameters double list."""
        xmlfile=open(self.tools)
        dom=minidom.parse(xmlfile)
        tool=dom.firstChild.firstChild
        for i in range(0, toolid):
            tool=tool.nextSibling
        query=tool.getAttribute("query")
        name= tool.getAttribute("name")
        lines=[]
        parm=tool.firstChild
        while parm:
            lines.append(
            [parm.attributes.getNamedItem("label").value,
            parm.attributes.getNamedItem("type").value,
            parm.attributes.getNamedItem("default").value,
            parm.attributes.getNamedItem("notnull").value])
            parm=parm.nextSibling
        xmlfile.close()
        return name, query, lines

    # run method that performs all the real work
    def run(self, actionid): 
        #reads the xml file
        name, self.command, parameters= self.getTool(actionid)
        # create and show the dialog 
        self.dlg = PluginsDialog(parameters) 
        self.dlg.setWindowTitle(name)
        #connect the slots
        QObject.connect(self.dlg.ui.buttonBox, SIGNAL("accepted()"), self.start)
        # show the dialog
        self.dlg.show()
        result = self.dlg.exec_() 
        # See if OK was pressed
        if result == 1: 
            # do something useful (delete the line containing pass and
            # substitute with your code
            print "ok pressed"
            
class PluginsDialog(QDialog):
    def __init__(self, interface): 
        QDialog.__init__(self) 
        self.ui = GenericVerticalUI()
        self.ui.setupUi(self, interface)
