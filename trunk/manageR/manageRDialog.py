from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from QConsole import QConsole
from QLayerConverter import QVectorLayerConverter, QRasterLayerConverter
from RLayerConverter import RVectorLayerConverter
from RLayerWriter import RVectorLayerWriter, RRasterLayerWriter

try:
  import rpy2.robjects as robjects
#  import rpy2.rinterface as rinterface
except ImportError:
  QMessageBox.warning( None , "manageR", "Unable to load manageR: Required package rpy2 was unable to load"
  + "\nPlease ensure that both R, and the corresponding version of Rpy are correctly installed.")

class manageR( QDialog ):
  VECTOR = 0
  RASTER = 1
  
  def __init__( self, iface, version ):
    QDialog.__init__ ( self )
    # initialise variables
    self.iface = iface
    self.mapCanvas = self.iface.mapCanvas()
    self.version = version
    # adjust user interface
    self.setSizeGripEnabled( True )
    self.setWindowTitle( 'manageR' )
    self.setWindowIcon( QIcon( ":manager.png" ) )
    self.setWindowFlags( Qt.Window )
    self.wgt_console = QConsole( self, self.runCommand )
    self.wgt_console.append( self.welcomeString() )
    self.wgt_console.append( "" )
    self.wgt_console.displayPrompt()
    gbox = QGridLayout()
    gbox.addWidget( self.wgt_console )
    self.setLayout( gbox )
    self.setGeometry( 100, 100, 550, 400 )
    self.startTimer( 50 )
    # create the required connections
    
  def timerEvent( self, e ):
    robjects.rinterface.process_revents()

  def helpDialog( self ):
    message = QString( "<center><h2>manageR " + self.version + "</h2>" )
    message.append( "<h3>Interface to the R statistical analysis program</h3>" )
    message.append( "<h4>Copyright (C) 2009 Carson J.Q. Farmer" )
    message.append( "<br/>carson.farmer@gmail.com" )
    message.append( "<br/><a href='http://www.ftools.ca/manageR.html'>www.ftools.ca/manageR.html</a>" )
    message.append( "<br/></h4></center>" )
    message.append( "<h4>Description:</h4>" )
    message.append( "manageR adds comprehensive statstical capabilities to Quantum GIS by loosely coupling QGIS with the R statistical programming environment." )
    message.append( "<h4>Usage:</h4>" )
    message.append( "<tt>Ctrl+L</tt><br/>" )
    message.append( "<tt>Ctrl+T</tt><br/>" )
    message.append( "<tt>Ctrl+M</tt><br/>" )
    message.append( "<tt>Ctrl+F</tt><br/>" )
    message.append( "<tt>Shift+Return</tt>" )
    message.append( "<h4>Details:</h4>" )
    message.append( "Use <tt>Ctrl+L</tt> to import the currently selected layer in the QGIS layer list into the manageR R environment. To limit the import to the attribute table of the selected layer, use <tt>Ctrl+T</tt>. Exporting R layers from the manageR R environment is done via <tt>Ctrl-M</tt> and <tt>Ctrl-F</tt>, where M signifies exporting to the map canvas, and F signifies exporting to file. To enter multiline R commands, use the <tt>Shift</tt> modifier when entering <tt>Return</tt> to signify continuation of command on the following line." )
    message.append( "<h4>Features:</h4>" )
    message.append( "<ul><li>Perform complex statistical analysis functions on raster, vector and spatial database formats</li>" )
    message.append( "<li>Use the R statistical environment to graph, plot, and map spatial and aspatial data from within QGIS</li>" )
    message.append( "<li>Export R (sp) vector layers directly to QGIS map canvas as QGIS vector layers</li>" )
    message.append( "<li>Perform all available R commands from within QGIS, including multi-line commands</li>" )
    message.append( "<li>Read QGIS vector layers directly from map canvas as R (sp) vector layers, allowing analysis to be carried out on any vector format supported by QGIS</li></ul>" )
    message.append( "<h4>References:</h4>" )
    message.append( "<ul><li><a href='http://www.r-project.org/'>The R Project for Statistical Computing</a></li>" )
    message.append( "<li><a href='http://rpy.sourceforge.net/'>RPy: A simple and efficient access to R from Python</a></li>" )
    message.append( "<li><a href='http://cran.r-project.org/web/packages/rgdal/index.html'>rgdal: Bindings for the Geospatial Data Abstraction Library</a></li>" )
    message.append( "<li><a href='http://cran.r-project.org/web/packages/sp/index.html'>sp: Classes and methods for spatial data</a></li>" )
    message.append( "<li><a href='http://r-spatial.sourceforge.net/'>Spatial data in R</a></li></ul>" )
    dialog = QDialog( self )
    about = QTextBrowser( dialog )
    about.setHtml( message )
    about.setOpenLinks( False )
    about.setReadOnly( True )
    self.connect( about, SIGNAL("anchorClicked(QUrl)"), self.launchBrowser )
    about.setHtml( message )
    vbox = QVBoxLayout()
    vbox.addWidget( about )
    dialog.setLayout( vbox )
    dialog.setWindowTitle( 'manageR Help' )
    dialog.setGeometry(200,200,400,400)
    dialog.exec_()
    
  def launchBrowser( self, url ):
    QDesktopServices.openUrl( url )
    
  def welcomeString( self ):    text = QString()
    text.append( "Welcome to manageR " + self.version + "\n")
    text.append( "QGIS interface to the R statistical analysis program\n" )
    text.append( "Copyright (C) 2009  Carson Farmer\n" )
    text.append( "Licensed under the terms of GNU GPL 2\nmanageR is free software; you can redistribute it " )
    text.append( "and/or modify it under the terms of " )
    text.append( "the GNU General Public License as published by the Free Software Foundation; either " )
    text.append( "version 2 of the License, or (at your option) any later version.\n" )
    text.append( "Currently running " + unicode( robjects.r.version[ 12 ][ 0 ] ) + "\n\n" )
    text.append( "Use Ctrl+H for manageR information and help")
    return text


  def keyPressEvent( self, e ):
    '''
    Reimplemented key press event:
    Used to import spatial data into R
    CTRL-L to load the selected vector layer
    CTRL-T to load the selected layer's attribute table only
    CTRL-M to export an R layer to the map canvas
    CTRL-F to export an R layer to file
    '''
    if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_L:
      mlayer = self.mapCanvas.currentLayer()
      self.importRObjects( mlayer, False )
    elif e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_T:
      mlayer = self.mapCanvas.currentLayer()
      self.importRObjects( mlayer, True )
    elif e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_M:
      self.exportRObjects( False )
    elif e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_F:
      self.exportRObjects( True )
    elif e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_H:
      self.helpDialog()
    else:
      QDialog.keyPressEvent( self, e )

  def runCommand( console, text ):
    if ( text.startsWith( 'quit(' ) or text.startsWith( 'q(' ) ) and text.count( ")" ) == 1:
      return False, "System exit not allowed"
    success = True
    out_text = QString()
    rbuf = QString()
    def f( x ):
      rbuf.append( x )
    robjects.rinterface.setWriteConsole(f)
    try:
      r_code = "withVisible( " + unicode( text ) + " )"
      output = robjects.r( r_code )
      visible = output.r["visible"][0][0]
      out_text.append( rbuf )
      if visible:
        out_text.append( unicode( output.r["value"][0] ) )
    except robjects.rinterface.RRuntimeError, rre:
      out_text = QString( str(rre) )
      success = False
    return success, out_text

  def closeEvent( self, e ):
    ask_save = QMessageBox.question( self, "manageR", "Save workspace image?", 
    QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel )
    if ask_save == QMessageBox.Cancel:
      e.ignore()
    else:
      if ask_save == QMessageBox.Yes:
        robjects.r( 'save.image(file=".Rdata")' )
      robjects.r( 'rm(list=ls(all=T))' )
      robjects.r( 'gc()' )
      robjects.r( 'graphics.off()' )
      e.accept()

