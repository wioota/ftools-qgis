from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *
import ftools_utils
from frmVoronoi import Ui_Dialog
import voronoi

class Dialog( QDialog, Ui_Dialog ):
	def __init__( self, iface ):
		QDialog.__init__( self )
		self.iface = iface
		# Set up the user interface from Designer.
		self.setupUi( self )
		self.polygons = False
		QObject.connect (self.outTool, SIGNAL( "clicked()" ), self.outFile )

		layer_list = ftools_utils.getLayerNames( [ QGis.Point, QGis.Line, QGis.Polygon ] )
		self.inShape.addItems( layer_list )

	def accept(self):
		if self.inShape.currentText() == "":
			QMessageBox.information(self, "Voronoi/Thiessen tesselation", "Please specify input point layer")
		elif self.outShape.text() == "":
			QMessageBox.information(self, "Voronoi/Thiessen tesselations", "Please specify output polygon shapefile")
		else:
			self.outShape.clear()
			self.vlayer = ftools_utils.getVectorLayerByName( self.inShape.currentText() )
			self.voronoi_polygons()


	def outFile(self):
		self.outShape.clear()
		(self.shapefileName, self.encoding) = ftools_utils.saveDialog(self)
		if self.shapefileName is None or self.encoding is None:
			return
		self.outShape.setText(QString(self.shapefileName))

	def voronoi_polygons( self ):
		vprovider = self.vlayer.dataProvider()
		allAttrs = vprovider.attributeIndexes()
		vprovider.select( allAttrs )
		fields = vprovider.fields()
		if self.polygons:
			geom_type = QGis.WKBPolygon
		else:
			geom_type = QGis.WKBLineString
		writer = QgsVectorFileWriter( self.shapefileName, self.encoding, 
		fields, geom_type, vprovider.crs() )
		inFeat = QgsFeature()
		points = []
		
		while vprovider.nextFeature( inFeat ):
			inGeom = QgsGeometry( inFeat.geometry() )
			point = inGeom.asPoint()
			points.append( point )
		vprovider.rewind()
		vprovider.select( allAttrs )
		if False:
			self.delaunay_triangulation( writer, vprovider, points )
		else:
			self.voronoi_tesselation( writer, vprovider, points )


	def voronoi_tesselation( self, writer, provider, points ):
		coords, equation, edges, bounds = voronoi.computeVoronoiDiagram( points )
		all_attrs = provider.attributeIndexes()
		provider.select( all_attrs )
		feat = QgsFeature()
		count = 0
		for index,v1,v2 in edges:
			a,b,c = equation[ index ]
			x_0,y_0 = coords[ v1 ]
			x_1,y_1 = coords[ v2 ]
			if v1 < 0:
				if a == 1.0:
					if b < 0:
						y = bounds[1]
					elif b > 0:
						y = bounds[3]
					x = c - b * y
				else: # b ==1
					if a < 0:
						y = bounds[1]
					elif a > 0:
						y = bounds[3]
					x = ( c - y ) / a
				if x < bounds[0] or x > bounds[2]:
					if x < bounds[0]:
						x = bounds[0]
					elif x > bounds[2]:
						x = bounds[2]
					if a == 1:
						y = ( c - x ) / b
					else: # b == 1
						y = c - a * x
				x_0 = x
				y_0 = y
			elif v2 < 0:
				if a == 1.0:
					y = bounds[1]
					x = ( c - b * y )
					if x < bounds[0] or x > bounds[2]:
						if x < bounds[0]:
							x = bounds[0]
						elif x > bounds[2]:
							x = bounds[2]
						y = ( c - x ) / b
				elif b == 1.0:
					if a < 0:
						x = bounds[2]
					elif a > 0:
						x = bounds[0]
					y = ( c - a * x )
					if y < bounds[1] or y > bounds[3]:
						if y < bounds[1]:
							y = bounds[1]
						elif y > bounds[3]:
							y = bounds[3]
						x = ( c - y ) / a
				x_1 = x
				y_1 = y
			else:
				x_0,y_0 = coords[ v1 ]
				x_1,y_1 = coords[ v2 ]
			line = [ QgsPoint( x_0, y_0 ), QgsPoint( x_1, y_1 ) ]
			geometry = QgsGeometry().fromPolyline( line )
