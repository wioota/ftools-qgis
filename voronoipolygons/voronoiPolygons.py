from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import doVoronoiPolygons
import resources

class voronoiPolygonsPlugin:
	def __init__( self, iface ):
		# Save a reference to the QGIS iface
		self.iface = iface

	def initGui( self ):
		# Create projection action
		self.action = QAction(QIcon( ":/voronoipolygons.png" ), "Voronoi/Thiessen tesselation", self.iface.mainWindow() )
		self.action.setWhatsThis( "Tool for generating a voronoi tessellation from a point layer" )
		QObject.connect( self.action, SIGNAL( "activated()" ), self.activate )
		# Create about button
		self.helpaction = QAction( QIcon( ":/voronoipolygonshelp.png" ), "About", self.iface.mainWindow() )
		self.helpaction.setWhatsThis( "Help for Voronoi/Thiessen tesselation" )
		QObject.connect( self.helpaction, SIGNAL( "activated()" ), self.helprun )

		# Add to the main toolbar
		self.iface.addToolBarIcon( self.action )
		self.iface.addPluginToMenu( "&Voronoi/Thiessen tesselation", self.action )
		self.iface.addPluginToMenu( "&Voronoi/Thiessen tesselation", self.helpaction )

	def unload( self ):
		self.iface.removePluginMenu( "&Voronoi/Thiessen tesselation", self.action )
		self.iface.removePluginMenu( "&Voronoi/Thiessen tesselation", self.helpaction )
		self.iface.removeToolBarIcon( self.action )

	def helprun( self ):
		infoString = QString( "Written by Carson Farmer\ncarson.farmer@gmail.com\n" )
		infoString = infoString.append( "http://www.ftools.ca/\n\n" )
		infoString = infoString.append( "This tool generates a voronoi tessellation from a point layer, " )
		infoString = infoString.append( "and exports it as a polygon shapefile." )
		QMessageBox.information( self.iface.mainWindow(), "About Voronoi/Thiessen tesselation", infoString )

	def activate( self ):
		d = doVoronoiPolygons.Dialog( self.iface )
		d.exec_()
