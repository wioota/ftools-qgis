#-----------------------------------------------------------
# 
# manageR
#
# A QGIS plugin for loosely coupling QGIS with the R statistical
# programming language. Allows uplaod of QGIS layers directly
# into R, and the ability to perform R operations on the data
# directly from within QGIS.
#
# Copyright (C) 2008  Carson Farmer
#
# EMAIL: carson.farmer@gmail.com
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
import doLoadRLayer
import doRAnalysis
import doSaveRLayer
from frmManageR import Ui_Dialog
try:
	from rpy import *
except:
	try:
		import rpy2.rpy_classic as rpy
	except:
		QMessageBox.warning(self, "manageR", "Unable to load manageR: Required package rpy was unable to load"
							+ "\nPlease ensure that both R, and the corresponding version of Rpy are correctly installed.")

class Dialog(QDialog, Ui_Dialog):
	def __init__(self, iface):
		QDialog.__init__(self)
		set_default_mode(BASIC_CONVERSION)
		self.iface = iface
		# Set up the user interface from Designer.
		self.setupUi(self)
		self.setWindowIcon(QIcon(":/manage.png"))
		self.setWindowFlags(Qt.Window)
		self.txtMulti.hide()
		self.multiArrow.hide()
		self.btnSingle.hide()
		self.btnAbout.setIcon(QIcon(":/managehelp.png"))
		self.btnSingle.setIcon(QIcon(":/multi.png"))
		self.btnEntered.hide()
		self.btnEntered.setIcon(QIcon(":/entered.png"))
		self.btnMulti.setIcon(QIcon(":/single.png"))
		self.currentInShape = QgsVectorLayer("", "", "")
		self.currentOutShape = None
		# Set up the signal connections to watch for certain actions
		#QObject.connect(self.iface.mainWindow(), SIGNAL("lastWindowClosed()"), self.closeEvent)
		# The above appears to make no difference: TODO: Figure out how to catch this and ask for save?
		QObject.connect(self.txtInput, SIGNAL("returnPressed()"), self.entered)
		QObject.connect(self.btnData, SIGNAL("clicked()"), self.getDataFrame)
		QObject.connect(self.btnAbout, SIGNAL("clicked()"), self.helprun)
		QObject.connect(self.btnLoad, SIGNAL("clicked()"), self.load)
		QObject.connect(self.btnExport, SIGNAL("clicked()"), self.export)
		QObject.connect(self.btnClose, SIGNAL("clicked()"), self.closeEvent)
		QObject.connect(self.btnSave, SIGNAL("clicked()"), self.save)
		QObject.connect(self.btnMulti, SIGNAL("clicked()"), self.expand)
		QObject.connect(self.btnSingle, SIGNAL("clicked()"), self.expand)
		QObject.connect(self.btnEntered, SIGNAL("clicked()"), self.entered)
		self.mapCanvas = self.iface.mapCanvas()
		QObject.connect(self.mapCanvas, SIGNAL("layersChanged()"), self.update)
		QObject.connect(self.inShape, SIGNAL("currentIndexChanged(QString)"), self.updateInShape)
		# Populate layer list
		self.update()
		#self.updateObs()
		# Show welcome and license info
		self.txtMain.append("Welcome to manageR v" + self.instVersion() + "\nQGIS interface to the R statistical analysis program\n")
		self.txtMain.append("Copyright (C) 2008  Carson Farmer\n")
		self.txtMain.append("Licensed under the terms of GNU GPL 2\nmanageR is free software; you can redistribute it "
							+ "and/or modify it under the terms of the GNU General Public License as published by the "
							+ "Free Software Foundation; either version 2 of the License, or (at your option) any later "
							+ "version.\n\n For licensing information for R type 'license()' or 'licence()' into the "
							+ "manageR console./n For licensing information for Rpy see http://rpy.sourceforge.net/rpy/"
							+ "README\nCurrently running " + str(r.version['version.string']) + "\n")
		self.commandList = []
		self.commandIndex = 0

# This is used each time the input layer combo box is changed
# It automatically updates self.currentInShape to save time 
# for other functions that require this as input
	def updateInShape(self, inName):
		self.currentInShape = self.getMapLayerByName(inName)

