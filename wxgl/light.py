#!/usr/bin/env python3

import sys
from OpenGL.GL import *
from . model import Model

class _Light:
    """光照模型基类"""
 
    def __init__(self, **kwds):
        """构造函数"""
 
        self.ambient = kwds.get('ambient')              # 环境光亮度
        self.lamp = kwds.get('lamp')                    # 光源位置
        self.direction = kwds.get('direction')          # 光的方向
        self.lightcolor = kwds.get('lightcolor')        # 光的颜色
        self.sky = kwds.get('sky')                      # 来自天空的环境光
        self.ground = kwds.get('ground')                # 来自地面的环境光
        self.diffuse = kwds.get('diffuse')              # 漫反射系数：值域范围[0.0, 1.0]，数值越大，表面越亮
        self.specular = kwds.get('specular')            # 镜面反射系数：值域范围[0.0, 1.0]，数值越大，高光越亮
        self.shiny = kwds.get('shiny')                  # 高光系数：值域范围[1, 3000]，数值越大，高光区域越小
        self.pellucid = kwds.get('pellucid')            # 透光系数：值域范围[0.0,1.0]，数值越大，反面越亮
        self.factor = kwds.get('factor')                # 反射衰减因子：值域范围[0.0,1.0]，仅用于球谐光照模型
        self.cpos = kwds.get('cpos')                    # 相机位置
        self.fixed = kwds.get('fixed', False)           # 使用固定的MVP矩阵

        self.texcoodr_type = None                       # 纹理坐标数据类型（attribute变量）
        self.sampler_type = None                        # 纹理采样器类型（uniform变量）
        self.texture_func = None                        # 纹理函数

        self.platform = sys.platform.lower()            # 操作系统
        self.glsl_version = '#version 330 core \n\n'    # 适配的GLSL版本
        self.glsl_functions = ''                        # 低版本GLSL的扩展函数

        if self.platform == 'darwin':
            self.glsl_version = ''
            self.glsl_functions = """
                mat4 inverse(mat4 m) {
                    float Coef00 = m[2][2] * m[3][3] - m[3][2] * m[2][3];
                    float Coef02 = m[1][2] * m[3][3] - m[3][2] * m[1][3];
                    float Coef03 = m[1][2] * m[2][3] - m[2][2] * m[1][3];
                       
                    float Coef04 = m[2][1] * m[3][3] - m[3][1] * m[2][3];
                    float Coef06 = m[1][1] * m[3][3] - m[3][1] * m[1][3];
                    float Coef07 = m[1][1] * m[2][3] - m[2][1] * m[1][3];
                       
                    float Coef08 = m[2][1] * m[3][2] - m[3][1] * m[2][2];
                    float Coef10 = m[1][1] * m[3][2] - m[3][1] * m[1][2];
                    float Coef11 = m[1][1] * m[2][2] - m[2][1] * m[1][2];
                       
                    float Coef12 = m[2][0] * m[3][3] - m[3][0] * m[2][3];
                    float Coef14 = m[1][0] * m[3][3] - m[3][0] * m[1][3];
                    float Coef15 = m[1][0] * m[2][3] - m[2][0] * m[1][3];
                       
                    float Coef16 = m[2][0] * m[3][2] - m[3][0] * m[2][2];
                    float Coef18 = m[1][0] * m[3][2] - m[3][0] * m[1][2];
                    float Coef19 = m[1][0] * m[2][2] - m[2][0] * m[1][2];
                       
                    float Coef20 = m[2][0] * m[3][1] - m[3][0] * m[2][1];
                    float Coef22 = m[1][0] * m[3][1] - m[3][0] * m[1][1];
                    float Coef23 = m[1][0] * m[2][1] - m[2][0] * m[1][1];
                       
                    const vec4 SignA = vec4( 1.0, -1.0,  1.0, -1.0);
                    const vec4 SignB = vec4(-1.0,  1.0, -1.0,  1.0);
                       
                    vec4 Fac0 = vec4(Coef00, Coef00, Coef02, Coef03);
                    vec4 Fac1 = vec4(Coef04, Coef04, Coef06, Coef07);
                    vec4 Fac2 = vec4(Coef08, Coef08, Coef10, Coef11);
                    vec4 Fac3 = vec4(Coef12, Coef12, Coef14, Coef15);
                    vec4 Fac4 = vec4(Coef16, Coef16, Coef18, Coef19);
                    vec4 Fac5 = vec4(Coef20, Coef20, Coef22, Coef23);
                       
                    vec4 Vec0 = vec4(m[1][0], m[0][0], m[0][0], m[0][0]);
                    vec4 Vec1 = vec4(m[1][1], m[0][1], m[0][1], m[0][1]);
                    vec4 Vec2 = vec4(m[1][2], m[0][2], m[0][2], m[0][2]);
                    vec4 Vec3 = vec4(m[1][3], m[0][3], m[0][3], m[0][3]);
                       
                    vec4 Inv0 = SignA * (Vec1 * Fac0 - Vec2 * Fac1 + Vec3 * Fac2);
                    vec4 Inv1 = SignB * (Vec0 * Fac0 - Vec2 * Fac3 + Vec3 * Fac4);
                    vec4 Inv2 = SignA * (Vec0 * Fac1 - Vec1 * Fac3 + Vec3 * Fac5);
                    vec4 Inv3 = SignB * (Vec0 * Fac2 - Vec1 * Fac4 + Vec2 * Fac5);
                       
                    mat4 Inverse = mat4(Inv0, Inv1, Inv2, Inv3);
                    vec4 Row0 = vec4(Inverse[0][0], Inverse[1][0], Inverse[2][0], Inverse[3][0]);
                    float Determinant = dot(m[0], Row0);
                    Inverse /= Determinant;
                       
                    return Inverse;
                }

                mat4 transpose(mat4 m) {
                    mat4 result = mat4(0.0);
                    for (int i=0; i<4; i++)
                        for (int j=0; j<4; j++)
                            result[i][j] = m[j][i];

                    return result;
                }
            """
 
    def _get_model(self, gltype, vs, **kwds):
        """返回模型对象"""
 
        indices = kwds.get('indices')
        color = kwds.get('color')
        normal = kwds.get('normal')
        texture = kwds.get('texture')
        texcoord = kwds.get('texcoord')
        align = kwds.get('align')
        tsize = kwds.get('tsize')
        psize = kwds.get('psize')
        vid = kwds.get('vid')
        cpos = kwds.get('cpos')
        lw = kwds.get('lw')
        ls = kwds.get('ls')

        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull')
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')

        if texture:
            if texture.ttype == GL_TEXTURE_1D:
                self.texcoodr_type = 'float'
                self.sampler_type = 'sampler1D'
                self.texture_func = 'texture1D'
            elif texture.ttype == GL_TEXTURE_2D:
                self.texcoodr_type = 'vec2'
                self.sampler_type = 'sampler2D'
                self.texture_func = 'texture2D'
            elif texture.ttype == GL_TEXTURE_2D_ARRAY:
                self.texcoodr_type = 'vec3'
                if self.platform == 'darwin':
                    self.sampler_type = 'sampler3D'
                    self.texture_func = 'texture3D'
                else:
                    self.sampler_type = 'sampler2DArray'
            elif texture.ttype == GL_TEXTURE_3D:
                self.texcoodr_type = 'vec3'
                self.sampler_type = 'sampler3D'
                self.texture_func = 'texture3D'

            if self.platform != 'darwin':
                self.texture_func = 'texture'

        vshader = self.get_vshader(texture)
        fshader = self.get_fshader(texture)
 
        m = Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
        m.set_vertex('a_Position', vs, indices)
        m.set_picked('u_Picked')

        if not color is None:
            m.set_color('a_Color', color)
        if not psize is None:
            m.set_psize('a_Psize', psize)
        if not normal is None:
            m.set_normal('a_Normal', normal)
        if not texcoord is None:
            m.set_texcoord('a_Texcoord', texcoord)
        if not texture is None:
            m.add_texture('u_Texture', texture)
        
        if not self.ambient is None:
            m.set_argument('u_AmbientColor', self.ambient)
        if not self.lamp is None:
            m.set_argument('u_LightPos', self.lamp)
        if not self.direction is None:
            m.set_argument('u_LightDir', self.direction)
        if not self.lightcolor is None:
            m.set_argument('u_LightColor', self.lightcolor)
        if not self.sky is None:
            m.set_argument('u_SkyColor', self.sky)
        if not self.ground is None:
            m.set_argument('u_GroundColor', self.ground)
        if not self.shiny is None:
            m.set_argument('u_Shiny', self.shiny)
        if not self.diffuse is None:
            m.set_argument('u_Diffuse', self.diffuse)
        if not self.specular is None:
            m.set_argument('u_Specular', self.specular)
        if not self.pellucid is None:
            m.set_argument('u_Pellucid', self.pellucid)
        if not self.factor is None:
            m.set_argument('u_ScaleFactor', self.factor)
        if not self.cpos is None:
            m.set_cam_pos('u_CamPos')
        if not lw is None or not ls is None:
            m.set_line_style(width=lw, stipple=ls)
        if not tsize is None:
            m.set_text_size('u_TextSize', tsize)
        if not align is None:
            m.set_argument('u_Align', align)
        if not vid is None:
            m.set_argument('a_VertexID', vid)
 
        m.set_cull_mode(cull)
        m.set_fill_mode(fill)
        m.set_slide(slide)

        if not self.fixed:
            m.set_proj_matrix('u_ProjMatrix')
            m.set_view_matrix('u_ViewMatrix')
            m.set_model_matrix('u_ModelMatrix', transform)

        return m

    def get_vshader(self, texture):
        """返回顶点着色器源码"""

        return ''

    def get_fshader(self, texture):
        """返回片元着色器源码"""
 
        return ''

