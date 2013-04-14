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

if __name__ == "__main__":
    exit(0)

from PIL import Image, ImageFilter
try:
    from urllib.request import urlopen
    from urllib.error import URLError
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen
    from urllib2 import URLError
    from urllib2 import HTTPError
import io
import datetime
import sys
from time import clock
from debug import debug
#
import projections

time_str = {0:" first ", 1:" second ", 2:" third and last "}

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
        tile_x = x // self.tile_height
        x = x % self.tile_height
        tile_y = y // self.tile_width
        y = y % self.tile_width
        try:
            self.tiles[(tile_x, tile_y)]["pix"][x, y] = v
        except KeyError:
            self.FetchTile(tile_x, tile_y)
            self.tiles[(tile_x, tile_y)]["pix"][x, y] = v

    def __getitem__ (self, x):
        x, y = x
        tile_x = x // self.tile_height
        x = x % self.tile_height
        tile_y = y // self.tile_width
        y = y % self.tile_width
        for i in range(0, 3):
            try:
                return self.tiles[(tile_x, tile_y)]["pix"][x, y]
            except KeyError:
                self.FetchTile(tile_x, tile_y)
        raise KeyError("internal error while fetching tile")

    def ConstructTileUrl (self, x, y):
        a, b, c, d = projections.from4326(projections.bbox_by_tile(self.zoom, x, y, self.proj), self.proj)
        return self.wms_url + "width=%s&height=%s&srs=%s&bbox=%s,%s,%s,%s" % (self.tile_width, self.tile_height, self.proj, a, b, c, d)

    def FetchTile(self, x, y):
        dl_done = False
        server_error = False

        if (x, y) in self.tiles:
            return

        tile_data = ""
        if self.wms_url:
            remote = self.ConstructTileUrl (x, y)
            start = clock()
            for dl_retrys in range(0, 3):
                try:
                    contents = urlopen(remote).read()
                    
                except URLError as detail:
                    server_error = True
                    debug("error while fetching tile (" + str(x) + ", " + str(y) + ": " + str(detail))
                    debug("retry download" + time_str[dl_retrys] + "time")
                    continue

                except HTTPError as detail:
                    server_error = True
                    debug("error while fetching tile (" + str(x) + ", " + str(y) + ": " + str(detail))
                    debug("retry download" + time_str[dl_retrys] + "time")
                    continue

                debug("Download took %s sec" % str(clock() - start))
                try:
                    tile_data = Image.open(io.BytesIO(contents))

                except:
                    debug("error while loading tile image-data corrupt")
                    debug("retry download" + time_str[dl_retrys] + "time")
                    continue
                dl_done = True
                break
        
        if not dl_done:
            if server_error:
                raise URLError(detail)
            tile_data = Image.new(self.mode, (self.tile_width, self.tile_height))
            debug("could not be loaded, blanking tile")

        if tile_data.mode != self.mode:
            tile_data = tile_data.convert(self.mode)
        self.tiles[(x, y)] = {}
        self.tiles[(x, y)]["im"] = tile_data
        self.tiles[(x, y)]["pix"] = tile_data.load()
        

    def PixelAs4326(self, x, y):
            return projections.coords_by_tile(self.zoom, 1. * x / self.tile_width, 1. * y / self.tile_height, self.proj)

    def PixelFrom4326(self, lon, lat):
        a, b = projections.tile_by_coords(lon, lat, self.zoom, self.proj)
        return a * self.tile_width, b * self.tile_height

    def MaxFilter(self, size = 3):
        for tile in self.tiles:
            self.tiles[tile]["pix"] = self.tiles[tile]["im"].filter(ImageFilter.MedianFilter(size)).load()
