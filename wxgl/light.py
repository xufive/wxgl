#!/usr/bin/env python3

import numpy as np
from OpenGL.GL import *
from . model import Model

class _Light:
    """光照模式基类"""
 
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

        self.a_dtype = None                             # 纹理坐标数据类型（attribute变量）
        self.u_dtype = None                             # 纹理采样器类型（uniform变量）
 
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""
 
        indices = kwds.get('indices')
        color = kwds.get('color')
        normal = kwds.get('normal')
        texture = kwds.get('texture')
        texcoord = kwds.get('texcoord')
        align = kwds.get('align')
        tsize = kwds.get('tsize')
        psize = kwds.get('psize')
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
                self.a_dtype = 'float'
                self.u_dtype = 'sampler1D'
            elif texture.ttype == GL_TEXTURE_2D:
                self.a_dtype = 'vec2'
                self.u_dtype = 'sampler2D'
            elif texture.ttype == GL_TEXTURE_2D_ARRAY:
                self.a_dtype = 'vec3'
                slef.u_dtype = 'sampler2DArray'
            elif texture.ttype == GL_TEXTURE_3D:
                self.a_dtype = 'vec3'
                self.u_dtype = 'sampler3D'

        vshader = self.get_vshader(texture)
        fshader = self.get_fshader(texture)
 
        m = Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
        m.set_vertex('a_Position', vs, indices)
        m.set_proj_matrix('u_ProjMatrix')
        m.set_view_matrix('u_ViewMatrix')
        m.set_model_matrix('u_ModelMatrix', transform)
        m.set_cull_mode(cull)
        m.set_fill_mode(fill)
        m.set_slide(slide)

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
 
        return m.verify()
 
    def get_vshader(self, texture):
        """返回顶点着色器源码"""
 
        pass
 
    def get_fshader(self, texture):
        """返回片元着色器源码"""
 
        pass

class ScatterLight(_Light):
    """适用于散列点的环境光照情景模式"""
 
    def __init__(self, ambient=(1.0,1.0,1.0)):
        """构造函数"""
 
        _Light.__init__(self, ambient=ambient)
 
    def get_vshader(self, texure):
        """返回顶点着色器源码"""
 
        return """
            #version 330 core
 
            in vec4 a_Position;
            in vec4 a_Color;
            in float a_Psize;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            out vec4 v_Color;
 
            void main() { 
                v_Color = a_Color;
                gl_PointSize = a_Psize;
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position;
            }
        """
 
    def get_fshader(self,texture):
        """返回片元着色器源码"""
 
        return """
            #version 330 core
 
            in vec4 v_Color;
            uniform vec3 u_AmbientColor;
 
            void main() { 
                vec2 temp = gl_PointCoord - vec2(0.5);
                float f = dot(temp, temp);
 
                if (f > 0.25)
                    discard;
 
                vec3 rgb = v_Color.rgb * u_AmbientColor;
                vec4 color = mix(vec4(rgb, v_Color.a), vec4(rgb, 0.0), smoothstep(0.2, 0.25, f));
                
                gl_FragColor = color;
            } 
        """

