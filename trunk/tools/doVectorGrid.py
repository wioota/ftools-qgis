#-----------------------------------------------------------
# 
# Generate Vector Grid
#
# A QGIS plugin for generating a line or polygon grid
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
from frmVectorGrid import Ui_Dialog

class Dialog(QDialog, Ui_Dialog):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.toolOut, SIGNAL("clicked()"), self.outFile)
		QObject.connect(self.spnX, SIGNAL("valueChanged(double)"), self.offset)
		self.setWindowTitle("Vector grid")
		mapCanvas = self.iface.mapCanvas()
		for i in range(mapCanvas.layerCount()):
			layer = mapCanvas.layer(i)
			self.inShape.addItem(layer.name())

	def offset(self, value):
		if self.chkLock.isChecked():
			self.spnY.setValue(value)

	def accept(self):
		if not self.rdoCoordinates.isChecked() and self.inShape.currentText() == "":
			QMessageBox.information(self, "Generate Vector Grid", "Please specify input layer")
		elif self.rdoCoordinates.isChecked() and (self.xMin.text() == "" or self.xMax.text() == "" or self.yMin.text() == "" or self.yMax.text() == ""):
			QMessageBox.information(self, "Generate Vector Grid", "Please properly specify extent coordinates")
		elif self.outShape.text() == "":
			QMessageBox.information(self, "Generate Vector Grid", "Please specify output shapefile")
		else:
			inName = self.inShape.currentText()
			outPath = self.outShape.text()
			self.outShape.clear()
			if outPath.contains("\\"):
				outName = outPath.right((outPath.length() - outPath.lastIndexOf("\\")) - 1)
			else:
				outName = outPath.right((outPath.length() - outPath.lastIndexOf("/")) - 1)
			if outName.endsWith(".shp"):
				outName = outName.left(outName.length() - 4)
			if self.rdoBoundary.isChecked():
				mLayer = self.getMapLayerByName(unicode(inName))
				boundBox = mLayer.extent()
			else:
				boundBox = QgsRect(float(self.xMin.text()), float(self.yMin.text()), float(self.xMax.text()), float(self.yMax.text()))
			xSpace = self.spnX.value()
			ySpace = self.spnY.value()
			if self.rdoPolygons.isChecked(): polygon = True
			else: polygon = False
			self.compute(boundBox, outPath, xSpace, ySpace, polygon, self.progressBar)
			addToTOC = QMessageBox.question(self, "Generate Vector Grid", "Created output Shapefile:\n" + outPath 
				+ "\nNote: Layer has no associated coordinate system, please use the Projection Management Tool to specify spatial reference system."
				+ "\n\nWould you like to add the new layer to the TOC?", QMessageBox.Yes, QMessageBox.No, QMessageBox.NoButton)
			if addToTOC == QMessageBox.Yes:
				self.vlayer = QgsVectorLayer(outPath, unicode(outName), "ogr")
				QgsMapLayerRegistry.instance().addMapLayer(self.vlayer)
			self.progressBar.setValue(0)

	def compute(self, bound, outPath, xOffset, yOffset, polygon, progressBar):
		if polygon:
			fields = {0:QgsField("ID", QVariant.Int), 1:QgsField("XMIN", QVariant.Double), 2:QgsField("XMAX", QVariant.Double),
			3:QgsField("YMIN", QVariant.Double), 4:QgsField("YMAX", QVariant.Double)}
			check = QFile(self.shapefileName)
			if check.exists():
				if not QgsVectorFileWriter.deleteShapeFile(self.shapefileName):
					return
			writer = QgsVectorFileWriter(self.shapefileName, self.encoding, fields, QGis.WKBPolygon, None)
			#writer = QgsVectorFileWriter(outPath, "CP1250", fields, QGis.WKBPolygon, None)
		else:
			fields = {0:QgsField("ID", QVariant.Int), 1:QgsField("COORD", QVariant.Double)}
			check = QFile(self.shapefileName)
			if check.exists():
				if not QgsVectorFileWriter.deleteShapeFile(self.shapefileName):
					return
			writer = QgsVectorFileWriter(self.shapefileName, self.encoding, fields, QGis.WKBLineString, None)
			#writer = QgsVectorFileWriter(unicode(outPath), "CP1250", fields, QGis.WKBLineString, None)
		outFeat = QgsFeature()
		outGeom = QgsGeometry()
		idVar = 0
		progressBar.setRange(0,0)
		if not polygon:
			y = bound.yMaximum()
			while y >= bound.yMinimum():
				pt1 = QgsPoint(bound.xMinimum(), y)
				pt2 = QgsPoint(bound.xMaximum(), y)
				line = [pt1, pt2]
				outFeat.setGeometry(outGeom.fromPolyline(line))
				outFeat.addAttribute(0, QVariant(idVar))
				outFeat.addAttribute(1, QVariant(y))
				writer.addFeature(outFeat)
				y = y - yOffset
				idVar = idVar + 1
			x = bound.xMinimum()
			while x <= bound.xMaximum():
				pt1 = QgsPoint(x, bound.yMaximum())
				pt2 = QgsPoint(x, bound.yMinimum())
				line = [pt1, pt2]
				outFeat.setGeometry(outGeom.fromPolyline(line))
				outFeat.addAttribute(0, QVariant(idVar))
				outFeat.addAttribute(1, QVariant(x))
				writer.addFeature(outFeat)
				x = x + xOffset
				idVar = idVar + 1
		else:
			y = bound.yMaximum()
			while y >= bound.yMinimum():
				x = bound.xMinimum()
				while x <= bound.xMaximum():
					pt1 = QgsPoint(x, y)
					pt2 = QgsPoint(x + xOffset, y)
					pt3 = QgsPoint(x + xOffset, y - yOffset)
					pt4 = QgsPoint(x, y - yOffset)
					pt5 = QgsPoint(x, y)
					polygon = [[pt1, pt2, pt3, pt4, pt5]]
					outFeat.setGeometry(outGeom.fromPolygon(polygon))
					outFeat.addAttribute(0, QVariant(idVar))
					outFeat.addAttribute(1, QVariant(x))
					outFeat.addAttribute(2, QVariant(x + xOffset))
					outFeat.addAttribute(3, QVariant(y - yOffset))
					outFeat.addAttribute(4, QVariant(y))
					writer.addFeature(outFeat)
					idVar = idVar + 1
					x = x + xOffset
				y = y - yOffset
		progressBar.setRange(0,100)
		del writer

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

	def getVectorLayerByName(self, myName):
		mc = self.iface.mapCanvas()
		nLayers = mc.layerCount()
		for l in range(nLayers):
			layer = mc.layer(l)
			if unicode(layer.name()) == unicode(myName):
				vlayer = QgsVectorLayer(unicode(layer.source()),  unicode(myName),  unicode(layer.dataProvider().name()))
				if vlayer.isValid():
					return vlayer

	def getMapLayerByName(self, myName):
		mc = self.iface.mapCanvas()
		nLayers = mc.layerCount()
		for l in range(nLayers):
			layer = mc.layer(l)
			if unicode(layer.name()) == unicode(myName):
				if layer.isValid():
					return layer
