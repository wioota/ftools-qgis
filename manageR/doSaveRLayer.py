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

def saveOgr(dialog, mlayer):
	returnText = ""
	drivers = "ESRI Shapefile (*.shp);;MapInfo File (*.mif);;GML (*.gml);;KML (*.kml)"
	fileDialog = QFileDialog()
	fileDialog.setConfirmOverwrite(False)
	selectedDriver = QString()
	outName = fileDialog.getSaveFileName(dialog, "Save OGR",".", drivers, selectedDriver)
	if not outName.isEmpty():
		fileCheck = QFile(outName)
		if fileCheck.exists():
			QMessageBox.warning(dialog, "Save OGR", "Cannot overwrite existing file...")
		else:
			filePath = QFileInfo(outName).absoluteFilePath()
			filePath.replace("\\", "/")
			fileName = QFileInfo(outName).baseName()
			selDriveList = selectedDriver.split("(")
			Driver = selDriveList[0]
			Driver.chop(1)
			Extension = selDriveList[1].right(5)
			Extension.chop(1)
			if not filePath.endsWith(Extension, Qt.CaseInsensitive): filePath = filePath.append(Extension)
			if not outName.isEmpty():
				returnText += "Saving " + str(mlayer) + " ..."
				try:
					exec "r(''' writeOGR(obj = " + str(mlayer) + ", dsn = '" + str(filePath) + "', layer = '" + str(fileName) + "', driver = '" + str(Driver) + "') ''')"
					returnText += " Done\n"
					addToTOC = QMessageBox.question(dialog, "manageR", "Created vector file:\n" + filePath
					+ "\n\nWould you like to add the new layer to the TOC?", QMessageBox.Yes, QMessageBox.No, QMessageBox.NoButton)
					if addToTOC == QMessageBox.Yes:
						vlayer = QgsVectorLayer(str(filePath), str(fileName), "ogr")
						QgsMapLayerRegistry.instance().addMapLayer(vlayer)
				except RException, e:
					returnText += "\n" + str(e)
	return (True, returnText)

def saveGdal(dialog, mlayer):
	returnText = ""
	drivers = "GeoTIFF (*.tif);;Erdas Imagine Images (*.img);;Arc/Info ASCII Grid " \
	+ "(*.asc);;ENVI Header Labelled (*.hdr);;JPEG-2000 part 1 (*.jp2);;Portable " \
	+ "Network Graphics (*.png);;USGS Optional ASCII DEM (*.dem)"
	fileDialog = QFileDialog()
	fileDialog.setConfirmOverwrite(False)
	selectedDriver = QString()
	outName = fileDialog.getSaveFileName(dialog, "Save GDAL",".", drivers, selectedDriver)
	if not outName.isEmpty():
		fileCheck = QFile(outName)
		if fileCheck.exists():
			QMessageBox.warning(dialog, "Save GDAL", "Cannot overwrite existing file...")
		else:
			filePath = QFileInfo(outName).absoluteFilePath()
			filePath.replace("\\", "/")
			fileName = QFileInfo(outName).baseName()
			selDriveList = selectedDriver.split("(")
			Driver = selDriveList[0]
			Driver.chop(1)
			Extension = selDriveList[1].right(5)
			Extension.chop(1)
			if Driver == "GeoTIFF": Driver = "GTiff"
			elif Driver == "Erdas Imagine Images": Driver = "HFA"
			elif Driver == "Arc/Info ASCII Grid": Driver = "AAIGrid"
			elif Driver == "ENVI Header Labelled": Driver = "ENVI"
			elif Driver == "JPEG-2000 part 1": Driver = "JPEG2000"
			elif Driver == "Portable Network Graphics": Driver = "PNG"
			elif Driver == "USGS Optional ASCII DEM": Driver = "USGSDEM"
			if not filePath.endsWith(Extension, Qt.CaseInsensitive) and Driver != "ENVI": filePath = filePath.append(Extension)
			if not outName.isEmpty():
				returnText += "Saving " + str(mlayer) + " ..."
				try:
					if Driver == "AAIGrid" or Driver == "JPEG2000" or Driver == "PNG" or Driver == "USGSDEM":
						exec "r(''' saveDataset(dataset = copyDataset(create2GDAL(dataset = " + str(mlayer) + ", type = 'Float32'), driver = '" + str(Driver) + "'), filename = '" + str(filePath) + "') ''')"
					else:
						exec "r(''' writeGDAL(dataset = " + str(mlayer) + ", fname = '" + str(filePath) + "', drivername = '" + str(Driver) + "', type = 'Float32') ''')"
					returnText += " Done\n"
					addToTOC = QMessageBox.question(dialog, "Save GDAL", "Created raster file:\n" + filePath
					+ "\n\nWould you like to add the new layer to the TOC?", QMessageBox.Yes, QMessageBox.No, QMessageBox.NoButton)
					if addToTOC == QMessageBox.Yes:
						rlayer = QgsRasterLayer(str(filePath), str(fileName))
						QgsMapLayerRegistry.instance().addMapLayer(rlayer)
				except RException, e:
					returnText += "\n" + str(e)
	return (True, returnText)
