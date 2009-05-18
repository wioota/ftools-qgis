import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtXml import QDomDocument

class Suggestions( QObject ):

  def __init__( self, auto_list ):
    QObject.__init__( self )
    document = QDomDocument( "mydocument" )
    file =  QFile ( auto_list )
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

  def getAllSuggestions( self ):
    return QStringList( self.choices )

class Suggest( QFrame ):
  def __init__( self, parent ):
    QFrame.__init__( self, parent )
    self.setObjectName("Form")
    self.resize(200, 43)
    self.gridLayout = QGridLayout(self)
    self.gridLayout.setObjectName("gridLayout")
    self.treeWidget = QTreeWidget(self)
    sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
    self.treeWidget.setSizePolicy(sizePolicy)
    self.treeWidget.setFrameShadow(QFrame.Raised)
    self.treeWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.treeWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self.treeWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
    self.treeWidget.setProperty("showDropIndicator", QVariant(False))
    self.treeWidget.setAlternatingRowColors(True)
    self.treeWidget.setObjectName("treeWidget")
    self.treeWidget.header().hide()
    self.gridLayout.addWidget(self.treeWidget, 0, 0, 1, 1)

class TestApp( QMainWindow ):
  def __init__(self):
    QMainWindow.__init__(self)
    self.editor = QTextEdit()
    self.suggestions = Suggestions( "commands.xml" )
    self.suggestions = self.suggestions.getAllSuggestions()
    self.connect( self.editor, SIGNAL( "textChanged()" ), self.makeSuggestions )
    self.setCentralWidget( self.editor )
    self.setWindowTitle( "Autocomplete Test" )
    
  def makeSuggestions( self ):
    text = self.editor.toPlainText()
    if text.contains( QRegExp( "\\b\\w{3,}" ) ):
      suggestions = self.suggestions.filter( QRegExp( text + "+" ) )
      dialog = Suggest( self.editor )
      for i in suggestions:
          item = QTreeWidgetItem( dialog.treeWidget )
          item.setText( 0, i )
      dialog.resize(dialog.width(), suggestions.count() * 30)
      dialog.setFocus()
      dialog.show()

if __name__ == "__main__":
  app = QApplication( sys.argv )
  window = TestApp()
  window.show()
  sys.exit( app.exec_() )