# Display a short description of manageR
# Also indicates the currently installed version of manageR,
# and the official manageR webpage
	def helprun(self):
		infoString = QString("manageR v" + self.instVersion() +" - Interface to the R statistical analysis program\n")
		infoString = infoString.append("Copyright (C) 2008 Carson J.Q. Farmer\ncarson.farmer@gmail.com\nhttp://www.ftools.ca/manageR.html\n")
		infoString = infoString.append("manageR loosely couples QGIS with the R statistical "
									+ "programming language. Allows upload of QGIS layers directly "
									+ "into R, and the ability to perform R operations on the data "
									+ "directly from within QGIS. It interfaces with R using RPy, "
									+ "which is a Python interface to the R Programming Language.\n\n")
		infoString = infoString.append("Features:\n"
									+ "- Perform complex statistical analysis functions on raster, vector "
									+ "and spatial database formats\n"
									+ "- Use the R statistical environment to graph, plot, and map spatial "
									+ "and aspatial data from within QGIS\n"
									+ "- Export R (sp) vector layers directly to QGIS map canvas as QGIS "
									+ "vector layers\n"
									+ "- Perform almost all available R commands from within QGIS, including "
									+ "multi-line commands\n"
									+ "- Read QGIS vector layers directly from map canvas as R (sp) vector "
									+ "layers, allowing analysis to be carried out on any "
									+ "vector format supported by QGIS")
		QMessageBox.information(self.iface.mainWindow(), "About manageR", infoString)

# This function controls the current input console type
# Default is single line console, but when the down arrow is
# pressed, it switches to a multi-line console.
# When multi-line console is used, the return arrow button is
# made visible to allow submission of R commands
	def expand(self):
		if self.txtMulti.isHidden():
			self.inputArrow.hide()
			self.multiArrow.show()
			self.txtInput.hide()
			self.txtMulti.show()
			self.btnMulti.hide()
			self.btnSingle.show()
			self.btnEntered.show()
			self.txtMulti.insertPlainText(self.txtInput.text())
			self.txtInput.clear()
		else:
			self.multiArrow.hide()
			self.inputArrow.show()
			self.txtMulti.hide()
			self.txtInput.show()
			self.btnMulti.show()
			self.btnSingle.hide()
			self.btnEntered.hide()
			self.txtInput.insert(self.txtMulti.toPlainText())
			self.txtMulti.clear()

# This is the current version of manageR
# This function is used solely so that it is easy
# get the version number for updates and displaying
	def instVersion(self):
		return "0.4"

# Grab all the layers in the TOC
# Used by several other functions
	def update(self):
		self.inShape.clear()
		layermap = QgsMapLayerRegistry.instance().mapLayers()
		for name, layer in layermap.iteritems():
			self.inShape.addItem( unicode( layer.name() ) )

# If up or down are pressed, redo/undo the last commands
# This is just a simple way of being able to quickly redo
# commands without having to cut and paste...
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Up:
			if len(self.commandList) >= 1:
				if self.commandIndex <= 1:
					self.commandIndex = 0
				else:
					self.commandIndex -= 1
				if self.txtMulti.isHidden():
					self.txtInput.setText(self.commandList[self.commandIndex])
		elif event.key() == Qt.Key_Down:
			if len(self.commandList) >= 1:
				self.commandIndex += 1
				if self.commandIndex >= len(self.commandList):
					self.commandIndex = len(self.commandList)
					if self.txtMulti.isHidden():
						self.txtInput.clear()
					else:
						self.txtMulti.clear()
				else:
					if self.txtMulti.isHidden():
						self.txtInput.setText(self.commandList[self.commandIndex])

# Close the dialog and remove all R objects from memory
# This is used to release memory from the R interpreter
# Don't know if this actually works or not?
	def closeEvent(self, ask = True):
		askSave = QMessageBox.question(self, "manageR", "Save workspace image?", QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel)
		if askSave == QMessageBox.Yes:
			r.save_image(file_ = ".Rdata")
			if self.chkClear.isChecked():
				r.rm(list_ = r.ls(all_ = True))
				r.gc()
			r.graphics_off()
			self.reject()
		elif not askSave == QMessageBox.Cancel:
			if self.chkClear.isChecked():
				r.rm(list_ = r.ls(all_ = True))
				r.gc()
			r.graphics_off()
			self.reject()

# This is used whenever we check for sp objects in manageR
# TODO: Find a better way to implement this
	def updateObs(self):
		self.outShape.clear()
		set_default_mode(BASIC_CONVERSION)
		items = list()
		if type(r.ls()) == type(" "):
			items.append(r.ls())
		else:
			items = r.ls()
		for i in items:
			exec "check = r(''' capture.output(class(" + i + ")[1]) ''')"
			if check == '[1] "SpatialPointsDataFrame"' or check == '[1] "SpatialPolygonsDataFrame"' or check == '[1] "SpatialLinesDataFrame"' or check == '[1] "SpatialGridDataFrame"' or check == '[1] "SpatialPixelsDataFrame"':
				self.outShape.addItem(i)

