import pathlib
import time

import panda3d.core as p3d
from pman.hooks import Converter, converter_blend_bam

LOADOPTS = p3d.LoaderOptions()
LOADOPTS.flags |= p3d.LoaderOptions.LF_no_cache

def opt_bam(bampath):
    print(f'Optimizing {bampath}')
    bampath = p3d.Filename.from_os_specific(bampath)
    loader = p3d.Loader.get_global_ptr()
    modelroot = p3d.NodePath(loader.load_sync(bampath, LOADOPTS))

    for geomnp in modelroot.find_all_matches('**/+GeomNode'):
        geomnode = geomnp.node()
        for idx in range(geomnode.get_num_geoms()):
            geom = geomnode.modify_geom(idx)
            state = geomnode.get_geom_state(idx)
            if not state.has_attrib(p3d.MaterialAttrib):
                continue

            # Get material
            mat = state.get_attrib(p3d.MaterialAttrib).get_material()
            if not mat.has_base_color():
                if mat.has_diffuse():
                    print(f'mat on {geomnp} had no base_color, using diffuse')
                    base_color = mat.diffuse
                else:
                    print(f'mat on {geomnp} had no base_color or diffuse, skipping')
                    continue
            else:
                base_color = mat.base_color

            gvd = geom.get_vertex_data()
            if not gvd.has_column(p3d.InternalName.get_color()):
                # Apply base color to vertex color
                vformat = p3d.GeomVertexFormat(gvd.format)
                varray = p3d.GeomVertexArrayFormat()
                varray.add_column(
                    p3d.InternalName.get_color(),
                    4,
                    p3d.Geom.NT_float32,
                    p3d.Geom.C_color
                )
                vformat.add_array(varray)
                reg_format = p3d.GeomVertexFormat.register_format(vformat)
                gvd = gvd.convert_to(reg_format)
                geom.set_vertex_data(gvd)
                gvd = geom.modify_vertex_data()

                coldata = p3d.GeomVertexWriter(gvd, p3d.InternalName.get_color())
                while not coldata.is_at_end():
                    coldata.set_data4f(base_color)

            # Remove material
            state = state.remove_attrib(p3d.MaterialAttrib)
            geomnode.set_geom_state(idx, state)

    if bampath.get_basename() == 'buildings.bam':
        pass
        # for child in modelroot.children:
        #     pos = child.get_pos()
        #     child.set_pos(0, 0, 0)
        #     child.flatten_strong()
        #     child.set_pos(pos)
    else:
        modelroot.flatten_strong()
    modelroot.write_bam_file(bampath)

@Converter(['.blend'])
def extended_blend2bam(config, srcdir, dstdir, assets):
    converter_blend_bam(config, srcdir, dstdir, assets)

    start = time.perf_counter()
    bampaths = [
        str(pathlib.Path(i.replace(srcdir, dstdir)).with_suffix('.bam'))
        for i in assets
    ]
    bampaths = [
        i
        for i in bampaths
        if 'Environment' in i or i.endswith('buildings.bam')
    ]

    for i in bampaths:
        opt_bam(i)

    print(f'Optimizing took {time.perf_counter() - start:.4f}s')

if __name__ == '__main__':
    import sys
    opt_bam(sys.argv[1])
