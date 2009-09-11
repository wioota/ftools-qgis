# -*- coding: utf-8 -*-
'''
This file is part of manageR

Copyright (C) 2009 Carson J. Q. Farmer

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public Licence as published by the Free Software
Foundation; either version 2 of the Licence, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public Licence for more 
details.

You should have received a copy of the GNU General Public Licence along with
this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
Street, Fifth Floor, Boston, MA  02110-1301, USA
'''

from PyQt4.QtCore import *
from PyQt4.QtGui import *
#from qgis.core import *
from qgis.gui import *
import resources

class Plugin:
    def __init__(self, iface, version):
        self.iface = iface
        self.version = version
        
    def initGui(self):
        self.action = QAction(QIcon( ":mActionIcon.png" ), "manageR", self.iface.mainWindow())
        self.action.setWhatsThis("Interface to the R statistical programming language")
        self.action.setStatusTip("Interface to the R statistical programming language")
        QObject.connect(self.action, SIGNAL("activated()"), self.run)
        # Add to the main toolbar
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        from manageR import MainWindow, loadConfig, saveConfig
        loadConfig()
        if not MainWindow.Instances:
            MainWindow(self.iface, self.version,isConsole=True).show()