# Checks if an R spatial object is a vector or raster layer
	def checkObs(self, inName):
		set_default_mode(NO_DEFAULT)
		exec "check = r(''' capture.output(class(" + str(inName) + ")[1]) ''')"
		if check == '[1] "SpatialPointsDataFrame"' or check == '[1] "SpatialPolygonsDataFrame"' or check == '[1] "SpatialLinesDataFrame"':
			return True
		elif check == '[1] "SpatialGridDataFrame"' or check == '[1] "SpatialPixelsDataFrame"':
			return False
		else:
			return None

# This is used whenever the user clicks the save button
# Used to save R sp objects as gdal/org files
	def save(self):
		if not doLoadRLayer.checkPack("rgdal"):
			QMessageBox.information(self, "manageR", "Unable to find R package 'rgdal'.\n "
			+ "\n Please manually install the 'rgdal' package in R via install.packages() (or another preferred method).")
		# If there is no input layer, tell user...
		if self.outShape.currentText() == "":
			QMessageBox.information(self, "manageR", "No R spatial object specified")
		else:
			checkVect = self.checkObs(self.outShape.currentText())
			if checkVect:
				(check, output) = doSaveRLayer.saveOgr(self, self.outShape.currentText())
				self.txtMain.append(output)
			elif not checkVect:
				(check, output) = doSaveRLayer.saveGdal(self, self.outShape.currentText())
				self.txtMain.append(output)
			else:
				self.txtMain.append("Unrecognized sp object, cannot save to file.")

# Converts a QgsVectorLayer to an R Spatial*DataFrame
# Provides the ability to load any vector layer that QGIS
# supports into R. Only selected features will be imported into R
	def getSpatialDataFrame(self, mlayer):
		if not doLoadRLayer.checkPack("sp"):
			QMessageBox.information(self, "manageR", "Unable to find R package 'sp'.\n "
			+ "\n Please manually install the 'sp' package in R via install.packages() (or another preferred method).")
		else:
			#if self.inShape.currentText() == "":
			if not self.currentInShape.isValid():
				QMessageBox.information(self, "manageR", "No valid input layer specified")
			else:
				self.btnData.setEnabled(False)
				#layerName = self.inShape.currentText()
				#mlayer = self.getMapLayerByName(layerName)
				mlayer = self.currentInShape
				if mlayer.type() == mlayer.VectorLayer:
					#self.txtMain.append("Loading " + str(layerName) + " ...")
					(spatialDataFrame, rows, columns, extra) = doRAnalysis.getSpatialDataFrame(mlayer, True)
					if not spatialDataFrame == False:
						r.assign(str(mlayer.name()), spatialDataFrame)
						self.updateObs()
						self.txtMain.append("QGis Vector Layer")
						self.txtMain.append("with " + str(rows) + " rows and " + str(columns) + " columns")
						if not extra == "":
							self.txtMain.append(extra)
					else:
						self.txtMain.append(rows + columns)
				else:
					QMessageBox.information(self, "manageR", "Cannot load raster layer attributes")
		self.btnData.setEnabled(True)

# Converts a QgsMapLayer attribute table to an R data.frame
# Faster than loading a spatial dataset into manageR, useful if user
# only needs vector layer attributes with no spatial information.
# If there are selected features, only their attributes will be 
# imported into R.
	def getDataFrame(self):
		#if self.inShape.currentText() == "":
		if not self.currentInShape.isValid():
			QMessageBox.information(self, "manageR", "No input layer specified")
		else:
			self.btnData.setEnabled(False)
			#layerName = self.inShape.currentText()
			#mlayer = self.getMapLayerByName(layerName)
			mlayer = self.currentInShape
			if mlayer.type() == mlayer.VectorLayer:
				self.txtMain.append("Loading data for " + str(mlayer.name()) + " ...")
				(dataFrame, rows, columns, extra) = doRAnalysis.getSpatialDataFrame(mlayer, False)
				if not dataFrame == False:
					r.assign(str(mlayer.name()), dataFrame)
					self.updateObs()
					self.txtMain.append("QGis Attribute Table")
					self.txtMain.append("with " + str(rows) + " rows and " + str(columns) + " columns")
					if not extra == "":
						self.txtMain.append(extra)
				else:
					self.txtMain.append(rows + columns)
			else:
				QMessageBox.information(self, "manageR", "Cannot load raster layer attributes")
			self.btnData.setEnabled(True)

