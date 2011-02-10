#!/usr/bin/python
# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*- 

import datetime
whole_time = datetime.datetime.now()
import os, sys, urllib2,  math, ImageDraw

from canvas import WmsCanvas


try:
        import psyco
        psyco.full()
except ImportError:
        pass


def debug(st):
  sys.stderr.write(str(st)+"\n")
  sys.stderr.flush()





lat = float(sys.argv[2])  #  Coordinates from command string. You can use SAS-Planet: click right mouse button on center of forest.
lon = float(sys.argv[1])  #  (format is decimal, for SAS-planet go to Settings and set'em there as --d.


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

dlat = 0.02                     # default values for proportion of requested image
dlon = 0.04                     # default values for proportion of requested image
           
douglas_peucker_epsilon = 0.45   # smoothness of way, bigger = less dots and turns = 0.6-1.3 is ok
color_str = 32                  # sensivity for color change, bigger = larger area covered = 20-23-25 is ok
tile_size = (256, 256)
#josm_string = "http://gis.ktimanet.gr/wms/wmsopen/wmsserver.aspx?request=GetMap&"
josm_string = "http://wms.latlon.org/?layers=bing&"

zoom = 13
proj = "EPSG:3857"


polygon_tags = {"source":"Bing Imagery traced by fuzzer",}

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
multipolygon = polygon_tags.copy()
multipolygon["type"] = "multipolygon"


web = WmsCanvas(josm_string, proj, zoom, tile_size, mode = "RGB")



def distance(a,b):
  #debug((a,b))
  return math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2+(a[2]-b[2])**2)             


black = 0
white = 1
was_expanded = True
H, W = 2**zoom, 2**zoom

normales_list = []        


if True:
  mask = WmsCanvas(None, proj, zoom, tile_size, mode = "1")

  #### Getting start pixel
  x,y  = web.PixelFrom4326(lon, lat)
  x,y = int(x),int(y)
  debug ((x,y))
  debug ((lon,lat))
  initcolour = web[x,y]
  debug(mask[x,y])
  color_table = {}
  directions = [(1,0),(-1,0),(0,1),(0,-1)]
  queue = set([(x,y),])
  mask[x,y] = white      
  ttz = datetime.datetime.now()
  normales_list = set([])
  norm_dir = {(0,-1):0,(1,0):1,(0,1):2,(-1,0):3}
  while queue:                            
    px = queue.pop()                      
    for d in directions:                  
      x1,y1 = px[0]+d[0], px[1]+d[1]
      #if x1 >= W or x1 < 0 or y1 >= H or y1 < 0:
      #  continue
      #debug(mask[x1,y1])
      if mask[x1,y1] is not white:
       col = web[x1,y1] 
       if col not in color_table:
          #debug(col)
          try:
           color_table[col] = (distance(initcolour, col) <= color_str)
          except:
           debug(web.tiles)
           debug(mask.tiles)
       if color_table[col]:
        #if distance(prev_col, cur_col) <= 7:
        
        mask[x1,y1] = white
        queue.add((x1,y1))
      # else:
      #  normales_list.add(((x1+px[0])/2.,(y1+px[1])/2.,norm_dir[px[0]-x1,px[1]-y1]))
  debug("First walk (masking): %s" % str(datetime.datetime.now() - ttz) )
  debug("Color table has %s entries" % len(color_table) )
  queue = [(x,y),]

  
               
          
  ttz = datetime.datetime.now()
  #mask_img = mask_img.filter(ImageFilter.MaxFilter(medianfilter_str))
  mask.MaxFilter(5)
  debug("B/W MaxFilter: %s" % str(datetime.datetime.now() - ttz) )
  web = mask
  mask = WmsCanvas(None, proj, zoom, tile_size, mode = "1")
  bc = 1
  ttz = datetime.datetime.now()
  
  while queue:
    px = queue.pop()
    for d in directions:
      x1,y1 = px[0]+d[0], px[1]+d[1]
      #if x1 >= W:                            
      #  normales_list.add(((x1+px[0])/2.,(y1+px[1])/2.,norm_dir[px[0]-x1,px[1]-y1]))
      #  continue                             
      #if x1 < 0:                             
      #  normales_list.add(((x1+px[0])/2.,(y1+px[1])/2.,norm_dir[px[0]-x1,px[1]-y1]))
      #  continue
      #if y1 >= H:                            
      #  normales_list.add(((x1+px[0])/2.,(y1+px[1])/2.,norm_dir[px[0]-x1,px[1]-y1]))
      #  continue                             
      #if y1 < 0:                             
      #  normales_list.add(((x1+px[0])/2.,(y1+px[1])/2.,norm_dir[px[0]-x1,px[1]-y1]))
      #  continue                             
      if mask[x1,y1] is not white and web[x1,y1] is white:
        mask[x1,y1] = white
        bc += 1
        queue.append((x1,y1))
      if web[x1,y1] is not white:
        normales_list.add(((x1+px[0])/2.,(y1+px[1])/2.,norm_dir[px[0]-x1,px[1]-y1]))
  debug("Found %s normales here."%len(normales_list))
  debug("Second walk (leaving only poly): %s" % str(datetime.datetime.now() - ttz) )
  

