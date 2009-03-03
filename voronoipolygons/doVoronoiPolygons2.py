from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *
import ftools_utils
from frmVoronoi import Ui_Dialog

class Dialog( QDialog, Ui_Dialog ):
	def __init__( self, iface ):
		QDialog.__init__( self )
		self.iface = iface
		# Set up the user interface from Designer.
		self.setupUi( self )

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
			self.voronoi()


	def outFile(self):
		self.outShape.clear()
		(self.shapefileName, self.encoding) = ftools_utils.saveDialog(self)
		if self.shapefileName is None or self.encoding is None:
			return
		self.outShape.setText(QString(self.shapefileName))

	def voronoi( self ):
		vprovider = self.vlayer.dataProvider()
		allAttrs = vprovider.attributeIndexes()
		vprovider.select( allAttrs )
		fields = vprovider.fields()
		writer = QgsVectorFileWriter( self.shapefileName, self.encoding, 
		fields, QGis.WKBLineString, vprovider.crs() )
#		point_writer = QgsVectorFileWriter( "/home/cfarmer/Desktop/problem_layers/tests/intersections.shp", self.encoding, 
#		fields, QGis.WKBPoint, vprovider.crs() )
		line_writer = QgsVectorFileWriter( "/home/cfarmer/Desktop/problem_layers/tests/int_lines.shp", self.encoding, 
		fields, QGis.WKBLineString, vprovider.crs() )
		inFeat = QgsFeature()
		feat = QgsFeature()
		feature = QgsFeature()
		x1 = []
		y1 = []
		while vprovider.nextFeature( inFeat ):
			inGeom = QgsGeometry( inFeat.geometry() )
			inPoint = inGeom.asPoint()
			x1.append( inPoint.x() )
			y1.append( inPoint.y() )
		bounds = self.vlayer.extent()
		haba = bounds.xMaximum()
		taka = bounds.yMaximum()
		xmin = bounds.xMinimum()
		ymin = bounds.yMinimum()
		N = len( x1 )
		kx = []
		ky = []
		kz = []
		
		line_list = []


		for i in range(1, N ):
			for j  in range(i + 1, N + 1 ):
				#consider the bisector(perpendicular at midpoint) between i and j
				br = 0 # label
				kx = []
				ky = []
				di2 = float( y1[ i - 1 ] - y1[ j - 1 ] ) / float( x1[ i - 1 ] - x1[ j - 1 ] ) # the slope the line segment from i to j
				di = float( -1.00 / di2 ) # the slope of bisector(perpendicular at midpoint) between i and j
				cp2 = float( float( y1[ i - 1 ] + y1[ j - 1 ] ) / 2.00 ) # y-coordinate of midpoint of i and j
				cpx = float( float( x1[ i - 1 ] + x1[ j - 1 ] ) / 2.00 ) # x-coordinate of midpoint of i and j
				ys = float( cp2 - cpx * di ) # intercept of the bisector(perpendicular at midpoint) between i and j
				
				#Now, y = di * x +ys is the bisector(perpendicular at midpoint) between i and j.
				#So, every point (x,y) on this line has a property.
				#distance between i and (x,y) equals to the distance between j and (x,y).
				#So we can obtain region V(a_i) = {x|d(x,a_i)<=d(x,a_j) for j not i}, in this case, j is fixed.
				#Voronoi euqation is V(a_i) = {x|d(x,a_i)<=d(x,a_j) for all j not i}, in this case j is not fixed, for all j not i.
				#So, we must check line segments(group of points) on this bisector is nearer than any other j 
				# (not fixed, this j becomes k and u at later for-loop) 
				# we do this check loop- for(u=1;u<=N;u++)	u<>i, u<>j

				#Now, what are line segments(group of points)?
				# We want compare with any other j, So line segments are obtained from intersection between this bisector and the bisector of i and k(k is not i,j).
				t = float( x1[ i - 1 ] - x1[ j - 1 ] )**2.00 + float( y1[ i - 1 ] - y1[ j - 1 ] )**2.00 # distance between i and j
				
				# taka is the hight, haba is width of the screen, respectively
				#if intercept > 0 and < (the hight of the screen) then the start point of the bisector is ( 0, ys )
				if ys > ymin and ys < taka:
					x0 = xmin
					y0 = float( ys )
				else: # ys > 0 and ys < taka ys < 0 or ys> the hight of the screen
					if di > 0.00: # if slope>0 then the start point is (-ys/di,0)
						x0 = float( ( -1 * ys ) / di )
						y0 = ymin
					else: # if slope<0 then the start point is ((taka-ys)/di,taka)
						x0 = float( float( taka - ys ) / di )
						y0 = float( taka )

				yy = float( di * haba + ys ) # yy is the y-coordinate at x= the width of the screen
				if yy > ymin and yy < taka: # if yy>0 and yy<the hight of the screen then the end point of the bisector(perpendicular at midpoint) between i and j is (width of the screen,yy)
					xa1 = float( haba )
					ya1 = float( yy )
				else: # yy<0 or yy> the hight of the screen
					if di > 0: #	slope>0
						xa1 = float( float( taka - ys ) / di )
						ya1 = float( taka )
					else: # slope<0
						xa1 = float( float(-1 * ys ) / di )
						ya1 = ymin
						
				#QMessageBox.information(self, "Voronoi/Thiessen tesselation", " i: " + str(i) + " j: " + str(j) )
				line = [ QgsPoint( x0, y0 ), QgsPoint( xa1, ya1 ) ]
				line = QgsGeometry().fromPolyline( line )
				feat.setGeometry( line )
				line_writer.addFeature( feat )
		
				#calculate the intersection of the two bisectors (i,j) and (i,k)
				#first intersection is the start point of the bisector between i and j
				#l = 1
				kx.append( x0 ) # kx[ l - 1 ] = x0
				ky.append( y0 ) # ky[ l - 1 ] = y0 # start point of the bisector between i and j

				sa2 = x1[ j - 1 ] - x1[ i - 1 ] # difference of x between i and j
				sa4 = y1[ j - 1 ] - y1[ i - 1 ] # difference of y between i and j

				#calculate the intersection of the two bisectors (i,j) and (i,k), k is not i,j
				for k in range( 1, N + 1 ): # k=1,...,n
					if not k == i and not k == j: # k is not i and not j
						di4 = float( y1[ i - 1 ] - y1[ k - 1 ] ) / float( x1[ i - 1 ] - x1[ k - 1 ] ) # slope of the line connecting two points i and k
						di3 = float( -1.00 / di4 ) # slope of the bisector between i and k
						cp3 = float( float( y1[ i - 1 ] + y1[ k - 1 ] ) / 2.00 ) # y-cooridnate of the midpoint between i and k
						cpx3 = float( float( x1[ i - 1 ] + x1[ k - 1 ] ) / 2.00 ) # x-cooridnate of the midpoint between i and k
						ys3 = float( cp3 - cpx3 * di3 ) # intercept of the bisector between i and k
						#Now, y = di3 * x +ys3 is the bisector(perpendicular at midpoint) between i and k (k is not i,j)
						t2 = float( x1[ i - 1 ] - x1[ k - 1 ] )**2.00 + float( y1[ i - 1 ] - y1[ k - 1 ] )**2.00 # the distance between i and k

						# taka is the hight, haba is width of the screen, respectively
						#if intercept > 0 and < (the hight of the screen) then the start point of the bisector is ( 0, ys )
						if ys3 > ymin and ys3 < taka:
							x02 = xmin
							y02 = float( ys3 )
						else: # ys > 0 and ys < taka ys < 0 or ys> the hight of the screen
							if di3 > 0.00: # if slope>0 then the start point is (-ys/di,0)
								x02 = float( ( -1 * ys3 ) / di3 )
								y02 = ymin
							else: # if slope<0 then the start point is ((taka-ys)/di,taka)
								x02 = float( float( taka - ys3 ) / di3 )
								y02 = float( taka )

						yy = float( di3 * haba + ys3 ) # yy is the y-coordinate at x= the width of the screen
						if yy > ymin and yy < taka: # if yy>0 and yy<the hight of the screen then the end point of the bisector(perpendicular at midpoint) between i and j is (width of the screen,yy)
							xa12 = float( haba )
							ya12 = float( yy )
						else: # yy<0 or yy> the hight of the screen
							if di3 > 0: #	slope>0
								xa12 = float( float( taka - ys3 ) / di3 )
								ya12 = float( taka )
							else: # slope<0
								xa12 = float( float(-1 * ys3 ) / di3 )
								ya12 = ymin

						line_2 = [ QgsPoint( x02, y02 ), QgsPoint( xa12, ya12 ) ]
						line_2 = QgsGeometry().fromPolyline( line_2 )
