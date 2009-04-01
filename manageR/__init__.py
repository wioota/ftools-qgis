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

import ConfigParser
import os.path
p = ConfigParser.ConfigParser()
here = os.path.join(os.path.dirname(__file__),"config.ini")
p.read(here)

def name():
  return p.get('general','name')

def description():
  return p.get('general','description')

def version():
  return p.get('general','version')

def qgisMinimumVersion():
  return p.get("general","qgisMinimumVersion")

def classFactory( iface ):
  from manageR import manageRPlugin
  return manageRPlugin( iface, version() )
