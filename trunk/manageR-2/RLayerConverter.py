# imports
from PyQt4.QtCore import *
from qgis.core import *
import rpy2.robjects as robjects

class RVectorLayerConverter( QObject ):
  '''
  RVectorLayerConvert:
  This aclass is used to convert an R 
  vector layer to a QgsVector layer for export
  to the QGIS map canvas.
  '''
  def __init__( self, r_layer, layer_name ):
    QObject.__init__( self )
    self.r_layer = r_layer
    self.layer_name = layer_name
    # define R functions as python variables
    self.slot_ = robjects.r[ '@' ]
    self.get_row_ = robjects.r(''' function( d, i ) d[ i ] ''')
    self.get_full_row_ = robjects.r(''' function( d, i ) data.frame( d[ i, ] ) ''')
    self.get_point_row_ = robjects.r(''' function( d, i ) d[ i, ] ''')
    self.class_ = robjects.r['class']
    self.names_ = robjects.r['names']
    self.dim_ = robjects.r['dim']
    self.as_character_ = robjects.r['as.character']

  def stop(self):
    '''
    Kill thread
    '''
    self.running = False

  #def run( self ):
  def start( self ):
    '''
    Main working function
    Emits threadSuccess when completed successfully
    Emits threadError when errors occur
    '''
    self.running = True
    error = False
    check, vtype = self.checkIfRObject( self.r_layer )
    if check:
      vlayer = QgsVectorLayer( vtype, unicode( self.layer_name ), "memory" )
      crs = QgsCoordinateReferenceSystem()
      crs_string =  self.slot_( self.slot_( self.r_layer, "proj4string" ), "projargs" )[ 0 ]
      # Figure out a better way to handle this problem:
      # QGIS does not seem to like the proj4 string that R outputs when it
      # contains +towgs84 as the final parameter
      crs_string = crs_string.lstrip().partition(" +towgs84")[ 0 ]
      if crs.createFromProj4( crs_string ):
        vlayer.setCrs( crs )
      provider = vlayer.dataProvider()
      check, fields = self.getAttributesList()
      if check:
        self.addAttributeSorted( fields, provider )
        rowCount = self.getRowCount()
        feat = QgsFeature()
        for row in range( 1, rowCount + 1 ):
          if vtype == "Point": coords = self.getPointCoords( row )
          elif vtype == "Polygon": coords = self.getPolygonCoords( row )
          else: coords = self.getLineCoords( row )
          attrs = self.getRowAttributes( provider, row )
          feat.setGeometry( coords )
          feat.setAttributeMap( attrs )
          provider.addFeatures( [ feat ] )
        vlayer.updateExtents()
      else:
        message = "R vector layer contains unsupported field type(s)"
        error = True
    else:
      message = "R vector layer is not of type SpatialPointsDataFrame, "
      + "SpatialLinesDataFrame, or SpatialPolygonsDataFrame."
      error = True
    if error:
      self.emit( SIGNAL( "threadError( PyQt_PyObject )" ), message )
    else:
      self.emit( SIGNAL( "threadSuccess( PyQt_PyObject, PyQt_PyObject )" ), vlayer, False )

  def addAttributeSorted( self, attributeList, provider ):
    '''
    Add attribute to memory provider in correct order
    To preserve correct order they must be added one-by-one
  '''
    for ( i, j ) in attributeList.iteritems():
      try:
        provider.addAttributes( { i : j } )
      except:
        if j == "int": j = QVariant.Int
        elif j == "double": j = QVariant.Double
        else: j = QVariant.String
        provider.addAttributes( [ QgsField( i, j ) ] )

  def getAttributesList( self ):
    '''
    Get list of attributes for R layer
    Return: Attribute list in format to be used by memory provider
    '''
    typeof_ = robjects.r['typeof']
    sapply_ = robjects.r['sapply']
    try:
      in_types = sapply_( self.slot_( self.r_layer, "data" ), typeof_ )
    except:
      return False, dict()
    in_names = self.names_( self.r_layer )
    out_fields = dict()
    for i in range( 0, len( in_types ) ):
      if in_types[ i ] == "double": out_fields[ in_names[ i ] ] = "double"
      elif in_types[ i ] == "integer": out_fields[ in_names[ i ] ] = "int"
      else: out_fields[ in_names[ i ] ] =  "string"
    return True, out_fields

  def checkIfRObject( self, layer ):
    '''
    Check if the input layer is an sp vector layer
    Return: True if it is, as well as the vector type
    '''
    check = self.class_( layer )[ 0 ]
    print check
    if check == "SpatialPointsDataFrame": return ( True, "Point" )
    elif check == "SpatialPolygonsDataFrame": return ( True, "Polygon" )
    elif check == "SpatialLinesDataFrame": return ( True, "LineString" )
    else: return ( False, "" )

  def getRowCount( self ):
    '''
    Get the number of features in the R spatial layer
    Return: Feature count
    '''
    return int( self.dim_( self.slot_( self.r_layer, "data" ) )[ 0 ] )

  def getRowAttributes( self, provider, row ):
    '''
    Get attributes associated with a single R feature
    Return: python dictionary containing key/value pairs,
    where key = field index and value = attribute
    '''
    temp = self.get_full_row_( self.slot_( self.r_layer, "data" ), row )
    names = self.names_( self.r_layer )
    out = {}
    if not provider.fieldCount() > 1:
      out = { 0 : QVariant( temp[ 0 ] ) }
    else:
  #    return dict( zip( [ provider.fieldNameIndex( str( name ) ) for name in names ],
  #    [ QVariant( item[0] ) for item in temp ] ) )
      count = 0
      for field in temp:
        if self.class_(field)[ 0 ] == "factor":
          out[ provider.fieldNameIndex( str( names[ count ] ) ) ] = QVariant( self.as_character_( field )[ 0 ] )
        else:
          out[ provider.fieldNameIndex( str( names[ count ] ) ) ] = QVariant( field[ 0 ] )
        count += 1
    return out

  def getPointCoords( self, row ):
    '''
    Get point coordinates of an R point feature
    Return: QgsGeometry from a point
    '''
    coords = self.get_point_row_( self.slot_( self.r_layer, 'coords' ), row )
    return QgsGeometry.fromPoint( QgsPoint( coords[ 0 ], coords[ 1 ] ) )
    
  def getPolygonCoords( self, row ):
    '''
    Get polygon coordinates of an R polygon feature
    Return: QgsGeometry from a polygon and multipolygon
    '''
    Polygons = self.get_row_( self.slot_( self.r_layer, "polygons" ), row )
    polygons_list = []
    for Polygon in Polygons:
      polygon_list = []
      polygons = self.slot_( Polygon, "Polygons" )
      for polygon in polygons:
        line_list = []
        points_list = self.slot_( polygon, "coords" )
        y_value = len( points_list )  / 2
        for j in range( 0, y_value ):
          line_list.append( self.convertToQgsPoints( ( points_list[ j ], points_list[ j + y_value ] ) ) )
        polygon_list.append( line_list )
      polygons_list.append( polygon_list )
    return QgsGeometry.fromMultiPolygon( polygons_list )

  def getLineCoords( self, row ):
    '''
    Get line coordinates of an R line feature
    Return: QgsGeometry from a line or multiline
    '''
    Lines = self.get_row_( self.slot_( self.r_layer, 'lines'), row )
    lines_list = []
    for Line in Lines:
      lines = self.slot_( Line, "Lines" )
      for line in lines:
        line_list = []
        points_list = self.slot_( line, "coords" )
        y_value = len( points_list )  / 2
        for j in range( 0, y_value ):
          line_list.append( self.convertToQgsPoints( ( points_list[ j ], points_list[ j + y_value ] ) ) )
      lines_list.append( line_list )
    return QgsGeometry.fromMultiPolyline( lines_list )

  def convertToQgsPoints( self, in_list ):
    '''
    Function to convert x, y coordinates list to QgsPoint
    Return: QgsPoint
    '''
    return QgsPoint( in_list[ 0 ], in_list[ 1 ] )