#  ttz = datetime.datetime.now()
#  mask_img.save("img.png")
#  debug("Debug mask write: %s" % str(datetime.datetime.now() - ttz) )


######## Copypasted from lakewalker
def point_line_distance(p0, p1, p2):
    ((x0, y0), (x1, y1), (x2, y2)) = (p0, p1, p2)

    if x2 == x1 and y2 == y1:
        # Degenerate cast: the "line" is actually a point.
        return math.sqrt((x1-x0)**2 + (y1-y0)**2)         
    else:                                                 
        # I don't understand this at all. Thank you, Mathworld.
        # http://mathworld.wolfram.com/Point-LineDistance2-Dimensional.html
        return abs((x2-x1)*(y1-y0) - (x1-x0)*(y2-y1)) / math.sqrt((x2-x1)**2 + (y2-y1)**2)

def douglas_peucker(nodes, epsilon):
    #print "Running DP on %d nodes" % len(nodes)
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
        #print "Minimized %d nodes to %d + %d nodes" % (len(nodes), len(seg_a), len(seg_b))
        nodes = seg_a[:-1] + seg_b                                                         
    else:                                                                                  
        return [nodes[0], nodes[-1]]                                                       

    return nodes

############## End of copypaste



osmcode = sys.stdout
osmcode.write('<osm version="0.6">')
node_num = 0
way_num = 0
#lo1, la1, lo2, la2 = tuple(bbox)
sys.setrecursionlimit(1500000)

outline = []

popped = False
lin = []
dir_names = ("^",">","v","<")
tz = datetime.datetime.now()
while normales_list:
  if not popped:
    
    x,y,d = normales_list.pop()
    lin = [(x,y),]
    popped = True
  found = False
  if d is 0:        ##  up-pointing vector
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
       x,y,d = kp
       lin.append((x,y))
       found = True
       break
  
  if not found:
   popped = False
   
   lin = douglas_peucker(lin, douglas_peucker_epsilon)
   debug("line found; simplified to %s"%len(lin))
   if len(lin)>=6:
      outline.append(lin)
      #debug(lin)
   lin = []
if lin:
  lin = douglas_peucker(lin, douglas_peucker_epsilon)
  debug("line post-found; simplified to %s"%len(lin))
  if len(lin)>=4:
      outline.append(lin)
  
debug("Normales walk: %s, " % (str(datetime.datetime.now() - ttz),) )

roles = {}
for lin in outline:
     area = 0
     prx,pry = lin[-1]
     for x,y in lin:
        area+=(x*pry-y*prx)/2
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
        for z in polygon_tags.iteritems():
          osmcode.write( ' <tag k="%s" v="%s" />"'%z)
     osmcode.write( "</way>")
if way_num < -1:
 osmcode.write( '<relation id="-1" version="1">')
 for y in range(way_num, 0):
   role = ("inner","outer")[int(roles[y])]   
   osmcode.write( '<member type="way" ref="%s" role="%s" />'%(y,role))
 for z in multipolygon.iteritems():
   osmcode.write( ' <tag k="%s" v="%s" />"'%z)
 osmcode.write( '</relation>')
osmcode.write("</osm>")
osmcode.flush()
debug("All done in: %s" % str(datetime.datetime.now() - whole_time) )  