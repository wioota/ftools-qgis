from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import Numeric, array

# Main function used to convert QgsVectorLayer
# to an R Spatial*DataFrame
def getSpatialDataFrame( robjects, inLayer, keepGeom ):
	provider = inLayer.dataProvider()
	extra = ""
	if keepGeom:
		sRs = provider.crs()
		if not sRs.isValid():
			projString = 'NA'
			extra = "Unable to determine projection information\nPlease specify using:\nlayer@proj4string <- CRS('+proj=longlat +datum=NAD83') for example."
		else:
			if not sRs.geographicFlag():
				projString = unicode( sRs.toProj4() )
			else:
				# TODO: Find better way to handle geographic coordinate systems
				# As far as I can tell, R does not like geographic coodinate systems input
				# into it's proj4string argument...
				projString = 'NA'
				extra = "Unable to determine projection information\nPlease specify using:\nlayer@proj4string <- CRS('+proj=longlat +datum=NAD83') for example."

	attrIndex = provider.attributeIndexes()
	provider.select(attrIndex)
	fields = provider.fields()
	df = {}
	types = {}
	for (id, field) in fields.iteritems():
		df[unicode(field.name()).encode('utf-8')] = []
		types[unicode(field.name()).encode('utf-8')] = field.type()
	fid = {"fid": []}
	Coords = []
	if inLayer.selectedFeatureCount() > 0:
		features = inLayer.selectedFeatures()
		for feat in features:
			for (key, value) in df.iteritems():
				df[key].append(convertAttribute(feat.attributeMap()[provider.fieldNameIndex(key)]))
			fid["fid"].append(feat.id())
			if keepGeom:
				if not getNextGeometry(Coords, feat):
					return (False, "Error! ", "Unable to convert layer geometry", extra)
	else:
		feat = QgsFeature()
		while provider.nextFeature(feat):
			for (key, value) in df.iteritems():
				attrib = convertAttribute(feat.attributeMap()[provider.fieldNameIndex(key)])
				#QMessageBox.information(None, 'test', str(type(attrib)))
				df[key].append(attrib)
			fid["fid"].append(feat.id())
			if keepGeom:
				if not getNextGeometry(Coords, feat):
					return (False, "Error! ", "Unable to convert layer geometry", extra)
		for (key, value) in df.iteritems():
			if types[key] == 10:
				df[key] = array.array('u', value)
			else:
				df[key] = array.array('f', value)
		fid["fid"] = array.array('i', fid["fid"])
	#try:
	QMessageBox.information(None, 'test', str(df))
	data = robjects.r['data.frame'](**df)
	data.row_names = fid["fid"]
	#except:
	#	return (False, "Error! ", "Unable to convert layer attributes", extra)
	if keepGeom:
		return (createSpatialDataset(feat.geometry().type(), Coords, data, projString), len(fid["fid"]), len(df.keys()), extra)
	else:
		return (data, len(fid["fid"]), len(df.keys()), extra)

# Gets field list (as python dictionary)
# for input vector layer
def getFieldList(vlayer):
	fProvider = vlayer.dataProvider()
	feat = QgsFeature()
	allAttrs = fProvider.attributeIndexes()
	fProvider.select(allAttrs)
	myFields = fProvider.fields()
	return myFields

# Function to retrieve QgsGeometry (polygon) coordinates
# and convert to a format that can be used by R
# Return: Item of class Polygons (R class)
def getPolygonCoords(geom, fid):
	if geom.isMultipart():
		keeps = []
		polygon = geom.asMultiPolygon() #multi_geom is a multipolygon
		for lines in polygon:
			for line in lines:
				keeps.append(rpy.r.Polygon(rpy.r.matrix(rpy.r.unlist([convertToXY(point) for point in line]), nrow=len([convertToXY(point) for point in line]), byrow=True)))
		return rpy.r.Polygons(keeps, fid)
	else:
		lines = geom.asPolygon() #multi_geom is a polygon
		Polygon = [rpy.r.Polygon(rpy.r.matrix(rpy.r.unlist([convertToXY(point) for point in line]), nrow=len([convertToXY(point) for point in line]), byrow=True)) for line in lines]
		return rpy.r.Polygons(Polygon, fid)