#						feature.setGeometry( line_2 )
#						line_writer.addFeature( feature )
						if line.intersects( line_2 ):
							intersect = QgsGeometry( line.intersection( line_2 ) )
#							feature.setGeometry( intersect )
							#point_writer.addFeature( feature )
							kx.append( intersect.asPoint().x() )
							ky.append( intersect.asPoint().y() )
						else:
							br = 0
							break
								
				if br == 0:
					#l += 1 # set the end point as the intersection
					# kx[ l - 1 ] = xa1
					# ky[ l - 1 ] = ya1
					kx.append( xa1 )
					ky.append( ya1 )
					#writer2.addFeature( feat2 )
					#Now, on the bisector between i and j, y=di*x+ys, there are l intersections.
					#Sort these (kx,ky)
					#heapv( kx , ky, kz, l );# order (kx,ky) such that kx[0]<kx[1]<....<kx[l-1]
					ky = self.heapv( ky, kx )
					kx = self.heapv( kx, kx )
					for k in range( 1, len( ky ) ): # consider the intervals between two intersections
						k2 = k + 1 # k is the start point of the interval, k2 is the end point of the interval
						xx = float( float( kx[ k - 1 ] + kx[ k2 - 1 ] ) / 2.00 )# x-coordinate of the midpoint of the two intersections
						yy2 = float( di * xx + ys ) # y-coordinate of the midpoint of the two intersections
						ds = float( xx - x1[ i - 1 ] )**2.00 + float( yy2 - y1[ i - 1 ] )**2.00 # distance between the midpoint and i, it is the same of the distance between the midpoint and j
						#if this distance, ds is shorter than any other distance to u ( u is not i, j ), this line segment is OK
						#Voronoi euqation: V(a_i) = {x|d(x,a_i)<=d(x,a_j) for all j not i}, in this case j is not fixed, for all j not i.
						br2 = 0 # if this distance, ds is shorter than any other distance to u, br2 keeps 0.
						for u in range( 1, N + 1 ): # u<>i, u<>j
							if not u == i and not u == j:
								us = float( xx - x1[ u - 1 ] )**2.00 + float( yy2 - y1[ u - 1 ] )**2.00 # the distance between the midpoint and u
								if us < ds: # if the distance to u is smaller than the distance to j(i) then the bisector should not be drawn -> break
									br2 = 1
									break

						if br2 == 0: # if flag=0 then draw the interval
							xz = float( kx[ k - 1 ] )
							xz2 = float( kx[ k2 - 1 ] )
							yz = float( ky[ k - 1 ] )
							yz2 = float( ky[ k2 - 1 ] )
							line = [ QgsPoint( xz, yz ), QgsPoint( xz2, yz2 ) ]
							geometry = QgsGeometry().fromPolyline( line )
							feat.setGeometry( geometry )
							writer.addFeature( feat )
							QMessageBox.information(self, "Voronoi/Thiessen tesselation", str(i) )
							break # the bisector should be draw just once -> break
		del writer

	# sort list by sorted order of another list
	# sort s1 by s2
	def heapv( self, s1, s2 ):
		try:
		 	d = dict( izip( s2, s1 ) )
			assert not len( d ) == len( s2 )
			return [ d[ v ] for v in sorted( d ) ]
		except Exception:
			_indices = range( len( s1 ) )
			_indices.sort( key = s2.__getitem__ )
			return map( s1.__getitem__, _indices )
