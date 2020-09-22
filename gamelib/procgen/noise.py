"""Provides noise generation helpers."""

import random

import numpy as np
from pyfastnoiselite.pyfastnoiselite import FastNoiseLite, FractalType


def asteroid_noise(xy:int, z:int, radius=None, seed=None):  # pylint: disable=invalid-name
    """
    Returns an Array of 4 arrays, each containing an array for every z-step
    for each component (e.g. heading, pitch, radius, color).
    """
    twopi = np.linspace(-np.pi, np.pi, xy, endpoint=False)
    pitch = np.linspace(-np.pi / 2, np.pi / 2, z)
    radius = radius or np.sqrt(((xy / 2) ** 2) * 2)
    x_mesh = np.cos(twopi) * radius
    y_mesh = np.sin(twopi) * radius
    z_val = np.sin(pitch) * radius
    z_cos = np.cos(pitch)
    points = 4 * z * xy
    coords = np.empty((3, points), np.float32)
    z_half = (z - 1) // 2
    for dim in range(4):
        dim_off = dim * z
        for zid in range(z):
            z_factor = 1 - abs(zid - z_half) / z_half
            z_factor = z_factor * 0.5 + 0.5
            z_off = zid * xy + dim_off
            rad_off = dim * radius * 3
            coords[0, z_off:z_off + xy] = x_mesh * z_cos[zid] + rad_off
            coords[1, z_off:z_off + xy] = y_mesh * z_cos[zid] + rad_off
            coords[2, z_off:z_off + xy] = z_val[zid]

    seed = seed or random.randrange(2 ** 31)
    fnl = FastNoiseLite(seed)
    fnl.frequency = 0.045
    fnl.fractal_type = FractalType.FractalType_FBm
    arr = fnl.gen_from_coords(coords)

    retval = []
    for dim in range(4):
        dim_off = dim * z
        retval.append([])
        for zid in range(z):
            z_off = zid * xy + dim_off
            retval[-1].append(arr[z_off:z_off + xy])
    return retval
