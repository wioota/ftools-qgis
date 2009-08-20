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

class QWorkingDir( QWidget ):
  '''
  QWorkingDir Class:
  Description to be added
  '''

  def __init__( self, parent, base ):
    QWidget.__init__( self, parent )
    # initialise standard settings
    self.setMinimumSize( 30, 30 )
    self.parent = parent
    self.base = base
    self.model = QDirModel( self )
    self.tree = QListView( self )
    #tree = QTreeView( self )
    self.tree.setModel( self.model )
    index = self.model.index( self.base, 0 )

    self.label = QLabel()
    self.label.setText( "Working directory" )

    self.current = QLineEdit( self )
    font = QFont( "Monospace" , 10, QFont.Normal )
    font.setFixedPitch( True )
    self.current.setFont( font )
    self.setCurrentDir( index )

    self.up = QToolButton( self )
    self.up.setText( "up" )
    self.up.setToolTip( "Move up one level" )
    self.up.setWhatsThis( "Move up one level" )
    self.up.setIcon( QIcon( ":mActionFolderUp.png" ) )
    self.up.setAutoRaise( True )
    
    self.mkdir = QToolButton( self )
    self.mkdir.setText( "mkdir" )
    self.mkdir.setToolTip( "Create new folder" )
    self.mkdir.setWhatsThis( "Create new folder" )
    self.mkdir.setIcon( QIcon( ":mActionFolderNew.png" ) )
    self.mkdir.setAutoRaise( True )
        
    self.set = QToolButton( self )
    self.set.setText( "setwd" )
    self.set.setToolTip( "Set working directory" )
    self.set.setWhatsThis( "Set working directory" )
    self.set.setIcon( QIcon( ":mActionFolderSet.png" ) )
    self.set.setAutoRaise( True )
    
    grid = QGridLayout( self )
    grid.addWidget( self.label, 0, 0, 1, 2 )
    grid.addWidget( self.current, 1, 0, 1, 1 )
    horiz = QHBoxLayout()
    horiz.addWidget( self.set )
    horiz.addWidget( self.up )
    horiz.addWidget( self.mkdir )
    grid.addLayout(horiz, 1, 1, 1, 1 )
    grid.addWidget( self.tree, 2, 0, 1, 2 )
    
    self.connect( self.tree, SIGNAL( "clicked(QModelIndex)" ), self.clicked )
    self.connect( self.up, SIGNAL( "clicked()" ), self.moveUpDir )
    self.connect( self.mkdir, SIGNAL( "clicked()" ), self.createDir )
    self.connect( self.set, SIGNAL( "clicked()" ), self.setWorkingDir )
    
  def clicked( self, index ):
    if self.model.isDir( index ):
      self.tree.setRootIndex( index )
    self.setCurrentDir( index )
      
  def moveUpDir( self ):
    self.setCurrentDir( self.tree.rootIndex().parent() )
    
  def setCurrentDir( self, index ):
    self.tree.setRootIndex( index )
    path = self.model.filePath( self.tree.rootIndex() )
    self.current.setText( path )
    
  def createDir( self ):
    parent = self.tree.rootIndex()
    ok = False
    path = self.model.filePath( self.tree.rootIndex() )
    text, ok = QInputDialog.getText( self, "New folder", \
           "Folder name:", QLineEdit.Normal, path )
    if ok and not text.isEmpty():
      QDir( path ).mkdir( text )
      self.model.refresh( parent )
      
  def setWorkingDir( self ):
    commands = QString( 'setwd("' + self.current.text() + '")' )
    if not commands.isEmpty():
      mime = QMimeData()
      mime.setText( commands )
      self.parent.console.insertFromMimeData( mime )
      self.parent.runCommand( commands )
      