class ScatterLight(_Light):
    """散列点专用的光照模型"""
 
    def __init__(self, ambient=(1.0,1.0,1.0)):
        """构造函数"""
 
        _Light.__init__(self, ambient=ambient)
 
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""

        kwds.update({'normal':None, 'texcoord':None})
        return self._get_model(gltype, vs, **kwds)
 
    def get_vshader(self, texture):
        """返回顶点着色器源码"""
 
        if texture is None:
            shader_src = self.glsl_version + """
                attribute vec4 a_Position;
                attribute vec4 a_Color;
                attribute float a_Psize;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                varying vec4 v_Color;
 
                void main() { 
                    v_Color = a_Color;
                    gl_PointSize = a_Psize;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position;
                }
            """
        else:
            shader_src = self.glsl_version + """
                attribute vec4 a_Position;
                attribute float a_Psize;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
 
                void main() { 
                    gl_PointSize = a_Psize;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position;
                }
            """

        return shader_src
 
    def get_fshader(self,texture):
        """返回片元着色器源码"""
 
        if self.platform == 'darwin':
            shader_src = self.glsl_version + """
                varying vec4 v_Color;
                uniform vec3 u_AmbientColor;
                uniform int u_Picked;
 
                void main() { 
                    vec3 rgb = v_Color.rgb * u_AmbientColor;
                    vec4 color = vec4(rgb, v_Color.a);
                    
                    if (u_Picked == 0)
                        gl_FragColor = color;
                    else
                        gl_FragColor = vec4(min(color.rgb*1.5, vec3(1.0)), color.a);
                } 
            """
        else:
            if texture is None:
                shader_src = self.glsl_version + """
                    varying vec4 v_Color;
                    uniform vec3 u_AmbientColor;
                    uniform int u_Picked;
 
                    void main() { 
                        vec2 temp = gl_PointCoord - vec2(0.5);
                        float f = dot(temp, temp);
 
                        if (f > 0.25)
                            discard;
 
                        vec3 rgb = v_Color.rgb * u_AmbientColor;
                        vec4 color = mix(vec4(rgb, v_Color.a), vec4(rgb, 0.0), smoothstep(0.2, 0.25, f));
                        
                        if (u_Picked == 0)
                            gl_FragColor = color;
                        else
                            gl_FragColor = vec4(min(color.rgb*1.5, vec3(1.0)), color.a);
                    } 
                """
            else:
                shader_src = self.glsl_version + """
                    uniform vec3 u_AmbientColor;
                    uniform sampler2D u_Texture;
                    uniform int u_Picked;
 
                    void main() { 
                        vec4 color = %s(u_Texture, gl_PointCoord);
                        vec3 rgb = color.rgb * u_AmbientColor;

                        if (u_Picked == 0)
                            gl_FragColor = vec4(rgb, color.a);
                        else
                            gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a);
                    } 
                """ % self.texture_func
        
        return shader_src

