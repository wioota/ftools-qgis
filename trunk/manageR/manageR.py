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
        import manageRDialog
        d = manageRDialog.manageR( self.iface, self.version )
        d.setWindowModality( Qt.NonModal )
        d.setModal( False )
        d.show()

