import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtXml import QDomDocument

class CommandCompletion( QObject ):

  def __init__( self, parent, commandList, delay = 500, statusBar = None ):
    QObject.__init__( self, parent )
    self.editor = parent
    self.statusBar = statusBar
    self.popup = QTreeWidget()
    self.popup.setColumnCount(1)
    self.popup.setUniformRowHeights(True)
    self.popup.setRootIsDecorated(False)
    self.popup.setEditTriggers(QTreeWidget.NoEditTriggers)
    self.popup.setSelectionBehavior(QTreeWidget.SelectRows)
    self.popup.setFrameStyle(QFrame.Box | QFrame.Plain)
    self.popup.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.popup.header().hide()
    self.popup.installEventFilter(self)
    self.popup.setMouseTracking(True)
    self.connect(self.popup, SIGNAL("itemClicked(QTreeWidgetItem*, int)"), self.doneCompletion)
    self.popup.setWindowFlags(Qt.Popup)
    self.popup.setFocusPolicy(Qt.NoFocus)
    self.popup.setFocusProxy(self.editor)
    self.choices = QStringList()
    if isinstance( commandList, str ):
      self.loadSuggestions( commandList )
    elif isinstance( commandList, QStringList ):
      self.choices = commandList
    else:
      return
    self.timer = QTimer(self)
    self.timer.setSingleShot(True)
    if type( delay ) == type( 500 ):
      self.timer.setInterval(delay)
    else:
      self.timer.setInterval(500)
    self.connect(self.timer, SIGNAL("timeout()"), self.autoSuggest)
    self.connect(self.editor, SIGNAL("textChanged()"), self.startTimer)

  def startTimer( self ):
    self.timer.start()
    
  def eventFilter(self, obj, ev):
    if not obj == self.popup:
      return False
    if ev.type() == QEvent.MouseButtonPress:
      self.popup.hide()
      self.editor.setFocus()
      return True
    if ev.type() == QEvent.KeyPress:
      consumed = False
      key = ev.key()
      if key == Qt.Key_Enter or key == Qt.Key_Return:
        self.doneCompletion()
        consumed = True
      elif key == Qt.Key_Escape:
        self.editor.setFocus()
        self.popup.hide()
        consumed = True
      elif key == Qt.Key_Up or \
      key == Qt.Key_Down or \
      key == Qt.Key_Home or \
      key == Qt.Key_End or \
      key == Qt.Key_PageUp or \
      key == Qt.Key_PageDown:
        pass
      else:
        self.editor.setFocus()
        self.editor.event(ev)
        self.popup.hide()
      return consumed
    return False

  def showCompletion( self, choices ):

    if choices.isEmpty():
      return

    pal = self.editor.palette()
    color = pal.color(QPalette.Disabled, QPalette.WindowText)

    self.popup.setUpdatesEnabled(False)
    self.popup.clear()
    for i in choices:
      item = QTreeWidgetItem(self.popup)
      item.setText(0, i.split(":")[0].simplified())
      try:
        item.setData(0, Qt.StatusTipRole, QVariant( i.split(":")[1].simplified() ) )
      except:
        pass
    self.popup.setCurrentItem(self.popup.topLevelItem(0))
    self.popup.resizeColumnToContents(0)
    self.popup.adjustSize()
    self.popup.setUpdatesEnabled(True)

    h = self.popup.sizeHintForRow(0) * min([7, choices.count()]) + 3
    self.popup.resize(self.popup.width(), h)

    self.popup.move(self.editor.mapToGlobal(self.editor.cursorRect().bottomRight()))
    self.popup.setFocus()
    self.popup.show()

  def doneCompletion( self ):
    self.timer.stop()
    self.popup.hide()
    self.editor.setFocus()
    item = self.popup.currentItem()
    self.statusBar.setText( item.data( 0, \
    Qt.StatusTipRole ).toString().replace("function", item.text(0)) )
    if item:
      self.replaceCurrentWord(item.text(0))
    self.preventSuggest()

  def preventSuggest( self ):
    self.timer.stop()

  def autoSuggest( self ):
    text = self.getCurrentWord()
    if text.contains( QRegExp( "\\b+" ) ):
      self.showCompletion( self.choices.filter( QRegExp( "^" + text ) ) )
      
  def getCurrentWord( self ):
    textCursor = self.editor.textCursor()
    textCursor.movePosition( QTextCursor.StartOfWord, QTextCursor.KeepAnchor )
    currentWord = textCursor.selectedText()
    textCursor.setPosition( textCursor.anchor(), QTextCursor.MoveAnchor )
    return currentWord
    
  def replaceCurrentWord( self, word ):
    textCursor = self.editor.textCursor()
    textCursor.movePosition( QTextCursor.StartOfWord, QTextCursor.KeepAnchor )
    textCursor.insertText( word )
    
  def loadSuggestions( self, commandList ):
    QObject.__init__( self )
    document = QDomDocument( "mydocument" )
    file =  QFile ( commandList )
    if not file.open( QIODevice.ReadOnly ):
      return
    if not document.setContent( file ):
      file.close()
      return
    file.close()
    self.choices = QStringList()
    xml = QXmlStreamReader( document.toByteArray() )
    while not xml.atEnd():
      xml.readNext()
      if xml.tokenType() == QXmlStreamReader.StartElement:
        if xml.name() == "cmd":
          strRef = QStringRef( xml.attributes().value("name") )
          self.choices.append( strRef.toString() )
          print str(strRef.toString())
    
class TestApp( QMainWindow ):
  def __init__(self):
    QMainWindow.__init__(self)
    self.editor = QTextEdit(self)
    self.setCentralWidget( self.editor )
    self.setWindowTitle( "Autocomplete Test" )
    self.popup = CommandCompletion( self.editor, "commands.xml" )

if __name__ == "__main__":
  app = QApplication( sys.argv )
  window = TestApp()
  window.show()
  sys.exit( app.exec_() )