#			feat.addAttribute(0,QVariant(test))
			feat.setGeometry( geometry )
			writer.addFeature( feat )
		rect = [ 
		QgsPoint( bounds[0],bounds[1] ),
		QgsPoint( bounds[2], bounds[1] ),
		QgsPoint( bounds[2], bounds[3] ),
		QgsPoint( bounds[0], bounds[3] ),
		QgsPoint( bounds[0],bounds[1] ) ]
		geometry = QgsGeometry().fromPolyline( rect )
		feat.setGeometry( geometry )
		writer.addFeature( feat )
		del writer
			
		
	def delaunay_triangulation( self, writer, provider, points ):
		triangles = voronoi.computeDelaunayTriangulation( points )
		all_attrs = provider.attributeIndexes()
		provider.select( all_attrs )
		feat = QgsFeature()
		for triangle in triangles:
			indicies = list( triangle )
			indicies.append( indicies[ 0 ] )
			polygon = []
			for index in indicies:
				provider.featureAtId( index, feat, True,  all_attrs)
				geom = QgsGeometry( feat.geometry() )
				point = QgsPoint( geom.asPoint() )
				polygon.append( point )
			geometry = QgsGeometry().fromPolygon( [ polygon ] )
			feat.setGeometry( geometry )
			writer.addFeature( feat )
		del writer

	def out_codes( x, y ):
		code = 0; 
		if y > bounds.yMaximum():
			code += 1 # code for above
		elif y < bounds.yMinimum():
			code += 2 # code for below
		if x > bounds.xMaximum():
			code += 4 # code for right
		elif x < bounds.xMinimum():
			code += 8 # code for left
		return Code
		
	def reject_check( out_code1, out_code2 ):
		if not out_code1 == 0 and not out_code2 == 0:
			return True
		return False

	def accept_check( out_code1, out_code2 ):
		if out_code1 == 0 and out_code2 == 0:
			return True
		return False

	def cohen_sutherland_clip( point1, point2, bounds ):
		while True:
			outCode0 = self.out_codes( point1 )
			outCode1 = self.out_codes( point2 )
			if self.reject_check( outCode0, outCode1 ):
				return False
			if self.accept_check( outCode0, outCode1 ):
				return True
			if outCode0 == 0:
				tempCoord = point0[ 0 ]
				point0[ 0 ] = point1[ 0 ]
				point1[ 0 ] = tempCoord
				tempCoord = point0[ 1 ]
				point0[ 1 ]= point1[ 1 ]
				point1[ 1 ] = tempCoord
				tempCode = outCode0
				outCode0 = outCode1
				outCode1 = tempCode
			if not ( outCode0 & 1 ) == 0:
				point0[ 0 ] += ( point0[ 1 ] - point0[ 0 ] ) * ( bounds.yMaximum() - point0[ 1 ] ) / ( point1[ 1 ] - point0[ 1 ] )
				point0[ 1 ] = bounds.yMaximum()
			elif not ( outCode0 & 2 ) == 0:
				point0[ 0 ] += ( point1[ 0 ] - point0[ 0 ] ) * ( bounds.yMinimum() - point0[ 1 ] ) / ( point1[ 1 ] - point0[ 1 ] )
				point0[ 1 ] = bounds.yMinimym()
			elif not ( outCode0 & 4 ) == 0:
				point0[ 1 ] += ( point1[ 1 ] - point0[ 1 ] ) * ( bounds.xMaximum() - point0[ 0 ] ) / ( point1[ 0 ] - point0[ 0 ] )
				point0[ 0 ] = bounds.xMaximum()
			elif not ( outCode0 & 8 ) == 0:
				point0[ 1 ] += ( point1[ 1 ] - point0[ 1 ] ) * ( bounds.xMinimum() - point0[ 0 ] ) / ( point1[ 0 ] - point0[ 0 ] )
				point0[ 0 ] = bounds.xMinimum()


