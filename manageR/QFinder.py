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

class QFinder( QWidget ):
  '''
  QFinder Class:
  Description to be added
  '''

  def __init__( self, parent ):
    QWidget.__init__( self, parent )
    # initialise standard settings
    self.parent = parent
    grid = QGridLayout( self )
    self.edit = QLineEdit( self )
    font = QFont( "Monospace" , 10, QFont.Normal )
    font.setFixedPitch( True )
    self.edit.setFont( font )
    self.edit.setToolTip( "Find text" )
    self.next = QToolButton( self )
    self.next.setText( ">" )
    self.next.setToolTip( "Find next" )
    self.previous = QToolButton( self )
    self.previous.setToolTip( "Find previous" )
    self.previous.setText( "<" )
    self.whole_words = QCheckBox()
    self.whole_words.setText( "Whole words only" )
    self.case_sensitive = QCheckBox()
    self.case_sensitive.setText( "Case sensitive" )
    self.find_horiz = QHBoxLayout()
    self.find_horiz.addWidget( self.edit )
    self.find_horiz.addWidget( self.previous )
    self.find_horiz.addWidget( self.next )
    grid.addWidget( self.whole_words, 0, 0, 1, 1 )
    grid.addWidget( self.case_sensitive, 0, 1, 1, 1 )
    grid.addLayout( self.find_horiz, 1, 0, 1, 2 )

    self.replace_edit = QLineEdit( self )
    self.replace_edit.setFont( font )
    self.replace_edit.setToolTip( "Replace text" )
    self.replace = QToolButton( self )
    self.replace.setText( "Replace" )
    self.replace.setToolTip( "Replace text" )
    self.replace_all = QToolButton( self )
    self.replace_all.setToolTip( "Replace all" )
    self.replace_all.setText( "Replace all" )
    self.replace_horiz = QHBoxLayout()
    self.replace_horiz.addWidget( self.replace_edit )
    self.replace_horiz.addWidget( self.replace )
    self.replace_horiz.addWidget( self.replace_all )
    grid.addLayout( self.replace_horiz, 2, 0, 1, 2 )
    self.setFocusProxy( self.edit )
    self.setVisible( False )
    self.edit.setMaximumSize( QSize( 300, 26 ) )
    self.edit.setSizePolicy( QSizePolicy.Maximum, QSizePolicy.Fixed )
    self.replace_edit.setMaximumSize( QSize( 300, 26 ) )
    self.replace_edit.setSizePolicy( QSizePolicy.Maximum, QSizePolicy.Fixed )
    
    self.connect( self.next, SIGNAL( "clicked()" ), self.findNext )
    self.connect( self.previous, SIGNAL( "clicked()" ), self.findPrevious )
    self.connect( self.replace, SIGNAL( "clicked()" ), self.replaceText )
    self.connect( self.edit, SIGNAL( "returnPressed()" ), self.findNext )
    self.connect( self.replace_all, SIGNAL( "clicked()" ), self.replaceAll )

  def setCurrentDocument( self, document, replace ):
    if not document is None:
      self.document = document
      if replace:
        self.showReplace()
      else:
        self.hideReplace()
    else:
      self.hide()

  def currentDocument( self ):
    return self.document
    
  def find( self, forward ):
    if not self.document:
      return False
    text = QString( self.edit.text() )
    found = False
    if text == "":
      return False
    else:
      flags = QTextDocument.FindFlag()
      if self.whole_words.isChecked():
        flags = ( flags | QTextDocument.FindWholeWords )
      if self.case_sensitive.isChecked():
        flags = ( flags | QTextDocument.FindCaseSensitively )
      if not forward:
        flags = ( flags | QTextDocument.FindBackward )
        fromPos = self.document.toPlainText().length() - 1
      else:
        fromPos = 0
      if not self.document.find( text, flags ):
        cursor = QTextCursor( self.document.textCursor() )
        selection = cursor.hasSelection()
        if selection:
          start = cursor.selectionStart()
          end = cursor.selectionEnd()
        else:
          pos = cursor.position()
        cursor.setPosition( fromPos )
        self.document.setTextCursor( cursor )
        if not self.document.find( text, flags ):
          if selection:
              cursor.setPosition(start, QTextCursor.MoveAnchor)
              cursor.setPosition(end, QTextCursor.KeepAnchor)
          else:
              cursor.setPosition( pos )
          self.document.setTextCursor( cursor )
          return False
        elif selection:
          cursor = QTextCursor( self.document.textCursor() )
          if start == cursor.selectionStart():
            return False
    return True
        
  def findNext( self ):
    return self.find( True )
    
  def findPrevious( self ):
    return self.find( False )
        
  def hide( self ):
    self.setVisible( False )
    if not self.document is None:
      self.document.setFocus()
    return True
    
  def show( self ):
    self.setVisible( True )
    self.setFocus()
    return True

  def showReplace( self ):
    self.replace_edit.setVisible( True )
    self.replace.setVisible( True )
    self.replace_all.setVisible( True )

  def hideReplace( self ):
    self.replace_edit.setVisible( False )
    self.replace.setVisible( False )
    self.replace_all.setVisible( False )
    
  def toggle( self ):
    if not self.isVisible():
      return self.show()
    else:
      return self.hide()

  def replaceText( self ):
    cursor = QTextCursor( self.document.textCursor() )
    selection = cursor.hasSelection()
    if selection:
      text = QString( cursor.selectedText() )
      current = QString( self.edit.text() )
      replace = QString( self.replace_edit.text() )
      if text == current:
        cursor.insertText( replace )
        cursor.select( QTextCursor.WordUnderCursor )
    else:
      return self.findNext()
    self.findNext()
    return True

  def replaceAll( self ):
    while self.findNext():
      self.replaceText()
    self.replaceText()