from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from frmGeoprocessing import Ui_Dialog
import ftools_utils

class GeoprocessingDialog( QDialog, Ui_Dialog ):
	def __init__( self, iface, function ):
		QDialog.__init__( self )
		self.iface = iface
		self.setupUi( self )
		self.myFunction = function
		QObject.connect( self.btnBrowse, SIGNAL( "clicked()" ), self.outFile )
		if function == 4 or function == 1 or function == 2:
			QObject.connect( self.inShapeA, SIGNAL( "currentIndexChanged(QString)" ), self.update )
		self.manageGui()
		self.success = False
		self.cancel_close = self.buttonBox_2.button( QDialogButtonBox.Close )
		self.progressBar.setValue (0 )
		
	def update( self ):
		self.attrib.clear()
		inputLayer = unicode( self.inShapeA.currentText() )
		if inputLayer != "":
			changedLayer = ftools_utils.getVectorLayerByName( inputLayer )
			changedField = changedLayer.dataProvider().fields()
			for i in changedField:
				self.attrib.addItem( unicode( changedField[i].name() ) )
			if self.myFunction == 4:
				self.attrib.addItem( "--- " + self.tr( "Dissolve all" ) + " ---" )

	def accept( self ):
		if self.inShapeA.currentText() == "":
			QMessageBox.warning( self,  "Geoprocessing", self.tr( "Please specify an input layer" ) )		
		elif self.inShapeB.isVisible() and self.inShapeB.currentText() == "":
			QMessageBox.warning( self,  "Geoprocessing", self.tr( "Please specify a difference/intersect/union layer" ) )
		elif self.param.isEnabled() and self.param.isVisible() and self.param.text() == "":
			QMessageBox.warning( self, "Geoprocessing", self.tr( "Please specify valid buffer value" ) )
		elif self.attrib.isEnabled() and self.attrib.isVisible() and self.attrib.currentText() == "":
			QMessageBox.warning( self, "Geoprocessing", self.tr( "Please specify dissolve field" ) )
		elif self.outShape.text() == "":
			QMessageBox.warning( self, "Geoprocessing", self.tr( "Please specify output shapefile" ) )
		else: 
			self.outShape.clear()
			if self.attrib.isEnabled():
				self.geoprocessing( self.inShapeA.currentText(), self.inShapeB.currentText(), 
				unicode( self.attrib.currentText() ), self.mergeOutput.checkState() )
			else:
				if self.param.isEnabled() and self.param.isVisible():
					parameter = float( self.param.text() )
				else:
					parameter = None
				self.geoprocessing( self.inShapeA.currentText(), self.inShapeB.currentText(), 
				parameter, self.mergeOutput.checkState() )
  
	def outFile( self ):
		self.outShape.clear()
		( self.shapefileName, self.encoding ) = ftools_utils.saveDialog( self )
		if self.shapefileName is None or self.encoding is None:
			return
		self.outShape.setText( QString( self.shapefileName ) )

	def manageGui( self ):
		if self.myFunction == 1:  # Buffer
			self.label_2.hide()
			self.inShapeB.hide()
			self.label_4.hide()
			self.setWindowTitle( self.tr( "Buffer(s)" ) )
		elif self.myFunction == 2: # Convex hull
			self.label_2.hide()
			self.inShapeB.hide()
			self.rdoBuffer.setText( self.tr( "Create single minimum convex hull" ) )
			self.rdoField.setText( self.tr( "Create convex hulls based on input field" ) )
			self.label_4.hide()
			self.param.hide()
			self.setWindowTitle( self.tr( "Convex hull(s)" ) )    
			self.mergeOutput.hide()
		elif self.myFunction == 4: # Dissolve
			self.label_2.hide()
			self.inShapeB.hide()
			self.rdoBuffer.hide()
			self.attrib.setEnabled( True )
			self.param.hide()
			self.rdoField.hide()
			self.mergeOutput.hide()
			self.setWindowTitle( self.tr( "Dissolve" ) )
		else:
			self.rdoBuffer.hide()
			self.param.hide()
			self.label_4.hide()
			self.rdoField.hide()
			self.attrib.hide()
			self.mergeOutput.hide()
			if self.myFunction == 3: # Difference
				self.label_2.setText( self.tr( "Erase layer" ) )
				self.setWindowTitle( self.tr( "Difference" ) )
			elif self.myFunction == 5: # Intersect
				self.label_2.setText( self.tr( "Intersect layer" ) )
				self.setWindowTitle( self.tr( "Intersect" ) )
			elif self.myFunction == 7: # Symetrical difference
				self.label_2.setText( self.tr( "Difference layer" ) )
				self.setWindowTitle( self.tr( "Symetrical difference" ) )
			elif self.myFunction == 8: # Clip
				self.label_2.setText( self.tr( "Clip layer" ) )
				self.setWindowTitle( self.tr( "Clip" ) )
			else: # Union
				self.label_2.setText( self.tr( "Union layer" ) )
				self.setWindowTitle( self.tr( "Union" ) )
		self.resize(381, 100)
		myListA = []
		myListB = []
		self.inShapeA.clear()
		self.inShapeB.clear() 
        
		if self.myFunction == 5 or self.myFunction == 8 or self.myFunction == 3:
			myListA = ftools_utils.getLayerNames( [ QGis.Point, QGis.Line, QGis.Polygon ] )    
			myListB = ftools_utils.getLayerNames( [ QGis.Polygon ] )    
		elif self.myFunction == 7 or self.myFunction == 6:
			myListA = ftools_utils.getLayerNames( [ QGis.Polygon ] )
			myListB = ftools_utils.getLayerNames( [ QGis.Polygon ] )                 
		elif self.myFunction == 4:
			myListA = ftools_utils.getLayerNames( [ QGis.Polygon ] )                
			myListB = []
		else:
			myListA = ftools_utils.getLayerNames( [ QGis.Point, QGis.Line, QGis.Polygon ] )    
			myListB = ftools_utils.getLayerNames( [ QGis.Point, QGis.Line, QGis.Polygon ] )
		self.inShapeA.addItems( myListA )
		self.inShapeB.addItems( myListB )
		return