class Text2dLight(_Light):
    """适用于2d文本的环境光照情景模式"""
 
    def __init__(self, ambient=(1.0,1.0,1.0)):
        """构造函数"""
 
        _Light.__init__(self, ambient=ambient)
 
    def get_vshader(self, texture):
        """返回2d文本的顶点着色器源码"""
 
        return """
            #version 330 core
 
            in vec4 a_Position;
            in vec2 a_Texcoord;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            uniform vec2 u_TextSize;
            uniform int u_Align;
            out vec2 v_Texcoord;
 
            void main() {
                v_Texcoord = a_Texcoord;
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
 
                switch (u_Align) {
                    case 0:
                        if (gl_VertexID == 1) {
                            gl_Position.y -= u_TextSize.y;
                        } else if (gl_VertexID == 3) {
                            gl_Position.y -= u_TextSize.y;
                            gl_Position.x += u_TextSize.x;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextSize.x;
                        }
                        break;
                    case 1:
                        if (gl_VertexID == 0) {
                            gl_Position.y += u_TextSize.y/2;
                        } else if (gl_VertexID == 1) {
                            gl_Position.y -= u_TextSize.y/2;
                        } else if (gl_VertexID == 3) {
                            gl_Position.x += u_TextSize.x;
                            gl_Position.y -= u_TextSize.y/2;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextSize.x;
                            gl_Position.y += u_TextSize.y/2;
                        }
                        break;
                    case 2:
                        if (gl_VertexID == 0) {
                            gl_Position.y += u_TextSize.y;
                        } else if (gl_VertexID == 3) {
                            gl_Position.x += u_TextSize.x;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextSize.x;
                            gl_Position.y += u_TextSize.y;
                        }
                        break;
                    case 3:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextSize.x/2;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextSize.x/2;
                            gl_Position.y -= u_TextSize.y;
                        } else if (gl_VertexID == 3) {
                            gl_Position.x += u_TextSize.x/2;
                            gl_Position.y -= u_TextSize.y;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextSize.x/2;
                        }
                        break;
                    case 4:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextSize.x/2;
                            gl_Position.y += u_TextSize.y/2;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextSize.x/2;
                            gl_Position.y -= u_TextSize.y/2;
                        } else if (gl_VertexID == 3) {
                            gl_Position.x += u_TextSize.x/2;
                            gl_Position.y -= u_TextSize.y/2;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextSize.x/2;
                            gl_Position.y += u_TextSize.y/2;
                        }
                        break;
                    case 5:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextSize.x/2;
                            gl_Position.y += u_TextSize.y;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextSize.x/2;
                        } else if (gl_VertexID == 3) {
                            gl_Position.x += u_TextSize.x/2;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextSize.x/2;
                            gl_Position.y += u_TextSize.y;
                        }
                        break;
                    case 6:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextSize.x;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextSize.x;
                            gl_Position.y -= u_TextSize.y;
                        } else if (gl_VertexID == 3) {
                            gl_Position.y -= u_TextSize.y;
                        }
                        break;
                    case 7:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextSize.x;
                            gl_Position.y += u_TextSize.y/2;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextSize.x;
                            gl_Position.y -= u_TextSize.y/2;
                        } else if (gl_VertexID == 3) {
                            gl_Position.y -= u_TextSize.y/2;
                        } else if (gl_VertexID == 2) {
                            gl_Position.y += u_TextSize.y/2;
                        }
                        break;
                    default:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextSize.x;
                            gl_Position.y += u_TextSize.y;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextSize.x;
                        } else if (gl_VertexID == 2) {
                            gl_Position.y += u_TextSize.y;
                        }
                }
            }
        """
 
    def get_fshader(self, texture):
        """返回片元着色器源码"""
 
        return """
            #version 330 core
 
            in vec2 v_Texcoord;
            uniform vec3 u_AmbientColor;
            uniform sampler2D u_Texture;
 
            void main() { 
                vec4 color = texture2D(u_Texture, v_Texcoord);
                vec3 rgb = color.rgb * u_AmbientColor;

                gl_FragColor = vec4(rgb, color.a);
            } 
        """

