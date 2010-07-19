# -*- coding: utf-8 -*-

# rpy2 (R) imports
import rpy2.robjects as robjects

class Node:
    def __init__(self, name, className="", dimension="", memory=""):
        self.__name = name
        self.__class = className
        self.__dim = dimension
        self.__memory = memory
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
    def memory(self):
        return self.__memory

def properties(obj):
    md = robjects.r.mode(obj)[0]
    lg = robjects.r.length(obj)[0]
    try:
        objdim = list(robjects.r.dim(obj))
        dim = "dim: %s x %s" % (str(objdim[0]),str(objdim[1]))
        if robjects.r["is.matrix"](obj)[0]:
            md = "matrix"
    except TypeError, e:
        dim = "length: %s" % str(lg)
    cls = robjects.r.oldClass(obj)
    if not robjects.r['is.null'](cls)[0]:
        md = cls[0]
        if robjects.r.inherits(obj, "factor")[0]:
            dim = "levels: %s" % robjects.r.length(robjects.r.levels(obj))[0]
    memory = robjects.r.get("object.size", mode="function")
    mem = memory(obj)
    return {"className":md, "dimension":dim, "memory":str(mem)}

def recurse(obj, name, cur, level):
    lg = robjects.r.length(obj)[0]
    nm = robjects.r.names(obj)
    props = properties(obj)
    node = Node(name, **props)
    if not robjects.r['is.recursive'](obj)[0] or lg < 1 or \
        name == 'call' or robjects.r['is.function'](obj)[0] or \
        robjects.r['is.environment'](obj)[0]:
        return node
    if robjects.r['is.null'](nm)[0]:
        nm = ["[[%s]]" % str(j+1) for j in range(lg)]
    if level > 0 and cur >= level:
        return node
    for i in range(lg):
        dub = robjects.r['[[']
        node.addChild(recurse(dub(obj, i+1), nm[i], (i+1)+cur, level))
    return node

def browseEnv(level=0):
    # level: how deep do we dig into recursive variables?
    # note: zero (0) means we do full recursion
    objlist = list(robjects.r.ls())
    ix = objlist.count("last.warning")
    if ix > 0:
        objlist.remove("last.warning")
    n = len(objlist)
    if n == 0: # do nothing!
        return list()
    nodes = []

    for objName in objlist:
        spatial = False
        obj = robjects.r.get(objName)
        if not robjects.r['is.null'](robjects.r['class'](obj))[0] \
            and robjects.r.inherits(obj, "Spatial")[0]:
            spatClass = robjects.r.oldClass(obj)[0]
            spatName = objName
            objName = "@data"
            memory = robjects.r.get("object.size", mode="function")
            spatMem = memory(obj)
            obj = robjects.r['@'](obj, 'data')
            spatial = True

        props = properties(obj)
        node = Node(objName, **props)
        #node.addChild(recurse(obj, objName))
        if robjects.r['is.recursive'](obj)[0] \
            and not robjects.r['is.function'](obj)[0] \
            and not robjects.r['is.environment'](obj)[0]:
            node = recurse(obj, objName, 1, level)
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
                    memory = robjects.r.get("object.size", mode="function")
                    mem = memory(obj)
                    node.addChild(Node(nm[k], md, dim, str(mem)))
        if spatial:
            spatNode = Node(spatName, spatClass, node.dimensions(), str(spatMem))
            spatNode.addChild(node)
            node = spatNode
        nodes.append(node)
    return nodes

def main():
    robjects.r.load(".RData")
    print robjects.r.ls()
    a = browseEnv()
    print [i.hasChildren() for i in a]

if __name__ == '__main__':
    main()