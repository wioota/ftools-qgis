# -*- coding: utf-8 -*-
 
import rpy2.robjects as robjects

class Node:
    def __init__(self, name, className="", dimension=""):
        self.__name = name
        self.__class = className
        self.__dim = dimension
        self.__children = []
    def addChild(self, child):
        self.__children.append(child)
    def children(self):
        return self.__children
    def hasChildren(self):
        return len(self.__children)>0
    def name(self):
        return self.__name
    def className(self):
        return self.__class
    def dimensions(self):
        return self.__dim

def properties(obj):
    md = robjects.r.mode(obj)[0]
    lg = robjects.r.length(obj)[0]
    try:
        objdim = list(robjects.r.dim(obj))
        dim = "dim: %s, %s" % (str(objdim[0]),str(objdim[1]))
        if robjects.r["is.matrix"](obj)[0]:
            md = "matrix"
    except TypeError, e:
        dim = "length: %s" % str(lg)
    cls = robjects.r.oldClass(obj)
    if not robjects.r['is.null'](cls)[0]:
        md = cls[0]
        if robjects.r.inherits(obj, "factor")[0]:
            dim = "levels: %s" % robjects.r.length(robjects.r.levels(obj))[0]
    return {"className":md, "dimension":dim}

def recurse(obj, name):
    lg = robjects.r.length(obj)[0]
    nm = robjects.r.names(obj)
    props = properties(obj)
    node = Node(name, **props)
    if not robjects.r['is.recursive'](obj)[0] or lg < 1 or \
        name == 'call' or robjects.r['is.function'](obj)[0] or \
        robjects.r['is.environment'](obj)[0]:
        return node
    print name, props
    if robjects.r['is.null'](nm)[0]:
        nm = ["[[%s]]" % str(j+1) for j in range(lg)]
    for i in range(lg):
        dub = robjects.r['[[']
        node.addChild(recurse(dub(obj, i+1), nm[i]))
    return node

def browseEnv():
    objlist = list(robjects.r.ls())
    ix = objlist.count("last.warning")
    if ix > 0:
        objlist.remove("last.warning")
    n = len(objlist)
    if n == 0: # do nothing!
        return None
    nodes = []
    
    for objName in objlist:
        Spatial = False
        obj = robjects.r.get(objName)
        if not robjects.r['is.null'](robjects.r['class'](obj))[0] and robjects.r.inherits(obj, "Spatial")[0]:
            tmpClass = robjects.r.oldClass(obj)[0]
            obj = robjects.r['@'](obj, 'data')
        props = properties(obj)
        node = Node(objName, **props)
        node.addChild(recurse(obj, objName))
        if robjects.r['is.recursive'](obj)[0] \
            and not robjects.r['is.function'](obj)[0] \
            and not robjects.r['is.environment'](obj)[0]:
            node = recurse(obj, objName)
        elif not robjects.r['is.null'](robjects.r['class'](obj))[0]:
            if robjects.r.inherits(obj, "table")[0]:
                nms = robjects.r.attr(obj, "dimnames")
                lg = robjects.r.length(nms)
                props = properties(obj)
                node = Node(objName, **props)
                if len(robjects.r.names(nms)) > 0:
                    nm <- robjects.r.names(nms)
                else:
                    nm = ["" for k in range(lg)]
                for i in range(lg):
                    dub = robjects.r['[[']
                    node.addChild(Node(nm[i], **properties(dub(obj, i+1))))
            elif robjects.r.inherits(obj, "mts")[0]:
                props = properties(obj)
                node = Node(objName, **props)
                nm = robjects.r.dimnames(obj)[1]
                lg = len(nm)
                for k in range(lg):
                    dim = "length: %s" % robjects.r.dim(obj)[0]
                    md = "ts"
                    node.addChild(Node(nm[k], md, dim))
        nodes.append(node)
    return nodes

def main():
    robjects.r.load("/home/cfarmer/temp/.RData")
    i = browseEnv()[0]
    while i.hasChildren():
        print [i.name() for i in i.children()]

if __name__ == '__main__':
    main()