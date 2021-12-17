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

"""
"""
from datetime import datetime, timedelta
from trollsched.drawing import save_fig

from fires_and_clouds.utils import create_passes_inside_time_window
from fires_and_clouds.utils import get_sats_within_horizon
from fires_and_clouds.utils import find_actual_tlefile

INSTRUMENTS = {'NOAA-20': 'viirs',
               'Suomi-NPP': 'viirs',
               'Metop-B': 'avhrr',
               'Metop-C': 'avhrr'}

if __name__ == "__main__":

    satnames = ['NOAA-20', 'Suomi-NPP']
    #satnames = ['Metop-B', 'Metop-C']
    start_time = datetime(2021, 6, 11, 8)
    end_time = datetime(2021, 6, 11, 14)
    delta_t = timedelta(minutes=60)
    nhours = 12

    tle_file = find_actual_tlefile(start_time)

    nextpasses = get_sats_within_horizon(satnames,
                                         start_time - delta_t,
                                         forward=nhours, tle_filename=tle_file)

    mypasses = create_passes_inside_time_window(nextpasses,
                                                INSTRUMENTS,
                                                start_time,
                                                end_time, tle_file)

    for p in mypasses:
        passlength = p.falltime - p.uptime
        #one_hour = timedelta(hours=1)
        #timestr = (p.uptime + one_hour + passlength/2.).strftime('%b-%d %H:%M')
        timestr = (p.uptime + passlength/2.).strftime('%b-%d %H:%M')
        #save_fig(p, directory="./", plot_title=timestr)
        save_fig(p, plot_title=timestr)
