#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2021 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c21856.ad.smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Test map a swath outline onto a map-projected area, and from there create a
2-d array of lons,lats of the area inside the swath.

"""

from pmw_data_coverage import find_actual_tlefile
from pmw_data_coverage import create_pass

from pyresample.boundary import AreaDefBoundary
from pyresample import load_area
from trollsched.drawing import save_fig
from datetime import datetime, timedelta
import scipy.ndimage as ndimage
import numpy as np
from pyresample import kd_tree, geometry

AREA_DEF_FILE = '/home/a000680/usr/src/pytroll-config/etc/areas.yaml'
AREAID = 'euro4'


if __name__ == "__main__":

    sensor = 'viirs'
    satname = 'NOAA-20'

    start_time = datetime(2021, 11, 1, 11, 54)
    end_time = start_time + timedelta(minutes=14)

    tle_filename = find_actual_tlefile(start_time)
    mypass = create_pass(satname, sensor, start_time, end_time, tle_filename)

    save_fig(mypass)

    # Now we have a number of geo points:
    # mypass.boundary.contour_poly.lon, mypass.boundary.contour_poly.lat
    # 1) Map these points (using the value of 1 for each point) onto the output area (euro4)
    # 2) Then use scipy's ndimage to create a mask
    # ...

    #import scipy.ndimage as ndimageleft
    #r_mask = ndimage.binary_fill_holes(r_mask)

    lons, lats = mypass.boundary.contour_poly.lon, mypass.boundary.contour_poly.lat
    lons = np.rad2deg(lons)
    lats = np.rad2deg(lats)

    swath_def = geometry.SwathDefinition(lons=lons, lats=lats)
    shape = lons.shape
    data = np.ones(shape)
    areadef = load_area(AREA_DEF_FILE, AREAID)
    result = kd_tree.resample_nearest(swath_def, data,
                                      areadef, radius_of_influence=50000)

    r_mask = ndimage.binary_fill_holes(result)
