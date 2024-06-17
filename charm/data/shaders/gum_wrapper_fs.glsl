#version 330

uniform sampler2D wrapper_texture0;

in vec4 gl_FragCoord;

out vec4 fs_colour;

void main() {
    vec2 uv = gl_FragCoord.xy / vec2(textureSize(wrapper_texture0, 0));
    fs_colour = texture(wrapper_texture0, uv);
}
