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
from qgis.core import *

from QConsole import QConsole
from QScripting import QScripting
from QFinder import QFinder
from QLayerConverter import QVectorLayerConverter, QRasterLayerConverter
from RLayerConverter import RVectorLayerConverter
from RLayerWriter import RVectorLayerWriter, RRasterLayerWriter
from highlighter import ConsoleHighlighter, ScriptHighlighter
from completer import CommandCompletion

try:
  import rpy2.robjects as robjects
#  import rpy2.rinterface as rinterface
except ImportError:
  QMessageBox.warning( None , "manageR", "Unable to load manageR: Required package rpy2 was unable to load"
  + "\nPlease ensure that both R, and the corresponding version of Rpy are correctly installed.")

import ConfigParser
import os.path
parser = ConfigParser.ConfigParser()
here = os.path.join( os.path.dirname( __file__ ),"config.ini" )
parser.read( here )

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
    theme = parser.get('general','theme')
    self.setupUserInterface( theme )
    autocomplete = parser.get('general', 'auto_completion')
    delay = int( parser.get('general', 'delay') )
    if not autocomplete == "None":
      completer_console = CommandCompletion( self.console, self.getDefaultCommands(), delay, self.label )
      if QFile( os.path.join( os.path.dirname( __file__ ), autocomplete ) ).exists():
        completer_console.loadSuggestions( os.path.join( os.path.dirname( __file__ ), autocomplete ) )
      completer_script = CommandCompletion( self.scripttab.scripting, completer_console.suggestions(), delay, self.label )
        
    self.console.append( self.welcomeString() )
    self.console.append( "" )
    self.console.displayPrompt()
    self.console.setFocus( Qt.ActiveWindowFocusReason )
    self.connect( self.console, \
    SIGNAL( "executeCommand(PyQt_PyObject)" ), self.runCommand )
    self.startTimer( 50 )

  def setupUserInterface( self, theme ):
    self.setSizeGripEnabled( True )
    self.setWindowTitle( 'manageR' )
    self.setWindowIcon( QIcon( ":manager.png" ) )
    self.setWindowFlags( Qt.Window )
    self.label = QLabel()
    self.label.setText(" ")
    self.label.setWordWrap( True )
    self.finder = QFinder( self )
    self.tabs = QTabWidget( self )
    self.tabs.setTabPosition( QTabWidget.East )

    self.console = QConsole( self, self.runCommand )
    highlighter_1 = ConsoleHighlighter( self.console, theme )
    self.tabs.addTab( self.console, "Console" )

    self.scripttab = QScripting( self )
    highlighter_2 = ScriptHighlighter( self.scripttab.scripting, theme )
    self.tabs.addTab( self.scripttab, "Script" )
    gbox = QGridLayout( self )
    gbox.addWidget( self.tabs, 0, 0, 1, 2 )
    gbox.addWidget( self.label, 1, 0, 1, 1 )
    gbox.addWidget( self.finder, 1, 1, 1, 1 )
    self.resize( 600, 500 )

  def timerEvent( self, e ):
    try:
      robjects.rinterface.process_revents()
    except:
      pass

  def helpDialog( self ):
    message = QString( "<center><h2>manageR " + self.version + "</h2>" )
    message.append( "<h3>Interface to the R statistical programming environment</h3>" )
    message.append( "<h4>Copyright (C) 2009 Carson J.Q. Farmer" )
    message.append( "<br/>carson.farmer@gmail.com" )
    message.append( "<br/><a href='http://www.ftools.ca/manageR.html'>www.ftools.ca/manageR.html</a>" )
    message.append( "<br/></h4></center>" )
    message.append( "<h4>Description:</h4>" )
    message.append( "<b>manageR</b> adds comprehensive statistical capabilities to Quantum GIS by loosely coupling QGIS with the <b>R</b> statistical programming environment." )
    message.append( "<h4>Usage:</h4>" )
    message.append( "<ul><li><tt>Ctrl+L</tt> : Import selected <b>l</b>ayer</li>" )
    message.append( "<li><tt>Ctrl+T</tt> : Import attribute <b>t</b>able of selected layer</li>" )
    message.append( "<li><tt>Ctrl+M</tt> : Export R layer to <b>m</b>ap canvas</li>" )
    message.append( "<li><tt>Ctrl+D</tt> : Export R layer to <b>d</b>isk</li>")
    message.append( "<li><tt>Ctrl+R</tt> : Send (selected) commands from script window to <b>R</b> console</li>" )
    message.append( "<li><tt>Ctrl+F</tt> : Toggle the <b>f</b>ind (search) bar</li>" )
    message.append( "<li><tt>Ctrl+H</tt> : Display <b>h</b>elp dialog</li></ul>")
    message.append( "<h4>Details:</h4>" )
    message.append( "Use <tt>Ctrl+L</tt> to import the currently selected layer in the QGIS layer list into the <b>manageR</b> environment. To import only the attribute table of the selected layer, use <tt>Ctrl+T</tt>. Exporting <b>R</b> layers from the <b>manageR</b> environment is done via <tt>Ctrl-M</tt> and <tt>Ctrl-D</tt>, where M signifies exporting to the map canvas, and D signifies exporting to disk. Multi-line <b>R</b> commands will automatically be recognised by <b>manageR</b>, however, to manaully enter multi-line commands, use the <tt>Shift</tt> modifier when typing <tt>Return</tt> to signify continuation of command on the following line. <br/><br/>Use <tt>Ctrl+R</tt> to send commands from the script tab to the <b>R</b> console. If the script tab contains selected text, only this text will be sent to the <b>R</b> console, otherwise, all text is sent. The script tab also contains tools for creating, loading, and saving <b>R</b> scripts, as well as basic functionality such as undo, redo, cut, copy, and paste. These tools are also available via the standard keyboard shortcuts (e.g. <tt>Ctrl+C</tt> to copy text)<br/><br/><tt>Ctrl+F</tt> will toggle (show/hide) the 'find bar'. To search for the next occurrence of the text or phrase in the 'find bar', type <tt>Enter</tt> or click the '&gt;' button. Conversely, click the '&lt;' button to search backwards." )
    message.append( "<h4>Features:</h4>" )
    message.append( "<ul><li>Perform complex statistical analysis functions on raster, vector and spatial database formats</li>" )
    message.append( "<li>Use the R statistical environment to graph, plot, and map spatial and aspatial data from within QGIS</li>" )
    message.append( "<li>Export R (sp) vector layers directly to QGIS map canvas as QGIS vector layers</li>" )
    message.append( "<li>Read QGIS vector layers directly from map canvas as R (sp) vector layers, allowing analysis to be carried out on any vector format supported by QGIS</li>" )
    message.append( "<li>Perform all available R commands from within QGIS, including multi-line commands</li>" )
    message.append( "<li>Visualise R commands clearly and cleanly using any one of the four included syntax highlighting themes</li>" )
    message.append( "<li>Create, edit, and save R scripts for complex statistical and computational operations</li></ul>" )
    message.append( "<h4>Notes:</h4>" )
    message.append( "<ul><li>The usual <b>R</b> commands to quit will not work in the <b>manageR</b> console, instead please close the <b>manageR</b> dialog manually.</li>" )
    message.append( "<li>To change the dialog colour theme, alter the 'theme' variable in the config.ini file in the <b>manageR</b> directory located here: " )
    message.append( "<tt>" + here + "</tt>.</li></ul>" )
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
    dialog.resize( 600,500 )
    dialog.setWindowModality( Qt.NonModal )
    dialog.setModal( False )
    dialog.show()

  def launchBrowser( self, url ):
    QDesktopServices.openUrl( url )
    
  def welcomeString( self ):
    text = QString()
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
    CTRL-Tab to switch between tabs
    '''
    if ( e.modifiers() == Qt.ControlModifier or e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_L:
      mlayer = self.mapCanvas.currentLayer()
      self.importRObjects( mlayer, False )
    elif ( e.modifiers() == Qt.ControlModifier or e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_T:
      mlayer = self.mapCanvas.currentLayer()
      self.importRObjects( mlayer, True )
    elif ( e.modifiers() == Qt.ControlModifier or e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_M:
      self.exportRObjects( False )
    elif ( e.modifiers() == Qt.ControlModifier or e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_D:
      self.exportRObjects( True )
    elif ( e.modifiers() == Qt.ControlModifier or e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_H:
      self.helpDialog()
    elif ( e.modifiers() == Qt.ControlModifier or e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_R:
      self.scripttab.parseCommands()
    elif ( e.modifiers() == Qt.ControlModifier or e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_F:
      self.finder.toggle()
    elif ( e.modifiers() == Qt.ControlModifier or e.modifiers() == Qt.MetaModifier ) and \
    ( e.key() == Qt.Key_PageUp or e.key() == Qt.Key_PageDown ):
      current = self.tabs.currentIndex()
      if e.key() == Qt.Key_PageUp:
        if current < self.tabs.count() - 1:
          self.tabs.setCurrentIndex( current + 1 )
        else:
          self.tabs.setCurrentIndex( 0 )
      elif e.key() == Qt.Key_PageDown:
        if current > 0:
          self.tabs.setCurrentIndex( current - 1 )
        else:
          self.tabs.setCurrentIndex( self.tabs.count() - 1 )
    else:
      QDialog.keyPressEvent( self, e )

  def runCommand( self, text ):
    self.console.enableHighlighting( False )
    self.label.setText("Running...")
    self.repaint()
    QApplication.processEvents()    
    highlighting = True
    sinking = False
    try:
      if ( text.startsWith( 'quit(' ) or text.startsWith( 'q(' ) ) \
      and text.count( ")" ) == 1:
        self.threadError( "System exit from manageR not allowed, close dialog manually" )
      else:
        output_text = QString()
        def write( output ):
          if not QString( output ).startsWith( "Error" ):
            output_text.append( unicode(output, 'utf-8') )
          if output_text.length() >= 50000 and output_text[ -1 ] == "\n":
            self.threadOutput( output_text )
            output_text.clear()
        robjects.rinterface.setWriteConsole( write )
        def read( prompt ):
          input = "\n"
          return input
        robjects.rinterface.setReadConsole( read )
        try:
          try_ = robjects.r[ "try" ]
          parse_ = robjects.r[ "parse" ]
          paste_ = robjects.r[ "paste" ]
          seq_along_ = robjects.r[ "seq_along" ]
          withVisible_ = robjects.r[ "withVisible" ]
          class_ = robjects.r[ "class" ]
          result =  try_(parse_(text=paste_(unicode(text))), silent=True)
          exprs = result
          result = None
          for i in list(seq_along_(exprs)):
            ei = exprs[i-1]
            try:
              result =  try_( withVisible_( ei ), silent=True )
            except robjects.rinterface.RRuntimeError, rre:
              self.threadError( str( rre ) )
            visible = result.r["visible"][0][0]
            if visible:
              if class_( result.r["value"][0] )[0] == "help_files_with_topic" or \
                class_( result.r["value"][0] )[0] == "hsearch":
                self.helpTopic( result.r["value"][0], class_( result.r["value"][0] )[0] )
              else:
                robjects.r['print'](result.r["value"][0])
        except robjects.rinterface.RRuntimeError, rre:
          print "error happened"
          # this fixes error output to look more like R's output
          self.threadError( "Error: " + str(rre).split(":")[1].strip() )
        if not output_text.isEmpty():
          self.threadOutput( output_text )
    except Exception, err:
      self.threadError( str( err ) )
    self.label.setText("Complete!")
    self.console.enableHighlighting( True )
    self.threadComplete()
 
  def helpTopic( self, topic, search ):
    if search == "hsearch":
      print "made it here"
      dialog = searchDialog( self, topic )
    else:
      dialog = helpDialog( self, topic )
    dialog.setWindowModality( Qt.NonModal )
    dialog.setModal( False )
    dialog.show()
    self.label.setText("Help dialog opened")
    self.console.enableHighlighting( True )
    return
   
  def threadError( self, error ):
    #self.thread.stop()
    self.console.appendText( error, QConsole.ERR_TYPE )
    self.repaint()
    #self.repaint()
      
  def threadOutput( self, output ):
    #self.console.appendText( output, QConsole.OUT_TYPE )
    self.console.appendText( unicode( output ), QConsole.OUT_TYPE )
    self.repaint()
    QApplication.processEvents()
      
  def threadComplete( self ):
    #self.thread.stop()
    self.label.setText(" ")
    self.console.switchPrompt()
    self.console.displayPrompt()

  def closeEvent( self, e ):
    ask_save = QMessageBox.question( self, "manageR", "Save workspace image?", 
    QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel )
    if ask_save == QMessageBox.Cancel:
      e.ignore()
    elif ask_save == QMessageBox.Yes:
      robjects.r( 'save.image(file=".Rdata")' )
      robjects.r( 'rm(list=ls(all=T))' )
      robjects.r( 'gc()' )
      try:
        robjects.r( 'graphics.off()' )
      except:
        try:
          for i in list(robjects.r('dev.list()')):
            robjects.r('dev.next()')
            robjects.r('dev.off()')
        except:
          pass
      e.accept()
    else:
      if self.scripttab.scripting.document().isModified():
        if self.scripttab.maybeSave():
          e.accept()
        else:
          e.ignore()


# This is used whenever we check for sp objects in manageR
  def updateRObjects( self ):
    #ls_ = robjects.r[ 'ls' ]
    ls_ = robjects.conversion.ri2py(robjects.rinterface.globalEnv.get('ls',wantFun=True))
    #class_ = robjects.r[ 'class' ]
    class_ = robjects.conversion.ri2py(robjects.rinterface.globalEnv.get('class',wantFun=True))
    layers = {}
    for item in ls_():
      check = class_( robjects.r[ item ] )[ 0 ]
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
    self.label.setText("Running...")
    self.console.enableHighlighting( False )
    self.console.cursor.select( QTextCursor.LineUnderCursor )
    self.console.cursor.removeSelectedText()
    self.console.cursor.insertText( self.console.defaultPrompt + \
    "Importing data from canvas..." )
    self.repaint()
    QApplication.processEvents()
    if mlayer is None:
      self.console.appendText( "No layer selected in layer list", \
      QConsole.ERR_TYPE )
      self.console.displayPrompt()
      return
    rbuf = QString()
    def f( x ):
      rbuf.append( x )
    robjects.rinterface.setWriteConsole(f)
    if not data_only and not self.isPackageLoaded( "sp" ):
      self.console.appendText( "Unable to find R package 'sp'."
      + "\nPlease manually install the 'sp' package in R via "
      + "install.packages().", QConsole.ERR_TYPE )
      self.console.displayPrompt()
      return
    if mlayer.type() == QgsMapLayer.VectorLayer:
      self.r_layer_creator = QVectorLayerConverter( mlayer, data_only )
    if mlayer.type() == QgsMapLayer.RasterLayer:
      if data_only:
        self.console.appendText( "Cannot load raster layer attributes", \
        QConsole.ERR_TYPE )
        self.console.displayPrompt()
        return
      if not self.isPackageLoaded( "rgdal" ):
        self.console.appendText( "Unable to find R package 'rgdal'.\n "
        + "\n Please manually install the 'rgdal' package in R via "
        + "install.packages().", QConsole.ERR_TYPE )
        self.console.displayPrompt()
        return
      self.r_layer_creator = QRasterLayerConverter( mlayer )
    self.console.appendText( rbuf, QConsole.OUT_TYPE )
    QObject.connect( self.r_layer_creator, SIGNAL( "threadError( PyQt_PyObject )" ),
    self._showErrors )
    QObject.connect( self.r_layer_creator, \
    SIGNAL( "threadSuccess( PyQt_PyObject, PyQt_PyObject, PyQt_PyObject )" ), \
    self._showImport )
    self.r_layer_creator.start()

  def exportRObjects( self, to_file ):
    '''
    Export R sp objects to file or mapcanvas
    Vector layers can be saved to file or mapcanvas, raster 
    layers can be saved to file only
    Saving to file uses the R gdal functions, saving to map 
    canvas is a native manageR implementation
    '''
    self.label.setText("Running...")
    self.console.enableHighlighting( False )
    self.console.cursor.select( QTextCursor.LineUnderCursor )
    self.console.cursor.removeSelectedText()
    if to_file:
      put_text = "to file..."
    else:
      put_text = "to canvas..."
    self.console.cursor.insertText( self.console.defaultPrompt + "Exporting layer " + put_text )
    self.repaint()
    QApplication.processEvents()
    result = self.exportRObjectsDialog( to_file )
    # If there is no input layer, don't do anything
    if result is None: # this needs to be updated to reflect where we  get the R objects from...
      self.console.appendText( "No R spatial objects available", QConsole.ERR_TYPE )
      self.console.displayPrompt()
      return
    if not result:
      return
    if not to_file and not self.isPackageLoaded( "sp" ):
      self.console.appendText( "Unable to find R package 'sp'."
      + "\nPlease manually install the 'sp' package in R via "
      + "install.packages().", QConsole.ERR_TYPE )
      self.console.displayPrompt()
      return
    if to_file and not self.isPackageLoaded( "rgdal" ):
      self.console.appendText( "Unable to find R package 'rgdal'."
      + "\nPlease manually install the 'rgdal' package in R via "
      + "install.packages().", QConsole.ERR_TYPE )
      self.console.displayPrompt()
      return
    if not self.export_type == manageR.VECTOR and not self.export_type == manageR.RASTER:
      self.console.appendText( "Unrecognised sp object, unable to save to file.", QConsole.ERR_TYPE )
      self.console.displayPrompt()
      return
    if not to_file and self.export_type == manageR.RASTER:
      self.console.appendText( "Unable to export raster layers to map canvas at this time.", QConsole.ERR_TYPE )
      self.console.displayPrompt()
      return
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
      driver = QString()
      layer_name = fileDialog.getSaveFileName( self, "Save OGR",".", drivers, driver )
      if not layer_name.isEmpty():
          fileCheck = QFile( layer_name )
          if fileCheck.exists():
            if not QgsVectorFileWriter.deleteShapeFile( layer_name ):
              self.console.appendText( "Unable to overwrite existing file", QConsole.ERR_TYPE )
              self.console.displayPrompt()
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
    self.console.appendText( message, QConsole.OUT_TYPE )
    self.console.enableHighlighting( True )
    self.label.setText(" ")
    self.console.displayPrompt()

  def _showImport( self, rlayer, layer_name, message ):
    self.r_layer_creator.stop()
    del self.r_layer_creator
    robjects.globalEnv[ str( layer_name ) ] = rlayer
    self.updateRObjects()
    self.console.appendText( message, QConsole.OUT_TYPE )
    self.console.enableHighlighting( True )
    self.label.setText(" ")
    self.console.displayPrompt()
      
  def _showErrors( self, message ):
    self.console.enableHighlighting( False )
    try:
      self.r_layer_creator.stop()
      del self.r_layer_creator
    except:
      pass
    try:
      self.q_layer_creator.stop()
    except:
      pass
    self.console.appendText( message, QConsole.ERR_TYPE )
    self.console.enableHighlighting( True )
    self.label.setText(" ")
    
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
    
  def getDefaultCommands( self ):
    packages = ["base"]#robjects.r('.packages()') #changed temp
    store = QStringList()
    for package in packages:
      info = robjects.r('lsf.str("package:' + package + '" )') 
      test = QString(str(info)).replace(", \n    ", ", ")
      items = test.split('\n')
      for item in items:
        store.append( item )
    return store
    
    
class helpDialog( QDialog ):

  def __init__( self, parent, help_topic ):
    QDialog.__init__ ( self, parent )
    #initialise the display text edit
    display = QTextEdit( self )
    display.setReadOnly( True )
    #set the font style of the help display
    font = QFont( "Monospace" , 10, QFont.Normal )
    font.setFixedPitch( True )
    display.setFont( font )
    display.document().setDefaultFont( font )
    #initialise grid layout for dialog
    grid = QGridLayout( self )
    grid.addWidget( display )
    self.setWindowTitle( "manageR Help" )
    help_file = QFile( unicode( help_topic[ 0 ] ) )
    help_file.open( QFile.ReadOnly )
    stream = QTextStream( help_file )
    help_string = QString( stream.readAll() )
    #workaround to remove the underline formatting that r uses
    help_string.remove("_")
    display.setPlainText( help_string )
    help_file.close()
    self.resize( 550, 400 )

class searchDialog( QDialog ):

  def __init__( self, parent, help_topic ):
    QDialog.__init__ ( self, parent )
    #initialise the display text edit
    display = QTextEdit( self )
    display.setReadOnly( True )
    #set the font style of the help display
    font = QFont( "Monospace" , 10, QFont.Normal )
    font.setFixedPitch( True )
    display.setFont( font )
    display.document().setDefaultFont( font )
    #initialise grid layout for dialog
    grid = QGridLayout( self )
    grid.addWidget( display )
    self.setWindowTitle( "manageR Help Search" )
    #get help output from r 
    #note: help_topic should only contain the specific
    #      help topic (i.e. no brackets etc.)
    matches = help_topic.subset("matches")[0]
    fields = help_topic.subset("fields")[0]
    pattern = help_topic.subset("pattern")[0]
    fields_string = QString()
    for i in fields:
      fields_string.append( i + " or ")
    fields_string.chop( 3 )
    display_string = QString( "Help files with " + fields_string )
    display_string.append( "matching '" + pattern[0] + "' using " )
    display_string.append( "regular expression matching:\n\n" )
    nrows = robjects.r.nrow( matches )[0]
    ncols = robjects.r.ncol( matches )[0]
    for i in range( 1, nrows + 1 ):
        row = QString()
        pack = matches.subset( i, 3 )[0]
        row.append(pack)
        row.append("::")
        pack = matches.subset( i, 1 )[0]
        row.append(pack)
        row.append("\t\t")
        pack = matches.subset( i, 2 )[0]
        row.append(pack)
        row.append("\n")
        display_string.append( row )
    display.setPlainText( display_string )
    #help_file.close()
    self.resize( 550, 400 )

class commandThread( QThread ):

  def __init__( self, thread, parent, text ):
    QThread.__init__( self, thread )
    self.parent = parent
    self.running = False
    self.command = text
    self.words = QString( text )

  def stop( self ):
    self.running = False

  def run( self ):
    print "***" + self.words + "***"
    try:
      self.running = True
      if ( self.words.startsWith( 'quit(' ) or self.words.startsWith( 'q(' ) ) and self.words.count( ")" ) == 1:
        self.emit( SIGNAL( "threadError( PyQt_PyObject )" ), "System exit not allowed" )
      def f( x ):
        print x
        if x.contains("<Return>"):
          self.emit( SIGNAL( "threadComplete()" ) )
        self.emit( SIGNAL( "threadOutput( PyQt_PyObject )" ), x )
      robjects.rinterface.setWriteConsole( f )
      try:
        r_code = "withVisible( " + unicode( self.words ) + " )"
        output = robjects.r( r_code )
        visible = output.r["visible"][0][0]
        if visible:
          self.emit( SIGNAL( "threadOutput( PyQt_PyObject )" ), unicode( output.r["value"][0] ) )
      except robjects.rinterface.RRuntimeError, rre:
  #      self.emit( SIGNAL( "threadError( PyQt_PyObject )" ), QString( str(rre) ) )
        pass
      self.emit( SIGNAL( "threadComplete()" ) )
    except Exception, e:
      self.emit( SIGNAL( "threadError( PyQt_PyObject )" ), str(e) )