class BaseLight(_Light):
    """环境光"""
 
    def __init__(self, ambient=(1.0,1.0,1.0)):
        """构造函数"""
 
        _Light.__init__(self, ambient=ambient)
 
    def get_vshader(self, texture):
        """返回顶点着色器源码"""
 
        if texture is None:
            shader_src = """
                #version 330 core
 
                in vec4 a_Position;
                in vec4 a_Color;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                out vec4 v_Color;
 
                void main() { 
                    v_Color = a_Color;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                }
            """
        else:
            shader_src = """
                #version 330 core
 
                in vec4 a_Position;
                in %s a_Texcoord;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                out %s v_Texcoord;
 
                void main() { 
                    v_Texcoord = a_Texcoord;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                }
            """ % (self.a_dtype, self.a_dtype)
 
        return shader_src
 
    def get_fshader(self, texture):
        """返回片元着色器源码"""
 
        if texture is None:
            shader_src = """
                #version 330 core
 
                in vec4 v_Color;
                uniform vec3 u_AmbientColor;
 
                void main() { 
                    vec3 rgb = v_Color.rgb * u_AmbientColor;
                    gl_FragColor = vec4(rgb, v_Color.a); 
                } 
            """
        else:
            shader_src = """
                #version 330 core
 
                in %s v_Texcoord;
                uniform vec3 u_AmbientColor;
                uniform %s u_Texture;
 
                void main() { 
                    vec4 color = texture(u_Texture, v_Texcoord);
                    vec3 rgb = color.rgb * u_AmbientColor;
                    
                    gl_FragColor = vec4(rgb, color.a);
                } 
            """ % (self.a_dtype, self.u_dtype)
 
        return shader_src

class SunLight(_Light):
    """太阳光照情景模式"""

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
 
    def get_vshader(self, texture):
        """返回顶点着色器源码"""
 
        if texture is None:
            shader_src =  """
                #version 330 core
 
                in vec4 a_Position;
                in vec3 a_Normal;
                in vec4 a_Color;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_CamPos;
                uniform vec3 u_LightDir; // 定向光方向
                out vec4 v_Color;
                out vec3 v_Normal;
                out vec3 v_LightDir;
                out vec3 v_MiddleDir;
 
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
            shader_src = """
                #version 330 core
 
                in vec4 a_Position;
                in vec3 a_Normal;
                in %s a_Texcoord;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_CamPos;
                uniform vec3 u_LightDir; // 定向光方向
                out %s v_Texcoord;
                out vec3 v_Normal;
                out vec3 v_LightDir;
                out vec3 v_MiddleDir;
 
                void main() { 
                    v_Texcoord = a_Texcoord;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
 
                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix)); // 法向量矩阵
                    v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0))); // 重新计算模型变换后的法向量
                    vec3 camDir = normalize(u_CamPos - vec3(u_ModelMatrix * a_Position)); // 从当前顶点指向相机的向量
                    v_LightDir = normalize(-u_LightDir); // 光线向量取反后单位化
                    v_MiddleDir = normalize(camDir + v_LightDir); // 视线和光线的中间向量
                }
            """ % (self.a_dtype, self.a_dtype)

        return shader_src
 
    def get_fshader(self, texture):
        """返回片元着色器源码"""
 
        if texture is None:
            shader_src = """
                #version 330 core
 
                in vec4 v_Color;
                in vec3 v_Normal;
                in vec3 v_LightDir;
                in vec3 v_MiddleDir;
                uniform vec3 u_LightColor; // 定向光颜色
                uniform vec3 u_AmbientColor; // 环境光颜色
                uniform float u_Shiny; // 高光系数
                uniform float u_Specular; // 镜面反射系数
                uniform float u_Diffuse; // 漫反射系数
                uniform float u_Pellucid; // 透光系数
 
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
 
                    gl_FragColor = vec4(rgb, v_Color.a);
                }
            """
        else:
            shader_src = """
                #version 330 core
 
                in %s v_Texcoord;
                in vec3 v_Normal;
                in vec3 v_LightDir;
                in vec3 v_MiddleDir;
                uniform %s u_Texture;
                uniform vec3 u_LightColor; // 定向光颜色
                uniform vec3 u_AmbientColor; // 环境光颜色
                uniform float u_Shiny; // 高光系数
                uniform float u_Specular; // 镜面反射系数
                uniform float u_Diffuse; // 漫反射系数
                uniform float u_Pellucid; // 透光系数
 
                void main() { 
                    vec4 color = texture(u_Texture, v_Texcoord);
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
 
                    gl_FragColor = vec4(rgb, color.a);
                } 
            """ % (self.a_dtype, self.u_dtype)

        return shader_src

class LampLight(_Light):
    """定位光照情景模式"""

    def __init__(self, lamp=(0.0,0.0,2.0), lightcolor=(1.0,1.0,1.0), ambient=(0.3,0.3,0.3), **kwds):
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

    def get_vshader(self, texture):
        """返回顶点着色器源码"""
 
        if texture is None:
            shader_src =  """
                #version 330 core
 
                in vec4 a_Position;
                in vec3 a_Normal;
                in vec4 a_Color;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_CamPos;
                uniform vec3 u_LightPos;
                out vec4 v_Color;
                out vec3 v_Normal;
                out vec3 v_LightDir;
                out vec3 v_MiddleDir;
 
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
            shader_src = """
                #version 330 core
 
                in vec4 a_Position;
                in vec3 a_Normal;
                in %s a_Texcoord;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_CamPos;
                uniform vec3 u_LightPos;
                out %s v_Texcoord;
                out vec3 v_Normal;
                out vec3 v_LightDir;
                out vec3 v_MiddleDir;
 
                void main() { 
                    v_Texcoord = a_Texcoord;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
 
                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix)); // 法向量矩阵
                    v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0))); // 重新计算模型变换后的法向量
                    
                    vec3 camDir = normalize(u_CamPos - vec3(u_ModelMatrix * a_Position)); // 从当前顶点指向相机的向量
                    v_LightDir = normalize(u_LightPos - a_Position.xyz); // 光线向量单位化
                    v_MiddleDir = normalize(camDir + v_LightDir); // 视线和光线的中间向量
                }
            """ % (self.a_dtype, self.a_dtype)

        return shader_src
 
    def get_fshader(self, texture):
        """返回片元着色器源码"""
 
        if texture is None:
            shader_src = """
                #version 330 core
 
                in vec4 v_Color;
                in vec3 v_Normal;
                in vec3 v_LightDir;
                in vec3 v_MiddleDir;
                uniform vec3 u_LightColor; // 灯光颜色
                uniform vec3 u_AmbientColor; // 环境光颜色
                uniform float u_Shiny; // 高光系数
                uniform float u_Specular; // 镜面反射系数
                uniform float u_Diffuse; // 漫反射系数
                uniform float u_Pellucid; // 透光系数
 
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
 
                    gl_FragColor = vec4(rgb, v_Color.a);
                }
            """
        else:
            shader_src = """
                #version 330 core
 
                in %s v_Texcoord;
                in vec3 v_Normal;
                in vec3 v_LightDir;
                in vec3 v_MiddleDir;
                uniform %s u_Texture;
                uniform vec3 u_LightColor; // 灯光颜色
                uniform vec3 u_AmbientColor; // 环境光颜色
                uniform float u_Shiny; // 高光系数
                uniform float u_Specular; // 镜面反射系数
                uniform float u_Diffuse; // 漫反射系数
                uniform float u_Pellucid; // 透光系数
 
                void main() { 
                    vec4 color = texture(u_Texture, v_Texcoord);
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
 
                    gl_FragColor = vec4(rgb, color.a);
                } 
            """ % (self.a_dtype, self.u_dtype)

        return shader_src

