#-----------------------------------------------------------
# 
# Generate Regular Points
#
# A QGIS plugin for generating a simple points
# shapefile of regularly spaced points. 
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
from random import *
from math import *
from frmRegPoints import Ui_Dialog

class Dialog(QDialog, Ui_Dialog):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		QObject.connect(self.toolOut, SIGNAL("clicked()"), self.outFile)
		self.setWindowTitle("Regular points")
		self.progressBar.setValue(0)
		mapCanvas = self.iface.mapCanvas()
		for i in range(mapCanvas.layerCount()):
			layer = mapCanvas.layer(i)
			self.inShape.addItem(layer.name())

	def accept(self):
		if not self.rdoCoordinates.isChecked() and self.inShape.currentText() == "":
			QMessageBox.information(self, "Generate Regular Points", "Please specify input layer")
		elif self.rdoCoordinates.isChecked() and (self.xMin.text() == "" or self.xMax.text() == "" or self.yMin.text() == "" or self.yMax.text() == ""):
			QMessageBox.information(self, "Generate Regular Points", "Please properly specify extent coordinates")
		elif self.outShape.text() == "":
			QMessageBox.information(self, "Generate Regular Points", "Please specify output shapefile")
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
			if self.rdoSpacing.isChecked(): value = self.spnSpacing.value()
			else: value = self.spnNumber.value()
			if self.chkRandom.isChecked(): offset = True
			else: offset = False
			if self.rdoBoundary.isChecked():
				mLayer = self.getMapLayerByName(unicode(inName))
				boundBox = mLayer.extent()
			else:
				boundBox = QgsRect(float(self.xMin.text()), float(self.yMin.text()), float(self.xMax.text()), float(self.yMax.text()))
			self.regularize(boundBox, outPath, offset, value, self.rdoSpacing.isChecked(), self.spnInset.value(), self.progressBar)
			addToTOC = QMessageBox.question(self, "Generate Regular Points", "Created output point Shapefile:\n" + outPath 
			+ "\nNote: Layer has no associated coordinate system, please use the Projection Management Tool to specify spatial reference system."
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
		check = QFileInfo(QFile(self.shapefileName))
		if check.baseName() == "":
			return
		self.encoding = unicode(encodingBox.currentText())
		self.outShape.clear()
		self.outShape.insert(self.shapefileName)
	
# Generate list of random points     
	def simpleRandom(self, n, bound, xmin, xmax, ymin, ymax):
		seed()
		points = []
		i = 1
		while i <= n:
			pGeom = QgsGeometry().fromPoint(QgsPoint(xmin + (xmax-xmin) * random(), ymin + (ymax-ymin) * random()))
			if pGeom.intersects(bound):
				points.append(pGeom)
				i = i + 1
		return points
	
# Get vector layer by name from TOC     
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
					QMessageBox.information(self, "Generate Regular Points", "Vector layer is not valid")
	
# Get map layer by name from TOC     
	def getMapLayerByName(self, myName):
		mc = self.iface.mapCanvas()
		nLayers = mc.layerCount()
		for l in range(nLayers):
			layer = mc.layer(l)
			if layer.name() == unicode(myName):
				if layer.isValid():
					return layer
	
 
	def regularize(self, bound, outPath, offset, value, gridType, inset, progressBar):
		area = bound.width() * bound.height()
		if offset:
			seed()
		if gridType:
			pointSpacing = value
		else:
			# Calculate grid spacing
			pointSpacing = sqrt(area / value)
		outFeat = QgsFeature()
		fields = { 0 : QgsField("ID", QVariant.Int) }
		check = QFile(self.shapefileName)
		if check.exists():
			if not QgsVectorFileWriter.deleteShapeFile(self.shapefileName):
				return
		writer = QgsVectorFileWriter(self.shapefileName, self.encoding, fields, QGis.WKBPoint, None)
		#writer = QgsVectorFileWriter(unicode(outPath), "CP1250", fields, QGis.WKBPoint, None)
		idVar = 0
		count = 10.00
		add = 90.00 / (area / pointSpacing)
		y = bound.yMaximum() - inset
		while y >= bound.yMinimum():
			x = bound.xMinimum() + inset
			while x <= bound.xMaximum():
				if offset:
					pGeom = QgsGeometry().fromPoint(QgsPoint(uniform(x - (pointSpacing / 2.0), x + (pointSpacing / 2.0)), 
					uniform(y - (pointSpacing / 2.0), y + (pointSpacing / 2.0))))
				else:
					pGeom = QgsGeometry().fromPoint(QgsPoint(x, y))
				if pGeom.intersects(bound):
					outFeat.setGeometry(pGeom)
					outFeat.addAttribute(0, QVariant(idVar))
					writer.addFeature(outFeat)
					idVar = idVar + 1
					x = x + pointSpacing
					count = count + add
					progressBar.setValue(count)
			y = y - pointSpacing
		del writer

