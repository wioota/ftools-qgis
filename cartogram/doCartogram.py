#-----------------------------------------------------------
# 
# Cartogram Creator
#
# A QGIS plugin for creating cartograms based on polygon
# shapefile. Uses algorithm proposed in:
#     Dougenik, J. A, N. R. Chrisman, and D. R. Niemeyer. 1985.
#     "An algorithm to construct continuous cartograms."
#     Professional Geographer 37:75-81
#
# This plugin uses python code adapted from Eric Wolfs pyCartogram.py
# See about dialog for more information.
#
# EMAIL: carson.farmer (at) gmail.com
# WEB  : http://www.ftools.ca/
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
import os, sys, string, math
from frmCartogram import Ui_Dialog

class Dialog(QDialog, Ui_Dialog):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        # Set up the user interface from Designer.
        self.setupUi(self)
        QObject.connect(self.toolOut, SIGNAL("clicked()"), self.outFile)
        QObject.connect(self.inShape, SIGNAL("currentIndexChanged(QString)"), self.update)
        # populate layer list
        self.progressBar.setValue(0)       
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for name, layer in layermap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.geometryType() == QGis.Polygon:
                    self.inShape.addItem( unicode( layer.name() ) )
      
    def update(self, inputLayer):
        self.inFields.clear()
        changedLayer = self.getVectorLayerByName(inputLayer)
        changedFields = self.getFieldList(changedLayer)
        for i in changedFields:
            if changedFields[i].type() == QVariant.Int or \
            changedFields[i].type() == QVariant.Double:
                self.inFields.addItem(unicode(changedFields[i].name()))
    
    def accept(self):
        if self.inShape.currentText() == "":
            QMessageBox.information(self, "Cartogram Creator", "No input shapefile specified")
        elif self.outShape.text() == "":
            QMessageBox.information(self, "Cartogram Creator", "Please specify output shapefile")
        else:
            keep = bool(self.chkKeep.isChecked())
            iterations = int(self.spnIterations.value())
            inField = self.inFields.currentText()
            inLayer = self.getVectorLayerByName(unicode(self.inShape.currentText()))
            self.progressBar.setValue(5)
            outPath = self.outShape.text()
            self.progressBar.setValue(10)
            if outPath.contains("\\"):
                outPath.replace("\\", "/")
            self.progressBar.setValue(15)
            tempList = self.cartogram(inLayer, outPath, iterations, unicode(inField), keep, self.progressBar)
            if not keep:
                for temp in tempList:
                    myInfo = QFileInfo(unicode(temp))
                    myBase = temp.remove(".shp")
                    if (myInfo.exists()):
                        QFile.remove(myBase + ".shp")
                    myInfo.setFile(myBase + ".shx")
                    if (myInfo.exists()):
                        QFile.remove(myBase + ".shx")
                    myInfo.setFile(myBase + ".dbf")
                    if (myInfo.exists()):
                        QFile.remove(myBase + ".dbf")
                    myInfo.setFile(myBase + ".prj")
                    if (myInfo.exists()):
                        QFile.remove(myBase + ".prj")
            outName = outPath.right((outPath.length() - outPath.lastIndexOf("/")) - 1)
            outName = outName.left(outName.length())             
            self.progressBar.setValue(100)
            self.outShape.clear()
            addToTOC = QMessageBox.question(self, "Cartogram Creator", 
            "Created output polygon shapefile:\n" + unicode(outPath)
            + "\n\nWould you like to add the new layer to the TOC?", 
            QMessageBox.Yes, QMessageBox.No, QMessageBox.NoButton)
            if addToTOC == QMessageBox.Yes:
                vlayer = QgsVectorLayer(outPath + ".shp", unicode(outName), "ogr")
                QgsMapLayerRegistry.instance().addMapLayer(vlayer)
        self.progressBar.setValue(0)

    def outFile(self):
        self.outShape.clear()
        fileDialog = QFileDialog()
        fileDialog.setConfirmOverwrite(False)
        outName = fileDialog.getSaveFileName(self,
        "Cartogram Creator",".", "Shapefiles (*.shp)")
        fileCheck = QFile(outName)
        if fileCheck.exists():
            QMessageBox.warning(self, "Cartogram Creator", "Cannot overwrite existing shapefile...")
        else:
            filePath = QFileInfo(outName).absoluteFilePath()
            if filePath.right(4) != ".shp": filePath = filePath + ".shp"
            if not outName.isEmpty():
                self.outShape.clear()
                self.outShape.insert(filePath)

    def cartogram(self, vlayer, outPath, iterations, inField, keep, progressBar):
        provider = vlayer.dataProvider()
        totalFeats = provider.featureCount()
        aLocal = []
        dMean = 0
        dForceReductionFactor = 0
        dTotalArea = 0
        dTotalValue = 0
        tempList = []
        for (i, attr) in provider.fields().iteritems():
            if (inField == attr.name()): index = i #get 'area' field index
        basePath = outPath
        basePath.remove(".shp")
        for i in range(1, iterations + 1):
            if (i > 1):
                vlayer = QgsVectorLayer(tempPath, "", "ogr")
                provider = vlayer.dataProvider()
            if (i < iterations):
                tempPath = basePath + "_" + unicode(i) + ".shp"
                tempList.append(tempPath)
            else:
                tempPath = outPath + ".shp"
            progressBar.setValue(20)
            (dMean, aLocal, dForceReductionFactor, dTotalArea, dTotalValue) = self.getInfo(provider, index)
            progressBar.setValue(40)
            feature = QgsFeature()
            allAttrs = provider.attributeIndexes()
            provider.select(allAttrs)
            fieldList = self.getFieldList(vlayer)
            sRs = provider.crs()
            progressBar.setValue(45)
            writer = QgsVectorFileWriter(unicode(tempPath), "UTF-8", fieldList, QGis.WKBPolygon, sRs)
            outfeat = QgsFeature()
            geometry2 = QgsGeometry()
            progressBar.setValue(50)
            ink = 100.00 / provider.featureCount()
            start = 1.00
            while provider.nextFeature(feature):
                geometry = feature.geometry()
                geometry2 = self.TransformGeometry(aLocal, dForceReductionFactor, geometry, totalFeats)
                outfeat.setGeometry(geometry2)
                atMap = feature.attributeMap()
                for h in atMap.keys():
                    outfeat.addAttribute(h, atMap[h])
                writer.addFeature(outfeat)
                start = start + ink
                progressBar.setValue(start)
            del writer
            del aLocal
        return tempList
    
