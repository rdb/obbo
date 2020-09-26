import math

from panda3d import core


def srgb_color(color, alpha = 255):
    if isinstance(color, str):
        color = int(color.lstrip('#'), 16)

    return core.LColor(
        core.decode_sRGB_float((color >> 16) & 0xff),
        core.decode_sRGB_float((color >> 8) & 0xff),
        core.decode_sRGB_float(color & 0xff),
        alpha / 255.0)


def clamp_angle(deg):
    while deg > 180:
        deg -= 180
    while deg < -180:
        deg += 180
    return deg


def cfg_tuple(name, default, convert=float):
    if isinstance(default, (tuple, list)):
        default = ' '.join([str(i) for i in default])
    sval = core.ConfigVariableString(name, default).get_value()
    return tuple(
        (convert(i) for i in sval.strip().replace(',', ' ').split(' ') if i))


def ease_elastic_out(v):
    a = 0.1
    p = 0.2
    if v == 0:
        return 0
    if v >= 1:
        return 1
    a = 1
    s = p / 4
    return a * math.pow(2, -10 * v) * math.sin((v - s) * (2 * math.pi) / p) + 1
