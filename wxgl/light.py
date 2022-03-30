# -*- coding: utf-8 -*-

from OpenGL.GL import *
from . import model as wxModel


class BaseLight:
    """环境光照情景模式"""
    
    def __init__(self, ambient=(1.0,1.0,1.0)):
        """构造函数"""
        
        self.ambient = ambient              # 环境光
    
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""
        
        indices = kwds.get('indices')
        color = kwds.get('color')
        texture = kwds.get('texture')
        texcoord = kwds.get('texcoord')
        lw = kwds.get('lw')
        ls = kwds.get('ls')
        
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull')
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        
        if color is None:
            vshader = self.get_texture_vshader(texture.ttype)
            fshader = self.get_texture_fshader(texture.ttype)
            
            m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
            m.set_vertex('a_Position', vs, indices)
            m.set_texcoord('a_Texcoord', texcoord)
            m.add_texture('u_Texture', texture)
            m.set_argument('u_AmbientColor', self.ambient)
            m.set_picked('u_Picked')
            m.set_proj_matrix('u_ProjMatrix')
            m.set_view_matrix('u_ViewMatrix')
            m.set_model_matrix('u_ModelMatrix', transform)
            m.set_cull_mode(cull)
            m.set_fill_mode(fill)
            m.set_slide(slide)
        else:
            vshader = self.get_color_vshader()
            fshader = self.get_color_fshader()
            
            m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
            m.set_vertex('a_Position', vs, indices)
            m.set_color('a_Color', color)
            m.set_argument('u_AmbientColor', self.ambient)
            m.set_picked('u_Picked')
            m.set_proj_matrix('u_ProjMatrix')
            m.set_view_matrix('u_ViewMatrix')
            m.set_model_matrix('u_ModelMatrix', transform)
            m.set_line_style(lw, ls)
            m.set_cull_mode(cull)
            m.set_fill_mode(fill)
            m.set_slide(slide)
        
        return m
    
    def get_color_vshader(self):
        """返回颜色模型的顶点着色器源码"""
        
        return """
            #version 330 core
            
            in vec4 a_Position;
            in vec4 a_Color;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            out vec4 v_Color;
            
            void main() { 
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                v_Color = a_Color;
            }
        """
    
    def get_texture_vshader(self, ttype):
        """返回纹理模型的顶点着色器源码"""
        
        if ttype == GL_TEXTURE_1D:
            a_dtype = 'float'
        elif ttype == GL_TEXTURE_2D:
            a_dtype = 'vec2'
        elif ttype == GL_TEXTURE_2D_ARRAY or ttype == GL_TEXTURE_3D:
            a_dtype = 'vec3'
        
        return """
            #version 330 core
            
            in vec4 a_Position;
            in %s a_Texcoord;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            out %s v_Texcoord;
            
            void main() { 
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                v_Texcoord = a_Texcoord;
            }
        """ % (a_dtype, a_dtype)
        
    def get_color_fshader(self):
        """返回颜色的片元着色器源码"""
        
        return """
            #version 330 core
            
            in vec4 v_Color;
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
        
    def get_texture_fshader(self, ttype):
        """返回纹理的片元着色器源码"""
        
        if ttype == GL_TEXTURE_1D:
            a_dtype = 'float'
            u_dtype = 'sampler1D'
            f_name = 'texture1D'
        elif ttype == GL_TEXTURE_2D:
            a_dtype = 'vec2'
            u_dtype = 'sampler2D'
            f_name = 'texture2D'
        elif ttype == GL_TEXTURE_2D_ARRAY:
            a_dtype = 'vec3'
            u_dtype = 'sampler2DArray'
            f_name = 'texture2DArray'
        elif ttype == GL_TEXTURE_3D:
            a_dtype = 'vec3'
            u_dtype = 'sampler3D'
            f_name = 'texture3D'
        
        return """
            #version 330 core
            
            in %s v_Texcoord;
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
        """ % (a_dtype, u_dtype, f_name)

class BaseLightPoint:
    """适用于点环境光照情景模式"""
    
    def __init__(self, ambient=(1.0,1.0,1.0)):
        """构造函数"""
        
        self.ambient = ambient              # 环境光
    
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""
        
        color = kwds.get('color')
        psize = kwds.get('psize')
        
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', False)
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        
        vshader = self.get_point_vshader()
        fshader = self.get_point_fshader()
        
        m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
        m.set_vertex('a_Position', vs)
        m.set_color('a_Color', color)
        m.set_psize('a_Psize', psize)
        m.set_picked('u_Picked')
        m.set_argument('u_AmbientColor', self.ambient)
        m.set_proj_matrix('u_ProjMatrix')
        m.set_view_matrix('u_ViewMatrix')
        m.set_model_matrix('u_ModelMatrix', transform)
        m.set_slide(slide)
        
        return m
    
    def get_point_vshader(self):
        """返回点的顶点着色器源码"""
        
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
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position;
                gl_PointSize = a_Psize;
                v_Color = a_Color;
            }
        """
        
    def get_point_fshader(self):
        """返回散点的片元着色器源码"""
        
        return """
            #version 330 core
            
            in vec4 v_Color;
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

class BaseLightText2d:
    """适用于2d文本的环境光照情景模式"""
    
    def __init__(self, ambient=(1.0,1.0,1.0)):
        """构造函数"""
        
        self.ambient = ambient              # 环境光
    
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""
        
        color = kwds.get('color')
        texture = kwds.get('texture')
        texcoord = kwds.get('texcoord')
        loc = kwds.get('loc')
        tw = kwds.get('tw')
        th = kwds.get('th')
        
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        slide = kwds.get('slide')
        
        vshader = self.get_text2d_vshader()
        fshader = self.get_text2d_fshader()
        
        m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
        m.set_vertex('a_Position', vs)
        m.set_texcoord('a_Texcoord', texcoord)
        m.add_texture('u_Texture', texture)
        m.set_argument('u_AmbientColor', self.ambient)
        m.set_argument('u_TextWidth', tw)
        m.set_argument('u_TextHeight', th)
        m.set_argument('u_Corner', loc)
        m.set_picked('u_Picked')
        m.set_proj_matrix('u_ProjMatrix')
        m.set_view_matrix('u_ViewMatrix')
        m.set_model_matrix('u_ModelMatrix')
        m.set_slide(slide)
        
        return m
    
    def get_text2d_vshader(self):
        """返回2d文本的顶点着色器源码"""
        
        return """
            #version 330 core
            
            in vec4 a_Position;
            in vec2 a_Texcoord;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            uniform float u_TextWidth;
            uniform float u_TextHeight;
            uniform int u_Corner;
            out vec2 v_Texcoord;
            
            void main() {
                v_Texcoord = a_Texcoord;
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                
                switch (u_Corner) {
                    case 0:
                        if (gl_VertexID == 1) {
                            gl_Position.y -= u_TextHeight;
                        } else if (gl_VertexID == 3) {
                            gl_Position.y -= u_TextHeight;
                            gl_Position.x += u_TextWidth;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextWidth;
                        }
                        break;
                    case 1:
                        if (gl_VertexID == 0) {
                            gl_Position.y += u_TextHeight/2;
                        } else if (gl_VertexID == 1) {
                            gl_Position.y -= u_TextHeight/2;
                        } else if (gl_VertexID == 3) {
                            gl_Position.x += u_TextWidth;
                            gl_Position.y -= u_TextHeight/2;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextWidth;
                            gl_Position.y += u_TextHeight/2;
                        }
                        break;
                    case 2:
                        if (gl_VertexID == 0) {
                            gl_Position.y += u_TextHeight;
                        } else if (gl_VertexID == 3) {
                            gl_Position.x += u_TextWidth;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextWidth;
                            gl_Position.y += u_TextHeight;
                        }
                        break;
                    case 3:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextWidth/2;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextWidth/2;
                            gl_Position.y -= u_TextHeight;
                        } else if (gl_VertexID == 3) {
                            gl_Position.x += u_TextWidth/2;
                            gl_Position.y -= u_TextHeight;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextWidth/2;
                        }
                        break;
                    case 4:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextWidth/2;
                            gl_Position.y += u_TextHeight/2;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextWidth/2;
                            gl_Position.y -= u_TextHeight/2;
                        } else if (gl_VertexID == 3) {
                            gl_Position.x += u_TextWidth/2;
                            gl_Position.y -= u_TextHeight/2;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextWidth/2;
                            gl_Position.y += u_TextHeight/2;
                        }
                        break;
                    case 5:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextWidth/2;
                            gl_Position.y += u_TextHeight;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextWidth/2;
                        } else if (gl_VertexID == 3) {
                            gl_Position.x += u_TextWidth/2;
                        } else if (gl_VertexID == 2) {
                            gl_Position.x += u_TextWidth/2;
                            gl_Position.y += u_TextHeight;
                        }
                        break;
                    case 6:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextWidth;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextWidth;
                            gl_Position.y -= u_TextHeight;
                        } else if (gl_VertexID == 3) {
                            gl_Position.y -= u_TextHeight;
                        }
                        break;
                    case 7:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextWidth;
                            gl_Position.y += u_TextHeight/2;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextWidth;
                            gl_Position.y -= u_TextHeight/2;
                        } else if (gl_VertexID == 3) {
                            gl_Position.y -= u_TextHeight/2;
                        } else if (gl_VertexID == 2) {
                            gl_Position.y += u_TextHeight/2;
                        }
                        break;
                    default:
                        if (gl_VertexID == 0) {
                            gl_Position.x -= u_TextWidth;
                            gl_Position.y += u_TextHeight;
                        } else if (gl_VertexID == 1) {
                            gl_Position.x -= u_TextWidth;
                        } else if (gl_VertexID == 2) {
                            gl_Position.y += u_TextHeight;
                        }
                }
            }
        """
        
    def get_text2d_fshader(self):
        """返回2d文本的片元着色器源码"""
        
        return """
            #version 330 core
            
            in vec2 v_Texcoord;
            uniform vec3 u_AmbientColor;
            uniform sampler2D u_Texture;
            uniform int u_Picked;
            
            void main() { 
                vec4 color = texture2D(u_Texture, v_Texcoord);
                vec3 rgb = color.rgb * u_AmbientColor;
                if (u_Picked == 0)
                    gl_FragColor = vec4(rgb, color.a);
                else
                    gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a);
            } 
        """

class BaseLightText2dArray:
    """适用于2d文本数组的环境光照情景模式"""
    
    def __init__(self, ambient=(1.0,1.0,1.0)):
        """构造函数"""
        
        self.ambient = ambient              # 环境光
    
    def get_model(self, gltype, vs_arr, loc_view, texture, texcoord, tw, th, **kwds):
        """返回模型对象"""
        
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', False)
        slide = kwds.get('slide')
        
        vshader = self.get_text2darray_vshader()
        fshader = self.get_text2darray_fshader()
        
        m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
        m.set_vertex('a_Position', vs_arr)
        m.set_texcoord('a_Texcoord', texcoord)
        m.add_texture('u_Texture', texture)
        m.set_argument('u_AmbientColor', self.ambient)
        m.set_argument('u_TextWidth', tw)
        m.set_argument('u_TextHeight', th)
        m.set_argument('a_LocView', loc_view)
        m.set_ae('u_Ae')
        m.set_picked('u_Picked')
        m.set_proj_matrix('u_ProjMatrix')
        m.set_view_matrix('u_ViewMatrix')
        m.set_model_matrix('u_ModelMatrix')
        m.set_slide(slide)
        
        return m
    
    def get_text2darray_vshader(self):
        """返回2d文本数组的顶点着色器源码"""
        
        return """
            #version 330 core
            
            in vec4 a_Position;
            in vec3 a_Texcoord;
            in ivec2 a_LocView;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            uniform float u_TextWidth;
            uniform float u_TextHeight;
            out vec3 v_Texcoord;
            out float v_View;
            
            void main() {
                v_Texcoord = a_Texcoord;
                v_View = float(a_LocView[1]);
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                
                int idx = gl_VertexID % 4;
                if (a_LocView[0] == 4) {
                    if (idx == 0) {
                        gl_Position.x -= u_TextWidth/2;
                        gl_Position.y += u_TextHeight/2;
                    } else if (idx == 1) {
                        gl_Position.x -= u_TextWidth/2;
                        gl_Position.y -= u_TextHeight/2;
                    } else if (idx == 2) {
                        gl_Position.x += u_TextWidth/2;
                        gl_Position.y -= u_TextHeight/2;
                    } else if (idx == 3) {
                        gl_Position.x += u_TextWidth/2;
                        gl_Position.y += u_TextHeight/2;
                    }
                } else {
                    if (idx == 0) {
                        gl_Position.x -= u_TextWidth;
                        gl_Position.y += u_TextHeight/2;
                    } else if (idx == 1) {
                        gl_Position.x -= u_TextWidth;
                        gl_Position.y -= u_TextHeight/2;
                    } else if (idx == 2) {
                        gl_Position.y -= u_TextHeight/2;
                    } else if (idx == 3) {
                        gl_Position.y += u_TextHeight/2;
                    }
                }
            }
        """
        
    def get_text2darray_fshader(self):
        """返回2d文本数组的片元着色器源码"""
        
        return """
            #version 330 core
            
            in vec3 v_Texcoord;
            in float v_View;
            uniform vec3 u_AmbientColor;
            uniform sampler2DArray u_Texture;
            uniform int u_Picked;
            uniform vec2 u_Ae;
            
            void main() { 
                bool up = u_Ae[1] > -90 && u_Ae[1] < 90; 
                switch (int(v_View)) {
                    case 1:
                        if (u_Ae[0] < 0 || u_Ae[0] >= 90) discard;
                        break;
                    case 2:
                        if (u_Ae[0] < 90 || u_Ae[0] >= 180) discard;
                        break;
                    case 3:
                        if (u_Ae[0] >= -90 || u_Ae[0] < -180) discard;
                        break;
                    case 4:
                        if (u_Ae[0] >= 0 || u_Ae[0] < -90) discard;
                        break;
                    case 5:
                        if (u_Ae[1] < 0 || (up && (u_Ae[0] <= -90 || u_Ae[0] >= 90)) || (!up && u_Ae[0] >= -90 && u_Ae[0] <= 90)) discard;
                        break;
                    case 6:
                        if (u_Ae[1] >= 0 || (up && (u_Ae[0] <= -90 || u_Ae[0] >= 90)) || (!up && u_Ae[0] >= -90 && u_Ae[0] <= 90)) discard;
                        break;
                    case 7:
                        if (u_Ae[1] < 0 || (up && u_Ae[0] >= -90 && u_Ae[0] <= 90) || (!up && (u_Ae[0] <= -90 || u_Ae[0] >= 90))) discard;
                        break;
                    case 8:
                        if (u_Ae[1] >= 0 || (up && u_Ae[0] >= -90 && u_Ae[0] <= 90) || (!up && (u_Ae[0] <= -90 || u_Ae[0] >= 90))) discard;
                        break;
                    case 9:
                        if (u_Ae[1] < 0 || (up && u_Ae[0] >= 0 && u_Ae[0] <= 180) || (!up && u_Ae[0] >= -180 && u_Ae[0] <= 0)) discard;
                        break;
                    case 10:
                        if (u_Ae[1] >= 0 || (up && u_Ae[0] >= 0 && u_Ae[0] <= 180) || (!up && u_Ae[0] >= -180 && u_Ae[0] <= 0)) discard;
                        break;
                    case 11:
                        if (u_Ae[1] < 0 || (!up && u_Ae[0] >= 0 && u_Ae[0] <= 180) || (up && u_Ae[0] >= -180 && u_Ae[0] <= 0)) discard;
                        break;
                    case 12:
                        if (u_Ae[1] >= 0 || (!up && u_Ae[0] >= 0 && u_Ae[0] <= 180) || (up && u_Ae[0] >= -180 && u_Ae[0] <= 0)) discard;
                        break;
                    default:
                        break;
                }
                
                vec4 color = texture2DArray(u_Texture, v_Texcoord);
                vec3 rgb = color.rgb * u_AmbientColor;
                if (u_Picked == 0)
                    gl_FragColor = vec4(rgb, color.a);
                else
                    gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a);
            } 
        """

class SunLight:
    """太阳光照情景模式"""
    
    def __init__(self, direction=(-5.0,-1.0,-5.0), color=(1.0,1.0,1.0), ambient=(0.3,0.3,0.3), **kwds):
        """构造函数"""
        
        self.direction = direction                          # 光的方向
        self.color = color                                  # 光的颜色
        self.ambient = ambient                              # 环境光
        self.stray = kwds.get('stray', False)               # 杂散光
        self.roughness = kwds.get('roughness', 0.2)         # 粗糙度（1-镜面反射系数）：值域范围[0.0,1.0]
        self.metalness = kwds.get('metalness', 0.2)         # 金属度（1-漫反射系数）：值域范围[0.0,1.0]
        self.pellucidness = kwds.get('pellucidness', 0.2)   # 透光度：值域范围[0.0,1.0]
        self.shininess = kwds.get('shininess', 30.0)        # 光洁度（高光指数）：值域范围(0.0,3000.0]
    
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""
        
        indices = kwds.get('indices')
        color = kwds.get('color')
        normal = kwds.get('normal')
        texture = kwds.get('texture')
        texcoord = kwds.get('texcoord')
        
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull')
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        
        if color is None:
            vshader = self.get_texture_vshader(texture.ttype)
            fshader = self.get_texture_fshader(texture.ttype)
            
            m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
            m.set_texcoord('a_Texcoord', texcoord)
            m.add_texture('u_Texture', texture)
        else:
            vshader = self.get_color_vshader()
            fshader = self.get_color_fshader()
            
            m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
            m.set_color('a_Color', color)
        
        m.set_vertex('a_Position', vs, indices)
        m.set_normal('a_Normal', normal)
        m.set_cam_pos('u_CamPos')
        m.set_picked('u_Picked')
        m.set_argument('u_AmbientColor', self.ambient)
        m.set_argument('u_LightDir', self.direction)
        m.set_argument('u_LightColor', self.color)
        m.set_argument('u_Shininess', self.shininess)
        m.set_argument('u_Roughness', self.roughness)
        m.set_argument('u_Metalness', self.metalness)
        m.set_argument('u_Pellucidness', self.pellucidness)
        m.set_proj_matrix('u_ProjMatrix')
        m.set_view_matrix('u_ViewMatrix')
        m.set_model_matrix('u_ModelMatrix', transform)
        m.set_cull_mode(cull)
        m.set_fill_mode(fill)
        m.set_slide(slide)
        
        return m
    
    def get_color_vshader(self):
        """返回使用颜色的顶点着色器源码"""
        
        return """
            #version 330 core
            
            in vec4 a_Position;
            in vec3 a_Normal;
            in vec4 a_Color;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            out vec4 v_Color;
            out vec3 v_Position;
            out vec3 v_Normal;
            
            void main() { 
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                v_Color = a_Color;
                v_Position= vec3(u_ModelMatrix * a_Position);
                
                mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
            }
        """
    
    def get_texture_vshader(self, ttype):
        """返回使用纹理的顶点着色器源码"""
        
        if ttype == GL_TEXTURE_1D:
            a_dtype = 'float'
        elif ttype == GL_TEXTURE_2D:
            a_dtype = 'vec2'
        elif ttype == GL_TEXTURE_2D_ARRAY or ttype == GL_TEXTURE_3D:
            a_dtype = 'vec3'
        
        return """
            #version 330 core
            
            in vec4 a_Position;
            in vec3 a_Normal;
            in %s a_Texcoord;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            out %s v_Texcoord;
            out vec3 v_Position;
            out vec3 v_Normal;
            
            void main() { 
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                v_Texcoord = a_Texcoord;
                v_Position= vec3(u_ModelMatrix * a_Position);
                
                mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
            }
        """ % (a_dtype, a_dtype)
    
    def get_color_fshader(self):
        """返回使用颜色的片元着色器源码"""
        
        if self.stray:
            diffuse_str = '(1 - u_Metalness) * (dot(lightDir, v_Normal) + 1.0) / 2.0'
        else:
            diffuse_str = '(1 - u_Metalness) * max(0.0, dot(lightDir, v_Normal))'
        
        return """
            #version 330 core
            
            in vec4 v_Color;
            in vec3 v_Position;
            in vec3 v_Normal;
            uniform vec3 u_LightDir; // 定向光方向
            uniform vec3 u_LightColor; // 定向光颜色
            uniform vec3 u_AmbientColor; // 环境光颜色
            uniform vec3 u_CamPos; // 相机位置
            uniform int u_Picked; // 拾取标志
            uniform float u_Shininess; // 光洁度
            uniform float u_Roughness; // 粗糙度
            uniform float u_Metalness; // 金属度
            uniform float u_Pellucidness; // 透光度
            
            void main() { 
                vec3 lightDir = normalize(u_LightDir); // 光线向量
                vec3 camDir = normalize(v_Position - u_CamPos); // 视线向量
                vec3 middleDir = normalize(camDir + lightDir); // 视线和光线的中间向量
                
                float diffuseCos = %s; // 光线向量和法向量的内积
                float specularCos = (1 - u_Roughness) * max(0.0, dot(middleDir, v_Normal)); // 中间向量和法向量内积
                
                specularCos = pow(specularCos, u_Shininess);
                if (!gl_FrontFacing) diffuseCos *= u_Pellucidness;
                
                vec3 scatteredLight = u_AmbientColor + u_LightColor * diffuseCos; // 散射光
                vec3 reflectedLight = u_LightColor * specularCos; // 反射光
                vec3 rgb = min(v_Color.rgb * (scatteredLight + reflectedLight), vec3(1.0));
                
                if (u_Picked == 0)
                    gl_FragColor = vec4(rgb, v_Color.a);
                else
                    gl_FragColor = vec4(min(rgb * 1.5, vec3(1.0)), v_Color.a);
            }
        """ % diffuse_str
    
    def get_texture_fshader(self, ttype):
        """返回使用纹理的片元着色器源码"""
        
        if ttype == GL_TEXTURE_1D:
            a_dtype = 'float'
            u_dtype = 'sampler1D'
            f_name = 'texture1D'
        elif ttype == GL_TEXTURE_2D:
            a_dtype = 'vec2'
            u_dtype = 'sampler2D'
            f_name = 'texture2D'
        elif ttype == GL_TEXTURE_2D_ARRAY:
            a_dtype = 'vec3'
            u_dtype = 'sampler2DArray'
            f_name = 'texture2DArray'
        elif ttype == GL_TEXTURE_3D:
            a_dtype = 'vec3'
            u_dtype = 'sampler3D'
            f_name = 'texture3D'
        
        if self.stray:
            diffuse_str = '(1 - u_Metalness) * (dot(lightDir, v_Normal) + 1.0) / 2.0'
        else:
            diffuse_str = '(1 - u_Metalness) * max(0.0, dot(lightDir, v_Normal))'
        
        return """
            #version 330 core
            
            in %s v_Texcoord;
            in vec3 v_Position;
            in vec3 v_Normal;
            uniform %s u_Texture;
            uniform vec3 u_LightDir; // 定向光方向
            uniform vec3 u_LightColor; // 定向光颜色
            uniform vec3 u_AmbientColor; // 环境光颜色
            uniform vec3 u_CamPos; // 相机位置
            uniform int u_Picked; // 拾取标志
            uniform float u_Shininess; // 光洁度
            uniform float u_Roughness; // 粗糙度
            uniform float u_Metalness; // 金属度
            uniform float u_Pellucidness; // 透光度
            
            void main() { 
                vec3 lightDir = normalize(u_LightDir); // 光线向量
                vec3 camDir = normalize(v_Position - u_CamPos); // 视线向量
                vec3 middleDir = normalize(camDir + lightDir); // 视线和光线的中间向量
                vec4 color = %s(u_Texture, v_Texcoord);
                
                float diffuseCos = %s; // 光线向量和法向量的内积
                float specularCos = (1 - u_Roughness) * max(0.0, dot(middleDir, v_Normal)); // 中间向量和法向量内积
                
                if (!gl_FrontFacing) 
                    diffuseCos *= u_Pellucidness;
                
                if (diffuseCos == 0.0 || u_Shininess > 2980.0) 
                    specularCos = 0.0;
                else
                    specularCos = pow(specularCos, u_Shininess);
                
                vec3 scatteredLight = u_AmbientColor + u_LightColor * diffuseCos; // 散射光
                vec3 reflectedLight = u_LightColor * specularCos; // 反射光
                vec3 rgb = min(color.rgb * (scatteredLight + reflectedLight), vec3(1.0));
                
                if (u_Picked == 0)
                    gl_FragColor = vec4(rgb, color.a);
                else
                    gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a);
            } 
        """ % (a_dtype, u_dtype, f_name, diffuse_str)

class LampLight:
    """室内光照情景模式"""
    
    def __init__(self, position=(5.0,1.0,5.0), color=(1.0,1.0,1.0), ambient=(0.3,0.3,0.3), **kwds):
        """构造函数"""
        
        self.position = position                            # 光源位置
        self.color = color                                  # 光的颜色
        self.ambient = ambient                              # 环境光
        self.stray = kwds.get('stray', False)               # 杂散光
        self.roughness = kwds.get('roughness', 0.2)         # 粗糙度（1-镜面反射系数）：值域范围[0.0,1.0]
        self.metalness = kwds.get('metalness', 0.2)         # 金属度（1-漫反射系数）：值域范围[0.0,1.0]
        self.pellucidness = kwds.get('pellucidness', 0.2)   # 透光度：值域范围[0.0,1.0]
        self.shininess = kwds.get('shininess', 30.0)        # 光洁度（高光指数）：值域范围(0.0,3000.0]
    
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""
        
        indices = kwds.get('indices')
        color = kwds.get('color')
        normal = kwds.get('normal')
        texture = kwds.get('texture')
        texcoord = kwds.get('texcoord')
        
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull')
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        
        if color is None:
            vshader = self.get_texture_vshader(texture.ttype)
            fshader = self.get_texture_fshader(texture.ttype)
            
            m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
            m.set_texcoord('a_Texcoord', texcoord)
            m.add_texture('u_Texture', texture)
        else:
            vshader = self.get_color_vshader()
            fshader = self.get_color_fshader()
            
            m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
            m.set_color('a_Color', color)
        
        m.set_vertex('a_Position', vs, indices)
        m.set_normal('a_Normal', normal)
        m.set_cam_pos('u_CamPos')
        m.set_picked('u_Picked')
        m.set_argument('u_AmbientColor', self.ambient)
        m.set_argument('u_LightPos', self.position)
        m.set_argument('u_LightColor', self.color)
        m.set_argument('u_Shininess', self.shininess)
        m.set_argument('u_Roughness', self.roughness)
        m.set_argument('u_Metalness', self.metalness)
        m.set_argument('u_Pellucidness', self.pellucidness)
        m.set_proj_matrix('u_ProjMatrix')
        m.set_view_matrix('u_ViewMatrix')
        m.set_model_matrix('u_ModelMatrix', transform)
        m.set_cull_mode(cull)
        m.set_fill_mode(fill)
        m.set_slide(slide)
        
        return m
    
    def get_color_vshader(self):
        """返回使用颜色的顶点着色器源码"""
        
        return """
            #version 330 core
            in vec4 a_Position;
            in vec3 a_Normal;
            in vec4 a_Color;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            out vec4 v_Color;
            out vec3 v_Position;
            out vec3 v_Normal;
            void main() { 
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                v_Color = a_Color;
                v_Position= vec3(u_ModelMatrix * a_Position);
                
                mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
            }
        """
    
    def get_texture_vshader(self):
        """返回使用纹理的顶点着色器源码"""
        
        if ttype == GL_TEXTURE_1D:
            a_dtype = 'float'
        elif ttype == GL_TEXTURE_2D:
            a_dtype = 'vec2'
        elif ttype == GL_TEXTURE_2D_ARRAY or ttype == GL_TEXTURE_3D:
            a_dtype = 'vec3'
        
        return """
            #version 330 core
            in vec4 a_Position;
            in vec3 a_Normal;
            in %s a_Texcoord;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            out %s v_Texcoord;
            out vec3 v_Position;
            out vec3 v_Normal;
            void main() { 
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                v_Texcoord = a_Texcoord;
                v_Position= vec3(u_ModelMatrix * a_Position);
                
                mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
            }
        """ % (a_dtype, a_dtype)
    
    def get_color_fshader(self):
        """返回使用颜色的片元着色器源码"""
        
        if self.stray:
            diffuse_str = '(1 - u_Metalness) * (dot(lightDir, v_Normal) + 1.0) / 2.0'
        else:
            diffuse_str = '(1 - u_Metalness) * max(0.0, dot(lightDir, v_Normal))'
        
        return """
            #version 330 core
            in vec4 v_Color;
            in vec3 v_Position;
            in vec3 v_Normal;
            uniform vec3 u_LightPos; // 光源位置
            uniform vec3 u_LightColor; // 光源颜色
            uniform vec3 u_AmbientColor; // 环境光颜色
            uniform vec3 u_CamPos; // 相机位置
            uniform int u_Picked; // 拾取标志
            uniform float u_Shininess; // 光洁度
            uniform float u_Roughness; // 粗糙度
            uniform float u_Metalness; // 金属度
            uniform float u_Pellucidness; // 透光度
            void main() { 
                vec3 lightDir = normalize(v_Position - u_LightPos); // 光线向量
                vec3 camDir = normalize(v_Position - u_CamPos); // 视线向量
                vec3 middleDir = normalize(camDir + lightDir); // 视线和光线的中间向量
                
                float diffuseCos = %s; // 光线向量和法向量的内积
                float specularCos = (1 - u_Roughness) * max(0.0, dot(middleDir, v_Normal)); // 中间向量和法向量内积
                
                specularCos = pow(specularCos, u_Shininess);
                if (!gl_FrontFacing) diffuseCos *= u_Pellucidness;
                
                vec3 scatteredLight = u_AmbientColor + u_LightColor * diffuseCos; // 散射光
                vec3 reflectedLight = u_LightColor * specularCos; // 反射光
                vec3 rgb = min(v_Color.rgb * (scatteredLight + reflectedLight), vec3(1.0));
                
                if (u_Picked == 0)
                    gl_FragColor = vec4(rgb, v_Color.a);
                else
                    gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), v_Color.a);
            }
        """ % diffuse_str
    
    def get_texture_fshader(self):
        """返回使用纹理的片元着色器源码"""
        
        if ttype == GL_TEXTURE_1D:
            a_dtype = 'float'
            u_dtype = 'sampler1D'
            f_name = 'texture1D'
        elif ttype == GL_TEXTURE_2D:
            a_dtype = 'vec2'
            u_dtype = 'sampler2D'
            f_name = 'texture2D'
        elif ttype == GL_TEXTURE_2D_ARRAY:
            a_dtype = 'vec3'
            u_dtype = 'sampler2DArray'
            f_name = 'texture2DArray'
        elif ttype == GL_TEXTURE_3D:
            a_dtype = 'vec3'
            u_dtype = 'sampler3D'
            f_name = 'texture3D'
        
        if self.stray:
            diffuse_str = '(1 - u_Metalness) * (dot(lightDir, v_Normal) + 1.0) / 2.0'
        else:
            diffuse_str = '(1 - u_Metalness) * max(0.0, dot(lightDir, v_Normal))'
        
        return """
            #version 330 core
            in %s v_Texcoord;
            in vec3 v_Position;
            in vec3 v_Normal;
            uniform %s u_Texture;
            uniform vec3 u_LightPos; // 光源位置
            uniform vec3 u_LightColor; // 光源颜色
            uniform vec3 u_AmbientColor; // 环境光颜色
            uniform vec3 u_CamPos; // 相机位置
            uniform int u_Picked; // 拾取标志
            uniform float u_Shininess; // 光洁度
            uniform float u_Roughness; // 粗糙度
            uniform float u_Metalness; // 金属度
            uniform float u_Pellucidness; // 透光度
            void main() { 
                vec3 lightDir = normalize(v_Position - u_LightPos); // 光线向量
                vec3 camDir = normalize(v_Position - u_CamPos); // 视线向量
                vec3 middleDir = normalize(camDir + lightDir); // 视线和光线的中间向量
                vec4 color = %s(u_Texture, v_Texcoord);
                
                float diffuseCos = %s; // 光线向量和法向量的内积
                float specularCos = (1 - u_Roughness) * max(0.0, dot(middleDir, v_Normal)); // 中间向量和法向量内积
                
                if (!gl_FrontFacing) 
                    diffuseCos *= u_Pellucidness;
                
                if (diffuseCos == 0.0 || u_Shininess > 2980.0) 
                    specularCos = 0.0;
                else
                    specularCos = pow(specularCos, u_Shininess);
                
                vec3 scatteredLight = u_AmbientColor + u_LightColor * diffuseCos; // 散射光
                vec3 reflectedLight = u_LightColor * specularCos; // 反射光
                vec3 rgb = min(color.rgb * (scatteredLight + reflectedLight), vec3(1.0));
                
                if (u_Picked == 0)
                    gl_FragColor = vec4(rgb, color.a);
                else
                    gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a);
            } 
        """ % (a_dtype, u_dtype, f_name, diffuse_str)

class SkyLight:
    """户外光照情景模式"""
    
    def __init__(self, direction=(0.0,-1.0,0.0), sky=(0.8,0.8,0.8), ground=(0.5,0.5,0.5)):
        """构造函数"""
        
        self.direction = direction          # 光的方向
        self.sky = sky                      # 来自天空的环境光
        self.ground = ground                # 来自地面的环境光
    
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""
        
        indices = kwds.get('indices')
        color = kwds.get('color')
        normal = kwds.get('normal')
        texture = kwds.get('texture')
        texcoord = kwds.get('texcoord')
        
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull')
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        
        if color is None:
            vshader = self.get_texture_vshader(texture.ttype)
            fshader = self.get_texture_fshader(texture.ttype)
            
            m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
            m.set_texcoord('a_Texcoord', texcoord)
            m.add_texture('u_Texture', texture)
        else:
            vshader = self.get_color_vshader()
            fshader = self.get_color_fshader()
            
            m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
            m.set_color('a_Color', color)
        
        m.set_vertex('a_Position', vs, indices)
        m.set_normal('a_Normal', normal)
        m.set_argument('u_LightDir', self.direction)
        m.set_argument('u_SkyColor', self.sky)
        m.set_argument('u_GroundColor', self.ground)
        m.set_picked('u_Picked')
        m.set_proj_matrix('u_ProjMatrix')
        m.set_view_matrix('u_ViewMatrix')
        m.set_model_matrix('u_ModelMatrix', transform)
        m.set_cull_mode(cull)
        m.set_fill_mode(fill)
        m.set_slide(slide)
        
        return m
    
    def get_color_vshader(self):
        """返回使用颜色的顶点着色器源码"""
        
        return """
            #version 330 core
            
            in vec4 a_Position;
            in vec3 a_Normal;
            in vec4 a_Color;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            out vec3 v_Normal;
            out vec4 v_Color;
            
            void main() { 
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                v_Color = a_Color;
                
                mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
            }
        """
    
    def get_texture_vshader(self):
        """返回使用纹理的顶点着色器源码"""
        
        if ttype == GL_TEXTURE_1D:
            a_dtype = 'float'
        elif ttype == GL_TEXTURE_2D:
            a_dtype = 'vec2'
        elif ttype == GL_TEXTURE_2D_ARRAY or ttype == GL_TEXTURE_3D:
            a_dtype = 'vec3'
        
        return """
            #version 330 core
            
            in vec4 a_Position;
            in vec3 a_Normal;
            in %s a_Texcoord;
            uniform mat4 u_ProjMatrix;
            uniform mat4 u_ViewMatrix;
            uniform mat4 u_ModelMatrix;
            out vec3 v_Normal;
            out %s v_Texcoord;
            
            void main() { 
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
                v_Texcoord = a_Texcoord;
                
                mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
            }
        """ % (a_dtype, a_dtype)
    
    def get_color_fshader(self):
        """返回使用颜色的片元着色器源码"""
        
        return """
            #version 330 core
            
            in vec4 v_Color;
            in vec3 v_Normal;
            uniform vec3 u_LightDir; // 定向光方向
            uniform vec3 u_SkyColor; // 天空光线颜色
            uniform vec3 u_GroundColor; // 地面光线颜色
            uniform int u_Picked; // 拾取标志
            
            void main() { 
                float costheta = dot(v_Normal, normalize(u_LightDir)) * 0.5 + 0.5;
                if (!gl_FrontFacing) costheta *= 0.5;
                
                vec3 rgb = mix(u_GroundColor, u_SkyColor, costheta) * v_Color.rgb;
                if (u_Picked == 0)
                    gl_FragColor = vec4(rgb, v_Color.a);
                else
                    gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), v_Color.a);
            } 
        """
    
    def get_texture_fshader(self):
        """返回使用纹理的片元着色器源码"""
        
        if ttype == GL_TEXTURE_1D:
            a_dtype = 'float'
            u_dtype = 'sampler1D'
            f_name = 'texture1D'
        elif ttype == GL_TEXTURE_2D:
            a_dtype = 'vec2'
            u_dtype = 'sampler2D'
            f_name = 'texture2D'
        elif ttype == GL_TEXTURE_2D_ARRAY:
            a_dtype = 'vec3'
            u_dtype = 'sampler2DArray'
            f_name = 'texture2DArray'
        elif ttype == GL_TEXTURE_3D:
            a_dtype = 'vec3'
            u_dtype = 'sampler3D'
            f_name = 'texture3D'
        
        return """
            #version 330 core
            
            in vec3 v_Normal;
            in %s v_Texcoord;
            uniform %s u_Texture;
            uniform vec3 u_LightDir; // 定向光方向
            uniform vec3 u_SkyColor; // 天空光线颜色
            uniform vec3 u_GroundColor; // 地面光线颜色
            uniform int u_Picked; // 拾取标志
            
            void main() { 
                float costheta = dot(v_Normal, normalize(u_LightDir)) * 0.5 + 0.5;
                if (!gl_FrontFacing) costheta *= 0.5;
                vec4 color = %s(u_Texture, v_Texcoord);
                vec3 rgb = mix(u_GroundColor, u_SkyColor, costheta) * color.rgb;
                
                if (u_Picked == 0)
                    gl_FragColor = vec4(rgb, color.a);
                else
                    gl_FragColor = vec4(min(rgb*1.5, vec3(1.0)), color.a);
            } 
        """ % (a_dtype, u_dtype, f_name)
        
class SphereLight:
    """球谐光照情景模式"""
    
    def __init__(self, key=0, factor=0.8):
        """构造函数"""
        
        self.factor = factor                # 反射衰减因子
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
        ][key]
    
    def get_model(self, gltype, vs, **kwds):
        """返回模型对象"""
        
        indices = kwds.get('indices')
        color = kwds.get('color')
        normal = kwds.get('normal')
        texture = kwds.get('texture')
        texcoord = kwds.get('texcoord')
        
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull')
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        
        if color is None:
            vshader = self.get_texture_vshader(texture.ttype)
            fshader = self.get_texture_fshader(texture.ttype)
            
            m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
            m.set_texcoord('a_Texcoord', texcoord)
            m.add_texture('u_Texture', texture)
        else:
            vshader = self.get_color_vshader()
            fshader = self.get_color_fshader()
            
            m = wxModel.Model(gltype, vshader, fshader, visible=visible, opacity=opacity, inside=inside)
            m.set_color('a_Color', color)
        
        m.set_vertex('a_Position', vs, indices)
        m.set_normal('a_Normal', normal)
        m.set_picked('u_Picked')
        m.set_argument('u_ScaleFactor', self.factor)
        m.set_proj_matrix('u_ProjMatrix')
        m.set_view_matrix('u_ViewMatrix')
        m.set_model_matrix('u_ModelMatrix', transform)
        m.set_cull_mode(cull)
        m.set_fill_mode(fill)
        m.set_slide(slide)
        
        return m
    
    def get_color_vshader(self):
        """返回使用颜色的顶点着色器源码"""
        
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
                mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
                v_Color = a_Color;
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
            }
        """
    
    def get_texture_vshader(self):
        """返回使用纹理的顶点着色器源码"""
        
        if ttype == GL_TEXTURE_1D:
            a_dtype = 'float'
        elif ttype == GL_TEXTURE_2D:
            a_dtype = 'vec2'
        elif ttype == GL_TEXTURE_2D_ARRAY or ttype == GL_TEXTURE_3D:
            a_dtype = 'vec3'
        
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
                mat4 NormalMatrix = transpose(inverse(u_ModelMatrix));
                v_Normal = normalize(vec3(NormalMatrix * vec4(a_Normal, 1.0)));
                v_Texcoord = a_Texcoord;
                gl_Position = u_ProjMatrix * u_ViewMatrix * u_ModelMatrix * a_Position; 
            }
        """ % (a_dtype, a_dtype)
    
    def get_color_fshader(self):
        """返回使用颜色的片元着色器源码"""
        
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
    
    def get_texture_fshader(self):
        """返回使用纹理的片元着色器源码"""
        
        if ttype == GL_TEXTURE_1D:
            a_dtype = 'float'
            u_dtype = 'sampler1D'
            f_name = 'texture1D'
        elif ttype == GL_TEXTURE_2D:
            a_dtype = 'vec2'
            u_dtype = 'sampler2D'
            f_name = 'texture2D'
        elif ttype == GL_TEXTURE_2D_ARRAY:
            a_dtype = 'vec3'
            u_dtype = 'sampler2DArray'
            f_name = 'texture2DArray'
        elif ttype == GL_TEXTURE_3D:
            a_dtype = 'vec3'
            u_dtype = 'sampler3D'
            f_name = 'texture3D'
        
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
        """ % (a_dtype, self.parameter, u_dtype, f_name)
        
        