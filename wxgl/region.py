# -*- coding: utf-8 -*-
#
# MIT License
# 
# Copyright (c) 2020 天元浪子
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
WxGL是一个基于pyopengl的三维数据可视化库

WxGL以wx为显示后端，提供matplotlib风格的交互绘图模式
同时，也可以和wxpython无缝结合，在wx的窗体上绘制三维模型
"""


import wx
import uuid
import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo
from PIL import Image
from scipy.spatial.transform import Rotation as sstr

from . import util


class WxGLRegion:
    """GL视区类"""
    
    def __init__(self, scene, rid, box, fixed=False):
        """构造函数
        
        scene       - 所属场景对象
        rid         - 唯一标识
        box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
        fixed       - 是否锁定旋转缩放
        """
        
        self.scene = scene
        self.rid = rid
        self.box = box
        self.fixed = fixed
        
        self.cm = self.scene.cm                                 # 调色板对象
        self.fm = self.scene.fm                                 # 字体管理对象
        self.assembly = dict()                                  # 绘图指令集
        self.models = dict()                                    # 模型字典
        self.textures = list()                                  # 纹理对象列表
        self.buffers = dict()                                   # 缓冲区字典
        self.grid_tick = None                                   # 网格和刻度容器
        self.grid_tick_kwds = dict()                            # 网格和刻度容器的默认参数
        self.timers = dict()                                    # 定时器、计数器管理
        
        self.r_x = [1e10, -1e10]                                # 数据在x轴上的动态范围
        self.r_y = [1e10, -1e10]                                # 数据在y轴上的动态范围
        self.r_z = [1e10, -1e10]                                # 数据在z轴上的动态范围
        self.scale = 1.0                                        # 模型缩放比例
        self.translate = np.array([0,0,0], dtype=np.float)      # 模型位移量
      
    def reset_box(self, box, clear=False):
        """重置视区大小
        
        box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
        clear       - 是否清空所有模型
        """
        
        self.box = box
        
        if clear:
            for name in list(self.models.keys()):
                self.delete_model(name)
            
            self.r_x = [1e10, -1e10]
            self.r_y = [1e10, -1e10]
            self.r_z = [1e10, -1e10]
            self.scale = 1.0
            self.translate = np.array([0,0,0], dtype=np.float)
            
            self.grid_tick = None
            self.grid_tick_kwds = dict()
    
    def set_data_range(self, r_x=None, r_y=None, r_z=None):
        """设置坐标轴范围
        
        r_x         - 二元组，x坐标轴范围
        r_y         - 二元组，y坐标轴范围
        r_z         - 二元组，z坐标轴范围
        """
        
        if r_x and r_x[0] < self.r_x[0]:
            self.r_x[0] = r_x[0]
        if r_x and r_x[1] > self.r_x[1]:
            self.r_x[1] = r_x[1]
        
        if r_y and r_y[0] < self.r_y[0]:
            self.r_y[0] = r_y[0]
        if r_y and r_y[1] > self.r_y[1]:
            self.r_y[1] = r_y[1]
        
        if r_z and r_z[0] < self.r_z[0]:
            self.r_z[0] = r_z[0]
        if r_z and r_z[1] > self.r_z[1]:
            self.r_z[1] = r_z[1]
        
        self.scale = 2/max(self.r_x[1]-self.r_x[0], self.r_y[1]-self.r_y[0], self.r_z[1]-self.r_z[0])
        self.translate = (-sum(self.r_x)/2, -sum(self.r_y)/2, -sum(self.r_z)/2)
    
    def get_model_view(self, box):
        """返回模型视图的缩放比例和位移"""
        
        if self.fixed:
            w, h = box[1]-box[0], box[3]-box[2]
            dx, dy = self.r_x[1]-self.r_x[0]+0.2, self.r_y[1]-self.r_y[0]+0.2
            return min(w/dx, h/dy), np.array([0,0,0], dtype=np.float)
        else:
            return self.scale, self.translate
    
    def refresh(self):
        """更新视区显示"""
        
        wx.CallAfter(self.scene.Refresh, False)
    
    def delete_model(self, name):
        """删除模型
        
        name        - 模型名
        """
        
        if name in self.models:
            for item in self.models[name]['component']:
                self.buffers[item['args'][0]].delete()
                if item['genre'] in ['line', 'point', 'surface', 'mesh']:
                    self.buffers[item['args'][1]].delete()
                if item['genre'] == 'surface' and item['args'][5]:
                    self.delete_texture(item['args'][5])
            del self.models[name]
        
        if name in self.assembly:
            del self.assembly[name]
    
    def add_model(self, name, genre, args, visible=True, light=None):
        """增加模型"""
        
        if name not in self.models:
            self.models.update({name:{'display':visible, 'component':list()}})
        
        self.models[name]['component'].append({
            'genre': genre,
            'args': args
        })
        
        if name not in self.assembly:
            self.assembly.update({name:{'display':visible, 'component':list()}})
        
        if not light is None:
            self._set_light(name, GL_LIGHT0, GL_AMBIENT, light)
            self._set_light(name, GL_LIGHT0, GL_DIFFUSE, light)
            self._enable_env(name, GL_LIGHTING)
        
        if genre == 'surface' or genre == 'mesh':
            vertices_id, indices_id, v_type, gl_type, mode, texture, program = args
            
            if mode:
                self._set_polygon_mode(name, mode)
            
            self._add_elements(name, vertices_id, indices_id, v_type, gl_type, texture=texture, program=program)
            
            if mode and mode != 'FCBC':
                self._set_polygon_mode(name, 'FCBC')
        elif genre == 'line':
            vertices_id, indices_id, v_type, gl_type, width, stipple, program = args
            
            if width:
                self._set_line_width(name, width)
            if stipple:
                self._enable_env(name, GL_LINE_STIPPLE)
                self._set_line_stipple(name, stipple)
            
            self._add_elements(name, vertices_id, indices_id, v_type, gl_type, texture=None, program=program)
            
            if width and width != 1.0:
                self._set_line_width(name, 1.0)
            if stipple:
                self._disable_env(name, GL_LINE_STIPPLE)
                if stipple != (1, 0xFFFF):
                    self._set_line_stipple(name, stipple)
        elif genre == 'point':
            vertices_id, indices_id, v_type, gl_type, size, program = args
            
            if size:
                self._set_point_size(name, size)
            
            self._add_elements(name, vertices_id, indices_id, v_type, gl_type, texture=None, program=program)
            
            if size and size != 1.0:
                self._set_point_size(name, size)
        elif genre == 'text':
            pixels_id, rows, cols, pos = args
            self._add_pixels(name, pixels_id, rows, cols, pos)
        
        if not light is None:
            self._disable_env(name, GL_LIGHTING)
        
        self.refresh()
    
    def show_model(self, name):
        """显示模型
        
        name        - 模型名
        """
        
        if name in self.assembly:
            self.assembly[name]['display'] = True
        if name in self.models:
            self.models[name]['display'] = True
    
    def hide_model(self, name):
        """隐藏模型
        
        name        - 模型名
        """
        
        if name in self.assembly:
            self.assembly[name]['display'] = False
        if name in self.models:
            self.models[name]['display'] = False
    
    def set_model_visible(self, name, display):
        """设置模型可见性"""
        
        if display:
            self.show_model(name)
        else:
            self.hide_model(name)
    
    def get_model_visible(self, name):
        """返回模型可见性"""
        
        return name in self.assembly and self.assembly[name]['display']
    
    def show_models(self, names):
        """显示多个模型"""
        
        for name in names:
           self.show_model(name)
    
    def hide_models(self, names):
        """隐藏多个模型"""
        
        for name in names:
           self.hide_model(name)
    
    def create_texture(self, img, alpha=True):
        """创建纹理对象
        
        img         - 纹理图片文件名或数据
        alpha       - 是否使用透明通道
        """
        
        assert isinstance(img, (np.ndarray, str)), u'参数类型错误'
        
        mode = 'RGBA' if alpha else 'RGB'
        if isinstance(img, np.ndarray):
            im = Image.fromarray(np.uint8(img), mode=mode)
        else:
            im = Image.open(img)
        
        ix, iy, image = im.size[0], im.size[1], im.tobytes('raw', mode, 0, -1)
        
        mode = GL_RGBA if alpha else GL_RGB
        self.textures.append(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, self.textures[-1])
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, mode, ix, iy, 0, mode, GL_UNSIGNED_BYTE, image)
        
        return self.textures[-1]
    
    def delete_texture(self, texture):
        """删除纹理对象"""
        
        try:
            #glDeleteTextures(self.textures.pop(self.textures.index(texture)))
            pass
        except:
            pass
    
    def _wxglLightfv(self, args):
        """glLightfv"""
        
        glLightfv(*args)
    
    def _wxglPolygonMode(self, args):
        """glPolygonMode"""
        
        glPolygonMode(*args)
    
    def _wxglPointSize(self, args):
        """glPointSize"""
        
        glPointSize(*args)
    
    def _wxglLineWidth(self, args):
        """glLineWidth"""
        
        glLineWidth(*args)
    
    def _wxglLineStipple(self, args):
        """glLineStipple"""
        
        glLineStipple(*args[0])
    
    def _wxglDrawTexture(self, args):
        """glDrawElements us texture"""
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, args[4])
        self._wxglDrawElements((*args[:-1], None))
        glDisable(GL_TEXTURE_2D)
    
    def _wxglDrawElements(self, args):
        """glDrawElements"""
        
        vertices_vbo, indices_ebo, v_type, gl_type, program = args
        
        if program:
            shaders.glUseProgram(program[0])
            glUniform1f(program[1], self.timers[program[2]]['counter'])
        
        vertices_vbo.bind()
        glInterleavedArrays(v_type, 0, None)
        indices_ebo.bind()
        glDrawElements(gl_type, int(indices_ebo.size/4), GL_UNSIGNED_INT, None) 
        vertices_vbo.unbind()
        indices_ebo.unbind()
        
        if program:
            shaders.glUseProgram(0)
    
    def _wxglDrawPixels(self, args):
        """glDrawElements"""
        
        scale = np.array([1.0,1.0,1.0], dtype=np.float)
        glPixelZoom(scale[0], scale[1])
        glDepthMask(GL_FALSE)
        glRasterPos3fv(args[3]*scale)
        args[0].bind()
        glDrawPixels(args[2], args[1], GL_RGBA, GL_UNSIGNED_BYTE, None)
        args[0].unbind()
        glDepthMask(GL_TRUE)
    
    def _wxglEnable(self, args):
        """glEnable"""
        
        glEnable(*args)
    
    def _wxglDisable(self, args):
        """glDisable"""
        
        glDisable(*args)
    
    def _create_vbo(self, vertices):
        """创建顶点缓冲区对象"""
        
        id = uuid.uuid1().hex
        buff = vbo.VBO(vertices)
        self.buffers.update({id: buff})
        
        return id
        
    def _create_ebo(self, indices):
        """创建索引缓冲区对象"""
        
        id = uuid.uuid1().hex
        buff = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)
        self.buffers.update({id: buff})
        
        return id
        
    def _create_pbo(self, pixels):
        """创建像素缓冲区对象"""
        
        id = uuid.uuid1().hex
        buff = vbo.VBO(pixels, target=GL_PIXEL_UNPACK_BUFFER)
        self.buffers.update({id: buff})
        
        return id
        
    def _enable_env(self, name, env):
        """开启功能
        
        env         - 指定功能项
        """
        
        self.assembly[name]['component'].append({'cmd':self._wxglEnable, 'args':[env]})
        
    def _disable_env(self, name, env):
        """关闭功能
        
        env         - 指定功能项
        """
        
        self.assembly[name]['component'].append({'cmd':self._wxglDisable, 'args':[env]})
        
    def _set_light(self, name, n_light, pname, value):
        """设置灯光参数
        
        name        - 模型名
        n_light     - 灯光编号
        pname       - 参数名
        value       - 参数值
        """
        
        self.assembly[name]['component'].append({'cmd':self._wxglLightfv, 'args':[n_light, pname, value]})
        
    def _set_polygon_mode(self, name, mode):
        """设置多边形显示模式
        
        name        - 模型名
        mode        - 显示模式
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        """
        
        if mode == 'FCBC':
            self.assembly[name]['component'].append({'cmd':self._wxglPolygonMode, 'args':[GL_FRONT_AND_BACK, GL_FILL]})
        elif mode == 'FLBL':
            self.assembly[name]['component'].append({'cmd':self._wxglPolygonMode, 'args':[GL_FRONT_AND_BACK, GL_LINE]})
        elif mode == 'FCBL':
            self.assembly[name]['component'].append({'cmd':self._wxglPolygonMode, 'args':[GL_FRONT, GL_FILL]})
            self.assembly[name]['component'].append({'cmd':self._wxglPolygonMode, 'args':[GL_BACK, GL_LINE]})
        elif mode == 'FLBC':
            self.assembly[name]['component'].append({'cmd':self._wxglPolygonMode, 'args':[GL_FRONT, GL_LINE]})
            self.assembly[name]['component'].append({'cmd':self._wxglPolygonMode, 'args':[GL_BACK, GL_FILL]})
        
    def _set_point_size(self, name, size):
        """设置点的大小
        
        name        - 模型名
        size        - 点的大小
        """
        
        self.assembly[name]['component'].append({'cmd':self._wxglPointSize, 'args':[size]})
        
    def _set_line_width(self, name, width):
        """设置线宽
        
        name        - 模型名
        width       - 线宽
        """
        
        self.assembly[name]['component'].append({'cmd':self._wxglLineWidth, 'args':[width]})
        
    def _set_line_stipple(self, name, stipple):
        """设置线型
        
        name        - 模型名
        stipple     - 线型
        """
        
        self.assembly[name]['component'].append({'cmd':self._wxglLineStipple, 'args':[stipple]})
        
    def _create_text(self, text, size, color, family, weight):
        """生成文字的像素集、高度、宽度
        
        text        - Unicode字符串
        size        - 文本大小，整形
        color       - 文本颜色，list或numpy.ndarray类型，shape=(3,)
        family      - 字体（系统支持的）
        weight      - 粗细，light/bold/normal
        """
        
        font_file = self.fm.get_font_file(family=family, weight=weight)
        pixels = self.fm.get_text_pixels(text, size, font_file)
        rows, cols = pixels.shape
        color = color*255
        color = np.tile(color, (rows*cols, 1)).astype(np.uint8)
        pixels = pixels.reshape(-1, 1)
        pixels = np.hstack((color, pixels)).reshape(rows, cols, 4)
        pixels = pixels[::-1].ravel()
        pixels_id = self._create_pbo(pixels)
        
        return pixels_id, rows, cols
        
    def _create_point_or_lLine(self, v, c, uvw, rand):
        """生成点或线段的顶点集、索引集、顶点数组类型
        
        v           - 顶点坐标集，numpy.ndarray类型，shape=(cols,3)
        c           - 顶点颜色集，numpy.ndarray类型，shape=(3,)|(4,)|(cols,3)|(cols,4)
        uvw         - 顶点着色器所用的顶点速度分量
        rand        - 顶点着色器所用的顶点初始随机位置
        """
        
        if c.ndim == 1:
            c = np.tile(c, (v.shape[0], 1))
        
        if isinstance(uvw, np.ndarray) and isinstance(rand, np.ndarray):
            if c.shape[-1] == 3:
                c = np.hstack((c, np.tile(np.array([1]), (c.shape[0], 1))))
            v_type = GL_T2F_C4F_N3F_V3F
            vertices = np.hstack((rand, c, uvw, v)).astype(np.float32)
        else:
            if c.shape[-1] == 3:
                v_type = GL_C3F_V3F
                vertices = np.hstack((c,v)).astype(np.float32)
            else:
                v_type = GL_C4F_N3F_V3F
                n = np.tile(np.array([1.0, 1.0, 1.0]), v.shape[0])
                n = n.reshape(-1, 3)
                vertices = np.hstack((c,n,v)).astype(np.float32)
        
        vertices_id = self._create_vbo(vertices)
        indices_id = self._create_ebo(np.array(list(range(v.shape[0])), dtype=np.int))
        
        return vertices_id, indices_id, v_type
        
    def _create_surface(self, v, c, t, gl_type):
        """生成曲面的顶点集、索引集、顶点数组类型
        
        v           - 顶点坐标集，numpy.ndarray类型，shape=(clos,3)
        c           - 顶点的颜色集，None或numpy.ndarray类型，shape=(3|4,)|(cols,3|4)
        t           - 顶点的纹理坐标集，None或numpy.ndarray类型，shape=(cols,2)
        gl_type     - 绘制方法，GL_QUADS|GL_TRIANGLES
        """
        
        n = np.tile(np.array([0.0, 0.0, 0.0]), (v.shape[0],1))
        if gl_type == GL_QUADS:
            for i in range(0, v.shape[0], 4):
                ab, ac = v[i+1]-v[i], v[i+2]-v[i]
                nk = np.cross(ac, ab)
                n[i] += nk
                n[i+1] += nk
                n[i+2] += nk
                n[i+3] += nk
        elif gl_type == GL_TRIANGLES:
            for i in range(0, v.shape[0], 3):
                ab, ac = v[i+1]-v[i], v[i+2]-v[i]
                nk = np.cross(ac, ab)
                n[i] += nk
                n[i+1] += nk
                n[i+2] += nk
        elif gl_type == GL_QUAD_STRIP:
            for i in range(2, v.shape[0], 2):
                ab, ac = v[i-1]-v[i-2], v[i+1]-v[i-2]
                nk = np.cross(ac, ab)
                n[i] += nk
                n[i+1] += nk
                n[i-1] += nk
                n[i-2] += nk
        elif gl_type == GL_TRIANGLE_STRIP:
            for i in range(2, v.shape[0], 2):
                ab, ac = v[i-1]-v[i-2], v[i]-v[i-2]
                nk = np.cross(ac, ab)
                n[i] += nk
                n[i-1] += nk
                n[i-2] += nk
                
                ab, ac = v[i]-v[i-1], v[i+1]-v[i-1]
                nk = np.cross(ac, ab)
                n[i] += nk
                n[i-1] += nk
                n[i+1] += nk
        elif gl_type == GL_TRIANGLE_FAN or gl_type == GL_POLYGON:
            for i in range(2, v.shape[0]):
                ab, ac = v[i-1]-v[0], v[i]-v[0]
                nk = np.cross(ab, ac)
                n[0] += nk
                n[i] += nk
                n[i-1] += nk
        
        if isinstance(t, np.ndarray):
            if isinstance(c, np.ndarray):
                if c.ndim == 1:
                    c = np.tile(c[:3], (v.shape[0], 1))
                else:
                    c = c[:,:3]
                
                v_type = GL_T2F_C3F_V3F
                vertices = np.hstack((t,c,v)).astype(np.float32)
            else:
                v_type = GL_T2F_V3F
                vertices = np.hstack((t,v)).astype(np.float32)
        else:
            if c.ndim == 1:
                c = np.tile(c, (v.shape[0], 1))
            
            if c.shape[-1] == 3:
                v_type = GL_C3F_V3F
                vertices = np.hstack((c,v)).astype(np.float32)
            else:
                v_type = GL_C4F_N3F_V3F
                vertices = np.hstack((c,util.normalize(n),v)).astype(np.float32)
        
        vertices_id = self._create_vbo(vertices)
        indices_id = self._create_ebo(np.array(list(range(v.shape[0])), dtype=np.int))
        
        return vertices_id, indices_id, v_type
        
    def _create_mesh(self, x, y, z, c, gl_type):
        """生成网格的顶点集、索引集、顶点数组类型
        
        x           - 顶点的x坐标集，numpy.ndarray类型，shape=(rows,cols)
        y           - 顶点的y坐标集，numpy.ndarray类型，shape=(rows,cols)
        z           - 顶点的z坐标集，numpy.ndarray类型，shape=(rows,cols)
        c           - 顶点的颜色集，None或numpy.ndarray类型，shape=(3|4,)|(rows,cols,3|4)
        gl_type     - 绘制方法，GL_QUADS|GL_TRIANGLES
        """
        
        rows, cols = z.shape
        v = np.dstack((x,y,z)).reshape(-1,3)
        n = np.tile(np.array([0.0, 0.0, 0.0]), (v.shape[0],1))
        
        if gl_type == GL_QUADS:
            indices = list()
            for i in range(1, rows):
                for j in range(1, cols):
                    i_a, i_b, i_c, i_d = (i-1)*cols+j-1, i*cols+j-1, i*cols+j, (i-1)*cols+j
                    indices += [i_a, i_b, i_c, i_d]
                    
                    ab, ac = v[i_b]-v[i_a], v[i_c]-v[i_a]
                    nk = np.cross(ac, ab)
                    n[i_a] += nk
                    n[i_b] += nk
                    n[i_c] += nk
                    n[i_d] += nk
                    
        elif gl_type == GL_TRIANGLES:
            indices = list()
            for i in range(1, rows):
                for j in range(1,cols):
                    i_a, i_b, i_c, i_d, i_e, i_f = (i-1)*cols+j-1, i*cols+j-1, i*cols+j, i*cols+j, (i-1)*cols+j, (i-1)*cols+j-1
                    indices += [i_a, i_b, i_c, i_d, i_e, i_f]
                    
                    ab, ac = v[i_b]-v[i_a], v[i_c]-v[i_a]
                    nk = np.cross(ac, ab)
                    n[i_a] += nk
                    n[i_b] += nk
                    n[i_c] += nk
                    
                    ab, ac = v[i_e]-v[i_d], v[i_f]-v[i_d]
                    nk = np.cross(ac, ab)
                    n[i_d] += nk
                    n[i_e] += nk
                    n[i_f] += nk
        
        if c.ndim == 1:
            c = np.tile(c, (rows*cols, 1))
        else:
            c = c.reshape(-1, c.shape[-1])
        
        if c.shape[-1] == 3:
            v_type = GL_C3F_V3F
            vertices = np.hstack((c,v)).astype(np.float32)
        else:
            v_type = GL_C4F_N3F_V3F
            vertices = np.hstack((c,util.normalize(n),v)).astype(np.float32)
        
        vertices_id = self._create_vbo(vertices)
        indices_id = self._create_ebo(np.array(indices, dtype=np.int))
        
        return vertices_id, indices_id, v_type
        
    def _create_capsule(self, v, i, c):
        """生成囊体的的顶点集、索引集、顶点数组类型
        
        v           - 顶点集，numpy.ndarray类型，shape=(n,3)
        i           - 索引集，numpy.ndarray类型，shape=(x,3)
        c           - 顶点的颜色集，None或numpy.ndarray类型，shape=(3|4,)|(n,3|4)
        """
        
        n = np.tile(np.array([0.0, 0.0, 0.0]), (v.shape[0],1))
        indices = i.astype(np.int)
        for i_a, i_b, i_c in indices:
            ab, ac = v[i_b]-v[i_a], v[i_c]-v[i_a]
            nk = np.cross(ab, ac)
            n[i_a] += nk
            n[i_b] += nk
            n[i_c] += nk
        
        if c.shape[-1] == 3:
            v_type = GL_C3F_V3F
            vertices = np.hstack((c,v)).astype(np.float32)
        else:
            v_type = GL_C4F_N3F_V3F
            vertices = np.hstack((c,util.normalize(n),v)).astype(np.float32)
        
        vertices_id = self._create_vbo(vertices)
        indices_id = self._create_ebo(indices.ravel())
        
        return vertices_id, indices_id, v_type
        
    def _add_elements(self, name, vertices_id, indices_id, v_type, gl_type, texture=None, program=None):
        """生成绘制图元命令
        
        name        - 模型名
        vertices_id - 顶点VBO的id
        indices_id  - 索引EBO的id
        v_type      - 顶点混合数组类型
        gl_type     - 绘制方法
        texture     - 纹理对象
        """
        
        vertices_vbo = self.buffers[vertices_id]
        indices_ebo = self.buffers[indices_id]
        if texture:
            self.assembly[name]['component'].append({'cmd':self._wxglDrawTexture, 'args':[vertices_vbo, indices_ebo, v_type, gl_type, texture]})
        else:
            self.assembly[name]['component'].append({'cmd':self._wxglDrawElements, 'args':[vertices_vbo, indices_ebo, v_type, gl_type, program]})
        
    def _add_pixels(self, name, pixels_id, rows, cols, pos):
        """生成绘制像素命令
        
        name        - 模型名
        pixels_id   - 像素VBO的id
        rows        - 像素行数
        cols        - 像素列数
        pos         - 位置
        """
        
        pixels_pbo = self.buffers[pixels_id]
        self.assembly[name]['component'].append({'cmd':self._wxglDrawPixels, 'args':[pixels_pbo, rows, cols, pos]})
    
    def _get_tick_label(self, v_min, v_max, ks=(1, 2, 2.5, 3, 4, 5), s_min=4, s_max=8, endpoint=True):
        """返回合适的Colorbar标注值
        
        v_min       - 数据最小值
        v_max       - 数据最大值
        ks          - 分段选项
        s_min       - 分段数最小值
        s_max       - 分段数最大值
        endpoint    - 是否包含v_min和v_max
        """
        
        r = v_max-v_min
        tmp = np.array([[abs(float(('%E'%(r/i)).split('E')[0])-k) for i in range(s_min,s_max+1)] for k in ks])
        i, j = divmod(tmp.argmin(), tmp.shape[1])
        step, steps = ks[i], j+s_min
        step *= pow(10, int(('%E'%(r/steps)).split('E')[1]))
        
        result = list()
        v = int(v_min/step)*step
        while v <= v_max:
            if v >= v_min:
                result.append(round(v, 6))
            v += step
        
        if len(result) > 3:
            if endpoint:
                if result[0] > v_min:
                    result.insert(0, v_min)
                if result[-1] < v_max:
                    result.append(v_max)
                
                if result[1]-result[0] < (result[2]-result[1])*0.25:
                    result.remove(result[1])
                if result[-1]-result[-2] < (result[-2]-result[-3])*0.25:
                    result.remove(result[-2])
            else:
                if result[0] == v_min or result[0]-v_min < (result[1]-result[0])*0.25:
                    result.remove(result[0])
                if result[-1] == v_max or v_max-result[-1] < (result[-1]-result[-2])*0.25:
                    result.remove(result[-1])
        
        return result
    
    def text2d(self, text, size=32, color=None, pos=[0,0,0], **kwds):
        """绘制2D文字
        
        text        - 文本字符串
        size        - 文字大小，整型
        color       - 文本颜色
                        None表示使用场景对象scene的style风格提供的文本颜色
                        预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
                        浮点型的元组或列表，值域范围：[0,1]，长度：3
                        numpy.ndarray类型，shape=(3,)
        pos         - 文本位置，元组、列表或numpy数组
        kwds        - 关键字参数
                        align       - 兼容text3d()，并无实际意义
                        valign      - 兼容text3d()，并无实际意义
                        family      - （系统支持的）字体
                        weight      - light/bold/normal分别表示字体的轻、重、正常（默认）
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
        """
        
        assert isinstance(pos, (tuple, list, np.ndarray)), '期望参数pos类型是元组、列表或numpy数组'
        
        for key in kwds:
            if key not in ['align', 'valign', 'family', 'weight', 'name', 'inside', 'visible']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        align = kwds.get('align', 'center')
        valign = kwds.get('valign', 'middle')
        weight = kwds.get('weight', 'normal')
        family = kwds.get('family', None)
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        
        if color:
            color = self.cm.color2c(color, alpha=None)
        else:
            color = np.array(self.scene.tc)
        
        if isinstance(pos, (tuple, list)):
            pos = np.array(pos, dtype=np.float)
        
        if inside:
            self.set_data_range((pos[0],pos[0]), (pos[1],pos[1]), (pos[2],pos[2]))
        
        pixels_id, rows, cols = self._create_text(text, size, color, family, weight)
        self.add_model(name, 'text', [pixels_id, rows, cols, pos], visible=visible)
    
    def text3d(self, text, size=32, color=None, pos=[0,0,0], **kwds):
        """绘制3D文字
        
        text        - 文本字符串
        size        - 文字大小，整型
        color       - 文本颜色
                        None表示使用场景对象scene的style风格提供的文本颜色
                        预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
                        浮点型的元组或列表，值域范围：[0,1]，长度：3
                        numpy.ndarray类型，shape=(3,)
        pos         - 文本位置，元组、列表或numpy数组
        kwds        - 关键字参数
                        align       - left/right/center分别表示左对齐、右对齐、居中（默认）
                        valign      - top/bottom/middle分别表示上对齐、下对齐、垂直居中（默认）
                        family      - （系统支持的）字体
                        weight      - light/bold/normal分别表示字体的轻、重、正常（默认）
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
        """
        
        assert isinstance(pos, (tuple, list, np.ndarray)), '期望参数pos类型是元组、列表或numpy数组'
        
        for key in kwds:
            if key not in ['align', 'valign', 'family', 'weight', 'name', 'inside', 'visible']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        align = kwds.get('align', 'center')
        valign = kwds.get('valign', 'middle')
        weight = kwds.get('weight', 'normal')
        family = kwds.get('family', None)
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        
        if isinstance(pos, (tuple, list)):
            pos = np.array(pos, dtype=np.float)
        
        if isinstance(color,(str, tuple, list, np.ndarray)):
            color = self.cm.color2c(color, alpha=None)
        else:
            color = np.array(self.scene.tc)
        
        font_file = self.fm.get_font_file(family=family, weight=weight)
        pixels = self.fm.get_text_pixels(text, 64, font_file)
        rows, cols = pixels.shape
        
        x = np.ones(pixels.shape)*color[0]*255
        y = np.ones(pixels.shape)*color[1]*255
        z = np.ones(pixels.shape)*color[2]*255
        im = np.dstack((x,y,z,pixels)).astype(np.uint8)
        
        k = 1/256
        w, h = k*size*cols/rows, k*size
        
        if self.fixed:
            head = 'y+'
        else:
            head = self.scene.head
        
        if head == 'x+':
            if align == 'center':
                pos[2] -= w/2
            elif align == 'right':
                pos[2] -= w
            
            if valign == 'middle':
                pos[0] += h/2
            elif valign == 'bottom':
                pos[0] += h
            
            vs = [[pos[0],pos[1],pos[2]], [pos[0]-h,pos[1],pos[2]], [pos[0]-h,pos[1],pos[2]+w], [pos[0],pos[1],pos[2]+w]]
        elif head == 'y+':
            if align == 'center':
                pos[0] -= w/2
            elif align == 'right':
                pos[0] -= w
            
            if valign == 'middle':
                pos[1] += h/2
            elif valign == 'bottom':
                pos[1] += h
            
            vs = [[pos[0],pos[1],pos[2]], [pos[0],pos[1]-h,pos[2]], [pos[0]+w,pos[1]-h,pos[2]], [pos[0]+w,pos[1],pos[2]]]
        else:
            if align == 'center':
                pos[1] -= w/2
            elif align == 'right':
                pos[1] -= w
            
            if valign == 'middle':
                pos[2] += h/2
            elif valign == 'bottom':
                pos[2] += h
            
            vs = [[pos[0],pos[1],pos[2]], [pos[0],pos[1],pos[2]-h], [pos[0],pos[1]+w,pos[2]-h], [pos[0],pos[1]+w,pos[2]]]
        
        texture = self.create_texture(im)
        texcoord =  np.array([[0,1],[0,0],[1,0],[1,1]])
        self.surface(np.array(vs), texcoord=texcoord, texture=texture, name=name, inside=inside, visible=visible)
        
    def point(self, vs, color, size=None, **kwds):
        """绘制点
        
        vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
        color       - 顶点或顶点集颜色
                        预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
                        浮点型的元组或列表，值域范围：[0,1]，长度：3
                        numpy.ndarray类型，shape=(3,)|(4,)|(n,3)|(n,4)
        size        - 点的大小，整数，None表示使用当前设置
        kwds        - 关键字参数
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
                        program     - 着色器程序
                        slide       - 是否作为动画播放的帧
        """
        
        for key in kwds:
            if key not in ['name', 'inside', 'visible', 'program', 'slide']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        program = kwds.get('program', None)
        slide = kwds.get('slide', False)
        
        if inside:
            r_x = (np.nanmin(vs[:,0]),np.nanmax(vs[:,0]))
            r_y = (np.nanmin(vs[:,1]),np.nanmax(vs[:,1]))
            r_z = (np.nanmin(vs[:,2]),np.nanmax(vs[:,2]))
            self.set_data_range(r_x, r_y, r_z)
        
        if program:
            uvw, rand = self.timers[program[2]]['uvw'], self.timers[program[2]]['rand']
        else:
            uvw, rand = None, None
        
        if slide:
            self.scene.add_slide_page(self, name)
            visible = False
        
        color = self.cm.color2c(color, shape=vs.shape[:-1])
        vertices_id, indices_id, v_type = self._create_point_or_lLine(vs, color, uvw, rand)
        self.add_model(name, 'point', [vertices_id, indices_id, v_type, GL_POINTS, size, program], visible=visible)
        
    def line(self, vs, color, method='SINGLE', width=None, stipple=None, **kwds):
        """绘制线段
        
        vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
        color       - 顶点或顶点集颜色
                        预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
                        浮点型的元组或列表，值域范围：[0,1]，长度：3
                        numpy.ndarray类型，shape=(3,)|(4,)|(n,3)|(n,4)
        method      - 绘制方法
                        'MULTI'     - 线段
                        'SINGLE'    - 连续线段
                        'LOOP'      - 闭合线段
        width       - 线宽，0.0~10.0之间，None表示使用当前设置
        stipple     - 线型，整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None表示使用当前设置
        kwds        - 关键字参数
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
                        program     - 着色器程序
                        slide       - 是否作为动画播放的帧
        """
        
        for key in kwds:
            if key not in ['name', 'inside', 'visible', 'program', 'slide']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        program = kwds.get('program', None)
        slide = kwds.get('slide', False)
        
        if inside:
            r_x = (np.nanmin(vs[:,0]),np.nanmax(vs[:,0]))
            r_y = (np.nanmin(vs[:,1]),np.nanmax(vs[:,1]))
            r_z = (np.nanmin(vs[:,2]),np.nanmax(vs[:,2]))
            self.set_data_range(r_x, r_y, r_z)
        
        if program:
            uvw, rand = self.timers[program[2]]['uvw'], self.timers[program[2]]['rand']
        else:
            uvw, rand = None, None
        
        if slide:
            self.scene.add_slide_page(self, name)
            visible = False
        
        color = self.cm.color2c(color, shape=vs.shape[:-1])
        gl_type = {'MULTI':GL_LINES, 'SINGLE':GL_LINE_STRIP, 'LOOP':GL_LINE_LOOP}[method]
        vertices_id, indices_id, v_type = self._create_point_or_lLine(vs, color, uvw, rand)
        self.add_model(name, 'line', [vertices_id, indices_id, v_type, gl_type, width, stipple, program], visible=visible)
    
    def surface(self, vs, color=None, texcoord=None, texture=None, method='Q', mode=None, **kwds):
        """绘制曲面
        
        vs          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
        color       - 顶点或顶点集颜色
                        None表示仅使用纹理
                        预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
                        浮点型的元组或列表，值域范围：[0,1]，长度：3
                        numpy.ndarray类型，shape=(3|4,)|(n,3|4)
        texcoord    - 顶点的纹理坐标集，numpy.ndarray类型，shape=(n,2)
        texture     - 2D纹理对象
        method      - 绘制方法
                        'Q'         - 四边形
                                        0--3 4--7
                                        |  | |  |
                                        1--2 5--6
                        'T'         - 三角形
                                        0--2 3--5
                                         \/   \/
                                          1    4
                        'Q+'        - 边靠边的连续四边形
                                       0--2--4
                                       |  |  |
                                       1--3--5
                        'T+'        - 边靠边的连续三角形
                                       0--2--4
                                        \/_\/_\
                                         1  3  5
                        'F'         - 扇形
                        'P'         - 多边形
        mode        - 显示模式
                        None        - 使用当前设置
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        kwds        - 关键字参数
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
                        program     - 着色器程序
                        light       - 材质灯光颜色，None表示关闭材质灯光
                        slide       - 是否作为动画播放的帧
        """
        
        for key in kwds:
            if key not in ['name', 'inside', 'visible', 'program', 'light', 'slide']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        program = kwds.get('program', None)
        light = kwds.get('light', None)
        slide = kwds.get('slide', False)
        
        if inside:
            r_x = (np.nanmin(vs[:,0]),np.nanmax(vs[:,0]))
            r_y = (np.nanmin(vs[:,1]),np.nanmax(vs[:,1]))
            r_z = (np.nanmin(vs[:,2]),np.nanmax(vs[:,2]))
            self.set_data_range(r_x, r_y, r_z)
        
        if isinstance(color,(str, tuple, list, np.ndarray)):
            color = self.cm.color2c(color, shape=vs.shape[:-1])
        
        if color is None and (texcoord is None or texture is None):
            color = self.cm.color2c(self.scene.tc, shape=vs.shape[:-1])
        
        if slide:
            self.scene.add_slide_page(self, name)
            visible = False
        
        gl_type = {'Q':GL_QUADS, 'T':GL_TRIANGLES, 'Q+':GL_QUAD_STRIP, 'T+':GL_TRIANGLE_STRIP, 'F':GL_TRIANGLE_FAN, 'P':GL_POLYGON}[method]
        vertices_id, indices_id, v_type = self._create_surface(vs, color, texcoord, gl_type)
        self.add_model(name, 'surface', [vertices_id, indices_id, v_type, gl_type, mode, texture, program], visible=visible, light=light)
    
    def mesh(self, xs, ys, zs, color, method='Q', mode=None, **kwds):
        """绘制网格
        
        xs          - 顶点集的x坐标集，numpy.ndarray类型，shape=(rows,cols)
        ys          - 顶点集的y坐标集，numpy.ndarray类型，shape=(rows,cols)
        zs          - 顶点集的z坐标集，numpy.ndarray类型，shape=(rows,cols)
        color       - 顶点或顶点集颜色
                        预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
                        浮点型的元组或列表，值域范围：[0,1]，长度：3
                        numpy.ndarray类型，shape=(3|4,)|(rows,cols,3|4)
        method      - 绘制方法：
                        'Q'         - 四边形
                        'T'         - 三角形
        mode        - 显示模式
                        None        - 使用当前设置
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        kwds        - 关键字参数
                        blc         - 边框的颜色，None表示无边框
                        blw         - 边框宽度
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
                        program     - 着色器程序
                        light       - 材质灯光颜色，None表示关闭材质灯光
                        slide       - 是否作为动画播放的帧
                        name        - 模型名
        """
        
        for key in kwds:
            if key not in ['blc', 'blw', 'name', 'inside', 'visible', 'program', 'light', 'slide']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        blc = kwds.get('inside', None)
        blw = kwds.get('inside', 1.0)
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        program = kwds.get('program', None)
        light = kwds.get('light', None)
        slide = kwds.get('slide', False)
        
        if inside:
            self.set_data_range((np.nanmin(xs),np.nanmax(xs)), (np.nanmin(ys),np.nanmax(ys)), (np.nanmin(zs),np.nanmax(zs)))
        
        if slide:
            self.scene.add_slide_page(self, name)
            visible = False
        
        color = self.cm.color2c(color, shape=zs.shape)
        gl_type = {'Q':GL_QUADS, 'T':GL_TRIANGLES}[method]
        vertices_id, indices_id, v_type = self._create_mesh(xs, ys, zs, color, gl_type)
        self.add_model(name, 'mesh', [vertices_id, indices_id, v_type, gl_type, mode, None, program], visible=visible, light=light)
        
        if isinstance(blc, (str, list, tuple, np.ndarray)):
            top_x = xs[0,1:-1]
            top_y = ys[0,1:-1]
            top_z = zs[0,1:-1]

            bottom_x = xs[-1,1:-1][::-1]
            bottom_y = ys[-1,1:-1][::-1]
            bottom_z = zs[-1,1:-1][::-1]

            right_x = xs[:,-1]
            right_y = ys[:,-1]
            right_z = zs[:,-1]

            left_x = xs[:,0][::-1]
            left_y = ys[:,0][::-1]
            left_z = zs[:,0][::-1]

            x = np.hstack((top_x, right_x, bottom_x, left_x))
            y = np.hstack((top_y, right_y, bottom_y, left_y))
            z = np.hstack((top_z, right_z, bottom_z, left_z))
            v = np.dstack((x, y, z))[0]
            
            self.line(v, blc, method='LOOP', width=blw, name=name, inside=inside, visible=visible)
        
    def sphere(self, center, radius, color, mode='FLBL', slices=60, **kwds):
        """绘制球体
        
        center      - 球心坐标，元组、列表或numpy数组
        radius      - 半径，浮点型
        color       - 表面颜色
        mode        - 显示模式
                        None        - 使用当前设置
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        slices      - 锥面分片数（数值越大越精细）
        kwds        - 关键字参数
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
                        light       - 材质灯光开关
        """
        
        for key in kwds:
            if key not in ['name', 'inside', 'visible', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        light = kwds.get('light', True)
        
        lats, lons = np.mgrid[-np.pi/2:np.pi/2:complex(0,slices/2+1), 0:2*np.pi:complex(0,slices+1)]
        xs = radius*np.cos(lats)*np.cos(lons) + center[0]
        ys = radius*np.cos(lats)*np.sin(lons) + center[1]
        zs = radius*np.sin(lats) + center[2]
        
        if light:
            light = self.cm.color2c(color)
        else:
            light = None
        
        self.mesh(xs, ys, zs, color, method='T', mode=mode, name=name, inside=inside, visible=visible, light=light)        
        
    def cube(self, center, side, color, mode='FLBL', **kwds):
        """绘制六面体
        
        center      - 中心坐标，元组、列表或numpy数组
        side        - 棱长，整型、浮点型，或长度为3的元组、列表、numpy数组
        color       - 顶点或顶点集颜色
                        预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
                        浮点型的元组或列表，值域范围：[0,1]，长度：3
                        numpy.ndarray类型，shape=(3|4,)|(rows,cols,3|4)
        mode        - 显示模式
                        None        - 使用当前设置
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        kwds        - 关键字参数
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
                        light       - 材质灯光开关
        """
        
        for key in kwds:
            if key not in ['name', 'inside', 'visible', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        light = kwds.get('light', True)
        
        if isinstance(side, (tuple, list, np.ndarray)):
            x, y, z = side
        elif isinstance(side, (int, float)):
            x, y, z = side, side, side
        else:
            raise ValueError("期望参数side是整型、浮点型，或长度为3的元组、列表、numpy数组")
        
        vs_front = np.array(((x/2,-y/2,-z/2),(x/2,-y/2,z/2),(x/2,y/2,z/2),(x/2,y/2,-z/2))) + center
        vs_back = np.array(((-x/2,y/2,-z/2),(-x/2,y/2,z/2),(-x/2,-y/2,z/2),(-x/2,-y/2,-z/2))) + center
        vs_top = np.array(((-x/2,y/2,z/2),(x/2,y/2,z/2),(x/2,-y/2,z/2),(-x/2,-y/2,z/2))) + center
        vs_bottom = np.array(((-x/2,-y/2,-z/2),(x/2,-y/2,-z/2),(x/2,y/2,-z/2),(-x/2,y/2,-z/2))) + center
        vs_left = np.array(((x/2,-y/2,z/2),(x/2,-y/2,-z/2),(-x/2,-y/2,-z/2),(-x/2,-y/2,z/2))) + center
        vs_right = np.array(((-x/2,y/2,z/2),(-x/2,y/2,-z/2),(x/2,y/2,-z/2),(x/2,y/2,z/2))) + center
        
        if light:
            light = self.cm.color2c(color)
        else:
            loght = None
        
        self.surface(vs_front, color=color, mode=mode, name=name, inside=inside, visible=visible, light=light)
        self.surface(vs_back, color=color, mode=mode, name=name, inside=inside, visible=visible, light=light)
        self.surface(vs_top, color=color, mode=mode, name=name, inside=inside, visible=visible, light=light)
        self.surface(vs_bottom, color=color, mode=mode, name=name, inside=inside, visible=visible, light=light)
        self.surface(vs_left, color=color, mode=mode, name=name, inside=inside, visible=visible, light=light)
        self.surface(vs_right, color=color, mode=mode, name=name, inside=inside, visible=visible, light=light)
    
    def cone(self, center, spire, radius, color, slices=50, mode='FCBC', **kwds):
        """绘制圆锥体
        
        center      - 锥底圆心坐标，元组、列表或numpy数组
        spire       - 锥尖坐标，元组、列表或numpy数组
        radius      - 锥底半径，浮点型
        color       - 圆锥颜色
                        预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
                        浮点型的元组或列表，值域范围：[0,1]，长度：3
                        numpy.ndarray类型，shape=(3,)
        slices      - 锥面分片数（数值越大越精细）
        mode        - 显示模式
                        None        - 使用当前设置
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        kwds        - 关键字参数
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
                        light       - 材质灯光开关
        """
        
        for key in kwds:
            if key not in ['name', 'inside', 'visible', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        light = kwds.get('light', True)
        
        if not isinstance(spire, np.ndarray):
            spire = np.array(spire)
        
        if not isinstance(center, np.ndarray):
            center = np.array(center)
        
        rotator, h = util.rotate(spire-center)
        
        theta = np.linspace(0, 2*np.pi, slices+1)
        xs = np.cos(theta) * radius
        ys = np.sin(theta) * radius
        zs = np.zeros_like(theta)
        
        v_cone = np.dstack((np.hstack((0, xs)), np.hstack((0, ys)), np.hstack((h, zs))))[0]
        v_ground = np.dstack((np.hstack((0, xs)), np.hstack((0, ys)), np.hstack((0, zs))))[0]
        v_cone = rotator.apply(v_cone) + center
        v_ground = rotator.apply(v_ground) + center
        
        if light:
            light = self.cm.color2c(color)
        else:
            loght = None
        
        self.surface(v_cone, color, method='F', mode=mode, name=name, inside=inside, visible=visible, light=light)
        self.surface(v_ground, color, method='F', mode=mode, name=name, inside=inside, visible=visible, light=light)
    
    def cylinder(self, v_top, v_bottom, radius, color, slices=50, mode='FCBC', **kwds):
        """绘制圆柱体
        
        v_top       - 圆柱上端面的圆心坐标，元组、列表或numpy数组
        v_bottom    - 圆柱下端面的圆心坐标，元组、列表或numpy数组
        radius      - 圆柱半径，浮点型
        color       - 圆柱颜色
                        预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
                        浮点型的元组或列表，值域范围：[0,1]，长度：3
                        numpy.ndarray类型，shape=(3|4,)|(2,3|4)
        slices      - 圆柱面分片数（数值越大越精细）
        mode        - 显示模式
                        None        - 使用当前设置
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        kwds        - 关键字参数
                        headface    - 是否显示圆柱端面
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
        """
        
        for key in kwds:
            if key not in ['headface', 'name', 'inside', 'visible']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        headface = kwds.get('headface', True)
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        
        color = self.cm.color2c(color, shape=(2,))
        if (color[0] == color[1]).all():
            light = color[0]
        else:
            light = None
        
        if not isinstance(v_top, np.ndarray):
            v_top = np.array(v_top)
        if not isinstance(v_bottom, np.ndarray):
            v_bottom = np.array(v_bottom)
        
        rotator, h = util.rotate(v_bottom-v_top)
        
        theta = np.linspace(0, 2*np.pi, slices+1)
        xs = np.cos(theta) * radius
        ys = np.sin(theta) * radius
        zs0 = np.zeros_like(theta)
        zs1 = np.ones_like(theta) * h
        
        vv, cc = list(), list()
        for i in range(len(theta)):
            vv += [
                [xs[i], ys[i], zs1[i]],
                [xs[i], ys[i], zs0[i]]
            ]
            cc += [color[1], color[0]]
        
        vv = rotator.apply(np.array(vv)) + v_top
        cc = np.vstack(cc)
        self.surface(vv, cc, method='Q+', mode=mode, name=name, inside=inside, visible=visible, light=light)
        
        if headface:
            hf0 = np.dstack((np.hstack((0, xs)), np.hstack((0, ys)), np.hstack((0, zs0))))[0]
            hf1 = np.dstack((np.hstack((0, xs)), np.hstack((0, ys)), np.hstack((h, zs1))))[0]
            
            hf0 = rotator.apply(hf0) + v_top
            hf1 = rotator.apply(hf1) + v_top
            
            self.surface(hf0, color[0], method='F', mode=mode, name=name, inside=inside, visible=visible, light=light)
            self.surface(hf1, color[1], method='F', mode=mode, name=name, inside=inside, visible=visible, light=light)
    
    def pipe(self, vs, radius, color, slices=36, mode='FCBC', **kwds):
        """绘制圆管线
        
        vs          - 圆管中心点坐标集，numpy.ndarray类型，shape=(n,3)
        radius      - 圆管半径，浮点型
        color       - 圆管颜色
                        预定义的颜色，或形如'#FF0000'的十六进制表示的颜色
                        浮点型的元组或列表，值域范围：[0,1]，长度：3
                        numpy.ndarray类型，shape=(3|4,)|(n,3|4)
        slices      - 圆管面分片数（数值越大越精细）
        mode        - 显示模式
                        None        - 使用当前设置
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        kwds        - 关键字参数
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
        """
        
        for key in kwds:
            if key not in ['headface', 'name', 'inside', 'visible']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        headface = kwds.get('headface', True)
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        
        cs = self.cm.color2c(color, shape=vs.shape[:1])
        theta = np.linspace(0, 2*np.pi, slices+1)
        xs = np.cos(theta) * radius
        ys = np.sin(theta) * radius
        zs0 = np.zeros_like(theta)
        
        if isinstance(color, np.ndarray) and color.ndim == 2:
            light = None
        else:
            light = cs[0]
        
        for k in range(vs.shape[0])[:-1]:
            v0, v1 = vs[k], vs[k+1]
            rotator, h = util.rotate(v1-v0)
            zs1 = np.ones_like(theta) * h
            
            if k == 0:
                 base = rotator.apply([[xs[i], ys[i], zs0[i]] for i in range(len(theta))]) + v0
            curr = rotator.apply([[xs[i], ys[i], zs1[i]] for i in range(len(theta))]) + v0
            
            vv, cc = list(), list()
            for i in range(len(theta)):
                vv += [base[i], curr[i]]
                cc += [cs[k], cs[k+1]]
            
            base = curr
            vv = np.vstack(vv)
            cc = np.vstack(cc)
            self.surface(vv, cc, method='Q+', mode=mode, name=name, inside=inside, visible=visible, light=light)
    
    def capsule(self, data, threshold, color, r_x=None, r_y=None, r_z=None, mode='FLBL', **kwds):
        """绘制囊（三维等值面）
        
        data        - 数据集，numpy.ndarray类型，shape=(layers,rows,cols)
        threshold   - 阈值，浮点型
        color       - 表面颜色
        r_x         - x的动态范围，元组
        r_y         - y的动态范围，元组
        r_z         - z的动态范围，元组
        mode        - 显示模式
                        None        - 使用当前设置
                        'FCBC'      - 前后面填充颜色FCBC
                        'FLBL'      - 前后面显示线条FLBL
                        'FCBL'      - 前面填充颜色，后面显示线条FCBL
                        'FLBC'      - 前面显示线条，后面填充颜色FLBC
        kwds        - 关键字参数
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
                        light       - 材质灯光开关
        """
        
        for key in kwds:
            if key not in ['name', 'inside', 'visible', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        light = kwds.get('light', True)
        
        data = np.rollaxis(data, 2)
        data = np.rollaxis(data, 2, 1)
        
        vs, idxs = util.find_capsule(data[:,:,::-1], threshold)
        cs = self.cm.color2c(color, shape=vs.shape[:1])
        
        if light:
            light = cs[0]
        else:
            light = None
        
        if r_x and r_y and r_z:
            xs, ys, zs = vs[:,0], vs[:,1], vs[:,2]
            x0, x1 = 0, data.shape[0]
            y0, y1 = 0, data.shape[1]
            z0, z1 = 0, data.shape[2]
            
            xs = r_x[0] + (xs-x0)*(r_x[1]-r_x[0])/(x1-x0)
            ys = r_y[0] + (ys-y0)*(r_y[1]-r_y[0])/(y1-y0)
            zs = r_z[0] + (zs-z0)*(r_z[1]-r_z[0])/(z1-z0)
            vs = np.stack((xs, ys, zs), axis=1)
        
        if inside:
            r_x = (np.nanmin(vs[:,0]),np.nanmax(vs[:,0]))
            r_y = (np.nanmin(vs[:,1]),np.nanmax(vs[:,1]))
            r_z = (np.nanmin(vs[:,2]),np.nanmax(vs[:,2]))
            self.set_data_range(r_x, r_y, r_z)
        
        gl_type = GL_TRIANGLES
        vertices_id, indices_id, v_type = self._create_capsule(vs, idxs, cs)
        self.add_model(name, 'mesh', [vertices_id, indices_id, v_type, gl_type, mode, None, None], visible=visible, light=light)
    
    def volume(self, data, x=None, y=None, z=None, method='Q', **kwds):
        """绘制体数据
        
        data        - 顶点的颜色集，numpy.ndarray类型，shape=(layers,rows,cols,4)
        x           - 顶点的x坐标集，numpy.ndarray类型，shape=(rows,cols)。缺省则使用volume的2轴索引构造
        y           - 顶点的y坐标集，numpy.ndarray类型，shape=(rows,cols)。缺省则使用volume的1轴索引构造
        z           - 顶点的z坐标集，numpy.ndarray类型，shape=(layers,)。缺省则使用volume的0轴索引构造
        method      - 绘制方法：
                        'Q'         - 四边形
                        'T'         - 三角形
        kwds        - 关键字参数
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
        """
        
        for key in kwds:
            if key not in ['name', 'inside', 'visible']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        
        assert isinstance(data, np.ndarray) and data.ndim == 4, '期望参数volume类型是一个4维的numpy数组'
        assert data.shape[-1] == 4, '期望参数volume是RBGA类型的数据'
        
        
        mode = 'FCBC'
        d, h, w  = data.shape[0], data.shape[1], data.shape[2]
        
        if not isinstance(x, np.ndarray) and x == None:
            x = np.tile(np.arange(w, dtype=np.float), (h,1)) 
            x *= 2.0/max(d,h,w)
            x -= x.max()/2.0
        
        if not isinstance(y, np.ndarray) and y == None:
            y = np.arange(h, dtype=np.float).repeat(w).reshape((h,w)) 
            y *= 2.0/max(d,h,w)
            y -= y.max()/2.0
        
        if not isinstance(z, np.ndarray) and z == None:
            z = np.arange(d, dtype=np.float) 
            z *= 2.0/max(d,h,w)
            z -= z.max()/2.0
        
        for i in range(d):
            self.mesh(x, y, z[i]*np.ones_like(x), data[i], method=method, mode=mode, name=name, inside=inside, visible=visible)
        
        z_h = z.repeat(h).reshape((-1, h))
        for i in range(w):
            x_h = np.tile(x[:,i], (d,1))
            y_h = np.tile(y[:,i], (d,1))
            c_h = data[:d,:,i]
            self.mesh(x_h, y_h, z_h, c_h, method=method, mode=mode, name=name, inside=inside, visible=visible)
        
        z_v = z.repeat(w).reshape((-1, w))
        for i in range(h):
            x_v = np.tile(x[i,:], (d,1))
            y_v = np.tile(y[i,:], (d,1))
            c_v = data[:d,i,:]
            self.mesh(x_v, y_v, z_v, c_v, method=method, mode=mode, name=name, inside=inside, visible=visible)
    
    def coordinate(self, length=1.0, xlabel=None, ylabel=None, zlabel=None, **kwds):
        """绘制坐标轴
        
        length      - 坐标轴半轴长度，从-length到length
        xlabel      - x轴标注
        ylabel      - y轴标注
        zlabel      - z轴标注
        kwds        - 关键字参数
                        half        - 是否画半轴
                        slices      - 锥面分片数（数值越大越精细）
                        label_size  - 标注文本的字号
                        name        - 模型名
                        inside      - 是否更新数据动态范围
                        visible     - 是否显示
        """
        
        for key in kwds:
            if key not in ['half', 'label_size', 'slices', 'name', 'inside', 'visible']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        half = kwds.get('half', False)
        slices = kwds.get('slices', 32)
        label_size = kwds.get('label_size', 40)
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        
        if half:
            start = 0
        else:
            start = -length
        
        c_x, c_y, c_z = [1,0,0], [0,1,0], [0,0,1]
        v = np.array([[start,0,0],[0.8*length,0,0],[0,start,0],[0,0.8*length,0],[0,0,start],[0,0,0.8*length]])
        c = np.array([c_x, c_x, c_y, c_y, c_z, c_z])
        radius = 0.03*length
        
        self.line(v, c, method='MULTI', name=name, inside=inside, visible=visible)
        self.cone(np.array([0.8*length,0,0]), np.array([length,0,0]), radius, c_x, slices=slices, name=name, inside=inside, visible=visible)
        self.cone(np.array([0,0.8*length,0]), np.array([0,length,0]), radius, c_y, slices=slices, name=name, inside=inside, visible=visible)
        self.cone(np.array([0,0,0.8*length]), np.array([0,0,length]), radius, c_z, slices=slices, name=name, inside=inside, visible=visible)
        
        if xlabel:
            self.text2d(xlabel, size=label_size, color=c_x, pos=[length,0,0], name=name, inside=inside, visible=visible)
        if ylabel:
            self.text2d(ylabel, size=label_size, color=c_y, pos=[0,length,0], name=name, inside=inside, visible=visible)
        if zlabel:
            self.text2d(zlabel, size=label_size, color=c_z, pos=[0,0,length], name=name, inside=inside, visible=visible)
    
    def colorbar(self, drange, cmap, loc='right', **kwds):
        """绘制colorBar 
        
        drange      - 值域范围，tuple类型
        cmap        - 调色板名称
        loc         - 位置，top|bottom|left|right
        kwds        - 关键字参数
                        length          - ColorBar所在视区的长边长度，默认短边长度为1
                        subject         - 标题
                        subject_size    - 标题字号
                        label_size      - 标注字号
                        label_format    - 标注格式化所用lambda函数
                        tick_line       - 刻度线长度
                        endpoint        - 刻度是否包含值域范围的两个端点值
                        name            - 模型名
                        inside          - 是否更新数据动态范围
                        visible         - 是否显示
        """
        
        assert isinstance(drange, (tuple, list)) and len(drange) == 2, '期望参数drange是长度为2的元组或列表'
        assert loc in ('top','bottom','left','right'), '期望参数loc为top|bottom|left|right其中之一'
        
        for key in kwds:
            if key not in ('length','subject','subject_size','label_size','label_format','tick_line','endpoint','name','inside', 'visible'):
                raise KeyError('不支持的关键字参数：%s'%key)
        
        length = kwds.get('length', 2)
        subject = kwds.get('subject', None)
        subject_size = kwds.get('subject_size', 48)
        label_size = kwds.get('label_size', 32)
        label_format = kwds.get('label_format', str)
        tick_line = kwds.get('tick_line', 0.1)
        endpoint = kwds.get('endpoint', False)
        name = kwds.get('name', uuid.uuid1().hex)
        inside = kwds.get('inside', True)
        visible = kwds.get('visible', True)
        
        if subject:
            if loc == 'left':
                self.text3d(subject, size=subject_size, pos=(0.1,length-0.1,0), valign='top', name=name, inside=inside, visible=visible)
                x_min, x_max = 0.1, 0.6
                y_min, y_max = -length, length-0.5
            elif loc == 'right':
                self.text3d(subject, size=subject_size, pos=(-0.1,length-0.1,0), valign='top', name=name, inside=inside, visible=visible)
                x_min, x_max = -0.6, -0.1
                y_min, y_max = -length, length-0.5
            elif loc == 'bottom':
                self.text3d(subject, size=subject_size, pos=(0,0.7,0), valign='top', name=name, inside=inside, visible=visible)
                x_min, x_max = -length, length
                y_min, y_max = -0.1, 0.4
            else:
                self.text3d(subject, size=subject_size, pos=(0,0.7,0), valign='top', name=name, inside=inside, visible=visible)
                x_min, x_max = -length, length
                y_min, y_max = -0.1, 0.4
        else:
            if loc == 'left':
                x_min, x_max = 0.1, 0.6
                y_min, y_max = -length, length
            elif loc == 'right':
                x_min, x_max = -0.6, -0.1
                y_min, y_max = -length, length
            else:
                x_min, x_max = -length, length
                y_min, y_max = 0, 0.5
        
        
        v_min, v_max = drange
        xs, ys, zs, cs = list(), list(), list(), list()
        tick_label = self._get_tick_label(v_min, v_max, endpoint=endpoint)
        
        for k, rgb in self.cm.cms[cmap]:
            if loc == 'left' or loc == 'right':
                y = y_min + k*(y_max-y_min)
                xs.append([x_min, x_max])
                ys.append([y, y])
            else:
                x = x_min + k*(x_max-x_min)
                xs.append([x, x])
                ys.append([y_min, y_max])
            zs.append([0.0, 0.0])
            cs.append([rgb, rgb])
        
        xs, ys, zs, cs = np.array(xs), np.array(ys), np.array(zs), np.array(cs)/255.0
        self.mesh(xs, ys, zs, color=cs, mode='FCBC', name=name, inside=inside, visible=visible)
        
        for tick in tick_label:
            if loc == 'left':
                y = y_min + (y_max-y_min)*(tick-v_min)/(v_max-v_min)
                p0, p1, p3 = (x_min, y, 0), (x_min-tick_line, y, 0), (x_min-tick_line-0.01, y, 0)
                align, valign = 'right', 'middle'
            elif loc == 'right':
                y = y_min + (y_max-y_min)*(tick-v_min)/(v_max-v_min)
                p0, p1, p3 = (x_max, y, 0), (x_max+tick_line, y, 0), (x_max+tick_line+0.01, y, 0)
                align, valign = 'left', 'middle'
            else:
                x = x_min + (x_max-x_min)*(tick-v_min)/(v_max-v_min)
                p0, p1, p3 = (x, y_min, 0), (x, y_min-tick_line, 0), (x, y_min-tick_line-0.01, 0)
                align, valign = 'center', 'top'
            
            mark = label_format(tick)
            self.line(np.array((p0, p1)), color=self.scene.tc, name=name, inside=inside, visible=visible)
            self.text3d(mark, size=label_size, pos=p3, align=align, valign=valign, name=name, inside=inside, visible=visible)
        
    def hide_ticks(self):
        """隐藏刻度网格"""
        
        for item in ('xy_zmin', 'xy_zmax', 'zx_ymin', 'zx_ymax', 'yz_xmin', 'yz_xmax'):
            self.delete_model('%s_%s'%(self.grid_tick['gid'], item))
        for ax in self.grid_tick['tick']:
            for key in self.grid_tick['tick'][ax]:
                for name in  self.grid_tick['tick'][ax][key]:
                    self.delete_model(name)
        
        self.grid_tick = None
        self.refresh()
        
    def ticks(self, **kwds):
        """绘制网格和刻度
        
        kwds        - 关键字参数
                        segment_min     - 标注最少分段数量
                        segment_max     - 标注最多分段数量
                        label_2D3D      - 标注试用2D或3D文字
                        label_size      - 标注字号
                        xlabel_format   - x轴标注格式化所用lambda函数
                        ylabel_format   - y轴标注格式化所用lambda函数
                        zlabel_format   - z轴标注格式化所用lambda函数
                        
        """
        
        assert self.r_x[0] <= self.r_x[1] and self.r_y[0] <= self.r_y[1] and self.r_z[0] <= self.r_z[1], '当前没有模型，无法显示网格和刻度'
        
        for key in kwds:
            if key not in ['segment_min', 'segment_max', 'label_2D3D', 'label_size', 'xlabel_format', 'ylabel_format', 'zlabel_format']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        segment_min = kwds.get('segment_min', 5)
        segment_max = kwds.get('segment_max', 8)
        label_2D3D = kwds.get('label_2D3D', '3D')
        label_size = kwds.get('label_size', 16)
        label_precision = kwds.get('label_precision', '%.2f')
        xlabel_format = kwds.get('xlabel_format', str)
        ylabel_format = kwds.get('ylabel_format', str)
        zlabel_format = kwds.get('zlabel_format', str)
        t_size = label_size/self.scale
        
        self.grid_tick_kwds = kwds
        if self.grid_tick:
            self.hide_ticks()
        
        head = 'y+' if self.fixed else self.scene.head
        gid = uuid.uuid1().hex
        draw_text = self.text3d if label_2D3D == '3D' else self.text2d
        
        self.grid_tick = {
            'gid': gid,
            'tick': {
                'x':{'y0z0':list(), 'y0z1':list(), 'y1z0':list(), 'y1z1':list()},
                'y':{'z0x0':list(), 'z0x1':list(), 'z1x0':list(), 'z1x1':list()},
                'z':{'x0y0':list(), 'x0y1':list(), 'x1y0':list(), 'x1y1':list()}
            }
        }
        
        x_values = self._get_tick_label(self.r_x[0], self.r_x[1], s_min=segment_min, s_max=segment_max, endpoint=False)
        y_values = self._get_tick_label(self.r_y[0], self.r_y[1], s_min=segment_min, s_max=segment_max, endpoint=False)
        z_values = self._get_tick_label(self.r_z[0], self.r_z[1], s_min=segment_min, s_max=segment_max, endpoint=False)
        
        xx = [self.r_x[0]] + x_values + [self.r_x[1]]
        yy = [self.r_y[0]] + y_values + [self.r_y[1]]
        zz = [self.r_z[0]] + z_values + [self.r_z[1]]
        
        xy_x, xy_y = np.meshgrid(xx, yy)
        xy_zmin = np.ones_like(xy_x) * self.r_z[0]
        xy_zmax = np.ones_like(xy_x) * self.r_z[1]
        
        zx_x, zx_z = np.meshgrid(xx, zz)
        zx_ymin = np.ones_like(zx_x) * self.r_y[0]
        zx_ymax = np.ones_like(zx_x) * self.r_y[1]
        
        yz_y, yz_z = np.meshgrid(yy, zz)
        yz_xmin = np.ones_like(yz_y) * self.r_x[0]
        yz_xmax = np.ones_like(yz_y) * self.r_x[1]
        
        self.mesh(xy_x, xy_y, xy_zmin, color='blue', mode='FLBL', name='%s_xy_zmin'%gid, inside=False)
        self.mesh(xy_x, xy_y, xy_zmax, color='blue', mode='FLBL', name='%s_xy_zmax'%gid, inside=False)
        
        self.mesh(zx_x, zx_ymin, zx_z, color='green', mode='FLBL', name='%s_zx_ymin'%gid, inside=False)
        self.mesh(zx_x, zx_ymax, zx_z, color='green', mode='FLBL', name='%s_zx_ymax'%gid, inside=False)
        
        self.mesh(yz_xmin, yz_y, yz_z, color='red', mode='FLBL', name='%s_yz_xmin'%gid, inside=False)
        self.mesh(yz_xmax, yz_y, yz_z, color='red', mode='FLBL', name='%s_yz_xmax'%gid, inside=False)
        
        for x in x_values:
            y0z0, y0z1, y1z0, y1z1 = uuid.uuid1().hex, uuid.uuid1().hex, uuid.uuid1().hex, uuid.uuid1().hex
            self.grid_tick['tick']['x']['y0z0'].append(y0z0)
            self.grid_tick['tick']['x']['y0z1'].append(y0z1)
            self.grid_tick['tick']['x']['y1z0'].append(y1z0)
            self.grid_tick['tick']['x']['y1z1'].append(y1z1)
            
            if head == 'z+':
                p0, align0, valign0 = (x, self.r_y[0], self.r_z[0]-0.05/self.scale), 'right', 'top'
                p1, align1, valign1 = (x, self.r_y[0], self.r_z[1]+0.05/self.scale), 'right', 'bottom'
                p2, align2, valign2 = (x, self.r_y[1], self.r_z[0]-0.05/self.scale), 'left', 'top'
                p3, align3, valign3 = (x, self.r_y[1], self.r_z[1]+0.05/self.scale), 'left', 'bottom'
            elif head == 'y+':
                p0, align0, valign0 = (x, self.r_y[0]-0.05/self.scale, self.r_z[0]), 'center', 'top'
                p1, align1, valign1 = (x, self.r_y[0]-0.05/self.scale, self.r_z[1]), 'center', 'top'
                p2, align2, valign2 = (x, self.r_y[1]+0.05/self.scale, self.r_z[0]), 'center', 'bottom'
                p3, align3, valign3 = (x, self.r_y[1]+0.05/self.scale, self.r_z[1]), 'center', 'bottom'
            else:
                p0, align0, valign0 = (x, self.r_y[0], self.r_z[0]-0.05/self.scale), 'right', 'middle'
                p1, align1, valign1 = (x, self.r_y[0], self.r_z[1]+0.05/self.scale), 'left', 'middle'
                p2, align2, valign2 = (x, self.r_y[1], self.r_z[0]-0.05/self.scale), 'right', 'middle'
                p3, align3, valign3 = (x, self.r_y[1], self.r_z[1]+0.05/self.scale), 'left', 'middle'
            
            tick = xlabel_format(x)
            draw_text(tick, pos=p0, size=t_size, align=align0, valign=valign0, name=y0z0, inside=False)
            draw_text(tick, pos=p1, size=t_size, align=align1, valign=valign1, name=y0z1, inside=False)
            draw_text(tick, pos=p2, size=t_size, align=align2, valign=valign2, name=y1z0, inside=False)
            draw_text(tick, pos=p3, size=t_size, align=align3, valign=valign3, name=y1z1, inside=False)
        
        for y in y_values:
            z0x0, z0x1, z1x0, z1x1 = uuid.uuid1().hex, uuid.uuid1().hex, uuid.uuid1().hex, uuid.uuid1().hex
            self.grid_tick['tick']['y']['z0x0'].append(z0x0)
            self.grid_tick['tick']['y']['z0x1'].append(z0x1)
            self.grid_tick['tick']['y']['z1x0'].append(z1x0)
            self.grid_tick['tick']['y']['z1x1'].append(z1x1)
            
            if head == 'z+':
                p0, align0, valign0 = (self.r_x[0], y, self.r_z[0]-0.05/self.scale), 'center', 'top'
                p1, align1, valign1 = (self.r_x[1], y, self.r_z[0]-0.05/self.scale), 'center', 'top'
                p2, align2, valign2 = (self.r_x[0], y, self.r_z[1]+0.05/self.scale), 'center', 'bottom'
                p3, align3, valign3 = (self.r_x[1], y, self.r_z[1]+0.05/self.scale), 'center', 'bottom'
            elif head == 'y+':
                p0, align0, valign0 = (self.r_x[0]-0.05/self.scale, y, self.r_z[0]), 'right', 'middle'
                p1, align1, valign1 = (self.r_x[1]+0.05/self.scale, y, self.r_z[0]), 'left', 'middle'
                p2, align2, valign2 = (self.r_x[0]-0.05/self.scale, y, self.r_z[1]), 'right', 'middle'
                p3, align3, valign3 = (self.r_x[1]+0.05/self.scale, y, self.r_z[1]), 'left', 'middle'
            else:
                p0, align0, valign0 = (self.r_x[0]-0.05/self.scale, y, self.r_z[0]), 'right', 'top'
                p1, align1, valign1 = (self.r_x[1]+0.05/self.scale, y, self.r_z[0]), 'right', 'bottom'
                p2, align2, valign2 = (self.r_x[0]-0.05/self.scale, y, self.r_z[1]), 'left', 'top'
                p3, align3, valign3 = (self.r_x[1]+0.05/self.scale, y, self.r_z[1]), 'left', 'bottom'
            
            tick = ylabel_format(y)
            draw_text(tick, pos=p0, size=t_size, align=align0, valign=valign0, name=z0x0, inside=False)
            draw_text(tick, pos=p1, size=t_size, align=align1, valign=valign1, name=z0x1, inside=False)
            draw_text(tick, pos=p2, size=t_size, align=align2, valign=valign2, name=z1x0, inside=False)
            draw_text(tick, pos=p3, size=t_size, align=align3, valign=valign3, name=z1x1, inside=False)
        
        for z in z_values:
            x0y0, x0y1, x1y0, x1y1 = uuid.uuid1().hex, uuid.uuid1().hex, uuid.uuid1().hex, uuid.uuid1().hex
            self.grid_tick['tick']['z']['x0y0'].append(x0y0)
            self.grid_tick['tick']['z']['x0y1'].append(x0y1)
            self.grid_tick['tick']['z']['x1y0'].append(x1y0)
            self.grid_tick['tick']['z']['x1y1'].append(x1y1)
            
            if head == 'z+':
                p0, align0, valign0 = (self.r_x[0], self.r_y[0]-0.05/self.scale, z), 'right', 'middle'
                p1, align1, valign1 = (self.r_x[0], self.r_y[1]+0.05/self.scale, z), 'left', 'middle'
                p2, align2, valign2 = (self.r_x[1], self.r_y[0]-0.05/self.scale, z), 'right', 'middle'
                p3, align3, valign3 = (self.r_x[1], self.r_y[1]+0.05/self.scale, z), 'left', 'middle'
            elif head == 'y+':
                p0, align0, valign0 = (self.r_x[0], self.r_y[0]-0.05/self.scale, z), 'right', 'top'
                p1, align1, valign1 = (self.r_x[0], self.r_y[1]+0.05/self.scale, z), 'right', 'bottom'
                p2, align2, valign2 = (self.r_x[1], self.r_y[0]-0.05/self.scale, z), 'left', 'top'
                p3, align3, valign3 = (self.r_x[1], self.r_y[1]+0.05/self.scale, z), 'left', 'bottom'
            else:
                p0, align0, valign0 = (self.r_x[0]-0.05/self.scale, self.r_y[0], z), 'center', 'top'
                p1, align1, valign1 = (self.r_x[0]-0.05/self.scale, self.r_y[1], z), 'center', 'top'
                p2, align2, valign2 = (self.r_x[1]+0.05/self.scale, self.r_y[0], z), 'center', 'bottom'
                p3, align3, valign3 = (self.r_x[1]+0.05/self.scale, self.r_y[1], z), 'center', 'bottom'
            
            tick = zlabel_format(z)
            draw_text(tick, pos=p0, size=t_size, align=align0, valign=valign0, name=x0y0, inside=False)
            draw_text(tick, pos=p1, size=t_size, align=align1, valign=valign1, name=x0y1, inside=False)
            draw_text(tick, pos=p3, size=t_size, align=align3, valign=valign3, name=x1y1, inside=False)
            draw_text(tick, pos=p2, size=t_size, align=align2, valign=valign2, name=x1y0, inside=False)
        
        self.refresh()
        self.scene.set_posture()
        
    def ticks2d(self, **kwds):
        """绘制2D网格和刻度
        
        kwds        - 关键字参数
                        segment_min     - 标注最少分段数量
                        segment_max     - 标注最多分段数量
                        label_2D3D      - 标注试用2D或3D文字
                        label_size      - 标注字号
                        xlabel_format   - x轴标注格式化所用lambda函数
                        ylabel_format   - y轴标注格式化所用lambda函数
                        
        """
        
        assert self.r_x[0] <= self.r_x[1] and self.r_y[0] <= self.r_y[1] and self.r_z[0] <= self.r_z[1], '当前没有模型，无法显示网格和刻度'
        
        for key in kwds:
            if key not in ['segment_min', 'segment_max', 'label_2D3D', 'label_size', 'xlabel_format', 'ylabel_format']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        segment_min = kwds.get('segment_min', 5)
        segment_max = kwds.get('segment_max', 8)
        label_2D3D = kwds.get('label_2D3D', '3D')
        label_size = kwds.get('label_size', 16)
        label_precision = kwds.get('label_precision', '%.2f')
        xlabel_format = kwds.get('xlabel_format', str)
        ylabel_format = kwds.get('ylabel_format', str)
        t_size = label_size/self.scale
        
        dx, dy = (self.r_x[1]-self.r_x[0])/30, (self.r_y[1]-self.r_y[0])/30
        d = max(dx, dy)
        self.set_data_range((self.r_x[0]-dx, self.r_x[1]+dx), (self.r_y[0]-dy, self.r_y[1]+dy))
        
        vs = np.array([
            [self.r_x[0], self.r_y[0], 0], [self.r_x[1], self.r_y[0], 0], 
            [self.r_x[0], self.r_y[0], 0], [self.r_x[0], self.r_y[1], 0]
        ])
        self.line(vs, self.scene.tc, method='MULTI', width=1.5, inside=False)
        
        vs_arrow = np.array([
            (self.r_x[1]+d, self.r_y[0], 0), (self.r_x[1], self.r_y[0]+d/4, 0), (self.r_x[1], self.r_y[0]-d/4, 0), 
            (self.r_x[0], self.r_y[1]+d, 0), (self.r_x[0]-d/4, self.r_y[1], 0), (self.r_x[0]+d/4, self.r_y[1], 0)
        ])
        self.surface(vs_arrow, color=self.scene.tc, method='T', mode='FCBC', inside=False)
        
        x_values = self._get_tick_label(self.r_x[0], self.r_x[1], s_min=segment_min, s_max=segment_max, endpoint=False)
        y_values = self._get_tick_label(self.r_y[0], self.r_y[1], s_min=segment_min, s_max=segment_max, endpoint=False)
        draw_text = self.text3d if label_2D3D == '3D' else self.text2d
        
        vs_xtick = list()
        for x in x_values:
            tick = xlabel_format(x)
            vs_xtick += [(x, self.r_y[0], 0), (x, self.r_y[0]-0.4*d, 0)]
            draw_text(tick, pos=(x,self.r_y[0]-0.5*d,0), size=t_size, align='center', valign='top', inside=False)
        
        vs_ytick = list()
        for y in y_values:
            tick = ylabel_format(y)
            vs_ytick += [(self.r_x[0], y, 0), (self.r_x[0]-0.4*d, y, 0)]
            draw_text(tick, pos=(self.r_x[0]-0.5*d,y,0), size=t_size, align='right', valign='middle', inside=False)
        
        self.line(np.array(vs_xtick), self.scene.tc, method='MULTI', width=1, inside=False)
        self.line(np.array(vs_ytick), self.scene.tc, method='MULTI', width=1, inside=False)
    
    def flow(self, ps, us, vs, ws, **kwds):
        """绘制流体
        
        ps          - 顶点坐标集，numpy.ndarray类型，shape=(n,3)
        us          - 顶点u分量集，numpy.ndarray类型，shape=(n,)
        vs          - 顶点v分量集，numpy.ndarray类型，shape=(n,)
        ws          - 顶点w分量集，numpy.ndarray类型，shape=(n,)
        kwds        - 关键字参数
                        color       - 轨迹线颜色，None表示使用速度映射颜色
                        actor       - 顶点模型类型，'point'|'line'两个选项
                        size        - point大小
                        width       - line宽度
                        length      - 轨迹线长度，以速度矢量的模为单位
                        duty        - 顶点line模型长度与轨迹线长度之比（占空比），建议值为0.4
                        frames      - 总帧数
                        interval    - 帧间隔，以ms为单位
                        threshold   - 高通阈值，滤除速度小于阈值的数据点
                        name        - 模型名
        """
        
        for key in kwds:
            if key not in ['color', 'actor', 'size', 'width', 'length', 'duty', 'frames', 'interval', 'threshold', 'name']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        color = kwds.get('color', None)
        actor = kwds.get('actor', 'line')
        size = kwds.get('size', 1.0)
        width = kwds.get('width', 1.0)
        length = kwds.get('length', 1.0)
        duty = kwds.get('duty', 0.4)
        frames = kwds.get('frames', 10)
        interval = kwds.get('interval', 10)
        threshold = kwds.get('threshold', None)
        name = kwds.get('name', uuid.uuid1().hex)
        
        VERTEX_SHADER = shaders.compileShader("""#version 140 
            uniform float counter;
            out vec4 myColor;
            
            void main() {
                vec4 v = vec4(gl_Vertex);
                vec3 n = vec3(gl_Normal);
                vec4 rand = vec4(gl_MultiTexCoord0);
                float k = mod(rand[1]+counter, rand[0]);
                v.x += n[0] * k;
                v.y += n[1] * k;
                v.z += n[2] * k;
                gl_Position = gl_ModelViewProjectionMatrix * v; 
                myColor = gl_Color;
            }""", GL_VERTEX_SHADER)
        
        FRAGMENT_SHADER = shaders.compileShader("""#version 140 
            out vec4 FragColor;  
            in vec4 myColor;
            
            void main() { 
                gl_FragColor = myColor;
            }""", GL_FRAGMENT_SHADER)
        
        
        shader = shaders.compileProgram(VERTEX_SHADER, FRAGMENT_SHADER)
        loc_counter = glGetUniformLocation(shader, 'counter')
        program = (shader, loc_counter, name)
        
        fs = np.sqrt(np.power(us,2)+np.power(vs,2)+np.power(ws,2))
        if threshold != None:
            sieve = fs > threshold
            fs = fs[sieve]
            us = us[sieve]
            vs = vs[sieve]
            ws = ws[sieve]
            ps = ps[sieve]
        
        rand = np.random.randint(0, frames, ps.shape[0])
        rand = np.stack((np.ones(ps.shape[0])*frames, rand), axis=1)
        
        if color is None:
            colors = self.scene.cm.cmap(fs, 'wind')
        else:
            colors = self.scene.cm.color2c(color, shape=fs.shape)
        
        if actor == 'point':
            uvw = np.stack((us,vs,ws), axis=1)*length/frames
            self.timers.update({name:{'timer':None, 'counter':0, 'frames':frames, 'uvw':uvw, 'rand':rand}})
            self.point(ps, colors, size=size, program=program, name=name)
        else:
            vertexes = list()
            for p, u, v, w, f in zip(ps, us, vs, ws, fs):
                a_y = np.arccos(w/f)
                if u == 0:
                    a_z = np.pi/2 if v > 0 else -np.pi/2
                else:
                    a_z = np.arctan(v/u) + (np.pi if u < 0 else 0)
                
                rotator = sstr.from_euler('xyz', [0, a_y, a_z], degrees=False)
                vertexes.append(rotator.apply(np.array([[0,0,0], [0,0,f*length*duty]])) + p)
            
            vertexes = np.vstack(vertexes)
            rand = np.repeat(rand, 2, axis=0)
            colors = np.repeat(colors, 2, axis=0)
            uvw = np.stack((us,vs,ws), axis=1)*length*(1-duty)/frames
            uvw = np.repeat(uvw, 2, axis=0)
            
            self.timers.update({name:{'timer':None, 'counter':0, 'frames':frames, 'uvw':uvw, 'rand':rand}})
            self.line(vertexes, colors, method='MULTI', width=width, program=program, name=name)
        
        def on_timer(evt):
            if name in self.models:
                self.timers[name]['counter'] += 1
                if self.timers[name]['counter'] >= self.timers[name]['frames']:
                    self.timers[name]['counter'] = 0
            elif name in self.timers:
                self.timers[name]['timer'].Unbind(wx.EVT_TIMER)
                self.timers[name]['timer'].Stop()
                del self.timers[name]['timer']
                del self.timers[name]
            
            self.refresh()
        
        self.timers[name]['timer'] = wx.Timer()
        self.timers[name]['timer'].Bind(wx.EVT_TIMER, on_timer)
        self.timers[name]['timer'].Start(interval)
        