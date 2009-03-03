from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import time, threading
import loadRLayer, spatialDataFrame, saveRLayer
from frmManageR import Ui_Dialog

try:
    import rpy2.robjects as robjects
    import rpy2.rinterface as rinterface
except ImportError:
    QMessageBox.warning( None , "manageR", "Unable to load manageR: Required package rpy2 was unable to load"
    + "\nPlease ensure that both R, and the corresponding version of Rpy are correctly installed.")


class Dialog( QDialog, Ui_Dialog ):
    def __init__( self, iface ):
        QDialog.__init__ ( self )
        self.iface = iface
        self.mapCanvas = self.iface.mapCanvas()
        self.setupUi( self )
        self.initialiseVariables()
        self.adjustUI()
        # create the required connections
        QObject.connect( self.txtInput, SIGNAL( "returnPressed()" ), self.entered )
        QObject.connect( self.btnData, SIGNAL( "clicked()" ), self.getDataFrame )
        QObject.connect( self.btnAbout, SIGNAL( "clicked()" ), self.helprun )
        QObject.connect( self.btnLoad, SIGNAL( "clicked()" ), self.load )
        QObject.connect( self.btnExport, SIGNAL( "clicked()" ), self.export )
        QObject.connect( self.btnClose, SIGNAL( "clicked()" ), self.closeEvent )
        QObject.connect( self.btnSave, SIGNAL( "clicked()" ), self.save )
        QObject.connect( self.btnMulti, SIGNAL( "clicked()" ), self.expand )
        QObject.connect( self.btnSingle, SIGNAL( "clicked()" ), self.expand )
        QObject.connect( self.btnEntered, SIGNAL( "clicked()" ), self.entered )
        QObject.connect( self.mapCanvas, SIGNAL( "layersChanged()" ), self.update )
        QObject.connect( self.inShape, SIGNAL( "currentIndexChanged(QString)" ), self.updateInShape )
        self.txtMain.append( self.welcomeString() )
        # populate layer list
        self.update()
        self.plot_thread = threading.Timer( 0.1, refresh )
        self.plot_thread.start()

