# -*- coding: utf-8 -*-
#
# Copyright 2019 xufive@gmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 

"""
WxGL是一个基于pyopengl的三维数据展示库

WxGL以wx为显示后端，以加速渲染为第一追求目标
借助于wxpython，WxGL可以很好的融合matplotlib等其他数据展示技术
"""


import uuid
import freetype
import numpy as np
from OpenGL.GL import *
from OpenGL.arrays import vbo


class GLRegion(object):
    """GL视区类"""
    
    def __init__(self, scene, name, box, font, lookat=None, scale=None, view=None, mode=None):
        """构造函数
        
        scene       - 所属场景对象
        name        - 视区的名字
        box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
        font        - 字体文件
        lookat      - 视点、参考点和向上的方向。若为None，表示使用父级场景的设置
        scale       - 模型矩阵缩放比例。若为None，表示使用父级场景的设置
        view        - 视景体。若为None，表示使用父级场景的设置
        mode        - 投影模式
                        None    - 使用父级设置
                        ortho   - 平行投影
                        cone    - 透视投影
        """
        
        self.scene = scene
        self.name = name
        self.box = box
        self.font = font
        self.mode = mode
        
        if lookat:
            self.lookat = np.array(lookat, dtype=np.float)
        else:
            self.lookat = lookat
        
        if scale:
            self.scale = np.array(scale, dtype=np.float)
        else:
            self.scale = scale
        
        if view:
            self.view = np.array(view, dtype=np.float)
        else:
            self.view = view
        
        # 绘图指令集
        self.assembly = list()
        
    def clearCmd(self):
        """清除视区内所有部件模型的生成命令"""
        
        self.assembly = list()
    
    def appendCmd(self, cmd, *args):
        """添加部件或模型"""
        
        self.assembly.append({'cmd':cmd, 'args':args})
    
    def createVBO(self, vertices):
        """创建顶点缓冲区对象"""
        
        id = uuid.uuid1().hex
        buff = vbo.VBO(vertices)
        self.scene.buffers.update({id: buff})
        
        return id
        
    def createEBO(self, indices):
        """创建索引缓冲区对象"""
        
        id = uuid.uuid1().hex
        buff = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)
        self.scene.buffers.update({id: buff})
        
        return id
        
    def createPBO(self, pixels):
        """创建像素缓冲区对象"""
        
        id = uuid.uuid1().hex
        buff = vbo.VBO(pixels, target=GL_PIXEL_UNPACK_BUFFER)
        self.scene.buffers.update({id: buff})
        
        return id
        
    def getIndices(self, rows, cols, glMethod):
        """生成索引集"""
        
        if glMethod in [GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP]:
            indices = list(range(cols))
        elif glMethod == GL_QUADS:
            indices = list()
            for i in range(1, rows):
                for j in range(1, cols):
                    indices += [(i-1)*cols+j-1, i*cols+j-1, i*cols+j, (i-1)*cols+j]
        elif glMethod == GL_QUAD_STRIP:
            indices = list()
            for i in range(1, rows):
                indices += [(i-1)*cols, i*cols]
                for j in range(1, cols):
                    indices += [(i-1)*cols+j, i*cols+j]
        elif glMethod == GL_TRIANGLES:
            indices = list()
            for i in range(1, rows):
                for j in range(1,cols):
                    indices += [(i-1)*cols+j-1, i*cols+j-1, i*cols+j, i*cols+j, (i-1)*cols+j, (i-1)*cols+j-1]
        elif glMethod == GL_TRIANGLE_STRIP:
            indices = list()
            for i in range(1, rows):
                indices += [(i-1)*cols, i*cols]
                for j in range(1,cols):
                    indices += [(i-1)*cols+j, i*cols+j]
        elif glMethod == GL_TRIANGLE_FAN:
            indices = list(range(cols))
        elif glMethod == GL_POLYGON or glMethod == GL_POINTS:
            indices = list(range(cols))
        
        indices_id = self.createEBO(np.array(indices, dtype=np.int))
        return indices_id
        
    def setPolygonMode(self, mode):
        """设置多边形显示模式
        
        mode        - 显示模式
                        0   - 使用当前设置
                        1   - 前后面填充颜色
                        2   - 前后面显示线条
                        3   - 前面填充颜色，后面显示线条
                        4   - 前面显示线条，后面填充颜色
        """
        
        if mode == 1:
            self.appendCmd(self.wxglPolygonMode, GL_FRONT_AND_BACK, GL_FILL)
        elif mode == 2:
            self.appendCmd(self.wxglPolygonMode, GL_FRONT_AND_BACK, GL_LINE)
        elif mode == 3:
            self.appendCmd(self.wxglPolygonMode, GL_FRONT, GL_FILL)
            self.appendCmd(self.wxglPolygonMode, GL_BACK, GL_LINE)
        elif mode == 4:
            self.appendCmd(self.wxglPolygonMode, GL_FRONT, GL_LINE)
            self.appendCmd(self.wxglPolygonMode, GL_BACK, GL_FILL)
        
    def drawElements(self, vertices_id, indices_id, v_type, gl_type):
        """绘制图元
        
        vertices_id - 顶点VBO的id
        indices_id  - 索引EBO的id
        v_type      - 顶点混合数组类型
        gl_type     - 绘制方法
        """
        
        all = [GL_QUADS, GL_QUAD_STRIP, GL_TRIANGLES, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN, GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP]
        assert gl_type in all, u'参数错误'
        
        vertices_vbo = self.scene.buffers[vertices_id]
        indices_ebo = self.scene.buffers[indices_id]
        self.appendCmd(self.wxglDrawElements, vertices_vbo, indices_ebo, v_type, gl_type)
        
    def drawText(self, text, pos, size, color):
        """绘制文字
        
        text        - Unicode字符串
        pos         - 文本位置坐标，list或numpy.ndarray类型，shape=(3，)
        size        - 文本大小，整形
        color       - 文本颜色，list或numpy.ndarray类型，shape=(3,)
        """
        
        assert isinstance(pos, (list, np.ndarray)), u'参数类型错误'
        assert isinstance(color, (list, np.ndarray)), u'参数类型错误'
        
        if isinstance(pos, list):
            pos = np.array(pos)
        
        if isinstance(color, list):
            color = np.array(color)
        
        over, under = -1, -1
        pixels = None
        face = freetype.Face(self.font)
        face.set_char_size(size*size)
        for ch in text:
            face.load_char(ch)
            btm_obj = face.glyph.bitmap
            w, h = btm_obj.width, btm_obj.rows
            data = np.array(btm_obj.buffer, dtype=np.uint8).reshape(h,w)
            bx, by = int(face.glyph.metrics.horiBearingX/64), int(face.glyph.metrics.horiBearingY/64)
            ha = int(face.glyph.metrics.horiAdvance/64)
            sapre = ha - bx - w
            bottom = h-by
            if bottom < 0:
                patch = np.zeros((-bottom, data.shape[1]), dtype=np.uint8)
                data = np.vstack((data, patch))
                bottom = 0
            
            if bx > 0:
                patch = np.zeros((data.shape[0], bx), dtype=np.uint8)
                data = np.hstack((patch, data))
            if sapre > 0:
                patch = np.zeros((data.shape[0], sapre), dtype=np.uint8)
                data = np.hstack((data, patch))
            
            if not isinstance(pixels, np.ndarray):
                pixels = data
                over, under = by, bottom
            else:
                if over > by:
                    patch = np.zeros((over-by, data.shape[1]), dtype=np.uint8)
                    data = np.vstack((patch, data))
                elif over < by:
                    patch = np.zeros((by-over, pixels.shape[1]), dtype=np.uint8)
                    pixels = np.vstack((patch, pixels))
                
                if under > bottom:
                    patch = np.zeros((under-bottom, data.shape[1]), dtype=np.uint8)
                    data = np.vstack((data, patch))
                elif under < bottom:
                    patch = np.zeros((bottom-under, pixels.shape[1]), dtype=np.uint8)
                    pixels = np.vstack((pixels, patch ))
                
                pixels = np.hstack((pixels, data))
                over = max(over, by)
                under = max(under, bottom)
        
        rows, cols = pixels.shape
        color = color*255
        color = np.tile(color, (rows*cols, 1)).astype(np.uint8)
        pixels = pixels.reshape(-1, 1)
        pixels = np.hstack((color, pixels)).reshape(rows, cols, 4)
        pixels = pixels[::-1].ravel()
        
        pixels_id = self.createPBO(pixels)
        pixels_pbo = self.scene.buffers[pixels_id]
        self.appendCmd(self.wxglDrawPixels, pixels_pbo, rows, cols, pos)
        
    def drawLine(self, v, c, method=0):
        """绘制线段
        v           - 顶点坐标集，numpy.ndarray类型，shape=(cols,3)
        c           - 顶点颜色集，numpy.ndarray类型，shape=(3,)|(4,)|(cols,3)|(cols,4)
        method      - 绘制方法
                        0   - 线段
                        1   - 连续线段
                        2   - 闭合线段
        """
        
        if c.ndim == 1:
            c = np.tile(c, (v.shape[0], 1))
        
        if c.shape[-1] == 3:
            v_type = GL_C3F_V3F
            vertices_id = self.createVBO(np.hstack((c,v)).astype(np.float32))
        else:
            v_type = GL_C4F_N3F_V3F
            n = np.tile(np.array([1.0, 1.0, 1.0]), v.shape[0])
            n = n.reshape(-1, 3)
            vertices_id = self.createVBO(np.hstack((c,n,v)).astype(np.float32))
        
        gl_type_options = [GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP]
        gl_type = gl_type_options[method]
        indices_id = self.getIndices(1, v.shape[0], gl_type)
        
        self.drawElements(vertices_id, indices_id, v_type, gl_type)
        
    def drawSurface(self, x, y, z, c, method=0, mode=0):
        """绘制曲面
        
        x           - 顶点的x坐标集，numpy.ndarray类型，shape=(rows,cols)
        y           - 顶点的y坐标集，numpy.ndarray类型，shape=(rows,cols)
        z           - 顶点的z坐标集，numpy.ndarray类型，shape=(rows,cols)
        c           - 顶点的颜色，numpy.ndarray类型，shape=(3,)|(4,)|(rows,cols,3)|(rows,cols,4)
        method      - 绘制方法
                        0   - 四边形
                        1   - 连续四边形
                        2   - 三角形
                        3   - 连续三角形
                        4   - 扇形
        mode        - 显示模式
                        0   - 使用当前设置
                        1   - 前后面填充颜色
                        2   - 前后面显示线条
                        3   - 前面填充颜色，后面显示线条
                        4   - 前面显示线条，后面填充颜色
        """
        
        rows, cols = z.shape
        v = np.dstack((x,y,z)).reshape(-1,3)
        
        if c.ndim == 1:
            c = np.tile(c, (rows*cols, 1))
        else:
            c = c.reshape(-1, c.shape[-1])
        
        if c.shape[-1] == 3:
            v_type = GL_C3F_V3F
            vertices_id = self.createVBO(np.hstack((c,v)).astype(np.float32))
        else:
            v_type = GL_C4F_N3F_V3F
            n = np.tile(np.array([1.0, 1.0, 1.0]), v.shape[0])
            n = n.reshape(-1, 3)
            vertices_id = self.createVBO(np.hstack((c,n,v)).astype(np.float32))
        
        gl_type_options = [GL_QUADS, GL_QUAD_STRIP, GL_TRIANGLES, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN]
        gl_type = gl_type_options[method]
        indices_id = self.getIndices(rows, cols, gl_type)
        
        self.setPolygonMode(mode)
        self.drawElements(vertices_id, indices_id, v_type, gl_type)
        
        return vertices_id, indices_id, v_type, gl_type, mode
        
    def plotAxes(self, k=1.0, slices=50, half=False, xlabel=None, ylabel=None, zlabel=None, size=40):
        """绘制坐标轴
        
        k           - 坐标轴长度，从-k到k
        slices      - 锥面分片数（数值越大越精细）
        half        - 是否画半轴
        xlabel      - x轴标注
        ylabel      - y轴标注
        zlabel      - z轴标注
        size        - 字号
        """
        
        if half:
            start = 0
        else:
            start = -k
        
        v = np.array([[start,0,0],[0.8*k,0,0],[0,start,0],[0,0.8*k,0],[0,0,start],[0,0,0.8*k]])
        c = np.array([[1,0,0],[1,0,0],[0,1,0],[0,1,0],[0,0,1],[0,0,1]])
        self.drawLine(v, c, method=0)
        
        self._plotAxisCone('x', k=k, slices=slices, label=xlabel, size=size)
        self._plotAxisCone('y', k=k, slices=slices, label=ylabel, size=size)
        self._plotAxisCone('z', k=k, slices=slices, label=zlabel, size=size)
        
    def _plotAxisCone(self, axis, k, slices, label, size):
        """绘制单个坐标轴的圆锥和标注
        
        axis        - 轴名称
        k           - 坐标轴长度，从-k到k
        slices      - 锥面分片数（数值越大越精细）
        label       - 轴标注
        size        - 字号
        """
        
        r = 0.03*k
        angles = np.linspace(0, 2*np.pi, slices+1)
        v_type = GL_C3F_V3F
        
        if axis == 'x':
            center = np.array([0.8*k,0,0])
            spire = np.array([k,0,0])
            c = np.array([1,0,0])
            x = np.ones_like(angles)*0.8*k
            y = np.sin(angles)*r
            z = np.cos(angles)*r
            v = np.dstack((x,y,z)).reshape(-1,3)
        elif axis == 'y':
            center = np.array([0,0.8*k,0])
            spire = np.array([0,k,0])
            c = np.array([0,1,0])
            y = np.ones_like(angles)*0.8*k
            z = np.sin(angles)*r
            x = np.cos(angles)*r
            v = np.dstack((x,y,z)).reshape(-1,3)
        elif axis == 'z':
            center = np.array([0,0,0.8*k])
            spire = np.array([0,0,k])
            c = np.array([0,0,1])
            z = np.ones_like(angles)*0.8*k
            x = np.sin(angles)*r
            y = np.cos(angles)*r
            v = np.dstack((x,y,z)).reshape(-1,3)
            
        cone = np.vstack((spire.reshape(1,3), v))
        circle = np.vstack((center.reshape(1,3), v))
        color = np.tile(c, (cone.shape[0], 1))
        
        cone_id = self.createVBO(np.hstack((color,cone)).astype(np.float32))
        circle_id = self.createVBO(np.hstack((color,cone)).astype(np.float32))
        
        indices = list(range(cone.shape[0]))
        indices_id = self.createEBO(np.array(indices, dtype=np.int))
        
        self.setPolygonMode(1)
        self.drawElements(cone_id, indices_id, v_type, GL_TRIANGLE_FAN)
        self.drawElements(circle_id, indices_id, v_type, GL_TRIANGLE_FAN)
        
        if label:
            self.drawText(label, spire, size, c)
        
    def plotColorBar(self, value, color, location, **kwds):
        """绘制colorBar
        
        value       - ColorBar标注的值，list类型，升序
        color       - ColorBar的颜色，list类型，长度与v相等或少1
        location    - ColorBar位置：top|right|bottom|left
        kwds        - 其他参数：title|title_size|label_size|text_color|bar_offset|title_offset|label_offset
        """
        
        assert isinstance(value, list), u'参数类型错误'
        assert isinstance(color, list), u'参数类型错误'
        assert len(value)==len(color) or len(value)==len(color)+1, u'参数格式错误'
        
        for key in kwds:
            if key not in ['title','title_size','label_size','text_color','bar_offset','title_offset','label_offset']:
                raise TypeError(u'未知的参数%s'%key)
        
        if 'title' not in kwds:
            kwds.update({'title':None})
        if 'title_size' not in kwds:
            kwds.update({'title_size':40})
        if 'label_size' not in kwds:
            kwds.update({'label_size':32})
        if 'text_color' not in kwds:
            kwds.update({'text_color':[1,1,1]})
        if 'bar_offset' not in kwds:
            kwds.update({'bar_offset':(0,0)})
        if 'title_offset' not in kwds:
            kwds.update({'title_offset':(0,0)})
        if 'label_offset' not in kwds:
            kwds.update({'label_offset':(0,0)})
        
        w = int(self.box[2]*self.scene.size[0])
        h = int(self.box[3]*self.scene.size[1])
        
        if location == 'right' or location == 'left':
            x_min, x_max = -0.6+kwds['bar_offset'][0], 0.0+kwds['bar_offset'][0]
            y_min, y_max = -0.8*h/w+kwds['bar_offset'][1], 0.7*h/w+kwds['bar_offset'][1]
            
            if kwds['title']:
                title_pos = [(x_min+x_max)/2+kwds['title_offset'][0], y_max+kwds['title_offset'][1], 0.0]
                self.drawText(kwds['title'], title_pos, kwds['title_size'], kwds['text_color'])
            
            dy = (y_max-y_min)/(len(value)-1)
            if len(value) == len(color): # 渐变色
                x, y, z, c = list(), list(), list(), list()
                for i in range(len(value)):
                    x.append([x_min, x_max])
                    y.append([y_min+i*dy, y_min+i*dy])
                    z.append([0.0, 0.0])
                    c.append([color[i], color[i]])
                    
                    label_pos = [x_max+kwds['label_offset'][0], y_min+i*dy+kwds['label_offset'][1], 0.0]
                    self.drawText(str(value[i]), label_pos, kwds['label_size'], kwds['text_color'])
                
                x = np.array(x)
                y = np.array(y)
                z = np.array(z)
                c = np.array(c)
                self.drawSurface(x, y, z, c, method=0, mode=1)
            else:
                x, y, z, c = list(), list(), list(), list()
                x.append([x_min, x_max])
                y.append([y_min, y_min])
                z.append([0.0, 0.0])
                c.append([color[0], color[0]])
                
                label_pos = [x_max+kwds['label_offset'][0], y_min+kwds['label_offset'][1], 0.0]
                self.drawText(str(value[0]), label_pos, kwds['label_size'], kwds['text_color'])
                
                for i in range(1,len(value)-1):
                    x.append([x_min, x_max])
                    y.append([y_min+i*dy-0.001, y_min+i*dy-0.001])
                    z.append([0.0, 0.0])
                    c.append([color[i-1], color[i-1]])
                    x.append([x_min, x_max])
                    y.append([y_min+i*dy, y_min+i*dy])
                    z.append([0.0, 0.0])
                    c.append([color[i], color[i]])
                    
                    label_pos = [x_max+kwds['label_offset'][0], y_min+i*dy+kwds['label_offset'][1], 0.0]
                    self.drawText(str(value[i]), label_pos, kwds['label_size'], kwds['text_color'])
                
                x.append([x_min, x_max])
                y.append([y_max, y_max])
                z.append([0.0, 0.0])
                c.append([color[-1], color[-1]])
                
                label_pos = [x_max+kwds['label_offset'][0], y_max+kwds['label_offset'][1], 0.0]
                self.drawText(str(value[-1]), label_pos, kwds['label_size'], kwds['text_color'])
                
                x = np.array(x)
                y = np.array(y)
                z = np.array(z)
                c = np.array(c)
                self.drawSurface(x, y, z, c, method=0, mode=1)
        elif location == 'top' or location == 'bottom':
            pass
    
    def wxglPolygonMode(self, args):
        """glPolygonMode"""
        
        glPolygonMode(args[0], args[1])
    
    def wxglDrawElements(self, args):
        """glDrawElements"""
        
        args[0].bind()
        glInterleavedArrays(args[2], 0, None)
        args[1].bind()
        glDrawElements(args[3], int(args[1].size/4), GL_UNSIGNED_INT, None) 
        args[0].unbind()
        args[1].unbind()
    
    def wxglDrawPixels(self, args):
        """glDrawElements"""
        
        if isinstance(self.scale, np.ndarray):
            scale = self.scale
        else:
            scale = self.scene.scale
        
        glPixelZoom(scale[0], scale[1])
        glDepthMask(GL_FALSE)
        glRasterPos3fv(args[3]*scale)
        args[0].bind()
        glDrawPixels(args[2], args[1], GL_RGBA, GL_UNSIGNED_BYTE, None)
        args[0].unbind()
        glDepthMask(GL_TRUE)
        