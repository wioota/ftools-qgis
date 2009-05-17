from PyQt4.QtCore import *
from PyQt4.QtXml import QDomDocument

document = QDomDocument( "mydocument" )
file =  QFile ( "R.lang" )
if not file.open( QIODevice.ReadOnly ):
  pass
if not document.setContent( file ):
  file.close()
  pass
file.close();

documentElement = document.documentElement()
firstChild = documentElement.firstChild()

styles = {}

while not firstChild.isNull():
  element = firstChild.toElement()
  if not element.isNull():
  
    if element.tagName()== "styles":
      style = element.firstChild()
      while not style.isNull():
        el = style.toElement()
        styles[ el.attribute('id') ] = { "map-to" : el.attribute('map-to') }
        style = style.nextSibling()
        
    if element.tagName() == "definitions":
      context = element.firstChild()
      while not context.isNull():
        item = context.firstChild()
        node = context.toElement()
        if node.attribute( "id" ) in styles.keys():
          if not item.isNull():
            while not item.isNull():
              part = item.toElement()
              if not part.isNull():
                i = part.toElement()
                styles[ node.attribute( "id" ) ][ "value" ] = i.text()
                styles[ node.attribute( "id" ) ][ "tag" ] = i.tagName()
              item = item.nextSibling()
        context = context.nextSibling()
  firstChild = firstChild.nextSibling()
print styles
