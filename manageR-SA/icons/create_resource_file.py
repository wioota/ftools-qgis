# -*- coding: utf-8 -*-
import glob
icons = glob.glob("*.png")
f = open("../resources.qrc", "w")
f.write("<RCC>\n")
f.write("    <qresource>\n")
for icon in icons:
    f.write('        <file alias="%s">icons/%s</file>\n' % (str(icon),str(icon)))
f.write("    </qresource>\n")
f.write("</RCC>\n")
f.close()