"""Apply Buffy's verified NVK helper-invocation texture-scale fix only."""
def prepare(text, upstream, out, replace):
    shader = (upstream / 'xboxrecomp/src/nv2a_gl/gl_psh.c').read_text(encoding='utf-8')
    shader = replace(shader, '#include "gl_psh.h"',
                     '#include "../burnout3-sw/xboxrecomp/src/nv2a_gl/gl_psh.h"')
    shader = replace(shader,
        '            "layout(std140, set = 0, binding = 1) uniform FsU {\\n"',
        '            "layout(push_constant) uniform FsP { vec2 u_tscale[4]; };\\n"\n'
        '            "layout(std140, set = 0, binding = 1) uniform FsU {\\n"')
    shader = replace(shader, '            "    vec2 u_tscale[4];\\n"',
                     '            "    vec4 u_tscale_unused[4];\\n"')
    (out / 'gl_psh.c').write_text(shader, encoding='utf-8')
    text = replace(text, '        pli.pSetLayouts = &s_dsl;',
        '        pli.pSetLayouts = &s_dsl;\n'
        '        VkPushConstantRange sc1_scale_range = { VK_SHADER_STAGE_FRAGMENT_BIT, 0, 32 };\n'
        '        pli.pushConstantRangeCount = 1;\n'
        '        pli.pPushConstantRanges = &sc1_scale_range;')
    # Push every draw: clear/post passes share this range, so a value-only
    # cache would incorrectly retain their constants after returning to 3D.
    text = replace(text,
        '    p_push_desc(s_cb, VK_PIPELINE_BIND_POINT_GRAPHICS, s_layout, 0, 7, wr);',
        '    vkCmdPushConstants(s_cb, s_layout, VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof tscale, tscale);\n'
        '    p_push_desc(s_cb, VK_PIPELINE_BIND_POINT_GRAPHICS, s_layout, 0, 7, wr);')
    return text
