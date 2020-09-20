// Based on code from:
//  * https://github.com/KhronosGroup/glTF-Sample-Viewer
//  * https://github.com/Moguri/panda3d-simplepbr/
//  * https://kink3d.github.io/blog/2017/10/04/Physically-Based-Toon-Shading-In-Unity

#version 120

#ifndef MAX_LIGHTS
    #define MAX_LIGHTS 8
#endif

const float WRAPPED_LAMBERT_W = 0.1;
const float RIM_LIGHT_POWER = 0.2;
const float DIFFUSE_STEP_EDGE = 0.01;
const float SPECULAR_STEP_EDGE = 0.01;
const float SPECULAR_CONTRIB_MAX = 0.5;

uniform struct p3d_MaterialParameters {
    vec4 baseColor;
    vec4 emission;
    float roughness;
    float metallic;
    float refractiveIndex;
} p3d_Material;

uniform struct p3d_LightSourceParameters {
    vec4 position;
    vec4 diffuse;
    vec4 specular;
    vec3 attenuation;
    vec3 spotDirection;
    float spotCosCutoff;
    float spotExponent;
#ifdef ENABLE_SHADOWS
    sampler2DShadow shadowMap;
    mat4 shadowViewMatrix;
#endif
} p3d_LightSource[MAX_LIGHTS];

uniform struct p3d_LightModelParameters {
    vec4 ambient;
} p3d_LightModel;

#ifdef ENABLE_FOG
uniform struct p3d_FogParameters {
    vec4 color;
    float density;
} p3d_Fog;
#endif

uniform vec4 p3d_ColorScale;

// Give texture slots names
#define p3d_TextureBaseColor p3d_Texture0
#define p3d_TextureMetalRoughness p3d_Texture1
#define p3d_TextureNormal p3d_Texture2
#define p3d_TextureEmission p3d_Texture3

uniform sampler2D p3d_TextureBaseColor;
uniform sampler2D p3d_TextureMetalRoughness;
uniform sampler2D p3d_TextureNormal;
uniform sampler2D p3d_TextureEmission;

const vec3 F0 = vec3(0.04);
const float PI = 3.141592653589793;
const float SPOTSMOOTH = 0.001;
const float LIGHT_CUTOFF = 0.001;

varying vec3 v_position;
varying vec4 v_color;
varying vec2 v_texcoord;
varying mat3 v_tbn;
#ifdef ENABLE_SHADOWS
varying vec4 v_shadow_pos[MAX_LIGHTS];
#endif

float saturate(float val) {
    return clamp(val, 0.0, 1.0);
}

void main() {
    vec4 metal_rough = texture2D(p3d_TextureMetalRoughness, v_texcoord);
    float perceptual_roughness = saturate(p3d_Material.roughness * metal_rough.g);
    float alpha_roughness = max(perceptual_roughness * perceptual_roughness, 0.01);
    vec4 base_color = p3d_Material.baseColor * v_color * p3d_ColorScale * texture2D(p3d_TextureBaseColor, v_texcoord);
    vec3 diffuse_color = base_color.rgb * (vec3(1.0) - F0);
#ifdef USE_NORMAL_MAP
    vec3 n = normalize(v_tbn * (2.0 * texture2D(p3d_TextureNormal, v_texcoord).rgb - 1.0));
#else
    vec3 n = normalize(v_tbn[2]);
#endif
    vec3 v = normalize(-v_position);

#ifdef USE_OCCLUSION_MAP
    float ambient_occlusion = metal_rough.r;
#else
    float ambient_occlusion = 1.0;
#endif

    vec4 color = vec4(vec3(0.0), base_color.a);

    float n_dot_v = saturate(abs(dot(n, v)));
    for (int i = 0; i < p3d_LightSource.length(); ++i) {
        vec3 lightcol = p3d_LightSource[i].diffuse.rgb;

        if (dot(lightcol, lightcol) < LIGHT_CUTOFF) {
            continue;
        }

        vec3 l = normalize(p3d_LightSource[i].position.xyz - v_position * p3d_LightSource[i].position.w);
        vec3 h = normalize(l + v);

        // Shadows
        float spotcos = dot(normalize(p3d_LightSource[i].spotDirection), -l);
        float spotcutoff = p3d_LightSource[i].spotCosCutoff;
        float shadowSpot = smoothstep(spotcutoff-SPOTSMOOTH, spotcutoff+SPOTSMOOTH, spotcos);
#ifdef ENABLE_SHADOWS
        float shadowCaster = shadow2DProj(p3d_LightSource[i].shadowMap, v_shadow_pos[i]).r;
#else
        float shadowCaster = 1.0;
#endif
        float shadow = shadowSpot * shadowCaster;

        // wrapped lambert diffuse
        float w = WRAPPED_LAMBERT_W;
        float diffuse = saturate((dot(n, l) + w) / ((1 + w) * (1 + w)));
        float stepped_diffuse = min(step(DIFFUSE_STEP_EDGE, diffuse) + w, 1);
        vec3 diffuse_contrib = diffuse_color * stepped_diffuse;

        // Blinn Phong specular
        float alpha2 = alpha_roughness * alpha_roughness;
        float shininess = 2.0 / alpha2 - 2.0;
        float n_dot_h = clamp(dot(n, h), 0.001, 1.0);
        float specular = pow(n_dot_h, shininess) / (PI * alpha2);
        float stepped_specular = min(step(SPECULAR_STEP_EDGE, specular), SPECULAR_CONTRIB_MAX);
        vec3 spec_contrib = vec3(stepped_specular);

        color.rgb += (diffuse_contrib + spec_contrib) * lightcol * shadow;

        float rim_light_term = 1 - pow(dot(v, n), RIM_LIGHT_POWER);
        color.rgb += vec3(rim_light_term);
    }

    // Ambient
    color.rgb += diffuse_color * p3d_LightModel.ambient.rgb * ambient_occlusion;

    // Emission
#ifdef USE_EMISSION_MAP
    color.rgb += p3d_Material.emission.rgb * texture2D(p3d_TextureEmission, v_texcoord).rgb;
#endif

#ifdef ENABLE_FOG
    // Exponential fog
    float fog_distance = length(v_position);
    float fog_factor = clamp(1.0 / exp(fog_distance * p3d_Fog.density), 0.0, 1.0);
    color = mix(p3d_Fog.color, color, fog_factor);
#endif

    gl_FragColor = color;
}
