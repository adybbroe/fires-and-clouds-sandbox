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

"""Helper functions to handle cloud information from the NWCSAF
"""

import os
from glob import glob
import numpy as np
from matplotlib import cm
import matplotlib
import matplotlib.pyplot as plt
import cartopy.feature as cf

from datetime import datetime, timedelta

from satpy import Scene
from satpy.utils import debug_on
from trollsift.parser import Parser, globify
from pykdtree.kdtree import KDTree
from pyresample import load_area
from pyresample import kd_tree, geometry

from trollimage.colormap import rdbu, ylgnbu
from trollimage.image import Image


# debug_on()

AREAID = 'euron1'
AREA_DEF_FILE = "/home/a000680/usr/src/pytroll-config/etc/areas.yaml"

PPS_PATH = "/data/lang/satellit/polar/PPS_products/satproj/"

# S_NWC_CMA_eos1_99033_20180731T2128120Z_20180731T2141123Z.nc
PATTERN = "S_NWC_{product:s}_{platform_name:s}_{orbit_number:5d}_{starttime:%Y%m%dT%H%M%S%fZ}_{endtime:%Y%m%dT%H%M%S%fZ}.nc"

# PLATFORM_NAMES = {'npp': 'Suomi-NPP',
#                  'noaa20': 'NOAA-20'}

PPS_SATNAMES = {'npp': 'Suomi-NPP',
                'eos1': 'EOS-Terra',
                'eos2': 'EOS-Aqua',
                'noaa18': 'NOAA-18',
                'noaa19': 'NOAA-19',
                'noaa20': 'NOAA-20',
                'metopc': 'Metop-C',
                'metopb': 'Metop-B',
                'metopa': 'Metop-A',
                'noaa15': 'NOAA-15'}


def get_cloudmask_scene(ppsfiles):
    """Get a cloudmask scene from a set of files."""

    filenames = {'nwcsaf-pps_nc': ppsfiles}
    scn = Scene(filenames=filenames)
    scn.load(['cma', 'cloudmask'])

    return scn


def get_satname_from_files(pps_files):
    """From a set of pps files extract the satellite name."""

    pattern = 'S_NWC_{product:s}_{satid:s}_{orbit:s}_{start_time:%Y%m%dT%H%M%S%fZ}_{end_time:%Y%m%dT%H%M%S%fZ}.nc'

    bname = os.path.basename(pps_files[0])
    p__ = Parser(pattern)
    res = p__.parse(bname)
    return PPS_SATNAMES.get(res['satid'], res['satid'])


class PPSFilesGetter(object):
    """Getting PPS cloud product files in a given time interval."""

    def __init__(self, basedir, starttime, endtime, pattern=PATTERN):
        """Initialize."""
        self.basedir = basedir
        self.start_time = starttime
        self.end_time = endtime
        self.platforms = []
        self.product = None
        self.pattern = pattern
        self.parser = Parser(self.pattern)
        self.pps_files = {}
        self.granules = False

    def collect_product_files(self, platforms=list(PPS_SATNAMES.values()), product_name='CMA'):
        """Search PPS cloud product files within a time interval and add to the pps_files dict."""

        otime = self.start_time
        subdirs = []
        while otime < self.end_time:
            subdir = os.path.join(self.basedir, otime.strftime('%Y/%m/%d'))
            if subdir not in subdirs:
                subdirs.append(subdir)
            otime = otime + timedelta(days=30)

        flist = []
        for sdir in subdirs:
            flist = flist + glob(os.path.join(subdir, globify(self.pattern, {'product': product_name})))

        newflist = []
        for fpath in flist:
            fname = os.path.basename(fpath)
            res = self.parser.parse(fname)
            if PPS_SATNAMES.get(res['platform_name']) not in platforms:
                continue
            if res['starttime'] < self.start_time or res['endtime'] > self.end_time:
                continue

            newflist.append(fpath)

        if product_name not in self.pps_files:
            self.pps_files[product_name] = newflist
        else:
            self.pps_files[product_name] = self.pps_files[product_name] + newflist

    def gather_granules(self, product_name):
        """Gather granules"""

        granule_collection = {}
        for filepath in self.pps_files[product_name]:
            res = self.parser.parse(os.path.basename(filepath))
            keyname = res['platform_name'] + '_' + str(res['orbit_number'])
            if keyname not in granule_collection:
                granule_collection[keyname] = [filepath]
            else:
                granule_collection[keyname].append(filepath)

        self.granules = True
        self.pps_files[product_name] = granule_collection


