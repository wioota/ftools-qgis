# -*- coding: utf-8 -*-

# regular imports
import time

# rpy2 imports
import rpy2.robjects as robjects
import rpy2.rlike as rlike

#PyQt and PyQGIS imports
from PyQt4.QtCore import (QString, QVariant, QFileInfo)
from qgis.core import    (QgsVectorLayer, QgsVectorDataProvider, QgsMapLayer,
                          QgsApplication, QgsRectangle, QgsGeometry)

# ---------------------------   VECTOR LAYERS   -------------------------------#
def spatialDataFrameObject(layer, keep=False):
    provider = layer.dataProvider()
    selection = layer.selectedFeatureCount()>0
    if keep:
        crs = provider.crs()
        if not crs.isValid():
            proj = 'NA'
        else:
            if not crs.geographicFlag():
                proj = unicode(crs.toProj4())
            else:
                # TODO: Find better way to handle geographic coordinate systems
                # As far as I can tell, R does not like geographic coodinate systems input
                # into it's proj4string argument...
                proj = 'NA'
    attrs = provider.attributeIndexes()
    layer.select(attrs, QgsRectangle())
    fields = [(field.name(), field.type()) for field in provider.fields().values()]
    if len(fields) < 1:
        raise Exception("Error: Attribute table must have at least one field")
    if selection:
        feats = layer.selectedFeatures()
    else:
        feats = features(layer)
    source = unicode(layer.publicSource())
    name = unicode(QFileInfo(layer.name()).baseName())
    make_names = robjects.r.get('make.names', mode='function')
    newname = make_names(name)[0]
    try:
        df = data(feats, fields)
        if not keep:
            try:
                robjects.r.assign(unicode(newname), df)
            except:
                raise Exception("Error: unable to assign data.frame object to environment")
            return True
        geoms = geometries(feats)
        type = layer.geometryType()
        sp = spatial(geoms, type, str(crs.toProj4()))
        result = spatialDataFrame(sp, df, type)
        try:
            robjects.r.assign(unicode(newname), result)
        except:
            raise Exception("Error: unable to assign spatial object to environment")
        length, width = list(robjects.r.dim(result))
        robjects.r['print']("Name: %s\nSource: %s\n" % (unicode(newname), unicode(source)))
        robjects.r['print']("with %s rows and %s columns\n" % (unicode(length), unicode(width)))
        if not newname == name:
            robjects.r['print']("**Note: layer name syntax changed")
    except Exception, e:
        raise Exception("Error: %s" % unicode(e))
    return True

def features(layer):
    try:
        return [feature for feature in layer]
    except Exception, e:
        raise Exception("error encountered when extracting features: %s" % unicode(e))

def data(feats, fields):
    try:
        # fields:   fields = [(field.name(), field.type()) for field in provider.fields().values()]
        # features: layer.select(provider.attributeIndexes(), QgsRectangle())
        #           features = [feature for feature in layer]
        attrs = [feat.attributeMap().values() for feat in feats]
        attrst = map(lambda *row: list(row), *attrs)
        df = [
          (
            (str(fields[i][0]), robjects.FloatVector(map(lambda x: x.toDouble()[0], row)))
            if fields[i][1] == 2 else
            (
              (str(fields[i][0]), robjects.IntVector(map(lambda x: x.toInt()[0], row)))
              if fields[i][1] == 6 else
              (
                (str(fields[i][0]), robjects.StrVector(map(lambda x: x.toString(), row)))
              )
            )
          )
          for i, row in enumerate(attrst)
        ]
        df = rlike.container.OrdDict(df)
        return robjects.DataFrame(df)
    except Exception, e:
        raise Exception("error encountered when extracting data.frame: %s" % unicode(e))

def geometries(feats):
    # features: layer.select(provider.attributeIndexes(), QgsRectangle())
    #           features = [feature for feature in layer]
    try:
        return [geometry(feat) for feat in feats]
    except Exception, e:
        raise Exception("error encountered when extracting geometries: %s" % unicode(e))