# Function to retrieve QgsGeometry (line) coordinates
# and convert to a format that can be used by R
# Return: Item of class Lines (R class)
def getLineCoords(geom, fid):
	if geom.isMultipart():
		keeps = []
		lines = geom.asMultiPolyline() #multi_geom is a multipolyline
		for line in lines:
			for line in lines:
				keeps.append(rpy.r.Polygon(rpy.r.matrix(rpy.r.unlist([convertToXY(point) for point in line]), nrow=len([convertToXY(point) for point in line]), byrow=True)))
		return rpy.r.Lines(keeps, fid)
	else:
		line = geom.asPolyline() #multi_geom is a line
		Line = rpy.r.Line(rpy.r.matrix(rpy.r.unlist([convertToXY(point) for point in line]), nrow = len([convertToXY(point) for point in line]), byrow=True))
		return rpy.r.Lines(Line, fid)

# Function to retrieve QgsGeometry (point) coordinates
# and convert to a format that can be used by R
# Return: Item of class Matrix (R class)
def getPointCoords(geom, fid):
	if geom.isMultipart():
		points = geom.asMultiPoint() #multi_geom is a multipoint
		return [convertToXY(point) for point in points]
	else:
		point = geom.asPoint() #multi_geom is a point
		return convertToXY(point)

# Helper function to get coordinates of input geometry
# Does not require knowledge of input geometry type
# Return: Appends R type geometry to input list
def getNextGeometry(Coords, feat):
	geom = feat.geometry()
	if geom.type() == 0:
		Coords.append(getPointCoords(geom, feat.id()))
		return True
	elif geom.type() == 1:
		Coords.append(getLineCoords(geom, feat.id()))
		return True
	elif geom.type() == 2:
		Coords.append(getPolygonCoords(geom, feat.id()))
		return True
	else:
		return False

# Helper function to create Spatial*DataFrame from
# input spatial and attribute information
# Return: Object of class Spatial*DataFrame (R class)
def createSpatialDataset(vectType, Coords, data, projString):
	if vectType == 0:
		# For points, coordinates must be input as a matrix, hense the extra bits below...
		# Not sure if this will work for multipoint features?
		spatialData = rpy.r.SpatialPoints(rpy.r.matrix(rpy.r.unlist(Coords), nrow = len(Coords), byrow = True), proj4string = rpy.r.CRS(projString))
		return rpy.r.SpatialPointsDataFrame(spatialData, data, match_ID = True)
	elif vectType == 1:
		spatialData = rpy.r.SpatialLines(Coords, proj4string = rpy.r.CRS(projString))
		return rpy.r.SpatialLinesDataFrame(spatialData, data, match_ID = True)
	elif vectType == 2:
		spatialData = rpy.r.SpatialPolygons(Coords, proj4string = rpy.r.CRS(projString))
		return rpy.r.SpatialPolygonsDataFrame(spatialData, data, match_ID = True)
	else:
		return

# Function to convert QgsPoint to x, y coordinate
# Return: list
def convertToXY(inPoint):
	return [inPoint.x(), inPoint.y()]

# Function to convert attribute to string or double
# for input into R object
# Return: Double or String
def convertAttribute(attribute):
	Qtype = attribute.type()
	if Qtype == 10:
		return unicode(attribute.toString())
	else:
		return attribute.toDouble()[0]

# Checks if an R spatial object is a vector or raster layer
# Return: True if vector, False if Raster, None if not of class (R class) Spatial*DataFrame
def checkObs(inName):
	check = with_mode(NO_DEFAULT, r('function(x) class(x)'))(rpy.r.get(i))
	if check == "SpatialPointsDataFrame" or check == "SpatialPolygonsDataFrame" or check == "SpatialLinesDataFrame":
		return True
	elif check == "SpatialGridDataFrame" or check == "SpatialPixelsDataFrame":
		return False
	else:
		return None

