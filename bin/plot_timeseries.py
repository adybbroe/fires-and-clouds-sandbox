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

"""Plot a time series of cloud cover data at a point from a cvs file.

"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime

# df = pd.read_csv('./cloud_cover_timeseries.csv', names=['obstime', 'cloud_cov', 'fraction_cloudfree'])
# fig, ax = plt.subplots(figsize=(15, 6))
# df.set_index('obstime').unstack().cloud_cov.plot(kind='bar', ax=ax, stacked=True)
# fig.autofmt_xdate()
# plt.show()

#filename = './cloud_cover_timeseries_viirs.csv'
filename = 'cloud_cover_timeseries_viirs_norrkoping.csv'
#filename = './cloud_cover_timeseries_avhrr_modis.csv'

df = pd.read_csv(filename, parse_dates=['obstime'], index_col=['obstime'],
                 names=['obstime', 'cloud_cov', 'fraction_cloudfree'])

fig, ax = plt.subplots(figsize=(15, 6))

days = mdates.DayLocator()
hours = mdates.HourLocator()
dfmt = mdates.DateFormatter('%H:%M')

ax.xaxis.set_major_locator(hours)
ax.xaxis.set_major_formatter(dfmt)
# ax.xaxis.set_minor_locator(hours)

clcov_color = (0.1, 0.1, 0.1, 0.4)
clear_color = (0.1, 0.3, 0.8, 0.8)
ax.bar(df.index.values, df['cloud_cov'], color=clcov_color, width=0.02, label='cloudy')
ax.bar(df.index.values, df['fraction_cloudfree'], color=clear_color,
       bottom=df['cloud_cov'], width=0.02, label='cloudfree')

# Set title and labels for axes
ax.set(xlabel="Observation time",
       ylabel="Cloud cover fraction",
       # title="Cloud cover fraction over one day from AVHRR/MODIS at a given point")
       title="Cloud cover fraction over one day from VIIRS at Norrköping")
ax.set_xlim((datetime(2021, 6, 11, 0), datetime(2021, 6, 12, 0)))
ax.xaxis_date()
ax.legend()
fig.autofmt_xdate()
plt.savefig('./cloudcover_time_series_viirs_newcolors_norrköping.png')
# plt.savefig('./cloudcover_time_series_viirs_newcolors.png')
# plt.savefig('./cloudcover_time_series_avhrr_modis.png')
# plt.show()