#        def out_to_console( x ):
#            self.output_text( str( x ) )
#        robjects.rinterface.setWriteConsole( out_to_console )

    def initialiseVariables( self ):
        self.commandList = []
        self.commandIndex = 0
        self.currentInShape = QgsVectorLayer( "", "", "" )
        self.currentOutShape = None
        self.instVersion = "0.5"
    
    def adjustUI( self ):
        font = QFont( "Monospace" , 10, QFont.Normal )
        font.setFixedPitch( True )
        self.txtMain.setFont( font )
        self.setWindowIcon( QIcon( ":icons/manage.png" ) )
        self.setWindowFlags( Qt.Window )
        self.txtMulti.hide()
        self.multiArrow.hide()
        self.btnSingle.hide()
        self.btnAbout.setIcon( QIcon( ":icons/managehelp.png" ) )
        self.btnSingle.setIcon( QIcon( ":icons/multi.png" ) )
        self.btnEntered.hide()
        self.btnEntered.setIcon( QIcon( ":icons/entered.png" ) )
        self.btnMulti.setIcon( QIcon( ":icons/single.png" ) )    

    def helprun( self ):
        text = QString()
        text.append( "manageR v" + self.instVersion + " - Interface to the R statistical analysis program\n" )
        text.append( "Copyright (C) 2009 Carson J.Q. Farmer\ncarson.farmer@gmail.com\nwww.ftools.ca/manageR.html\n" )
        text.append( "manageR provides comprehensive statistical capabilities to Quantum GIS " )
        text.append( "by loosely coupling QGIS with the R statistical " )
        text.append( "programming environment. Allows upload of QGIS layers directly " )
        text.append( "into R, and the ability to perform R operations on the data " )
        text.append( "directly from within QGIS. It interfaces with R using RPy, " )
        text.append( "which is a Python interface to the R Programming Language.\n\n" )
        text.append( "Features:\n* Perform complex statistical analysis functions on raster, " )
        text.append( "vector and spatial database formats\n* Use the R statistical environment to graph, plot, " )
        text.append( "and map spatial and aspatial data from within QGIS\n" )
        text.append( "* Export R (sp) vector layers directly to QGIS map canvas as QGIS vector layers\n" )
        text.append( "* Perform all available R commands from within QGIS, including multi-line commands\n" )
        text.append( "* Read QGIS vector layers directly from map canvas as R (sp) vector layers, " )
        text.append( "allowing analysis to be carried out on any vector format supported by QGIS" )
        QMessageBox.information( self, "manageR", text )
        
    def welcomeString( self ):        text = QString()
        text.append( "Welcome to manageR v" + self.instVersion + "\n")
        text.append( "QGIS interface to the R statistical analysis program\n" )
        text.append( "Copyright (C) 2009  Carson Farmer\n" )
        text.append( "Licensed under the terms of GNU GPL 2\nmanageR is free software; you can redistribute it " )
        text.append( "and/or modify it under the terms of " )
        text.append( "the GNU General Public License as published by the Free Software Foundation; either " )
        text.append( "version 2 of the License, or (at your option) any later version.\n" )
        text.append( "Currently running " + unicode( robjects.r.version[ 12 ][ 0 ] ) + "\n" )
        return text

    def expand( self ):
        if self.txtMulti.isHidden():
            self.inputArrow.hide()
            self.multiArrow.show()
            self.txtInput.hide()
            self.txtMulti.show()
            self.btnMulti.hide()
            self.btnSingle.show()
            self.btnEntered.show()
            self.txtMulti.insertPlainText( self.txtInput.text() )
            self.txtInput.clear()
        else:
            self.multiArrow.hide()
            self.inputArrow.show()
            self.txtMulti.hide()
            self.txtInput.show()
            self.btnMulti.show()
            self.btnSingle.hide()
            self.btnEntered.hide()
            self.txtInput.insert( self.txtMulti.toPlainText() )
            self.txtMulti.clear()
            
    def keyPressEvent( self, event ):
        if event.key() == Qt.Key_Up:
            if len( self.commandList ) >= 1:
                if self.commandIndex <= 1:
                    self.commandIndex = 0
                else:
                    self.commandIndex -= 1
                if self.txtMulti.isHidden():
                    self.txtInput.setText( self.commandList[ self.commandIndex ] )
        elif event.key() == Qt.Key_Down:
            if len( self.commandList ) >= 1:
                self.commandIndex += 1
                if self.commandIndex >= len( self.commandList ):
                    self.commandIndex = len( self.commandList )
                    if self.txtMulti.isHidden():
                        self.txtInput.clear()
                    else:
                        self.txtMulti.clear()
                else:
                    if self.txtMulti.isHidden():
                        self.txtInput.setText( self.commandList[ self.commandIndex ] )

    def closeEvent( self, ask = True ):
        askSave = QMessageBox.question( self, "manageR", "Save workspace image?", 
        QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel )
        if askSave == QMessageBox.Yes:
            robjects.r( 'save.image( file = ".Rdata" )' )
            if self.chkClear.isChecked():
                robjects.r( 'rm( list = ls( all = True ) )' )
                robjects.r( 'gc()' )
            robjects.r( 'graphics.off()' )
            self.plot_thread.cancel()
            self.reject()
        elif not askSave == QMessageBox.Cancel:
            if self.chkClear.isChecked():
                robjects.r( 'rm( list = ls( all = True ) )' )
                robjects.r( 'gc()' )
            robjects.r( 'graphics.off()' )
            self.plot_thread.cancel()
            self.reject()
            
    def update(self):
        self.inShape.clear()
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for name, layer in layermap.iteritems():
            self.inShape.addItem( unicode( layer.name() ) )
            
# This is used each time the input layer combo box is changed
# It automatically updates self.currentInShape to save time 
# for other functions that require this as input
    def updateInShape( self, inName ):
        self.currentInShape = self.getMapLayerByName(inName)

# This is used whenever we check for sp objects in manageR
# TODO: Find a better way to implement this
    def updateObs( self ):
        self.outShape.clear()
        ls_ = robjects.r[ 'ls' ]
        class_ = robjects.r[ 'class' ]
        for item in ls_():
            check = class_( robjects.r( item ) )[ 0 ]
            if check == "SpatialPointsDataFrame": self.outShape.addItem( item )
            elif check == "SpatialPolygonsDataFrame": self.outShape.addItem( item )
            elif check == "SpatialLinesDataFrame": self.outShape.addItem( item )
            elif check == "SpatialGridDataFrame": self.outShape.addItem( item )
            elif check == "SpatialPixelsDataFrame": self.outShape.addItem( item )

