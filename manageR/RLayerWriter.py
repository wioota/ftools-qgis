from PyQt4.QtCore import *
from qgis.core import *
import rpy2.robjects as robjects

class RVectorLayerWriter( QObject ):
  '''
  RVectorLayerWriter:
  This thread class is used to save an R 
  vector layer to file using the R package rgdal
  '''
  def __init__( self, layer_name, out_name, driver ):
    QObject.__init__( self )
    self.driver = driver
    self.out_name = out_name
    self.layer_name = layer_name
    
  def stop( self ):
    pass

  def start( self ):
    '''
    Main working function
    Emits threadSuccess when completed successfully
    Emits threadError when errors occur
    '''
    error = False
    file_path = QFileInfo( self.out_name ).absoluteFilePath()
    file_path.replace( "\\", "/" )
    file_name = QFileInfo( self.out_name ).baseName()
    driver_list = self.driver.split( "(" )
    self.driver = driver_list[ 0 ]
    self.driver.chop( 1 )
    extension = driver_list[ 1 ].right( 5 )
    extension.chop( 1 )
    if not file_path.endsWith( extension, Qt.CaseInsensitive ):
      file_path = file_path.append( extension )
    if not file_name.isEmpty():
      r_code = "writeOGR( obj = %s, dsn = '%s', layer = '%s', driver = '%s' )" %( unicode( self.layer_name ), unicode( file_path ), unicode( file_name ), unicode( self.driver ) )
      try:
        robjects.r( r_code )
        vlayer = QgsVectorLayer( unicode( file_path ), unicode( file_name ), "ogr" )
      except robjects.rinterface.RRuntimeError, rre:
        error = True
        message = unicode( rre )
    if error:
      self.emit( SIGNAL( "threadError( PyQt_PyObject )" ), message )
    else:
      self.emit( SIGNAL( "threadSuccess( PyQt_PyObject, PyQt_PyObject )" ), vlayer, True )


class RRasterLayerWriter( QObject ):
  '''
  RRasterLayerWriter:
  This thread class is used to save an R 
  raster layer to file using the R package rgdal
  '''
  def __init__( self, layer_name, out_name, driver ):
    QObject.__init__( self )
    self.driver = driver
    self.layer_name = layer_name
    self.out_name = out_name
    
  def stop( self ):
    pass

  def start( self ):
    '''
    Main working function
    Emits threadSuccess when completed successfully
    Emits threadError when errors occur
    '''
    error = False
    file_path = QFileInfo( self.out_name ).absoluteFilePath()
    file_path.replace( "\\", "/" )
    file_name = QFileInfo( self.out_name ).baseName()
    driver_list = self.driver.split( "(" )
    self.driver = driver_list[ 0 ]
    self.driver.chop( 1 )
    extension = driver_list[ 1 ].right( 5 )
    extension.chop( 1 )
    if self.driver == "GeoTIFF": self.driver = "GTiff"
    elif self.driver == "Erdas Imagine Images": self.driver = "HFA"
    elif self.driver == "Arc/Info ASCII Grid": self.driver = "AAIGrid"
    elif self.driver == "ENVI Header Labelled": self.driver = "ENVI"
    elif self.driver == "JPEG-2000 part 1": self.driver = "JPEG2000"
    elif self.driver == "Portable Network Graphics": self.driver = "PNG"
    elif self.driver == "USGS Optional ASCII DEM": self.driver = "USGSDEM"
    if not file_path.endsWith( extension, Qt.CaseInsensitive ) and self.driver != "ENVI":
      file_path = file_path.append( extension )
    if not file_path.isEmpty():
      if self.driver == "AAIGrid" or self.driver == "JPEG2000" or self.driver == "PNG" or self.driver == "USGSDEM":
        r_code = "saveDataset( dataset = copyDataset( create2GDAL( dataset = %s, type = 'Float32' ), driver = '%s'), filename = '%s')" %( unicode( self.layer_name ), unicode( self.driver ), unicode( file_path ) )
        robjects.r( r_code )
      else:
        r_code = "writeGDAL( dataset = %s, fname = '%s', drivername = '%s', type = 'Float32' )" %( unicode( self.layer_name ), unicode( file_path ), unicode( self.driver ) )
      try:
        robjects.r( r_code )
        rlayer = QgsRasterLayer( unicode( file_path ), unicode( file_name ) )
      except robjects.rinterface.RRuntimeError, rre:
        error = True
        message = unicode( rre )
    if error:
      self.emit( SIGNAL( "threadError( PyQt_PyObject )" ), message )
    else:
      self.emit( SIGNAL( "threadSuccess( PyQt_PyObject, PyQt_PyObject )" ), rlayer, True )