class QVariableTable( QWidget ):
  '''
  QVariableTable Class:
  Description to be added
  '''
  VECTORTYPES = [ "SpatialPointsDataFrame",
    "SpatialPolygonsDataFrame",
    "SpatialLinesDataFrame" ]
  RASTERTYPES = [ "SpatialGridDataFrame",
    "SpatialPixelsDataFrame" ]

  def __init__( self, parent ):
    QWidget.__init__( self, parent )
    # initialise standard settings
    self.setMinimumSize( 30, 30 )
    self.parent = parent
    
    self.variableTable = QTableWidget( 0, 2, self )
    labels = QStringList()
    labels.append( "Name" )
    labels.append( "Type" )
    self.variableTable.setHorizontalHeaderLabels( labels )
    self.variableTable.horizontalHeader().setResizeMode( 1, QHeaderView.Stretch )
    self.variableTable.setShowGrid( True )
    self.variableTable.setSelectionBehavior( QAbstractItemView.SelectRows )
    self.variableTable.setSelectionMode( QAbstractItemView.SingleSelection )
    self.label = QLabel()
    self.label.setText( "Variables list" )
    
    self.rm = QToolButton( self )
    self.rm.setText( "rm" )
    self.rm.setToolTip( "Remove selected variable" )
    self.rm.setWhatsThis( "Removed selected variable" )
    self.rm.setIcon( QIcon( ":mActionVariableRemove.png" ) )
    self.rm.setEnabled( False )
    self.rm.setAutoRaise( True )
    
    self.export = QToolButton( self )
    self.export.setText( "export" )
    self.export.setToolTip( "Export data to file" )
    self.export.setWhatsThis( "Export data to file" )
    self.export.setIcon( QIcon( ":mActionVariableExport.png" ) )
    self.export.setEnabled( False )
    self.export.setAutoRaise( True )
    
    self.canvas = QToolButton( self )
    self.canvas.setText( "canvas" )
    self.canvas.setToolTip( "Export layer to map canvas" )
    self.canvas.setWhatsThis( "Export layer to map canvas" )
    self.canvas.setIcon( QIcon( ":mActionVariableCanvas.png" ) )
    self.canvas.setEnabled( False )
    self.canvas.setAutoRaise( True )

    self.layer = QToolButton( self )
    self.layer.setText( "layer" )
    self.layer.setToolTip( "Import layer from map canvas" )
    self.layer.setWhatsThis( "Import layer from map canvas" )
    self.layer.setIcon( QIcon( ":mActionVariableLayer.png" ) )
    self.layer.setEnabled( True )
    self.layer.setAutoRaise( True )
    
    self.save = QToolButton( self )
    self.save.setText( "save" )
    self.save.setToolTip( "Save R variable to file" )
    self.save.setWhatsThis( "Save R variable to file" )
    self.save.setIcon( QIcon( ":mActionVariableSave.png" ) )
    self.save.setEnabled( False )
    self.save.setAutoRaise( True )
    
    self.load = QToolButton( self )
    self.load.setText( "load" )
    self.load.setToolTip( "Load R variable(s) from file" )
    self.load.setWhatsThis( "Load R variable(s) from file" )
    self.load.setIcon( QIcon( ":mActionVariableLoad.png" ) )
    self.load.setEnabled( True )
    self.load.setAutoRaise( True )
    
    grid = QGridLayout( self )
    horiz = QHBoxLayout()
    horiz.addWidget( self.label)
    horiz.addWidget( self.rm )
    horiz.addWidget( self.export )
    horiz.addWidget( self.canvas )
    horiz.addWidget( self.layer )
    horiz.addWidget( self.save )
    horiz.addWidget( self.load )
    #grid.addWidget( self.label )
    grid.addLayout( horiz, 0, 0, 1, 1 )
    grid.addWidget( self.variableTable, 1, 0, 1, 1 )
    
    self.variables = dict()
    self.connect( self.rm, SIGNAL( "clicked()" ), self.removeVariable )
    self.connect( self.export, SIGNAL( "clicked()" ), self.exportVariable )
    self.connect( self.save, SIGNAL( "clicked()" ), self.saveVariable )
    self.connect( self.canvas, SIGNAL( "clicked()" ), self.exportToCanvas )
    self.connect( self.load, SIGNAL( "clicked()" ), self.loadRVariable )
    self.connect( self.layer, SIGNAL( "clicked()" ), self.importFromCanvas )
    self.connect( self.variableTable, \
    SIGNAL( "itemSelectionChanged()" ), self.selectionChanged )

  def updateVariables( self, variables ):
    self.variables = {}