# Gets vector layer by layername in canvas     
    def getVectorLayerByName( self, myName ):
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for name, layer in layermap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer and layer.name() == myName:
                if layer.isValid():
                    return layer
                else:
                    return None
        
# Return the field list of a vector layer
    def getFieldList( self, vlayer ):
        vprovider = vlayer.dataProvider()
        feat = QgsFeature()
        allAttrs = vprovider.attributeIndexes()
        vprovider.select( allAttrs )
        myFields = vprovider.fields()
        return myFields    

# Gets the information required for calcualting size reduction factor
    def getInfo(self, provider, index):
        allAttrs = provider.attributeIndexes()
        provider.select(allAttrs)
        featCount = provider.featureCount()
        sRs = provider.crs()
        feat = QgsFeature()
        aLocal = []
        cx = 0
        cy = 0
        dAreaTotal = 0.00
        dTotalValue = 0.00
        while provider.nextFeature(feat):
            lfeat = Holder()
            geom = QgsGeometry(feat.geometry())
            dDistArea = QgsDistanceArea()
            area = dDistArea.measure(geom)
            lfeat.dArea = area # save area of this feature
            lfeat.lFID = feat.id() # save id for this feature
            dAreaTotal = dAreaTotal + area # save total area of all polygons
            atMap = feat.attributeMap()
            lfeat.dValue = atMap[index].toInt()[0] # save 'area' value for this feature
            #QMessageBox.information(self, "Generate Centroids", unicode(lfeat.dValue))
            dTotalValue = dTotalValue + lfeat.dValue
            (cx, cy) = self.centroid(feat, area) # get centroid info
            lfeat.ptCenter_x = cx # save centroid x for this feature
            lfeat.ptCenter_y = cy # save centroid y for this feature
            aLocal.append(lfeat)
        dFraction = dAreaTotal / dTotalValue    #ratio of actual area to total 'area' value...
        dSizeErrorTotal = 0    
        dSizeError = 0
        for i in range(featCount):
            lf = aLocal[i] # info for current feature
            dPolygonValue = lf.dValue
            dPolygonArea = lf.dArea
            if (dPolygonArea < 0): # area should never be less than zero 
                dPolygonArea = 0
            dDesired = dPolygonValue * dFraction # this is our 'desired' area...
            dRadius = math.sqrt(dPolygonArea / math.pi) # calculate radius, a zero area is zero radius
            lf.dRadius = dRadius
            lf.dMass = math.sqrt(dDesired / math.pi) - dRadius #calculate area mass, don't think this should be negative
            #both radius and mass are being added to the feature list for later on...
            dSizeError = max(dPolygonArea, dDesired) / min(dPolygonArea, dDesired) #calculate size error...
            dSizeErrorTotal = dSizeErrorTotal + dSizeError #this is the total size error for all polygons
        dMean = dSizeErrorTotal / featCount # average error
        dForceReductionFactor = 1 / (dMean + 1) # need to read up more on why this is done
        return (dMean, aLocal, dForceReductionFactor, dAreaTotal, dTotalValue)

