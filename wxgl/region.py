# -*- coding: utf-8 -*-

import os, time
import wx
import numpy as np
from PIL import Image
import uuid
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo

from . import texture as wxTexture
from . import light as wxLight
from . import util

class Region:
    """GL视区类"""
    
    def __init__(self, scene, box, fixed, proj, zoom):
        """构造函数
        
        scene       - 视区所属场景对象
        box         - 视区位置四元组：四个元素分别表示视区左下角坐标、宽度、高度，元素值域[0,1]
        fixed       - 是否锁定相机位置：布尔型
        proj        - 投影模式：字符串，'ortho' - 正射投影，'frustum' - 透视投影（默认）
        zoom        - 视口缩放因子：None表示跟随场景缩放
        """
        
        self.scene = scene
        self.box = box
        self.fixed = fixed
        self.proj = proj
        self.zoom = zoom
        self.pos = None
        self.size = None
        self.aspect = None
        self.vision = None                                      # 视锥体左右下上边距离中心点的距离
        self.models = dict()                                    # 成品模型（已生成缓冲区对象）字典
        self.mnames = [list(), list()]                          # 模型名列表：不透明、透明
        self.ticks = dict()                                     # 刻度线
        self.r_x = [1e10, -1e10]                                # 数据在x轴上的动态范围
        self.r_y = [1e10, -1e10]                                # 数据在y轴上的动态范围
        self.r_z = [1e10, -1e10]                                # 数据在z轴上的动态范围
        self.scale = 1.0                                        # 模型缩放比例
        self.shift = np.array((0, 0, 0), dtype=np.float32)      # 模型位移量
        
        self.mmat = self.get_mmat()                             # 模型矩阵
        self.vmat = self.get_vmat()                             # 视点矩阵
        self.pmat = None                                        # 投影矩阵
        
        self.update_size()
    
    def update_size(self, box=None):
        """设置视区大小"""
        
        if not box is None:
            self.box = box
        
        self.pos = int(self.scene.csize[0] * self.box[0]), int(self.scene.csize[1] * self.box[1])
        self.size = int(self.scene.csize[0] * self.box[2]), int(self.scene.csize[1] * self.box[3])
        self.aspect = self.size[0]/self.size[1] if self.size[1] > 0 else 10000
        
        vision = 1 if self.proj == 'ortho' else 0.75
        
        if self.aspect > 1:
            self.vision = (-vision*self.aspect, vision*self.aspect, -vision, vision)
        else:
            self.vision = (-vision, vision, -vision/self.aspect, vision/self.aspect)
        
        if self.pmat is None:
            self.pmat = self.get_pmat()
        else:
            self.pmat[:] = self.get_pmat()
        
        self.set_range()
    
    def get_mmat(self):
        """返回模型矩阵"""
        
        return util.model_matrix(self.shift, self.scale)
    
    def get_vmat(self):
        """返回视点矩阵"""
        
        if self.fixed:
            return util.view_matrix((0.0,0.0,5.0), (0.0,1.0,0.0), (0.0,0.0,0.0))
        else:
            return self.scene.vmat
    
    def get_pmat(self):
        """返回投影矩阵"""
        
        hexa = (*self.vision, self.scene.near, self.scene.far)
        zoom = self.scene.zoom if self.zoom is None else self.zoom
        
        return util.proj_matrix(self.proj, hexa, zoom)
    
    def clear_buffer(self):
        """删除buffer"""
        
        for name in self.models:
            for m in self.models[name]:
                for item in m.cshaders:
                    glDeleteShader(item)
                glDeleteProgram(m.program)
            
                if m.indices:
                    m.indices['ibo'].delete()
                
                for key in m.attribute:
                    if 'bo' in m.attribute[key]:
                        m.attribute[key]['bo'].delete()
                
                textures = list()
                for key in m.uniform:
                    if 'texture' in m.uniform[key]:
                        textures.append(m.attribute[key]['texture'])
                if textures:
                    glDeleteTextures(len(textures), textures)
        
    def reset(self):
        """视区复位"""
        
        self.clear_buffer()
        self.models.clear()
        self.ticks.clear()
        self.mnames[0].clear()
        self.mnames[1].clear()
        self.r_x = [1e10, -1e10]
        self.r_y = [1e10, -1e10]
        self.r_z = [1e10, -1e10]
        self.scale = 1.0
        self.shift = np.array((0, 0, 0), dtype=np.float32)
        
        wx.CallAfter(self.scene.render)
    
    def set_model_visible(self, name, visible):
        """设置模型显示属性
        
        name        - 模型名
        visible     - 布尔值
        """
        
        if name in self.models:
            for m in self.models[name]:
                m.visible = visible
    
    def show_model(self, name):
        """显示模型
        
        nams        - 模型名
        """
        
        self.set_model_visible(name, True)
    
    def hide_model(self, name):
        """隐藏模型
        
        name        - 模型名
        """
        
        self.set_model_visible(name, False)
    
    def drop_model(self, name):
        """删除模型"""
        
        for group in self.mnames:
            group = [item for item in group if name not in item]
        
        if name in self.models:
            for m in self.models[name]:
                if m.indices:
                    m.indices['ibo'].delete()
            
                for key in m.attribute:
                    if 'bo' in m.attribute[key]:
                        m.attribute[key]['bo'].delete()
                
                textures = list()
                for key in m.uniform:
                    if 'texture' in m.uniform[key]:
                        textures.append(m.attribute[key]['texture'])
                if textures:
                    glDeleteTextures(len(textures), textures)
                
            del self.models[name]
    
    def set_range(self, r_x=None, r_y=None, r_z=None):
        """设置坐标轴范围
        
        r_x         - 二元组，x坐标轴范围
        r_y         - 二元组，y坐标轴范围
        r_z         - 二元组，z坐标轴范围
        """
        
        if r_x:
            if r_x[0] < self.r_x[0]:
                self.r_x[0] = r_x[0]
            if r_x[1] > self.r_x[1]:
                self.r_x[1] = r_x[1]
        
        if r_y:
            if r_y[0] < self.r_y[0]:
                self.r_y[0] = r_y[0]
            if r_y[1] > self.r_y[1]:
                self.r_y[1] = r_y[1]
        
        if r_z:
            if r_z[0] < self.r_z[0]:
                self.r_z[0] = r_z[0]
            if r_z[1] > self.r_z[1]:
                self.r_z[1] = r_z[1]
        
        dx, dy = self.r_x[1]-self.r_x[0], self.r_y[1]-self.r_y[0]
        if dx == 0:
            dx = 1e-10
        if dy == 0:
            dy = 1e-10
        
        if self.aspect > dx/dy:
            self.scale = 2/dy if self.aspect > 1 else 2/(self.aspect*dy)
        else:
            self.scale = 2*self.aspect/dx if self.aspect > 1 else 2/dx
        
        self.shift = np.array((-sum(self.r_x)/2, -sum(self.r_y)/2, -sum(self.r_z)/2), dtype=np.float32)
        self.mmat[:] = util.model_matrix(self.shift, self.scale)
        
        for name in self.models:
            for m in self.models[name]:
                for key in m.uniform: 
                    item = m.uniform[key]
                    if item['tag'] == 'mmat' and 'v' in item:
                        item.update({'o': np.dot(self.mmat, util.model_matrix(*item['v']))})
    
    def add_model(self, m, name=None):
        """添加模型
        
        main        - 模型实例
        name        - 模型名
        """
        
        m.verify()
        if m.islive:
            self.scene.islive = True
        
        m.cshaders.clear()
        for src, genre in m.shaders:
            m.cshaders.append(shaders.compileShader(src, genre))
        m.program = shaders.compileProgram(*m.cshaders)
        
        glUseProgram(m.program)
        
        if m.indices:
            m.indices.update({'ibo':vbo.VBO(m.indices['data'], target=GL_ELEMENT_ARRAY_BUFFER)})
        
        if m.inside:
            self.set_range(r_x=m.r_x, r_y=m.r_y, r_z=m.r_z)
        
        for key in m.attribute:
            item = m.attribute[key]
            if item['tag'] == 'psize':
                if isinstance(item['data'], (int, float)):
                    data = np.float32(np.ones(m.vshape[0]) * item['data'])
                    item.update({'data': data, 'usize':data.itemsize})
                else:
                    item.update({'usize':item['data'].itemsize})
            
            item.update({'bo': vbo.VBO(item['data'])})
            
            if 'loc' not in item:
                item.update({'loc': glGetAttribLocation(m.program, key)})
        
        for key in m.uniform:
            item = m.uniform[key]
            if item['tag'] == 'texture':
                item.update({'tid': item['data'].create_texture()})
            elif item['tag'] == 'pmat':
                if 'v' not in item and 'f' not in item:
                    item.update({'v': self.pmat})
            elif item['tag'] == 'vmat':
                if 'v' not in item and 'f' not in item:
                    item.update({'v': self.vmat})
            elif item['tag'] == 'mmat':
                if 'v' in item:
                    item.update({'o': np.dot(self.mmat, util.model_matrix(*item['v']))})
                else:
                    if 'f' not in item:
                        item.update({'o': self.mmat})
            
            if 'loc' not in item:
                item.update({'loc': glGetUniformLocation(m.program, key)})
        
        glUseProgram(0)
        
        if name is None:
            name = uuid.uuid1().hex
        
        if name in self.models:
            idx = len(self.models[name])
            self.models[name].append(m)
        else:
            idx = 0
            self.models.update({name: [m]})
        
        if m.opacity:
            self.mnames[0].append((name, idx, m.depth))
        else:
            self.mnames[1].append((name, idx, m.depth))
            self.mnames[1].sort(key=lambda item:item[2])
        
        wx.CallAfter(self.scene.render)
    
    def _get_normal(self, gltype, vs, indices=None, cw=False):
        """返回法线集"""
        
        if gltype not in (GL_TRIANGLES, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN):
            raise KeyError('%s不支持法线计算'%(str(gltype)))
        
        if not indices is None and gltype != GL_TRIANGLES:
            raise KeyError('当前图元类型不支持indices参数')
        
        n = vs.shape[0]
        if indices is None:
            if gltype == GL_TRIANGLE_FAN:
                a = np.zeros(n-2, dtype=np.int32)
                b = np.arange(1, n-1)
                c = np.arange(2, n)
                idx = np.stack((a, b, c), axis=1).ravel()
            elif gltype == GL_TRIANGLE_STRIP:
                a = np.append(0, np.stack((np.arange(3, n, 2, dtype=np.int32), np.arange(2, n, 2, dtype=np.int32)[:(n-2)//2]), axis=1).ravel())[:n-2]
                b = np.arange(1, n-1, dtype=np.int32)
                c = np.stack((np.arange(2, n, 2, dtype=np.int32), np.arange(1, n, 2, dtype=np.int32)[:(n-1)//2]), axis=1).ravel()[:n-2]
                idx = np.stack((a, b, c), axis=1).ravel()
            else:
                idx = np.arange(n, dtype=np.int32)
        else:
            idx = np.array(indices, dtype=np.int32)
        
        primitive = vs[idx]
        a = primitive[::3]
        b = primitive[1::3]
        c = primitive[2::3]
        normal = np.repeat(np.cross(b-a, a-c), 3, axis=0)
        
        #uniind = idx.size -1 - np.unique(np.flipud(idx), return_index=True)[1]
        uniind = np.unique(idx, return_index=True)[1]
        result = normal[uniind]
        return result
    
    def _get_tick_label(self, v_min, v_max, ks=(1, 2, 2.5, 3, 4, 5), s_min=4, s_max=8, extend=False):
        """返回合适的Colorbar标注值
        
        v_min       - 数据最小值
        v_max       - 数据最大值
        ks          - 分段选项
        s_min       - 分段数最小值
        s_max       - 分段数最大值
        extend      - 是否外延一个标注单位
        """
        
        r = v_max - v_min
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
        
        if result[0] > v_min:
            if extend:
                result.insert(0, 2*result[0]-result[1])
            elif (result[0]-v_min) < 0.3*(result[1]-result[0]):
                result[0] = v_min
            else:
                result.insert(0, v_min)
        if result[-1] < v_max:
            if extend:
                result.append(2*result[-1]-result[-2])
            elif (v_max-result[-1]) < 0.3*(result[-1]-result[-2]):
                result[-1] = v_max
            else:
                result.append(v_max)
        
        return result
    
    def text(self, text, pos, color=None, size=32, family=None, weight='normal', loc='left_bottom', **kwds):
        """2d文字
        
        text        - 文本字符串
        pos         - 文本位置：元组、列表或numpy数组，shape=(2|3,)
        color       - 文本颜色：浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用场景默认的前景颜色
        size        - 字号：整型，默认32
        family      - 字体：None表示当前默认的字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        loc         - pos对应文本区域的位置
            'left-top'      - 左上
            'left-middle'   - 左中
            'left-bottom'   - 左下
            'center-top'    - 上中
            'center-middle' - 中
            'center-bottom' - 下中
            'right-top'     - 右上
            'right-middle'  - 右中
            'right-bottom'  - 右下
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            slide           - 幻灯片函数，默认None
            ambient         - 环境光，默认(1.0,1.0,1.0)
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'slide', 'ambient']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        slide = kwds.get('slide')
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        
        if color is None:
            color = self.scene.style[1]
        
        box = np.tile(np.array(pos, dtype=np.float32), (4,1))
        texcoord = np.array([[0,0],[0,1],[1,0],[1,1]], dtype=np.float32)
                
        loc = {
            'left-top':         0, 
            'left-middle':      1, 
            'left-bottom':      2, 
            'center-top':       3, 
            'center-middle':    4, 
            'center-bottom':    5,
            'right-top':        6, 
            'right-middle':     7, 
            'right-bottom':     8
        }.get(loc, 2)
        
        th = 0.1 * size/32
        size = int(round(pow(size/64, 0.5) * 64))
        
        im_text = util.text2image(text, size, color, family, weight)
        tw = th * im_text.shape[1]/im_text.shape[0] * self.size[1]/self.size[0]
        texture = wxTexture.Texture(im_text, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        
        light = wxLight.BaseLight(ambient)
        self.add_model(light.get_model(GL_TRIANGLE_STRIP, box, 
            texture     = texture, 
            texcoord    = texcoord, 
            loc         = loc, 
            tw          = tw, 
            th          = th, 
            visible     = visible, 
            opacity     = False, 
            inside      = inside, 
            slide       = slide
        ), name)
    
    def text3d(self, text, box, color=None, size=64, family=None, weight='normal', align='fill', valign='fill', **kwds):
        """3d文字
        
        text        - 文本字符串
        box         - 文本显式区域：左上、左下、右上、右下4个点的坐标，浮点型元组、列表或numpy数组，shape=(4,2|3)
        color       - 文本颜色：浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用场景默认的前景颜色
        size        - 字号：整型，默认64。此参数影响文本显示质量，不改变文本大小
        family      - 字体：None表示当前默认的字体
        weight      - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        align       - 文本宽度方向对齐方式
            'fill'          - 填充
            'left'          - 左对齐
            'right'         - 右对齐
            'center'        - 居中对齐
        valign      - 文本高度方向对齐方式
            'fill'          - 填充
            'top'           - 上对齐
            'bottom'        - 下对齐
            'middle'        - 居中对齐
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        light = kwds.get('light', wxLight.SunLight())
        
        gltype = GL_TRIANGLE_STRIP
        box = np.array(box, dtype=np.float32)
        normal = self._get_normal(gltype, box)
        
        if color is None:
            color = self.scene.style[1]
         
        im_text = util.text2image(text, size, color, family, weight)
        texture = wxTexture.Texture(im_text, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        texcoord = np.array([[0,0],[0,1],[1,0],[1,1]], dtype=np.float32)
        
        box_width = np.linalg.norm(box[2] - box[0])
        box_height = np.linalg.norm(box[0] - box[1])

        k_box, k_text = box_width/box_height, im_text.shape[1]/im_text.shape[0]
        
        if k_text > k_box:
            if valign != 'fill':
                align = 'fill'
        else:
            if align != 'fill':
                valign = 'fill'
        
        if align == 'fill':
            if valign == 'top':
                offset = (box[1] - box[0])*k_box/k_text
                box[1] = box[0] + offset
                box[3] = box[2] + offset
            elif valign == 'middle':
                offset = (box[1]-box[0])*(1-k_box/k_text)/2
                box[0] += offset
                box[2] += offset
                box[1] -= offset
                box[3] -= offset
            elif valign == 'bottom':
                offset = (box[0]-box[1])*k_box/k_text
                box[0] = box[1] + offset
                box[2] = box[3] + offset
        elif align == 'left':
            offset = (box[3]-box[1])*k_text/k_box
            box[3] = box[1] + offset
            box[2] = box[0] + offset
        elif align == 'right':
            offset = (box[0] - box[2])*k_text/k_box
            box[0] = box[2] + offset
            box[1] = box[3] + offset
        elif align == 'center':
            offset = (box[2] - box[0])*(1-k_text/k_box)/2
            box[0] += offset
            box[1] += offset
            box[2] -= offset
            box[3] -= offset
        
        self.add_model(light.get_model(gltype, box,
            normal      = normal, 
            texture     = texture, 
            texcoord    = texcoord, 
            visible     = visible, 
            opacity     = False, 
            inside      = inside, 
            slide       = slide,
            transform   = transform
        ), name)
        
    def point(self, vs, color=None, size=1.0, **kwds):
        """散列点
        
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
        size        - 点的大小：数值或数值型元组、列表或numpy数组
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            opacity         - 模型不透明属性，默认True（不透明）
            inside          - 模型顶点是否影响模型空间，默认True
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient         - 环境光，默认(1.0,1.0,1.0)
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'slide', 'transform', 'ambient']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        
        if color is None:
            color = self.scene.style[1]
        
        color = np.array(color, dtype=np.float32)
        if color.ndim == 1:
            color = np.tile(color, (len(vs),1))
        
        if isinstance(size, (int, float)):
            size = np.ones(len(vs), dtype=np.float32) * size
        else:
            size = np.float32(size)
        
        light = wxLight.BaseLight(ambient)
        self.add_model(light.get_model(GL_POINTS, vs, 
            color       = color, 
            psize       = size, 
            visible     = visible, 
            opacity     = opacity, 
            inside      = inside, 
            slide       = slide,
            transform   = transform
        ), name)
    
    def line(self, vs, color=None, method='strip', width=None, stipple=None, **kwds):
        """线段
        
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
        method      - 绘制方法
            'isolate'       - 独立线段
            'strip'         - 连续线段
            'loop'          - 闭合线段
        width       - 线宽：0.0~10.0之间，None使用默认设置
        stipple     - 线型：整数和两字节十六进制整数组成的元组，形如(1,0xFFFF)。None使用默认设置
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认True（不透明）
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient         - 环境光，默认(1.0,1.0,1.0)
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'slide', 'transform', 'ambient']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        
        if color is None:
            color = self.scene.style[1]
        
        color = np.array(color, dtype=np.float32)
        if color.ndim == 1:
            color = np.tile(color, (len(vs),1))
        
        method = method.upper()
        if method == "ISOLATE":
            gltype = GL_LINES
        elif method == "STRIP":
            gltype = GL_LINE_STRIP
        elif method == "LOOP":
            gltype = GL_LINE_LOOP
        else:
            raise ValueError('不支持的线段方法：%s'%method)
        
        light = wxLight.BaseLight(ambient)
        self.add_model(light.get_model(gltype, vs, 
            color       = color,
            lw          = width,
            ls          = stipple,
            visible     = visible, 
            opacity     = opacity, 
            inside      = inside, 
            slide       = slide,
            transform   = transform
        ), name)
    
    def surface(self, vs, color=None, texture=None, texcoord=None, method='isolate', indices=None, **kwds):
        """曲面
        
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理：wxgl.Texture对象
        texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
        method      - 绘制方法
            'isolate'       - 独立三角面
            'strip'         - 带状三角面
            'fan'           - 扇面
        indices     - 顶点索引集，默认None，表示不使用索引
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认True（不透明）
            fill            - 填充，默认None（使用当前设置）
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'fill', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        light = kwds.get('light', wxLight.SunLight())
        
        method = method.upper()
        if method == "ISOLATE":
            gltype = GL_TRIANGLES
        elif method == "STRIP":
            gltype = GL_TRIANGLE_STRIP
        elif method == "FAN":
            gltype = GL_TRIANGLE_FAN
        else:
            raise ValueError('不支持的三角面方法：%s'%method)
        
        if gltype != GL_TRIANGLES and not indices is None:
            raise ValueError('STRIP或FAN不支持indices参数')
        
        vs = np.array(vs, dtype=np.float32)
        normal = self._get_normal(gltype, vs, indices)
        
        if not color is None:
            color = np.array(color, dtype=np.float32)
            if color.ndim == 1:
                color = np.tile(color, (len(vs),1))
        
        self.add_model(light.get_model(gltype, vs,
            indices     = indices,
            normal      = normal, 
            color       = color,
            texture     = texture, 
            texcoord    = texcoord, 
            visible     = visible, 
            inside      = inside, 
            opacity     = opacity,
            fill        = fill,
            slide       = slide,
            transform   = transform
        ), name)
        
    def mesh(self, xs, ys, zs, color=None, texture=None, cw=False, closed=False, **kwds):
        """网格面
        
        xs/ys/zs    - 顶点坐标集：元组、列表或numpy数组，shape=(m,n)，m为网格行数，n为网格列数
        color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理：wxgl.Texture对象
        cw          - 三角面顶点索引顺序：布尔型，True表示顺时针，False表示逆时针
        closed      - 网格闭合：布尔型。该参数仅用于使用经纬度网格生成球
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            fill            - 填充，默认None（使用当前设置）
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'fill', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        light = kwds.get('light', wxLight.SunLight())
        
        vs = np.dstack((xs, ys, zs))
        rows, cols = vs.shape[:2]
        vs = vs.reshape(-1,3)
        
        idx = np.arange(rows*cols).reshape(rows, cols)
        idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[1:,1:], idx[:-1, 1:]
        indices = np.int32(np.dstack((idx_a, idx_d, idx_b, idx_c, idx_b, idx_d)).ravel())
        
        normal = self._get_normal(GL_TRIANGLES, vs, indices).reshape(rows,cols,-1)
        normal[0] += normal[-1]
        normal[-1] = normal[0]
        normal[:,0] += normal[:,-1]
        normal[:,-1] = normal[:,0]
        
        if color is None:
            u = np.linspace(0, 1, cols)
            v = np.linspace(1, 0, rows)
            texcoord = np.float32(np.dstack(np.meshgrid(u,v)).reshape(-1,2))
        else:
            texcoord = None
            color = np.array(color, dtype=np.float32)
            
            if color.ndim == 1:
                color = np.tile(color, (len(vs),1))
            
            if color.ndim > 2:
                color = color.reshape(-1, color.shape[-1])
        
        self.add_model(light.get_model(GL_TRIANGLES, vs,
            indices     = indices,
            normal      = normal, 
            color       = color,
            texture     = texture, 
            texcoord    = texcoord, 
            visible     = visible, 
            inside      = inside, 
            opacity     = opacity,
            fill        = fill,
            slide       = slide,
            transform   = transform
        ), name)
        
    def uvsphere(self, center, r, lon=(0,360), lat=(-90,90), color=None, texture=None, slices=90, **kwds):
        """使用经纬度网格生成球
        
        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        lon         - 经度范围：默认0°~360°
        lat         - 纬度范围：默认-90°~90°
        color       - 颜色：浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理：wxgl.Texture对象
        slices      - 圆周分片数：整型
        xflip       - 2D纹理左右翻转：布尔型，默认False
        yflip       - 2D纹理上下翻转：布尔型，False
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            slide           - 幻灯片函数，默认None
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            fill            - 填充，默认None（使用当前设置）
            ambient         - 环境亮度，开启灯光时默认(0.5, 0.5, 0.5)，关闭灯光时默认(1.0, 1.0, 1.0)
            light           - 平行光源的方向，默认(-0.5, -0.1, -0.5)，None表示关闭灯光
            light_color     - 平行光源的颜色，默认(1.0, 1.0, 1.0)
            shininess       - 高光系数，值域范围[0,1]，默认0.0（无镜面反射）
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'slide', 'inside', 'opacity', 'transform', 'fill', 'ambient', 'light', 'light_color', 'shininess']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        lon_0, lon_1 = np.radians(lon[0]), np.radians(lon[1])
        lat_0, lat_1 = np.radians(lat[0]), np.radians(lat[1])
        lats, lons = np.mgrid[lat_0:lat_1:complex(0,slices//2+1), lon_0:lon_1:complex(0,slices+1)]
        
        zs = -r * np.cos(lats)*np.cos(lons) + center[2]
        xs = r * np.cos(lats)*np.sin(lons) + center[0]
        ys = r * np.sin(lats) + center[1]
        
        self.mesh(xs, ys, zs, color=color, texture=texture, **kwds)
        
    def isosphere(self, center, r, color=None, iterations=5, **kwds):
        """通过对正八面体的迭代细分生成球
        
        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        color       - 颜色：浮点型元组、列表或numpy数组，值域范围[0,1]
        iterations  - 迭代次数：整型
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            fill            - 填充，默认None（使用当前设置）
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 平行光源的方向，默认(-0.5, -0.1, -0.5)，None表示关闭灯光
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'fill', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        light = kwds.get('light', wxLight.SunLight())
        
        vs = np.array([[r,0,0], [0,r,0], [-r,0,0], [0,-r,0], [0,0,r], [0,0,-r]])
        idx = np.array([4,0,1,4,1,2,4,2,3,4,3,0,5,0,3,5,3,2,5,2,1,5,1,0])
        vs = vs[idx]
        
        for i in range(iterations):
            p0 = (vs[::3] + vs[1::3]) / 2
            p0 = r * p0 / np.linalg.norm(p0, axis=1).reshape(-1, 1)
            p1 = (vs[1::3] + vs[2::3]) / 2
            p1 = r * p1 / np.linalg.norm(p1, axis=1).reshape(-1, 1)
            p2 = (vs[::3] + vs[2::3]) / 2
            p2 = r * p2 / np.linalg.norm(p2, axis=1).reshape(-1, 1)
            vs = np.stack((vs[::3],p0,p2,vs[1::3],p1,p0,vs[2::3],p2,p1,p0,p1,p2),axis=1).reshape(-1,3)
        vs += np.array(center)
        
        color = np.array(color, dtype=np.float32)
        if color.ndim == 1:
            color = np.tile(color, (len(vs),1))
        
        gltype = GL_TRIANGLES
        normal = self._get_normal(gltype, vs)
        
        self.add_model(light.get_model(gltype, vs,
            normal      = normal, 
            color       = color,
            visible     = visible, 
            inside      = inside, 
            opacity     = opacity,
            fill        = fill,
            slide       = slide,
            transform   = transform
        ), name)
    
    def cone(self, spire, center, r, color=None, base=True, slices=90, **kwds):
        """圆锥
        
        spire       - 锥尖：元组、列表或numpy数组
        center      - 锥底圆心：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        color       - 颜色：浮点型元组、列表或numpy数组，值域范围[0,1]
        base        - 是否绘制锥底：默认True
        slices      - 圆周分片数：整型
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            slide           - 幻灯片函数，默认None
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            fill            - 填充，默认None（使用当前设置）
            ambient         - 环境亮度，开启灯光时默认(0.5, 0.5, 0.5)，关闭灯光时默认(1.0, 1.0, 1.0)
            light           - 平行光源的方向，默认(-0.5, -0.1, -0.5)，None表示关闭灯光
            light_color     - 平行光源的颜色，默认(1.0, 1.0, 1.0)
            shininess       - 高光系数，值域范围[0,1]，默认0.0（无镜面反射）
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'slide', 'inside', 'opacity', 'transform', 'fill', 'ambient', 'light', 'light_color', 'shininess']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        if 'name' not in kwds:
            kwds.update({'name': uuid.uuid1().hex})
        
        spire = np.array(spire)
        center = np.array(center)
        m_rotate = util.y2v(spire - center)
        
        theta = np.linspace(0, 2*np.pi, slices+1)
        xs = r * np.cos(theta)
        zs = -r * np.sin(theta)
        ys = np.zeros_like(theta)
        vs = np.stack((xs,ys,zs), axis=1)
        vs = np.dot(vs, m_rotate) + center
        
        self.surface(np.vstack((spire, vs)), color=color, method='fan', **kwds)
        if base:
            self.surface(np.vstack((center, vs)), color=color, method='fan', **kwds)
    
    def cylinder(self, c1, c2, r, color=None, base=True, slices=90, **kwds):
        """圆柱
        
        c1          - 圆柱端面圆心：元组、列表或numpy数组
        c2          - 圆柱端面圆心：元组、列表或numpy数组
        r           - 圆柱半径：浮点型
        color       - 颜色：浮点型元组、列表或numpy数组，值域范围[0,1]
        base        - 是否绘制圆柱端面：默认True
        slices      - 圆周分片数：整型
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            slide           - 幻灯片函数，默认None
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            fill            - 填充，默认None（使用当前设置）
            ambient         - 环境亮度，开启灯光时默认(0.5, 0.5, 0.5)，关闭灯光时默认(1.0, 1.0, 1.0)
            light           - 平行光源的方向，默认(-0.5, -0.1, -0.5)，None表示关闭灯光
            light_color     - 平行光源的颜色，默认(1.0, 1.0, 1.0)
            shininess       - 高光系数，值域范围[0,1]，默认0.0（无镜面反射）
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'slide', 'inside', 'opacity', 'transform', 'fill', 'ambient', 'light', 'light_color', 'shininess']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        if 'name' not in kwds:
            kwds.update({'name': uuid.uuid1().hex})
        
        c1 = np.array(c1)
        c2 = np.array(c2)
        m_rotate = util.y2v(c1 - c2)
        
        theta = np.linspace(0, 2*np.pi, slices+1)
        xs = r * np.cos(theta)
        zs = -r * np.sin(theta)
        ys = np.zeros_like(theta)
        vs = np.stack((xs,ys,zs), axis=1)
        vs = np.dot(vs, m_rotate)
        
        vs1 = vs + c1
        vs2 = vs + c2
        
        self.surface(np.stack((vs1, vs2), axis=1).reshape(-1,3), color=color, method='strip', **kwds)
        if base:
            self.surface(np.vstack((c1, vs1)), color=color, method='fan', **kwds)
            self.surface(np.vstack((c2, vs2)), color=color, method='fan', **kwds)
    
    def isosurface(self, data, level, color, x=None, y=None, z=None, **kwds):
        """三维等值面
        
        data        - 数据集：三维numpy数组
        level       - 阈值：浮点型。data数据集中小于level的数据将被忽略
        color       - 颜色：浮点型元组、列表或numpy数组，值域范围[0,1]
        x/y/z       - 数据集对应的点的x/y/z轴的动态范围
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            slide           - 幻灯片函数，默认None
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            fill            - 填充，默认None（使用当前设置）
            ambient         - 环境亮度，开启灯光时默认(0.5, 0.5, 0.5)，关闭灯光时默认(1.0, 1.0, 1.0)
            light           - 平行光源的方向，默认(-0.5, -0.1, -0.5)，None表示关闭灯光
            light_color     - 平行光源的颜色，默认(1.0, 1.0, 1.0)
            shininess       - 高光系数，值域范围[0,1]，默认0.0（无镜面反射）
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'slide', 'inside', 'opacity', 'transform', 'fill', 'ambient', 'light', 'light_color', 'shininess']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        vs, ids = util.isosurface(data, level)
        #ids = np.stack((ids[:,0], ids[:,2], ids[:,1]), axis=1)
        indices = ids.ravel()
        
        xs = vs[:,0] if x is None else (x[1] - x[0]) * vs[:,0] / data.shape[0] + x[0]
        ys = vs[:,1] if y is None else (y[1] - y[0]) * vs[:,1] / data.shape[1] + y[0]
        zs = vs[:,2] if z is None else (z[1] - z[0]) * vs[:,2] / data.shape[2] + z[0]
        vs = np.stack((xs, ys, zs), axis=1)
        
        self.surface(vs[indices], color=color, indices=None, **kwds)
    
    def colorbar(self, cm, drange, box, mode='V', **kwds):
        """绘制colorBar 
        
        cm          - 调色板名称
        drange      - 值域范围或刻度序列：长度大于1的元组或列表
        box         - 调色板位置：左上、左下、右上、右下的坐标
        mode        - 水平或垂直模式：可选项：'H'|'V'
        kwds        - 关键字参数
                            subject         - 标题
                            tick_format     - 刻度标注格式化函数，默认str
                            density         - 刻度密度，最少和最多刻度线组成的元组，默认(3,6)
                            endpoint        - 刻度是否包含值域范围的两个端点值
        """
        
        for key in kwds:
            if key not in ['subject', 'tick_format', 'density', 'endpoint']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        if not mode in ('H','h','V','v'):
            raise ValueError('不支持的选项：%s'%mode)
        
        text_size = 48 # 此参数影响文本显示质量，不改变文本大小
        mode = mode.upper()
        
        subject = kwds.get('subject', None)
        tick_format = kwds.get('tick_format', str)
        s_min, s_max = kwds.get('density', (3,6))
        endpoint = kwds.get('endpoint', False)
        
        dmin, dmax = drange[0], drange[-1]
        if len(drange) > 2:
            ticks = drange
        else:
            ticks = self._get_tick_label(dmin, dmax, s_min=s_min, s_max=s_max)
       
        if endpoint:
            if (ticks[1]-ticks[0])/(ticks[2]-ticks[1]) < 0.2:
                ticks.remove(ticks[1])
            if (ticks[-1]-ticks[-2])/(ticks[-2]-ticks[-3]) < 0.2:
                ticks.remove(ticks[-2])
        else:
            ticks = ticks[1:-1]
        
        texcoord = np.array(((0,1),(0,0),(1,1),(1,0)), dtype=np.float32)
        colors = util.CM.cmap(np.linspace(dmin, dmax, 256), cm)
        
        if mode == 'H':
            texture = np.uint8(np.tile(255*colors, (2,1)).reshape(2,256,-1))
        else:
            texture = np.uint8(np.tile(255*colors[::-1], 2).reshape(256,2,-1))
        
        if mode == 'V':
            u = box[2,0] - box[0,0]
            h = box[0,1] - box[1,1]
            if not subject is None:
                vs_subject = np.array([
                    [box[0,0], box[0,1]+1.2*u],
                    [box[0,0], box[0,1]+0.4*u],
                    [box[2,0], box[2,1]+0.4*u],
                    [box[2,0], box[2,1]+1.2*u]
                ])
                self.text3d(subject, vs_subject, align='left', valign='fill', size=text_size, inside=False)
            
            tk = h/(dmax-dmin)
            dashes = list()
            for t in ticks:
                y = (t-dmin)*tk + box[1,1]
                dashes.extend([[box[2,0], y], [box[2,0]+0.4*u, y]])
                vs_tick = np.array([
                    [box[2,0]+0.6*u, y+0.25*u],
                    [box[2,0]+0.6*u, y-0.25*u],
                    [box[2,0]+3*u, y-0.25*u],
                    [box[2,0]+3*u, y+0.25*u]
                ])
                self.text3d(tick_format(t), vs_tick, align='left', valign='fill', size=text_size, inside=False)
            
            self.line(np.array(dashes, dtype=np.float32), method='isolate', width=0.5, inside=False)
        else:
            u = box[0,1] - box[1,1]
            w = box[2,0] - box[0,0]
            if not subject is None:
                vs_subject = np.array([
                    [box[0,0], box[0,1]+1.4*u],
                    [box[0,0], box[0,1]+0.3*u],
                    [box[2,0], box[2,1]+0.3*u],
                    [box[2,0], box[2,1]+1.4*u]
                ])
                self.text3d(subject, vs_subject, align='center', valign='fill', size=text_size, inside=False)
            
            tk = w/(dmax-dmin)
            dashes = list()
            for t in ticks:
                x = (t-dmin)*tk + box[1,0]
                dashes.extend([[x, box[1,1]], [x, box[1,1]-0.4*u]])
                vs_tick = np.array([
                    [x-u, box[1,1]-0.65*u],
                    [x-u, box[1,1]-1.35*u],
                    [x+u, box[1,1]-1.35*u],
                    [x+u, box[1,1]-0.65*u]
                ])
                self.text3d(tick_format(t), vs_tick, align='center', valign='fill', size=text_size, inside=False)
            
            self.line(np.array(dashes, dtype=np.float32), method='isolate', width=0.5, inside=False)
        
        self.surface(box, texture=texture, texcoord=texcoord, method='strip', inside=False)
        
    def ticks3d(self, xlabel='X', ylabel='Y', zlabel='Z', **kwds):
        """绘制3D网格和刻度
        
        xlabel      - x轴名称，默认'X'
        ylabel      - y轴名称，默认'Y'
        zlabel      - z轴名称，默认'Z'
        kwds        - 关键字参数
                            visible         - 是否可见，默认可见
                            xr              - x轴范围或刻度标注序列，元组，默认None
                            yr              - y轴范围或刻度标注序列，元组，默认None
                            zr              - z轴范围或刻度标注序列，元组，默认None
                            xf              - x轴刻度标注格式化函数，默认str
                            yf              - y轴刻度标注格式化函数，默认str
                            zf              - z轴刻度标注格式化函数，默认str
                            xd              - x轴刻度密度调整，整型，值域范围[-2,10], 默认0
                            yd              - y轴刻度密度调整，整型，值域范围[-2,10], 默认0
                            zd              - z轴刻度密度调整，整型，值域范围[-2,10], 默认0
                            lc              - 网格线颜色，浮点型元组、列表或numpy数组，值域范围[0,1]，默认使用前景色
                            lw              - 网格线宽度，默认0.5
                            bg              - 网格背景色，接受元组、列表或numpy数组形式的RGBA颜色
                            extend          - 网格外延，默认False
                            tick_size       - 刻度标注字号，默认32
                            label_size      - 坐标轴标注字号，默认40
        """
        
        for key in kwds:
            if key not in ['visible', 'xr','yr','zr','xf','yf','zf','xd','yd','zd','lc','lw','bg','extend','tick_size','label_size']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        # 删除当前的刻度模型（如果存在的话）
        for key in self.ticks:
            self.drop_model(self.ticks[key])
        self.ticks.clear()
        
        visible = kwds.get('visible', True)
        xr = kwds.get('xr', None)
        yr = kwds.get('yr', None)
        zr = kwds.get('zr', None)
        xf = kwds.get('xf', str)
        yf = kwds.get('yf', str)
        zf = kwds.get('zf', str)
        xd = kwds.get('xd', 0)
        yd = kwds.get('yd', 0)
        zd = kwds.get('zd', 0)
        lc = kwds.get('lc', self.scene.style[1])
        lw = kwds.get('lw', 0.5)
        bg = kwds.get('bg', (0.9,1.0,0.6,0.1))
        extend = kwds.get('extend', False)
        tick_size = kwds.get('tick_size', 32) + 16
        label_size = kwds.get('label_size', 40) + 16
        
        xd = max(-2, xd)
        yd = max(-2, yd)
        zd = max(-2, zd)
        
        if xr is None:
            if self.r_x[0] >= self.r_x[-1]:
                return # '模型空间不存在，返回
            dx = (self.r_x[1] - self.r_x[0]) * 0.1
            xx = self._get_tick_label(self.r_x[0]-dx, self.r_x[1]+dx, s_min=4+xd, s_max=6+xd, extend=extend)
        elif len(xr) == 2:
            xx = self._get_tick_label(xr[0], xr[-1], s_min=4+xd, s_max=6+xd, extend=extend)
        else:
            xx = xr
        
        if yr is None:
            if self.r_y[0] >= self.r_y[-1]:
                return # '模型空间不存在，返回
            dy = (self.r_y[1] - self.r_y[0]) * 0.1
            yy = self._get_tick_label(self.r_y[0]-dy, self.r_y[1]+dy, s_min=4+yd, s_max=6+yd, extend=extend)
        elif len(yr) == 2:
            yy = self._get_tick_label(yr[0], yr[-1], s_min=4+yd, s_max=6+yd, extend=extend)
        else:
            yy = yr
        
        if zr is None:
            if self.r_z[0] >= self.r_z[-1]:
                return # '模型空间不存在，返回
            dz = (self.r_z[1] - self.r_z[0]) * 0.1
            zz = self._get_tick_label(self.r_z[0]-dz, self.r_z[1]+dz, s_min=4+zd, s_max=6+zd, extend=extend)
        elif len(zr) == 2:
            zz = self._get_tick_label(zr[0], zr[-1], s_min=4+zd, s_max=6+zd, extend=extend)
        else:
            zz = xr
        
        u = max((xx[-1]-xx[0]), (yy[-1]-yy[0]), (zz[-1]-zz[0])) * 0.02 # 调整间隙的基本单位
        
        self.ticks.update({'top': uuid.uuid1().hex})
        self.ticks.update({'bottom': uuid.uuid1().hex})
        self.ticks.update({'left': uuid.uuid1().hex})
        self.ticks.update({'right': uuid.uuid1().hex})
        self.ticks.update({'front': uuid.uuid1().hex})
        self.ticks.update({'back': uuid.uuid1().hex})
        
        self.ticks.update({'x_ymin_zmin': uuid.uuid1().hex})
        self.ticks.update({'x_ymin_zmax': uuid.uuid1().hex})
        self.ticks.update({'x_ymax_zmin': uuid.uuid1().hex})
        self.ticks.update({'x_ymax_zmax': uuid.uuid1().hex})
        self.ticks.update({'y_xmin_zmin': uuid.uuid1().hex})
        self.ticks.update({'y_xmin_zmax': uuid.uuid1().hex})
        self.ticks.update({'y_xmax_zmin': uuid.uuid1().hex})
        self.ticks.update({'y_xmax_zmax': uuid.uuid1().hex})
        self.ticks.update({'z_xmin_ymin': uuid.uuid1().hex})
        self.ticks.update({'z_xmin_ymax': uuid.uuid1().hex})
        self.ticks.update({'z_xmax_ymin': uuid.uuid1().hex})
        self.ticks.update({'z_xmax_ymax': uuid.uuid1().hex})
        
        vs_zmin, vs_zmax = list(), list()
        for x in xx:
            vs_zmin.append((x, yy[0], zz[0]))
            vs_zmin.append((x, yy[-1], zz[0]))
            vs_zmax.append((x, yy[0], zz[-1]))
            vs_zmax.append((x, yy[-1], zz[-1]))
        for y in yy:
            vs_zmin.append((xx[0], y, zz[0]))
            vs_zmin.append((xx[-1], y, zz[0]))
            vs_zmax.append((xx[0], y, zz[-1]))
            vs_zmax.append((xx[-1], y, zz[-1]))
        
        vs_xmin, vs_xmax = list(), list()
        for y in yy:
            vs_xmin.append((xx[0], y, zz[0]))
            vs_xmin.append((xx[0], y, zz[-1]))
            vs_xmax.append((xx[-1], y, zz[0]))
            vs_xmax.append((xx[-1], y, zz[-1]))
        for z in zz:
            vs_xmin.append((xx[0], yy[0], z))
            vs_xmin.append((xx[0], yy[-1], z))
            vs_xmax.append((xx[-1], yy[0], z))
            vs_xmax.append((xx[-1], yy[-1], z))
        
        vs_ymin, vs_ymax = list(), list()
        for x in xx:
            vs_ymin.append((x, yy[0], zz[0]))
            vs_ymin.append((x, yy[0], zz[-1]))
            vs_ymax.append((x, yy[-1], zz[0]))
            vs_ymax.append((x, yy[-1], zz[-1]))
        for z in zz:
            vs_ymin.append((xx[0], yy[0], z))
            vs_ymin.append((xx[-1], yy[0], z))
            vs_ymax.append((xx[0], yy[-1], z))
            vs_ymax.append((xx[-1], yy[-1], z))
        
        self.line(np.array(vs_ymax), color=lc, width=lw, method='isolate', inside=False, name=self.ticks['top'], visible=visible)
        self.line(np.array(vs_ymin), color=lc, width=lw, method='isolate', inside=False, name=self.ticks['bottom'], visible=visible)
        self.line(np.array(vs_xmax), color=lc, width=lw, method='isolate', inside=False, name=self.ticks['right'], visible=visible)
        self.line(np.array(vs_xmin), color=lc, width=lw, method='isolate', inside=False, name=self.ticks['left'], visible=visible)
        self.line(np.array(vs_zmax), color=lc, width=lw, method='isolate', inside=False, name=self.ticks['front'], visible=visible)
        self.line(np.array(vs_zmin), color=lc, width=lw, method='isolate', inside=False, name=self.ticks['back'], visible=visible)
        
        vs_top = [[xx[0],yy[-1],zz[0]], [xx[0],yy[-1],zz[-1]], [xx[-1],yy[-1],zz[0]], [xx[-1],yy[-1],zz[-1]]]
        vs_bottom = [[xx[0],yy[0],zz[0]], [xx[0],yy[0],zz[-1]], [xx[-1],yy[0],zz[0]], [xx[-1],yy[0],zz[-1]]]
        vs_left = [[xx[0],yy[-1],zz[0]], [xx[0],yy[0],zz[0]], [xx[0],yy[-1],zz[-1]], [xx[0],yy[0],zz[-1]]]
        vs_right = [[xx[-1],yy[-1],zz[0]], [xx[-1],yy[0],zz[0]], [xx[-1],yy[-1],zz[-1]], [xx[-1],yy[0],zz[-1]]]
        vs_front = [[xx[0],yy[-1],zz[-1]], [xx[0],yy[0],zz[-1]], [xx[-1],yy[-1],zz[-1]], [xx[-1],yy[0],zz[-1]]]
        vs_back = [[xx[0],yy[-1],zz[0]], [xx[0],yy[0],zz[0]], [xx[-1],yy[-1],zz[0]], [xx[-1],yy[0],zz[0]]]
        
        self.surface(vs_top, color=bg, method='strip', inside=False, opacity=False, name=self.ticks['top'], visible=visible)
        self.surface(vs_bottom, color=bg, method='strip', inside=False, opacity=False, name=self.ticks['bottom'], visible=visible)
        self.surface(vs_left, color=bg, method='strip', inside=False, opacity=False, name=self.ticks['left'], visible=visible)
        self.surface(vs_right, color=bg, method='strip', inside=False, opacity=False, name=self.ticks['right'], visible=visible)
        self.surface(vs_front, color=bg, method='strip', inside=False, opacity=False, name=self.ticks['front'], visible=visible)
        self.surface(vs_back, color=bg, method='strip', inside=False, opacity=False, name=self.ticks['back'], visible=visible)
        
        for x in xx[1:-1]:
            self.text(xf(x), pos=(x, yy[0]-u, zz[-1]+u), size=tick_size, loc='center-top', inside=False, name=self.ticks['x_ymin_zmax'], visible=visible)
            self.text(xf(x), pos=(x, yy[-1]+u, zz[-1]+u), size=tick_size, loc='center-bottom', inside=False, name=self.ticks['x_ymax_zmax'], visible=visible)
            self.text(xf(x), pos=(x, yy[0]-u, zz[0]-u), size=tick_size, loc='center-top', inside=False, name=self.ticks['x_ymin_zmin'], visible=visible)
            self.text(xf(x), pos=(x, yy[-1]+u, zz[0]-u), size=tick_size, loc='center-bottom', inside=False, name=self.ticks['x_ymax_zmin'], visible=visible)
        
        for y in yy[1:-1]:
            self.text(yf(y), pos=(xx[-1]+u, y, zz[-1]+u), size=tick_size, loc='right-middle', inside=False, name=self.ticks['y_xmax_zmax'], visible=visible)
            self.text(yf(y), pos=(xx[-1]+u, y, zz[0]-u), size=tick_size, loc='right-middle', inside=False, name=self.ticks['y_xmax_zmin'], visible=visible)
            self.text(yf(y), pos=(xx[0]-u, y, zz[-1]+u), size=tick_size, loc='right-middle', inside=False, name=self.ticks['y_xmin_zmax'], visible=visible)
            self.text(yf(y), pos=(xx[0]-u, y, zz[0]-u), size=tick_size, loc='right-middle', inside=False, name=self.ticks['y_xmin_zmin'], visible=visible)
        
        for z in zz[1:-1]:
            self.text(zf(z), pos=(xx[-1]+u, yy[-1]+u, z), size=tick_size, loc='left-middle', inside=False, name=self.ticks['z_xmax_ymax'], visible=visible)
            self.text(zf(z), pos=(xx[-1]+u, yy[0]-u, z), size=tick_size, loc='left-middle', inside=False, name=self.ticks['z_xmax_ymin'], visible=visible)
            self.text(zf(z), pos=(xx[0]-u, yy[-1]+u, z), size=tick_size, loc='right-middle', inside=False, name=self.ticks['z_xmin_ymax'], visible=visible)
            self.text(zf(z), pos=(xx[0]-u, yy[0]-u, z), size=tick_size, loc='right-middle', inside=False, name=self.ticks['z_xmin_ymin'], visible=visible)
        
        if xlabel:
            self.text(xlabel, pos=((xx[0]+xx[-1])/2, yy[-1]+u, zz[0]), size=label_size, loc='center-bottom', inside=False, name=self.ticks['x_ymin_zmax'], visible=visible)
            self.text(xlabel, pos=((xx[0]+xx[-1])/2, yy[0]-u, zz[0]), size=label_size, loc='center-top', inside=False, name=self.ticks['x_ymax_zmax'], visible=visible)
            self.text(xlabel, pos=((xx[0]+xx[-1])/2, yy[-1]+u, zz[-1]), size=label_size, loc='center-bottom', inside=False, name=self.ticks['x_ymin_zmin'], visible=visible)
            self.text(xlabel, pos=((xx[0]+xx[-1])/2, yy[0]-u, zz[-1]), size=label_size, loc='center-top', inside=False, name=self.ticks['x_ymax_zmin'], visible=visible)
        
        if ylabel:
            self.text(ylabel, pos=(xx[0], (yy[0]+yy[-1])/2, zz[0]-u), size=label_size, loc='left-middle', inside=False, name=self.ticks['y_xmax_zmax'], visible=visible)
            self.text(ylabel, pos=(xx[0]-u, (yy[0]+yy[-1])/2, zz[-1]), size=label_size, loc='left-middle', inside=False, name=self.ticks['y_xmax_zmin'], visible=visible)
            self.text(ylabel, pos=(xx[-1]+u, (yy[0]+yy[-1])/2, zz[0]), size=label_size, loc='left-middle', inside=False, name=self.ticks['y_xmin_zmax'], visible=visible)
            self.text(ylabel, pos=(xx[-1]+u, (yy[0]+yy[-1])/2, zz[-1]), size=label_size, loc='left-middle', inside=False, name=self.ticks['y_xmin_zmin'], visible=visible)
        
        if zlabel:
            self.text(zlabel, pos=(xx[0], yy[0]-u, (zz[0]+zz[-1])/2), size=label_size, loc='center-top', inside=False, name=self.ticks['z_xmax_ymax'], visible=visible)
            self.text(zlabel, pos=(xx[0], yy[-1]+u, (zz[0]+zz[-1])/2), size=label_size, loc='center-bottom', inside=False, name=self.ticks['z_xmax_ymin'], visible=visible)
            self.text(zlabel, pos=(xx[-1], yy[0]-u, (zz[0]+zz[-1])/2), size=label_size, loc='center-top', inside=False, name=self.ticks['z_xmin_ymax'], visible=visible)
            self.text(zlabel, pos=(xx[-1], yy[-1]+u, (zz[0]+zz[-1])/2), size=label_size, loc='center-bottom', inside=False, name=self.ticks['z_xmin_ymin'], visible=visible)
    