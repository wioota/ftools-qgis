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

import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from qgis.core import *
#import resources

class QGraphicsTable( QWidget ):
  '''
  QGraphicsTable Class:
  Description to be added
  '''

  def __init__( self, parent ):
    QWidget.__init__( self, parent )
    # initialise standard settings
    self.setMinimumSize( 30, 30 )
    self.parent = parent
    
    self.graphicsTable = QTableWidget( 0, 2, self )
    labels = QStringList()
    labels.append( "Item" )
    labels.append( "Device" )
    self.graphicsTable.setHorizontalHeaderLabels( labels )
    self.graphicsTable.horizontalHeader().setResizeMode( 1, QHeaderView.Stretch )
    self.graphicsTable.setShowGrid( True )
    self.graphicsTable.setSelectionBehavior( QAbstractItemView.SelectRows )
    self.graphicsTable.setSelectionMode( QAbstractItemView.SingleSelection )
    self.label = QLabel()
    self.label.setText( "Graphics list" )
    
    self.rm = QToolButton( self )
    self.rm.setText( "close" )
    self.rm.setToolTip( "Close selected graphic" )
    self.rm.setWhatsThis( "Close selected graphic" )
    self.rm.setIcon( QIcon( ":mActionGraphicRemove.png" ) )
    self.rm.setEnabled( False )
    self.rm.setAutoRaise( True )
    
    self.export = QToolButton( self )
    self.export.setText( "export" )
    self.export.setToolTip( "Export graphic as bitmap" )
    self.export.setWhatsThis( "Export graphic as bitmap" )
    self.export.setIcon( QIcon( ":mActionGraphicExport.png" ) )
    self.export.setEnabled( False )
    self.export.setAutoRaise( True )
    
    self.save = QToolButton( self )
    self.save.setText( "save" )
    self.save.setToolTip( "Save graphic to file" )
    self.save.setWhatsThis( "Save graphic to file" )
    self.save.setIcon( QIcon( ":mActionGraphicSave.png" ) )
    self.save.setEnabled( False )
    self.save.setAutoRaise( True )

    self.new = QToolButton( self )
    self.new.setText( "new" )
    self.new.setToolTip( "Create new graphics device" )
    self.new.setWhatsThis( "Create new graphics device" )
    self.new.setIcon( QIcon( ":mActionGraphicNew.png" ) )
    self.new.setEnabled( True )
    self.new.setAutoRaise( True )

    self.refresh = QToolButton( self )
    self.refresh.setText( "refresh" )
    self.refresh.setToolTip( "Refresh list of graphic devices" )
    self.refresh.setWhatsThis( "Refresh list of graphic devices" )
    self.refresh.setIcon( QIcon( ":mActionGraphicRefresh.png" ) )
    self.refresh.setEnabled( True )
    self.refresh.setAutoRaise( True )
  
    grid = QGridLayout( self )
    horiz = QHBoxLayout()
    horiz.addWidget( self.label)
    horiz.addWidget( self.refresh )
    horiz.addWidget( self.rm )
    horiz.addWidget( self.export )
    horiz.addWidget( self.save )
    horiz.addWidget( self.new )
    grid.addLayout( horiz, 0, 0, 1, 1 )
    grid.addWidget( self.graphicsTable, 1, 0, 1, 1 )
    
    self.graphics = dict()
    self.connect( self.rm, SIGNAL( "clicked()" ), self.removeGraphic )
    self.connect( self.export, SIGNAL( "clicked()" ), self.exportGraphic )
    self.connect( self.save, SIGNAL( "clicked()" ), self.saveGraphic )
    self.connect( self.new, SIGNAL( "clicked()" ), self.newGraphic )
    self.connect( self.refresh, SIGNAL( "clicked()" ), self.refreshGraphics )
    self.connect( self.graphicsTable, \
    SIGNAL( "itemSelectionChanged()" ), self.selectionChanged )

  def updateGraphics( self, graphics ):
    self.graphics = {}
    while self.graphicsTable.rowCount() > 0:
      self.graphicsTable.removeRow( 0 )
    for graphic in graphics[1].items():
      self.addGraphic( graphic )

  def refreshGraphics( self ):
    self.parent.emit( SIGNAL( "newObjectCreated( PyQt_PyObject )" ), self.parent.updateRObjects() )

  def addGraphic( self, graphic ):
    self.graphics[ graphic[ 0 ] ] = graphic[ 1 ]
    itemID = QTableWidgetItem( QString( str(graphic[ 0 ]) ) )
    itemID.setFlags( Qt.ItemIsSelectable|Qt.ItemIsEnabled )
    itemDevice = QTableWidgetItem( QString(graphic[ 1 ]) )
    itemDevice.setTextAlignment( Qt.AlignRight | Qt.AlignVCenter )
    itemDevice.setFlags( Qt.ItemIsSelectable|Qt.ItemIsEnabled )
    row = self.graphicsTable.rowCount()
    self.graphicsTable.insertRow( row )
    self.graphicsTable.setItem( row, 0, itemID )
    self.graphicsTable.setItem( row, 1, itemDevice )
    self.graphicsTable.resizeColumnsToContents
    
  def selectionChanged( self ):
    row = self.graphicsTable.currentRow()
    if row < 0 or row >= self.graphicsTable.rowCount() or \
    self.graphicsTable.rowCount() < 1:
      self.save.setEnabled( False )
      self.rm.setEnabled( False )
      self.export.setEnabled( False )
    else:
      itemName, itemType = self.getGraphicInfo( row )
      self.save.setEnabled( True )
      self.rm.setEnabled( True )
      self.export.setEnabled( True )

  def removeGraphic( self ):
    row = self.graphicsTable.currentRow()
    if row < 0:
      return False
    itemID, itemDevice = self.getGraphicInfo( row )
    self.graphicsTable.removeRow( row )
    self.sendCommands( QString( 'dev.off(' + itemID + ')' ) )

  def newGraphic( self ):
    self.sendCommands( QString( 'dev.new()' ) )
      
  def exportGraphic( self ):
    row = self.graphicsTable.currentRow()
    if row < 0:
      return False
    itemID, itemDevice = self.getGraphicInfo( row )
    #self.connect( fd, SIGNAL( "filterSelected(QString)" ), self.setFilter )
    fd = QFileDialog( self.parent, "Save graphic to file", "", \
    "PNG (*.png);;JPEG (*.jpeg);;TIFF (*.TIFF);;BMP (*.bmp)" )
    fd.setAcceptMode( QFileDialog.AcceptSave )
    if not fd.exec_() == QDialog.Accepted:
      return False
    files = fd.selectedFiles()
    selectedFile = files.first()
    if selectedFile.length() == 0:
      return False
    suffix = QString( fd.selectedNameFilter() )
    index1 = suffix.lastIndexOf( "(" )+2
    index2 = suffix.lastIndexOf( ")" )
    suffix = suffix.mid( index1, index2-index1 )
    if not selectedFile.endsWith( suffix ):
      selectedFile.append( suffix )
    command = QString( 'dev.set(' + itemID + ')' )
    self.sendCommands( command )
    command = QString( QString( 'dev.copy( ' + suffix.remove(".") + ', filename = "' + selectedFile ) )
    command.append( QString( '", width = dev.size("px")[1], height = dev.size("px")[2]' ) )
    command.append( QString( ', units = "px", bg = "transparent")' ) )
    self.sendCommands( command )
    command = QString( 'dev.off()' )
    self.sendCommands( command )
    self.parent.label.setText( "Graphic exported" )
    
  def saveGraphic( self ):
    row = self.graphicsTable.currentRow()
    if row < 0:
      return False
    itemID, itemDevice = self.getGraphicInfo( row )
    fd = QFileDialog( self.parent, "Save R  graphic to file", "", \
    "PDF (*.pdf);;EPS (*.eps);;SVG (*.svg)" )
    fd.setAcceptMode( QFileDialog.AcceptSave )
    if not fd.exec_() == QDialog.Accepted:
      return False
    files = fd.selectedFiles()
    selectedFile = files.first()
    if selectedFile.length() == 0:
      return False
    suffix = QString( fd.selectedNameFilter() )
    index1 = suffix.lastIndexOf( "(" )+2
    index2 = suffix.lastIndexOf( ")" )
    suffix = suffix.mid( index1, index2-index1 )
    if not selectedFile.endsWith( suffix ):
      selectedFile.append( suffix )
    command = QString( 'dev.set(' + itemID + ')' )
    self.sendCommands( command )
    command = QString( 'dev.copy( ' + suffix.remove(".") + ', file = "' + selectedFile + '")' )
    self.sendCommands( command )
    command = QString( 'dev.off()' )
    self.sendCommands( command )
    self.parent.label.setText( "Graphic saved" )
      
  def getGraphicInfo( self, row ):
    itemID = self.graphicsTable.item( row, 0 )
    itemID = itemID.data( Qt.DisplayRole ).toString()
    itemDevice = self.graphicsTable.item( row, 1 )
    itemDevice = itemDevice.data( Qt.DisplayRole ).toString()
    return ( itemID, itemDevice )
    
  def sendCommands( self, commands ):
    if not commands.isEmpty():
      mime = QMimeData()
      mime.setText( commands )
      self.parent.console.insertFromMimeData( mime )
      self.parent.runCommand( commands )