from PyQt4.QtCore import *
from qgis.core import *
import rpy2.rpy_classic as rpy
import rpy2.robjects as robjects
r = rpy.r

# define R functions as python variables
slot_ = robjects.r[ '@' ]
get_row_ = robjects.r(''' function( d, i ) d[ i ] ''')
get_full_row_ = robjects.r(''' function( d, i ) data.frame( d[ i, ] ) ''')
get_point_row_ = robjects.r(''' function( d, i ) d[ i, ] ''')
class_ = robjects.r['class']
names_ = robjects.r['names']
dim_ = robjects.r['dim']
as_character_ = robjects.r['as.character']

# Main function used to convert R spatial object to QgsVectorLayer
# Uses QgsMemoryProvider to store the layer in memory
# Return True if conversion is successful, False otherwise
def convert( rlayer, layerName ):
	check, vtype = checkIfRObject( rlayer )
	if check:
		vlayer = QgsVectorLayer( vtype, unicode(layerName), "memory" )
		srs = QgsCoordinateReferenceSystem()
		slot = robjects.r['@']
		srs_string =  slot( slot( rlayer, "proj4string" ), "projargs" )[ 0 ]
		# TODO: Figure out a better way to handle this problem:
		# QGIS does not seem to like the proj4 string that R outputs when it
		# contains +towgs84 as the final parameter
		srs_string = srs_string.lstrip().partition(" +towgs84")[ 0 ]
		if srs.createFromProj4( srs_string ):
			vlayer.setCrs( srs )
		provider = vlayer.dataProvider()
		check, fields = getAttributesList( rlayer )
		if check:
			#provider.addAttributes(fields)
			addAttributeSorted( fields, provider )
			rowCount = getRowCount( rlayer )
			feat = QgsFeature()
#			set_default_mode(NO_CONVERSION)
			for row in range( 1, rowCount + 1 ):
				if vtype == "Point": coords = getPointCoords( rlayer, row )
				elif vtype == "Polygon": coords = getPolygonCoords( rlayer, row )
				else: coords = getLineCoords( rlayer, row )
				attrs = getRowAttributes( provider, rlayer, row )
				feat.setGeometry( coords )
				feat.setAttributeMap( attrs )
				provider.addFeatures( [ feat ] )
#			set_default_mode(NO_DEFAULT)
			vlayer.updateExtents()
			QgsMapLayerRegistry.instance().addMapLayer( vlayer )
			return ( True, "Loaded R layer!" )
		else:
			return ( False, "Error! R vector layer contains unsupported field type(s)." )
	else:
		return ( False, "Error! Rdata file does not contain object of type SpatialPointsDataFrame, SpatialLinesDataFrame, or SpatialPolygonsDataFrame." )
 
# Add attribute to memory provider in correct order
# To preserve correct order they must be added one-by-one
def addAttributeSorted( attributeList, provider ):
	for ( i, j ) in attributeList.iteritems():
		provider.addAttributes( { i : j } )

# Get list of attributes for R layer
# Return: Attribute list in format to be used my memory provider
def getAttributesList( rlayer ):
	typeof_ = robjects.r['typeof']
	sapply_ = robjects.r['sapply']
	try:
		in_types = sapply_( slot_( rlayer, "data" ), typeof_ )
	except:
		return False, dict()
	in_names = names_( rlayer )
	#known = [ "double", "character", "integer" ]
	out_fields = dict()
	for i in range( 0, len( in_types ) ):
		if in_types[ i ] == "double": out_fields[ in_names[ i ] ] = "double"
		elif in_types[ i ] == "integer": out_fields[ in_names[ i ] ] = "int"
		else: out_fields[ in_names[ i ] ] =  "string" # i == "character"
	return True, out_fields

# Check if the input layer is an sp vector layer
# Return: True if it is, as well as the vector type
def checkIfRObject( layer ):
	check = class_( layer )[ 0 ]
	print check
	if check == "SpatialPointsDataFrame": return ( True, "Point" )
	elif check == "SpatialPolygonsDataFrame": return ( True, "Polygon" )
	elif check == "SpatialLinesDataFrame": return ( True, "LineString" )
	else: return ( False, "" )
	
# Get the number of features in the R spatial layer
# Return: Feature count
def getRowCount( rlayer ):
	rows = dim_( slot_( rlayer, "data" ) )[ 0 ]
	#rows = as_list(r['@'](rlayer, 'data')[r['@'](rlayer, 'data').keys()[0]])
	return int( rows )

# Get attributes associated with a single R feature
# Return: python dictionary containing key/value pairs,
# where key = field index and value = attribute
def getRowAttributes( provider, rlayer, row ):
	temp = get_full_row_( slot_( rlayer, "data" ), row )
	names = names_( rlayer )
	out = {}
	if not provider.fieldCount() > 1:
		out = { 0 : QVariant( temp[ 0 ] ) }
	else:
#		return dict( zip( [ provider.fieldNameIndex( str( name ) ) for name in names ],
#		[ QVariant( item[0] ) for item in temp ] ) )
		count = 0
		for field in temp:
			if class_(field)[ 0 ] == "factor":
				out[ provider.fieldNameIndex( str( names[ count ] ) ) ] = QVariant( as_character_( field )[ 0 ] )
			else:
				out[ provider.fieldNameIndex( str( names[ count ] ) ) ] = QVariant( field[ 0 ] )
			count += 1
	return out

# Get point coordinates of an R point feature
# Return: QgsGeometry from a point
def getPointCoords(rlayer, row):
	coords = get_point_row_( slot_( rlayer, 'coords' ), row )
	print coords
	return QgsGeometry.fromPoint( QgsPoint( coords[ 0 ], coords[ 1 ] ) )
	
# Get polygon coordinates of an R polygon feature
# Return: QgsGeometry from a polygon and multipolygon
def getPolygonCoords( rlayer, row ):
	Polygons = get_row_( slot_( rlayer, "polygons" ), row )
	polygons_list = []
	for Polygon in Polygons:
		polygon_list = []
		polygons = slot_( Polygon, "Polygons" )
		for polygon in polygons:
			line_list = []
			points_list = slot_( polygon, "coords" )
			y_value = len( points_list )  / 2
			for j in range( 0, y_value ):
				line_list.append( convertToQgsPoints( ( points_list[ j ], points_list[ j + y_value ] ) ) )
			polygon_list.append( line_list )
		polygons_list.append( polygon_list )
	return QgsGeometry.fromMultiPolygon( polygons_list )

# Get line coordinates of an R line feature
# Return: QgsGeometry from a line or multiline
def getLineCoords(rlayer, row):
	Lines = get_row_( slot_( rlayer, 'lines'), row )
	lines_list = []
	for Line in Lines:
		lines = slot_( Line, "Lines" )
		for line in lines:
			line_list = []
			points_list = slot_( line, "coords" )
			y_value = len( points_list )  / 2
			for j in range( 0, y_value ):
				line_list.append( convertToQgsPoints( ( points_list[ j ], points_list[ j + y_value ] ) ) )
		lines_list.append( line_list )
	return QgsGeometry.fromMultiPolyline( lines_list )

# Function to convert x, y coordinates list to QgsPoint
# Return: QgsPoint
def convertToQgsPoints( in_list ):
	return QgsPoint( in_list[ 0 ], in_list[ 1 ] )

# Check that the sp package is loaded into R, 
# and if it is not, attempt to load it.
# Return: True if it is successfully loaded, False otherwise
def checkPack( inPack ):
	require_ = robjects.r[ 'require' ]
	return require_( inPack )[ 0 ]
