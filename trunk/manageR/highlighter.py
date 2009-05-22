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

class RHighlighter( QSyntaxHighlighter ):

    def __init__( self, parent, theme ):
      QSyntaxHighlighter.__init__( self, parent )
      self.theme = theme
      self.parent = parent
      keyword = QTextCharFormat()
      reservedClasses = QTextCharFormat()
      assignmentOperator = QTextCharFormat()
      delimiter = QTextCharFormat()
      specialConstant = QTextCharFormat()
      boolean = QTextCharFormat()
      #integerNumber = QTextCharFormat()
      #floatingPoint = QTextCharFormat()
      number = QTextCharFormat()
      comment = QTextCharFormat()
      string = QTextCharFormat()
      singleQuotedString = QTextCharFormat()
      
      #parent.setPalette( QPalette( self.getThemeColor( "background" ), self.getThemeColor( "background" ) ) )
      background = self.getThemeColor( "background" )
      self.parent.setStyleSheet( "QTextEdit { background-color: " + background + " }")
      self.parent.setDefaultColor( QColor( self.getThemeColor( "foreground" ) ) )
      self.parent.setOuputColors( QColor( self.getThemeColor( "error" ) ), \
      QColor( self.getThemeColor( "output") ) )
      
      self.highlightingRules = []

      # keyword
      brush = QBrush( self.getThemeColor( "keyword" ), Qt.SolidPattern )
      keyword.setForeground( brush )
      keyword.setFontWeight( QFont.Bold )
      keywords = QStringList( [ "break", "else", "for", "if", "in", 
                                "next", "repeat", "return", "switch", 
                                "try", "while" ] )
      for word in keywords:
        pattern = QRegExp("\\b" + word + "\\b")
        rule = HighlightingRule( pattern, keyword )
        self.highlightingRules.append( rule )

      # reservedClasses
      reservedClasses.setForeground( brush )
      reservedClasses.setFontWeight( QFont.Bold )
      keywords = QStringList( [ "array", "character", "complex", 
                                "data.frame", "double", "factor", 
                                "function", "integer", "list", 
                                "logical", "matrix", "numeric", 
                                "vector" ] )
      for word in keywords:
        pattern = QRegExp("\\b" + word + "\\b")
        rule = HighlightingRule( pattern, reservedClasses )
        self.highlightingRules.append( rule )


      # assignmentOperator
      brush = QBrush( self.getThemeColor( "operator" ), Qt.SolidPattern )
      pattern = QRegExp( "(<){1,2}-" )
      assignmentOperator.setForeground( brush )
      assignmentOperator.setFontWeight( QFont.Bold )
      rule = HighlightingRule( pattern, assignmentOperator )
      self.highlightingRules.append( rule )
      
      # delimiter
      pattern = QRegExp( "[\)\(]+|[\{\}]+|[][]+" )
      delimiter.setForeground( brush )
      delimiter.setFontWeight( QFont.Bold )
      rule = HighlightingRule( pattern, delimiter )
      self.highlightingRules.append( rule )

      # specialConstant
      brush = QBrush( self.getThemeColor( "value" ), Qt.SolidPattern )
      specialConstant.setForeground( brush )
      keywords = QStringList( [ "Inf", "NA", "NaN", "NULL" ] )
      for word in keywords:
        pattern = QRegExp("\\b" + word + "\\b")
        rule = HighlightingRule( pattern, specialConstant )
        self.highlightingRules.append( rule )

      # boolean
      boolean.setForeground( brush )
      keywords = QStringList( [ "TRUE", "FALSE" ] )
      for word in keywords:
        pattern = QRegExp("\\b" + word + "\\b")
        rule = HighlightingRule( pattern, boolean )
        self.highlightingRules.append( rule )

      # number
      pattern = QRegExp( "[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?" )
      pattern.setMinimal( True )
      number.setForeground( brush )
      rule = HighlightingRule( pattern, number )
      self.highlightingRules.append( rule )

      # comment
      brush = QBrush( self.getThemeColor( "comment" ), Qt.SolidPattern )
      pattern = QRegExp( "#[^\n]*" )
      comment.setForeground( brush )
      rule = HighlightingRule( pattern, comment )
      self.highlightingRules.append( rule )

      # string
      brush = QBrush( self.getThemeColor( "string" ), Qt.SolidPattern )
      pattern = QRegExp( "\".*\"" )
      pattern.setMinimal( True )
      string.setForeground( brush )
      rule = HighlightingRule( pattern, string )
      self.highlightingRules.append( rule )
      
      # singleQuotedString
      pattern = QRegExp( "\'.*\'" )
      pattern.setMinimal( True )
      singleQuotedString.setForeground( brush )
      rule = HighlightingRule( pattern, singleQuotedString )
      self.highlightingRules.append( rule )
      
    def getThemeColor( self, style ):
      if style == "keyword" or style == "operator":
        if self.theme == "Cobalt":
          return QColor( 255, 165, 0 )
        elif self.theme == "Matrix":
          return Qt.green
        elif self.theme == "Oblivion":
          return Qt.white
        else:
          return Qt.darkBlue
      elif style == "comment":
        if self.theme == "Cobalt":
          return QColor( "#0065bf" )
        elif self.theme == "Matrix":
          return Qt.green
        elif self.theme == "Oblivion":
          return Qt.gray
        else:
          return Qt.blue
      elif style == "value":
        if self.theme == "Cobalt":
          return QColor( "#80ffbb" )
        elif self.theme == "Matrix":
          return Qt.green
        elif self.theme == "Oblivion":
          return QColor( 154, 205, 50 )
        else:
          return Qt.darkGray
      elif style == "string":
        if self.theme == "Cobalt":
          return QColor( "#3ad900" )
        elif self.theme == "Matrix":
          return Qt.green
        elif self.theme == "Oblivion":
          return QColor( 255, 165, 0 )
        else:
          return QColor( 255, 20, 147 )
      elif style == "foreground":
        if self.theme == "Cobalt":
          return Qt.white
        elif self.theme == "Matrix":
          return Qt.green
        elif self.theme == "Oblivion":
          return Qt.lightGray
        else:
          return Qt.black
      elif style == "background":
        if self.theme == "Cobalt":
          return "#001b33"
        elif self.theme == "Matrix":
          return "black"
        elif self.theme == "Oblivion":
          return "#2e3436"
        else:
          return "white"
      elif style == "output":
        if self.theme == "Cobalt":
          return Qt.darkGray
        elif self.theme == "Matrix":
          return Qt.green
        elif self.theme == "Oblivion":
          return QColor( "#729fcf" )
        else:
          return "blue"
      elif style == "error":
        if self.theme == "Cobalt":
          return QColor( "#ff0044" )
        elif self.theme == "Matrix":
          return Qt.green
        elif self.theme == "Oblivion":
          return QColor( "#edd400" )
        else:
          return Qt.red
      

    def highlightBlock( self, text ):
      if not self.parent.isHighlighting():
        return
      for rule in self.highlightingRules:
        expression = QRegExp( rule.pattern )
        index = expression.indexIn( text )
        while index >= 0:
          length = expression.matchedLength()
          self.setFormat( index, length, rule.format )
          index = text.indexOf( expression, index + length )
      self.setCurrentBlockState( 0 )

