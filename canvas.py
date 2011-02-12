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

import projections
import Image, ImageFilter
import urllib2
import StringIO
import datetime
import sys

def debug(st):
    sys.stderr.write(str(st)+"\n")

class WmsCanvas:

    def __init__(self, wms_url = None, proj = "EPSG:4326", zoom = 4, tile_size = None, mode = "RGBA"):
        self.wms_url = wms_url
        self.zoom = zoom
        self.proj = proj
        self.mode = mode
        self.tile_height = 256
        self.tile_width = 256

        if tile_size:
            self.tile_width, self.tile_height = tile_size
        self.tiles = {}

    def __setitem__ (self, x, v):
        x, y = x
        tile_x = int(x/self.tile_height)
        x = x % self.tile_height
        tile_y = int(y/self.tile_width)
        y = y % self.tile_width
        try:
            self.tiles[(tile_x, tile_y)]["pix"][x,y] = v
        except KeyError:
            self.FetchTile(tile_x, tile_y)
            self.tiles[(tile_x, tile_y)]["pix"][x,y] = v

    def __getitem__ (self, x):
        x, y = x
        tile_x = int(x/self.tile_height)
        x = x % self.tile_height
        tile_y = int(y/self.tile_width)
        y = y % self.tile_width
        try:
            return self.tiles[(tile_x, tile_y)]["pix"][x,y]
            except KeyError:
            self.FetchTile(tile_x, tile_y)
            return self.tiles[(tile_x, tile_y)]["pix"][x,y]

    def ConstructTileUrl (self, x, y):
        a,b,c,d = projections.from4326(projections.bbox_by_tile(self.zoom, x, y, self.proj), self.proj)
        return self.wms_url + "width=%s&height=%s&srs=%s&bbox=%s,%s,%s,%s"%(self.tile_width, self.tile_height, self.proj, a,b,c,d)

    def FetchTile(self, x, y):
        if not (x,y) in self.tiles:
            im = ""
            if self.wms_url:
                remote = self.ConstructTileUrl (x, y)
                debug(remote)
                ttz = datetime.datetime.now()
                contents = urllib2.urlopen(remote).read()
                debug("Download took %s" % str(datetime.datetime.now() - ttz))
                im = Image.open(StringIO.StringIO(contents))
                if im.mode != self.mode:
                    im = im.convert(self.mode)
            else:
                im = Image.new(self.mode, (self.tile_width,self.tile_height))
                debug("blanking tile")
            self.tiles[(x,y)] = {}
            self.tiles[(x,y)]["im"] = im
            self.tiles[(x,y)]["pix"] = im.load()

    def PixelAs4326(self,x,y):
            return projections.coords_by_tile(self.zoom, 1.*x/self.tile_width, 1.*y/self.tile_height, self.proj)

    def PixelFrom4326(self,lon,lat):
        a,b =  projections.tile_by_coords((lon, lat), self.zoom, self.proj)
        return a*self.tile_width, b*self.tile_height

    def MaxFilter(self, size = 5):
        tiles = self.tiles.keys()
        for tile in tiles:
            self.tiles[tile]["im"] = self.tiles[tile]["im"].filter(ImageFilter.MedianFilter(size))
            self.tiles[tile]["pix"] = self.tiles[tile]["im"].load()

   def MaxFilter(self, size = 5):
      tiles = self.tiles.keys()
      for tile in tiles:
        self.tiles[tile]["im"] = self.tiles[tile]["im"].filter(ImageFilter.MedianFilter(size))
        self.tiles[tile]["pix"] = self.tiles[tile]["im"].load()