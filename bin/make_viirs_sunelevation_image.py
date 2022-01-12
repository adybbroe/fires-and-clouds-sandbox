#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 Adam.Dybbroe

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

"""Read a VIIRS SDR scene and remap and display sun- and satellite zenith angles on an area.
"""


from glob import glob
import os
import matplotlib.pyplot as plt
#import dask.array as da
import numpy as np

from satpy import Scene
from satpy.utils import debug_on
debug_on()

VIIRS_SDR_DIR = "/home/a000680/data/polar_in/jpss/lvl1/npp_20210610_0921_49841"

EARTH_RADIUS = 6371.0  # km


def make_cartopy_angle_plot(scn_obj, angle_param, **kwargs):
    """From a remapped Satpy scene object make a Cartopy plot of the sun/sat angles."""
    plotfile_name = kwargs.get('filename', './angles_plot.png')
    title = kwargs.get('title', 'Sun/sat angles for a VIIRS Scene')

    label = "Angle (degrees)"
    if angle_param in ['solar_zenith_angle']:
        label = "Solar Zenith angle (degrees)"
        crs = remap_scn[angle_param].attrs['area'].to_cartopy_crs()
        angles = remap_scn[angle_param]
    elif angle_param in ['solar_elevation_angle']:
        label = "Solar elevation angle (degrees)"
        crs = remap_scn['solar_zenith_angle'].attrs['area'].to_cartopy_crs()
        angles = 90. - remap_scn['solar_zenith_angle']
    else:
        print("Angle parameter not supported")
        return

    ax = plt.axes(projection=crs)

    ax.coastlines()
    ax.gridlines()
    ax.set_global()
    plt.title(title)
    plt.imshow(angles, transform=crs, extent=crs.bounds, origin='upper')
    cbar = plt.colorbar()

    cbar.set_label(label)
    plt.savefig(plotfile_name)
    # plt.show()


if __name__ == "__main__":

    areaid = 'euro4'
    FILENAMES = glob(os.path.join(VIIRS_SDR_DIR, "*h5"))

    scn = Scene(filenames=FILENAMES, reader='viirs_sdr')
    scn.load(['solar_zenith_angle', 'satellite_zenith_angle'])

    remap_scn = scn.resample(areaid, radius_of_influence=8000)

    CARTOPY = False

    #make_cartopy_angle_plot(remap_scn, 'solar_zenith_angle')
    if CARTOPY:
        make_cartopy_angle_plot(remap_scn, 'solar_elevation_angle',
                                title='Sun elevation angles for a VIIRS scene',
                                filename='./sun_elevation_angle.png')

    sun_elev = 90.0 - remap_scn['solar_zenith_angle']

    from trollimage.colormap import rdbu, greys
    from trollimage.image import Image

    img = Image(sun_elev.compute().data, mode="L")

    greys.set_range(-20, 0)
    rdbu.set_range(0, 90)
    my_cm = greys + rdbu
    img.colorize(my_cm)

    #rdbu.set_range(0, 90)
    # img.colorize(rdbu)

    img.show()