class Text2dLight(_Light):
    """2d文本专用的光照模型"""
 
    def __init__(self, ambient=(1.0,1.0,1.0)):
        """构造函数"""
 
        _Light.__init__(self, ambient=ambient)
 
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""

        kwds.update({'normal':None})
        return self._get_model(gltype, vs, **kwds)
 
    def get_vshader(self, texture):
        """返回2d文本的顶点着色器源码"""
 
        return self.glsl_version + """
            attribute vec4 a_Position;
            attribute vec2 a_Texcoord;
            attribute float a_VertexID;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            uniform vec2 u_TextSize;
            uniform int u_Align;
            varying vec2 v_Texcoord;
 
            void main() {
                v_Texcoord = a_Texcoord;
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
 
                if (u_Align == 0) {
                    if (a_VertexID == 1.0) {
                        gl_Position.y -= u_TextSize.y;
                    } else if (a_VertexID == 3.0) {
                        gl_Position.y -= u_TextSize.y;
                        gl_Position.x += u_TextSize.x;
                    } else if (a_VertexID == 2.0) {
                        gl_Position.x += u_TextSize.x;
                    }
                } else if (u_Align == 1) {
                    if (a_VertexID == 0.0) {
                        gl_Position.y += u_TextSize.y/2.0;
                    } else if (a_VertexID == 1.0) {
                        gl_Position.y -= u_TextSize.y/2.0;
                    } else if (a_VertexID == 3.0) {
                        gl_Position.x += u_TextSize.x;
                        gl_Position.y -= u_TextSize.y/2.0;
                    } else if (a_VertexID == 2.0) {
                        gl_Position.x += u_TextSize.x;
                        gl_Position.y += u_TextSize.y/2.0;
                    }
                } else if (u_Align == 2) {
                    if (a_VertexID == 0.0) {
                        gl_Position.y += u_TextSize.y;
                    } else if (a_VertexID == 3.0) {
                        gl_Position.x += u_TextSize.x;
                    } else if (a_VertexID == 2.0) {
                        gl_Position.x += u_TextSize.x;
                        gl_Position.y += u_TextSize.y;
                    }
                } else if (u_Align == 3) {
                    if (a_VertexID == 0.0) {
                        gl_Position.x -= u_TextSize.x/2.0;
                    } else if (a_VertexID == 1.0) {
                        gl_Position.x -= u_TextSize.x/2.0;
                        gl_Position.y -= u_TextSize.y;
                    } else if (a_VertexID == 3.0) {
                        gl_Position.x += u_TextSize.x/2.0;
                        gl_Position.y -= u_TextSize.y;
                    } else if (a_VertexID == 2.0) {
                        gl_Position.x += u_TextSize.x/2.0;
                    }
                } else if (u_Align == 4) {
                    if (a_VertexID == 0.0) {
                        gl_Position.x -= u_TextSize.x/2.0;
                        gl_Position.y += u_TextSize.y/2.0;
                    } else if (a_VertexID == 1.0) {
                        gl_Position.x -= u_TextSize.x/2.0;
                        gl_Position.y -= u_TextSize.y/2.0;
                    } else if (a_VertexID == 3.0) {
                        gl_Position.x += u_TextSize.x/2.0;
                        gl_Position.y -= u_TextSize.y/2.0;
                    } else if (a_VertexID == 2.0) {
                        gl_Position.x += u_TextSize.x/2.0;
                        gl_Position.y += u_TextSize.y/2.0;
                    }
                } else if (u_Align == 5) {
                    if (a_VertexID == 0.0) {
                        gl_Position.x -= u_TextSize.x/2.0;
                        gl_Position.y += u_TextSize.y;
                    } else if (a_VertexID == 1.0) {
                        gl_Position.x -= u_TextSize.x/2.0;
                    } else if (a_VertexID == 3.0) {
                        gl_Position.x += u_TextSize.x/2.0;
                    } else if (a_VertexID == 2.0) {
                        gl_Position.x += u_TextSize.x/2.0;
                        gl_Position.y += u_TextSize.y;
                    }
                } else if (u_Align == 6) {
                    if (a_VertexID == 0.0) {
                        gl_Position.x -= u_TextSize.x;
                    } else if (a_VertexID == 1.0) {
                        gl_Position.x -= u_TextSize.x;
                        gl_Position.y -= u_TextSize.y;
                    } else if (a_VertexID == 3.0) {
                        gl_Position.y -= u_TextSize.y;
                    }
                } else if (u_Align == 7) {
                    if (a_VertexID == 0.0) {
                        gl_Position.x -= u_TextSize.x;
                        gl_Position.y += u_TextSize.y/2.0;
                    } else if (a_VertexID == 1.0) {
                        gl_Position.x -= u_TextSize.x;
                        gl_Position.y -= u_TextSize.y/2.0;
                    } else if (a_VertexID == 3.0) {
                        gl_Position.y -= u_TextSize.y/2.0;
                    } else if (a_VertexID == 2.0) {
                        gl_Position.y += u_TextSize.y/2.0;
                    }
                } else {
                    if (a_VertexID == 0.0) {
                        gl_Position.x -= u_TextSize.x;
                        gl_Position.y += u_TextSize.y;
                    } else if (a_VertexID == 1.0) {
                        gl_Position.x -= u_TextSize.x;
                    } else if (a_VertexID == 2.0) {
                        gl_Position.y += u_TextSize.y;
                    }
                }
            }
        """
 
    def get_fshader(self, texture):
        """返回片元着色器源码"""
 
        return self.glsl_version + """
            varying vec2 v_Texcoord;
            uniform vec3 u_AmbientColor;
            uniform sampler2D u_Texture;
            uniform int u_Picked;
 
            void main() { 
                vec4 color = %s(u_Texture, v_Texcoord);
                vec3 rgb = color.rgb * u_AmbientColor;

                if (u_Picked == 0)
                    gl_FragColor = vec4(rgb, color.a);
                else
                    gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a);
            } 
        """ % self.texture_func