# Performs conversion of txt input in manageR to R
# commands
	def commands(self, rInput, update):
		set_default_mode(NO_DEFAULT)
		try:
			exec "output = r(''' capture.output(" + str(rInput) + ") ''')"
			if update:
				if isinstance(output, list):
					for i in output:
						self.txtMain.append(str(i))
				else:
					self.txtMain.append(str(output))
			return True
		except RException, e:
			if update:
				self.txtMain.append(str(e))
			return False

# When enter is pressed, convert input to R commands
# This function gathers the R input, and
# uses self.commands to convert it
	def entered(self):
		if self.txtMulti.isHidden():
			expression = self.txtInput.text()
			self.txtInput.clear()
		else:
			expression = self.txtMulti.toPlainText()
			self.txtMulti.clear()
		if expression.contains("quit(") and expression.contains(")"):
			#self.close(False)
			self.close()
		else:
			self.txtMain.append(">" + expression)
			self.commandList.append(expression)
			self.commandIndex = len(self.commandList)
			self.commands(expression, True)
		self.updateObs()

# Initializes the data conversion
# This function is used to setup conversion
# to R spatial object
	def load(self):
		self.btnLoad.setDisabled(True)
		if self.inShape.currentText() == "":
			QMessageBox.information(self, "manageR", "No input layer specified")
		else:
			inName = self.inShape.currentText()
			self.txtMain.append("Loading " + str(inName) + " ...")
			self.convert(inName)
			self.updateObs()
		self.btnLoad.setEnabled(True)

# Converts stored spatial data to R spatial (sp) object
# For Raster layers, this function gives the map layer 
# source and name information to R and uses rgdal to load 
# the dataset
# TODO: Change this function so that it reads in all (including raster) QgsMapLayers
	def convert(self, inName):
		#mlayer = self.getMapLayerByName(inName)
		mlayer = self.currentInShape
		if mlayer.type() == mlayer.VectorLayer:
			self.getSpatialDataFrame(mlayer)
		else:
			if not doLoadRLayer.checkPack("rgdal"):
				QMessageBox.information(self, "manageR", "Unable to find R package 'rgdal'.\n "
				+ "\n Please manually install the 'rgdal' package in R via install.packages() (or another preferred method).")
			else:
				dsn = mlayer.source()
				layer = mlayer.name()
				dsn.replace("\\", "/")
				self.commands(str(inName) + " <- readGDAL(fname = '" + str(dsn) + "')", True) #moved from below...
				#if mlayer.type() == 0:
					#if str(mlayer.dataProvider().name()) == "postgres":
						#index1 = dsn.indexOf("dbname=")
						#index2 = dsn.indexOf("table=") - 1
						#dsn = dsn.section("", index1, index2).remove("'")
						#self.commands(str(inName) + " <- readOGR(dsn = 'PG:" + str(dsn) +"', layer = '" + str(layer) + "')", True)
					#else:
						#self.commands(str(inName) + " <- readOGR(dsn = '" + str(dsn) +"', layer = '" + str(layer) + "')", True)
				#elif mlayer.type() == 1:
					#self.commands(str(inName) + " <- readGDAL(fname = '" + str(dsn) + "')", True)
				#else:
					#self.txtMain.append("Unknown Layer Type")

# Gets map layer by layername in canvas 
# (both vector and raster)
	def getMapLayerByName(self, myName):
		#mc = self.iface.mapCanvas()
		nLayers = self.mapCanvas.layerCount()
		for l in range(nLayers):
			mlayer = self.mapCanvas.layer(l)
			if str(mlayer.name()) == str(myName):
				return mlayer

# This function is used to setup the 'convert' function from 'doLoadRLayer'
# It is used to convert R sp objects to a format recognized by QGIS
# and then it is added to the mapCanvas as a 'memory' layer
	def export(self):
		if not doLoadRLayer.checkPack("sp"):
			QMessageBox.information(self, "manageR", "Unable to find R package 'sp'.\n "
			+ "\n Please manually install the 'sp' package in R via install.packages() (or another preferred method).")
		# If there is no input layer, tell user...
		if self.outShape.currentText() == "":
			QMessageBox.information(self, "manageR", "No R spatial object specified")
		else:
			checkVect = self.checkObs(self.outShape.currentText())
			if checkVect:
				(check, result) = doLoadRLayer.convert(r.get(str(self.outShape.currentText())), str(self.outShape.currentText()))
				if not check: self.txtMain.append(result)
			elif not checkVect:
				QMessageBox.information(self, "manageR", "Unable to export raster layers to map canvas at this time.")
			else:
				QMessageBox.information(self, "manageR", "Unrecognized sp object, cannot save to file.")