# Checks if an R spatial object is a vector or raster layer
    def checkObs( self, in_name ):
        class_ = robjects.r[ 'class' ]
        check = class_( robjects.r( str( in_name ) ) )[ 0 ]
        if check == "SpatialPointsDataFrame" or check == "SpatialPolygonsDataFrame" or check == "SpatialLinesDataFrame":
            return True
        elif check == "SpatialGridDataFrame" or check == "SpatialPixelsDataFrame":
            return False
        else:
            return None
    
# This is used whenever the user clicks the save button
# Used to save R sp objects as gdal/org files
    def save( self ):
        if self.outShape.currentText() == "":
            self.error_text( "No R spatial object specified" )
        else:
            if not loadRLayer.checkPack( "rgdal" ):
                self.error_text( "Unable to find R package 'rgdal'\n\n" 
                + "Please manually install the 'rgdal' package in R via install.packages() (or another preferred method)." )
            else:
                checkVect = self.checkObs( self.outShape.currentText() )
                if checkVect:
                    ( check, output ) = saveRLayer.saveOgr( self, self.outShape.currentText() )
                    self.output_text( output )
                elif not checkVect:
                    ( check, output ) = saveRLayer.saveGdal( self, self.outShape.currentText() )
                    self.output_text( output )
                else:
                    self.error_text( "Unrecognized sp object, cannot save to file." )

# Converts a QgsVectorLayer to an R Spatial*DataFrame
# Provides the ability to load any vector layer that QGIS
# supports into R. Only selected features will be imported into R
    def getSpatialDataFrame(self, mlayer):
        if not loadRLayer.checkPack("sp"):
            self.error_text( "Unable to find R package 'sp'.\n "
            + "\n Please manually install the 'sp' package in R via "
            + "install.packages() (or another preferred method).")
        else:
            #if self.inShape.currentText() == "":
            if not self.currentInShape.isValid():
                self.error_text( "No valid input layer specified" )
            else:
                self.btnData.setEnabled(False)
                mlayer = self.currentInShape
                if mlayer.type() == mlayer.VectorLayer:
                    ( spDataFrame, rows, columns, extra ) = spatialDataFrame.getSpatialDataFrame( robjects, mlayer, True )
                    if not type( spDataFrame ) == type( "" ):
                        robjects.globalEnv[ str( mlayer.name() ) ] = spDataFrame
                        self.updateObs()
                        self.output_text( "QGis Vector Layer\nwith " + unicode(rows) + " rows and " + unicode(columns) + " columns")
                        if not extra == "":
                            self.error_text( extra )
                    else:
                        self.error_text( spDataFrame )
                else:
                    self.error_text( "Cannot load raster layer attributes" )
        self.btnData.setEnabled( True )

# Converts a QgsMapLayer attribute table to an R data.frame
# Faster than loaded a spatial dataset into manageR, useful if user
# only needs vector layer attributes, with no spatial information.
# If there are selected features, only their attributes will be 
# imported into R.
    def getDataFrame( self ):
        if not self.currentInShape.isValid():
            self.error_text( "No input layer specified" )
        else:
            self.btnData.setEnabled(False)
            #layerName = self.inShape.currentText()
            #mlayer = self.getMapLayerByName(layerName)
            mlayer = self.currentInShape
            if mlayer.type() == mlayer.VectorLayer:
                self.output_text( "Loading data for " + unicode(mlayer.name()) + " ..." )
                (dataFrame, rows, columns, extra) = spatialDataFrame.getSpatialDataFrame(robjects, mlayer, False)
                if not dataFrame == False:
                    robjects.globalEnv[unicode(mlayer.name()).encode('utf-8')] = dataFrame
                    self.updateObs()
                    self.output_text("QGis Attribute Table\nwith " + unicode( rows ) + " rows and " + unicode( columns ) + " columns" )
                    if not extra == "":
                        self.error_text( extra )
                else:
                    self.error_text( rows + columns )
            else:
                self.error_text( "Cannot load raster layer attributes")
            self.btnData.setEnabled( True )

# Performs conversion of txt input in manageR to R
# commands
    def commands( self, r_code, update ):
        if not self.plot_thread.isAlive():
            try:
                self.plot_thread.start()
            except Exception, e:
                print "manageR error: plotting thread interrupt, plots will no longer automatically refresh"
        try:
            r_code = "withVisible( " + r_code + " )"
            output = robjects.r( r_code )
            if output[ 1 ][ 0 ]:
                self.output_text( str( output[ 0 ] ) )
            # restore default function
            #rinterface.setWriteConsole( rinterface.consolePrint )
            return True
        except Exception, e:
