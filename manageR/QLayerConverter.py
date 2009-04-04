from PyQt4.QtCore import *
#from PyQt4.QtGui import *
from qgis.core import *
#import Numeric, array

import rpy2.robjects as robjects
import rpy2.rinterface as rinterface
import rpy2.rlike as rlike

class QVectorLayerConverter( QObject ):
  '''
  QVectorLayerConvert:
  This class is used to convert a QGIS
  vector layer to an R (sp) vector layer for use
  in the manageR R environment.
  '''

  def __init__( self, mlayer, data_only ):
    QObject.__init__( self )
    self.mlayer = mlayer
    self.data_only = data_only
    self.running = False

    env = rinterface.globalEnv
    # variables are retrived by 'getting' them from the global environment,
    # specifying that we want functions only, which avoids funtions being
    # masked by variable names
    self.as_character_ = robjects.conversion.ri2py(env.get('as.character',wantFun=True))
    self.data_frame_ = robjects.conversion.ri2py(env.get('data.frame',wantFun=True))
    self.matrix_ = robjects.conversion.ri2py(env.get('matrix',wantFun=True))
    self.unlist_ = robjects.conversion.ri2py(env.get('unlist',wantFun=True))
    if not self.data_only:
      # variables from package sp (only needed if featching geometries as well)
      self.CRS_ = robjects.conversion.ri2py(env.get('CRS',wantFun=True))
      self.Polygon_ = robjects.conversion.ri2py(env.get('Polygon',wantFun=True))
      self.Polygons_ = robjects.conversion.ri2py(env.get('Polygons',wantFun=True))
      self.SpatialPolygons_ = robjects.conversion.ri2py(env.get('SpatialPolygons',wantFun=True))
      self.Line_ = robjects.conversion.ri2py(env.get('Line',wantFun=True))
      self.Lines_ = robjects.conversion.ri2py(env.get('Lines',wantFun=True))
      self.SpatialLines_ = robjects.conversion.ri2py(env.get('SpatialLines',wantFun=True))
      self.SpatialPoints_ = robjects.conversion.ri2py(env.get('SpatialPoints',wantFun=True))
      self.SpatialPointsDataFrame_ = robjects.conversion.ri2py(env.get('SpatialPointsDataFrame',wantFun=True))
      self.SpatialLinesDataFrame_ = robjects.conversion.ri2py(env.get('SpatialLinesDataFrame',wantFun=True))
      self.SpatialPolygonsDataFrame_ = robjects.conversion.ri2py(env.get('SpatialPolygonsDataFrame',wantFun=True))

  def stop( self ):
    '''
    Kill thread
    '''
    self.running = False

  def start( self ):
    self.running = True
    provider = self.mlayer.dataProvider()
    extra = QString()
    if not self.data_only:
      sRs = provider.crs()
      if not sRs.isValid():
        projString = 'NA'
        extra.append( "Unable to determine projection information\nPlease specify using:\n" )
        extra.append( "e.g. layer@proj4string <- CRS('+proj=longlat +datum=NAD83')" )
      else:
        if not sRs.geographicFlag():
          projString = str( sRs.toProj4() )
        else:
          # TODO: Find better way to handle geographic coordinate systems
          # As far as I can tell, R does not like geographic coodinate systems input
          # into it's proj4string argument...
          projString = 'NA'
          extra.append( "Unable to determine projection information\nPlease specify using:\n" )
          extra.append( "layer@proj4string <- CRS('+proj=longlat +datum=NAD83') for example." )

    attrIndex = provider.attributeIndexes()
    provider.select(attrIndex)
    fields = provider.fields()
    if len( fields.keys() ) <= 0:
      message = QString( "Attribute table must have at least one field" )
      self.emit( SIGNAL( "threadError( PyQt_PyObject )" ), message )
    df = {}
    types = {}
    order = []
    for (id, field) in fields.iteritems():
      # initial read in has correct ordering...
      name = str(field.name())
      df[ name ] = []
      types[ name ] = int( field.type() )
      order.append(name)
    fid = {"fid": []}
    Coords = []
    if self.mlayer.selectedFeatureCount() > 0:
      features = self.mlayer.selectedFeatures()
      for feat in features:
        for (key, value) in df.iteritems():
          df[key].append(self.convertAttribute(feat.attributeMap()[provider.fieldNameIndex(key)]))
        fid["fid"].append(feat.id())
        if not self.data_only:
          if not self.getNextGeometry( Coords, feat):
            message = QString( "Unable to convert layer geometry" )
            self.emit( SIGNAL( "threadError( PyQt_PyObject )" ), message )
    else:
      feat = QgsFeature()
      while provider.nextFeature(feat):
        for key in df.keys():
          attrib = self.convertAttribute(feat.attributeMap()[provider.fieldNameIndex(key)])
          df[key].append(attrib)
        fid["fid"].append(feat.id())
        if not self.data_only:
          if not self.getNextGeometry( Coords, feat):
            message = QString( "Unable to convert layer geometry" )
            self.emit( SIGNAL( "threadError( PyQt_PyObject )" ), message )
    data_frame = rlike.container.ArgsDict()
    for key in order:
      if types[key] == 10:
        data_frame[ key ] = self.as_character_( robjects.StrVector( df[ key ] ) )
      else:
        data_frame[ key ] = robjects.FloatVector( df[ key ] )
    #fid[ "fid" ] = robjects.IntVector( fid["fid"] )
    #data_frame = robjects.r(''' function( d ) data.frame( d ) ''')
    #data = data_frame( df )
    data_frame = self.data_frame_.rcall( data_frame.items() )
    #data = data_frame( df )
    #data['row.names'] = fid[ "fid" ]
    if not self.data_only:
      message = QString( "QGIS Vector Layer\n" )
      spds = self.createSpatialDataset( feat.geometry().type(), Coords, data_frame, projString)
    else:
      message = QString( "QGIS Attribute Table\n" )
      spds = data_frame
    length = len( fid[ "fid" ] )
    width = len( order )
    name = self.mlayer.name()
    source = self.mlayer.publicSource()
    name = QFileInfo( name ).baseName()
    
    message.append( QString( "Name: " + str( name ) + "\nSource: " + str( source ) ) )
    message.append( QString( "\nwith " + str( length ) + " rows and " + str( width ) + " columns" ) )
    message.append( "\n" + extra )
    self.emit( SIGNAL( "threadSuccess( PyQt_PyObject, PyQt_PyObject, PyQt_PyObject )" ), 
    spds, name, message )

  # Function to retrieve QgsGeometry (polygon) coordinates
  # and convert to a format that can be used by R
  # Return: Item of class Polygons (R class)
  def getPolygonCoords( self, geom, fid):
    if geom.isMultipart():
      keeps = []
      polygon = geom.asMultiPolygon() #multi_geom is a multipolygon
      for lines in polygon:
        for line in lines:
          keeps.append(self.Polygon_(self.matrix_(self.unlist_([self.convertToXY(point) for point in line]), nrow=len([self.convertToXY(point) for point in line]), byrow=True)))
      return self.Polygons_(keeps, fid)
    else:
      lines = geom.asPolygon() #multi_geom is a polygon
      Polygon = [self.Polygon_(self.matrix_(self.unlist_([self.convertToXY(point) for point in line]), nrow=len([self.convertToXY(point) for point in line]), byrow=True)) for line in lines]
      return self.Polygons_(Polygon, fid)

  # Function to retrieve QgsGeometry (line) coordinates
  # and convert to a format that can be used by R
  # Return: Item of class Lines (R class)
  def getLineCoords( self, geom, fid):
    if geom.isMultipart():
      keeps = []
      lines = geom.asMultiPolyline() #multi_geom is a multipolyline
      for line in lines:
        for line in lines:
          keeps.append(self.Line_(self.matrix_(self.unlist_([self.convertToXY(point) for point in line]), nrow=len([self.convertToXY(point) for point in line]), byrow=True)))
      return self.Lines_( keeps, str( fid ) )
    else:
      line = geom.asPolyline() #multi_geom is a line
      Line = self.Line_(self.matrix_(self.unlist_([self.convertToXY(point) for point in line]), nrow = len([self.convertToXY(point) for point in line]), byrow=True))
      return self.Lines_( Line, str( fid ) )

  # Function to retrieve QgsGeometry (point) coordinates
  # and convert to a format that can be used by R
  # Return: Item of class Matrix (R class)
  def getPointCoords( self, geom, fid ):
    if geom.isMultipart():
      points = geom.asMultiPoint() #multi_geom is a multipoint
      return [self.convertToXY(point) for point in points]
    else:
      point = geom.asPoint() #multi_geom is a point
      return self.convertToXY(point)

  # Helper function to get coordinates of input geometry
  # Does not require knowledge of input geometry type
  # Return: Appends R type geometry to input list
  def getNextGeometry( self, Coords, feat):
    geom = feat.geometry()
    if geom.type() == 0:
      Coords.append(self.getPointCoords(geom, feat.id()))
      return True
    elif geom.type() == 1:
      Coords.append(self.getLineCoords( geom, feat.id()))
      return True
    elif geom.type() == 2:
      Coords.append(self.getPolygonCoords( geom, feat.id()))
      return True
    else:
      return False

  # Helper function to create Spatial*DataFrame from
  # input spatial and attribute information
  # Return: Object of class Spatial*DataFrame (R class)
  def createSpatialDataset( self, vectType, Coords, data, projString):
    if vectType == 0:
      # For points, coordinates must be input as a matrix, hense the extra bits below...
      # Not sure if this will work for multipoint features?
      spatialData = self.SpatialPoints_(self.matrix_(self.unlist_(Coords), nrow = len(Coords), byrow = True), proj4string = self.CRS_( projString ) )
      try:
        return self.SpatialPointsDataFrame_( spatialData, data )#, match_ID = True )
        #kwargs = {'match.ID':"FALSE"}
        #return SpatialPointsDataFrame( spatialData, data, **kwargs )
      except Exception, e:
        return str( e )
    elif vectType == 1:
      try:
        spatialData = self.SpatialLines_( Coords, proj4string = self.CRS_( projString ) )
        kwargs = {'match.ID':"FALSE"}
        return self.SpatialLinesDataFrame_( spatialData, data, **kwargs )
      except Exception, e:
        return str( e )
    elif vectType == 2:
      try:
        spatialData = self.SpatialPolygons_( Coords, proj4string = self.CRS_( projString ) )
        kwargs = {'match.ID':"FALSE"}
        return self.SpatialPolygonsDataFrame_( spatialData, data, **kwargs )
      except Exception, e:
        return str( e )
    else:
      return ""

  # Function to convert QgsPoint to x, y coordinate
  # Return: list
  def convertToXY(self, inPoint):
    return [inPoint.x(), inPoint.y()]

  # Function to convert attribute to string or double
  # for input into R object
  # Return: Double or String
  def convertAttribute( self, attribute ):
    Qtype = attribute.type()
    if Qtype == 10:
      return attribute.toString()
    else:
      return attribute.toDouble()[0]
      
      