# Compute polygon centroids
    def centroid(self, feat, area):
        geom = QgsGeometry(feat.geometry())
        area = 0.00
        bounding = geom.boundingBox()
        xmin = bounding.xMinimum()
        ymin = bounding.yMinimum() 
        if geom.type() == 2:
            cx = 0
            cy = 0
            factor = 0
            if geom.isMultipart():
                polygons = geom.asMultiPolygon()
                for polygon in polygons:
                    for line in polygon: 
                        for i in range(0,len(line)-1):
                          j = (i + 1) % len(line)
                          factor=((line[i].x()-xmin)*(line[j].y()-ymin)-(line[j].x()-xmin)*(line[i].y()-ymin))
                          cx+=((line[i].x()-xmin)+(line[j].x()-xmin))*factor
                          cy+=((line[i].y()-ymin)+(line[j].y()-ymin))*factor
                          area+=factor
            else:
                polygon = geom.asPolygon()
                for line in polygon:
                    for i in range(0,len(line)-1):
                        j = (i + 1) % len(line)
                        factor=((line[i].x()-xmin)*(line[j].y()-ymin)-(line[j].x()-xmin)*(line[i].y()-ymin))
                        cx+=((line[i].x()-xmin)+(line[j].x()-xmin))*factor
                        cy+=((line[i].y()-ymin)+(line[j].y()-ymin))*factor
                        area+=factor
            cx/=area*3.00
            cy/=area*3.00
        return (cx, cy)

# Actually changes the x,y of each point
    def TransformGeometry(self, aLocal, dForceReductionFactor, geom, featCount):
        #QMessageBox.information(self, "Generate Centroids", "is it getting here?")
        multi_geom = QgsGeometry()
        temp_lines = []
        temp_polys = []
        temp_geom = []
        if geom.isMultipart():
            multi_geom = geom.asMultiPolygon() #multi_geom is a multipolygon
            for g in multi_geom: #i is a polygon
                for k in g: #k is a line
                    for j in k: #j is a point
                        x = x0 = j.x()
                        y = y0 = j.y()
                        # Compute the influence of all shapes on this point
                        for i in range(featCount):
                            lf = aLocal[i]
                            cx = lf.ptCenter_x
                            cy = lf.ptCenter_y
                            # Pythagorean distance
                            distance = math.sqrt((x0 - cx) ** 2 + (y0 - cy) ** 2)
                            if (distance > lf.dRadius):
                                # Calculate the force on verteces far away from the centroid of this feature
                                Fij = lf.dMass * lf.dRadius / distance
                            else:
                                # Calculate the force on verteces far away from the centroid of this feature
                                xF = distance / lf.dRadius
                                Fij = lf.dMass * (xF ** 2) * (4 - (3 * xF))
                            Fij = Fij * dForceReductionFactor / distance
                            x = (x0 - cx) * Fij + x
                            y = (y0 - cy) * Fij + y
                        temp_lines.append(QgsPoint(x, y))
                    temp_polys.append(temp_lines)
                    temp_lines = []
                temp_geom.append(temp_polys)
                temp_polys = []
            newGeom = QgsGeometry.fromMultiPolygon(temp_geom)
            temp_geom = []
        else:
            multi_geom = geom.asPolygon()
            for k in multi_geom: # k is a line
                for j in k: # j is a point
                    x = x0 = j.x()
                    y = y0 = j.y()
                    # Compute the influence of all shapes on this point
                    for i in range(featCount):
                        lf = aLocal[i]
                        cx = lf.ptCenter_x
                        cy = lf.ptCenter_y
                        # Pythagorean distance                
                        distance = math.sqrt((x0 - cx) ** 2 + (y0 - cy) ** 2)
                        if (distance > lf.dRadius):
                            # Calculate the force on verteces far away from the centroid of this feature
                            Fij = lf.dMass * lf.dRadius / distance
                        else:
                            # Calculate the force on verteces far away from the centroid of this feature
                            xF = distance / lf.dRadius
                            Fij = lf.dMass * (xF ** 2) * (4 - (3 * xF))
                        Fij = Fij * dForceReductionFactor / distance
                        #print "    " + unicode(i) + "  " + unicode(distance) + "  " + unicode(Fij)
                        x = (x0 - cx) * Fij + x
                        y = (y0 - cy) * Fij + y
                    temp_lines.append(QgsPoint(x, y))
                temp_polys.append(temp_lines)
                temp_lines = []
            newGeom = QgsGeometry.fromPolygon(temp_polys)        
            temp_polys = []
                # End: Loop through all the points
        return newGeom            
            
# Feature stores various pre-calculated values about each feature
class Holder(object):
    count = 0
    def __init__(self):
        Holder.count = Holder.count + 1
        self.lFID = -1 #
        self.lGElemPos = -1
        self.ptCenter_x = -1 #
        self.ptCenter_y = -1 #
        self.dNew_area = -1
        self.dFactor = -1
        self.sName = ""
        self.dValue = -1 #
        self.dArea = -1 #
        self.dMass = -1
        self.dRadius = -1
        self.dVertices = -1
