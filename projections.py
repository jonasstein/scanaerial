# -*- coding: utf-8 -*-
#    This file is part of tWMS.

#   tWMS is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   tWMS is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with tWMS.  If not, see <http://www.gnu.org/licenses/>.


import pyproj


projs = {
    "EPSG:4326":{
                  "proj": pyproj.Proj("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"),
                  "bounds": (-180.0,-90.0,180.0,90.0),
                },
    "EPSG:3395":{
                  "proj": pyproj.Proj("+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"),
                  "bounds": (-180.0,-85.0840591556,180.0,85.0840590501),
                },
    "EPSG:3857":{
                  "proj": pyproj.Proj("+proj=merc +lon_0=0 +lat_ts=0 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +units=m +no_defs"),
                  "bounds": (-180.0,-85.0511287798,180.0,85.0511287798),
                }
        }
proj_alias = {
     "EPSG:900913": "EPSG:3857",
     "EPSG:3785": "EPSG:3857",
              }

def tile_by_bbox(bbox, zoom, srs):
    """
    Converts bbox from 4326 format to tile numbers of given zoom level, with correct wraping around 180th meridian
    """
    a1, a2 = tile_by_coords((bbox[0],bbox[1]),zoom, srs)
    b1, b2 = tile_by_coords((bbox[2],bbox[3]),zoom, srs)
    if b1 < a1:
      b1 += 2**(zoom-1)
    return a1,a2,b1,b2

def bbox_by_tile(z,x,y, srs):
    """
    Tile numbers of given zoom level to EPSG:4326 bbox of srs-projected tile
    """
    a1,a2 = coords_by_tile(z,x,y,srs)
    b1,b2 = coords_by_tile(z,x+1,y+1,srs)
    return a1,b2,b1,a2


def coords_by_tile(z,x,y,srs):
    """
    Converts (z,x,y) to coordinates of corner of srs-projected tile
    """
    z -= 1
    normalized_tile = (x/(2.**z), 1.-(y/(2.**z)))
    projected_bounds = from4326(projs[proj_alias.get(srs,srs)]["bounds"], srs)
    maxp = [projected_bounds[2]-projected_bounds[0],projected_bounds[3]-projected_bounds[1]]
    projected_coords = [(normalized_tile[0]*maxp[0])+projected_bounds[0], (normalized_tile[1]*maxp[1])+projected_bounds[1]]
    return to4326(projected_coords, srs)


def tile_by_coords((lon,lat), zoom, srs):
    """
    Converts EPSG:4326 latitude and longitude to tile number of srs-projected tile pyramid.
    lat, lon - EPSG:4326 coordinates of a point
    zoom - zoomlevel of tile number
    srs - text string, specifying projection of tile pyramid
    """
    zoom -= 1
    projected_bounds = from4326(projs[proj_alias.get(srs,srs)]["bounds"], srs)
    point = from4326((lon,lat), srs)
    point = [point[0]-projected_bounds[0],point[1]-projected_bounds[1]]                       # shifting (0,0)
    maxp = [projected_bounds[2]-projected_bounds[0],projected_bounds[3]-projected_bounds[1]]
    point = [1.*point[0]/maxp[0],  1.*point[1]/maxp[1]]                                       # normalizing
    return point[0]*(2**zoom), (1-point[1])*(2**zoom)

def to4326 (line, srs):
    """
    Wrapper around transform call for convenience. Transforms line from srs to EPSG:4326
    line - a list of [lat0,lon0,lat1,lon1,...] or [(lat0,lon0),(lat1,lon1),...]
    srs - text string, specifying projection
    """
    return transform(line, srs, "EPSG:4326")

def from4326 (line, srs):
    """
    Wrapper around transform call for convenience. Transforms line from EPSG:4326 to srs
    line - a list of [lat0,lon0,lat1,lon1,...] or [(lat0,lon0),(lat1,lon1),...]
    srs - text string, specifying projection
    """
    return transform(line, "EPSG:4326", srs)

def transform (line, srs1, srs2):
    """
    Converts a bunch of coordinates from srs1 to srs2.
    line - a list of [lat0,lon0,lat1,lon1,...] or [(lat0,lon0),(lat1,lon1),...]
    srs[1,2] - text string, specifying projection (srs1 - from, srs2 - to)
    """
    line = list(line)
    serial = False
    if (type(line[0]) is not tuple) and (type(line[0]) is not list):
      serial = True
      l1 = []
      while line:
         a = line.pop(0)
         b = line.pop(0)
         l1.append([a,b])
      line = l1
    ans = []
    for point in line:
      p = pyproj.transform(projs[proj_alias.get(srs1,srs1)]["proj"], projs[proj_alias.get(srs2,srs2)]["proj"], point[0], point[1])
      if serial:
         ans.append(p[0])
         ans.append(p[1])
      else:
         ans.append(p)
    return ans

if __name__ == "__main__":
  pass