#1: Buffer
#2: Convex Hull
#3: Difference
#4: Dissolve
#5: Intersection
#6: Union
#7: Symetrical Difference
#8: Clip

	def geoprocessing(self,  myLayerA,  myLayerB,  myParam,  myMerge):
		print "starting geoprocessing..."
		vlayerA = ftools_utils.getVectorLayerByName( myLayerA )
		self.crs = vlayerA.dataProvider().crs()
		self.testThread = geoprocessingThread( self.iface.mainWindow(), self, self.myFunction, vlayerA, 
		myLayerB, myParam, myMerge )
		QObject.connect( self.testThread, SIGNAL( "runFinished(PyQt_PyObject)" ), self.runFinishedFromThread )
		QObject.connect( self.testThread, SIGNAL( "runStatus(PyQt_PyObject)" ), self.runStatusFromThread )
		QObject.connect( self.testThread, SIGNAL( "runRange(PyQt_PyObject)" ), self.runRangeFromThread )
		self.cancel_close.setText( "Cancel" )
		QObject.connect( self.cancel_close, SIGNAL( "clicked()" ), self.cancelThread )
		self.testThread.start()
		print "\n"
		return True

	def cancelThread( self ):
		self.testThread.stop()
		
	def runFinishedFromThread( self, output ):
		self.testThread.stop()
		check = QFile( self.shapefileName )
		if check.exists():
			if QgsVectorFileWriter.deleteShapeFile( self.shapefileName ):
				QMessageBox.warning( self, "Geoprocessing", self.tr( "Unable to create geoprocessing result." ) )
				return
		QgsVectorFileWriter.writeAsShapefile( output, self.shapefileName, self.encoding, None, False )
		# This is a hack since memory layer does not support projection information yet
		outputWkt = self.crs.toWkt()
		outputPrj = open( self.shapefileName.rstrip( ".shp" ) + ".prj", "w" )
		outputPrj.write( outputWkt )
		outputPrj.close()
		self.cancel_close.setText( "Close" )
		QObject.disconnect( self.cancel_close, SIGNAL( "clicked()" ), self.cancelThread )
		addToTOC = QMessageBox.question( self, "Geoprocessing", self.tr( "Created output shapefile:" ) + "\n" + unicode( self.shapefileName ) 
		+ "\n\n" + self.tr( "Would you like to add the new layer to the TOC?" ), QMessageBox.Yes, QMessageBox.No, QMessageBox.NoButton )
		if addToTOC == QMessageBox.Yes:
			ftools_utils.addShapeToCanvas( unicode( self.shapefileName ) )
		
	def runStatusFromThread( self, status ):
		self.progressBar.setValue( status )
        
	def runRangeFromThread( self, range_vals ):
		self.progressBar.setRange( range_vals[ 0 ], range_vals[ 1 ] )
		
