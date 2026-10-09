#version 330 core

in vec2 vTex;
out vec4 FragColor;

#define MAX_LAYERS 8
uniform samplerBuffer uFrameBuf[MAX_LAYERS];  // layer i reads texture unit i
uniform int   uFrameOffset[MAX_LAYERS];       // first texel of the layer's frame inside its buffer
uniform ivec2 uFrameSize[MAX_LAYERS];         // (width, height) of the layer's frame
uniform int   uLayerEnabled[MAX_LAYERS];
uniform int   uLayerCount;
uniform vec3  uBgColor;

// Provided by the effect shader object (identity by default).
vec4 userEffect(vec4 color, vec2 uv);

vec4 over(vec4 top, vec4 bottom) {
    float outA = top.a + bottom.a * (1.0 - top.a);
    vec3 outRGB = (outA > 0.0001)
        ? (top.rgb * top.a + bottom.rgb * bottom.a * (1.0 - top.a)) / outA
        : vec3(0.0);
    return vec4(outRGB, outA);
}

// Sampler arrays may only be indexed by constants in GLSL 3.30, hence the chain.
vec4 fetchTexel(int layer, int texel) {
    if (layer == 0) return texelFetch(uFrameBuf[0], texel);
    if (layer == 1) return texelFetch(uFrameBuf[1], texel);
    if (layer == 2) return texelFetch(uFrameBuf[2], texel);
    if (layer == 3) return texelFetch(uFrameBuf[3], texel);
    if (layer == 4) return texelFetch(uFrameBuf[4], texel);
    if (layer == 5) return texelFetch(uFrameBuf[5], texel);
    if (layer == 6) return texelFetch(uFrameBuf[6], texel);
    if (layer == 7) return texelFetch(uFrameBuf[7], texel);
    return vec4(0.0);
}

// Hand-written bilinear filtering (buffer textures have no hardware filter);
// equivalent to GL_LINEAR + clamp-to-edge on a normal texture.
vec4 sampleLayer(int layer) {
    ivec2 size = uFrameSize[layer];
    vec2 p = vTex * vec2(size) - 0.5;
    ivec2 p0 = ivec2(floor(p));
    vec2 f = fract(p);
    ivec2 lo = clamp(p0, ivec2(0), size - 1);
    ivec2 hi = clamp(p0 + 1, ivec2(0), size - 1);
    int base = uFrameOffset[layer];
    vec4 a = fetchTexel(layer, base + lo.y * size.x + lo.x);
    vec4 b = fetchTexel(layer, base + lo.y * size.x + hi.x);
    vec4 c = fetchTexel(layer, base + hi.y * size.x + lo.x);
    vec4 d = fetchTexel(layer, base + hi.y * size.x + hi.x);
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void main() {
    vec4 accum = vec4(0.0);
    // Layer 0 (top of the layer list) is drawn last, i.e. on top.
    for (int i = min(uLayerCount, MAX_LAYERS) - 1; i >= 0; --i) {
        if (uLayerEnabled[i] != 0) {
            accum = over(sampleLayer(i), accum);
        }
    }
    vec3 finalColor = mix(uBgColor, accum.rgb, accum.a);
    FragColor = userEffect(vec4(finalColor, 1.0), vTex);
}
