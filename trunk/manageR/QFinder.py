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
    horiz = QHBoxLayout( self )
    horiz.addWidget( self.edit )
    horiz.addWidget( self.previous )
    horiz.addWidget( self.next )
#    horiz.addWidget( self.close )
    self.setFocusProxy( self.edit )
    self.setVisible( False )
    self.setMaximumSize( QSize( 300, 50 ) )
    self.setSizePolicy( QSizePolicy.Maximum, QSizePolicy.Fixed )
    
    self.connect( self.next, SIGNAL( "clicked()" ), self.findNext )
    self.connect( self.previous, SIGNAL( "clicked()" ), self.findPrevious )
#    self.connect( self.close, SIGNAL( "clicked()" ), self.hide )
    self.connect( self.edit, SIGNAL( "returnPressed()" ), self.findNext )
    
  def find( self, forward ):
    current = self.parent.tabs.tabText( self.parent.tabs.currentIndex() )
    if current == "Script":
      document = self.parent.scripttab.scripting
    elif current == "Console":
      document = self.parent.console
    else:
      return False
    text = self.edit.text()
    found = False
    if text == "":
      return False
    else:
      if not forward:
        flags = ( QTextDocument.FindWholeWords | QTextDocument.FindBackward )
        fromPos = document.toPlainText().length() - 1
      else:
        flags = QTextDocument.FindWholeWords
        fromPos = 0
      if not document.find( text, flags ):
        cursor = QTextCursor( document.textCursor() )
        selection = cursor.hasSelection()
        if selection:
          start = cursor.selectionStart()
          end = cursor.selectionEnd()
        else:
          pos = cursor.position()
        cursor.setPosition( fromPos )
        document.setTextCursor( cursor )
        if not document.find( text, flags ):
          if selection:
              cursor.setPosition(start, QTextCursor.MoveAnchor)
              cursor.setPosition(end, QTextCursor.KeepAnchor)
          else:
              cursor.setPosition( pos )
          document.setTextCursor( cursor )
          return False
        elif selection:
          cursor = QTextCursor( document.textCursor() )
          if start == cursor.selectionStart():
            return False
    return True
        
  def findNext( self ):
    self.find( True )
    
  def findPrevious( self ):
    self.find( False )
        
  def hide( self ):
    self.setVisible( False )
    return True
    
  def show( self ):
    self.setVisible( True )
    self.setFocus()
    return True
    
  def toggle( self ):
    if not self.isVisible():
      return self.show()
    else:
      return self.hide()