def get_cloudfraction(lons, lats, filename):
    """Read the PPS cloudmask file and retrieve the cloud fraction at specified geographical positions."""

    scn = Scene(filenames=[filename], reader='nwcsaf-pps_nc')
    scn.load(['cma'])

    try:
        start_time = scn.attrs['start_time']
        end_time = scn.attrs['end_time']
    except KeyError:
        start_time = scn.start_time
        end_time = scn.end_time

    if 'viirs' in scn.sensor_names:
        pixels_per_scan = 16
    elif 'avhrr-3' in scn.sensor_names or 'avhrr' in scn.sensor_names:
        pixels_per_scan = 1
    else:
        pixels_per_scan = 10

    geodata = np.vstack((scn['cma'].area.lons.values.ravel(),
                         scn['cma'].area.lats.values.ravel())).T
    kd_tree = KDTree(geodata)
    shape = scn['cma'].shape
    number_of_scans = shape[0] / pixels_per_scan
    time_per_scan = (end_time - start_time) / number_of_scans

    req_point = np.vstack((lons, lats)).T.astype('float32')
    dists, kidx = kd_tree.query(req_point, k=1)

    rows, cols = kidx[:] / shape[1], kidx[:] % shape[1]
    rows = np.round(rows).astype('int')
    cols = np.round(cols).astype('int')

    obstimes = start_time + np.divide(rows, pixels_per_scan) * time_per_scan

    clcovs = []
    for (row, col, dist) in zip(rows, cols, dists):
        if dist < 0.1 and row >= 2 and col >= 2:
            arr = scn['cma'].data[row-2: row+3, col-2: col+3]
            arr = np.ma.masked_outside(arr, 0, 1)
            arr = arr.compressed()
            if len(arr) > 0:
                clcovs.append(arr.sum() / arr.shape[0])
            else:
                clcovs.append(np.nan)
        else:
            clcovs.append(np.nan)
            print("Outside or no-data. Continue...")

    return np.array(clcovs), obstimes


class LastCloudfreeView(object):
    """Keep track of the time of the last cloudfree observation."""

    def __init__(self, areaid, start_datetime):

        self.areaid = areaid
        self.start_time = start_datetime
        self.seconds = None
        self.area_def = load_area(AREA_DEF_FILE, self.areaid)
        self._crs = self.area_def.to_cartopy_crs()

        self.relative_obstimes = None
        self.scene_ids = []

    def get_cloudmask(self, ppsfiles):

        scn = get_cloudmask_scene(ppsfiles)
        scene_id = {'satellite': get_satname_from_files(ppsfiles),
                    'start_time': scn.start_time}
        self.scene_ids.append(scene_id)
        return scn

    def map_data(self, lons, lats, time_data):
        """Remap the data to projected area."""
        swath_def = geometry.SwathDefinition(lons=lons, lats=lats)
        result = kd_tree.resample_nearest(swath_def, time_data,
                                          self.area_def, radius_of_influence=10000,
                                          fill_value=None)
        return result

    def set_time_dataset(self, data):

        if self.relative_obstimes is None:
            self.relative_obstimes = data
        else:
            # Change only the pixels where it was cloudy before
            mask1 = self.relative_obstimes.mask
            mask2 = data.mask
            self.relative_obstimes = np.ma.where(mask1, data, self.relative_obstimes)
            self.relative_obstimes.mask = np.logical_and(mask1, mask2)

    def get_scene_times_cloudfree_view(self, scn):
        """Create a dataset with seconds from start_time to observation for all cloudfree pixels."""

        # Create an observation time dataset:
        num_of_lines = scn['cma'].shape[0]
        num_of_pixels_per_line = scn['cma'].shape[1]
        start_time_scene = scn['cma'].start_time
        end_time_scene = scn['cma'].end_time
        scene_length = end_time_scene - start_time_scene
        nsec = scene_length.total_seconds()

        delta_step = nsec/(num_of_pixels_per_line * num_of_lines)

        start_seconds = (self.start_time - start_time_scene).total_seconds()

        time_data = np.arange(num_of_pixels_per_line * num_of_lines)
        time_data = time_data.reshape(num_of_lines, num_of_pixels_per_line)
        time_data = time_data * delta_step
        time_data = time_data + start_seconds

        # Convert to minutes:
        time_data = (time_data / 60).astype('int')

        print("Min and max times in seconds: %d %d" % (time_data.min(), time_data.max()))

        # Create an array where value is -1 where it is cloudy:
        #time_data[scn['cma'].data == 1] = -1

        # Mask out "bowtie-deleted" pixels:
        mask = scn['cma'].data == 255
        #time_data = np.ma.masked_array(time_data, mask=mask)

        time_data = np.ma.masked_where(np.logical_or(scn['cma'].data == 1, scn['cma'].data == 255), time_data)
        #time_data.fill_value = 0

        lons = np.ma.masked_array(scn['cma'].area.lons.data.compute(), mask=mask)
        lats = np.ma.masked_array(scn['cma'].area.lats.data.compute(), mask=mask)

        return lons, lats, time_data

    def plot_data(self, filename):

        #cmap = cm.YlGn
        #cmaplist = [cmap(i) for i in range(cmap.N)]
        # create the new map
        #mycmap = cmap.from_list('Custom cmap', cmaplist, cmap.N)

        mycmap = cm.viridis

        # Plot the data with Cartopy:
        plt.figure(figsize=(14, 12))
        if len(self.scene_ids) > 1:
            time_span = '%s to %s' % (self.scene_ids[0]['start_time'].strftime('%Y-%m-%d %H%M'),
                                      self.scene_ids[-1]['start_time'].strftime('%Y-%m-%d %H%M'))
        else:
            time_span = '%s' % self.scene_ids[0]['start_time'].strftime('%Y-%m-%d %H%M')

        # font = {'family': 'normal',
        #         'weight': 'bold',
        #         'size': 20}
        # matplotlib.rc('font', **font)

        plt.rc('font', size=18)
        plt.tick_params(axis='both', labelsize=0, length=0)
        plt.title('Minutes since last cloudfree view: %s' % time_span)
        ax = plt.axes(projection=self._crs)
        ax.coastlines()
        ax.add_feature(cf.BORDERS)
        ax.gridlines()
        ax.set_global()
        plt.imshow(self.relative_obstimes, transform=self._crs,
                   extent=self._crs.bounds, interpolation='nearest',
                   origin='upper', cmap=mycmap)
        plt.clim(0, 720)
        cbar = plt.colorbar()
        cbar.set_label("Minutes")
        # ax.tick_params(axis=u'both', which=u'both',length=0) # Not tested!
        plt.savefig(filename)
        plt.clf()

    def create_image(self):

        data = self.relative_obstimes
        img = Image(data, mode="L", fill_value=None)
        print("Min: %d" % data.min())

        rdbu.set_range(0, data.max())
        img.colorize(ylgnbu)

        return img