class BaseLight(_Light):
    """环境光照模型"""
 
    def __init__(self, ambient=(1.0,1.0,1.0), fixed=False):
        """构造函数"""
 
        _Light.__init__(self, ambient=ambient, fixed=fixed)
 
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""

        kwds.update({'normal':None})
        return self._get_model(gltype, vs, **kwds)
 
    def get_vshader(self, texture):
        """返回顶点着色器源码"""
 
        if self.fixed:
            if texture is None:
                shader_src = self.glsl_version + """
                    attribute vec4 a_Position;
                    attribute vec4 a_Color;
                    varying vec4 v_Color;
 
                    void main() { 
                        v_Color = a_Color;
                        gl_Position = a_Position; 
                    }
                """
            else:
                shader_src = self.glsl_version + """
                    attribute vec4 a_Position;
                    attribute %s a_Texcoord;
                    varying %s v_Texcoord;
 
                    void main() { 
                        v_Texcoord = a_Texcoord;
                        gl_Position = a_Position; 
                    }
                """ % (self.texcoodr_type, self.texcoodr_type)
        else:
            if texture is None:
                shader_src = self.glsl_version + """
                    attribute vec4 a_Position;
                    attribute vec4 a_Color;
                    uniform mat4 u_ProjMatrix;
                    uniform mat4 u_ViewMatrix;
                    uniform mat4 u_ModelMatrix;
                    varying vec4 v_Color;
 
                    void main() { 
                        v_Color = a_Color;
                        gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                    }
                """
            else:
                shader_src = self.glsl_version + """
                    attribute vec4 a_Position;
                    attribute %s a_Texcoord;
                    uniform mat4 u_ProjMatrix;
                    uniform mat4 u_ViewMatrix;
                    uniform mat4 u_ModelMatrix;
                    varying %s v_Texcoord;
 
                    void main() { 
                        v_Texcoord = a_Texcoord;
                        gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                    }
                """ % (self.texcoodr_type, self.texcoodr_type)
 
        return shader_src
 
    def get_fshader(self, texture):
        """返回片元着色器源码"""
 
        if texture is None:
            shader_src = self.glsl_version + """
                varying vec4 v_Color;
                uniform vec3 u_AmbientColor;
                uniform int u_Picked;
 
                void main() { 
                    vec3 rgb = v_Color.rgb * u_AmbientColor;
                    if (u_Picked == 0)
                        gl_FragColor = vec4(rgb, v_Color.a);
                    else
                        gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), v_Color.a);
                } 
            """
        else:
            shader_src = self.glsl_version + """
                varying %s v_Texcoord;
                uniform vec3 u_AmbientColor;
                uniform %s u_Texture;
                uniform int u_Picked;
 
                void main() { 
                    vec4 color = %s(u_Texture, v_Texcoord);
                    vec3 rgb = color.rgb * u_AmbientColor;
                    
                    if (u_Picked == 0)
                        gl_FragColor = vec4(rgb, color.a);
                    else
                        gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a);
                } 
            """ % (self.texcoodr_type, self.sampler_type, self.texture_func)
 
        return shader_src

