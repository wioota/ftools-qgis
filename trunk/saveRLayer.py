from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import rpy2.rpy_classic as rpy
import rpy2.robjects as robjects
r = rpy.r

def saveOgr( dialog, mlayer ):
	returnText = ""
	drivers = "ESRI Shapefile (*.shp);;MapInfo File (*.mif);;GML (*.gml);;KML (*.kml)"
	fileDialog = QFileDialog()
	fileDialog.setConfirmOverwrite( True )
	selectedDriver = QString()
	outName = fileDialog.getSaveFileName( dialog, "Save OGR",".", drivers, selectedDriver )
	if not outName.isEmpty():
		fileCheck = QFile( outName )
		if fileCheck.exists():
			if not QgsVectorFileWriter.deleteShapeFile( outName ):
				QMessageBox.warning( self, "manageR", "Unable to delete existing shapefile." )
				return
		else:
			filePath = QFileInfo( outName ).absoluteFilePath()
			filePath.replace( "\\", "/" )
			fileName = QFileInfo( outName ).baseName()
			selDriveList = selectedDriver.split( "(" )
			Driver = selDriveList[ 0 ]
			Driver.chop( 1 )
			Extension = selDriveList[ 1 ].right( 5 )
			Extension.chop( 1 )
			if not filePath.endsWith( Extension, Qt.CaseInsensitive ): filePath = filePath.append( Extension )
			if not outName.isEmpty():
				returnText += "Saving " + unicode( mlayer ) + " ..."
				try:
					r_code = "writeOGR( obj = %s, dsn = '%s', layer = '%s', driver = '%s' )" %( unicode( mlayer ), unicode( filePath ), unicode( fileName ), unicode( Driver ) )
					robjects.r( r_code )
					returnText += " Done\n"
					addToTOC = QMessageBox.question( dialog, "manageR", "Created vector file:\n" + filePath
					+ "\n\nWould you like to add the new layer to the TOC?", QMessageBox.Yes, QMessageBox.No, QMessageBox.NoButton )
					if addToTOC == QMessageBox.Yes:
						vlayer = QgsVectorLayer( unicode( filePath ), unicode( fileName ), "ogr" )
						QgsMapLayerRegistry.instance().addMapLayer( vlayer )
				except Exception, e:
					returnText += "\n" + unicode( e )
	return ( True, returnText )

def saveGdal( dialog, mlayer ):
	returnText = ""
	drivers = "GeoTIFF (*.tif);;Erdas Imagine Images (*.img);;Arc/Info ASCII Grid " \
	+ "(*.asc);;ENVI Header Labelled (*.hdr);;JPEG-2000 part 1 (*.jp2);;Portable " \
	+ "Network Graphics (*.png);;USGS Optional ASCII DEM (*.dem)"
	fileDialog = QFileDialog()
	fileDialog.setConfirmOverwrite( True )
	selectedDriver = QString()
	outName = fileDialog.getSaveFileName(dialog, "Save GDAL",".", drivers, selectedDriver)
	if not outName.isEmpty():
		fileCheck = QFile(outName)
		if fileCheck.exists():
			# QMessageBox.warning(dialog, "Save GDAL", "Cannot overwrite existing file...")
			print "overwriting existing file..."
		else:
			filePath = QFileInfo( outName ).absoluteFilePath()
			filePath.replace( "\\", "/" )
			fileName = QFileInfo(outName).baseName()
			selDriveList = selectedDriver.split( "(" )
			Driver = selDriveList[ 0 ]
			Driver.chop( 1 )
			Extension = selDriveList[ 1 ].right( 5 )
			Extension.chop( 1 )
			if Driver == "GeoTIFF": Driver = "GTiff"
			elif Driver == "Erdas Imagine Images": Driver = "HFA"
			elif Driver == "Arc/Info ASCII Grid": Driver = "AAIGrid"
			elif Driver == "ENVI Header Labelled": Driver = "ENVI"
			elif Driver == "JPEG-2000 part 1": Driver = "JPEG2000"
			elif Driver == "Portable Network Graphics": Driver = "PNG"
			elif Driver == "USGS Optional ASCII DEM": Driver = "USGSDEM"
			if not filePath.endsWith( Extension, Qt.CaseInsensitive ) and Driver != "ENVI": filePath = filePath.append( Extension )
			if not outName.isEmpty():
				returnText += "Saving " + unicode(mlayer) + " ..."
				try:
					if Driver == "AAIGrid" or Driver == "JPEG2000" or Driver == "PNG" or Driver == "USGSDEM":
						r_code = "saveDataset( dataset = copyDataset( create2GDAL( dataset = %s, type = 'Float32' ), driver = '%s'), filename = '%s')" %( unicode( mlayer ), unicode( Driver ), unicode( Driver ) )
						robjects.r( r_code )
					else:
						r_code = "writeGDAL( dataset = %s, fname = '%s', drivername = '%s', type = 'Float32' )" %( unicode( mlayer ), unicode( filePath ), unicode( Driver ) )
					returnText += " Done\n"
					addToTOC = QMessageBox.question(dialog, "Save GDAL", "Created raster file:\n" + filePath
					+ "\n\nWould you like to add the new layer to the TOC?", QMessageBox.Yes, QMessageBox.No, QMessageBox.NoButton)
					if addToTOC == QMessageBox.Yes:
						rlayer = QgsRasterLayer( unicode( filePath ), unicode( fileName ) )
						QgsMapLayerRegistry.instance().addMapLayer( rlayer )
				except Exception, e:
					returnText += "\n" + unicode( e )
	return ( True, returnText )
