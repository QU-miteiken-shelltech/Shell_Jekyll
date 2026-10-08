#version 330 core
// Default (identity) post effect.
//
// To apply your own GLSL, pass a replacement for this file to
// OpenGLImageWidget.set_effect_shader(...).  A replacement only has to define
//
//     vec4 userEffect(vec4 color, vec2 uv)
//
//   color : composited RGBA of all visible layers
//   uv    : position inside the image, (0,0) = top-left, (1,1) = bottom-right
//
// and may declare its own uniforms, set with OpenGLImageWidget.set_custom_uniform().
// The "#version 330 core" line may be omitted in a replacement; it is added.

vec4 userEffect(vec4 color, vec2 uv) {
    return color;
}