class SunLight(_Light):
    """平行光照模型"""

    def __init__(self, direction=(0.0,0.0,-1.0), lightcolor=(1.0,1.0,1.0), ambient=(0.3,0.3,0.3), **kwds):
        """构造函数"""

        _Light.__init__(self, 
            ambient     = ambient,                      # 环境光
            direction   = direction,                    # 光的方向
            lightcolor  = lightcolor,                   # 光的颜色
            diffuse     = kwds.get('diffuse', 0.8),     # 漫反射系数：值域范围[0.0, 1.0]，数值越大，表面越亮
            specular    = kwds.get('specular', 0.6),    # 镜面反射系数：值域范围[0.0, 1.0]，数值越大，高光越亮
            shiny       = kwds.get('shiny', 50),        # 高光系数：值域范围[1, 3000]，数值越大，高光区域越小
            pellucid    = kwds.get('pellucid', 0.5),    # 透光系数：值域范围[0.0,1.0]，数值越大，反面越亮
            cpos        = True                          # 着色器需要传入相机位置
        )
 
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""

        return self._get_model(gltype, vs, **kwds)
 
    def get_vshader(self, texture):
        """返回顶点着色器源码"""
 
        if texture is None:
            shader_src =  self.glsl_version + """
                attribute vec4 a_Position;
                attribute vec3 a_Normal;
                attribute vec4 a_Color;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_CamPos;
                uniform vec3 u_LightDir; // 定向光方向
                varying vec4 v_Color;
                varying vec3 v_Normal;
                varying vec3 v_LightDir;
                varying vec3 v_MiddleDir;

                """ + self.glsl_functions + """

                void main() { 
                    v_Color = a_Color;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
 
                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix)); // 法向量矩阵
                    v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0))); // 重新计算模型变换后的法向量
                    vec3 camDir = normalize(u_CamPos - vec3(u_ModelMatrix * a_Position)); // 从当前顶点指向相机的向量
                    v_LightDir = normalize(-u_LightDir); // 光线向量取反后单位化
                    v_MiddleDir = normalize(camDir + v_LightDir); // 视线和光线的中间向量
                }
            """
        else:
            shader_src = self.glsl_version + """
                attribute vec4 a_Position;
                attribute vec3 a_Normal;
                attribute %s a_Texcoord;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_CamPos;
                uniform vec3 u_LightDir; // 定向光方向
                varying %s v_Texcoord;
                varying vec3 v_Normal;
                varying vec3 v_LightDir;
                varying vec3 v_MiddleDir;
 
                """ % (self.texcoodr_type, self.texcoodr_type) + self.glsl_functions + """

                void main() { 
                    v_Texcoord = a_Texcoord;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
 
                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix)); // 法向量矩阵
                    v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0))); // 重新计算模型变换后的法向量
                    vec3 camDir = normalize(u_CamPos - vec3(u_ModelMatrix * a_Position)); // 从当前顶点指向相机的向量
                    v_LightDir = normalize(-u_LightDir); // 光线向量取反后单位化
                    v_MiddleDir = normalize(camDir + v_LightDir); // 视线和光线的中间向量
                }
            """

        return shader_src
 
    def get_fshader(self, texture):
        """返回片元着色器源码"""
 
        if texture is None:
            shader_src = self.glsl_version + """
                varying vec4 v_Color;
                varying vec3 v_Normal;
                varying vec3 v_LightDir;
                varying vec3 v_MiddleDir;
                uniform vec3 u_LightColor; // 定向光颜色
                uniform vec3 u_AmbientColor; // 环境光颜色
                uniform float u_Shiny; // 高光系数
                uniform float u_Specular; // 镜面反射系数
                uniform float u_Diffuse; // 漫反射系数
                uniform float u_Pellucid; // 透光系数
                uniform int u_Picked;
 
                void main() { 
                    float diffuseCos = u_Diffuse * max(0.0, dot(v_LightDir, v_Normal)); // 光线向量和法向量的内积
                    float specularCos = u_Specular * max(0.0, dot(v_MiddleDir, v_Normal)); // 中间向量和法向量内积
 
                    if (!gl_FrontFacing) 
                        diffuseCos *= u_Pellucid; // 背面受透光系数影响
 
                    if (diffuseCos == 0.0) 
                        specularCos = 0.0;
                    else
                        specularCos = pow(specularCos, u_Shiny);
 
                    vec3 scatteredLight = min(u_AmbientColor + u_LightColor * diffuseCos, vec3(1.0)); // 散射光
                    vec3 reflectedLight = u_LightColor * specularCos; // 反射光
                    vec3 rgb = min(v_Color.rgb * (scatteredLight + reflectedLight), vec3(1.0));
 
                    if (u_Picked == 0)
                        gl_FragColor = vec4(rgb, v_Color.a);
                    else
                        gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), v_Color.a);
                }
            """
        else:
            shader_src = self.glsl_version + """
                varying %s v_Texcoord;
                varying vec3 v_Normal;
                varying vec3 v_LightDir;
                varying vec3 v_MiddleDir;
                uniform %s u_Texture;
                uniform vec3 u_LightColor; // 定向光颜色
                uniform vec3 u_AmbientColor; // 环境光颜色
                uniform float u_Shiny; // 高光系数
                uniform float u_Specular; // 镜面反射系数
                uniform float u_Diffuse; // 漫反射系数
                uniform float u_Pellucid; // 透光系数
                uniform int u_Picked;
 
                void main() { 
                    vec4 color = %s(u_Texture, v_Texcoord);
                    float diffuseCos = u_Diffuse * max(0.0, dot(v_LightDir, v_Normal)); // 光线向量和法向量的内积
                    float specularCos = u_Specular * max(0.0, dot(v_MiddleDir, v_Normal)); // 中间向量和法向量内积
 
                    if (!gl_FrontFacing) 
                        diffuseCos *= u_Pellucid; // 背面受透光系数影响
 
                    if (diffuseCos == 0.0) 
                        specularCos = 0.0;
                    else
                        specularCos = pow(specularCos, u_Shiny);
 
                    vec3 scatteredLight = min(u_AmbientColor + u_LightColor * diffuseCos, vec3(1.0)); // 散射光
                    vec3 reflectedLight = u_LightColor * specularCos; // 反射光
                    vec3 rgb = min(color.rgb * (scatteredLight + reflectedLight), vec3(1.0));
 
                    if (u_Picked == 0)
                        gl_FragColor = vec4(rgb, color.a);
                    else
                        gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a);
                } 
            """ % (self.texcoodr_type, self.sampler_type, self.texture_func)

        return shader_src

