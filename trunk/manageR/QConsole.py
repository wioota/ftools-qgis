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

class QConsole( QTextEdit ):
  '''
  QConsole Class:
  This class is used to simulate a console application using 
  the QTextEdit widget. It supports a command history, and the 
  ability to define where the console commands are sent, making 
  it useful for any number of console based applications (i.e R)
  '''
  # text type enumerator (sort-of)
  ERR_TYPE = 0
  OUT_TYPE = 1
  CMD_TYPE = 2
  def __init__( self, parent, function = None, \
    cmdColour = Qt.black, errColour = Qt.red, \
    outColour = Qt.blue ):
    QTextEdit.__init__( self, parent )
    # initialise standard settings
    self.setTextInteractionFlags( Qt.TextEditorInteraction )
    self.setMinimumSize( 30, 30 )
    self.parent = parent
    self.setTextFont()
    self.setUndoRedoEnabled( False )
    self.setAcceptRichText( False )
    self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )
    self.scrollbar = self.verticalScrollBar()
    # initialise required variables
    self.history = QStringList()
    self.historyIndex = 0
    self.runningCommand = QString()
    self.setOuputColors( errColour, outColour )
    self.highlightingStatus = True
    # prepare prompt
    self.reset()
    self.setPrompt()
    self.cursor = self.textCursor()
    self.function = function
    #QObject.connect( self, SIGNAL( "textChanged()" ), self.moveToEnd )

  def reset( self ):
    '''
    Clear and reset console history and display
    '''
    # clear all contents
    self.clear()
    # init attributes
    self.runningCommand.clear()
    self.historyIndex = 0
    self.history.clear()

  def setTextFont( self, font = "Monospace" ):
    '''
    Sets the console display font
    Default is Monospace size 10
    Note: it is recommended to use a fixed width font
    '''
    #set the style of the underlying document
    font = QFont( "Monospace" , 10, QFont.Normal )
    font.setFixedPitch( True )
    self.setFont( font )
    self.document().setDefaultFont( font )
    
  def setOuputColors( self, err, out ):
    if isinstance( err, QColor ):
      self.errColour = err
    else:
      self.errColour = Qt.red
    if isinstance( out, QColor ):
      self.outColour = out
    else:
      self.outColour = Qt.blue
      
  def setDefaultColor( self, color ):
    if isinstance( color, QColor ):
      self.setTextColor( color )
      self.defaultColour = color
    
  def setPrompt( self, newPrompt = "> ", alternatePrompt = "+ ", display = False ):
    '''
    Sets console prompt style
    If display is true, prompt is displayed immediately
    Default prompt is '>' (R style)
    '''
    self.defaultPrompt = newPrompt
    self.alternatePrompt = alternatePrompt
    self.currentPrompt = self.defaultPrompt
    self.currentPromptLength = len( self.currentPrompt )
    if display:
      self.setTextColor( self.defaultColour )
      self.displayPrompt()

  def switchPrompt( self, default = True ):
    if default:
      self.currentPrompt = self.defaultPrompt
    else:
      self.currentPrompt = self.alternatePrompt
    self.currentPromptLength = len( self.currentPrompt )

  def displayPrompt( self ):
    '''
    Displays console prompt specified by setPrompt
    Prompt is display in colour specified by cmdColour
    '''
    self.runningCommand.clear()
    self.setTextColor( self.defaultColour )
    self.append( self.currentPrompt )
    self.moveCursor( QTextCursor.End, QTextCursor.MoveAnchor )
    self.parent.label.setText( " " ) # this is not very generic, better way to do this?

  def keyPressEvent( self, e ):
    '''
    Reimplemented key press event:
    Used to control cursor movement with console
    Movement should be limited to the edition zone
    '''
    self.cursor = self.textCursor()
    # if the cursor isn't in the edition zone, don't do anything
    if not self.isCursorInEditionZone():
      if e.key() == Qt.Key_C and ( e.modifiers() == Qt.ControlModifier or \
         e.modifiers() == Qt.MetaModifier ):
        QTextEdit.keyPressEvent( self, e )
      if self.cursor.blockNumber() == self.document().blockCount()-1 and \
         self.cursor.columnNumber() < self.currentPromptLength:
        self.cursor.select( QTextCursor.LineUnderCursor )
        self.cursor.removeSelectedText()
        self.cursor.insertText( self.currentPrompt )
    else:
      if self.cursor.columnNumber() >= self.currentPromptLength and self.cursor.anchor:
        # if Ctrl + C is pressed, then undo the current command
        if e.key() == Qt.Key_C and ( e.modifiers() == Qt.ControlModifier or \
           e.modifiers() == Qt.MetaModifier ) and not self.cursor.hasSelection():
          self.runningCommand.clear()
          self.switchPrompt( True )
          self.displayPrompt()
          self.parent.label.setText( " " ) # this is not very generic, better way to do this?
        # if Return is pressed, then perform the commands
        elif e.key() == Qt.Key_Return:
          command = self.currentCommand()
          check = self.runningCommand.split("\n").last()
          if not self.runningCommand.isEmpty():
            if not command == check:
              self.runningCommand.append( command )
              self.updateHistory( command )
          else:
            if not command.isEmpty():
              self.runningCommand = command
              self.updateHistory( command )
            else:
              self.switchPrompt( True )
              self.displayPrompt()
          if e.modifiers() == Qt.ShiftModifier or \
            not self.checkBrackets( self.runningCommand ):
            self.switchPrompt( False )
            self.cursor.insertText( "\n" + self.currentPrompt )
            self.runningCommand.append( "\n" )
          else:
            if not self.runningCommand.isEmpty():
              command = self.runningCommand
            self.executeCommand( command, False )
            self.runningCommand.clear()
            self.switchPrompt( True )
            #self.displayPrompt()
          self.cursor.movePosition( QTextCursor.End, QTextCursor.MoveAnchor )
          self.moveToEnd()
        # if Up or Down is pressed
        elif e.key() == Qt.Key_Down or e.key() == Qt.Key_Up:
          # remove the current command
          self.cursor.select( QTextCursor.LineUnderCursor )
          self.cursor.removeSelectedText()
          self.cursor.insertText( self.currentPrompt )
          # update the historyIndex (up or down)
          if e.key() == Qt.Key_Down and self.historyIndex < len( self.history ):
            self.historyIndex += 1
          elif e.key() == Qt.Key_Up and self.historyIndex > 0:
            self.historyIndex -= 1
          # replace current command with one from the history
          if self.historyIndex == len( self.history ):
            self.insertPlainText( "" )
          else:
            self.insertPlainText( self.history[ self.historyIndex ] )
        # if backspace is pressed, delete until we get to the prompt
        elif e.key() == Qt.Key_Backspace:
          if not self.cursor.hasSelection() and \
             self.cursor.columnNumber() == self.currentPromptLength:
            return
          QTextEdit.keyPressEvent( self, e )
        # if the left key is pressed, move left until we get to the prompt
        elif e.key() == Qt.Key_Left and self.cursor.columnNumber() > self.currentPromptLength:
          if e.modifiers() == Qt.ShiftModifier:
            anchor = QTextCursor.KeepAnchor
          else:
            anchor = QTextCursor.MoveAnchor
          self.cursor.movePosition( QTextCursor.Left, anchor )
        # use normal operation for right key
        elif e.key() == Qt.Key_Right:
          if e.modifiers() == Qt.ShiftModifier:
            anchor = QTextCursor.KeepAnchor
          else:
            anchor = QTextCursor.MoveAnchor
          self.cursor.movePosition( QTextCursor.Right, anchor )
        # if home is pressed, move cursor to right of prompt
        elif e.key() == Qt.Key_Home:
          if e.modifiers() == Qt.ShiftModifier:
            anchor = QTextCursor.KeepAnchor
          else:
            anchor = QTextCursor.MoveAnchor
          self.cursor.movePosition( QTextCursor.StartOfLine, anchor, 1 )
          self.cursor.movePosition( QTextCursor.Right, anchor, self.currentPromptLength )
        # use normal operation for end key
        elif e.key() == Qt.Key_End:
          if e.modifiers() == Qt.ShiftModifier:
            anchor = QTextCursor.KeepAnchor
          else:
            anchor = QTextCursor.MoveAnchor
          self.cursor.movePosition( QTextCursor.EndOfLine, anchor, 1 )
        # use normal operation for all remaining keys
        else:
          QTextEdit.keyPressEvent( self, e )
      # if the cursor is behind the prompt, don't do anything
      else:
        return
    self.setTextCursor( self.cursor )
    self.ensureCursorVisible()
    
  def isHighlighting( self ):
    return self.highlightingStatus
    
  def enableHighlighting( self, status ):
    self.highlightingStatus = status

  def checkBrackets( self, command ):
    s = str(command)
    s = filter(lambda x: x in '()[]{}"\'', s)
    s = s.replace ("'''", "'")
    s = s.replace ('"""', '"')
    instring = False
    brackets = {'(':')', '[':']', '{':'}', '"':'"', '\'':'\''}
    stack = []
    
    while len( s ):
        if not instring:
            if s[ 0 ] in ')]}':
                if stack and brackets[ stack[ -1 ] ] == s[ 0 ]:
                    del stack[ -1 ]
                else:
                    return False
            elif s[ 0 ] in '"\'':
                if stack and brackets[ stack[ -1 ] ] == s[ 0 ]:
                    del stack[ -1 ]
                    instring = False
                else:
                    stack.append( s[ 0 ] )
                    instring = True
            else:
                stack.append( s[ 0 ] )
        else:
            if s[ 0 ] in '"\'' and stack and brackets[ stack[ -1 ] ] == s[ 0 ]:
                del stack[ -1 ]
                instring = False
        s = s[ 1: ]
    return len( stack ) == 0

  def mousePressEvent( self, e ):
    self.cursor = self.textCursor()
    if e.button() == Qt.LeftButton:
      QTextEdit.mousePressEvent( self, e )
    elif ( not self.isCursorInEditionZone() or \
       ( self.isCursorInEditionZone() and \
       not self.isAnchorInEditionZone() ) ) and \
       e.button() == Qt.RightButton:
      QTextEdit.mousePressEvent( self, e )
      menu = self.createStandardContextMenu()
      actions = menu.actions()
      keep = [ 0, 1, 2, 3, 5, 6, 9, 10 ]
      count = 0
      for action in keep:
        menu.removeAction( actions[ action ] )
      menu.exec_( e.globalPos() )
    else:
      QTextEdit.mousePressEvent( self, e )
      
  def moveToEnd( self ):
