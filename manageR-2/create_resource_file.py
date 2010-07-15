# -*- coding: utf-8 -*-
import glob, os
icons = glob.glob("icons/default/*.png")
f = open("resources.qrc", "w")
f.write("<RCC>\n")
f.write("    <qresource>\n")
for icon in icons:
    f.write('        <file alias="%s">%s</file>\n' % (str(icon.replace("icons/default/","")),str(icon)))
f.write("    </qresource>\n")
f.write("</RCC>\n")
f.close()
os.system("pyrcc4 resources.qrc > resources.py")
 