class LampLight(_Light):
    """定位光照模型"""

    def __init__(self, lamp=(0.0,0.0,2.0), lightcolor=(1.0,1.0,1.0), ambient=(0.5,0.5,0.5), **kwds):
        """构造函数"""

        _Light.__init__(self, 
            ambient     = ambient,                      # 环境光
            lamp        = lamp,                         # 光源位置
            lightcolor  = lightcolor,                   # 光的颜色
            diffuse     = kwds.get('diffuse', 0.8),     # 漫反射系数：值域范围[0.0, 1.0]，数值越大，表面越亮
            specular    = kwds.get('specular', 0.6),    # 镜面反射系数：值域范围[0.0, 1.0]，数值越大，高光越亮
            shiny       = kwds.get('shiny', 50),        # 高光系数：值域范围[1, 3000]，数值越大，高光区域越小
            pellucid    = kwds.get('pellucid', 0.5),    # 透光系数：值域范围[0.0,1.0]，数值越大，反面越亮
            cpos        = True                          # 着色器需要传入相机位置
        )

    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""

        return self._get_model(gltype, vs, **kwds)
 
    def get_vshader(self, texture):
        """返回顶点着色器源码"""
 
        if texture is None:
            shader_src =  self.glsl_version + """
                attribute vec4 a_Position;
                attribute vec3 a_Normal;
                attribute vec4 a_Color;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_CamPos;
                uniform vec3 u_LightPos;
                varying vec4 v_Color;
                varying vec3 v_Normal;
                varying vec3 v_LightDir;
                varying vec3 v_MiddleDir;
 
                """ + self.glsl_functions + """

                void main() { 
                    v_Color = a_Color;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
 
                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix)); // 法向量矩阵
                    v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0))); // 重新计算模型变换后的法向量
                    
                    vec3 camDir = normalize(u_CamPos - vec3(u_ModelMatrix * a_Position)); // 从当前顶点指向相机的向量
                    v_LightDir = normalize(u_LightPos - a_Position.xyz); // 光线向量单位化
                    v_MiddleDir = normalize(camDir + v_LightDir); // 视线和光线的中间向量
                }
            """
        else:
            shader_src = self.glsl_version + """
                attribute vec4 a_Position;
                attribute vec3 a_Normal;
                attribute %s a_Texcoord;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_CamPos;
                uniform vec3 u_LightPos;
                varying %s v_Texcoord;
                varying vec3 v_Normal;
                varying vec3 v_LightDir;
                varying vec3 v_MiddleDir;
 
                """ % (self.texcoodr_type, self.texcoodr_type) + self.glsl_functions + """

                void main() { 
                    v_Texcoord = a_Texcoord;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
 
                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix)); // 法向量矩阵
                    v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0))); // 重新计算模型变换后的法向量
                    
                    vec3 camDir = normalize(u_CamPos - vec3(u_ModelMatrix * a_Position)); // 从当前顶点指向相机的向量
                    v_LightDir = normalize(u_LightPos - a_Position.xyz); // 光线向量单位化
                    v_MiddleDir = normalize(camDir + v_LightDir); // 视线和光线的中间向量
                }
            """

        return shader_src
 
    def get_fshader(self, texture):
        """返回片元着色器源码"""
 
        if texture is None:
            shader_src = self.glsl_version + """
                varying vec4 v_Color;
                varying vec3 v_Normal;
                varying vec3 v_LightDir;
                varying vec3 v_MiddleDir;
                uniform vec3 u_LightColor; // 灯光颜色
                uniform vec3 u_AmbientColor; // 环境光颜色
                uniform float u_Shiny; // 高光系数
                uniform float u_Specular; // 镜面反射系数
                uniform float u_Diffuse; // 漫反射系数
                uniform float u_Pellucid; // 透光系数
                uniform int u_Picked;
 
                void main() { 
                    float diffuseCos = u_Diffuse * max(0.0, dot(v_LightDir, v_Normal)); // 光线向量和法向量的内积
                    float specularCos = u_Specular * max(0.0, dot(v_MiddleDir, v_Normal)); // 中间向量和法向量内积
 
                    if (!gl_FrontFacing) 
                        diffuseCos *= u_Pellucid; // 背面受透光系数影响
 
                    if (diffuseCos == 0.0) 
                        specularCos = 0.0;
                    else
                        specularCos = pow(specularCos, u_Shiny);
 
                    vec3 scatteredLight = min(u_AmbientColor + u_LightColor * diffuseCos, vec3(1.0)); // 散射光
                    vec3 reflectedLight = u_LightColor * specularCos; // 反射光
                    vec3 rgb = min(v_Color.rgb * (scatteredLight + reflectedLight), vec3(1.0));
 
                    if (u_Picked == 0)
                        gl_FragColor = vec4(rgb, v_Color.a);
                    else
                        gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), v_Color.a);
                }
            """
        else:
            shader_src = self.glsl_version + """
                varying %s v_Texcoord;
                varying vec3 v_Normal;
                varying vec3 v_LightDir;
                varying vec3 v_MiddleDir;
                uniform %s u_Texture;
                uniform vec3 u_LightColor; // 灯光颜色
                uniform vec3 u_AmbientColor; // 环境光颜色
                uniform float u_Shiny; // 高光系数
                uniform float u_Specular; // 镜面反射系数
                uniform float u_Diffuse; // 漫反射系数
                uniform float u_Pellucid; // 透光系数
                uniform int u_Picked;
 
                void main() { 
                    vec4 color = %s(u_Texture, v_Texcoord);
                    float diffuseCos = u_Diffuse * max(0.0, dot(v_LightDir, v_Normal)); // 光线向量和法向量的内积
                    float specularCos = u_Specular * max(0.0, dot(v_MiddleDir, v_Normal)); // 中间向量和法向量内积
 
                    if (!gl_FrontFacing) 
                        diffuseCos *= u_Pellucid; // 背面受透光系数影响
 
                    if (diffuseCos == 0.0) 
                        specularCos = 0.0;
                    else
                        specularCos = pow(specularCos, u_Shiny);
 
                    vec3 scatteredLight = min(u_AmbientColor + u_LightColor * diffuseCos, vec3(1.0)); // 散射光
                    vec3 reflectedLight = u_LightColor * specularCos; // 反射光
                    vec3 rgb = min(color.rgb * (scatteredLight + reflectedLight), vec3(1.0));
 
                    if (u_Picked == 0)
                        gl_FragColor = vec4(rgb, color.a);
                    else
                        gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a);
                } 
            """ % (self.texcoodr_type, self.sampler_type, self.texture_func)

        return shader_src

class SkyLight(_Light):
    """户外光照模型"""

    def __init__(self, direction=(0.0,-1.0,0.0), sky=(1.0,1.0,1.0), ground=(0.3,0.3,0.3)):
        """构造函数"""

        _Light.__init__(self, 
            direction   = direction,                    # 光的方向
            sky         = sky,                          # 来自天空的环境光
            ground      = ground,                       # 来自地面的环境光
        )
 
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""

        return self._get_model(gltype, vs, **kwds)
 
    def get_vshader(self, texture):
        """返回使用颜色的顶点着色器源码"""
 
        if texture is None:
            return self.glsl_version + """
                attribute vec4 a_Position;
                attribute vec3 a_Normal;
                attribute vec4 a_Color;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_LightDir; // 定向光方向
                varying vec4 v_Color;
                varying float v_Costheta;
 
                """ + self.glsl_functions + """

                void main() { 
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                    v_Color = a_Color;
 
                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                    vec3 normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
                    v_Costheta = dot(normal, normalize(-u_LightDir)) * 0.5 + 0.5;
                }
            """
        else:
            return self.glsl_version + """
                attribute vec4 a_Position;
                attribute vec3 a_Normal;
                attribute %s a_Texcoord;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_LightDir; // 定向光方向
                varying %s v_Texcoord;
                varying float v_Costheta;
 
                """ % (self.texcoodr_type, self.texcoodr_type) + self.glsl_functions + """

                void main() { 
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                    v_Texcoord = a_Texcoord;
 
                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                    vec3 normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
                    v_Costheta = dot(normal, normalize(-u_LightDir)) * 0.5 + 0.5;
                }
            """
 
    def get_fshader(self, texture):
        """返回使用颜色的片元着色器源码"""
 
        if texture is None:
            return self.glsl_version + """
                varying vec4 v_Color;
                varying float v_Costheta;
                uniform vec3 u_SkyColor; // 天空光线颜色
                uniform vec3 u_GroundColor; // 地面光线颜色
                uniform int u_Picked;
 
                void main() { 
                    float costheta = v_Costheta;
                    if (!gl_FrontFacing) 
                        costheta *= 0.5;
 
                    vec3 rgb = mix(u_GroundColor, u_SkyColor, costheta) * v_Color.rgb;
                    if (u_Picked == 0)
                        gl_FragColor = vec4(rgb, v_Color.a); 
                    else
                        gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), v_Color.a); 
                } 
            """
        else:
            return self.glsl_version + """
                varying %s v_Texcoord;
                varying float v_Costheta;
                uniform %s u_Texture;
                uniform vec3 u_SkyColor; // 天空光线颜色
                uniform vec3 u_GroundColor; // 地面光线颜色
                uniform int u_Picked;
 
                void main() { 
                    vec4 color = %s(u_Texture, v_Texcoord);
                    float costheta = v_Costheta;
                    if (!gl_FrontFacing) 
                        costheta *= 0.5;

                    vec3 rgb = mix(u_GroundColor, u_SkyColor, costheta) * color.rgb;
                    if (u_Picked == 0)
                        gl_FragColor = vec4(rgb, color.a); 
                    else
                        gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a); 
                } 
            """ % (self.texcoodr_type, self.sampler_type, self.texture_func)
 
