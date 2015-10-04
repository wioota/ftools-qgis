ftools-qgis provides a set of advanced spatial analysis tools designed to extend the functionality of Quantum GIS, a free, open-source GIS.

Currently, ftools-qgis features:

1) manageR - Interface to R statistical analysis

Provides advanced statistical functionality within QGIS by loosely coupling QGIS with the R statistical programming language. Allows upload of QGIS layers directly into R, and the ability to perform R operations on the data directly from within QGIS. It interfaces with R using RPy2, which is a Python interface to the R Programming Language

2) voronoipolygons - Voronoi/Thiessen tessellation

Given a set of points in the plane, there exists an associated set of regions surrounding these points, such that all locations within any given region are closer to one of the points than to any other point. These regions are often referred to as proximity polygons, Voronoi polygons or Thiessen regions.