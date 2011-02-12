#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script will search a area with similar color and send
it back to JOSM
"""

# __version__ = 0.01 # later...
__author__ = "Darafei Praliaskouski, Jonas Stein"
__license__ = "GPL"
__credits__ = ["Lakewalker-developer-Team","JOSM-developer-Team"]
__email__ = "news@jonasstein.de"
__maintainer__ = "Jonas Stein"
__status__ = "Development"

from datetime import datetime
from sys import stderr, argv, stdout, setrecursionlimit

from canvas import WmsCanvas

try:
    import psyco
    psyco.full()

except ImportError:
    pass

def debug(debug_var):
    """write things to stderr
    """
    stderr.write(str(debug_var)+"\n")
    stderr.flush()

def distance(a, b):
    """ Euclidean metric
    """
#    debug((a, b))
    return  ((a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2)**0.5

def point_line_distance(point, startline, endline):
    """
    check if the "line" is actually a point
    if not use
    http://mathworld.wolfram.com/Point-LineDistance2-Dimensional.html
    Copypasted from lakewalker
    """

    if (startline == endline):
        return ((startline[0] - endline[0])**2 + \
                 (startline[1] - endline[1])**2   )**0.5
    else:
        return abs( (endline[0] - startline[0]) * (startline[1]-point[1]) - \
                     (startline[0] - point[0]) * (endline[1] - startline[1])) / \
                      ((endline[0] - startline[0])**2 + (endline[1] - startline[1])**2)**0.5

def douglas_peucker(nodes, epsilon):
    """
    makes a linear curve smoother see also
    http://en.wikipedia.org/wiki/Ramer-Douglas-Peucker_algorithm
    Copypasted from lakewalker
    """
        farthest_node = None
    farthest_dist = 0
    first = nodes[0]
    last = nodes[-1]

    for i in xrange(1, len(nodes) - 1):
        d = point_line_distance(nodes[i], first, last)
        if d > farthest_dist:
            farthest_dist = d
            farthest_node = i

    if farthest_dist > epsilon:
        seg_a = douglas_peucker(nodes[0:farthest_node+1], epsilon)
        seg_b = douglas_peucker(nodes[farthest_node:-1], epsilon)
        nodes = seg_a[:-1] + seg_b
    else:
        return [nodes[0], nodes[-1]]
    return nodes

PROGRAM_START_TIMESTAMP = datetime.now()

#========================================
# User configuration START
## default values for proportion of requested image
DLAT = 0.02
DLON = 0.04

# smoothness of way, bigger = less dots and turns = 0.6-1.3 is ok
# DOUGLAS_PEUCKER_EPSILON = 0.60 # for Benchmark
DOUGLAS_PEUCKER_EPSILON = 0.60

# sensivity for color change, bigger = larger area covered = 20-23-25 is ok
color_str = 30 # for Benchmark
# color_str = 42

tile_size = (256, 256) # for Benchmark
#tile_size = (512, 512)

# WMS_SERVER_URL = "http://gis.ktimanet.gr/wms/wmsopen/wmsserver.aspx?request=GetMap&"

# WMS_SERVER_URL = "http://wms.latlon.org/?layers=bing&" # for Benchmark
WMS_SERVER_URL = "http://wms.latlon.org/?layers=bing&"

# have a look at http://wms.latlon.org/ to select your favourite WMS server

# ZOOM = 17 # for Benchmark
ZOOM = 17
proj = "EPSG:3857"

POLYGON_TAGS = {"source":"Bing Imagery traced by fuzzer", "natural":"water"}

#
# User configuration END
#========================================

lon = float(argv[1])
lat = float(argv[2])
# Coordinates from command string.
# (format is decimal, for SAS-planet go to Settings and set'em there as --d.
# You can use SAS-Planet: click right mouse button on center of forest.

multipolygon = POLYGON_TAGS.copy()
multipolygon["type"] = "multipolygon"

web = WmsCanvas(WMS_SERVER_URL, proj, ZOOM, tile_size, mode = "RGB")

BLACK = 0
WHITE = 1
was_expanded = True

normales_list = []

if True:
    mask = WmsCanvas(None, proj, ZOOM, tile_size, mode = "1")

    ## Getting start pixel ##
    x, y  = web.PixelFrom4326(lon, lat)
    x, y = int(x), int(y)
#    debug ((x, y))
#    debug ((lon, lat))
    initcolour = web[x, y]
#    debug(mask[x, y])
    color_table = {}
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    queue = set([(x, y),])
    mask[x, y] = WHITE
    ttz = datetime.now()
    normales_list = set([])
    norm_dir = {(0, -1):0, (1, 0):1, (0, 1):2, (-1, 0):3}
    while queue:
        px = queue.pop()
        for d in directions:
            x1, y1 = px[0]+d[0], px[1]+d[1]
            if mask[x1, y1] is not WHITE:
                col = web[x1, y1]
                if col not in color_table:
          #debug(col)
                    try:
                        color_table[col] = (distance(initcolour, col) <= color_str)
                    except:
                        debug(web.tiles)
                        debug(mask.tiles)
                if color_table[col]:
                    mask[x1, y1] = WHITE
                    queue.add((x1, y1))

    debug("First walk (masking): %s" % str(datetime.now() - ttz) )
    debug("Color table has %s entries" % len(color_table) )
    queue = [(x, y), ]

    ttz = datetime.now()
    #mask_img = mask_img.filter(ImageFilter.MaxFilter(medianfilter_str))
    mask.MaxFilter(5)
    debug("B/W MaxFilter: %s" % str(datetime.now() - ttz) )
    web = mask
    mask = WmsCanvas(None, proj, ZOOM, tile_size, mode = "1")
    bc = 1
    ttz = datetime.now()

    while queue:
        px = queue.pop()
        for d in directions:
            x1, y1 = px[0]+d[0], px[1]+d[1]
            if mask[x1, y1] is not WHITE and web[x1, y1] is WHITE:
                mask[x1, y1] = WHITE
                bc += 1
                queue.append((x1, y1))
            if web[x1, y1] is not WHITE:
                normales_list.add(((x1 + px[0])/2., \
                                    (y1 + px[1])/2., \
                                      norm_dir[px[0] - x1, px[1]-y1]))
    debug("Found %s normales here."%len(normales_list))
    debug("Second walk (leaving only poly): %s" % str(datetime.now() - ttz) )

osmcode = stdout
osmcode.write('<osm version="0.6">')
node_num = 0
way_num = 0

setrecursionlimit(1500000)

outline = []

popped = False
lin = []

tz = datetime.now()

while normales_list:
    if not popped:
        x, y, d = normales_list.pop()
        lin = [(x, y), ]
        popped = True
    found = False
    if d is 0: #up-pointing vector
        search = [(x+0.5, y-0.5, 3),(x+1, y, 0),(x+0.5, y+0.5, 1)]
    if d is 1:
        search = [(x+0.5, y+0.5, 0),(x, y+1, 1),(x-0.5, y+0.5, 2)]
    if d is 2:
        search = [(x-0.5, y+0.5, 1),(x-1, y, 2),(x-0.5, y-0.5, 3)]
    if d is 3:
        search = [(x-0.5, y-0.5, 2),(x, y-1, 3),(x+0.5, y-0.5, 0)]
    for kp in search:
        if kp in normales_list:
            normales_list.remove(kp)
            x, y, d = kp
            lin.append((x, y))
            found = True
            break

    if not found:
        popped = False

        lin = douglas_peucker(lin, DOUGLAS_PEUCKER_EPSILON)
        debug("line found; simplified to %s"%len(lin))

        if len(lin)>=6:
            outline.append(lin)
        #debug(lin)
        lin = []

if lin:
    lin = douglas_peucker(lin, DOUGLAS_PEUCKER_EPSILON)
    debug("line post-found; simplified to %s"%len(lin))
    if len(lin)>=4:
        outline.append(lin)

debug("Normales walk: %s, " % (str(datetime.now() - ttz),) )

roles = {}
for lin in outline:
    area = 0
    prx, pry = lin[-1]
    for x, y in lin:
        area += (x * pry - y * prx) / 2
        prx = x
        pry = y

    for coord in lin:
        node_num -= 1
        lon, lat = web.PixelAs4326(coord[0], coord[1])
        osmcode.write( '<node id="%s" lon="%s" lat="%s" version="1" />'%(node_num, lon, lat))

    way_num -= 1
    roles[way_num] =  (area > 0)
    osmcode.write( '<way id="%s" version="1">'%(way_num))
    for y in range(node_num, node_num+len(lin)):
        osmcode.write('<nd ref="%s" />'%(y))
    osmcode.write('<nd ref="%s" />'%(node_num))
    if len(outline) == 1:
        for z in POLYGON_TAGS.iteritems():
            osmcode.write( ' <tag k="%s" v="%s" />"'%z)
    osmcode.write( "</way>")

if way_num < -1:
    osmcode.write( '<relation id="-1" version="1">')
    for y in range(way_num, 0):
        role = ("inner","outer")[int(roles[y])]
        osmcode.write( '<member type="way" ref="%s" role="%s" />'%(y, role))

    for z in multipolygon.iteritems():
        osmcode.write( ' <tag k="%s" v="%s" />"'%z)

    osmcode.write( '</relation>')
osmcode.write("</osm>")
osmcode.flush()
debug("All done in: %s" % str(datetime.now() - PROGRAM_START_TIMESTAMP) )

""" TODO

Ext_Tools nice substitute for fuzzer.jar

TMSZoom
TMS zoom is integer for all TMS tiles, but JOSM zoomlevel is not neccecarily matches any of TMS tiles.

"""
