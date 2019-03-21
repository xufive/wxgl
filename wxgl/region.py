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


class WxGLRegion(object):
    """GL视区类"""
    
    def __init__(self, scene, name, box, lookat=None, scale=None, view=None, mode=None):
        """构造函数
        
        scene       - 所属场景对象
        name        - 视区的名字
        box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
        lookat      - 相机、目标点和头部指向。若为None，表示使用父级场景的设置
        scale       - 模型矩阵缩放比例。若为None，表示使用父级场景的设置
        view        - 视景体。若为None，表示使用父级场景的设置
        mode        - 投影模式
                        None    - 使用父级设置
                        ortho   - 平行投影
                        cone    - 透视投影
        """
        
        self.scene = scene
        self.font = self.scene.font
        self.name = name
        self.box = box
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

        self.cm = self.scene.cm                             # 调色板对象
        self.assembly = list()                              # 绘图指令集
        self.models = dict()                                # 所有模型
    
    def clearCmd(self):
        """清除视区内所有部件模型的生成命令"""
        
        self.assembly = list()
    
    def appendCmd(self, cmd, *args):
        """添加部件或模型"""
        
        self.assembly.append({'cmd':cmd, 'args':args})
    
    def update(self):
        """模型指令化"""
        
        self.clearCmd()
        for key in self.models:
            if self.models[key]['display']:
                for item in self.models[key]['component']:
                    if item['type'] == 'surface':
                        vertices_id, indices_id, v_type, gl_type, mode = item['args']
                        self._setPolygonMode(mode)
                        self._addElements(vertices_id, indices_id, v_type, gl_type)
                    elif item['type'] == 'line':
                        vertices_id, indices_id, v_type, gl_type, width, stipple = item['args']
                        self._setLineWidth(width)
                        self._setLineStipple(stipple)
                        self._addElements(vertices_id, indices_id, v_type, gl_type)
                    elif item['type'] == 'point':
                        vertices_id, indices_id, v_type, gl_type, size = item['args']
                        self._setPointSize(size)
                        self._addElements(vertices_id, indices_id, v_type, gl_type)
                    elif item['type'] == 'text':
                        pixels_id, rows, cols, pos = item['args']
                        self._addPixels(pixels_id, rows, cols, pos)
        
        self.scene.Refresh(False)
    
    def showModel(self, name):
        """显示模型"""
        
        if name in self.models:
            self.models[name]['display'] = True
            self.update()
    
    def hideModel(self, name):
        """隐藏模型"""
        
        if name in self.models:
            self.models[name]['display'] = False
            self.update()
    
    def deleteModel(self, name):
        """删除模型"""
        
        if name in self.models:
            for item in self.models[name]['component']:
                if item['type'] == 'text':
                    self.scene.buffers[item['args'][0]].delete()
                elif item['type'] in ['line', 'surface']:
                   self.scene.buffers[item['args'][0]].delete()
                   self.scene.buffers[item['args'][1]].delete()
            
            del self.models[name]
            self.update()
    
    def getTextSize(self, textList, size):
        """返回字符串列表中每个字符串的宽度、高度
        
        textList    - 字符串列表
        size        - 字符大小
        """
        
        face = freetype.Face(self.font)
        face.set_char_size(size*size)
        
        size = list()
        for text in textList:
            twidth = 0
            charHlist = []
            for ch in text:
                face.load_char(ch)
                twidth += int(face.glyph.metrics.horiAdvance/64)
                charHlist.append(face.glyph.bitmap.rows)
            size.append((twidth, max(charHlist)))
            
        return size
    
    def getTickLabel(self, vmin, vmax):
        """返回合适的Colorbar标注值
        
        vmin        - 最小值
        vmax        - 最大值
        """
        
        r = vmax - vmin
        tmp = list()
        tmp_min = list()
        option = [1, 2, 5]
        for k in option:
            tmp.append(np.array([abs(float(('%E'%(r/i)).split('E')[0])-k) for i in range(4,10)]))
            tmp_min.append(np.min(tmp[-1]))
        
        k = tmp_min.index(min(tmp_min))
        step = option[k]
        steps = tmp[k].argmin() + 4
        m = int(('%E'%(r/steps)).split('E')[1])
        step *= 10**m
        
        label = list()
        v = round(int(vmin/step)*step, 6)
        while v <= vmax:
            if v >= vmin:
                label.append(v)
            v += step
            v = round(v, 6)
        
        return label
    
    def _wxglPolygonMode(self, args):
        """glPolygonMode"""
        
        glPolygonMode(args[0], args[1])
    
    def _wxglPointSize(self, args):
        """glPointSize"""
        
        glPointSize(args[0])
    
    def _wxglLineWidth(self, args):
        """glLineWidth"""
        
        glLineWidth(args[0])
    
    def _wxglLineStipple(self, args):
        """glLineStipple"""
        
        glLineStipple(args[0][0], args[0][1])
    
    def _wxglDrawElements(self, args):
        """glDrawElements"""
        
        args[0].bind()
        glInterleavedArrays(args[2], 0, None)
        args[1].bind()
        glDrawElements(args[3], int(args[1].size/4), GL_UNSIGNED_INT, None) 
        args[0].unbind()
        args[1].unbind()
    
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
        
        glEnable(args[0])
    
    def _wxglDisable(self, args):
        """glDisable"""
        
        glDisable(args[0])
    
    def _createVBO(self, vertices):
        """创建顶点缓冲区对象"""
        
        id = uuid.uuid1().hex
        buff = vbo.VBO(vertices)
        self.scene.buffers.update({id: buff})
        
        return id
        
    def _createEBO(self, indices):
        """创建索引缓冲区对象"""
        
        id = uuid.uuid1().hex
        buff = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)
        self.scene.buffers.update({id: buff})
        
        return id
        
    def _createPBO(self, pixels):
        """创建像素缓冲区对象"""
        
        id = uuid.uuid1().hex
        buff = vbo.VBO(pixels, target=GL_PIXEL_UNPACK_BUFFER)
        self.scene.buffers.update({id: buff})
        
        return id
        
    def _getIndices(self, glMethod, cols, rows=None):
        """生成索引集
        
        glMethod    - 图元绘制方法
        cols        - 顶点颜色集，numpy.ndarray类型，shape=(3,)|(4,)|(cols,3)|(cols,4)
        rows        - 仅对GL_QUADS|GL_QUAD_STRIP|GL_TRIANGLES|GL_TRIANGLE_STRIP有效
        """
        
        if glMethod in [GL_POINTS, GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP, GL_POLYGON, GL_TRIANGLE_FAN]:
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
        
        return self._createEBO(np.array(indices, dtype=np.int))
        
    def _setPolygonMode(self, mode):
        """设置多边形显示模式
        
        mode        - 显示模式
                        0   - 使用当前设置
                        1   - 前后面填充颜色
                        2   - 前后面显示线条
                        3   - 前面填充颜色，后面显示线条
                        4   - 前面显示线条，后面填充颜色
        """
        
        if mode == 1:
            self.appendCmd(self._wxglPolygonMode, GL_FRONT_AND_BACK, GL_FILL)
        elif mode == 2:
            self.appendCmd(self._wxglPolygonMode, GL_FRONT_AND_BACK, GL_LINE)
        elif mode == 3:
            self.appendCmd(self._wxglPolygonMode, GL_FRONT, GL_FILL)
            self.appendCmd(self._wxglPolygonMode, GL_BACK, GL_LINE)
        elif mode == 4:
            self.appendCmd(self._wxglPolygonMode, GL_FRONT, GL_LINE)
            self.appendCmd(self._wxglPolygonMode, GL_BACK, GL_FILL)
        
    def _setPointSize(self, size):
        """设置点的大小
        
        size        - 点的大小
        """
        
        if size:
            self.appendCmd(self._wxglPointSize, size)
        
    def _setLineWidth(self, width):
        """设置线宽
        
        width       - 线宽
        """
        
        if width:
            self.appendCmd(self._wxglLineWidth, width)
        
    def _setLineStipple(self, stipple):
        """设置线型
        
        stipple     - 线型
        """
        
        if stipple:
            self.appendCmd(self._wxglEnable, GL_LINE_STIPPLE)
            self.appendCmd(self._wxglLineStipple, stipple)
        
    def _createText(self, text, size, color, offset=0):
        """生成文字的像素集、高度、宽度
        
        text        - Unicode字符串
        size        - 文本大小，整形
        color       - 文本颜色，list或numpy.ndarray类型，shape=(3,)
        offset      - 偏移数
        """
        
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
        if offset != 0:
            patch = np.zeros((rows, offset), dtype=np.uint8)
            pixels = np.hstack((patch, pixels))
        
        rows, cols = pixels.shape
        color = color*255
        color = np.tile(color, (rows*cols, 1)).astype(np.uint8)
        pixels = pixels.reshape(-1, 1)
        pixels = np.hstack((color, pixels)).reshape(rows, cols, 4)
        pixels = pixels[::-1].ravel()
        pixels_id = self._createPBO(pixels)
        
        return pixels_id, rows, cols
        
    def _createPoint(self, v, c):
        """生成点的顶点集、索引集、顶点数组类型、图元绘制方法
        
        v           - 顶点坐标集，numpy.ndarray类型，shape=(cols,3)
        c           - 顶点颜色集，numpy.ndarray类型，shape=(3,)|(4,)|(cols,3)|(cols,4)
        """
        
        if c.ndim == 1:
            c = np.tile(c, (v.shape[0], 1))
        
        if c.shape[-1] == 3:
            v_type = GL_C3F_V3F
            vertices_id = self._createVBO(np.hstack((c,v)).astype(np.float32))
        else:
            v_type = GL_C4F_N3F_V3F
            n = np.tile(np.array([1.0, 1.0, 1.0]), v.shape[0])
            n = n.reshape(-1, 3)
            
            vertices_id = self._createVBO(np.hstack((c,n,v)).astype(np.float32))
        
        gl_type = GL_POINTS
        indices_id = self._getIndices(gl_type, v.shape[0])
        
        return vertices_id, indices_id, v_type, gl_type
        
    def _createLine(self, v, c, method=0):
        """生成线段的顶点集、索引集、顶点数组类型、图元绘制方法
        
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
            vertices_id = self._createVBO(np.hstack((c,v)).astype(np.float32))
        else:
            v_type = GL_C4F_N3F_V3F
            n = np.tile(np.array([1.0, 1.0, 1.0]), v.shape[0])
            n = n.reshape(-1, 3)
            
            vertices_id = self._createVBO(np.hstack((c,n,v)).astype(np.float32))
        
        gl_type_options = [GL_LINES, GL_LINE_STRIP, GL_LINE_LOOP]
        gl_type = gl_type_options[method]
        indices_id = self._getIndices(gl_type, v.shape[0])
        
        return vertices_id, indices_id, v_type, gl_type
        
    def _createSurface(self, x, y, z, c, method=0):
        """生成曲面的顶点集、索引集、顶点数组类型、图元绘制方法
        
        x           - 顶点的x坐标集，numpy.ndarray类型，shape=(clos,)|(rows,cols)
        y           - 顶点的y坐标集，numpy.ndarray类型，shape=(clos,)|(rows,cols)
        z           - 顶点的z坐标集，numpy.ndarray类型，shape=(clos,)|(rows,cols)
        c           - 顶点的颜色，numpy.ndarray类型，shape=(3|4,)|(cols,3|4)|(rows,cols,3|4)
        method      - 绘制方法
                        0   - 四边形
                        1   - 连续四边形
                        2   - 三角形
                        3   - 连续三角形
                        4   - 扇形
                        5   - 多边形
        """
        if method < 4:
            rows, cols = z.shape
        else:
            rows, cols = 1, z.shape[0]
        
        v = np.dstack((x,y,z)).reshape(-1,3)
        
        if c.ndim == 1:
            c = np.tile(c, (rows*cols, 1))
        else:
            c = c.reshape(-1, c.shape[-1])
        
        if c.shape[-1] == 3:
            v_type = GL_C3F_V3F
            vertices_id = self._createVBO(np.hstack((c,v)).astype(np.float32))
        else:
            v_type = GL_C4F_N3F_V3F
            n = np.tile(np.array([1.0, 1.0, 1.0]), v.shape[0])
            n = n.reshape(-1, 3)
            vertices_id = self._createVBO(np.hstack((c,n,v)).astype(np.float32))
        
        gl_type_options = [GL_QUADS, GL_QUAD_STRIP, GL_TRIANGLES, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN, GL_POLYGON]
        gl_type = gl_type_options[method]
        indices_id = self._getIndices(gl_type, cols, rows)
        
        return vertices_id, indices_id, v_type, gl_type
        
    def _addElements(self, vertices_id, indices_id, v_type, gl_type):
        """生成绘制图元命令
        
        vertices_id - 顶点VBO的id
        indices_id  - 索引EBO的id
        v_type      - 顶点混合数组类型
        gl_type     - 绘制方法
        """
        
        vertices_vbo = self.scene.buffers[vertices_id]
        indices_ebo = self.scene.buffers[indices_id]
        self.appendCmd(self._wxglDrawElements, vertices_vbo, indices_ebo, v_type, gl_type)
        
    def _addPixels(self, pixels_id, rows, cols, pos):
        """生成绘制像素命令
        
        pixels_id   - 像素VBO的id
        rows        - 像素行数
        cols        - 像素列数
        pos         - 位置
        """
        
        pixels_pbo = self.scene.buffers[pixels_id]
        self.appendCmd(self._wxglDrawPixels, pixels_pbo, rows, cols, pos)
        
    def _plotAxisCone(self, name, axis, k, slices, label, size):
        """绘制单个坐标轴的圆锥和标注
        
        name        - 模型名称
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
            #v = np.dstack((x,y,z)).reshape(-1,3)
        elif axis == 'y':
            center = np.array([0,0.8*k,0])
            spire = np.array([0,k,0])
            c = np.array([0,1,0])
            y = np.ones_like(angles)*0.8*k
            z = np.sin(angles)*r
            x = np.cos(angles)*r
            #v = np.dstack((x,y,z)).reshape(-1,3)
        elif axis == 'z':
            center = np.array([0,0,0.8*k])
            spire = np.array([0,0,k])
            c = np.array([0,0,1])
            z = np.ones_like(angles)*0.8*k
            x = np.sin(angles)*r
            y = np.cos(angles)*r
            #v = np.dstack((x,y,z)).reshape(-1,3)
            
        x_cone = np.hstack((spire[0], x))
        y_cone = np.hstack((spire[1], y))
        z_cone = np.hstack((spire[2], z))
        x_ground = np.hstack((center[0], x))
        y_ground = np.hstack((center[1], y))
        z_ground = np.hstack((center[2], z))
        
        self.drawSurface(name, x_cone, y_cone, z_cone, c, method=4, mode=1)
        self.drawSurface(name, x_ground, y_ground, z_ground, c, method=4, mode=1)
        if label:
            self.drawText(name, label, spire, size, c)
        
    def drawText(self, name, text, pos, size, color, offset=0, display=True):
        """绘制文字
        
        name        - 模型名
        text        - Unicode字符串
        pos         - 文本位置坐标，list或numpy.ndarray类型，shape=(3，)
        size        - 文本大小，整形
        color       - 文本颜色，list或numpy.ndarray类型，shape=(3,)
        offset      - 偏移数
        display     - 是否显示
        """
        
        assert isinstance(pos, (list, np.ndarray)), u'参数类型错误'
        assert isinstance(color, (list, np.ndarray)), u'参数类型错误'
        
        if isinstance(pos, list):
            pos = np.array(pos)
        
        if isinstance(color, list):
            color = np.array(color)
        
        pixels_id, rows, cols = self._createText(text, size, color, offset)
        if name in self.models:
            self.models[name]['component'].append({
                'type': 'text',
                'args': [pixels_id, rows, cols, pos]
            })
        else:
            self.models.update({name: {
                'display': display,
                'component': [{
                    'type': 'text',
                    'args': [pixels_id, rows, cols, pos]
                }]
            }})
        
    def drawPoint(self, name, v, c, size=None, display=True):
        """绘制点
        
        name        - 模型名
        v           - 顶点坐标集，numpy.ndarray类型，shape=(cols,3)
        c           - 顶点颜色集，numpy.ndarray类型，shape=(3,)|(4,)|(cols,3)|(cols,4)
        size        - 点的大小，整数，系统默认为1，None表示使用当前设置
        display     - 是否显示
        """
        
        vertices_id, indices_id, v_type, gl_type = self._createPoint(v, c)
        if name in self.models:
            self.models[name]['component'].append({
                'type': 'point',
                'args': [vertices_id, indices_id, v_type, gl_type, size]
            })
        else:
            self.models.update({name: {
                'display': display,
                'component': [{
                    'type': 'point',
                    'args': [vertices_id, indices_id, v_type, gl_type, size]
                }]
            }})
        
    def drawLine(self, name, v, c, method=0, width=None, stipple=None, display=True):
        """绘制线段
        
        name        - 模型名
        v           - 顶点坐标集，numpy.ndarray类型，shape=(cols,3)
        c           - 顶点颜色集，numpy.ndarray类型，shape=(3,)|(4,)|(cols,3)|(cols,4)
        method      - 绘制方法
                        0   - 线段
                        1   - 连续线段
                        2   - 闭合线段
        width       - 线宽，0.0~10.0之间，None表示使用当前设置
        stipple     - 线型，整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None表示使用当前设置
        display     - 是否显示
        """
        
        vertices_id, indices_id, v_type, gl_type = self._createLine(v, c, method)
        if name in self.models:
            self.models[name]['component'].append({
                'type': 'line',
                'args': [vertices_id, indices_id, v_type, gl_type, width, stipple]
            })
        else:
            self.models.update({name: {
                'display': display,
                'component': [{
                    'type': 'line',
                    'args': [vertices_id, indices_id, v_type, gl_type, width, stipple]
                }]
            }})
    
    def drawSurface(self, name, x, y, z, c, method=0, mode=0, display=True):
        """绘制曲面
        
        name        - 模型名
        x           - 顶点的x坐标集，numpy.ndarray类型，shape=(rows,cols)
        y           - 顶点的y坐标集，numpy.ndarray类型，shape=(rows,cols)
        z           - 顶点的z坐标集，numpy.ndarray类型，shape=(rows,cols)
        c           - 顶点的颜色，numpy.ndarray类型，shape=(3|4,)|(rows,cols,3|4)
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
        display     - 是否显示
        """
        
        vertices_id, indices_id, v_type, gl_type = self._createSurface(x, y, z, c, method)
        if name in self.models:
            self.models[name]['component'].append({
                'type': 'surface',
                'args': [vertices_id, indices_id, v_type, gl_type, mode]
            })
        else:
            self.models.update({name: {
                'display': display,
                'component': [{
                    'type': 'surface',
                    'args': [vertices_id, indices_id, v_type, gl_type, mode]
                }]
            }})
    
    def drawVolume(self, name, volume, x=None, y=None, z=None, display=True):
        """绘制体数据
        
        name        - 模型名
        volume      - 顶点的颜色集，numpy.ndarray类型，shape=(layers,rows,cols,3|4)
        x           - 顶点的x坐标集，numpy.ndarray类型，shape=(rows,cols)。缺省则使用volume的2轴索引构造
        y           - 顶点的y坐标集，numpy.ndarray类型，shape=(rows,cols)。缺省则使用volume的1轴索引构造
        z           - 顶点的z坐标集，numpy.ndarray类型，shape=(layers,)。缺省则使用volume的0轴索引构造
        display     - 是否显示
        """
        
        method = 0  # 四边形
        mode = 1    # 前后面填充颜色
        d, h, w  = volume.shape[0], volume.shape[1], volume.shape[2]
        
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
            self.drawSurface(name, x, y, z[i]*np.ones_like(x), volume[i], method=method, mode=mode, display=display)
        
        z_h = z.repeat(h).reshape((-1, h))
        for i in range(w):
            x_h = np.tile(x[:,i], (d,1))
            y_h = np.tile(y[:,i], (d,1))
            c_h = volume[:d,:,i]
            self.drawSurface(name, x_h, y_h, z_h, c_h, method=method, mode=mode, display=display)
        
        z_v = z.repeat(w).reshape((-1, w))
        for i in range(h):
            x_v = np.tile(x[i,:], (d,1))
            y_v = np.tile(y[i,:], (d,1))
            c_v = volume[:d,i,:]
            self.drawSurface(name, x_v, y_v, z_v, c_v, method=method, mode=mode, display=display)
    
    def drawAxes(self, name, k=1.0, slices=50, half=False, xlabel=None, ylabel=None, zlabel=None, size=40, display=True):
        """绘制坐标轴
        
        name        - 模型名
        k           - 坐标轴长度，从-k到k
        slices      - 锥面分片数（数值越大越精细）
        half        - 是否画半轴
        xlabel      - x轴标注
        ylabel      - y轴标注
        zlabel      - z轴标注
        size        - 字号
        display     - 是否显示
        """
        
        if half:
            start = 0
        else:
            start = -k
        
        v = np.array([[start,0,0],[0.8*k,0,0],[0,start,0],[0,0.8*k,0],[0,0,start],[0,0,0.8*k]])
        c = np.array([[1,0,0],[1,0,0],[0,1,0],[0,1,0],[0,0,1],[0,0,1]])
        
        self.drawLine(name, v, c, method=0, width=1, stipple=(1,0xFFFF), display=display)
        
        self._plotAxisCone(name, 'x', k=k, slices=slices, label=xlabel, size=size)
        self._plotAxisCone(name, 'y', k=k, slices=slices, label=ylabel, size=size)
        self._plotAxisCone(name, 'z', k=k, slices=slices, label=zlabel, size=size)
        
    def drawColorBar(self, name, drange, cmap, orient, **kwds):
        """绘制colorBar 
        
        name        - 模型名
        drange      - 值域范围，tuple类型
        cmap        - 调色板名称
        orient      - 方向：h|v|horizontal|vertical
        kwds        - 其他参数
        """
        
        ccfg = self.cm.cms[cmap]
        value = []
        color = []
        for item in ccfg:
            v, rgb = item[0], item[1]
            value.append((drange[1] - drange[0]) * v + drange[0])
            color.append(rgb)
        
        # 允许输入的可选参数
        allowedKwds = [
            'title_name', 'title_size', 'title_color', 'title_offset', 'title_align', 
            'label_color','label_size', 'label_offset', 'label_align', 'label_precision', 
            'line_length', 'line_color', 
            'ticklabel', 'bar_offset', 'display'
        ]
        
        for key in kwds:
            if key not in allowedKwds:
                raise TypeError(u'未知的参数%s'%key)
        
        # title设置
        title_name      = kwds['title_name']      if 'title_name'      in kwds else None               # ColorBar标题
        title_size      = kwds['title_size']      if 'title_size'      in kwds else 40                 # 标题字号
        title_color     = kwds['title_color']     if 'title_color'     in kwds else [1,1,1]            # 标题颜色
        title_offset    = kwds['title_offset']    if 'title_offset'    in kwds else (0,0)              # 标题偏移量
        title_align     = kwds['title_align']     if 'title_align'     in kwds else 'center'           # 标题对齐方式 left|center|right
        
        # label设置     
        label_color     = kwds['label_color']     if 'label_color'     in kwds else [1,1,1]            # 标题颜色
        label_size      = kwds['label_size']      if 'label_size'      in kwds else 32                 # 标注字号
        label_offset    = kwds['label_offset']    if 'label_offset'    in kwds else (0,0)              # 标注偏移量
        label_align     = kwds['label_align']     if 'label_align'     in kwds else 'center'           # 标注对齐方式 left|center|right
        label_precision = kwds['label_precision'] if 'label_precision' in kwds else None               # 标注文字精度，形如u'%.2f' u'%d'
        
        # 刻度线设置
        line_length     = kwds['line_length']     if 'ticket_line'     in kwds else 0.1                # 刻度线长度，0表示不显示刻度线
        line_color      = kwds['line_color']      if 'line_color'      in kwds else [1,1,1]            # 刻度线颜色
        
        # 其他设置
        ticklabel       = kwds['ticklabel']       if 'ticklabel'       in kwds else None               # 标注值列表，为None则按照调色板中的值显示
        bar_offset      = kwds['bar_offset']      if 'bar_offset'      in kwds else (0,0)              # ColorBar偏移量
        display         = kwds['display']         if 'display'         in kwds else True 
        
        # 计算当前region的宽度、高度（像素）
        w = int(self.box[2]*self.scene.size[0])
        h = int(self.box[3]*self.scene.size[1])
        vmin, vmax = np.nanmin(value), np.nanmax(value)
        
        # 计算刻度值
        if not ticklabel:
            ticklabel = self.getTickLabel(vmin, vmax)
        
        if orient in ['v', 'vertical']:
            x_min, x_max = -0.6+bar_offset[0], 0.0+bar_offset[0]
            y_min, y_max = -0.8*h/w+bar_offset[1], 0.7*h/w+bar_offset[1]
            
            totalxmin, totalxmax = -1, 1
            totalymin, totalymax = -h/w, h/w
            kx = (totalxmax-totalxmin)/w
            ky = (totalymax-totalymin)/h
            
            if title_name:
                textw, texth = self.getTextSize([title_name], title_size)[0]
                if title_align == "left":
                    xpos = x_min
                elif title_align == "right":
                    xpos = x_max - (kx*textw)
                else: # center
                    xpos = x_min + ((x_max-x_min) - (kx*textw)) / 2
                    
                title_pos = [xpos+title_offset[0], y_max+title_offset[1]+(ky*texth*0.4), 0.0]
                self.drawText(name, title_name, title_pos, title_size, title_color, display=display)
            
            x, y, z, c = list(), list(), list(), list()
            
            for i in range(len(value)):
                k = (value[i]-vmin) / (vmax-vmin)
                newy  = k * (y_max-y_min) + y_min
                x.append([x_min, x_max])
                y.append([newy, newy])
                z.append([0.0, 0.0])
                c.append([color[i], color[i]])
                
            x, y, z, c = np.array(x), np.array(y), np.array(z), np.array(c)/255.0
            self.drawSurface(name, x, y, z, c, method=0, mode=1, display=display)
            
            for i in range(len(ticklabel)):
                mark = label_precision % ticklabel[i] if label_precision else str(ticklabel[i])
                textw, texth  = self.getTextSize([mark], label_size)[0]
                kd = (ticklabel[i]-vmin) / (vmax-vmin)
                newy  = kd * (y_max-y_min) + y_min
                
                xpos = x_max + line_length + (totalxmax-totalxmin) * 0.04
                ypos = newy - (ky*texth)/2
                self.drawText(name, mark, [xpos+label_offset[0], ypos+label_offset[1], 0], label_size, label_color, display=display)
                
                if line_length > 0:
                    v = np.array([[x_max, newy, 0], [x_max+line_length, newy, 0]])
                    self.drawLine(name, v, np.array(line_color), method=0, width=1, stipple=(1,0xFFFF), display=display)
        
        elif orient in ['h', 'horizontal']:
            x_min, x_max = -0.7*w/h+bar_offset[0], 0.7*w/h+bar_offset[0]
            y_min, y_max = -0+bar_offset[1], 0.5+bar_offset[1]
            
            totalxmin, totalxmax = -w/h, w/h
            totalymin, totalymax = -1.0, 1.0
            kx = (totalxmax-totalxmin)/w
            ky = (totalymax-totalymin)/h
            
            if title_name:
                textw, texth = self.getTextSize([title_name], title_size)[0]
                if title_align == "left":
                    xpos = x_min
                elif title_align == "right":
                    xpos = x_max - (kx*textw)
                else: # center
                    xpos = x_min + ((x_max-x_min) - (kx*textw)) / 2
                    
                title_pos = [xpos+title_offset[0], y_max+title_offset[1]+(ky*texth*0.4), 0.0]
                self.drawText(name, title_name, title_pos, title_size, title_color, display=display)
                
            x, z, c = list(), list(), list()
            for i in range(len(value)-1, -1, -1):
                kd = (value[i]-vmin) / (vmax-vmin)
                newx  = kd * (x_max-x_min) + x_min
                x.append(newx)
                z.append(0.0)
                c.append(color[i])
                
            x, z, c = np.array(x), np.array(z), np.array(c)/255.0
            y = np.vstack((np.tile(np.array([y_max]), (1, len(x))), np.tile(np.array([y_min]), (1, len(x)))))
            x = np.tile(x, (2, 1))
            z = np.tile(z, (2, 1))
            c = np.tile(c, (2, 1, 1))
            
            self.drawSurface(name, x, y, z, c, method=0, mode=1, display=display)
            
            for i in range(len(ticklabel)):
                mark = label_precision % ticklabel[i] if label_precision else str(ticklabel[i])
                textw, texth  = self.getTextSize([mark], label_size)[0]
                kd = (ticklabel[i]-vmin) / (vmax-vmin)
                newx  = kd * (x_max-x_min) + x_min
                
                if label_align == "left":
                    xpos = newx
                elif label_align == "right":
                    xpos = newx - (kx * textw)
                else:
                    xpos = newx - (kx * textw)/2
                
                ypos = y_min - line_length - (ky * texth) - (totalymax-totalymin)*0.04
                self.drawText(name, mark, [xpos+label_offset[0], ypos+label_offset[1], 0], label_size, label_color, display=display)
                
                if line_length > 0:
                    v = np.array([[newx, y_min, 0], [newx, y_min-line_length, 0]])
                    self.drawLine(name, v, np.array(line_color), method=0, width=1, stipple=(1,0xFFFF), display=display)
        
        
        