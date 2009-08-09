# -*- coding: utf-8 -*-
'''
manageR: Interface to the R statistical programming language

Copyright: (C) 2009 Carson J. Q. Farmer
Email: Carson.Farmer@gmail.com

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
from qgis.core import *
from qgis.gui import *

import resources

class manageRPlugin:
    def __init__( self, iface, version, ):
        # Save a reference to the QGIS iface
        self.iface = iface
        self.version = version
        
    def initGui( self ):
        # Create projection action
        self.action = QAction( QIcon( ":manager.png" ), "manageR", self.iface.mainWindow() )
        self.action.setWhatsThis( "Interface to the R statistical programming language" )
        self.action.setStatusTip( "Interface to the R statistical programming language" )
        QObject.connect( self.action, SIGNAL( "activated()" ), self.run )
        # Add to the main toolbar
        self.iface.addToolBarIcon( self.action )

    def unload( self ):
        # Remove the plugin
        self.iface.removeToolBarIcon( self.action )

    def run( self ):
        pixmap = QPixmap( ":splash.png" )
        splash = QSplashScreen(pixmap)
        splash.showMessage( "Checking for previously saved history and R environment", \
        (Qt.AlignBottom|Qt.AlignHCenter), Qt.white )
        splash.show()
        QApplication.processEvents()
        import manageRDialog
        splash.showMessage( "Setting up manageR GUI", \
        (Qt.AlignBottom|Qt.AlignHCenter), Qt.white )
        d = manageRDialog.manageR( self.iface, self.version )
        d.setWindowModality( Qt.NonModal )
        d.setModal( False )
        splash.showMessage( "manageR Ready!", \
        (Qt.AlignBottom|Qt.AlignHCenter), Qt.white )
        splash.finish( d )
        d.show()
