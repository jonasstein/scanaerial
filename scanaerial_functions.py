#!/usr/bin/env python
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

if __name__ == "__main__":
    exit(0)

from sys import setrecursionlimit
setrecursionlimit(1500000)    
    
def distance(a, b):
    """
    Euclidean metric
    """
    return  ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5
    
def point_line_distance(point, startline, endline):
    """
    check if the "line" is actually a point
    if not use
    http://mathworld.wolfram.com/Point-LineDistance2-Dimensional.html
    Copypasted from lakewalker
    """

    if (startline == endline):
        return ((startline[0] - endline[0]) ** 2 + \
                 (startline[1] - endline[1]) ** 2) ** 0.5
    else:
        return abs((endline[0] - startline[0]) * (startline[1] - point[1]) - \
                     (startline[0] - point[0]) * (endline[1] - startline[1])) / \
                      ((endline[0] - startline[0]) ** 2 + (endline[1] - startline[1]) ** 2) ** 0.5
                      
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
        seg_a = douglas_peucker(nodes[0:farthest_node + 1], epsilon)
        seg_b = douglas_peucker(nodes[farthest_node:-1], epsilon)
        nodes = seg_a[:-1] + seg_b
    else:
        return [nodes[0], nodes[-1]]
    return nodes