def polygons(polys, fid):
    try:
        Polygon = robjects.r.get('Polygon', mode='function')
        Polygons = robjects.r.get('Polygons', mode='function')
        result = Polygons([Polygon([points(line) for line in poly]) for poly in polys], fid)
        return result
    except Exception, e:
        raise Exception("unable to extract polygon geomety (%s)" % unicode(e))

def points(line):
    try:
        numeric = robjects.FloatVector(sum([[point.x(), point.y()] for point in line], []))
        result = robjects.r.matrix(numeric, ncol=2, byrow=True)
        return result
    except Exception, e:
        raise Exception("unable to extract point geomety (%s)" % unicode(e))

def lines(lins, fid):
    try:
        Line = robjects.r.get('Line', mode='function')
        Lines = robjects.r.get('Lines', mode='function')
        result = Lines([Line(points(line)) for line in lins], fid)
        return result
    except Exception, e:
        raise Exception("unable to extract polyline geomety (%s)" % unicode(e))

def geometry(feature):
    try:
        geom = QgsGeometry(feature.geometry())
        fid = feature.id()
        if not geom.convertToMultiType():
            return None
        if geom.type() == 0:
            return points(geom.asMultiPoint(), fid)
        elif geom.type() == 1:
            return lines(geom.asMultiPolyline(), fid)
        elif geom.type() == 2:
            return polygons(geom.asMultiPolygon(), fid)
        else:
            return None
    except Exception, e:
        raise Exception("unable to extract feature geometry: %s" % unicode(e))

def spatial(geometries, type, proj="NULL"):
    try:
        SpatialPolygons = robjects.r.get('SpatialPolygons', mode='function')
        SpatialLines = robjects.r.get('SpatialLines', mode='function')
        SpatialPoints = robjects.r.get('SpatialPoints', mode='function')
        CRS = robjects.r.get('CRS', mode='function')
        if type == 0:
            return SpatialPoints(geometries, proj4string = CRS(proj))
        elif type == 1:
            return SpatialLines(geometries, proj4string = CRS(proj))
        elif type == 2:
            return SpatialPolygons(geometries, proj4string = CRS(proj))
        else:
            return None
    except Exception, e:
        raise Exception("unable to create spatial object: %s" % unicode(e))

def spatialDataFrame(spatial, data, type):
    try:
        SpatialPolygonsDataFrame = robjects.r.get('SpatialPolygonsDataFrame', mode='function')
        SpatialLinesDataFrame = robjects.r.get('SpatialLinesDataFrame', mode='function')
        SpatialPointsDataFrame = robjects.r.get('SpatialPointsDataFrame', mode='function')
        kwargs = {'match.ID':"FALSE"}
        if type == 0:
            return SpatialPointsDataFrame(spatial, data, **kwargs)
        elif type == 1:
            return SpatialLinesDataFrame(spatial, data, **kwargs)
        elif type == 2:
            return SpatialPolygonsDataFrame(spatial, data, **kwargs)
        else:
            return None
    except Exception, e:
        raise Exception("unable to create spatial dataset: %s" % unicode(e))

#dsn = self.mlayer.source()
#name = self.mlayer.name()
#encode = provider.encoding()
#readOGR_ = robjects.r.get('readOGR', mode='function')
#try:
    ##print unicode(dsn,encoding=str(encode)), unicode(name,encoding=str(encode)), str(encode)
    #spds = readOGR_(dsn=unicode(dsn,encoding=str(encode)),layer=unicode(name,encoding=str(encode)),
    #input_field_name_encoding=str(encode))
#except Exception, err:
    #spds = None
    #name = "Error"
    #print str(err)
#if self.data_only:
    #spds = robjects.r["@"](spds,"data")

# ---------------------------   RASTER LAYERS   -------------------------------#