class SkyLight(_Light):
    """户外光照情景模式"""

    def __init__(self, direction=(0.0,-1.0,0.0), sky=(1.0,1.0,1.0), ground=(0.5,0.5,0.5)):
        """构造函数"""

        _Light.__init__(self, 
            direction   = direction,                    # 光的方向
            sky         = sky,                          # 来自天空的环境光
            ground      = ground,                       # 来自地面的环境光
        )
 
    def get_vshader(self, texture):
        """返回使用颜色的顶点着色器源码"""
 
        if texture is None:
            return """
                #version 330 core
 
                in vec4 a_Position;
                in vec3 a_Normal;
                in vec4 a_Color;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_LightDir; // 定向光方向
                out vec4 v_Color;
                out float v_Costheta;
 
                void main() { 
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                    v_Color = a_Color;
 
                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                    vec3 normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
                    v_Costheta = dot(normal, normalize(-u_LightDir)) * 0.5 + 0.5;
                }
            """
        else:
            return """
                #version 330 core
 
                in vec4 a_Position;
                in vec3 a_Normal;
                in %s a_Texcoord;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                uniform vec3 u_LightDir; // 定向光方向
                out %s v_Texcoord;
                out float v_Costheta;
 
                void main() { 
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                    v_Texcoord = a_Texcoord;
 
                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                    vec3 normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
                    v_Costheta = dot(normal, normalize(-u_LightDir)) * 0.5 + 0.5;
                }
            """ % (self.a_dtype, self.a_dtype)
 
    def get_fshader(self, texture):
        """返回使用颜色的片元着色器源码"""
 
        if texture is None:
            return """
                #version 330 core
 
                in vec4 v_Color;
                in float v_Costheta;
                uniform vec3 u_SkyColor; // 天空光线颜色
                uniform vec3 u_GroundColor; // 地面光线颜色
 
                void main() { 
                    float costheta = v_Costheta;
                    if (!gl_FrontFacing) 
                        costheta *= 0.5;
 
                    vec3 rgb = mix(u_GroundColor, u_SkyColor, costheta) * v_Color.rgb;
                    gl_FragColor = vec4(rgb, v_Color.a);
                } 
            """
        else:
            return """
                #version 330 core
 
                in %s v_Texcoord;
                in float v_Costheta;
                uniform %s u_Texture;
                uniform vec3 u_SkyColor; // 天空光线颜色
                uniform vec3 u_GroundColor; // 地面光线颜色
 
                void main() { 
                    vec4 color = texture(u_Texture, v_Texcoord);
                    float costheta = v_Costheta;
                    if (!gl_FrontFacing) 
                        costheta *= 0.5;

                    vec3 rgb = mix(u_GroundColor, u_SkyColor, costheta) * color.rgb;
                    gl_FragColor = vec4(rgb, color.a);
                } 
            """ % (self.a_dtype, self.u_dtype)
 
