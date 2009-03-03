from PyQt4.QtCore import *
from qgis.core import *
from PyQt4.QtGui import *
try:
	from rpy import *
except:
	try:
		from rpy2.rpy_classic import *
	except:
		QMessageBox.warning(self, "manageR", "Unable to load manageR: Required package rpy was unable to load"
							+ "\nPlease ensure that both R, and the corresponding version of Rpy are correctly installed.")

# Main function used to convert QgsVectorLayer
# to an R Spatial*DataFrame
def getSpatialDataFrame(inLayer, keepGeom):
	sRs = inLayer.srs()
	extra = ""
	if not sRs.isValid():
		projString = r.as_character(r.NA)
		extra = "Unable to determine projection information\nPlease specify using:\nlayer@proj4string <- CRS('+proj=longlat +datum=NAD83') for example."
	else:
		if not sRs.geographicFlag():
			projString = str(sRs.toProj4())
		else:
			# TODO: Find better way to handle geographic coordinate systems
			# As far as I can tell, R does not like geographic coodinate systems input
			# into it's proj4string argument...
			projString = r.as_character(r.NA)
			extra = "Unable to determine projection information\nPlease specify using:\nlayer@proj4string <- CRS('+proj=longlat +datum=NAD83') for example."
	provider = inLayer.dataProvider()
	df = getFieldList(inLayer)
	keys = [str(df[i].name()) for i in df.keys()]
	df = dict(zip(keys, [[] for item in df.values()]))
	FID = {'fid': []}
	Coords = []
	if inLayer.selectedFeatureCount() > 0:
		features = inLayer.selectedFeatures()
		for feat in features:
			for i in keys:
				df[i].append(convertAttribute(feat.attributeMap()[provider.fieldNameIndex(str(i))]))
			FID["fid"].append(feat.id())
			if keepGeom:
				if not getNextGeometry(Coords, feat):
					return (False, "Error! ", "Unable to convert layer geometry", extra)
	else:
		feat = QgsFeature()
		while provider.nextFeature(feat):
			for i in keys:
				df[i].append(convertAttribute(feat.attributeMap()[provider.fieldNameIndex(i)]))
			FID["fid"].append(feat.id())
			if keepGeom:
				if not getNextGeometry(Coords, feat):
					return (False, "Error! ", "Unable to convert layer geometry", extra)
	try:
		data = with_mode(NO_CONVERSION, r("function(d, i) data.frame(d, row.names = i)"))(df, FID["fid"])
	except:
		return (False, "Error! ", "Unable to convert layer attributes", extra)
	if keepGeom:
		return (createSpatialDataset(feat.geometry().type(), Coords, data, projString), len(FID["fid"]), len(keys), extra)
	else:
		return (data, len(FID["fid"]), len(keys), extra)

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
				keeps.append(r.Polygon(r.matrix(r.unlist([convertToXY(point) for point in line]), nrow=len([convertToXY(point) for point in line]), byrow=True)))
		return r.Polygons(keeps, str(fid))
	else:
		lines = geom.asPolygon() #multi_geom is a polygon
		Polygon = [r.Polygon(r.matrix(r.unlist([convertToXY(point) for point in line]), nrow=len([convertToXY(point) for point in line]), byrow=True)) for line in lines]
		return r.Polygons(Polygon, str(fid))

# Function to retrieve QgsGeometry (line) coordinates
# and convert to a format that can be used by R
# Return: Item of class Lines (R class)
def getLineCoords(geom, fid):
	if geom.isMultipart():
		keeps = []
		lines = geom.asMultiPolyline() #multi_geom is a multipolyline
		for line in lines:
			for line in lines:
				keeps.append(r.Polygon(r.matrix(r.unlist([convertToXY(point) for point in line]), nrow=len([convertToXY(point) for point in line]), byrow=True)))
		return r.Lines(keeps, str(fid))
	else:
		line = geom.asPolyline() #multi_geom is a line
		Line = r.Line(r.matrix(r.unlist([convertToXY(point) for point in line]), nrow = len([convertToXY(point) for point in line]), byrow=True))
		return r.Lines(Line, str(fid))

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
		spatialData = r.SpatialPoints(r.matrix(r.unlist(Coords), nrow = len(Coords), byrow = True), proj4string = r.CRS(projString))
		return r.SpatialPointsDataFrame(spatialData, data, match_ID = True)
	elif vectType == 1:
		spatialData = r.SpatialLines(Coords, proj4string = r.CRS(projString))
		return r.SpatialLinesDataFrame(spatialData, data, match_ID = True)
	elif vectType == 2:
		spatialData = r.SpatialPolygons(Coords, proj4string = r.CRS(projString))
		return r.SpatialPolygonsDataFrame(spatialData, data, match_ID = True)
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
		attribute= str(attribute.toString())
	else:
		attribute = attribute.toDouble()[0]
	return attribute

# Checks if an R spatial object is a vector or raster layer
# Return: True if vector, False if Raster, None if not of class (R class) Spatial*DataFrame
def checkObs(inName):
	check = with_mode(NO_DEFAULT, r('function(x) class(x)'))(r.get(i))
	if check == "SpatialPointsDataFrame" or check == "SpatialPolygonsDataFrame" or check == "SpatialLinesDataFrame":
		return True
	elif check == "SpatialGridDataFrame" or check == "SpatialPixelsDataFrame":
		return False
	else:
		return None

