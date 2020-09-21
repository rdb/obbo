# Based heavily on the BSD licensed panda3d-simplepbr (https://github.com/Moguri/panda3d-simplepbr/)
import os

import panda3d.core as p3d

from direct.filter.CommonFilters import CommonFilters


__all__ = [
    'Pipeline'
]


def _add_shader_defines(shaderstr, defines):
    shaderlines = shaderstr.split('\n')

    for line in shaderlines:
        if '#version' in line:
            version_line = line
            break
    else:
        raise RuntimeError('Failed to find GLSL version string')
    shaderlines.remove(version_line)


    define_lines = [
        f'#define {define} {value}'
        for define, value in defines.items()
    ]

    return '\n'.join(
        [version_line]
        + define_lines
        + ['#line 1']
        + shaderlines
    )


def _load_shader_str(shadername, defines=None):
    shaderpath = p3d.Filename.expand_from(f'$MAIN_DIR/shaders/{shadername}').to_os_specific()

    with open(shaderpath) as shaderfile:
        shaderstr = shaderfile.read()

    if defines is not None:
        shaderstr = _add_shader_defines(shaderstr, defines)

    return shaderstr


class Pipeline:
    def __init__(
            self,
            *,
            render_node=None,
            window=None,
            camera_node=None,
            taskmgr=None,
            max_lights=4,
            use_normal_maps=False,
            use_emission_maps=True,
            exposure=0.0,
            enable_shadows=True,
            enable_fog=True,
            use_occlusion_maps=False
    ):
        if render_node is None:
            render_node = base.render

        if window is None:
            window = base.win

        if camera_node is None:
            camera_node = base.cam

        if taskmgr is None:
            taskmgr = base.task_mgr

        self._shader_ready = False
        self.render_node = render_node
        self.window = window
        self.camera_node = camera_node
        self.max_lights = max_lights
        self.use_normal_maps = use_normal_maps
        self.use_emission_maps = use_emission_maps
        self.enable_shadows = enable_shadows
        self.enable_fog = enable_fog
        self.exposure = exposure
        self.use_occlusion_maps = use_occlusion_maps

        # Create a CommonFilters instance
        self.filters = CommonFilters(window, camera_node)

        # Do not force power-of-two textures
        p3d.Texture.set_textures_power_2(p3d.ATS_none)

        # PBR Shader
        self._recompile_pbr()

        # Tonemapping
        self._setup_tonemapping()

        # Do updates based on scene changes
        taskmgr.add(self._update, 'render update')

        self._shader_ready = True

    def __setattr__(self, name, value):
        if hasattr(self, name):
            prev_value = getattr(self, name)
        else:
            prev_value = None
        super().__setattr__(name, value)
        if not self._shader_ready:
            return

        pbr_vars = [
            'max_lights',
            'use_normal_maps',
            'use_emission_maps',
            'enable_shadows',
            'enable_fog',
            'use_occlusion_maps',
        ]
        if name in pbr_vars and prev_value != value:
            self._recompile_pbr()
        elif name == 'exposure':
            self.filters.setExposureAdjust(self.exposure)

    def _recompile_pbr(self):
        pbr_defines = {
            'MAX_LIGHTS': self.max_lights,
        }
        if self.use_normal_maps:
            pbr_defines['USE_NORMAL_MAP'] = ''
        if self.use_emission_maps:
            pbr_defines['USE_EMISSION_MAP'] = ''
        if self.enable_shadows:
            pbr_defines['ENABLE_SHADOWS'] = ''
        if self.enable_fog:
            pbr_defines['ENABLE_FOG'] = ''
        if self.use_occlusion_maps:
            pbr_defines['USE_OCCLUSION_MAP'] = ''

        pbr_vert_str = _load_shader_str('pbr.vert', pbr_defines)
        pbr_frag_str = _load_shader_str('pbr.frag', pbr_defines)
        pbrshader = p3d.Shader.make(
            p3d.Shader.SL_GLSL,
            vertex=pbr_vert_str,
            fragment=pbr_frag_str,
        )
        self.render_node.set_shader(pbrshader)

    def _setup_tonemapping(self):
        if self._shader_ready:
            # Destroy previous buffers so we can re-create
            self.filters.cleanup()

            # Fix shadow buffers after CommonFilters.cleanup()
            for caster in self.get_all_casters():
                sbuff_size = caster.get_shadow_buffer_size()
                caster.set_shadow_buffer_size((0, 0))
                caster.set_shadow_buffer_size(sbuff_size)

        self.filters.setSrgbEncode()
        self.filters.setHighDynamicRange()
        self.filters.setExposureAdjust(self.exposure)

    def get_all_casters(self):
        return [
            i.node()
            for i in self.render_node.find_all_matches('**/+LightLensNode')
            if i.node().is_shadow_caster()
        ]

    def _update(self, task):
        # Use a simpler, faster shader for shadows
        for caster in self.get_all_casters():
            state = caster.get_initial_state()
            if not state.has_attrib(p3d.ShaderAttrib):
                shader = p3d.Shader.make(
                    p3d.Shader.SL_GLSL,
                    vertex=_load_shader_str('shadow.vert'),
                    fragment=_load_shader_str('shadow.frag')
                )
                state = state.add_attrib(p3d.ShaderAttrib.make(shader), 1)
                caster.set_initial_state(state)

        # Use the auto-shader for node types that simplepbr does not support
        unsupported_types = [
            'TextNode',
        ]
        nodes = [
            node
            for node_type in unsupported_types
            for node in self.render_node.find_all_matches(f'**/+{node_type}')
        ]
        for node in nodes:
            if not node.has_attrib(p3d.ShaderAttrib):
                node.set_shader_auto(True)

        return task.cont
