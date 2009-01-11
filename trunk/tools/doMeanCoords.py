from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from math import *
from frmMeanCoords import Ui_Dialog

class Dialog(QDialog, Ui_Dialog):
	def __init__(self, iface, function):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)
		self.updateUi()
		QObject.connect(self.toolOut, SIGNAL("clicked()"), self.outFile)
		QObject.connect(self.inShape, SIGNAL("currentIndexChanged(QString)"), self.update)

		# populate layer list
		self.progressBar.setValue(0)
		mapCanvas = self.iface.mapCanvas()
		for i in range(mapCanvas.layerCount()):
			layer = mapCanvas.layer(i)
			if layer.type() == layer.VectorLayer:
				self.inShape.addItem(layer.name())

	def updateUi(self):
		if self.function == 1:
			self.setWindowTitle("Mean coordinates")
			self.sizeValue.setVisible(False)
			self.label_size.setVisible(False)
		elif self.function == 2:
			self.setWindowTitle("Standard distance")
		self.resize(381, 100)

	def update(self, inputLayer):
		self.weightField.clear()
		self.uniqueField.clear()
		self.weightField.addItem("(Optional) Weight field")
		self.uniqueField.addItem("(Optional) Unique ID field")
		self.changedLayer = self.getVectorLayerByName(inputLayer)
		changedField = self.getFieldList(self.changedLayer)
		for i in changedField:
			if changedField[i].type() == QVariant.Int or changedField[i].type() == QVariant.Double:
				self.weightField.addItem(unicode(changedField[i].name()))
			self.uniqueField.addItem(unicode(changedField[i].name()))

	def accept(self):
		if self.inShape.currentText() == "":
			QMessageBox.information(self, "Coordinate statistics", "No input vector layer specified")
		elif self.outShape.text() == "":
			QMessageBox.information(self, "Coordinate statistics", "Please specify output shapefile")
		else:
			inName = self.inShape.currentText()
			outPath = self.outShape.text()

			if outPath.contains("\\"):
				outName = outPath.right((outPath.length() - outPath.lastIndexOf("\\")) - 1)
			else:
				outName = outPath.right((outPath.length() - outPath.lastIndexOf("/")) - 1)
			if outName.endsWith(".shp"):
				outName = outName.left(outName.length() - 4)
			self.compute(inName, outPath, self.weightField.currentText(), self.sizeValue.value(), self.uniqueField.currentText())
			self.progressBar.setValue(100)
			self.outShape.clear()
			addToTOC = QMessageBox.question(self, "Coordinate statistics", "Created output point Shapefile:\n" + outPath
				+ "\n\nWould you like to add the new layer to the TOC?", QMessageBox.Yes, QMessageBox.No, QMessageBox.NoButton)
			if addToTOC == QMessageBox.Yes:
				self.vlayer = QgsVectorLayer(outPath, unicode(outName), "ogr")
				if self.vlayer.geometryType() == QGis.Point:
					render = QgsSingleSymbolRenderer(QGis.Point)
					symbol = QgsSymbol(QGis.Point)
					symbol.setFillColor(Qt.red)
					symbol.setFillStyle(Qt.SolidPattern)
					symbol.setColor(Qt.red)
					symbol.setPointSize(5)
					render.addSymbol(symbol)
					self.vlayer.setRenderer(render)
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


	def compute(self, inName, outName, weightField="", times=1, uniqueField=""):
		vlayer = self.getVectorLayerByName(inName)
		provider = vlayer.dataProvider()
		weightIndex = provider.fieldNameIndex(weightField)
		uniqueIndex = provider.fieldNameIndex(uniqueField)
		feat = QgsFeature()
		allAttrs = provider.attributeIndexes()
		provider.select(allAttrs)
		sRs = provider.crs()
		check = QFile(self.shapefileName)
		if check.exists():
			if not QgsVectorFileWriter.deleteShapeFile(self.shapefileName):
				return
		if uniqueIndex <> -1:
			uniqueValues = self.getUniqueValues(provider, int(uniqueIndex))
			single = False
		else:
			uniqueValues = [QVariant(1)]
			single = True
		if self.function == 2:
			fieldList = { 0 : QgsField("STD_DIST", QVariant.Double), 1 : QgsField("UID", QVariant.String) }
			writer = QgsVectorFileWriter(self.shapefileName, self.encoding, fieldList, QGis.WKBPolygon, sRs)
		else:
			fieldList = { 0 : QgsField("MEAN_X", QVariant.Double), 1 : QgsField("MEAN_Y", QVariant.Double), 2 : QgsField("UID", QVariant.String)  }
			writer = QgsVectorFileWriter(self.shapefileName, self.encoding, fieldList, QGis.WKBPoint, sRs)
		outfeat = QgsFeature()
		points = []
		weights = []
		nFeat = provider.featureCount() * len(uniqueValues)
		nElement = 0
		self.progressBar.setValue(0)
		self.progressBar.setRange(0, nFeat)
		for j in uniqueValues:
			provider.rewind()
			while provider.nextFeature(feat):
				nElement += 1  
				self.progressBar.setValue(nElement)
				if single:
					check = j.toString().trimmed()
				else:
					check = feat.attributeMap()[uniqueIndex].toString().trimmed()
				if check == j.toString().trimmed():
					cx = 0.00
					cy = 0.00
					if weightIndex == -1:
						weight = 1.00
					else:
						weight = float(feat.attributeMap()[weightIndex].toDouble()[0])
					geom = QgsGeometry(feat.geometry())
					geom = self.extract(geom)
					for i in geom:
						cx += i.x()
						cy += i.y()
					points.append(QgsPoint((cx / len(geom)), (cy / len(geom))))
					weights.append(weight)
			sumWeight = sum(weights)
			cx = 0.00
			cy = 0.00
			item = 0
			for i in points:
				cx += i.x() * weights[item]
				cy += i.y() * weights[item]
				item += 1
			cx = cx / sumWeight
			cy = cy / sumWeight
			meanPoint = QgsPoint(cx, cy)
			if self.function == 2:
				values = []
				md = 0.00
				sd = 0.00
				dist = QgsDistanceArea()
				item = 0
				for i in points:
					tempDist = dist.measureLine(i, meanPoint)
					values.append(tempDist)
					item += 1
					md += tempDist
				md = md / item
				for i in values:
					sd += (i-md)*(i-md)
				sd = sqrt(sd/item)
				outfeat.setGeometry(QgsGeometry.fromPoint(meanPoint).buffer(sd * times, 10))
				outfeat.addAttribute(0, QVariant(sd))
				outfeat.addAttribute(1, QVariant(j))
			else:
				outfeat.setGeometry(QgsGeometry.fromPoint(meanPoint))
				outfeat.addAttribute(0, QVariant(cx))
				outfeat.addAttribute(1, QVariant(cy))
				outfeat.addAttribute(2, QVariant(j))
			writer.addFeature(outfeat)
			if single:
				break
		del writer
	    
