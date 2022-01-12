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

"""Various common helper tools
"""


from glob import glob
import os
from datetime import timedelta

from trollsched.satpass import Pass as overpass
from pyorbital.orbital import Orbital
from pyorbital import tlefile
from trollsift import Parser, globify

# Location = Longitude (deg), Latitude (deg), Altitude (km)
NRK = (16.148649, 58.581844, 0.052765)
#SDK = (26.632, 67.368, 0.18)

TLE_REALTIME_ARCHIVE = "/data/24/saf/polar_in/tle"
TLE_LONGTIME_ARCHIVE = "/data/lang/satellit/polar/orbital_elements/TLE"

# tle-202103222030.txt
tlepattern = 'tle-{time:%Y%m%d%H%M}.txt'
tlepattern2 = 'tle-{time:%Y%m%d}.txt'


def find_valid_file_from_list(parse_obj, obstime, tlefiles, tol_sec):

    found_file = None
    tlefiles.sort()
    seconds_dist = timedelta(days=10).total_seconds()
    for filepath in tlefiles[::-1]:
        res = parse_obj.parse(os.path.basename(filepath))
        dsecs = abs((res['time'] - obstime).total_seconds())

        if dsecs < seconds_dist:
            seconds_dist = dsecs
            found_file = filepath

        if seconds_dist < tol_sec:
            break

    return found_file


def find_actual_tlefile(obstime):
    """Given a time find the tle-file with the timestamp closest in time and return filename."""

    tlefiles = glob(os.path.join(TLE_REALTIME_ARCHIVE, globify(tlepattern)))

    p__ = Parser(tlepattern)
    found_file = None
    tol_sec = 3600

    found_file = find_valid_file_from_list(p__, obstime, tlefiles, tol_sec)
    if not found_file:
        for pattern in [tlepattern, tlepattern2]:
            p__ = Parser(pattern)
            tlefiles_archive = glob(os.path.join(TLE_LONGTIME_ARCHIVE + obstime.strftime("/%Y%m"), globify(pattern)))
            found_file = find_valid_file_from_list(p__, obstime, tlefiles_archive, tol_sec)
            if found_file:
                break

    return found_file


def get_sats_within_horizon(satnames, obstime, forward=1, tle_filename=None, location=NRK):
    """For a given time find all passes for a list of satellites within the horizon of a given location."""

    passes = {}
    local_horizon = 0
    for satname in satnames:
        satorb = Orbital(satname, tle_file=tle_filename)
        passlist = satorb.get_next_passes(obstime,
                                          forward,
                                          *location,
                                          horizon=local_horizon)

        passes[satname] = passlist

    return passes


def create_passes_inside_time_window(allpasses, instruments, time_left, time_right, tle_filename):
    """Go through list of passes and adapt passes so they are fully inside the relevant time window."""

    passes = []
    for satname in allpasses:
        for mypass in allpasses[satname]:
            rtime, ftime, uptime = mypass
            time_start = max(rtime, time_left)
            time_end = min(ftime, time_right)
            sensor = instruments.get(satname, 'mhs')
            if time_start > time_end:
                continue
            print(satname, sensor, rtime, ftime, time_start, time_end)
            passes.append(create_pass(satname, sensor,
                                      time_start, time_end, tle_filename))

    return passes


def create_pass(satname, instrument, starttime, endtime, tle_filename=None):
    """Create a satellite pass given a start and an endtime."""

    tle = tlefile.Tle(satname, tle_file=tle_filename)
    cpass = overpass(satname, starttime, endtime, instrument=instrument, tle1=tle.line1, tle2=tle.line2)

    return cpass
