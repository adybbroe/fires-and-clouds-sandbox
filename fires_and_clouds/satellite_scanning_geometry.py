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

"""Tools for satellite viewing geometry.

E.g to convert scanning angles to observer zenith angles
"""


import numpy as np

EARTH_RADIUS = 6371.0  # km


def convert_angles_scan2zenith(phi_scan, sat_height):
    """Convert satellite scan angles to satellite (observer) zenith angles."""
    scan_angle = np.deg2rad(phi_scan)
    rquota = (EARTH_RADIUS + sat_height) / EARTH_RADIUS
    trig = np.sin(scan_angle) + np.cos(scan_angle)**2 / np.sin(scan_angle)
    zenith_angle = np.arcsin(rquota / trig)

    return np.rad2deg(zenith_angle)


def convert_angles_zenith2scan(theta_zenith, sat_height):
    """Convert satellite (observer) zenith angles to satellite scan angles."""
    zenith_angle = np.deg2rad(theta_zenith)

    rquota = EARTH_RADIUS / (EARTH_RADIUS + sat_height)
    scan_angle = np.arcsin(rquota * np.sin(zenith_angle))

    return np.rad2deg(scan_angle)
