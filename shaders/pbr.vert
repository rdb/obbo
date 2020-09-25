#version 120

#ifndef MAX_LIGHTS
    #define MAX_LIGHTS 8
#endif

#ifdef ENABLE_SHADOWS
uniform struct p3d_LightSourceParameters {
    vec4 position;
    vec4 diffuse;
    vec4 specular;
    vec3 spotDirection;
    float spotCosCutoff;
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
} p3d_LightSource[MAX_LIGHTS];
#endif

uniform mat4 p3d_ProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat3 p3d_NormalMatrix;

attribute vec4 p3d_Vertex;
attribute vec4 p3d_Color;
attribute vec3 p3d_Normal;
attribute vec2 p3d_MultiTexCoord0;

uniform vec2 uv_shift;


varying vec3 v_position;
varying vec4 v_color;
varying vec3 v_normal;
varying vec2 v_texcoord;
#ifdef ENABLE_SHADOWS
varying vec4 v_shadow_pos[MAX_LIGHTS];
#endif

void main() {
    vec4 vert_pos4 = p3d_ModelViewMatrix * p3d_Vertex;
    v_position = vec3(vert_pos4);
    v_color = p3d_Color;
    v_normal = normalize(p3d_NormalMatrix * p3d_Normal);
    v_texcoord = p3d_MultiTexCoord0 + uv_shift;
#ifdef ENABLE_SHADOWS
    for (int i = 0; i < p3d_LightSource.length(); ++i) {
        v_shadow_pos[i] = p3d_LightSource[i].shadowViewMatrix * vert_pos4;
    }
#endif

    gl_Position = p3d_ProjectionMatrix * vert_pos4;
}