#            # restore default function
            #rinterface.setWriteConsole( rinterface.consolePrint )
#            self.txtMain.setTextColor( QColor( 255, 0, 0, 255 ) )
#            self.txtMain.append( str( e ) )
#            self.txtMain.setTextColor( QColor( 0, 0, 0, 255 ) )
            return False

# When enter is pressed, convert input to R commands
# This function gathers the R input, and
# uses self.commands to convert it
    def entered( self ):
        if self.txtMulti.isHidden():
            expression = self.txtInput.text()
        else:
            expression = self.txtMulti.toPlainText()
        self.txtInput.clear()
        self.txtMulti.clear()
        self.txtMain.append( "> " + expression )
        if not expression.contains("quit("):
            self.commandList.append( expression )
            self.commandIndex = len( self.commandList )
            self.commands( unicode( expression ), True )
            self.updateObs()
        
# Initializes the data conversion
# This function is used to setup conversion
# to R spatial object
    def load(self):
        self.btnLoad.setDisabled(True)
        if self.inShape.currentText() == "":
            self.error_text( "No input layer specified" )
        else:
            inName = self.inShape.currentText()
            self.output_text( "Loading " + unicode(inName) + " ..." )
            self.convert (inName )
            self.updateObs()
        self.btnLoad.setEnabled( True )

# Converts stored spatial data to R spatial (sp) object
# For Raster layers, this function gives the map layer 
# source and name information to R and uses rgdal to load 
# the dataset
# TODO: Change this function so that it reads in all (including raster) QgsMapLayers
    def convert(self, inName):
        mlayer = self.currentInShape
        if mlayer.type() == mlayer.VectorLayer:
            self.getSpatialDataFrame( mlayer )
        else:
            if not loadRLayer.checkPack( "rgdal" ):
                self.error_text( "Unable to find R package 'rgdal'.\n "
                + "\n Please manually install the 'rgdal' package in R via "
                + "install.packages() (or another preferred method)." )
            else:
                dsn = mlayer.source()
                layer = mlayer.name()
                dsn.replace("\\", "/")
                self.txtMain.setTextColor( QColor( 0, 0, 255, 255 ) )
                self.commands( unicode(inName) + " <- readGDAL(fname = '" + str( dsn ) + "')", True ) #moved from below...
                self.txtMain.setTextColor( QColor( 0, 0, 0, 255 ) )

# Gets map layer by layername in canvas 
# (both vector and raster)
    def getMapLayerByName(self, myName):
        #mc = self.iface.mapCanvas()
        nLayers = self.mapCanvas.layerCount()
        for l in range(nLayers):
            mlayer = self.mapCanvas.layer(l)
            if unicode(mlayer.name()) == unicode(myName):
                return mlayer

# This function is used to setup the 'convert' function from 'loadRLayer'
# It is used to convert R sp objects to a format recognized by QGIS
# and then it is added to the mapCanvas as a 'memory' layer
    def export(self):
        if not loadRLayer.checkPack("sp"):
            self.error_text( "Unable to find R package 'sp'.\n "
            + "\n Please manually install the 'sp' package in R via "
            + "install.packages() (or another preferred method)." )
        # If there is no input layer, tell user...
        if self.outShape.currentText() == "":
            self.error_text( "No R spatial object specified" )
        else:
            checkVect = self.checkObs(self.outShape.currentText())
            if checkVect:
                layer_name = str( self.outShape.currentText() )
                ( check, result ) = loadRLayer.convert(robjects.r[ layer_name ], layer_name )
                if not check: self.txtMain.append( result )
            elif not checkVect:
                self.error_text( "Unable to export raster layers to map canvas at this time." )
            else:
                self.error_text( "Unrecognized sp object, cannot save to file." )
                
    def error_text( self, text ):
        self.txtMain.setTextColor( QColor( 255, 0, 0, 255 ) )
        self.txtMain.append( text )
        self.txtMain.setTextColor( QColor( 0, 0, 0, 255 ) )
        
    def output_text( self, text ):
        self.txtMain.setTextColor( QColor( 0, 0, 255, 255 ) )
        self.txtMain.append( text )
        self.txtMain.setTextColor( QColor( 0, 0, 0, 255 ) )
        
def refresh():
    # Ctrl-C to interrupt
    while True:
        rinterface.process_revents()
        time.sleep(0.1)