#    self.variableTable.clearContents()
    while self.variableTable.rowCount() > 0:
      self.variableTable.removeRow( 0 )
    for variable in variables[0].items():
      self.addVariable( variable )

  def addVariable( self, variable ):
    self.variables[ variable[ 0 ] ] = variable[ 1 ]
    nameItem = QTableWidgetItem( QString(variable[ 0 ]) )
    nameItem.setFlags( Qt.ItemIsSelectable|Qt.ItemIsEnabled )
    typeItem = QTableWidgetItem( QString(variable[ 1 ]) )
    typeItem.setTextAlignment( Qt.AlignRight | Qt.AlignVCenter )
    typeItem.setFlags( Qt.ItemIsSelectable|Qt.ItemIsEnabled )
    row = self.variableTable.rowCount()
    self.variableTable.insertRow( row )
    self.variableTable.setItem( row, 0, nameItem )
    self.variableTable.setItem( row, 1, typeItem )
    self.variableTable.resizeColumnsToContents
    
  def selectionChanged( self ):
    row = self.variableTable.currentRow()
    if row < 0 or row >= self.variableTable.rowCount() or \
    self.variableTable.rowCount() < 1:
      self.save.setEnabled( False )
      self.rm.setEnabled( False )
      self.canvas.setEnabled( False )
      self.export.setEnabled( False )
    else:
      itemName, itemType = self.getVariableInfo( row )
      self.save.setEnabled( True )
      self.rm.setEnabled( True )
      self.export.setEnabled( True )
      if itemType in QVariableTable.VECTORTYPES:
        self.canvas.setEnabled( True )
      else:
        self.canvas.setEnabled( False )

  def removeVariable( self ):
    row = self.variableTable.currentRow()
    if row < 0:
      return False
    itemName, itemType = self.getVariableInfo( row )
    self.sendCommands( QString( 'rm(' + itemName + ')' ) )
      
  def exportVariable( self ):
    row = self.variableTable.currentRow()
    if row < 0:
      return False
    itemName, itemType = self.getVariableInfo( row )
    if itemType in QVariableTable.VECTORTYPES or \
    itemType in QVariableTable.RASTERTYPES:
      self.parent.exportRObjects( True, itemName, itemType, False )
    else:
      #self.connect( fd, SIGNAL( "filterSelected(QString)" ), self.setFilter )
      fd = QFileDialog( self.parent, "Save data to file", "", \
      "Comma separated (*.csv);;Text file (*.txt);;All files (*.*)" )
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
      command = QString( 'write.table( ' + itemName + ', file = "' + selectedFile )
      command.append( QString( '", append = FALSE, quote = TRUE, sep = ",", eol = "\\n", na = "NA"' ) )
      command.append( QString( ', dec = ".", row.names = FALSE, col.names = TRUE, qmethod = "escape" )' ) )
      self.sendCommands( command )
    self.parent.label.setText( "Data saved" )
   
  def saveVariable( self ):
    row = self.variableTable.currentRow()
    if row < 0:
      return False
    itemName, itemType = self.getVariableInfo( row )
    fd = QFileDialog( self.parent, "Save data to file", "", \
    "R data file (*.Rda)" )
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
    commands = QString( 'save(' + itemName )
    commands.append( QString( ', file="' + selectedFile + '")' ) )
    self.sendCommands( commands )
    self.parent.label.setText( "Variable saved" )
    
  def exportToCanvas( self ):
    row = self.variableTable.currentRow()
    if row < 0:
      return False
    itemName, itemType = self.getVariableInfo( row )
    if itemType in QVariableTable.VECTORTYPES:
      self.parent.exportRObjects( False, itemName, itemType, False )
      self.parent.label.setText( "Exported to canvas" )
    else:
      return False

  def importFromCanvas( self ):
    mlayer = self.parent.mapCanvas.currentLayer()
    self.parent.importRObjects( mlayer, False )
    return True
      
  def loadRVariable( self ):
    dialog = QFileDialog( self, "Load R variable(s) from file", "" )
    dialog.setAcceptMode( QFileDialog.AcceptOpen )
    if dialog.exec_() == QDialog.Rejected:
      return False
    selectedFile = QString( dialog.selectedFiles().first() )
    if selectedFile.length() == 0:
      return False
    self.sendCommands( QString( 'load("' + selectedFile + '")' ) )
    self.parent.label.setText( "Variable(s) loaded" )
    
  def getVariableInfo( self, row ):
    item_name = self.variableTable.item( row, 0 )
    item_name = item_name.data( Qt.DisplayRole ).toString()
    item_type = self.variableTable.item( row, 1 )
    item_type = item_type.data( Qt.DisplayRole ).toString()
    return ( item_name, item_type )
    
  def sendCommands( self, commands ):
    if not commands.isEmpty():
      mime = QMimeData()
      mime.setText( commands )
      self.parent.console.insertFromMimeData( mime )
      self.parent.runCommand( commands )