#    self.scrollbar.setValue( self.scrollbar.maximum() )
#    self.update()
    cursor = self.textCursor()
    cursor.movePosition( QTextCursor.End, QTextCursor.MoveAnchor )
    self.setTextCursor( cursor )
#    self.ensureCursorVisible()
    self.emit( SIGNAL("textChanged()") )

  def insertFromMimeData( self, source ):
    self.cursor = self.textCursor()
    self.cursor.movePosition( QTextCursor.End, 
    QTextCursor.MoveAnchor, 1 )
    self.setTextCursor( self.cursor )
    if source.hasText():
      pastList = QStringList()
      pasteList = source.text().split("\n")
      self.runningCommand.append( source.text() )
      for line in pasteList:
        self.updateHistory( line )
    newSource = QMimeData()
    newSource.setText( source.text().replace( "\n", "\n"+self.alternatePrompt ) )
    QTextEdit.insertFromMimeData( self, newSource )
  
  def currentCommand( self ):
    '''
    Gets the currently entered command from the console
    Returns the command as a text string suitable for 
    sending to the interpreter
    '''
    block = self.cursor.block()
    text = block.text()
    return text.right( text.length()-self.currentPromptLength )

  def executeCommand( self, text, echo ):
    '''
    Sends the specified command to the console interpreter
    Emits 'runCommand' signal
    '''
    if not text.trimmed() == "":
      if echo:
        self.appendText( text )
      self.emit( SIGNAL( "executeCommand(PyQt_PyObject)" ), text )
