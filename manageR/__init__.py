#-----------------------------------------------------------
# 
# manageR
#
# A QGIS plugin for loosely coupling QGIS with the R statistical
# programming language. Allows uplaod of QGIS layers directly
# into R, and the ability to perform R operations on the data
# directly from within QGIS.
#
# Copyright (C) 2009 Carson J.Q. Farmer
#
# EMAIL: carson.farmer@gmail.com
# WEB  : http://www.ftools.ca/manageR.html
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

from manageR import manageRPlugin

def name():
  return "manageR"

def description():
  return "Interface to the R statistical analysis program"

def version():
  return "Version 0.6.2"
  
def qgisMinimumVersion():
  return "1.0"

def classFactory( iface ):
  return manageRPlugin( iface, version() )
