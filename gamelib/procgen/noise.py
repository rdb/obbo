"""Provides noise generation helpers."""

import random

import numpy as np
from opensimplex import OpenSimplex


def asteroid_noise(xy:int, z:int, radius=None, seed=None):  # pylint: disable=invalid-name
    """
    Returns an Array of 4 arrays, each containing an array for every z-step
    for each component (e.g. heading, pitch, radius, color).
    """
    twopi = np.linspace(-np.pi, np.pi, xy, endpoint=False)
    radius = radius or np.sqrt(((xy / 2) ** 2) * 2)
    step_size = 2 * np.pi * radius / xy
    x_mesh = np.cos(twopi) * radius
    y_mesh = np.sin(twopi) * radius
    z_mesh = np.linspace(0, z * step_size, z)
    points = 4 * z * xy
    coords = np.empty((4, points), np.float32)
    z_half = (z - 1) // 2
    for dim in range(4):
        dim_off = dim * z
        for zid in range(z):
            z_factor = 1 - abs(zid - z_half) / z_half
            z_factor = z_factor * 0.5 + 0.5
            z_off = zid * xy + dim_off
            rad_off = dim * radius * 3
            coords[0, z_off:z_off + xy] = x_mesh + rad_off
            coords[1, z_off:z_off + xy] = y_mesh + rad_off
            coords[2, z_off:z_off + xy] = z_mesh[zid]
            coords[3, z_off:z_off + xy] = z_factor
    arr = np.empty((points,), np.float32)

    seed = seed or random.randrange(2 ** 31)
    osn = OpenSimplex()
    try:
        for i in range(points):
            arr[i] = osn.noise3d(coords[0, i], coords[1, i], coords[2, i]) * coords[3, i]
    except (ValueError, OverflowError):
        return asteroid_noise(xy, z, radius, random.randrange(2 ** 31))

    retval = []
    for dim in range(4):
        dim_off = dim * z
        retval.append([])
        for zid in range(z):
            z_off = zid * xy + dim_off
            retval[-1].append(arr[z_off:z_off + xy])
    return retval