def create_clfree_freshness_from_cloudmask(scn):
    """Get the cloudmask and derive a freshness of cloudfree view from it.

    From a scene (several VIIRS granules) with a PPS Cloudmask retrieve the
    cloud mask and generate a new dataset with seconds since start of day if
    cloudfree. If cloudy the seconds is set to zero.

    """

    # Create an observation time dataset:
    num_of_lines = scn['cma'].shape[0]
    num_of_pixels_per_line = scn['cma'].shape[1]
    start_time = scn['cma'].start_time
    end_time = scn['cma'].end_time
    scene_length = end_time - start_time
    nsec = scene_length.total_seconds()

    delta_step = nsec/(num_of_pixels_per_line * num_of_lines)

    start_seconds_of_day = (start_time -
                            datetime(start_time.year,
                                     start_time.month,
                                     start_time.day)).total_seconds()

    # total_seconds_one_day = 3600*24

    # time_data = (np.arange(num_of_pixels_per_line * num_of_lines) *
    #             delta_step + start_seconds_of_day)
    # time_data = time_data.reshape(num_of_lines, num_of_pixels_per_line)
    time_data = np.arange(num_of_pixels_per_line * num_of_lines)
    time_data = time_data.reshape(num_of_lines, num_of_pixels_per_line)
    time_data = time_data * delta_step
    time_data = time_data + start_seconds_of_day

    # Create array where value is 0 where it is cloudy:
    time_data[scn['cma'].data == 1] = 0

    # Mask out "bowtie-deleted" pixels:
    mask = scn['cma'].data == 255
    time_data = np.ma.masked_array(time_data, mask=mask)

    lons = np.ma.masked_array(scn['cma'].area.lons.data.compute(), mask=mask)
    lats = np.ma.masked_array(scn['cma'].area.lats.data.compute(), mask=mask)

    # plt.hist(time_data[::10, ::10])
    # plt.show()

    return lons, lats, time_data


def generate_cloudmask_image(scn, areaid=AREAID):
    """Generate a cloudmask image with coastlines and overlays."""

    smhilogo = "/home/a000680/data/logos/SMHIlogotypevitRGB8mm.png"
    eumetsatlogo = "/home/a000680/data/logos/eumetsat_logo.gif"
    fonts = "/usr/share/fonts/dejavu/DejaVuSerif.ttf"

    local_scn = scn.resample(areaid, radius_of_influence=8000)
    start_time_txt = local_scn.start_time.strftime('%Y-%m-%d %H:%M')

    local_scn.save_dataset('cloudmask',
                           filename='viirs_cloudmask_%s_%s.png' % (local_scn.start_time.strftime('%Y%m%d_%H%M'),
                                                                   areaid),
                           overlay={'coast_dir': '/home/a000680/data/shapes/', 'color': 'white'},
                           decorate={'decorate': [
                               {'logo': {'logo_path': smhilogo,
                                         'height': 90, 'bg': 'white', 'bg_opacity': 120}},
                               {'logo': {'logo_path': eumetsatlogo,
                                         'height': 90, 'bg': 'white', 'bg_opacity': 120}},
                               {'text': {'txt': start_time_txt,
                                         'align': {'top_bottom': 'top', 'left_right': 'left'},
                                         'font': fonts,
                                         'font_size': 56,
                                         'height': 90,
                                         'bg': 'black',
                                         'bg_opacity': 120,
                                         'line': 'white'}}]})
