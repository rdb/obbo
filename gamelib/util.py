import math

from panda3d import core
from direct.interval.IntervalGlobal import *


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


def shake_cam(shake_time, pos_only=False):
    start_pos = base.camera.get_pos()
    x = start_pos.x
    y = start_pos.y
    start_hpr = base.camera.get_hpr()
    h = start_hpr.x
    p = start_hpr.y
    r = start_hpr.z
    num_steps = math.ceil(shake_time / 0.4)
    pos_shake = []
    hpr_shake = []
    for _ in range(num_steps):
        pos_shake += [base.camera.posInterval(0.1, (x - 0.05, y + 0.05, start_pos.z), start_pos),
            base.camera.posInterval(0.1, (x + 0.05, y - 0.05, start_pos.z)),
            base.camera.posInterval(0.1, (x - 0.05, y + 0.05, start_pos.z)),
            base.camera.posInterval(0.1, start_pos)]
        hpr_shake += [base.camera.hprInterval(0.1, (h - 1, p + 1, r - 1), start_hpr),
            base.camera.hprInterval(0.1, (h + 1, p - 1, r + 1)),
            base.camera.hprInterval(0.1, (h - 1, p + 1, r - 1)),
            base.camera.hprInterval(0.1, start_hpr)]

    if pos_only:
        cycle = Sequence(*pos_shake)
    else:
        cycle = Parallel(Sequence(*pos_shake), Sequence(*hpr_shake))
    cycle.start()
