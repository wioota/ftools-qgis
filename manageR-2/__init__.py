# -*- coding: utf-8 -*-
'''
This file is part of manageR

Copyright (C) 2009 Carson J. Q. Farmer

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public Licence as published by the Free Software
Foundation; either version 2 of the Licence, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public Licence for more 
details.

You should have received a copy of the GNU General Public Licence along with
this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
Street, Fifth Floor, Boston, MA  02110-1301, USA
'''


def name():
  return "manageR"

def description():
  return "Interface to the R statistical programming language"

def version():
  return "0.8"

def qgisMinimumVersion():
  return "1.0"
  
def author():
  return "Carson J. Q. Farmer <carson.farmer@gmail.com>"

def classFactory(iface):
  from plugin import Plugin
  return Plugin(iface, version())
