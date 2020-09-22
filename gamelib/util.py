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
