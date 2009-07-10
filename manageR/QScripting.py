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

class QScripting( QWidget ):
  '''
  QScripting Class:
  Description to be added
  '''

  def __init__( self, parent ):
    QWidget.__init__( self, parent )
    # initialise standard settings
    self.setMinimumSize( 30, 30 )
    self.parent = parent
    self.scripting = QTextEdit( self )
    self.scripting.setUndoRedoEnabled( True )
    self.scripting.setAcceptRichText( False )
    font = QFont( "Monospace" , 10, QFont.Normal )
    font.setFixedPitch( True )
    self.scripting.setFont( font )
    self.scripting.document().setDefaultFont( font )

    self.btn_parse = QToolButton( self )
    self.btn_parse.setText( "Execute commands(s)" )
    self.btn_parse.setToolTip( "Send selected text to R interpreter" )
    self.btn_parse.setWhatsThis( "Send selected text to R interpreter" )
    
    self.info_label = QLabel( self )
    self.info_label.setText( "" )
    self.info_label.setAlignment ( Qt.AlignHCenter )
    self.info_label.setWordWrap( True )
    
    self.save_file_as = QToolButton( self )
    self.save_file_as.setIcon( self.qgisThemeIcon( "mActionFileSaveAs.png" ) )
    self.save_file = QToolButton( self )
    self.save_file.setIcon( self.qgisThemeIcon( "mActionFileSave.png" ) )
    self.open_file = QToolButton( self )
    self.open_file.setIcon( self.qgisThemeIcon( "mActionFileOpen.png" ) )
    self.new_file = QToolButton( self )
    self.new_file.setIcon( self.qgisThemeIcon( "mActionFileNew.png" ) )
    horiz = QHBoxLayout()
    grid = QGridLayout( self )
    grid.addWidget( self.info_label, 0, 0, 1, 3 )
    grid.addWidget( self.scripting, 1, 0, 1, 3 )
    horiz.addWidget( self.new_file )
    horiz.addWidget( self.open_file )
    horiz.addWidget( self.save_file )
    horiz.addWidget( self.save_file_as )
    grid.addLayout( horiz, 2, 0, 1, 1 )
    grid.addWidget( self.btn_parse, 2, 2, 1, 1 )
    self.setCurrentFile( "" )
    self.connect( self.btn_parse, SIGNAL( "clicked()" ), self.parseCommands )
    self.connect( self.new_file, SIGNAL( "clicked()" ), self.newFile )
    self.connect( self.open_file, SIGNAL( "clicked()" ), self.openFile )
    self.connect( self.save_file, SIGNAL( "clicked()" ), self.save )
    self.connect( self.save_file_as, SIGNAL( "clicked()" ), self.saveFileAs )
    
    self.connect( self.scripting.document(), SIGNAL( "contentsChanged()" ), \
    self.documentWasModified )

  def newFile( self ):
    if self.maybeSave():
      self.scripting.clear()
      self.setCurrentFile( "" )
      
  def openFile( self ):
    if self.maybeSave():
      fileName = QFileDialog().getOpenFileName( self )
      if fileName.length() != 0:
        self.loadFile( fileName )

  def save( self ):
    if self.cur_file.length() == 0:
      return self.saveFileAs()
    else:
      return self.saveFile( self.cur_file )

  def saveFileAs( self ):
    fileName = QFileDialog().getSaveFileName( self )
    if fileName.length() == 0:
      return False
    return self.saveFile( fileName )
    
  def documentWasModified( self ):
    self.info_label.setText( "*" + self.show_name )
    
  def documentNotModified( self ):
    self.info_label.setText( self.show_name )
    
  def maybeSave( self ):
    if self.scripting.document().isModified():
      ret = QMessageBox.warning( self.parent, "manageR", \
      "The document has been modified.\nSave your changes?", \
      QMessageBox.StandardButtons(QMessageBox.StandardButton.Ok, \
      QMessageBox.StandardButton.Discard, QMessageBox.StandardButton.Cancel ) )
      if ret == QMessageBox.StandardButton.Ok:
        return self.save()
      elif ret == QMessageBox.StandardButton.Cancel:
        return False
    return True
    
  def loadFile( self, fileName ):
    qfile = QFile( fileName )
    if not qfile.open( QFile.OpenMode( QFile.OpenModeFlag.ReadOnly, \
    QFile.OpenModeFlag.Text ) ):
      QMessageBox.warning( self, "manageR", "Cannot read file " + fileName )
      return
    in_file = QTextStream( qfile )
    QApplication.setOverrideCursor( QCursor( Qt.CursorShape.WaitCursor ) )
    self.scripting.setPlainText( in_file.readAll() )
    QApplication.restoreOverrideCursor()
    self.setCurrentFile( fileName )
    self.parent.label.setText( "File loaded" )
    
  def saveFile( self, fileName ):
    qfile = QFile( fileName )
    if not qfile.open( QFile.OpenMode( QFile.OpenModeFlag.WriteOnly, \
    QFile.OpenModeFlag.Text ) ):
      QMessageBox.warning( self, "manageR", "Cannot write file " + fileName )
      return False
    out_file = QTextStream( qfile )
    QApplication.setOverrideCursor( QCursor( Qt.CursorShape.WaitCursor ) )
    out_file.writeString( self.scripting.toPlainText() )
    QApplication.restoreOverrideCursor()
    self.setCurrentFile( fileName )
    self.parent.label.setText( "File saved" )
    qfile.close()

  def setCurrentFile( self, fileName ):
    self.cur_file = QString( fileName )
    self.show_name = "untitled.R"
    self.scripting.document().setModified( False )
    if not self.cur_file.length() == 0:
      self.shown_name = self.strippedName( self.cur_file )

  def strippedName( self, fullFileName ):
    return QFileInfo( fullFileName ).fileName()
    
  def qgisThemeIcon( self, icon_name ):
    myPreferredPath = QgsApplication.activeThemePath() + QDir.separator() + icon_name
    myDefaultPath = QgsApplication.defaultThemePath() + QDir.separator() + icon_name
    if QFile( myPreferredPath ).exists():
      return QIcon( myPreferredPath )
    elif QFile( myDefaultPath ).exists():
      return QIcon( myDefaultPath )
    else:
      return QIcon()

  def parseCommands( self ):
    cursor = self.scripting.textCursor()
    if cursor.hasSelection():
      commands = cursor.selectedText()
    else:
      commands = self.scripting.toPlainText()
    if not commands.isEmpty():
      mime = QMimeData()
      mime.setText( commands )
      self.parent.console.insertFromMimeData( mime )
      self.parent.runCommand( commands )
      
  def keyPressEvent( self, e ):
    '''
    Reimplemented key press event:
    CTRL-R to export selected (or all if no selection) 
    commands to the R console
    '''
    if ( e.modifiers() == Qt.ControlModifier or e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_R:
      self.parseCommands()
    else:
      QWidget.keyPressEvent( self, e )

