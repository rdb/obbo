import panda3d.core as p3d

_SB_VERT = """
#version 120

uniform mat4 p3d_ModelViewProjectionMatrix;

attribute vec4 p3d_Vertex;
attribute vec2 p3d_MultiTexCoord0;

varying vec2 v_texcoord;
void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_texcoord = p3d_MultiTexCoord0;
}
"""

_SB_FRAG = """
#version 120

uniform sampler2D p3d_Texture0;

varying vec2 v_texcoord;

void main() {
    vec4 texcolor = texture2D(p3d_Texture0, v_texcoord);
    gl_FragColor = vec4(texcolor.rgb, 1.0);
}
"""

class Skybox:
    def __init__(self, parent):
        self.root = loader.load_model('models/space.bam')
        #self.root.set_shader(p3d.Shader.make(
        #    p3d.Shader.SL_GLSL,
        #    vertex=_SB_VERT,
        #    fragment=_SB_FRAG
        #))
        self.root.set_scale(50)
        self.root.set_bin('background', 0)
        self.root.set_depth_write(False)
        self.root.reparent_to(parent)
