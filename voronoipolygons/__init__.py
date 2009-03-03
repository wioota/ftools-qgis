def name():
  return "Voronoi/Thiessen tesselation"

def description():
  return "Generate a voronoi tessellation from a point layer"
  
def qgisMinimumVersion():
	return "1.0.0"
	
def authorName():
	return "Carson J. Q. Farmer"

def version():
  return "Version 1.0"

def classFactory(iface):
  from voronoiPolygons import voronoiPolygonsPlugin
  return voronoiPolygonsPlugin(iface)
