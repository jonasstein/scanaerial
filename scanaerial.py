#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
This script will search an area with similar color and send
it back to JOSM
"""

__author__ = "Darafei Praliaskouski, Jonas Stein, Ruben W."
__license__ = "GPL"
__credits__ = ["Lakewalker-developer-Team", "JOSM-developer-Team", "Malenki"]
__email__ = "news@jonasstein.de"
__maintainer__ = "Jonas Stein"
__status__ = "Development"


import ConfigParser, sys
from time import clock
from sys import argv, stdout, setrecursionlimit
from canvas import WmsCanvas
from debug import debug
from scanaerial_functions import distance, point_line_distance, douglas_peucker

try:
    import psyco
    psyco.full()

except ImportError:
    pass
try:
    config = ConfigParser.ConfigParser()
    config.readfp(open(sys.path[0] + '/scanaerial.cfg'))
except:
    debug('could not read config')
    exit(1)

### main ###

try:
    INPUT_LAT = float(argv[1])
    INPUT_LON = float(argv[2])
except (IndexError, ValueError):
    debug("this program expects latitude longitude, now running debug mode")
    INPUT_LAT = 51.0720147
    INPUT_LON = 7.2181707
try:
    ZOOM = int(float(argv[3]))
except (IndexError, ValueError):
    debug("could not read TZoom from commandline, fixed zoom level is used")
    ZOOM = config.getint('WMS', 'fixedzoomlevel')  

# Coordinates from command string.
# (format is decimal, for SAS-planet go to Settings and set'em there as --d.
# You can use SAS-Planet: click right mouse button on center of forest.



# SET SOME CONSTANTS
BLACK = 0
WHITE = 1
PROGRAM_START_TIMESTAMP = clock()

WMS_SERVER_URL = config.get('WMS', 'wms_server_url')
PROJECTION = config.get('WMS', 'projection')
TILE_SIZE = (config.getint('WMS', 'tile_sizex'), config.getint('WMS', 'tile_sizey'))
#FIXME natural:water should go to .cfg NODES but how? It would be nice if the user could expand it for more keys.
WAY_TAGS = {"source:tracer":"scanaerial", \
                    "source:zoomlevel": ZOOM , \
                    "source:position":  config.get('WMS', 'wmsname'), \
                    "natural":"water"} 
POLYGON_TAGS = WAY_TAGS.copy()
POLYGON_TAGS["type"] = "multipolygon"

#smoothness of way, bigger = less dots and turns = 0.6-1.3 is ok
DOUGLAS_PEUCKER_EPSILON =  config.getfloat('SCAN', 'douglas_peucker_epsilon')

#sensivity for colour change, bigger = larger area covered = 20-23-25 is ok
colour_str = config.getfloat('SCAN', 'colour_str')




web = WmsCanvas(WMS_SERVER_URL, PROJECTION, ZOOM, TILE_SIZE, mode = "RGB")

was_expanded = True

normales_list = []

mask = WmsCanvas(None, PROJECTION, ZOOM, TILE_SIZE, mode = "1")

## Getting start pixel ##

x, y = web.PixelFrom4326(INPUT_LON, INPUT_LAT)
x, y = int(x), int(y)
INITCOLOUR = web[x, y]

colour_table = {}
DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
queue = set([(x, y), ])
mask[x, y] = WHITE
ttz = clock()
normales_list = set([])
norm_dir = {(0, -1):0, (1, 0):1, (0, 1):2, (-1, 0):3}

while queue:
    px = queue.pop()
    for d in DIRECTIONS:
        x1, y1 = px[0] + d[0], px[1] + d[1]
        if mask[x1, y1] is not WHITE:
            col = web[x1, y1]
            if col not in colour_table:
                try:
                    colour_table[col] = (distance(INITCOLOUR, col) <= colour_str)
                except:
                    debug(web.tiles)
                    debug(mask.tiles)
            if colour_table[col]:
                mask[x1, y1] = WHITE
                queue.add((x1, y1))

debug("First walk (masking): %s" % str(clock() - ttz))
debug("Colour table has %s entries" % len(colour_table))
queue = [(x, y), ]

ttz = clock()
mask.MaxFilter(config.getint('SCAN', 'maxfilter_setting'))
debug("B/W MaxFilter: %s" % str(clock() - ttz))
del web
oldmask = mask
mask = WmsCanvas(None, PROJECTION, ZOOM, TILE_SIZE, mode = "1")
bc = 1
ttz = clock()

while queue:
    px = queue.pop()
    for d in DIRECTIONS:
        x1, y1 = px[0] + d[0], px[1] + d[1]
        if mask[x1, y1] is not WHITE and oldmask[x1, y1] is WHITE:
            mask[x1, y1] = WHITE
            bc += 1
            queue.append((x1, y1))
        if oldmask[x1, y1] is not WHITE:
            normales_list.add(((x1 + px[0]) / 2., \
                                (y1 + px[1]) / 2., \
                                  norm_dir[px[0] - x1, px[1] - y1]))
debug("Found %s normales here." % len(normales_list))
debug("Second walk (leaving only poly): %s" % str(clock() - ttz))

stdout.write('<osm version="0.6">')
node_num = 0
way_num = 0


outline = []

popped = False
lin = []

tz = clock()

while normales_list:
    if not popped:
        x, y, d = normales_list.pop()
        lin = [(x, y), ]
        popped = True
    found = False
    if d is 0: #up-pointing vector
        search = [(x + 0.5, y - 0.5, 3), (x + 1, y, 0), (x + 0.5, y + 0.5, 1)]
    if d is 1:
        search = [(x + 0.5, y + 0.5, 0), (x, y + 1, 1), (x - 0.5, y + 0.5, 2)]
    if d is 2:
        search = [(x - 0.5, y + 0.5, 1), (x - 1, y, 2), (x - 0.5, y - 0.5, 3)]
    if d is 3:
        search = [(x - 0.5, y - 0.5, 2), (x, y - 1, 3), (x + 0.5, y - 0.5, 0)]
    for kp in search:
        if kp in normales_list:
            normales_list.remove(kp)
            x, y, d = kp
            lin.append((x, y))
            found = True
            break

    if not found:
        popped = False
        
        if not config.getint('SCAN', 'deactivate_simplifying'):
            lin = douglas_peucker(lin, DOUGLAS_PEUCKER_EPSILON)
            debug("line found; simplified to %s" % len(lin))
        else:
            debug("skipped simplifing")

        if len(lin) >= 6:
            outline.append(lin)
        lin = []

if lin:
    lin = douglas_peucker(lin, DOUGLAS_PEUCKER_EPSILON)
    debug("line post-found; simplified to %s" % len(lin))
    if len(lin) >= 4:
        outline.append(lin)

debug("Normales walk: %s, " % (str(clock() - ttz),))

roles = {}
for lin in outline:
    area = 0
    prx, pry = lin[-1]

    for x, y in lin:
        area += (x * pry - y * prx) / 2
        prx = x
        pry = y

        node_num -= 1
        lon, lat = oldmask.PixelAs4326(x, y)
        stdout.write('<node id="%s" lon="%s" lat="%s" version="1" />' % (node_num, lon, lat))  

    way_num -= 1
    roles[way_num] = (area > 0)
    stdout.write('<way id="%s" version="1">' % (way_num))
    for y in range(node_num, node_num + len(lin)):
        stdout.write('<nd ref="%s" />' % (y))
    stdout.write('<nd ref="%s" />' % (node_num))
    if len(outline) == 1:
        for z in WAY_TAGS.iteritems():
            stdout.write(' <tag k="%s" v="%s" />"' % z)
    stdout.write("</way>")

if way_num < -1:
    stdout.write('<relation id="-1" version="1">')
    for y in range(way_num, 0):
        role = ("inner", "outer")[int(roles[y])]
        stdout.write('<member type="way" ref="%s" role="%s" />' % (y, role))

    for z in POLYGON_TAGS.iteritems():
        stdout.write(' <tag k="%s" v="%s" />"' % z)

    stdout.write('</relation>')
stdout.write("</osm>")
stdout.flush()

debug("All done in: %s" % str(clock() - PROGRAM_START_TIMESTAMP))


""" TODO
* Zoomlevel to the source? May be soon there are higher resolutions and on different 
  zoomlevels things look quite different

"""
