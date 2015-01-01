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

    def __init__(self, server_url = None, server_api = None, proj = "EPSG:4326", zoom = 4, tile_size = None, mode = "RGBA"):
        self.server_url = server_url
        self.server_api = server_api
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
        if self.server_api == "tms":
            url = self.server_url
            url = url.replace("{zoom}", str(self.zoom))
            url = url.replace("{x}", str(x))
            url = url.replace("{y}", str(y))
            return url
        elif self.server_api == "wms":
            a, b, c, d = projections.from4326(projections.bbox_by_tile(self.zoom, x, y, self.proj), self.proj)
            return self.server_url + "width=%s&height=%s&srs=%s&bbox=%s,%s,%s,%s" % (self.tile_width, self.tile_height, self.proj, a, b, c, d)
        else:
            return self.server_url.replace("{quadkey}", self.ConstructQuadkey(x, y))

    def baseN(self, num, b, numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
        """Convert num into string with base b"""
        return ((num == 0) and numerals[0]) or (self.baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

    def ConstructQuadkey (self, tileX, tileY):
        """return Bing quadkey for given integer tile
        see (http://msdn.microsoft.com/en-us/library/bb259689.aspx)"""
        
        tileX2 = self.baseN(tileX, 2)
        tileY2 = self.baseN(tileY, 2)
        
        pad = self.zoom
        
        tileX2 = "0"*(pad - len(tileX2)) + tileX2
        tileY2 = "0"*(pad - len(tileY2)) + tileY2
        
        quadkey2 = ""
        for x in range(pad):
            quadkey2 = quadkey2 + tileY2[x] + tileX2[x]
        
        quadkey = int(quadkey2, 2)
        
        quadkey4 = self.baseN(quadkey, 4)
        quadkey4_pad = "0"*(pad - len(str(quadkey4))) + str(quadkey4)

        return quadkey4_pad

    def FetchTile(self, x, y):
        dl_done = False
        server_error = False

        if (x, y) in self.tiles:
            return

        tile_data = ""
        if self.server_url:
            remote = self.ConstructTileUrl (x, y)
            debug("URL: " + remote)
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
        scale = 1.0
        if (self.server_api == "tms") or (self.server_api == "bing"):
            scale = 0.5
        return projections.coords_by_tile(self.zoom, scale * x / self.tile_width, scale * y / self.tile_height, self.proj)

    def PixelFrom4326(self, lon, lat):
        scale = 1.0
        if (self.server_api == "tms") or (self.server_api == "bing"):
            scale = 2.0
        a, b = projections.tile_by_coords(lon, lat, self.zoom, self.proj)
        return scale * a * self.tile_width, scale * b * self.tile_height

    def MaxFilter(self, size = 3):
        for tile in self.tiles:
            self.tiles[tile]["pix"] = self.tiles[tile]["im"].filter(ImageFilter.MedianFilter(size)).load()