# This is used whenever we check for sp objects in manageR
  def updateRObjects( self ):
    ls_ = robjects.r[ 'ls' ]
    class_ = robjects.r[ 'class' ]
    layers = {}
    for item in ls_():
      check = class_( robjects.r( item ) )[ 0 ]
      if check == "SpatialPointsDataFrame" or check == "SpatialPolygonsDataFrame" or check == "SpatialLinesDataFrame":
        layers[ unicode( item ) ] = manageR.VECTOR
      elif check == "SpatialGridDataFrame" or check == "SpatialPixelsDataFrame":
        layers[ unicode( item ) ] = manageR.RASTER
    return layers

  def isPackageLoaded( self, package="sp" ):
    '''
    Check that the input package is loaded into R, 
    Return: True if it is loaded, False otherwise
    '''
    require_ = robjects.r[ 'require' ]
    return require_( package )[ 0 ]
  
  def importRObjects( self, mlayer, data_only ):
    '''
    Converts a QgsVectorLayer to an R Spatial*DataFrame, or
    a simple DataFrame if no spatial data is requested
    Provides the ability to load any vector layer that QGIS
    supports into R. Only selected features will be imported into R
    '''
    self.wgt_console.cursor.select( QTextCursor.LineUnderCursor )
    self.wgt_console.cursor.removeSelectedText()
    self.wgt_console.cursor.insertText( self.wgt_console.prompt + "Importing data from canvas..." )
    if mlayer is None:
      self.wgt_console.appendText( "No layer selected in layer list", QConsole.ERR_TYPE )
      self.wgt_console.displayPrompt()
      return
    rbuf = QString()
    def f( x ):
      rbuf.append( x )
    robjects.rinterface.setWriteConsole(f)
    if not data_only and not self.isPackageLoaded( "sp" ):
      self.wgt_console.appendText( "Unable to find R package 'sp'.\n "
      + "\n Please manually install the 'sp' package in R via "
      + "install.packages().", QConsole.ERR_TYPE )
      self.wgt_console.displayPrompt()
      return
    if mlayer.type() == QgsMapLayer.VectorLayer:
      self.r_layer_creator = QVectorLayerConverter( mlayer, data_only )
    if mlayer.type() == QgsMapLayer.RasterLayer:
      if data_only:
        self.wgt_console.appendText( "Cannot load raster layer attributes", QConsole.ERR_TYPE )
        self.wgt_console.displayPrompt()
        return
      if not self.isPackageLoaded( "rgdal" ):
        self.wgt_console.appendText( "Unable to find R package 'rgdal'.\n "
        + "\n Please manually install the 'rgdal' package in R via "
        + "install.packages().", QConsole.ERR_TYPE )
        self.wgt_console.displayPrompt()
        return
      self.r_layer_creator = QRasterLayerConverter( mlayer )
    self.wgt_console.appendText( rbuf, QConsole.OUT_TYPE )
    QObject.connect( self.r_layer_creator, SIGNAL( "threadError( PyQt_PyObject )" ),
    self._showErrors )
    QObject.connect( self.r_layer_creator, SIGNAL( "threadSuccess( PyQt_PyObject, PyQt_PyObject, PyQt_PyObject )" ),
    self._showImport )
    self.r_layer_creator.start()

  def exportRObjects( self, to_file ):
    '''
    Export R sp objects to file or mapcanvas
    Vector layers can be saved to file or mapcanvas, raster 
    layers can be saved to file only
    Saving to file uses the R gdal functions, saving to map 
    canvas is a native manageR implimentation
    '''
    self.wgt_console.cursor.select( QTextCursor.LineUnderCursor )
    self.wgt_console.cursor.removeSelectedText()
    if to_file:
      put_text = "to file..."
    else:
      put_text = "to canvas..."
    self.wgt_console.cursor.insertText( self.wgt_console.prompt + "Exporting layer " + put_text )
    result = self.exportRObjectsDialog( to_file )
    # If there is no input layer, don't do anything
    if result is None: # this needs to be updated to reflect where we  get the R objects from...
      self.wgt_console.appendText( "No R spatial objects available", QConsole.ERR_TYPE )
      self.wgt_console.displayPrompt()
      return
    if not result:
      return
    if not to_file and not self.isPackageLoaded( "sp" ):
      self.wgt_console.appendText( "Unable to find R package 'sp'.\n "
      + "\n Please manually install the 'sp' package in R via "
      + "install.packages().", QConsole.ERR_TYPE )
      self.wgt_console.displayPrompt()
      return
    if to_file and not self.isPackageLoaded( "rgdal" ):
      self.wgt_console.appendText( "Unable to find R package 'rgdal'.\n "
      + "\n Please manually install the 'rgdal' package in R via "
      + "install.packages().", QConsole.ERR_TYPE )
      self.wgt_console.displayPrompt()
      return
    if not self.export_type == manageR.VECTOR and not self.export_type == manageR.RASTER:
      self.wgt_console.appendText( "Unrecognized sp object, unable to save to file.", QConsole.ERR_TYPE )
      self.wgt_console.displayPrompt()
      return
    if not to_file and self.export_type == manageR.RASTER:
      self.wgt_console.appendText( "Unable to export raster layers to map canvas at this time.", QConsole.ERR_TYPE )
      self.wgt_console.displayPrompt()
      return
    self.wgt_console.cursor.select( QTextCursor.LineUnderCursor )
    self.wgt_console.cursor.removeSelectedText()
    self.wgt_console.cursor.insertText( self.wgt_console.prompt + "Exporting data from: " + str( self.export_layer ) )
    if not to_file:
      if self.export_type == manageR.VECTOR:
        self.q_layer_creator = RVectorLayerConverter( robjects.r[ str( self.export_layer ) ], self.export_layer )
    else:
      if self.export_type == manageR.VECTOR:
         drivers = "ESRI Shapefile (*.shp);;MapInfo File (*.mif);;GML (*.gml);;KML (*.kml)"
      else:
        drivers = "GeoTIFF (*.tif);;Erdas Imagine Images (*.img);;Arc/Info ASCII Grid " \
        + "(*.asc);;ENVI Header Labelled (*.hdr);;JPEG-2000 part 1 (*.jp2);;Portable " \
        + "Network Graphics (*.png);;USGS Optional ASCII DEM (*.dem)"
      fileDialog = QFileDialog()
      fileDialog.setConfirmOverwrite( True )
      driver = QString()      layer_name = fileDialog.getSaveFileName( self, "Save OGR",".", drivers, driver )
      if not layer_name.isEmpty():
          fileCheck = QFile( layer_name )
          if fileCheck.exists():
            if not QgsVectorFileWriter.deleteShapeFile( layer_name ):
              self.wgt_console.appendText( "Unable to overwrite existing file", QConsole.ERR_TYPE )
              self.wgt_console.displayPrompt()
              return
      if self.export_type == manageR.VECTOR:
        self.q_layer_creator = RVectorLayerWriter( str( self.export_layer ), layer_name, driver )
      else:
        self.q_layer_creator = RRasterLayerWriter( str( self.export_layer ), layer_name, driver )
    QObject.connect( self.q_layer_creator, SIGNAL( "threadError( PyQt_PyObject )" ),
    self._showErrors )
    QObject.connect( self.q_layer_creator, SIGNAL( "threadSuccess( PyQt_PyObject, PyQt_PyObject )" ),
    self._showExport )
    self.q_layer_creator.start()

  def _showExport( self, layer, to_file ):
    self.q_layer_creator.stop()
    add = False
    if to_file:
      message = "Created file:\n" + unicode( layer.source() )
      add = QMessageBox.question( self, "manageR", "Would you like to add the new layer to the map canvas?",
      QMessageBox.Yes, QMessageBox.No, QMessageBox.NoButton )
    else:
      message = unicode( layer.name() ) + " exported to canvas"
    if add == QMessageBox.Yes or not to_file:
      QgsMapLayerRegistry.instance().addMapLayer( layer )
    self.wgt_console.appendText( message, QConsole.OUT_TYPE )
    self.wgt_console.displayPrompt()

  def _showImport( self, rlayer, layer_name, message ):
    self.r_layer_creator.stop()
    del self.r_layer_creator
    robjects.globalEnv[ str( layer_name ) ] = rlayer
    self.updateRObjects()
    self.wgt_console.appendText( message, QConsole.OUT_TYPE )
    self.wgt_console.displayPrompt()
      
  def _showErrors( self, message ):
    try:
      self.r_layer_creator.stop()
      del self.r_layer_creator
    except:
      pass
    try:
      self.q_layer_creator.stop()
    except:
      pass
    self.wgt_console.appendText( message, QConsole.ERR_TYPE )
    
  def exportRObjectsDialog( self, to_file ):
    self.export_layer = None
    self.export_type = None
    dialog = QDialog( self )
    layers = QComboBox( dialog )
    buttons = QDialogButtonBox( QDialogButtonBox.Ok|QDialogButtonBox.Cancel, 
    Qt.Horizontal, dialog )
    dialog.connect( buttons, SIGNAL( "rejected()" ), dialog.reject )
    dialog.connect( buttons, SIGNAL( "accepted()" ), dialog.accept )
    r_layers = self.updateRObjects()
    if not len( r_layers ) > 0:
      return None
    for layer in r_layers.keys():
      if r_layers[ layer ] == manageR.VECTOR or r_layers[ layer ] == manageR.RASTER:
        layers.addItem( unicode( layer ) )
    vbox = QVBoxLayout()
    vbox.addWidget( layers )
    vbox.addWidget( buttons )
    dialog.setLayout( vbox )
    dialog.setWindowTitle( 'Export R Layer' )
    if not dialog.exec_() == QDialog.Accepted:
		  return False
    self.export_layer = layers.currentText()
    self.export_type = r_layers[ unicode( self.export_layer ) ]
    return True