class QLibraryTable( QWidget ):
  '''
  QLibraryTable Class:
  Description to be added
  '''
  #VECTORTYPES = [ "SpatialPointsDataFrame",
    #"SpatialPolygonsDataFrame",
    #"SpatialLinesDataFrame" ]
  #RASTERTYPES = [ "SpatialGridDataFrame",
    #"SpatialPixelsDataFrame" ]

  def __init__( self, parent ):
    QWidget.__init__( self, parent )
    # initialise standard settings
    self.setMinimumSize( 30, 30 )
    self.parent = parent
    
    self.libraryTable = QTableWidget( 0, 2, self )
    labels = QStringList()
    labels.append( "Name" )
    labels.append( "Type" )
    self.variableTable.setHorizontalHeaderLabels( labels )
    self.variableTable.horizontalHeader().setResizeMode( 1, QHeaderView.Stretch )
    self.variableTable.setShowGrid( True )
    self.variableTable.setSelectionBehavior( QAbstractItemView.SelectRows )
    self.variableTable.setSelectionMode( QAbstractItemView.SingleSelection )
    self.label = QLabel()
    self.label.setText( "Variables list" )
    
    self.rm = QToolButton( self )
    self.rm.setText( "rm" )
    self.rm.setToolTip( "Remove selected variable" )
    self.rm.setWhatsThis( "Removed selected variable" )
    self.rm.setIcon( QIcon( ":mActionVariableRemove.png" ) )
    self.rm.setEnabled( False )
    self.rm.setAutoRaise( True )
    
    self.export = QToolButton( self )
    self.export.setText( "export" )
    self.export.setToolTip( "Export data to file" )
    self.export.setWhatsThis( "Export data to file" )
    self.export.setIcon( QIcon( ":mActionVariableExport.png" ) )
    self.export.setEnabled( False )
    self.export.setAutoRaise( True )
    
    self.canvas = QToolButton( self )
    self.canvas.setText( "canvas" )
    self.canvas.setToolTip( "Export layer to map canvas" )
    self.canvas.setWhatsThis( "Export layer to map canvas" )
    self.canvas.setIcon( QIcon( ":mActionVariableCanvas.png" ) )
    self.canvas.setEnabled( False )
    self.canvas.setAutoRaise( True )

    self.layer = QToolButton( self )
    self.layer.setText( "layer" )
    self.layer.setToolTip( "Import layer from map canvas" )
    self.layer.setWhatsThis( "Import layer from map canvas" )
    self.layer.setIcon( QIcon( ":mActionVariableLayer.png" ) )
    self.layer.setEnabled( True )
    self.layer.setAutoRaise( True )
    
    self.save = QToolButton( self )
    self.save.setText( "save" )
    self.save.setToolTip( "Save R variable to file" )
    self.save.setWhatsThis( "Save R variable to file" )
    self.save.setIcon( QIcon( ":mActionVariableSave.png" ) )
    self.save.setEnabled( False )
    self.save.setAutoRaise( True )
    
    self.load = QToolButton( self )
    self.load.setText( "load" )
    self.load.setToolTip( "Load R variable(s) from file" )
    self.load.setWhatsThis( "Load R variable(s) from file" )
    self.load.setIcon( QIcon( ":mActionVariableLoad.png" ) )
    self.load.setEnabled( True )
    self.load.setAutoRaise( True )
    
    grid = QGridLayout( self )
    horiz = QHBoxLayout()
    horiz.addWidget( self.label)
    horiz.addWidget( self.rm )
    horiz.addWidget( self.export )
    horiz.addWidget( self.canvas )
    horiz.addWidget( self.layer )
    horiz.addWidget( self.save )
    horiz.addWidget( self.load )
    #grid.addWidget( self.label )
    grid.addLayout( horiz, 0, 0, 1, 1 )
    grid.addWidget( self.variableTable, 1, 0, 1, 1 )
    
    self.variables = dict()
    self.connect( self.rm, SIGNAL( "clicked()" ), self.removeVariable )
    self.connect( self.export, SIGNAL( "clicked()" ), self.exportVariable )
    self.connect( self.save, SIGNAL( "clicked()" ), self.saveVariable )
    self.connect( self.canvas, SIGNAL( "clicked()" ), self.exportToCanvas )
    self.connect( self.load, SIGNAL( "clicked()" ), self.loadRVariable )
    self.connect( self.layer, SIGNAL( "clicked()" ), self.importFromCanvas )
    self.connect( self.variableTable, \
    SIGNAL( "itemSelectionChanged()" ), self.selectionChanged )

  def updateVariables( self, variables ):
    self.variables = {}
