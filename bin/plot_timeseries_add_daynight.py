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

"""Plot a time series of cloud cover data at a point from a cvs file. Add info on day/night.
"""


import matplotlib.pyplot as plt
from matplotlib import gridspec
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime
from fires_and_clouds.utils import find_actual_tlefile
from pyorbital.orbital import Orbital
from pyorbital import astronomy
from pyorbital.orbital import get_observer_look

from fires_and_clouds.satellite_scanning_geometry import convert_angles_zenith2scan
from fires_and_clouds.utils import NRK

#LONS = [NRK[0], ]
#LATS = [NRK[1], ]
# LONS = [22.897562, ] # Fire pixel 12 June, 2021
# LATS = [66.573494, ] # Fire pixel 12 June, 2021
LONS = [18.3244, ]  # Fire pixel 28 July, 2021, Lycksele
LATS = [64.8210, ]  # Fire pixel 28 July, 2021, Lycksele


def dt64_to_datetime(dt64):
    """Convert a numpy.datetime64 to a datetime object."""
    ts = (dt64 - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
    return datetime.utcfromtimestamp(ts)


def get_utc_times(pandas_df):
    """Get utc times as a list of datetime objects from a pandas data fram of numpy datetime64 objects."""
    # NB! Seems unecessary atm - works well with numpy.datetime64 arrays...
    utc_times = []
    for np_tobj in df.index.values:
        utc_times.append(dt64_to_datetime(np_tobj))

    return utc_times


def get_sensor_scan_angles(lons, lats, obstimes, satnames, tle_filename):
    """Get the satellite sensor viewing geometry at a given location and time."""

    angles = []
    for (obs_time, satname) in zip(obstimes, satnames):
        satorb = Orbital(satname.strip(), tle_file=tle_filename)
        _, satel = satorb.get_observer_look(obs_time, lons, lats, 0)

        satel = satel[0]
        if satel < 0:
            raise ValueError("Something wrong - satellite under horizon!")

        # Get longitude, latitude and altitude of the satellite:
        satpos = satorb.get_lonlatalt(obs_time)

        satz = 90 - satel
        scan_angle = convert_angles_zenith2scan(satz, satpos[2])
        print(satz, scan_angle)

        angles.append(scan_angle)

    return angles


if __name__ == "__main__":

    filename = "./cloud_cover_timeseries_viirs_firepoint_july28.csv"
    #filename = './cloud_cover_timeseries_viirs_norrkoping.csv'
    #filename = './cloud_cover_timeseries_viirs.csv'
    #filename = './cloud_cover_timeseries_avhrr_modis.csv'
    #filename = './cloud_cover_timeseries_avhrr_modis_norrkoping.csv'

    df = pd.read_csv(filename, parse_dates=['obstime'], index_col=['obstime'],
                     names=['obstime', 'cloud_cov', 'fraction_cloudfree', 'platform_name'])

    utc_times = get_utc_times(df)

    tlefile = find_actual_tlefile(utc_times[0])

    sat_scan_angles = get_sensor_scan_angles(LONS, LATS,
                                             df.index.values,
                                             df['platform_name'], tlefile)

    #np_tobj = df.index.values[0]
    #utc_time = dt64_to_datetime(np_tobj)

    #sol_zen = astronomy.sun_zenith_angle(np.array(utc_times), LONS, LATS)

    sol_zen = astronomy.sun_zenith_angle(df.index.values, LONS, LATS)

    shape = sol_zen.shape
    night = np.where(np.greater(sol_zen, 90), 1, np.nan)

    clcov_color = (0.1, 0.1, 0.1, 0.4)
    clear_color = (0.1, 0.3, 0.8, 0.8)

    days = mdates.DayLocator()
    hours = mdates.HourLocator(interval=3)
    dfmt = mdates.DateFormatter('%H:%M')

    #
    # Figure creation #1:
    # fig, ax = plt.subplots(figsize=(15, 6))

    # ax.xaxis.set_major_locator(hours)
    # ax.xaxis.set_major_formatter(dfmt)

    # ax.bar(df.index.values, df['cloud_cov'], color=clcov_color, width=0.02, label='cloudy')
    # ax.bar(df.index.values, df['fraction_cloudfree'], color=clear_color,
    #        bottom=df['cloud_cov'], width=0.02, label='cloudfree')
    # ax.bar(df.index.values, night, color=(0, 0, 0, 0.3), edgecolor='black', width=0.02, label='night')

    # # Set title and labels for axes
    # ax.set(xlabel="Observation time",
    #        ylabel="Cloud cover fraction",
    #        # title="Cloud cover fraction over one day from AVHRR/MODIS at a given point")
    #        # title="Cloud cover fraction over one day from VIIRS at a given point")
    #        title="Cloud cover fraction over one day from VIIRS at Norrköping")
    # ax.set_xlim((datetime(2021, 6, 11, 0), datetime(2021, 6, 12, 0)))
    # ax.xaxis_date()
    # ax.legend()
    # fig.autofmt_xdate()
    # plt.savefig('./cloudcover_time_series_viirs_newcolors_with_daynight.png')

    # Figure creation #2:
    fig = plt.figure(figsize=(15, 6))
    # set height ratios for subplots
    gs = gridspec.GridSpec(2, 1, height_ratios=[2, 1])
    ax0 = plt.subplot(gs[0])

    ax0.xaxis.set_major_locator(hours)
    ax0.xaxis.set_major_formatter(dfmt)

    ax0.bar(df.index.values, df['cloud_cov'], color=clcov_color, width=0.02, label='cloudy')
    ax0.bar(df.index.values, df['fraction_cloudfree'], color=clear_color,
            bottom=df['cloud_cov'], width=0.02, label='cloudfree')
    ax0.bar(df.index.values, night, color=(0, 0, 0, 0.0), edgecolor='black', linewidth=2.5,
            width=0.02, label='night')

    # Set title and labels for axes
    position = "(%4.1f,%4.1f)" % (LONS[0], LATS[0])
    ax0.set(xlabel="Observation time",
            ylabel="Cloud cover fraction",
            # title="Cloud cover fraction over one day from AVHRR/MODIS at Norrköping")
            # title="Cloud cover fraction over one day from AVHRR/MODIS at {point}".format(point=position))
            # title="Cloud cover fraction over one day from AVHRR/MODIS at a given point")
            # title="Cloud cover fraction over one day from VIIRS at a given point")
            title="Cloud cover fraction over one day from VIIRS at {point}".format(point=position))
    # title="Cloud cover fraction over one day from VIIRS at Norrköping")
    #ax0.set_xlim((datetime(2021, 6, 11, 0), datetime(2021, 6, 12, 0)))
    ax0.set_xlim((datetime(2021, 7, 26, 0), datetime(2021, 7, 28, 14)))
    ax0.xaxis_date()
    ax0.legend(loc='upper right')

    # the second subplot
    # shared axis X
    ax1 = plt.subplot(gs[1], sharex=ax0)

    ax1.bar(df.index.values, sat_scan_angles, color=(0.5, 0.3, 0.3, 0.8), width=0.02, label='scan-angle')
    ax1.legend(loc='upper right')

    fig.autofmt_xdate()
    plt.subplots_adjust(hspace=.0)
    # plt.savefig('./cloudcover_time_series_avhrr_modis_newcolors_with_daynight_norrkoping.png')
    # plt.savefig('./cloudcover_time_series_avhrr_modis_newcolors_with_daynight.png')
    # plt.savefig('./cloudcover_time_series_viirs_newcolors_with_daynight.png')
    # plt.savefig('./cloudcover_time_series_viirs_newcolors_with_daynight_norrkoping.png')
    plt.savefig('./cloudcover_time_series_viirs_newcolors_with_daynight_firepoint_july28.png')
