#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2021, 2022 Adam.Dybbroe

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

"""Read NWCSAF/PPS cloud parameter and remap to area and overlay fire spots
"""
from glob import glob
import os

from fires_and_clouds.cloud_utils import generate_cloudmask_image
from fires_and_clouds.cloud_utils import get_cloudmask_scene
from fires_and_clouds.cloud_utils import get_satname_from_files

# Polar cloud products:
VIIRS_DATADIR = "/data/lang/satellit2/polar/pps/2021/06/11"
AVHRR_MODIS_DATADIR = "/data/lang/satellit/polar/PPS_products/satproj/2021/06/11"

SMHILOGO = "/home/a000680/data/logos/SMHIlogotypevitRGB8mm.png"
SMHILOGO_BLACK = "/home/a000680/data/logos/SMHIlogotypesvartRGB8mm.png"
FONTS = "/usr/share/fonts/dejavu/DejaVuSerif.ttf"

if __name__ == "__main__":

    #ppsfiles = glob(os.path.join(AVHRR_MODIS_DATADIR, "S_NWC_CMA_metopb*20210611T11*nc"))
    #ppsfiles = glob(os.path.join(AVHRR_MODIS_DATADIR, "S_NWC_CMA_noaa19*20210611T11*nc"))
    #ppsfiles = glob(os.path.join(AVHRR_MODIS_DATADIR, "S_NWC_CMA_metopb*20210611T09*nc"))
    #ppsfiles = glob(os.path.join(AVHRR_MODIS_DATADIR, "S_NWC_CMA_noaa19*20210611T09*nc"))

    ppsfiles = glob(os.path.join(VIIRS_DATADIR, "S_NWC_CMA_noaa20*20210611T11*nc"))

    platform_name = get_satname_from_files(ppsfiles)

    areaid = "euron1"

    scn = get_cloudmask_scene(ppsfiles)
    local_scn = scn.resample(areaid, radius_of_influence=8000)

    cma = local_scn['cma'] * 255
    local_scn['cma'] = cma
    local_scn['cma'].attrs['area'] = local_scn['cloudmask'].area

    start_time_txt = platform_name + ': ' + local_scn.start_time.strftime('%Y-%m-%d %H:%M')
    stime_fname = local_scn.start_time.strftime('%Y%m%d_%H%M')
    # output_filename = './cloudmask_{time}_{area}.png'.format(time=stime_fname,
    #                                                         area=areaid)
    output_filename = './cloudmask_{time}_{area}_nofires.png'.format(time=stime_fname,
                                                                     area=areaid)

    fire_point = {"type": "Feature",
                  "geometry": {"type": "Point", "coordinates": [22.897562, 66.573494]},
                  "properties": {"power": 4.39215326, "tb": 330.76779175,
                                 "observation_time": "2021-06-11T12:51:07",
                                 "platform_name": "Suomi-NPP"}}

    poi_list = [(fire_point['geometry']['coordinates'], '%5.2f' % fire_point['properties']['power']), ]
    points = {'font': FONTS, 'font_size': 48,
              'points_list': poi_list,
              'symbol': 'circle', 'ptsize': 24,
              'outline': 'black', 'width': 3,
              'fill': 'red', 'fill_opacity': 128,
              'box_outline': 'blue', 'box_linewidth': 0.5,
              'box_fill': (255, 150,  0), 'box_opacity': 200}

    coast = {'outline': (255, 100, 100), 'width': 1.5, 'level': 1, 'resolution': 'i'}
    borders = {'outline': (255, 100, 100), 'width': 1.0, 'level': 3, 'resolution': 'i'}
    #rivers = {'outline': (0,   0, 255), 'width': 1.0, 'level': 3, 'resolution': 'i'}

    local_scn.save_dataset('cma', filename=output_filename,
                           overlay={'coast_dir': '/home/a000680/data/shapes/',
                                    'overlays': {'coasts': coast,
                                                 'borders': borders}},
                           # 'rivers': rivers,
                           # 'points': points}},
                           decorate={'decorate': [
                               {'logo': {'logo_path': SMHILOGO_BLACK,
                                         'height': 90, 'bg': 'white', 'bg_opacity': 120}},
                               {'text': {'txt': start_time_txt,
                                         'align': {'top_bottom': 'top', 'left_right': 'left'},
                                         'font': FONTS,
                                         'font_size': 56,
                                         'height': 90,
                                         'bg': 'black',
                                         'bg_opacity': 120,
                                         'line': 'white'}}, ]})