#    self.variableTable.clearContents()
    while self.variableTable.rowCount() > 0:
      self.variableTable.removeRow( 0 )
    for variable in variables[0].items():
      self.addVariable( variable )

  def addVariable( self, variable ):
    self.variables[ variable[ 0 ] ] = variable[ 1 ]
    nameItem = QTableWidgetItem( QString(variable[ 0 ]) )
    nameItem.setFlags( Qt.ItemIsSelectable|Qt.ItemIsEnabled )
    typeItem = QTableWidgetItem( QString(variable[ 1 ]) )
    typeItem.setTextAlignment( Qt.AlignRight | Qt.AlignVCenter )
    typeItem.setFlags( Qt.ItemIsSelectable|Qt.ItemIsEnabled )
    row = self.variableTable.rowCount()
    self.variableTable.insertRow( row )
    self.variableTable.setItem( row, 0, nameItem )
    self.variableTable.setItem( row, 1, typeItem )
    self.variableTable.resizeColumnsToContents
    
  def selectionChanged( self ):
    row = self.variableTable.currentRow()
    if row < 0 or row >= self.variableTable.rowCount() or \
    self.variableTable.rowCount() < 1:
      self.save.setEnabled( False )
      self.rm.setEnabled( False )
      self.canvas.setEnabled( False )
      self.export.setEnabled( False )
    else:
      itemName, itemType = self.getVariableInfo( row )
      self.save.setEnabled( True )
      self.rm.setEnabled( True )
      self.export.setEnabled( True )
      if itemType in QVariableTable.VECTORTYPES:
        self.canvas.setEnabled( True )
      else:
        self.canvas.setEnabled( False )

  def removeVariable( self ):
    row = self.variableTable.currentRow()
    if row < 0:
      return False
    itemName, itemType = self.getVariableInfo( row )
    self.sendCommands( QString( 'rm(' + itemName + ')' ) )
      
  def exportVariable( self ):
    row = self.variableTable.currentRow()
    if row < 0:
      return False
    itemName, itemType = self.getVariableInfo( row )
    if itemType in QVariableTable.VECTORTYPES or \
    itemType in QVariableTable.RASTERTYPES:
      self.parent.exportRObjects( True, itemName, itemType, False )
    else:
      #self.connect( fd, SIGNAL( "filterSelected(QString)" ), self.setFilter )
      fd = QFileDialog( self.parent, "Save data to file", "", \
      "Comma separated (*.csv);;Text file (*.txt);;All files (*.*)" )
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
      command = QString( 'write.table( ' + itemName + ', file = "' + selectedFile )
      command.append( QString( '", append = FALSE, quote = TRUE, sep = ",", eol = "\\n", na = "NA"' ) )
      command.append( QString( ', dec = ".", row.names = FALSE, col.names = TRUE, qmethod = "escape" )' ) )
      self.sendCommands( command )
    self.parent.label.setText( "Data saved" )
   
  def saveVariable( self ):
    row = self.variableTable.currentRow()
    if row < 0:
      return False
    itemName, itemType = self.getVariableInfo( row )
    fd = QFileDialog( self.parent, "Save data to file", "", \
    "R data file (*.Rda)" )
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
    commands = QString( 'save(' + itemName )
    commands.append( QString( ', file="' + selectedFile + '")' ) )
    self.sendCommands( commands )
    self.parent.label.setText( "Variable saved" )
    
  def exportToCanvas( self ):
    row = self.variableTable.currentRow()
    if row < 0:
      return False
    itemName, itemType = self.getVariableInfo( row )
    if itemType in QVariableTable.VECTORTYPES:
      self.parent.exportRObjects( False, itemName, itemType, False )
      self.parent.label.setText( "Exported to canvas" )
    else:
      return False

  def importFromCanvas( self ):
    mlayer = self.parent.mapCanvas.currentLayer()
    self.parent.importRObjects( mlayer, False )
    return True
      
  def loadRVariable( self ):
    dialog = QFileDialog( self, "Load R variable(s) from file", "" )
    dialog.setAcceptMode( QFileDialog.AcceptOpen )
    if dialog.exec_() == QDialog.Rejected:
      return False
    selectedFile = QString( dialog.selectedFiles().first() )
    if selectedFile.length() == 0:
      return False
    self.sendCommands( QString( 'load("' + selectedFile + '")' ) )
    self.parent.label.setText( "Variable(s) loaded" )
    
  def getVariableInfo( self, row ):
    item_name = self.variableTable.item( row, 0 )
    item_name = item_name.data( Qt.DisplayRole ).toString()
    item_type = self.variableTable.item( row, 1 )
    item_type = item_type.data( Qt.DisplayRole ).toString()
    return ( item_name, item_type )
    
  def sendCommands( self, commands ):
    if not commands.isEmpty():
      mime = QMimeData()
      mime.setText( commands )
      self.parent.console.insertFromMimeData( mime )
      self.parent.runCommand( commands )