class SphereLight(_Light):
    """球谐光照模型"""

    def __init__(self, factor=0.8, style=0):
        """构造函数"""
 
        _Light.__init__(self)

        self.factor = factor # 反射衰减因子
        self.parameter = [
            # 0. Old Town square 
            """
            const vec3 L00 = vec3(0.871297, 0.875255, 0.864470);
            const vec3 L1m1 = vec3(0.175058, 0.245335, 0.312891);
            const vec3 L10 = vec3(0.034675, 0.036107, 0.037362);
            const vec3 L11 = vec3(-0.004629, -0.029448, -0.048028);
            const vec3 L2m1 = vec3(0.003242, 0.003624, 0.007511);
            const vec3 L2m2 = vec3(-0.120535, -0.121160, -0.117507);
            const vec3 L20 = vec3(-0.028667, -0.024926, -0.020998);
            const vec3 L21 = vec3(-0.077539, -0.086325, -0.091591);
            const vec3 L22 = vec3(-0.161784, -0.191783, -0.219152);
            """,
 
            # 1. Grace cathedral
            """
            const vec3 L00 = vec3(0.79, 0.44, 0.54);
            const vec3 L1m1 = vec3(0.39, 0.35, 0.60);
            const vec3 L10 = vec3(-0.34, -0.18, -0.27);
            const vec3 L11 = vec3(-0.29, -0.06, 0.01);
            const vec3 L2m1 = vec3(-0.26, -0.22, -0.47);
            const vec3 L2m2 = vec3(-0.11, -0.05, -0.12);
            const vec3 L20 = vec3(-0.16, -0.09, -0.15);
            const vec3 L21 = vec3(0.56, 0.21, 0.14);
            const vec3 L22 = vec3(0.21, -0.05, -0.30);
            """,

            # 2. Eucalyptus grove
            """
            const vec3 L00 = vec3(0.38, 0.43, 0.45);
            const vec3 L1m1 = vec3(0.29, 0.36, 0.41);
            const vec3 L10 = vec3(0.04, 0.03, 0.01);
            const vec3 L11 = vec3(-0.10, -0.10, -0.09);
            const vec3 L2m1 = vec3(0.01, -0.01, -0.05);
            const vec3 L2m2 = vec3(-0.06, -0.06, -0.04);
            const vec3 L20 = vec3(-0.09, -0.13, -0.15);
            const vec3 L21 = vec3(-0.06, -0.05, -0.04);
            const vec3 L22 = vec3(0.02, 0.0, -0.05);
            """,
 
            # 3. St. Peter's basilica
            """
            const vec3 L00 = vec3(0.36, 0.26, 0.23);
            const vec3 L1m1 = vec3(0.18, 0.14, 0.13);
            const vec3 L10 = vec3(-0.02, -0.01, 0.0);
            const vec3 L11 = vec3(0.03, 0.02, 0.0);
            const vec3 L2m1 = vec3(-0.05, -0.03, -0.01);
            const vec3 L2m2 = vec3(0.02, 0.01, 0.0);
            const vec3 L20 = vec3(-0.09, -0.08, -0.07);
            const vec3 L21 = vec3(0.01, 0.0, 0.0);
            const vec3 L22 = vec3(-0.08, -0.03, 0.0);
            """,
 
            # 4. Uffizi gallery
            """
            const vec3 L00 = vec3(0.32, 0.31, 0.35);
            const vec3 L1m1 = vec3(0.37, 0.37, 0.43);
            const vec3 L10 = vec3(0.0, 0.0, 0.0);
            const vec3 L11 = vec3(-0.01, -0.01, -0.01);
            const vec3 L2m1 = vec3(-0.01, -0.01, -0.01);
            const vec3 L2m2 = vec3(-0.02, -0.02, -0.03);
            const vec3 L20 = vec3(-0.28, -0.28, -0.32);
            const vec3 L21 = vec3(0.0, 0.0, 0.0);
            const vec3 L22 = vec3(-0.24, -0.24, -0.28);
            """,
 
            # 5. Galileo's tomb
            """
            const vec3 L00 = vec3(1.04, 0.76, 0.71);
            const vec3 L1m1 = vec3(0.44, 0.34, 0.34);
            const vec3 L10 = vec3(-0.22, -0.18, -0.17);
            const vec3 L11 = vec3(0.71, 0.54, 0.56);
            const vec3 L2m1 = vec3(-0.12, -0.09, -0.08);
            const vec3 L2m2 = vec3(0.64, 0.50, 0.52);
            const vec3 L20 = vec3(-0.37, -0.28, -0.29);
            const vec3 L21 = vec3(-0.17, -0.13, -0.13);
            const vec3 L22 = vec3(0.55, 0.42, 0.42);
            """,
 
            # 6. Vine street kitchen
            """
            const vec3 L00 = vec3(0.64, 0.67, 0.73);
            const vec3 L1m1 = vec3(0.28, 0.32, 0.33);
            const vec3 L10 = vec3(0.42, 0.60, 0.77);
            const vec3 L11 = vec3(-0.05, -0.04, -0.02);
            const vec3 L2m1 = vec3(0.25, 0.39, 0.53);
            const vec3 L2m2 = vec3(-0.10, -0.08, -0.05);
            const vec3 L20 = vec3(0.38, 0.54, 0.71);
            const vec3 L21 = vec3(0.06, 0.01, -0.02);
            const vec3 L22 = vec3(-0.03, -0.02, -0.03);
            """,
 
            # 7. Breezeway
            """
            const vec3 L00 = vec3(0.32, 0.36, 0.38);
            const vec3 L1m1 = vec3(0.37, 0.41, 0.45);
            const vec3 L10 = vec3(-0.01, -0.01, -0.01);
            const vec3 L11 = vec3(-0.10, -0.12, -0.12);
            const vec3 L2m1 = vec3(-0.01, -0.02, 0.02);
            const vec3 L2m2 = vec3(-0.13, -0.15, -0.17);
            const vec3 L20 = vec3(-0.07, -0.08, -0.09);
            const vec3 L21 = vec3(0.02, 0.03, 0.03);
            const vec3 L22 = vec3(-0.29, -0.32, -0.36);
            """,
 
            # 8. Campus sunset
            """
            const vec3 L00 = vec3(0.79, 0.94, 0.98);
            const vec3 L1m1 = vec3(0.44, 0.56, 0.70);
            const vec3 L10 = vec3(-0.10, -0.18, -0.27);
            const vec3 L11 = vec3(0.45, 0.38, 0.20);
            const vec3 L2m1 = vec3(-0.14, -0.22, -0.31);
            const vec3 L2m2 = vec3(0.18, 0.14, 0.05);
            const vec3 L20 = vec3(-0.39, -0.40, -0.36);
            const vec3 L21 = vec3(0.09, 0.07, 0.04);
            const vec3 L22 = vec3(0.67, 0.67, 0.52);
            """,
 
            # 9. Funston Beach sunset
            """
            const vec3 L00 = vec3(0.68, 0.69, 0.70);
            const vec3 L1m1 = vec3(0.32, 0.37, 0.44);
            const vec3 L10 = vec3(-0.17, -0.17, -0.17);
            const vec3 L11 = vec3(-0.45, -0.42, -0.34);
            const vec3 L2m1 = vec3(-0.08, -0.09, -0.10);
            const vec3 L2m2 = vec3(-0.17, -0.17, -0.15);
            const vec3 L20 = vec3(-0.03, -0.02, -0.01);
            const vec3 L21 = vec3(0.16, 0.14, 0.10);
            const vec3 L22 = vec3(0.37, 0.31, 0.20);
            """
        ][style]
 
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""

        return self._get_model(gltype, vs, **kwds)
 
    def get_vshader(self, texture):
        """返回使用颜色的顶点着色器源码"""
 
        if texture is None:
            return self.glsl_version + """
                attribute vec4 a_Position;
                attribute vec3 a_Normal;
                attribute vec4 a_Color;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                varying vec4 v_Color;
                varying vec3 v_Normal;
 
                """ + self.glsl_functions + """

                void main() { 
                    v_Color = a_Color;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position;

                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                    v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
                }
            """
        else:
            return self.glsl_version + """
                attribute vec4 a_Position;
                attribute vec3 a_Normal;
                attribute %s a_Texcoord;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                varying %s v_Texcoord;
                varying vec3 v_Normal;
 
                """ % (self.texcoodr_type, self.texcoodr_type) + self.glsl_functions + """

                void main() { 
                    v_Texcoord = a_Texcoord;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position;

                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                    v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
                }
            """
 
    def get_fshader(self, texture):
        """返回使用颜色的片元着色器源码"""
 
        if texture is None:
            return self.glsl_version + """
                varying vec4 v_Color;
                varying vec3 v_Normal;
                const float C1 = 0.429043;
                const float C2 = 0.511664;
                const float C3 = 0.743125;
                const float C4 = 0.886227;
                const float C5 = 0.247708;
                %s
                uniform float u_ScaleFactor;
                uniform int u_Picked;
 
                void main() { 
                    vec3 diffuse = C1 * L22 * (v_Normal.x * v_Normal.x - v_Normal.y * v_Normal.y)
                            + C3 * L20 * v_Normal.z * v_Normal.z
                            + C4 * L00
                            - C5 * L20
                            + 2.0 * C1 * L2m2 * v_Normal.x * v_Normal.y
                            + 2.0 * C1 * L21 * v_Normal.x * v_Normal.z
                            + 2.0 * C1 * L2m1 * v_Normal.y * v_Normal.z
                            + 2.0 * C2 * L11 * v_Normal.x
                            + 2.0 * C2 * L1m1 * v_Normal.y
                            + 2.0 * C2 * L10 * v_Normal.z;
 
                    diffuse *= u_ScaleFactor;
                    vec3 rgb = v_Color.rgb * diffuse;

                    if (u_Picked == 0)
                        gl_FragColor = vec4(rgb, v_Color.a); 
                    else
                        gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), v_Color.a); 
                } 
            """ % self.parameter
        else: 
            return self.glsl_version + """
                varying %s v_Texcoord;
                varying vec3 v_Normal;
                const float C1 = 0.429043;
                const float C2 = 0.511664;
                const float C3 = 0.743125;
                const float C4 = 0.886227;
                const float C5 = 0.247708;
                %s
                uniform %s u_Texture;
                uniform float u_ScaleFactor;
                uniform int u_Picked;
 
                void main() { 
                    vec3 diffuse = C1 * L22 * (v_Normal.x * v_Normal.x - v_Normal.y * v_Normal.y)
                            + C3 * L20 * v_Normal.z * v_Normal.z
                            + C4 * L00
                            - C5 * L20
                            + 2.0 * C1 * L2m2 * v_Normal.x * v_Normal.y
                            + 2.0 * C1 * L21 * v_Normal.x * v_Normal.z
                            + 2.0 * C1 * L2m1 * v_Normal.y * v_Normal.z
                            + 2.0 * C2 * L11 * v_Normal.x
                            + 2.0 * C2 * L1m1 * v_Normal.y
                            + 2.0 * C2 * L10 * v_Normal.z;
 
                    diffuse *= u_ScaleFactor;
                    vec4 color = %s(u_Texture, v_Texcoord);
                    vec3 rgb = color.rgb * diffuse;

                    if (u_Picked == 0)
                        gl_FragColor = vec4(rgb, color.a); 
                    else
                        gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a); 
                } 
            """ % (self.texcoodr_type, self.parameter, self.sampler_type, self.texture_func)
        
