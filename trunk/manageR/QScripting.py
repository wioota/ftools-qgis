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

def whoami():
    "returns name of calling function"
    import sys
    return sys._getframe(1).f_code.co_name

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
    self.btn_parse.setText( "Execute command(s)" )
    self.btn_parse.setToolTip( "Send selected text to R console (Ctrl+R)" )
    self.btn_parse.setWhatsThis( "Send selected text to R console (Ctrl+R)" )
    self.info_label = QLabel( self )
    self.info_label.setVisible( True )
    self.info_label.setAlignment ( Qt.AlignHCenter )
    self.info_label.setWordWrap( True )
    
    self.save_file_as = QToolButton( self )
    self.save_file_as.setIcon( self.qgisThemeIcon( "mActionFileSaveAs.png" ) )
    self.save_file_as.setToolTip( "Save current R script as... (Ctrl+Shift+S)" )
    self.save_file = QToolButton( self )
    self.save_file.setIcon( self.qgisThemeIcon( "mActionFileSave.png" ) )
    self.save_file.setToolTip( "Save current R script (Ctrl+S)" )
    self.open_file = QToolButton( self )
    self.open_file.setIcon( self.qgisThemeIcon( "mActionFileOpen.png" ) )
    self.open_file.setToolTip( "Open existing R script (Ctrl+O)" )
    self.new_file = QToolButton( self )
    self.new_file.setIcon( self.qgisThemeIcon( "mActionFileNew.png" ) )
    self.new_file.setToolTip( "Create new R script (Ctrl+N)" )
    self.undo = QToolButton( self )
    self.undo.setIcon( self.qgisThemeIcon( "mActionUndo.png" ) )
    self.undo.setToolTip( "Undo last operation (Ctrl+Z)" )
    self.redo = QToolButton( self )
    self.redo.setIcon( self.qgisThemeIcon( "mActionRedo.png" ) )
    self.redo.setToolTip( "Redo last operation (Ctrl+Shift+Z)" )
    self.cut = QToolButton( self )
    self.cut.setIcon( self.qgisThemeIcon( "mActionEditCut.png" ) )
    self.cut.setToolTip( "Remove selected text to clipboard (Ctrl+X)" )
    self.copy = QToolButton( self )
    self.copy.setIcon( self.qgisThemeIcon( "mActionEditCopy.png" ) )
    self.copy.setToolTip( "Copy selected text to clipboard (Ctrl+C)" )
    self.paste = QToolButton( self )
    self.paste.setIcon( self.qgisThemeIcon( "mActionEditPaste.png" ) )
    self.paste.setToolTip( "Paste text from clipboard (Ctrl+V)" )
    frame_one = QFrame( self )
    frame_one.setFrameStyle( QFrame.VLine | QFrame.Sunken )
    frame_two = QFrame( self )
    frame_two.setFrameStyle( QFrame.VLine | QFrame.Sunken )

    grid = QGridLayout( self )
    grid.addWidget( self.info_label, 0, 0, 1, 3 )
    horiz = QHBoxLayout()
    horiz.addWidget( self.new_file )
    horiz.addWidget( self.open_file )
    horiz.addWidget( self.save_file )
    horiz.addWidget( self.save_file_as )
    horiz.addWidget( frame_one )
    horiz.addWidget( self.undo )
    horiz.addWidget( self.redo )
    horiz.addWidget( frame_two )
    horiz.addWidget( self.cut )
    horiz.addWidget( self.copy )
    horiz.addWidget( self.paste )
    grid.addLayout( horiz, 1, 0, 1, 2 )
    horiz_two = QHBoxLayout()
    horiz_two.addStretch()
    horiz_two.addWidget( self.btn_parse )
    grid.addLayout( horiz_two, 1, 2, 1, 1 )
    grid.addWidget( self.scripting, 2, 0, 1, 3 )
    
    self.connect( self.btn_parse, SIGNAL( "clicked()" ), self.parseCommands )
    self.connect( self.new_file, SIGNAL( "clicked()" ), self.newFile )
    self.connect( self.open_file, SIGNAL( "clicked()" ), self.openFile )
    self.connect( self.save_file, SIGNAL( "clicked()" ), self.save )
    self.connect( self.save_file_as, SIGNAL( "clicked()" ), self.saveFileAs )
    self.connect( self.undo, SIGNAL( "clicked()" ), self.scripting.undo )
    self.connect( self.redo, SIGNAL( "clicked()" ), self.scripting.redo )
    self.connect( self.cut, SIGNAL( "clicked()" ), self.scripting.cut )
    self.connect( self.copy, SIGNAL( "clicked()" ), self.scripting.copy )
    self.connect( self.paste, SIGNAL( "clicked()" ), self.scripting.paste )
    self.connect( self.scripting, SIGNAL( "textChanged()" ), \
    self.documentWasModified )
    self.setCurrentFile( "" )

  def newFile( self ):
    
    if self.maybeSave():
      self.scripting.clear()
      self.setCurrentFile( "" )
      
  def openFile( self ):
    
    if self.maybeSave():
      fileName = QFileDialog().getOpenFileName( self, \
      "Open R script", "", "R Script (*.R)" )
      if fileName.length() != 0:
        self.loadFile( fileName )

  def save( self ):
    
    if self.cur_file.length() == 0:
      return self.saveFileAs()
    else:
      return self.saveFile( self.cur_file )

  def saveFileAs( self ):
    
    fileName = QFileDialog().getSaveFileName( self, \
    "Save R script", "", "R Script (*.R)" )
    if not fileName.endsWith( ".R" ):
      fileName += ".R"
    if fileName.length() == 0:
      return False
    return self.saveFile( fileName )
    
  def documentWasModified( self ):
    
    if not self.info_label.text().startsWith( "*" ) and self.isVisible():
      self.info_label.setText( "*" + self.show_name )
      self.scripting.document().setModified( True )
    
  def maybeSave( self ):
    
    if self.scripting.document().isModified():
      ret = QMessageBox.warning( self.parent, "manageR", \
      "The R script has been modified.\nSave your changes?", \
      QMessageBox.Ok | QMessageBox.Discard | QMessageBox.Cancel )
      if ret == QMessageBox.Ok:
        return self.save()
      elif ret == QMessageBox.Cancel:
        return False
    return True
    
  def loadFile( self, fileName ):
    
    qfile = QFile( fileName )
    if not qfile.open( QIODevice.ReadOnly ):
      QMessageBox.warning( self, "manageR", "Cannot read file " + fileName )
      return
    in_file = QTextStream( qfile )
    QApplication.setOverrideCursor( QCursor( Qt.WaitCursor ) )
    self.scripting.setPlainText( in_file.readAll() )
    QApplication.restoreOverrideCursor()
    self.setCurrentFile( fileName )
    self.parent.label.setText( "File loaded" )
    
  def saveFile( self, fileName ):
    
    qfile = QFile( fileName )
    if not qfile.open( QIODevice.WriteOnly ):
      QMessageBox.warning( self, "manageR", "Cannot write file " + fileName )
      return False
    qfile_info = QFileInfo( qfile )
    qfile.close()
    QApplication.setOverrideCursor( QCursor( Qt.WaitCursor ) )
    out_file = open( qfile_info.filePath(), "w" )
    s = self.scripting.toPlainText()
    out_file.write( s )
    if s[-1:] != "\n":
      out_file.write( "\n" )
    out_file.flush()
    QApplication.restoreOverrideCursor()
    self.setCurrentFile( fileName )
    self.parent.label.setText( "File saved" )
    return True

  def setCurrentFile( self, fileName ):
    self.cur_file = QString( fileName )
    self.show_name = QString( "untitled.R" )
    if not self.cur_file.length() == 0:
      self.show_name = self.strippedName( self.cur_file ) + \
      " (" + self.strippedPath( self.cur_file ) + ")"
    self.info_label.setText( self.show_name )
    self.scripting.document().setModified( False )

  def strippedName( self, fullFileName ):
    
    return QString( QFileInfo( fullFileName ).fileName() )
    
  def strippedPath( self, fullFileName ):
    return QString( QFileInfo( fullFileName ).absolutePath() )
    
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
      commands = cursor.selectedText().replace( u"\u2029", "\n" )
    else:
      commands = self.scripting.toPlainText()
    if not commands.isEmpty():
      mime = QMimeData()
      mime.setText( commands )
      self.parent.console.insertFromMimeData( mime )
      self.parent.runCommand( commands )
      
  def keyPressEvent( self, e ):
    
    if ( e.modifiers() == ( Qt.ControlModifier|Qt.ShiftModifier ) or \
    e.modifiers() == ( Qt.MetaModifier|Qt.ShiftModifier) ) and e.key() == Qt.Key_S:
      self.saveFileAs()
    elif ( e.modifiers() == Qt.ControlModifier or \
    e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_S:
      self.save()
    elif ( e.modifiers() == Qt.ControlModifier or \
    e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_N:
      self.newFile()
    elif ( e.modifiers() == Qt.ControlModifier or \
    e.modifiers() == Qt.MetaModifier ) and e.key() == Qt.Key_O:
      self.openFile()
    else:
      QWidget.keyPressEvent( self, e )