# Gets vector layer by layername in canvas     
	def getVectorLayerByName(self, myName):
		mc = self.iface.mapCanvas()
		nLayers = mc.layerCount()
		for l in range(nLayers):
			layer = mc.layer(l)
			if layer.name() == unicode(myName):
				vlayer = QgsVectorLayer(unicode(layer.source()),  unicode(myName),  unicode(layer.dataProvider().name()))
				if vlayer.isValid():
					return vlayer

# Retreive the field map of a vector Layer     
	def getFieldList(self, vlayer):
		fProvider = vlayer.dataProvider()
		feat = QgsFeature()
		allAttrs = fProvider.attributeIndexes()
		# fetch all attributes for each feature
		fProvider.select(allAttrs)
		# retrieve all fields
		myFields = fProvider.fields()
		return myFields

	def extract(self, geom):
		multi_geom = QgsGeometry()
		temp_geom = []
		if geom.type() == 0: # it's a point
			if geom.isMultipart():
				temp_geom = geom.asMultiPoint()
			else:
				temp_geom.append(geom.asPoint())
		if geom.type() == 1: # it's a line
			if geom.isMultipart():
				multi_geom = geom.asMultiPolyline() #multi_geog is a multiline
				for i in multi_geom: #i is a line
					temp_geom.extend(i)
			else:
				temp_geom = geom.asPolyline()
		elif geom.type() == 2: # it's a polygon
			if geom.isMultipart():
				multi_geom = geom.asMultiPolygon() #multi_geom is a multipolygon
				for i in multi_geom: #i is a polygon
					for j in i: #j is a line
						temp_geom.extend(j)
			else:
				multi_geom = geom.asPolygon() #multi_geom is a polygon
				for i in multi_geom: #i is a line
					temp_geom.extend(i)
		return temp_geom

	def getUniqueValues(self, provider, index):
		allAttrs = provider.attributeIndexes()    
		provider.select(allAttrs)   
		f = QgsFeature()
		values = []
		check = []
		while provider.nextFeature( f ):
			if not f.attributeMap()[index].toString() in check:
				values.append( f.attributeMap()[index] )
				check.append( f.attributeMap()[index].toString() )
		return values   