def rasterDataFrameObject(layer, package='raster'):
    dsn = unicode(layer.publicSource())
    dsn.replace("\\", "/")
    name = unicode(layer.name())
    make_names = robjects.r.get('make.names', mode='function')
    newname = make_names(name)[0]
    if package == "raster":
        rcode = "raster('%s')" % dsn
    else:
        rcode = "readGDAL(fname = '%s')" % dsn
    result = robjects.r(rcode)
    try:
        robjects.r.assign(unicode(newname), result)
    except:
        raise Exception("Error: unable to assign raster object to environment")
    summary = robjects.r.get('summary', mode='function')
    slot = robjects.r.get('@', mode='function')
    robjects.r['print']("QGIS Raster Layer\n")
    robjects.r['print']("Name: %s\n" % unicode(newname))
    robjects.r['print']("Source: %s\n" % unicode(source))
    if package == 'raster':
        robjects.r['print']("Used package 'raster'\n")
    else:
        robjects.r['print'](unicode(summary(slot(result, 'grid'))))
        robjects.r['print']("Used package 'rgdal'\n")
    if not newname == name:
        robjects.r['print']("**Note: layer name syntax changed")
    return True

# ---------------------------   RVECTOR LAYERS   -------------------------------#

    def __init__(name):
        QObject.__init__(self)
        self.r_layer = r_layer
        self.layer_name = layer_name
        # define R functions as python variables
        self.slot_ = robjects.r.get('@', mode='function')
        self.get_row_ = robjects.r(''' function(d, i) d[i] ''')
        self.get_full_row_ = robjects.r(''' function(d, i) data.frame(d[i,]) ''')
        self.get_point_row_ = robjects.r(''' function(d, i) d[i,] ''')
        self.class_ = robjects.r.get('class', mode='function')
        self.names_ = robjects.r.get('names', mode='function')
        self.dim_ = robjects.r.get('dim', mode='function')
        self.as_character_ = robjects.r.get('as.character', mode='function')

        spatial = robjects.r.get(name)
        vtype = vectorType(spatial)
        layer = QgsVectorLayer(vtype, unicode(name), "memory")
        crs = QgsCoordinateReferenceSystem()
        proj = spatial.do_slot('proj4string').do_slot('projargs')[0]
        if crs.createFromProj4(proj):
            layer.setCrs(crs)
        else:
            robjects.r['print']("Error: unable to parse proj4string: using QGIS default\n")
        provider = layer.dataProvider()
        fields = spFields(spatial)
        provider.addAttributes(fields)

        rowCount = self.getRowCount()
        feat = QgsFeature()
        for row in range(1, rowCount + 1):
            if vtype == "Point": coords = self.getPointCoords(row)
            elif vtype == "Polygon": coords = self.getPolygonCoords(row)
            else: coords = self.getLineCoords(row)
            attrs = self.getRowAttributes(provider, row)
            feat.setGeometry(coords)
            feat.setAttributeMap(attrs)
            provider.addFeatures([feat])
        vlayer.updateExtents()
        return vlayer

    def spFields(spatial):
        typeof = robjects.r.get('class', mode='function')
        sapply = robjects.r.get('sapply', mode='function')
        try:
            types = sapply(spatial.do_slot('data'), typeof)
        except:
            raise Exception("R vector layer contains unsupported field type(s)")
        names = list(spatial.do_slot('data').names)
        fields = [QgsField(name, QVariant.Double) if types[i] == "numeric"
                  else (name, QVariant.String) for i, name in enumerate(names)]
        return fields

    def spType(spatial):
        class_ = robjects.r.get('class', mode='function')
        check = class_(spatial)[0]
        if check == "SpatialPointsDataFrame": return "Point"
        elif check == "SpatialPolygonsDataFrame": return "Polygon"
        elif check == "SpatialLinesDataFrame": return "LineString"
        else:
            raise Exception("R vector layer is not of type Spatial*DataFrame")

    def spGeometries(spatial):
        def split(L):
            n = len(L)/2
            return [L[:n], L[n:]]
        type = spType(spatial)
        if type == "Polygon":
            coords =
                [
                  [map(lambda p: QgsPoint(*p), zip(*split(list(po.do_slot('coords')))))
                  for po in poly.do_slot('Polygons')]
                  for poly in list(polys.do_slot('polygons'))
                ]
        elif type == "LineString":
            coords =
                [
                  [map(lambda p: QgsPoint(*p), zip(*split(list(ln.do_slot('coords')))))
                  for ln in line.do_slot('Lines')]
                  for line in list(spatial.do_slot('lines'))
                ]
        elif type == "Point":
            coords =
                [
                  map(lambda p: QgsPoint(*p), zip(*split(list(spatial.do_slot('coords')))))
                ]
        else:
            raise Exception("unable to convert geometries")
        return coords

    def spData(spatial):
        

    def getRowAttributes(self, provider, row):
        '''
        Get attributes associated with a single R feature
        Return: python dictionary containing key/value pairs,
        where key = field index and value = attribute
        '''
        temp = self.get_full_row_(self.slot_(self.r_layer, "data"), row)
        names = self.names_(self.r_layer)
        out = {}
        if not provider.fieldCount() > 1:
            out = {0 : QVariant(temp[0])}
        else:
        #    return dict(zip([provider.fieldNameIndex(str(name)) for name in names],
        #    [QVariant(item[0]) for item in temp]))
            count = 0
            for field in temp:
                if self.class_(field)[0] == "factor":
                    out[provider.fieldNameIndex(unicode(names[count]))] = QVariant(self.as_character_(field)[0])
                else:
                    out[provider.fieldNameIndex(unicode(names[count]))] = QVariant(field[0])
                count += 1
        return out

    

    def getPointCoords(self, row):
        '''
        Get point coordinates of an R point feature
        Return: QgsGeometry from a point
        '''
        coords = self.get_point_row_(self.slot_(self.r_layer, 'coords'), row)
        return QgsGeometry.fromPoint(QgsPoint(coords[0], coords[1]))

    def getPolygonCoords(self, row):
        '''
        Get polygon coordinates of an R polygon feature
        Return: QgsGeometry from a polygon and multipolygon
        '''
        Polygons = self.get_row_(self.slot_(self.r_layer, "polygons"), row)
        polygons_list = []
        for Polygon in Polygons:
            polygon_list = []
            polygons = self.slot_(Polygon, "Polygons")
            for polygon in polygons:
                line_list = []
                points_list = self.slot_(polygon, "coords")
                y_value = len(points_list)  / 2
                for j in range(0, y_value):
                    line_list.append(self.convertToQgsPoints(
                    (points_list[j], points_list[j + y_value])))
                polygon_list.append(line_list)
            polygons_list.append(polygon_list)
        return QgsGeometry.fromMultiPolygon(polygons_list)

    def getLineCoords(self, row):
        '''
        Get line coordinates of an R line feature
        Return: QgsGeometry from a line or multiline
        '''
        Lines = self.get_row_(self.slot_(self.r_layer, 'lines'), row)
        lines_list = []
        for Line in Lines:
            lines = self.slot_(Line, "Lines")
            for line in lines:
                line_list = []
                points_list = self.slot_(line, "coords")
                y_value = len(points_list)  / 2
                for j in range(0, y_value):
                    line_list.append(self.convertToQgsPoints((points_list[j], points_list[j + y_value])))
            lines_list.append(line_list)
        return QgsGeometry.fromMultiPolyline(lines_list)

    def convertToQgsPoints(self, in_list):
        '''
        Function to convert x, y coordinates list to QgsPoint
        Return: QgsPoint
        '''
        return QgsPoint(in_list[0], in_list[1])



def main():
    QgsApplication.setPrefixPath('/usr/local', True)
    QgsApplication.initQgis()
    layer = QgsVectorLayer("/home/cfarmer/temp/test_buffer_1.shp", "test_buffer_1", "ogr")
    provider = layer.dataProvider()
    if not robjects.r.require('sp')[0]:
        raise Exception("Error: missing 'sp' package: classes and methods for spatial data")
    t1 = time.time()
    output = spatialDataFrameObject(layer, True)
    t2 = time.time()
    print t2-t1

if __name__ == '__main__':
    main()