class HighlightingRule():
  def __init__( self, pattern, format ):
    self.pattern = pattern
    self.format = format
    
class TestApp( QMainWindow ):
  def __init__(self):
    QMainWindow.__init__(self)
    #font = QFont()
    #font.setFamily( "Courier" )
    #font.setFixedPitch( True )
    #font.setPointSize( 10 )

    editor = TestEdit()
    #editor.setFont( font )
    highlighter = RHighlighter( editor, "Classic" )
#    highlighter.setDocument( editor.document() )
    
    self.setCentralWidget( editor )
    self.setWindowTitle( "Syntax Highlighter" )

class TestEdit (QTextEdit ):
  def __init__(self):
    QTextEdit.__init__(self)
    
  def setDefaultColor( self, color ):
    if isinstance( color, QColor ):
      self.setTextColor( color )
      self.defaultColour = color

  def setOuputColors( self, err, out ):
    if isinstance( err, QColor ):
      self.errColour = err
    else:
      self.errColour = Qt.red
    if isinstance( out, QColor ):
      self.outColour = out
    else:
      self.outColour = Qt.blue
      
  def isHighlighting( self ):
    return True

if __name__ == "__main__":
  app = QApplication( sys.argv )
  window = TestApp()
  window.show()
  sys.exit( app.exec_() )

