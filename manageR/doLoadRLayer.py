from PyQt4.QtCore import *
from qgis.core import *
try:
	from rpy import *
except:
	from rpy2.rpy_classic import *

# Main function used to convert R spatial object to QgsVectorLayer
# Uses QgsMemoryProvider to store the layer in memory
# Return True if conversion is successful, False otherwise
def convert(rlayer, layerName):
	check, vtype = checkIfRObject(rlayer)
	if check:
		vlayer = QgsVectorLayer(vtype, str(layerName), "memory")
		srs = QgsCoordinateReferenceSystem()
		srsString = with_mode(BASIC_CONVERSION, r('function(d) d@projargs'))(r['@'](rlayer, "proj4string"))
		# TODO: Figure out a better way to handle this problem:
		# QGIS does not seem to like the proj4 string that R outputs when it
		# contains +towgs84 as the final parameter
		srsString = srsString.lstrip().partition(" +towgs84")[0]
		if srs.createFromProj4(QString(srsString)):
			vlayer.setCrs(srs)
		provider = vlayer.dataProvider()
		check, fields = getAttributesList(rlayer)
		if check:
			#provider.addAttributes(fields)
			addAttributeSorted(fields, provider)
			rowCount = getRowCount(rlayer)
			feat = QgsFeature()
			set_default_mode(NO_CONVERSION)
			for row in range(1, rowCount+1):
				if vtype == "Point": coords = getPointCoords(rlayer, row)
				elif vtype == "Polygon": coords = getPolygonCoords(rlayer, row)
				else: coords = getLineCoords(rlayer, row)
				attrs = getRowAttributes(provider, rlayer,row)
				feat.setGeometry(coords)
				feat.setAttributeMap(attrs)
				provider.addFeatures([feat])
			set_default_mode(NO_DEFAULT)
			vlayer.updateExtents()
			QgsMapLayerRegistry.instance().addMapLayer(vlayer)
			return (True, "Loaded R layer!")
		else:
			return (False, "Error! R vector layer contains unsupported field type(s).")
	else:
		return (False, "Error! Rdata file does not contain object of type SpatialPointsDataFrame, SpatialLinesDataFrame, or SpatialPolygonsDataFrame.")
 
# Add attribute to memory provider in correct order
# To preserve correct order they must be added one-by-one
def addAttributeSorted(attributeList, provider):
	for (i, j) in attributeList.iteritems():
		provider.addAttributes({ i:j })

# Get list of attributes for R layer
# Return: Attribute list in format to be used my memory provider
def getAttributesList(rlayer):
	if not "data" in as_list(r.names(r.getSlots(r.class_(rlayer)))):
		return (False, [])
	else:
		func = r('typeof')
		dftof = r.sapply(r.slot(rlayer, "data"), func)
		known = ["double", "character", "integer"]
		for i in dftof.keys():
			if dftof[i] == "double": dftof[i] = "double"
			elif dftof[i] == "character": dftof[i] = "string"
			elif dftof[i] == "integer": dftof[i] = "int"
			else: check = dftof.popitem(i)
		return True, dftof

# Check if the input layer is an sp vector layer
# Return: True if it is, as well as the vector type
def checkIfRObject(layer):
	check = r.class_(layer)
	if check == 'SpatialPointsDataFrame': return (True, "Point")
	elif check == 'SpatialPolygonsDataFrame': return (True, "Polygon")
	elif check == 'SpatialLinesDataFrame': return (True, "LineString")
	else: return (False, "")
	
# Get the number of features in the R spatial layer
# Return: Feature count
def getRowCount(rlayer):
	rows = as_list(r['@'](rlayer, 'data')[r['@'](rlayer, 'data').keys()[0]])
	return len(rows)

# Get attributes associated with a single R feature
# Return: python dictionary containing key/value pairs,
# where key = field index and value = attribute
def getRowAttributes(provider, rlayer, row):
	temp = with_mode(BASIC_CONVERSION, r("function(d, i) d[i,]"))(r['@'](rlayer, 'data'), row)
	if not provider.fieldCount() > 1:
		return { 0 : QVariant(temp) }
	else:
		return dict(zip([provider.fieldNameIndex(str(i)) for i in temp.keys()], [QVariant(item) for item in temp.values()]))

# Get point coordinates of an R point feature
# Return: QgsGeometry from a point
def getPointCoords(rlayer, row):
	coords = with_mode(BASIC_CONVERSION, r("function(d, i) d[i,]"))(r['@'](rlayer, 'coords'), row)
	return QgsGeometry.fromPoint(QgsPoint(coords['coords.x1'], coords['coords.x2']))

# Get polygon coordinates of an R polygon feature
# Return: QgsGeometry from a polygon and multipolygon
def getPolygonCoords(rlayer, row):
	Polygons = with_mode(BASIC_CONVERSION, r("function(d, i) d[i]"))(r['@'](rlayer, 'polygons'), row)
	Polygon = with_mode(BASIC_CONVERSION, r("function(d) d@Polygons"))(Polygons)
	if with_mode(BASIC_CONVERSION, r("function(d) class(d)"))(Polygon) == "list":
		coords = []
		polygons = with_mode(BASIC_CONVERSION, r("function(d) length(d)"))(Polygon)
		for polygon in range(1, polygons):
			temp_list = with_mode(BASIC_CONVERSION, r("function(d, i) d[[i]]@coords"))(Polygon, polygon)
			coords.append([map(convertToQgsPoints, temp_list)])
		return QgsGeometry.fromMultiPolygon(coords)
	else:
		temp_list = with_mode(BASIC_CONVERSION, r("function(d) d@coords"))(Polygon)
		return QgsGeometry.fromPolygon([map(convertToQgsPoints, temp_list)])

# Get line coordinates of an R line feature
# Return: QgsGeometry from a line or multiline
def getLineCoords(rlayer, row):
	Lines = with_mode(BASIC_CONVERSION, r("function(d, i) d[i]"))(r['@'](rlayer, 'lines'), row)
	Line = with_mode(BASIC_CONVERSION, r("function(d) d@Lines"))(Lines)
	if with_mode(BASIC_CONVERSION, r("function(d) class(d)"))(Line) == "list":
		coords = []
		lines = with_mode(BASIC_CONVERSION, r("function(d) length(d)"))(Line)
		for line in range(1, lines):
			temp_list = with_mode(BASIC_CONVERSION, r("function(d, i) d[[i]]@coords"))(Line, line)
			coords.append(map(convertToQgsPoints, temp_list))
		return QgsGeometry.fromMultiPolyline(coords)
	else:
		temp_list = with_mode(BASIC_CONVERSION, r("function(d) d@coords"))(Line)
		return QgsGeometry.fromPolyline(map(convertToQgsPoints, temp_list))

# Function to convert x, y coordinates list to QgsPoint
# Return: QgsPoint
def convertToQgsPoints(inList):
	return QgsPoint(inList[0], inList[1])

# Check that the sp package is loaded into R, 
# and if it is not, attempt to load it.
# Return: True if it is successfully loaded, False otherwise
def checkPack(inPack):
	if r.require(inPack):
		return True
	else:
		return False