#    else:
#      self.displayPrompt()
    

  def appendText( self, out_text, out_type ):
    '''
    Appends text to the console
    Text is coloured according to type:
    Error = 1, Command = 2, or Output = 0
    '''
    if out_type == QConsole.ERR_TYPE:
      self.setTextColor( self.errColour )
    elif out_type == QConsole.OUT_TYPE:
      self.setTextColor( self.outColour )
    else:
      self.setTextColor( self.defaultColour )
      pass
    if not out_text == "":
      self.append( out_text )
    cursor = self.textCursor()
    cursor.movePosition( QTextCursor.End, QTextCursor.MoveAnchor )
    self.setTextCursor( cursor )

  def isCursorInEditionZone( self ):
    '''
    Tests whether the cursor is in the edition zone or not
    Return True if yes, False otherwise
    '''
    self.cursor = self.textCursor()
    index = self.textCursor().columnNumber()
    row = self.textCursor().blockNumber()
    self.setTextCursor( self.cursor )
    return row == self.document().blockCount()-1 and index >= self.currentPromptLength
    
  def isAnchorInEditionZone( self ):
    self.cursor = self.textCursor()
    index = self.textCursor().columnNumber()
    block = self.document().lastBlock()
    row = self.cursor.anchor()
    return row >= ( block.position() + self.currentPromptLength )

  def updateHistory( self, command ):
    '''
    Updates the command history and its index
    '''
    if not command == "":
      self.history.append( command )
      self.historyIndex = len( self.history )


  def insertPlainText( self, text ):
    '''
    Redefines insert() slot to avoid 
    inserting text outside of the edition zone
    '''
    if self.isCursorInEditionZone():
      QTextEdit.insertPlainText( self, text )

class QScratchPad( QWidget ):
  def __init__( self, parent = None, function = None ):
    QWidget.__init__( self, parent )
    self.text_area = QTextEdit( self )
    self.push_button = QPushButton( "Execute Selected Text", self )
    self.function = function
    
    title = QLabel( "Scratch Pad" )
    vbox = QVBoxLayout()
    vbox.addWidget( title )
    vbox.addWidget( self.text_area )
    vbox.addWidget( self.push_button )
    self.setLayout(vbox)
    QObject.connect( self.push_button, SIGNAL( "clicked()" ), self.export )
    
  def export( self ):
    cursor = self.text_area.textCursor()
    if not self.function == None:
      self.function( cursor.selectedText() )  