class QRasterLayerConverter( QObject ):
  '''
  QRasterLayerConvert:
  This class is used to convert a QGIS
  raster layer to an R (sp) raster layer for use
  in the manageR R environment.
  '''
  def __init__( self, mlayer ):
    QObject.__init__( self )
    self.running = False
    self.mlayer = mlayer

  def stop( self ):
    '''
    Kill thread
    '''
    self.running = False

  def start( self ):
    '''
    Main working function
    Emits threadSuccess when completed successfully
    Emits threadError when errors occur
    '''
    self.running = True
    dsn = unicode( self.mlayer.source() )
    layer = unicode( self.mlayer.name() )
    dsn.replace("\\", "/")
    rcode = "readGDAL( fname = '" + dsn + "')"
    try:
      rlayer = robjects.r( rcode )
    except robjects.rinterface.RRuntimeError, rre:
      message = QString( "Unable to convert raster layer\n" )
      message.append( str( rre ) )
      self.emit( SIGNAL( "threadError( PyQt_PyObject )" ), message )
      return
    summary_ = robjects.conversion.ri2py(rinterface.globalEnv.get('summary',wantFun=True))
    slot_ = robjects.conversion.ri2py(rinterface.globalEnv.get('@',wantFun=True))
    message = QString( "QGIS Raster Layer\n" )
    message.append( "Name: " + str( self.mlayer.name() ) + "\nSource: " + str( self.mlayer.source() ) + "\n" )
    message.append( str( summary_( slot_( rlayer, 'grid' ) ) ) )
    self.emit( SIGNAL( "threadSuccess( PyQt_PyObject, PyQt_PyObject, PyQt_PyObject )" ), rlayer, layer, message )
    