class geoprocessingThread( QThread ):
	def __init__( self, parentThread, parentObject, function, vlayerA, myLayerB, myParam, myMerge ):
		QThread.__init__( self, parentThread )
		self.parent = parentObject
		self.running = False
		self.myFunction = function
		self.vlayerA = vlayerA
		self.myLayerB = myLayerB
		self.myParam = myParam
		self.myMerge = myMerge

	def run( self ):
		self.running = True
		if self.myFunction == 1 or self.myFunction == 2 or self.myFunction == 4:
			tempLayer = QgsVectorLayer( "Polygon", "TempLayer", "memory" )
			( self.myParam, useField ) = self.checkParameter( self.vlayerA, self.myParam )
			if not self.myParam is None:
				if self.myFunction == 1:
					output = self.buffering( tempLayer, self.vlayerA,  self.myParam, useField, self.myMerge )
				elif self.myFunction == 2:
					output = self.convex_hull( tempLayer, self.vlayerA,  self.myParam, useField )
				elif self.myFunction == 4:
					output = self.dissolve( tempLayer, self.vlayerA, self.myParam, useField )
		else:
			self.vlayerB = ftools_utils.getVectorLayerByName( self.myLayerB )
			tempLayer = QgsVectorLayer(ftools_utils.getVectorTypeAsString( self.vlayerA ), "TempLayer", "memory")
			if self.myFunction == 3:
				output = self.difference( tempLayer, self.vlayerA, self.vlayerB )
			elif self.myFunction == 5:
				output = self.intersect( tempLayer, self.vlayerA, self.vlayerB )
			elif self.myFunction == 6:
				output = self.union( tempLayer, self.vlayerA, self.vlayerB )
			elif self.myFunction == 7:    
				output = self.symetrical_difference( tempLayer, self.vlayerA, self.vlayerB )
			elif self.myFunction == 8:    
				output = self.clip( tempLayer, self.vlayerA, self.vlayerB )
		self.emit( SIGNAL( "runFinished(PyQt_PyObject)" ), output )
		self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), 0 )

	def stop(self):
		self.running = False

	def buffering( self, tempLayer, vlayerA,  myParam, useField, myMerge ):
		vproviderA = vlayerA.dataProvider()
		allAttrs = vproviderA.attributeIndexes()
		vproviderA.select( allAttrs )
		fields = vproviderA.fields()
		tempProvider = tempLayer.dataProvider()
		for ( index, field ) in fields.iteritems():
			tempProvider.addAttributes({ unicode( field.name() ) : ftools_utils.convertFieldNameType( unicode( field.typeName() ) ) } )
		outFeat = QgsFeature()
		inFeat = QgsFeature()
		inGeom = QgsGeometry()
		outGeom = QgsGeometry()
		nFeat = vproviderA.featureCount()
		nElement = 0
		self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), 0)
		self.emit( SIGNAL( "runRange(PyQt_PyObject)" ), ( 0, nFeat ) )
		if myMerge:
			first = True
			vproviderA.rewind()
			while vproviderA.nextFeature( inFeat ):
				nElement += 1
				self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), nElement )
				print '%s\r' % ''*20,
				print '%d%%' % int( float( nElement ) / float( nFeat ) * 100.00 ),
				atMap = inFeat.attributeMap()
				if useField:
					value = atMap[ myParam ].toDouble()[ 0 ]
				else:
					value = myParam
				inGeom = inFeat.geometry()
				outGeom = inGeom.buffer( float( value ), 5 )
				if first:
					tempGeom = QgsGeometry( outGeom )
					first = False
				else:
					tempGeom = tempGeom.combine( QgsGeometry( outGeom ) )
			outFeat.setGeometry( tempGeom )
			tempProvider.addFeatures( [ outFeat ] )
		else:
			vproviderA.rewind()
			while vproviderA.nextFeature( inFeat ):
				nElement += 1
				self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
				print '%s\r' % ''*20,
				print '%d%%' % int( float( nElement ) / float( nFeat ) * 100.00 ),
				atMap = inFeat.attributeMap()
				if useField:
					value = atMap[ myParam ].toDouble()[ 0 ]
				else:
					value = myParam
				inGeom = inFeat.geometry()
				outGeom = inGeom.buffer( float( value ), 5 )
				outFeat.setGeometry( outGeom )
				outFeat.setAttributeMap( atMap )
				tempProvider.addFeatures( [ outFeat ] )
			tempLayer.updateExtents()
		return tempLayer

	def convex_hull(self, tempLayer, vlayerA,  myParam, useField ):
		test = open( "/home/cfarmer/Desktop/test.txt", "w" )
		test.write( str( myParam ) )
		test.write( str( useField) )
		test.close()
		vproviderA = vlayerA.dataProvider()
		allAttrsA = vproviderA.attributeIndexes()
		vproviderA.select( allAttrsA )
		fields = vproviderA.fields()
		tempProvider = tempLayer.dataProvider()
		for ( index, field ) in fields.iteritems():
			tempProvider.addAttributes( { unicode( field.name() ) : ftools_utils.convertFieldNameType( unicode( field.typeName() ) ) } )
		inFeat = QgsFeature()
		outFeat = QgsFeature()
		inGeom = QgsGeometry()
		outGeom = QgsGeometry()
		if useField:
			unique = ftools_utils.getUniqueValues( vproviderA, myParam )
			nFeat = vproviderA.featureCount() * len( unique )
			nElement = 0
			self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), 0)
			self.emit( SIGNAL( "runRange(PyQt_PyObject)" ), ( 0, nFeat ) )
			for i in unique:
				vproviderA.rewind()
				hull = []
				first = True
				outID = 0
				while vproviderA.nextFeature( inFeat ):
					nElement += 1
					self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
					print '%s\r' % ''*20,
					print '%d%%' % int( float( nElement ) / float( nFeat ) * 100.00 ),
					atMap = inFeat.attributeMap()
					idVar = atMap[ myParam ]
					if idVar.toString().trimmed() == i.toString().trimmed():
						if first:
							outID = idVar
							first = False
						inGeom = inFeat.geometry()
						points = ftools_utils.extractPoints( inGeom )
						hull.extend( points )
				if len( hull ) >= 3:
					outGeom = outGeom.fromMultiPoint( hull ).convexHull()
					outFeat.setGeometry( outGeom )
					(area, perim) = self.simpleMeasure( outGeom )
					outFeat.addAttribute( 0, QVariant( outID ) )
					outFeat.addAttribute( 1, QVariant( area ) )
					outFeat.addAttribute( 2, QVariant( perim ) )
					tempProvider.addFeatures( [ outFeat ] )
		else:
			hull = []
			vproviderA.rewind()
			nFeat = vproviderA.featureCount()
			nElement = 0
			self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), 0)
			self.emit( SIGNAL( "runRange(PyQt_PyObject)" ), ( 0, nFeat ) )
			while vproviderA.nextFeature( inFeat ):
				nElement += 1
				self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
				print '%s\r' % ''*20,
				print '%d%%' % int( float( nElement ) / float( nFeat ) * 100.00 ),
				inGeom = inFeat.geometry()
				points = ftools_utils.extractPoints( inGeom )
				hull.extend( points )
			outGeom = outGeom.fromMultiPoint( hull ).convexHull()
			outFeat.setGeometry(outGeom)
			tempProvider.addFeatures( [ outFeat ] )
		tempLayer.updateExtents()
		return tempLayer

	def dissolve( self, tempLayer, vlayerA, myParam, useField ):
		vproviderA = vlayerA.dataProvider()
		allAttrsA = vproviderA.attributeIndexes()
		vproviderA.select( allAttrsA )
		fields = vproviderA.fields()
		tempProvider = tempLayer.dataProvider()
		for ( index, field ) in fields.iteritems():
			tempProvider.addAttributes( { unicode( field.name() ) : ftools_utils.convertFieldNameType( unicode( field.typeName() ) ) } )
		inFeat = QgsFeature()
		outFeat = QgsFeature()
		inGeom = QgsGeometry()
		outGeom = QgsGeometry()
		vproviderA.rewind()
		if useField:
			unique = ftools_utils.getUniqueValues( vproviderA, int( myParam ) )
		else:
			unique = [ 1 ]
		nFeat = vproviderA.featureCount() * len(unique)
		nElement = 0
		self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), 0)
		self.emit( SIGNAL( "runRange(PyQt_PyObject)" ), ( 0, nFeat ) )
		for item in unique:
			first = True
			vproviderA.rewind()
			while vproviderA.nextFeature( inFeat ):
				nElement += 1
				self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
				print '%s\r' % ''*20,
				print '%d%%' % int( float( nElement ) / float( nFeat ) * 100.00 ),
				if not useField:
					if first:
						attrs = inFeat.attributeMap()
						outFeat.setGeometry( QgsGeometry( inFeat.geometry() ) )
						first = False
					else:
						outFeat.setGeometry( QgsGeometry( outFeat.geometry().combine( inFeat.geometry() ) ) )
				else:
					if inFeat.attributeMap()[ myParam ].toString().trimmed() == item.toString().trimmed():
						if first:
							outFeat.setGeometry( QgsGeometry( inFeat.geometry() ) )
							first = False
							attrs = inFeat.attributeMap()
						else:
							outFeat.setGeometry( QgsGeometry( outFeat.geometry().combine( inFeat.geometry() ) ) )
			outFeat.setAttributeMap( attrs )
			tempProvider.addFeatures( [ outFeat ] )
		tempLayer.updateExtents()
		return tempLayer

	def difference(self, tempLayer, vlayerA, vlayerB ):
		vproviderA = vlayerA.dataProvider()
		allAttrsA = vproviderA.attributeIndexes()
		vproviderA.select( allAttrsA )
		vproviderB = vlayerB.dataProvider()
		allAttrsB = vproviderB.attributeIndexes()
		vproviderB.select( allAttrsB )
		fields = vproviderA.fields()
		tempProvider = tempLayer.dataProvider()
		for ( index, field ) in fields.iteritems():
			tempProvider.addAttributes( { unicode( field.name() ) : ftools_utils.convertFieldNameType( unicode( field.typeName() ) ) } )
		inFeatA = QgsFeature()
		inFeatB = QgsFeature()
		outFeat = QgsFeature()
		geom = QgsGeometry()
		index = ftools_utils.createIndex( vproviderB )
		nFeat = vproviderA.featureCount()
		nElement = 0
		self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), 0)
		self.emit( SIGNAL( "runRange(PyQt_PyObject)" ), ( 0, nFeat ) )
		vproviderA.rewind()
		while vproviderA.nextFeature( inFeatA ):
			nElement += 1
			self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
			print '%s\r' % ''*20,
			print '%d%%' % int( float( nElement ) / float( nFeat ) * 100.00 ),
			geom = inFeatA.geometry()
			atMap = inFeatA.attributeMap()
			intersects = index.intersects( geom.boundingBox() )
			for _id in intersects:
				vproviderB.featureAtId( int( _id ), inFeatB , True, allAttrsB )
				if geom.intersects( inFeatB.geometry() ):
					geom = geom.difference( inFeatB.geometry() )
			outFeat.setGeometry( geom )
			outFeat.setAttributeMap( atMap )
			tempProvider.addFeatures( [ outFeat ] )
		tempLayer.updateExtents()
		return tempLayer

	def intersect( self, tempLayer, vlayerA, vlayerB ):
		vproviderA = vlayerA.dataProvider()
		allAttrsA = vproviderA.attributeIndexes()
		vproviderA.select( allAttrsA )
		vproviderB = vlayerB.dataProvider()
		allAttrsB = vproviderB.attributeIndexes()
		vproviderB.select( allAttrsB )
		fields = ftools_utils.combineVectorFields( vlayerA, vlayerB )
		tempProvider = tempLayer.dataProvider()
		for ( index, field ) in fields.iteritems():
			tempProvider.addAttributes( { unicode( field.name() ) : ftools_utils.convertFieldNameType( unicode( field.typeName() ) ) } )
		inFeatA = QgsFeature()
		inFeatB = QgsFeature()
		outFeat = QgsFeature()
		geom = QgsGeometry()
		index = ftools_utils.createIndex( vproviderB )
		nFeat = vproviderA.featureCount()
		nElement = 0
		self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), 0)
		self.emit( SIGNAL( "runRange(PyQt_PyObject)" ), ( 0, nFeat ) )
		vproviderA.rewind()
		while vproviderA.nextFeature( inFeatA ):
			nElement += 1
			self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
			print '%s\r' % ''*20,
			print '%d%%' % int( float( nElement ) / float( nFeat ) * 100.00 ),
			geom = inFeatA.geometry()
			atMapA = inFeatA.attributeMap()    
			intersects = index.intersects( geom.boundingBox() )
			for _id in intersects: 
				vproviderB.featureAtId( int( _id ), inFeatB , True, allAttrsB )
				if geom.intersects( inFeatB.geometry() ):
					atMapB = inFeatB.attributeMap()
					result = geom.intersection( inFeatB.geometry() )
					outFeat.setGeometry( result )
					outFeat.setAttributeMap( ftools_utils.combineVectorAttributes( atMapA, atMapB ) )
					tempProvider.addFeatures( [ outFeat ] )
		tempLayer.updateExtents()
		return tempLayer

	def union(self, tempLayer, vlayerA, vlayerB ):
		vproviderA = vlayerA.dataProvider()
		allAttrsA = vproviderA.attributeIndexes()
		vproviderA.select( allAttrsA )
		vproviderB = vlayerB.dataProvider()
		allAttrsB = vproviderB.attributeIndexes()
		vproviderB.select( allAttrsB )
		fields = ftools_utils.combineVectorFields( vlayerA, vlayerB )
		tempProvider = tempLayer.dataProvider()
		for ( index, field ) in fields.iteritems():
			tempProvider.addAttributes( { unicode( field.name() ) : ftools_utils.convertFieldNameType( unicode( field.typeName() ) ) } )
		inFeatA = QgsFeature()
		inFeatB = QgsFeature()
		outFeat = QgsFeature()
		geom = QgsGeometry()
		diffGeom = QgsGeometry()
		indexA = ftools_utils.createIndex( vproviderB )
		indexB = ftools_utils.createIndex( vproviderA )
		nFeat = vproviderA.featureCount() * vproviderB.featureCount()
		nElement = 0
		self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), 0)
		self.emit( SIGNAL( "runRange(PyQt_PyObject)" ), ( 0, nFeat ) )
		vproviderA.rewind()
		while vproviderA.nextFeature( inFeatA ):
			nElement += 1
			self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
			print int( float( nElement ) / float( nFeat ) * 100.00 )
			found = False
			geom = QgsGeometry( inFeatA.geometry() )
			diffGeom = QgsGeometry( inFeatA.geometry() )
			atMapA = inFeatA.attributeMap()
			intersects = indexA.intersects( geom.boundingBox() )
			if len( intersects ) <= 0:
				outFeat.setGeometry( geom )
				outFeat.setAttributeMap( atMapA )
				tempProvider.addFeatures( [ outFeat ] )
			else:
				for _id in intersects:
					vproviderB.featureAtId( int( _id ), inFeatB , True, allAttrsB )
					atMapB = inFeatB.attributeMap()
					if geom.intersects( inFeatB.geometry() ):
						found = True
						diffGeom = diffGeom.difference( inFeatB.geometry() )
						result = geom.intersection( inFeatB.geometry() )
						outFeat.setGeometry( result )
						outFeat.setAttributeMap( ftools_utils.combineVectorAttributes( atMapA, atMapB ) )
						tempProvider.addFeatures( [ outFeat ] )
				if found:
					outFeat.setGeometry( diffGeom )
					outFeat.setAttributeMap( atMapA )
					tempProvider.addFeatures( [ outFeat ] )
		length = len( atMapA.values() )
		vproviderB.rewind()
		while vproviderB.nextFeature( inFeatA ):
			nElement += 1
			self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
			print int( float( nElement ) / float( nFeat ) * 100.00 ),
			geom = QgsGeometry( inFeatA.geometry() )
			atMap = inFeatA.attributeMap().values()
			atMap = dict( zip( range( length, length + len( atMap ) ), atMap ) )
			intersects = indexB.intersects( geom.boundingBox() )
			if len(intersects) <= 0:
				outFeat.setGeometry( geom )
				outFeat.setAttributeMap( atMapA )
				tempProvider.addFeatures( [ outFeat ] )
			else:
				for _id in intersects:
					vproviderA.featureAtId( int( _id ), inFeatB , True, allAttrsA )
					atMapB = inFeatB.attributeMap()
					if geom.intersects( inFeatB.geometry() ):
						geom = geom.difference( inFeatB.geometry() )
				outFeat.setGeometry( geom )
				outFeat.setAttributeMap( atMap )
				tempProvider.addFeatures( [ outFeat ] )
		tempLayer.updateExtents()
		return tempLayer

	def symetrical_difference( self, tempLayer, vlayerA, vlayerB ):
		vproviderA = vlayerA.dataProvider()
		allAttrsA = vproviderA.attributeIndexes()
		vproviderA.select( allAttrsA )
		vproviderB = vlayerB.dataProvider()
		allAttrsB = vproviderB.attributeIndexes()
		vproviderB.select( allAttrsB )
		fields = ftools_utils.combineVectorFields( vlayerA, vlayerB )
		tempProvider = tempLayer.dataProvider()
		for ( index, field ) in fields.iteritems():
			tempProvider.addAttributes( { unicode( field.name() ) : ftools_utils.convertFieldNameType( unicode( field.typeName() ) ) } )
		inFeatA = QgsFeature()
		inFeatB = QgsFeature()
		outFeat = QgsFeature()
		geom = QgsGeometry()
		indexA = ftools_utils.createIndex( vproviderB )
		indexB = ftools_utils.createIndex( vproviderA )
		nFeat = vproviderA.featureCount() * vproviderB.featureCount()
		nElement = 0
		self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), 0)
		self.emit( SIGNAL( "runRange(PyQt_PyObject)" ), ( 0, nFeat ) )
		vproviderA.rewind()
		while vproviderA.nextFeature( inFeatA ):
			nElement += 1
			self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
			print '%s\r' % ''*20,
			print '%d%%' % int( float( nElement ) / float( nFeat ) * 100.00 ),
			geom = inFeatA.geometry()
			atMapA = inFeatA.attributeMap()
			intersects = indexA.intersects( geom.boundingBox() )
			for _id in intersects:
				vproviderB.featureAtId( int( _id ), inFeatB , True, allAttrsB )
				if geom.intersects( inFeatB.geometry() ):
					geom = geom.difference( inFeatB.geometry() )        
			outFeat.setGeometry( geom )
			outFeat.setAttributeMap( atMapA )
			tempProvider.addFeatures( [ outFeat ] )
		length = len( atMapA.values() )
		vproviderB.rewind()
		while vproviderB.nextFeature( inFeatA ):
			nElement += 1
			self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
			print '%s\r' % ''*20,
			print '%d%%' % int( float( nElement ) / float( nFeat ) * 100.00 ),
			geom = inFeatA.geometry()
			atMap = inFeatA.attributeMap().values()
			atMap = dict( zip( range( length, length + len( atMap ) ), atMap ) )
			intersects = indexB.intersects( geom.boundingBox() )
			for _id in intersects:
				vproviderA.featureAtId( int( _id ), inFeatB , True, allAttrsA )
				if geom.intersects( inFeatB.geometry() ):
					geom = geom.difference( inFeatB.geometry() )      
			outFeat.setGeometry( geom )
			outFeat.setAttributeMap( atMap )
			tempProvider.addFeatures( [ outFeat ] )
		tempLayer.updateExtents()
		return tempLayer

	def clip( self, tempLayer, vlayerA, vlayerB ):
		vproviderA = vlayerA.dataProvider()
		allAttrsA = vproviderA.attributeIndexes()
		vproviderA.select( allAttrsA )
		vproviderB = vlayerB.dataProvider()
		allAttrsB = vproviderB.attributeIndexes()
		vproviderB.select( allAttrsB )
		fields = vproviderA.fields()
		tempProvider = tempLayer.dataProvider()
		for ( index, field ) in fields.iteritems():
			tempProvider.addAttributes( { unicode( field.name() ) : ftools_utils.convertFieldNameType( unicode( field.typeName() ) ) } )
		inFeatA = QgsFeature()
		inFeatB = QgsFeature()
		outFeat = QgsFeature()
		geom = QgsGeometry()
		outGeom = QgsGeometry()
		index = ftools_utils.createIndex(vproviderB)
		nFeat = vproviderA.featureCount()
		nElement = 0
		self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ), 0)
		self.emit( SIGNAL( "runRange(PyQt_PyObject)" ), ( 0, nFeat ) )
		vproviderA.rewind()
		while vproviderA.nextFeature( inFeatA ):
			nElement += 1
			self.emit( SIGNAL( "runStatus(PyQt_PyObject)" ),  nElement )
			print '%s\r' % ''*20,
			print '%d%%' % int( float( nElement ) / float( nFeat ) * 100.00 ),
			geom = inFeatA.geometry()
			atMap = inFeatA.attributeMap()    
			intersects = index.intersects( geom.boundingBox() )
			for _id in intersects:
				vproviderB.featureAtId( int( _id ), inFeatB , True, allAttrsB )
				if geom.intersects( inFeatB.geometry() ):  
					outGeom = geom.intersection( inFeatB.geometry() )
					outFeat.setGeometry( outGeom )
					outFeat.setAttributeMap( atMap )
					tempProvider.addFeatures( [ outFeat ] )
		tempLayer.updateExtents()
		return tempLayer

	def checkParameter( self, layer, param ):
		if self.myFunction == 1:
			if type( param ) == unicode:
				check = layer.dataProvider().fieldNameIndex( param )
				if check == -1:
					return ( None, False )
				else:
					return ( check, True )
			else:
				if type( param ) == float or type( param ) == int:
					return ( param, False )
				else:
					return ( None, False )
		elif self.myFunction == 2:
			if not param is None:
				if type( param ) == unicode:
					check = layer.dataProvider().fieldNameIndex( param )
					if check == -1:
						return ( None, False )
					else:
						return ( check, True )
				else:
					return ( None, False )
			else:
				return ( True, False )
		elif self.myFunction == 4:
			if type( param ) == unicode:
				check = layer.dataProvider().fieldNameIndex( param )
				if check == -1:
					return ( check, False )
				else:
					return ( check, True )
			else:
				return ( None, False )

	def simpleMeasure( self, inGeom ):
		if inGeom.wkbType() == QGis.WKBPoint:
			pt = QgsPoint()
			pt = inGeom.asPoint()
			attr1 = pt.x()
			attr2 = pt.y()
		else:
			measure = QgsDistanceArea()
			attr1 = measure.measure(inGeom)      
			if inGeom.type() == QGis.Polygon:
				attr2 = self.perimMeasure( inGeom, measure )
			else:
				attr2 = attr1
		return ( attr1, attr2 )

	def perimMeasure( self, inGeom, measure ):
		value = 0.00
		if inGeom.isMultipart():
			poly = inGeom.asMultiPolygon()
			for k in poly:
				for j in k:
					value = value + measure.measureLine( j )
		else:
			poly = inGeom.asPolygon()
			for k in poly:
				value = value + measure.measureLine( k )
		return value
