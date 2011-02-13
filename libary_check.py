#!/usr/bin/python
# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License.
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
Use this to detect missing libaries which are needed by fuzzer.
"""

import sys

def debug(st):
    sys.stderr.write(str(st)+"\n")
    
check = True

debug("searching (Image, ImageFilter) Python Image Libary...")
try:
    import Image, ImageFilter
    debug("Found.")
except ImportError:
    check = False
    debug("PIL missing, download at http://www.pythonware.com/products/pil/")

debug("searching (pyproj) Python Projection Libary...")
try:
    import pyproj
    debug("found.")
except ImportError:
    check = False
    debug("Python Projection Libary missing, download at http://code.google.com/p/pyproj/")
    
if check:
    print("Everthing works fine, you may run fuzzer now.")
