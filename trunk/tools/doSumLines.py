#-----------------------------------------------------------
# 
# Sum Lines In Polygons
#
# A QGIS plugin for calculating the total sum of line 
# lengths in each polygon of an input vector polygon layer.
#
# Copyright (C) 2008  Carson Farmer
#
# EMAIL: carson.farmer (at) gmail.com
# WEB  : www.geog.uvic.ca/spar/carson
#
#-----------------------------------------------------------
# 
# licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# 
#---------------------------------------------------------------------

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from frmSumLines import Ui_Dialog

class Dialog(QDialog, Ui_Dialog):

	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		# Set up the user interface from Designer.
		self.setupUi(self)
		QObject.connect(self.toolOut, SIGNAL("clicked()"), self.outFile)
		self.setWindowTitle("Sum line lengths")
		# populate layer list
		self.progressBar.setValue(0)
		mapCanvas = self.iface.mapCanvas()
		for i in range(mapCanvas.layerCount()):
			layer = mapCanvas.layer(i)
			if layer.type() == layer.VectorLayer:
				if layer.geometryType() == QGis.Polygon:
					self.inPolygon.addItem(layer.name())
				elif layer.geometryType() == QGis.Line:
					self.inPoint.addItem(layer.name())
		
	def accept(self):
		if self.inPolygon.currentText() == "":
			QMessageBox.information(self, "Sum Line Lengths In Polyons", "Please specify input polygon vector layer")
		elif self.outShape.text() == "":
			QMessageBox.information(self, "Sum Line Lengths In Polyons", "Please specify output shapefile")
		elif self.inPoint.currentText() == "":
			QMessageBox.information(self, "Sum Line Lengths In Polyons", "Please specify input line vector layer")
		elif self.lnField.text() == "":
			QMessageBox.information(self, "Sum Line Lengths In Polyons", "Please specify output length field")
		else:
			inPoly = self.inPolygon.currentText()
			inLns = self.inPoint.currentText()
			inField = self.lnField.text()
			outPath = self.outShape.text()
			if outPath.contains("\\"):
				outName = outPath.right((outPath.length() - outPath.lastIndexOf("\\")) - 1)
			else:
				outName = outPath.right((outPath.length() - outPath.lastIndexOf("/")) - 1)
			if outName.endsWith(".shp"):
				outName = outName.left(outName.length() - 4)
			self.compute(inPoly, inLns, inField, outPath, self.progressBar)
			self.outShape.clear()
			addToTOC = QMessageBox.question(self, "Sum line lengths", "Created output shapefile:\n" + outPath 
			+ "\n\nWould you like to add the new layer to the TOC?", QMessageBox.Yes, QMessageBox.No, QMessageBox.NoButton)
			if addToTOC == QMessageBox.Yes:
				self.vlayer = QgsVectorLayer(outPath, unicode(outName), "ogr")
				QgsMapLayerRegistry.instance().addMapLayer(self.vlayer)
		self.progressBar.setValue(0)

	def outFile(self):
		fileDialog = QFileDialog()
		settings = QSettings()
		dirName = settings.value("/UI/lastShapefileDir").toString()
		fileDialog.setDirectory(dirName)
		fileDialog.setDefaultSuffix(QString("shp"))
		fileDialog.setFileMode(QFileDialog.AnyFile)
		encodingBox = QComboBox()
		l = QLabel("Encoding:",fileDialog)
		fileDialog.layout().addWidget(l)
		fileDialog.layout().addWidget(encodingBox)
		encodingBox.addItem("BIG5") 
		encodingBox.addItem("BIG5-HKSCS")
		encodingBox.addItem("EUCJP")
		encodingBox.addItem("EUCKR")
		encodingBox.addItem("GB2312")
		encodingBox.addItem("GBK") 
		encodingBox.addItem("GB18030")
		encodingBox.addItem("JIS7") 
		encodingBox.addItem("SHIFT-JIS")
		encodingBox.addItem("TSCII")
		encodingBox.addItem("UTF-8")
		encodingBox.addItem("UTF-16")
		encodingBox.addItem("KOI8-R")
		encodingBox.addItem("KOI8-U") 
		encodingBox.addItem("ISO8859-1")
		encodingBox.addItem("ISO8859-2")
		encodingBox.addItem("ISO8859-3")
		encodingBox.addItem("ISO8859-4")
		encodingBox.addItem("ISO8859-5")
		encodingBox.addItem("ISO8859-6")
		encodingBox.addItem("ISO8859-7")
		encodingBox.addItem("ISO8859-8") 
		encodingBox.addItem("ISO8859-8-I")
		encodingBox.addItem("ISO8859-9")
		encodingBox.addItem("ISO8859-10")
		encodingBox.addItem("ISO8859-13")
		encodingBox.addItem("ISO8859-14")
		encodingBox.addItem("ISO8859-15")
		encodingBox.addItem("IBM 850")
		encodingBox.addItem("IBM 866")
		encodingBox.addItem("CP874") 
		encodingBox.addItem("CP1250")
		encodingBox.addItem("CP1251")
		encodingBox.addItem("CP1252")
		encodingBox.addItem("CP1253")
		encodingBox.addItem("CP1254")
		encodingBox.addItem("CP1255")
		encodingBox.addItem("CP1256")
		encodingBox.addItem("CP1257") 
		encodingBox.addItem("CP1258") 
		encodingBox.addItem("Apple Roman")
		encodingBox.addItem("TIS-620")
		encodingBox.setItemText(encodingBox.currentIndex(), QString(QTextCodec.codecForLocale().name()))
		filtering = QString("Shapefiles (*.shp)")
		fileDialog.setAcceptMode(QFileDialog.AcceptSave)
 		fileDialog.setFilter(filtering)
		fileDialog.setConfirmOverwrite(True)
		if not fileDialog.exec_() == 1:
			return
		self.shapefileName = unicode(fileDialog.selectedFiles().first())
		self.encoding = unicode(encodingBox.currentText())
		self.outShape.clear()
		self.outShape.insert(self.shapefileName)

	def compute(self, inPoly, inLns, inField, outPath, progressBar):
		polyLayer = self.getVectorLayerByName(inPoly)
		lineLayer = self.getVectorLayerByName(inLns)
		polyProvider = polyLayer.dataProvider()
		lineProvider = lineLayer.dataProvider()
		if polyProvider.crs() <> lineProvider.crs():
			QMessageBox.warning(self, "CRS warning!", "Warning: Input layers have non-matching CRS.\nThis may cause unexpected results.")
		allAttrs = polyProvider.attributeIndexes()
		polyProvider.select(allAttrs)
		allAttrs = lineProvider.attributeIndexes()
		lineProvider.select(allAttrs)
		fieldList = self.getFieldList(polyLayer)
		index = polyProvider.fieldNameIndex(unicode(inField))
		if index == -1:
			index = polyProvider.fieldCount()
			field = QgsField(unicode(inField), QVariant.Int, "real", 24, 15, "length field")
			fieldList[index] = field
		sRs = polyProvider.crs()
		inFeat = QgsFeature()
		outFeat = QgsFeature()
		inGeom = QgsGeometry()
		outGeom = QgsGeometry()
		distArea = QgsDistanceArea()
		lineProvider.rewind()
		start = 15.00
		add = 85.00 / polyProvider.featureCount()
		check = QFile(self.shapefileName)
		if check.exists():
			if not QgsVectorFileWriter.deleteShapeFile(self.shapefileName):
				return
		writer = QgsVectorFileWriter(self.shapefileName, self.encoding, fieldList, polyProvider.geometryType(), sRs)
		#writer = QgsVectorFileWriter(outPath, "UTF-8", fieldList, polyProvider.geometryType(), sRs)
		while polyProvider.nextFeature(inFeat):
			inGeom = inFeat.geometry()
			atMap = inFeat.attributeMap()
			lineList = []
			length = 0
			#(check, lineList) = lineLayer.featuresInRectangle(inGeom.boundingBox(), True, False)
			lineLayer.select(inGeom.boundingBox(), False)
			lineList = lineLayer.selectedFeatures()
			if len(lineList) > 0: check = 0
			else: check = 1
			if check == 0:
				for i in lineList:
					if inGeom.intersects(i.geometry()):
						outGeom = inGeom.intersection(i.geometry())
						length = length + distArea.measure(outGeom)
			outFeat.setGeometry(inGeom)
			outFeat.setAttributeMap(atMap)
			outFeat.addAttribute(index, QVariant(length))
			writer.addFeature(outFeat)
			start = start + 1
			progressBar.setValue(start)
		del writer
				
	def getVectorLayerByName(self, myName):
		mc = self.iface.mapCanvas()
		nLayers = mc.layerCount()
		for l in range(nLayers):
			layer = mc.layer(l)
			if layer.name() == unicode(myName):
				vlayer = QgsVectorLayer(unicode(layer.source()),  unicode(myName),  unicode(layer.dataProvider().name()))
				if vlayer.isValid():
					return vlayer
				else:
					QMessageBox.information(self, "Sum Line Lengths In Polyons", "Vector layer is not valid")

	def getFieldList(self, vlayer):
		fProvider = vlayer.dataProvider()
		feat = QgsFeature()
		allAttrs = fProvider.attributeIndexes()
		fProvider.select(allAttrs)
		myFields = fProvider.fields()
		return myFields