class SphereLight(_Light):
    """球谐光照情景模式"""

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
 
    def get_vshader(self, texture):
        """返回使用颜色的顶点着色器源码"""
 
        if texture is None:
            return """
                #version 330 core
 
                in vec4 a_Position;
                in vec3 a_Normal;
                in vec4 a_Color;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                out vec4 v_Color;
                out vec3 v_Normal;
 
                void main() { 
                    v_Color = a_Color;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position;

                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                    v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
                }
            """
        else:
            return """
                #version 330 core
 
                in vec4 a_Position;
                in vec3 a_Normal;
                in %s a_Texcoord;
                uniform mat4 u_ProjMatrix;
                uniform mat4 u_ViewMatrix;
                uniform mat4 u_ModelMatrix;
                out %s v_Texcoord;
                out vec3 v_Normal;
 
                void main() { 
                    v_Texcoord = a_Texcoord;
                    gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position;

                    mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                    v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
                }
            """ % (self.a_dtype, self.a_dtype)
 
    def get_fshader(self, texture):
        """返回使用颜色的片元着色器源码"""
 
        if texture is None:
            return """
                #version 330 core
 
                in vec4 v_Color;
                in vec3 v_Normal;
                const float C1 = 0.429043;
                const float C2 = 0.511664;
                const float C3 = 0.743125;
                const float C4 = 0.886227;
                const float C5 = 0.247708;
                %s
                uniform float u_ScaleFactor;
 
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
                    gl_FragColor = vec4(rgb, v_Color.a);
                } 
            """ % self.parameter
        else: 
            return """
                #version 330 core
 
                in %s v_Texcoord;
                in vec3 v_Normal;
                const float C1 = 0.429043;
                const float C2 = 0.511664;
                const float C3 = 0.743125;
                const float C4 = 0.886227;
                const float C5 = 0.247708;
                %s
                uniform %s u_Texture;
                uniform float u_ScaleFactor;
 
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
                    vec4 color = texture(u_Texture, v_Texcoord);
                    vec3 rgb = color.rgb * diffuse;
                    gl_FragColor = vec4(rgb, color.a);
                } 
            """ % (self.a_dtype, self.parameter, self.u_dtype)
        
