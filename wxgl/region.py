# -*- coding: utf-8 -*-

import os
import wx
import numpy as np
from PIL import Image
import uuid
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo

from . texture import Texture
from . light import *
from . import util

DIST = 5.0
NEAR = 3.0
FAR = 1000.0

class Region:
    """WxGL视区类"""
    
    def __init__(self, scene, box, **kwds):
        """构造函数
        
        scene       - 视区所属场景对象
        box         - 视区位置四元组：四个元素分别表示视区左下角坐标、宽度、高度，元素值域[0,1]
        kwds        - 关键字参数
            proj        - 投影模式：'O' - 正射投影，'P' - 透视投影（默认）
            fixed       - 锁定模式：固定ECS原点、相机位置和角度，以及视口缩放因子等。布尔型，默认False
            azim        - 方位角：-180°~180°范围内的浮点数，默认0°
            elev        - 高度角：-180°~180°范围内的浮点数，默认0°
            azim_range  - 方位角限位器：默认-180°~180°
            elev_range  - 仰角限位器：默认-180°~180°
            zoom        - 视口缩放因子：默认1.0
            name        - 视区名
        """
        
        for key in kwds:
            if key not in ['proj', 'fixed', 'azim', 'elev', 'azim_range', 'elev_range', 'zoom', 'name']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        self.scene = scene                                                  # 视区所属场景对象
        self.box = box                                                      # 视区位置四元组
        
        self.proj = kwds.get('proj', 'P')[0].upper()                        # 投影模式
        self.fixed = kwds.get('fixed', False)                               # 锁定模式
        self.azim = kwds.get('azim', 0.0)                                   # 初始方位角
        self.elev = kwds.get('elev', 0.0)                                   # 初始高度角
        self.azim_range = kwds.get('azim_range', (-180, 180))               # 方位角限位器
        self.elev_range = kwds.get('elev_range', (-180, 180))               # 仰角限位器
        self.zoom = kwds.get('zoom', 1.0)                                   # 视口缩放因子
        self.name = kwds.get('name', uuid.uuid1().hex)                      # 视区名
        
        self.oecs = [0.0, 0.0, 0.0]                                         # 视点坐标系ECS原点
        self.dist = DIST                                                    # 相机与ECS原点的距离
        self.near = NEAR                                                    # 视锥体前面距离相机的距离
        self.far = FAR                                                      # 视锥体后面距离相机的距离
        self.scale = 1.0                                                    # 缩放比例
        self.cam = [0.0, 0.0, 5.0]                                          # 相机位置
        self.up = [0.0, 1.0, 0.0]                                           # 指向相机上方的单位向量
        self.cam_cruise = None                                              # 相机巡航函数
        self.posture = dict()                                               # 存储相机姿态、缩放比例等设置参数的字典
        
        self.pos = None                                                     # 视区左下角坐标（像素表示）
        self.size = None                                                    # 视区大小（像素表示）
        self.aspect = None                                                  # 视区宽高像素比
        self.vision = None                                                  # 视锥体左右下上边距离中心点的距离
        
        self.models = dict()                                                # 成品模型（已生成缓冲区对象）字典
        self.mnames = [list(), list()]                                      # 模型名列表：不透明、透明
        self.ticks = dict()                                                 # 刻度线
        self.r_x = [1e10, -1e10]                                            # 数据在x轴上的动态范围
        self.r_y = [1e10, -1e10]                                            # 数据在y轴上的动态范围
        self.r_z = [1e10, -1e10]                                            # 数据在z轴上的动态范围
        
        self.mmat = np.eye(4, dtype=np.float32)                             # 模型矩阵
        self.vmat = np.eye(4, dtype=np.float32)                             # 视点矩阵
        self.pmat = np.eye(4, dtype=np.float32)                             # 投影矩阵
        
        self.reset_box()
        self.save_posture()
    
    def _update_cam_and_up(self, oecs=None, dist=None, azim=None, elev=None):
        """根据当前ECS原点位置、距离、方位角、仰角等参数，重新计算相机位置和up向量"""
        
        if not oecs is None:
            self.oecs = [*oecs,]
        
        if not dist is None:
            self.dist = dist
        
        if not azim is None:
            azim = (azim+180)%360 - 180
            if azim < self.azim_range[0]:
                self.azim = self.azim_range[0]
            elif azim > self.azim_range[1]:
                self.azim = self.azim_range[1]
            else:
                self.azim = azim
        
        if not elev is None:
            elev = (elev+180)%360 - 180
            if elev < self.elev_range[0]:
                self.elev = self.elev_range[0]
            elif elev > self.elev_range[1]:
                self.elev = self.elev_range[1]
            else:
                self.elev = elev
        
        azim, elev  = np.radians(self.azim), np.radians(self.elev)
        d = self.dist * np.cos(elev)
        
        self.cam[1] = self.dist * np.sin(elev) + self.oecs[1]
        self.cam[2] = d * np.cos(azim) + self.oecs[2]
        self.cam[0] = d * np.sin(azim) + self.oecs[0]
        self.up[1] = 1.0 if -90 <= self.elev <= 90 else -1.0
        
        self.vmat[:] = util.view_matrix(self.cam, self.up, self.oecs)
    
    def _clear_buffer(self):
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
    
    def _update_pmat(self):
        """更新投影矩阵"""
        
        self.pmat[:] = util.proj_matrix(self.proj, (*self.vision, self.near, self.far), self.zoom)
    
    def _motion(self, ctr, dx, dy):
        """鼠标移动"""
        
        if self.fixed:
            return
        
        if ctr:
            oecs = [self.oecs[0]-dx/(self.scene.csize[0]*self.scale), self.oecs[1]+dy/(self.scene.csize[1]*self.scale), self.oecs[2]]
            self._update_cam_and_up(oecs=oecs)
        else:
            azim = self.azim - self.up[1]*(180*dx/self.scene.csize[0])
            elev = self.elev + 90*dy/self.scene.csize[1]
            self._update_cam_and_up(azim=azim, elev=elev)
    
    def _wheel(self, ctr, wr):
        """鼠标滚轮"""
        
        if self.fixed:
            return
        
        if ctr:
            if wr < 0:
                dist = self.dist * 1.01
            else:
                dist = self.dist * 0.99
            
            self._update_cam_and_up(dist=dist)
        else:
            if wr < 0:
                self.zoom *= 1.05
                if self.zoom > 100:
                    self.zoom = 100
            else:
                self.zoom *= 0.95
                if self.zoom < 0.01:
                    self.zoom = 0.01
            
            self._update_pmat()
    
    def _get_normal(self, gltype, vs, indices=None):
        """返回法线集"""
        
        if gltype not in (GL_TRIANGLES, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN, GL_QUADS, GL_QUAD_STRIP):
            raise KeyError('%s不支持法线计算'%(str(gltype)))
        
        if not indices is None and gltype != GL_TRIANGLES and gltype != GL_QUADS:
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
            elif gltype == GL_QUAD_STRIP:
                a = np.arange(0, n-2, 2)
                b = np.arange(1, n-2, 2)
                c = np.arange(3, n, 2)
                d = np.arange(2, n, 2)
                idx = np.stack((a, b, c, d), axis=1).ravel()
            else:
                idx = np.arange(n, dtype=np.int32)
        else:
            idx = np.array(indices, dtype=np.int32)
        
        primitive = vs[idx]
        if gltype == GL_QUADS or gltype == GL_QUAD_STRIP:
            a = primitive[::4]
            b = primitive[1::4]
            c = primitive[2::4]
            d = primitive[3::4]
            normal = np.repeat(np.cross(c-a, b-d), 4, axis=0)
        else:
            a = primitive[::3]
            b = primitive[1::3]
            c = primitive[2::3]
            normal = np.repeat(np.cross(b-a, a-c), 3, axis=0)
        
        if indices is None and (gltype == GL_TRIANGLES or gltype == GL_QUADS):
            return normal
        
        result = np.zeros((n,3), dtype=np.float32)
        idx_arg = np.argsort(idx)
        rise = np.where(np.diff(idx[idx_arg])==1)[0]+1
        rise = np.hstack((0,rise,len(idx)))
        
        for i in range(n):
            result[i] = np.sum(normal[idx_arg[rise[i]:rise[i+1]]], axis=0)
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
    
    def reset_box(self, box=None):
        """重置视区位置和大小"""
        
        if not box is None:
            self.box = box
        
        self.pos = int(self.scene.csize[0] * self.box[0]), int(self.scene.csize[1] * self.box[1])
        self.size = int(self.scene.csize[0] * self.box[2]), int(self.scene.csize[1] * self.box[3])
        self.aspect = self.size[0]/self.size[1] if self.size[1] > 0 else 10000
        
        self.set_range()
    
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
        
        dx, dy, dz = self.r_x[1]-self.r_x[0], self.r_y[1]-self.r_y[0], self.r_z[1]-self.r_z[0]
        
        if dx > 0 and dy > 0:
            if self.aspect > dx/dy:
                self.scale = 2/dy if self.aspect > 1 else 2/(self.aspect*dy)
            else:
                self.scale = 2*self.aspect/dx if self.aspect > 1 else 2/dx
        elif dx > 0 and dy <= 0:
            self.scale = 2*self.aspect/dx if self.aspect > 1 else 2/dx
        elif dx <= 0 and dy > 0:
            self.scale = 2/dy if self.aspect > 1 else 2/(self.aspect*dy)
        
        if self.scale * dz > 4:
            self.scale = 4/dz
        
        self.near = NEAR/self.scale
        self.far = FAR/self.scale
        vision = 1/self.scale if self.proj == 'O' else 0.75/self.scale
        
        if self.aspect > 1:
            self.vision = (-vision*self.aspect, vision*self.aspect, -vision, vision)
        else:
            self.vision = (-vision, vision, -vision/self.aspect, vision/self.aspect)
        
        self._update_pmat()
        
        oecs = [sum(self.r_x)/2, sum(self.r_y)/2, sum(self.r_z)/2]
        dist = DIST/self.scale
        self._update_cam_and_up(oecs=oecs, dist=dist)
        self.posture.update({'oecs': [*self.oecs,]})
        
    def set_cam_cruise(self, func):
        """设置相机巡航函数"""
        
        if hasattr(func, '__call__'):
            self.cam_cruise = func
            self.scene.islive = True
    
    def save_posture(self):
        """保存相机姿态"""
        
        self.posture.update({
            'oecs': [*self.oecs,],
            'zoom': self.zoom,
            'azim': self.azim,
            'elev': self.elev
        })
    
    def restore_posture(self):
        """还原相机姿态"""
        
        self._update_cam_and_up(oecs=self.posture['oecs'], dist=DIST/self.scale, azim=self.posture['azim'], elev=self.posture['elev'])
        self.zoom = self.posture['zoom']
        self._update_pmat()
        
    def clear(self):
        """清空视区"""
        
        self._clear_buffer()
        self.models.clear()
        self.ticks.clear()
        self.mnames[0].clear()
        self.mnames[1].clear()
        self.r_x = [1e10, -1e10]
        self.r_y = [1e10, -1e10]
        self.r_z = [1e10, -1e10]
        self.scale = 1.0
        
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
        
        name        - 模型名
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
    
    def add_model(self, m, name=None):
        """添加模型
        
        m           - wxgl.Model实例
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
                if item['data'].tid is None:
                    item['data'].create_texture()
                item.update({'tid': item['data'].tid})
            elif item['tag'] == 'pmat':
                if 'v' not in item and 'f' not in item:
                    item.update({'v': self.pmat})
            elif item['tag'] == 'vmat':
                if 'v' not in item and 'f' not in item:
                    item.update({'v': self.vmat})
            elif item['tag'] == 'mmat':
                if 'v' not in item and 'f' not in item:
                    item.update({'v': self.mmat})
                elif 'v' in item:
                    item.update({'v': util.model_matrix(*item['v'])})
            
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
    
    def text(self, text, pos, color=None, size=32, loc='left_bottom', **kwds):
        """2d文字
        
        text        - 文本字符串
        pos         - 文本位置：元组、列表或numpy数组，shape=(2|3,)
        color       - 文本颜色：浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用场景默认的前景颜色
        size        - 字号：整型，默认32
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
            family          - 字体：None表示当前默认的字体
            weight          - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'slide', 'ambient', 'family', 'weight']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        slide = kwds.get('slide')
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        family = kwds.get('family')
        weight = kwds.get('weight', 'normal')
        
        if color is None:
            color = self.scene.style[1]
        elif isinstance(color, (tuple, list, np.ndarray)):
            color = np.float32(color)
            if color.shape != (3,) and color.shape != (4,):
                raise KeyError('期望color参数为浮点类型RGB或RGBA颜色')
        else:
            raise KeyError('期望color参数为浮点类型元组、列表或numpy数组')
        
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
        
        th = min(self.vision[1],self.vision[-1]) * 0.2 * size/32
        size = int(round(pow(size/64, 0.5) * 64))
        
        im_text = util.text2image(text, size, color, family, weight)
        tw = th * im_text.shape[1]/im_text.shape[0] * self.size[1]/self.size[0]
        texture = Texture(im_text, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        
        light = BaseLightText2d(ambient)
        self.add_model(light.get_model(GL_TRIANGLE_STRIP, box, 
            texture     = texture, 
            texcoord    = texcoord, 
            loc         = loc, 
            tw          = tw, 
            th          = th, 
            visible     = visible, 
            inside      = inside, 
            opacity     = False, 
            slide       = slide
        ), name)
    
    def text3d(self, text, box, color=None, align='fill', valign='fill', **kwds):
        """3d文字
        
        text        - 文本字符串
        box         - 文本显式区域：左上、左下、右上、右下4个点的坐标，浮点型元组、列表或numpy数组，shape=(4,2|3)
        color       - 文本颜色：浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用场景默认的前景颜色
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
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列，默认None
            ambient         - 环境光，默认(1.0,1.0,1.0)
            family          - 字体：None表示当前默认的字体
            weight          - 字体的浓淡：'normal'-正常（默认），'light'-轻，'bold'-重
            size            - 字号：整型，默认64。此参数影响文本显示质量，不改变文本大小
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'cull', 'slide', 'transform', 'ambient', 'family', 'weight', 'size']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        cull = kwds.get('cull')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        family = kwds.get('family')
        weight = kwds.get('weight', 'normal')
        size = kwds.get('size', 64)
        
        if color is None:
            color = self.scene.style[1]
        elif isinstance(color, (tuple, list, np.ndarray)):
            color = np.float32(color)
            if color.shape != (3,) and color.shape != (4,):
                raise KeyError('期望color参数为浮点类型RGB或RGBA颜色')
        else:
            raise KeyError('期望color参数为浮点类型元组、列表或numpy数组')
        
        gltype = GL_TRIANGLE_STRIP
        box = np.array(box, dtype=np.float32)
        normal = self._get_normal(gltype, box)
         
        im_text = util.text2image(text, size, color, family, weight)
        texture = Texture(im_text, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
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
        
        light = BaseLight(ambient)
        self.add_model(light.get_model(gltype, box,
            normal      = normal, 
            texture     = texture, 
            texcoord    = texcoord, 
            visible     = visible, 
            opacity     = False, 
            inside      = inside, 
            cull        = cull,
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
            if key not in ['name', 'visible', 'inside', 'slide', 'transform', 'ambient']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        
        vs = np.array(vs, dtype=np.float32)
        n = vs.shape[0]
        
        if color is None:
            color = self.scene.style[1]
        
        color = np.array(color, dtype=np.float32)
        if color.ndim == 1:
            color = np.tile(color, (n,1))
        
        if color.ndim != 2 or color.shape[0] != n or color.shape[1] not in (3,4):
            raise KeyError('期望color参数为%d个RGB或RGBA颜色组成的浮点型数组'%n)
        
        if isinstance(size, (int, float)):
            size = np.ones(n, dtype=np.float32) * size
        else:
            size = np.float32(size)
            if size.ndim != 1 or size.shape[0] != n:
                raise KeyError('期望size参数为长度等于%d的浮点型数组'%n)
        
        idx = np.argsort(vs[...,-1])
        light = BaseLightPoint(ambient)
        self.add_model(light.get_model(GL_POINTS, vs[idx], 
            color       = color[idx], 
            psize       = size[idx], 
            visible     = visible, 
            opacity     = False, 
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
        
        vs = np.array(vs, dtype=np.float32)
        n = vs.shape[0]
        
        if color is None:
            color = self.scene.style[1]
        
        color = np.array(color, dtype=np.float32)
        if color.ndim == 1:
            color = np.tile(color, (n,1))
        
        if color.ndim != 2 or color.shape[0] != n or color.shape[1] not in (3,4):
            raise KeyError('期望color参数为%d个RGB或RGBA颜色组成的浮点型数组'%n)
        
        method = method.upper()
        if method == "ISOLATE":
            gltype = GL_LINES
        elif method == "STRIP":
            gltype = GL_LINE_STRIP
        elif method == "LOOP":
            gltype = GL_LINE_LOOP
        else:
            raise ValueError('不支持的线段方法：%s'%method)
        
        light = BaseLight(ambient)
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
    
    def surface(self, vs, color=None, texture=None, texcoord=None, method='isolate', indices=None, closed=False, **kwds):
        """三角曲面
        
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理：wxgl.Texture对象
        texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
        method      - 绘制方法
            'isolate'       - 独立三角面
            'strip'         - 带状三角面
            'fan'           - 扇面
        indices     - 顶点索引集，默认None，表示不使用索引
        closed      - 带状三角面或扇面两端闭合：布尔型
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认True（不透明）
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull')
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        light = kwds.get('light', SunLight())
        
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
        
        if closed:
            if gltype == GL_TRIANGLE_STRIP:
                normal[0] += normal[-2]
                normal[1] += normal[-1]
                normal[-2] = normal[0]
                normal[-1] = normal[1]
            if gltype == GL_TRIANGLE_FAN:
                normal[1] += normal[-1]
                normal[-1] = normal[1]
        
        if color is None and texture is None:
            raise KeyError('缺少颜色或纹理参数')
        
        if color is None:
            if not isinstance(texture, Texture):
                raise KeyError('期望纹理参数为wxgl.Texture类型')
            
            if texcoord is None:
                raise KeyError('缺少纹理坐标参数')
            
            texcoord = np.float32(texcoord)
            #if texcoord.ndim != 2 or texcoord.shape[0] != vs.shape[0] or texcoord.shape[1] != 2:
            #    raise KeyError('期望纹理坐标参数为%d行2列的浮点型数组'%vs.shape[0])
        else:
            if not isinstance(color, (tuple, list, np.ndarray)):
                raise KeyError('期望颜色参数为元组、列表或numpy数组类型')
            
            color = np.array(color, dtype=np.float32)
            if color.ndim == 1:
                color = np.tile(color, (vs.shape[0],1))
            
            if color.ndim != 2 or color.shape[0] != vs.shape[0] or color.shape[1] not in (3,4):
                raise KeyError('期望颜色参数为%d个RGB或RGBA颜色组成的浮点型数组'%vs.shape[0])
        
        self.add_model(light.get_model(gltype, vs,
            indices     = indices,
            normal      = normal, 
            color       = color,
            texture     = texture, 
            texcoord    = texcoord, 
            visible     = visible, 
            inside      = inside, 
            opacity     = opacity,
            cull        = cull,
            fill        = fill,
            slide       = slide,
            transform   = transform
        ), name)
    
    def quad(self, vs, color=None, texture=None, texcoord=None, method='isolate', indices=None, closed=False, **kwds):
        """四角曲面
        
        vs          - 顶点集：元组、列表或numpy数组，shape=(n,2|3)
        color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理：wxgl.Texture对象
        texcoord    - 纹理坐标集：元组、列表或numpy数组，shape=(n,2|3)
        method      - 绘制方法
            'isolate'       - 独立四角面
            'strip'         - 带状四角面
        indices     - 顶点索引集，默认None，表示不使用索引
        closed      - 带状三角面或扇面两端闭合：布尔型
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认True（不透明）
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull')
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        light = kwds.get('light', SunLight())
        
        method = method.upper()
        if method == "ISOLATE":
            gltype = GL_QUADS
        elif method == "STRIP":
            gltype = GL_QUAD_STRIP
        else:
            raise ValueError('不支持的四角面方法：%s'%method)
        
        if gltype == GL_QUAD_STRIP and not indices is None:
            raise ValueError('STRIP不支持indices参数')
        
        vs = np.array(vs, dtype=np.float32)
        normal = self._get_normal(gltype, vs, indices)
        
        if closed and gltype == GL_QUAD_STRIP:
            normal[0] += normal[-2]
            normal[1] += normal[-1]
            normal[-2] = normal[0]
            normal[-1] = normal[1]
        
        if color is None and texture is None:
            raise KeyError('缺少颜色或纹理参数')
        
        if color is None:
            if not isinstance(texture, Texture):
                raise KeyError('期望纹理参数为wxgl.Texture类型')
            
            if texcoord is None:
                raise KeyError('缺少纹理坐标参数')
            
            texcoord = np.float32(texcoord)
            #if texcoord.ndim != 2 or texcoord.shape[0] != vs.shape[0] or texcoord.shape[1] not in (2,3):
            #    raise KeyError('期望纹理坐标参数为%d行2列的浮点型数组'%vs.shape[0])
        else:
            if not isinstance(color, (tuple, list, np.ndarray)):
                raise KeyError('期望颜色参数为元组、列表或numpy数组类型')
            
            color = np.array(color, dtype=np.float32)
            if color.ndim == 1:
                color = np.tile(color, (vs.shape[0],1))
            
            if color.ndim != 2 or color.shape[0] != vs.shape[0] or color.shape[1] not in (3,4):
                raise KeyError('期望颜色参数为%d个RGB或RGBA颜色组成的浮点型数组'%vs.shape[0])
        
        self.add_model(light.get_model(gltype, vs,
            indices     = indices,
            normal      = normal, 
            color       = color,
            texture     = texture, 
            texcoord    = texcoord, 
            visible     = visible, 
            inside      = inside, 
            opacity     = opacity,
            cull        = cull,
            fill        = fill,
            slide       = slide,
            transform   = transform
        ), name)
        
    def mesh(self, xs, ys, zs, color=None, texture=None, ur=(0,1), vr=(0,1), method='T', uclosed=False, vclosed=False, **kwds):
        """网格面
        
        xs/ys/zs    - 顶点坐标集：元组、列表或numpy数组，shape=(m,n)，m为网格行数，n为网格列数
        color       - 颜色或颜色集：浮点型元组、列表或numpy数组，值域范围[0,1]
        texture     - 纹理：wxgl.Texture对象
        ur          - u方向纹理坐标范围
        vr          - v方向纹理坐标范围
        method      - 绘制网格的方法：可选项：'T'- GL_TRIANGLES, 'Q' - GL_QUADS
        uclosed     - u方向网格两端闭合：布尔型
        vclosed     - v方向网格两端闭合：布尔型
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'opacity', 'cull', 'fill', 'slide', 'transform', 'light']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        opacity = kwds.get('opacity', True)
        cull = kwds.get('cull')
        fill = kwds.get('fill')
        slide = kwds.get('slide')
        transform = kwds.get('transform')
        light = kwds.get('light', SunLight())
        
        vs = np.dstack((xs, ys, zs))
        rows, cols = vs.shape[:2]
        vs = vs.reshape(-1,3)
        
        if color is None and texture is None:
            raise KeyError('缺少颜色或纹理参数')
        
        if color is None:
            if not isinstance(texture, Texture):
                raise KeyError('期望纹理参数为wxTexture.Texture类型')
            
            u = np.linspace(ur[0], ur[1], cols)
            v = np.linspace(vr[0], vr[1], rows)
            texcoord = np.float32(np.dstack(np.meshgrid(u,v)).reshape(-1,2))
        else:
            if not isinstance(color, (tuple, list, np.ndarray)):
                raise KeyError('期望颜色参数为元组、列表或numpy数组类型')
            
            texcoord = None
            color = np.array(color, dtype=np.float32)
            
            if color.ndim == 1:
                color = np.tile(color, (rows*cols,1))
            
            if color.ndim > 2:
                color = color.reshape(-1, color.shape[-1])
        
        gltype = GL_TRIANGLES if method[0].upper() == 'T' else GL_QUADS
        
        idx = np.arange(rows*cols).reshape(rows, cols)
        idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[1:,1:], idx[:-1, 1:]
        if gltype == GL_TRIANGLES:
            indices = np.int32(np.dstack((idx_a, idx_b, idx_d, idx_c, idx_d, idx_b)).ravel())
        else:
            indices = np.int32(np.dstack((idx_a, idx_b, idx_c, idx_d)).ravel())
        normal = self._get_normal(gltype, vs, indices).reshape(rows,cols,-1)
        
        if vclosed:
            normal[0] += normal[-1]
            normal[-1] = normal[0]
        
        if uclosed:
            normal[:,0] += normal[:,-1]
            normal[:,-1] = normal[:,0]
        
        self.add_model(light.get_model(gltype, vs,
            indices     = indices,
            normal      = normal, 
            color       = color,
            texture     = texture, 
            texcoord    = texcoord, 
            visible     = visible, 
            inside      = inside, 
            opacity     = opacity,
            cull        = cull,
            fill        = fill,
            slide       = slide,
            transform   = transform
        ), name)

    def cylinder(self, c1, c2, r, color=None, texture=None, ur=(0,1), vr=(0,1), arc=(0,360), cell=5, **kwds):
        """圆柱
        
        c1          - 圆柱端面圆心：元组、列表或numpy数组
        c2          - 圆柱端面圆心：元组、列表或numpy数组
        r           - 圆柱半径：浮点型
        color       - 颜色：浮点型元组、列表或numpy数组
        texture     - 纹理：wxgl.Texture对象
        ur          - u方向纹理坐标范围
        vr          - v方向纹理坐标范围
        arc         - 弧度角范围：默认0°~360°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        c1 = np.array(c1)
        c2 = np.array(c2)
        m_rotate = util.y2v(c1 - c2)
        
        arc_0, arc_1, cell = np.radians(min(arc)), np.radians(max(arc)), np.radians(cell)
        slices = round(abs(arc_0-arc_1)/cell)
        
        theta = np.linspace(arc_0, arc_1, slices)
        xs = r * np.cos(theta)
        zs = -r * np.sin(theta)
        ys = np.zeros_like(theta)
        vs = np.stack((xs,ys,zs), axis=1)
        vs = np.dot(vs, m_rotate)
        vs = np.stack((vs+c1, vs+c2), axis=0)
        
        xs = vs[..., 0]
        ys = vs[..., 1]
        zs = vs[..., 2]
        
        if color is None and texture is None:
            color = self.scene.style[1]
        
        self.mesh(xs, ys, zs, color=color, texture=texture, ur=ur, vr=vr, uclosed=abs(arc[0]-arc[1])==360, **kwds)

    def torus(self, center, r1, r2, vec=(0,1,0), color=None, texture=None, ur=(0,1), vr=(0,1), u=(0,360), v=(-180,180), cell=5, **kwds):
        """球环
        
        center      - 球环中心坐标：元组、列表或numpy数组
        r1          - 球半径：浮点型
        r2          - 环半径：浮点型
        vec         - 环面法向量
        color       - 颜色：浮点型元组、列表或numpy数组
        texture     - 纹理：wxgl.Texture对象
        ur          - u方向纹理坐标范围
        vr          - v方向纹理坐标范围
        u           - u方向范围：默认0°~360°
        v           - v方向范围：默认-90°~90°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        u_0, u_1 = np.radians(min(u)), np.radians(max(u))
        v_0, v_1 = np.radians(max(v)), np.radians(min(v))
        cell = np.radians(cell)
        u_slices, v_slices = round(abs(u_0-u_1)/cell), round(abs(v_0-v_1)/cell)
        gv, gu = np.mgrid[v_0:v_1:complex(0,v_slices), u_0:u_1:complex(0,u_slices)]
        
        xs = (r2 + r1 * np.cos(gv)) * np.cos(gu)
        zs = -(r2 + r1 * np.cos(gv)) * np.sin(gu)
        ys = r1 * np.sin(gv)
        
        m_rotate = util.y2v(vec)
        vs = np.dot(np.dstack((xs, ys, zs)), m_rotate) + center
        xs, ys, zs = vs[...,0], vs[...,1], vs[...,2]
        
        uclosed = abs(u[0]-u[1])==360
        vclosed = abs(v[0]-v[1])==360
        
        if color is None and texture is None:
            color = self.scene.style[1]
        
        self.mesh(xs, ys, zs, color=color, texture=texture, ur=ur, vr=vr, uclosed=uclosed, vclosed=vclosed, **kwds)
    
    def uvsphere(self, center, r, vec=(0,1,0), color=None, texture=None, ur=(0,1), vr=(0,1), u=(0,360), v=(-90,90), cell=5, **kwds):
        """使用经纬度网格生成球
        
        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        vec         - 轴向量
        color       - 颜色：浮点型元组、列表或numpy数组
        texture     - 纹理：wxgl.Texture对象
        ur          - u方向纹理坐标范围
        vr          - v方向纹理坐标范围
        u           - u方向范围：默认0°~360°
        v           - v方向范围：默认-90°~90°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        
        u_0, u_1 = np.radians(min(u)), np.radians(max(u))
        v_0, v_1 = np.radians(max(v)), np.radians(min(v))
        cell = np.radians(cell)
        u_slices, v_slices = round(abs(u_0-u_1)/cell), round(abs(v_0-v_1)/cell)
        gv, gu = np.mgrid[v_0:v_1:complex(0,v_slices), u_0:u_1:complex(0,u_slices)]
        
        zs = -r * np.cos(gv)*np.sin(gu)
        xs = r * np.cos(gv)*np.cos(gu)
        ys = r * np.sin(gv)
        
        m_rotate = util.y2v(vec)
        vs = np.dot(np.dstack((xs, ys, zs)), m_rotate) + center
        xs, ys, zs = vs[...,0], vs[...,1], vs[...,2]
        
        if color is None and texture is None:
            color = self.scene.style[1]
        
        self.mesh(xs, ys, zs, color=color, texture=texture, ur=ur, vr=vr, uclosed=abs(u[0]-u[1])==360, **kwds)

    def isosphere(self, center, r, color=None, iterations=5, **kwds):
        """通过对正八面体的迭代细分生成球
        
        center      - 锥底圆心坐标：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        color       - 颜色：浮点型元组、列表或numpy数组
        iterations  - 迭代次数：整型
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
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
        
        if color is None:
            color = self.scene.style[1]
        
        self.surface(vs, color=color, method='isolate', **kwds)

    def circle(self, center, r, vec=(0,1,0), color=None, arc=(0,360), cell=5, **kwds):
        """圆
        
        center      - 锥底圆心：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        vec         - 圆面法向量
        color       - 颜色：浮点型元组、列表或numpy数组
        arc         - 弧度角范围：默认0°~360°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        center = np.array(center)
        m_rotate = util.y2v(vec)
        
        arc_0, arc_1, cell = np.radians(min(arc)), np.radians(max(arc)), np.radians(cell)
        slices = round(abs(arc_0-arc_1)/cell)
        
        theta = np.linspace(arc_0, arc_1, slices)
        xs = r * np.cos(theta)
        zs = -r * np.sin(theta)
        ys = np.zeros_like(theta)
        
        vs = np.stack((xs,ys,zs), axis=1)
        vs = np.dot(vs, m_rotate) + center
        vs = np.vstack((center, vs))
        
        if color is None:
            color = self.scene.style[1]
        
        self.surface(vs, color=color, method='fan', indices=None, closed=abs(arc[0]-arc[1])==360, **kwds)

    def cone(self, spire, center, r, color=None, arc=(0,360), cell=5, **kwds):
        """圆锥
        
        spire       - 锥尖：元组、列表或numpy数组
        center      - 锥底圆心：元组、列表或numpy数组
        r           - 锥底半径：浮点型
        color       - 颜色：浮点型元组、列表或numpy数组
        arc         - 弧度角范围：默认0°~360°
        cell        - 网格精度：默认5°
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        spire = np.array(spire)
        center = np.array(center)
        m_rotate = util.y2v(spire - center)
        
        arc_0, arc_1, cell = np.radians(min(arc)), np.radians(max(arc)), np.radians(cell)
        slices = round(abs(arc_0-arc_1)/cell)
        
        theta = np.linspace(arc_0, arc_1, slices)
        xs = r * np.cos(theta)
        zs = -r * np.sin(theta)
        ys = np.zeros_like(theta)
        
        vs = np.stack((xs,ys,zs), axis=1)
        vs = np.dot(vs, m_rotate) + center
        vs = np.vstack((spire, vs))
        
        if color is None:
            color = self.scene.style[1]
        
        self.surface(vs, color=color, method='fan', indices=None, closed=abs(arc[0]-arc[1])==360, **kwds)

    def cube(self, center, side, vec=(0,1,0), color=None, **kwds):
        """六面体
        
        center      - 中心坐标，元组、列表或numpy数组
        side        - 棱长：数值或长度为3的元组、列表、numpy数组
        vec         - 六面体上表面法向量
        color       - 颜色：浮点型元组、列表或numpy数组
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        if isinstance(side, (tuple, list, np.ndarray)):
            x, y, z = side[0]/2, side[1]/2, side[2]/2
        else:
            x, y, z = side/2, side/2, side/2
        
        vs_front = np.array(((-x,y,z),(-x,-y,z),(x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)))
        vs_back = np.array(((x,y,-z),(x,-y,-z),(-x,-y,-z),(-x,-y,-z),(-x,y,-z),(x,y,-z)))
        vs_top = np.array(((-x,y,-z),(-x,y,z),(x,y,z),(x,y,z),(x,y,-z),(-x,y,-z)))
        vs_bottom = np.array(((-x,-y,z),(-x,-y,-z),(x,-y,-z),(x,-y,-z),(x,-y,z),(-x,-y,z)))
        vs_left = np.array(((-x,y,-z),(-x,-y,-z),(-x,-y,z),(-x,-y,z),(-x,y,z),(-x,y,-z)))
        vs_right = np.array(((x,y,z),(x,-y,z),(x,-y,-z),(x,-y,-z),(x,y,-z),(x,y,z)))
        
        vs = np.vstack((vs_front, vs_back, vs_top, vs_bottom, vs_left, vs_right))
        m_rotate = util.y2v(vec)
        vs = np.dot(vs, m_rotate) + center
        
        if color is None:
            color = self.scene.style[1]
        
        self.surface(vs, color=color, method='isolate', indices=None, **kwds)

    def isosurface(self, data, level, color=None, x=None, y=None, z=None, **kwds):
        """基于MarchingCube算法的三维等值面
        
        data        - 数据集：三维numpy数组
        level       - 阈值：浮点型
        color       - 颜色：浮点型元组、列表或numpy数组
        x/y/z       - 数据集对应的点的x/y/z轴的动态范围
        kwds        - 关键字参数
            name            - 模型名
            visible         - 是否可见，默认True
            inside          - 模型顶点是否影响模型空间，默认True
            opacity         - 模型不透明属性，默认不透明
            cull            - 面剔除，可选项：'front', 'back', None（默认，表示使用当前设置）
            fill            - 填充，可选项：True, False, None（默认，表示使用当前设置） 
            slide           - 幻灯片函数，默认None
            transform       - 由旋转、平移和缩放组成的模型几何变换序列
            light           - 光照情景模式，默认太阳光照情景模式
        """
        
        vs, ids = util._isosurface(data, level)
        indices = ids.ravel()
        
        xs = vs[:,0] if x is None else (x[1] - x[0]) * vs[:,0] / data.shape[0] + x[0]
        ys = vs[:,1] if y is None else (y[1] - y[0]) * vs[:,1] / data.shape[1] + y[0]
        zs = vs[:,2] if z is None else (z[1] - z[0]) * vs[:,2] / data.shape[2] + z[0]
        vs = np.stack((xs, ys, zs), axis=1)
        
        if color is None:
            color = self.scene.style[1]
        
        self.surface(vs, color=color, method='isolate', indices=indices, **kwds)
    
    def colorbar(self, cm, drange, box, mode='V', **kwds):
        """ColorBar 
        
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
            texture = Texture(np.uint8(np.tile(255*colors, (2,1)).reshape(2,256,-1)))
        else:
            texture = Texture(np.uint8(np.tile(255*colors[::-1], 2).reshape(256,2,-1)))
        
        if mode == 'V':
            u = box[2,0] - box[0,0]
            h = box[0,1] - box[1,1]
            if not subject is None:
                vs_subject = np.array([
                    [box[0,0], box[0,1]+1.05*u],
                    [box[0,0], box[0,1]+0.4*u],
                    [box[2,0], box[2,1]+1.05*u],
                    [box[2,0], box[2,1]+0.4*u]
                ])
                self.text3d(subject, vs_subject, align='left', valign='fill', size=text_size, inside=False)
            
            tk = h/(dmax-dmin)
            text_arr, box_arr, dashes = list(), list(), list()
            for t in ticks:
                y = (t-dmin)*tk + box[1,1]
                dashes.extend([[box[2,0], y], [box[2,0]+0.4*u, y]])
                vs_tick = np.array([
                    [box[2,0]+0.6*u, y+0.25*u],
                    [box[2,0]+0.6*u, y-0.25*u],
                    [box[2,0]+3*u, y-0.25*u],
                    [box[2,0]+3*u, y+0.25*u]
                ])
                
                text_arr.append(tick_format(t))
                box_arr.append(vs_tick)
            
            box_arr = np.stack(box_arr, axis=0)
            self._text3d_array(text_arr, box_arr, align='center', valign='fill', size=text_size, inside=False)
            self.line(np.array(dashes, dtype=np.float32), method='isolate', width=0.5, inside=False)
        else:
            u = box[0,1] - box[1,1]
            w = box[2,0] - box[0,0]
            if not subject is None:
                vs_subject = np.array([
                    [box[0,0], box[0,1]+1.2*u],
                    [box[0,0], box[0,1]+0.3*u],
                    [box[2,0], box[2,1]+1.2*u],
                    [box[2,0], box[2,1]+0.3*u]
                ])
                self.text3d(subject, vs_subject, align='center', valign='fill', size=text_size, inside=False)
            
            tk = w/(dmax-dmin)
            text_arr, box_arr, dashes = list(), list(), list()
            for t in ticks:
                x = (t-dmin)*tk + box[1,0]
                dashes.extend([[x, box[1,1]], [x, box[1,1]-0.4*u]])
                vs_tick = np.array([
                    [x-u, box[1,1]-0.65*u],
                    [x-u, box[1,1]-1.35*u],
                    [x+u, box[1,1]-1.35*u],
                    [x+u, box[1,1]-0.65*u]
                ])
                
                text_arr.append(tick_format(t))
                box_arr.append(vs_tick)
            
            box_arr = np.stack(box_arr, axis=0)
            self._text3d_array(text_arr, box_arr, align='center', valign='fill', size=text_size, inside=False)
            self.line(np.array(dashes, dtype=np.float32), method='isolate', width=0.5, inside=False)
        
        self.surface(box, texture=texture, texcoord=texcoord, method='strip', inside=False, light=BaseLight())
        
    def grid(self, xlabel='X', ylabel='Y', zlabel='Z', **kwds):
        """绘制网格和刻度
        
        xlabel      - x轴名称，默认'X'
        ylabel      - y轴名称，默认'Y'
        zlabel      - z轴名称，默认'Z'
        kwds        - 关键字参数
            xf              - x轴刻度标注格式化函数，默认str
            yf              - y轴刻度标注格式化函数，默认str
            zf              - z轴刻度标注格式化函数，默认str
            xd              - x轴刻度密度调整，整型，值域范围[-2,10], 默认0
            yd              - y轴刻度密度调整，整型，值域范围[-2,10], 默认0
            zd              - z轴刻度密度调整，整型，值域范围[-2,10], 默认0
            xc              - x轴标注文本颜色，默认(1.0,0.3,0)
            yc              - y轴标注文本颜色，默认(0,1.0,0.3)
            zc              - z轴标注文本颜色，默认(0,0.5,1.0)
            lc              - 网格线颜色，默认使用前景色
            tick_size       - 刻度标注字号，默认32
            label_size      - 坐标轴标注字号，默认40
        """
        
        for key in kwds:
            if key not in ['xr','yr','zr','xf','yf','zf','xd','yd','zd','lc','extend','tick_size','label_size']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        xf = kwds.get('xf', str)
        yf = kwds.get('yf', str)
        zf = kwds.get('zf', str)
        xd = kwds.get('xd', 0)
        yd = kwds.get('yd', 0)
        zd = kwds.get('zd', 0)
        xc = kwds.get('xc', (1.0,0.3,0))
        yc = kwds.get('yc', (0,1.0,0.3))
        zc = kwds.get('zc', (0,0.5,1.0))
        lc = kwds.get('lc', self.scene.style[1])
        tick_size = kwds.get('tick_size', 32)
        label_size = kwds.get('label_size', 40)
        
        xd, yd, zd = max(-2, xd), max(-2, yd), max(-2, zd)
        name = uuid.uuid1().hex
        
        if self.r_x[0] >= self.r_x[-1] or self.r_y[0] >= self.r_y[-1] or self.r_z[0] >= self.r_z[-1]:
            return # '模型空间不存在，返回
        
        dx = (self.r_x[1] - self.r_x[0]) * 0.1
        xx = self._get_tick_label(self.r_x[0]-dx, self.r_x[1]+dx, s_min=4+xd, s_max=6+xd)
        
        dy = (self.r_y[1] - self.r_y[0]) * 0.1
        yy = self._get_tick_label(self.r_y[0]-dy, self.r_y[1]+dy, s_min=4+yd, s_max=6+yd)
        
        dz = (self.r_z[1] - self.r_z[0]) * 0.1
        zz = self._get_tick_label(self.r_z[0]-dz, self.r_z[1]+dz, s_min=4+zd, s_max=6+zd)
        
        u = max((xx[2]-xx[1])/2, (yy[2]-yy[1])/2) # 计算文字布局的长度单位
        h, g = 0.4 * u, 0.2 * u # 文字宽度和间隙
        
        # 六个网格拼合成一个模型
        # -----------------------------
        xs, ys = np.meshgrid(xx, yy[::-1])
        zs = np.ones(xs.shape) * zz[-1]
        xs_front = self._mesh2quad(xs, ys, zs)
        
        xs, ys = np.meshgrid(xx[::-1], yy[::-1])
        zs = np.ones(xs.shape) * zz[0]
        xs_back = self._mesh2quad(xs, ys, zs)
        
        xs, zs = np.meshgrid(xx, zz)
        ys = np.ones(xs.shape) * yy[-1]
        xs_top = self._mesh2quad(xs, ys, zs)
        
        xs, zs = np.meshgrid(xx, zz[::-1])
        ys = np.ones(xs.shape) * yy[0]
        xs_bottom = self._mesh2quad(xs, ys, zs)
        
        zs, ys = np.meshgrid(zz, yy[::-1])
        xs = np.ones(zs.shape) * xx[0]
        xs_left = self._mesh2quad(xs, ys, zs)
        
        zs, ys = np.meshgrid(zz[::-1], yy[::-1])
        xs = np.ones(zs.shape) * xx[-1]
        xs_right = self._mesh2quad(xs, ys, zs)
        
        vs = np.vstack((xs_front, xs_back, xs_top, xs_bottom, xs_left, xs_right))
        self.quad(vs, color=lc, fill=False, cull='front', method='isolate', light=BaseLight(), name=name)
        
        # 所有刻度文字拼合成一个模型
        # -----------------------------
        im_arr, vs_arr, loc_view, texcoord = list(), list(), list(), list()
        th = min(self.vision[1],self.vision[-1]) * 0.2 * tick_size/32
        tw, rows_max, cols_max = 0, 0, 0
        
        for y in yy[1:-1]:
            im = util.text2image(yf(y), tick_size, yc)
            rows_max = max(im.shape[0], rows_max)
            cols_max = max(im.shape[1], cols_max)
            tw = max(th * im.shape[1]/im.shape[0] * self.size[1]/self.size[0], tw)
            
            im_arr.append((im, 'right'))
            i = len(im_arr) - 1
            
            texcoord.append([[0,0,i], [0,1,i], [1,1,i], [1,0,i]])
            vs_arr.extend([[xx[0]-g,y,zz[-1]], [xx[-1]+g,y,zz[-1]], [xx[-1]+g,y,zz[0]], [xx[0]-g,y,zz[0]]])
            loc_view.extend([[7,1], [7,2], [7,3], [7,4]])
        
        for x in xx[1:-1]:
            im = util.text2image(xf(x), tick_size, xc)
            rows_max = max(im.shape[0], rows_max)
            cols_max = max(im.shape[1], cols_max)
            tw = max(th * im.shape[1]/im.shape[0] * self.size[1]/self.size[0], tw)
            
            im_arr.append((im, 'center'))
            i = len(im_arr) - 1
            
            texcoord.append([[0,0,i], [0,1,i], [1,1,i], [1,0,i]])
            vs_arr.extend([[x,yy[0]-h,zz[-1]], [x,yy[-1]+h,zz[-1]], [x,yy[0]-h,zz[0]], [x,yy[-1]+h,zz[0]]])
            loc_view.extend([[4,5], [4,6], [4,7], [4,8]])
        
        for z in zz[1:-1]:
            im = util.text2image(zf(z), tick_size, zc)
            rows_max = max(im.shape[0], rows_max)
            cols_max = max(im.shape[1], cols_max)
            tw = max(th * im.shape[1]/im.shape[0] * self.size[1]/self.size[0], tw)
            
            im_arr.append((im, 'center'))
            i = len(im_arr) - 1
            
            texcoord.append([[0,0,i], [0,1,i], [1,1,i], [1,0,i]])
            vs_arr.extend([[xx[0],yy[0]-h,z], [xx[0],yy[-1]+h,z], [xx[-1],yy[0]-h,z], [xx[-1],yy[-1]+h,z]])
            loc_view.extend([[4,9], [4,10], [4,11], [4,12]])
        
        texcoord = np.repeat(np.array(texcoord), 4, axis=0).reshape(-1,3)
        vs_arr = np.repeat(np.array(vs_arr), 4, axis=0)
        loc_view = np.repeat(np.array(loc_view), 4, axis=0)
        
        self._text2d_array(im_arr, vs_arr, loc_view, texcoord, tw, th, rows_max, cols_max, name=name) #刻度文字模型
        
        # 三个轴名称拼合成一个模型
        # -----------------------------
        im_arr, vs_arr, loc_view, texcoord = list(), list(), list(), list()
        th = min(self.vision[1],self.vision[-1]) * 0.2 * label_size/32
        tw, rows_max, cols_max = 0, 0, 0
        
        if ylabel:
            im = util.text2image(ylabel, label_size, yc)
            rows_max = max(im.shape[0], rows_max)
            cols_max = max(im.shape[1], cols_max)
            tw = max(th * im.shape[1]/im.shape[0] * self.size[1]/self.size[0], tw)
            
            im_arr.append((im, 'right'))
            i = len(im_arr) - 1
            
            texcoord.append([[0,0,i], [0,1,i], [1,1,i], [1,0,i]])
            vs_arr.extend([[xx[0]-g,yy[-1],zz[-1]], [xx[-1]+g,yy[-1],zz[-1]], [xx[-1]+g,yy[-1],zz[0]], [xx[0]-g,yy[-1],zz[0]]])
            loc_view.extend([[7,1], [7,2], [7,3], [7,4]])
        
        if xlabel:
            im = util.text2image(xlabel, label_size, xc)
            rows_max = max(im.shape[0], rows_max)
            cols_max = max(im.shape[1], cols_max)
            tw = max(th * im.shape[1]/im.shape[0] * self.size[1]/self.size[0], tw)
            
            im_arr.append((im, 'center'))
            i = len(im_arr) - 1
            x = (xx[0]+xx[-1])/2
            
            texcoord.append([[0,0,i], [0,1,i], [1,1,i], [1,0,i]])
            vs_arr.extend([[x,yy[0]-2.5*h,zz[-1]], [x,yy[-1]+2.5*h,zz[-1]], [x,yy[0]-2.5*h,zz[0]], [x,yy[-1]+2.5*h,zz[0]]])
            loc_view.extend([[4,5], [4,6], [4,7], [4,8]])
        
        if zlabel:
            im = util.text2image(zlabel, label_size, zc)
            rows_max = max(im.shape[0], rows_max)
            cols_max = max(im.shape[1], cols_max)
            tw = max(th * im.shape[1]/im.shape[0] * self.size[1]/self.size[0], tw)
            
            im_arr.append((im, 'center'))
            i = len(im_arr) - 1
            z = (zz[0]+zz[-1])/2
            
            texcoord.append([[0,0,i], [0,1,i], [1,1,i], [1,0,i]])
            vs_arr.extend([[xx[0],yy[0]-2.5*h,z], [xx[0],yy[-1]+2.5*h,z], [xx[-1],yy[0]-2.5*h,z], [xx[-1],yy[-1]+2.5*h,z]])
            loc_view.extend([[4,9], [4,10], [4,11], [4,12]])
        
        if vs_arr:
            texcoord = np.repeat(np.array(texcoord), 4, axis=0).reshape(-1,3)
            vs_arr = np.repeat(np.array(vs_arr), 4, axis=0)
            loc_view = np.repeat(np.array(loc_view), 4, axis=0)
            
            self._text2d_array(im_arr, vs_arr, loc_view, texcoord, tw, th, rows_max, cols_max, name=name) # 轴名称模型
    
    def _mesh2quad(self, xs, ys, zs):
        """mesh转quad"""
        
        vs = np.dstack((xs, ys, zs))
        rows, cols = vs.shape[:2]
        
        idx = np.arange(rows*cols).reshape(rows, cols)
        idx_a, idx_b, idx_c, idx_d = idx[:-1,:-1], idx[1:,:-1], idx[1:,1:], idx[:-1, 1:]
        idx = np.int32(np.dstack((idx_a, idx_b, idx_c, idx_d)).ravel())
        
        return vs.reshape(-1,3)[idx]
    
    def _text2d_array(self, im_arr, vs_arr, loc_view, texcoord, tw, th, rows_max, cols_max, **kwds):
        """2d文字数组
        
        im_arr      - 文本图象数组
        vs_arr      - 文本位置数组
        loc_view    - 文本基点和可见性数组
        texcoord    - 纹理数组
        tw          - 文本宽度
        th          - 文本高度
        rows_max    - 文本图象最大行数
        cols_max    - 文本图像最大列数
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
        
        text_array = list()
        for im, align in im_arr:
            if im.shape[0] < rows_max:
                n = rows_max - im.shape[0]
                nu = n // 2
                nd = n - nu
                
                im = np.vstack((im, np.zeros((nd, *im.shape[1:]), dtype=np.uint8)))
                if nu > 0:
                    im = np.vstack((np.zeros((nu, *im.shape[1:]), dtype=np.uint8), im))
            
            if im.shape[1] < cols_max:   
                n = cols_max - im.shape[1]
                if align == 'right':
                    im = np.hstack((im, np.zeros((im.shape[0], n, im.shape[-1]), dtype=np.uint8)))
                elif align == 'center':
                    nl = n // 2
                    nr = n - nl
                    
                    im = np.hstack((im, np.zeros((im.shape[0], nr, im.shape[-1]), dtype=np.uint8)))
                    if nl > 0:
                        im = np.hstack((np.zeros((im.shape[0], nl, im.shape[-1]), dtype=np.uint8), im))
            
            text_array.append(im)
        
        light = BaseLightText2dArray(ambient)
        texture = Texture(np.stack(text_array), ttype=GL_TEXTURE_2D_ARRAY, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        self.add_model(light.get_model(GL_QUADS, vs_arr, loc_view, texture, texcoord, tw, th, 
            visible     = visible, 
            inside      = inside, 
            opacity     = False, 
            slide       = slide
        ), name)
    
    def _text3d_array(self, text_arr, box_arr, color=None, align='center', valign='fill', **kwds):
        """3d文字数组
        
        text_arr    - 文本字符串列表
        box_arr     - 文本显式区域数组
        color       - 文本颜色：浮点型元组、列表或numpy数组，值域范围[0,1]，None表示使用场景默认的前景颜色
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
            ambient         - 环境光，默认(1.0,1.0,1.0)
            size            - 字号：整型，默认64。此参数影响文本显示质量，不改变文本大小
        """
        
        for key in kwds:
            if key not in ['name', 'visible', 'inside', 'ambient', 'size']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        name = kwds.get('name')
        visible = kwds.get('visible', True)
        inside = kwds.get('inside', True)
        ambient = kwds.get('ambient', (1.0,1.0,1.0))
        size = kwds.get('size', 64)
        
        if color is None:
            color = self.scene.style[1]
        elif isinstance(color, (tuple, list, np.ndarray)):
            color = np.float32(color)
            if color.shape != (3,) and color.shape != (4,):
                raise KeyError('期望color参数为浮点类型RGB或RGBA颜色')
        else:
            raise KeyError('期望color参数为浮点类型元组、列表或numpy数组')
        
        im_arr, texcoord = list(), list()
        rows_max, cols_max = 0, 0
        for i in range(len(text_arr)):
            im = util.text2image(text_arr[i], size, color)
            rows_max = max(im.shape[0], rows_max)
            cols_max = max(im.shape[1], cols_max)
            im_arr.append(im)
            texcoord.append(np.array([[0,0,i],[0,1,i],[1,1,i],[1,0,i]], dtype=np.float32))
        
        nim_arr = list()
        for im in im_arr:
            if im.shape[0] < rows_max:
                n = rows_max - im.shape[0]
                nu = n // 2
                nd = n - nu
                
                im = np.vstack((im, np.zeros((nd, *im.shape[1:]), dtype=np.uint8)))
                if nu > 0:
                    im = np.vstack((np.zeros((nu, *im.shape[1:]), dtype=np.uint8), im))
            
            if im.shape[1] < cols_max:   
                n = cols_max - im.shape[1]
                nl = n // 2
                nr = n - nl
                
                im = np.hstack((im, np.zeros((im.shape[0], nr, im.shape[-1]), dtype=np.uint8)))
                if nl > 0:
                    im = np.hstack((np.zeros((im.shape[0], nl, im.shape[-1]), dtype=np.uint8), im))
            
            nim_arr.append(im)
        
        for i in range(box_arr.shape[0]):
            box_width = np.linalg.norm(box_arr[i][2] - box_arr[i][0])
            box_height = np.linalg.norm(box_arr[i][0] - box_arr[i][1])

            k_box, k_text = box_width/box_height, nim_arr[i].shape[1]/nim_arr[i].shape[0]
            
            if k_text > k_box:
                if valign != 'fill':
                    align = 'fill'
            else:
                if align != 'fill':
                    valign = 'fill'
            
            if align == 'fill':
                if valign == 'top':
                    offset = (box_arr[i][1] - box_arr[i][0])*k_box/k_text
                    box_arr[i][1] = box_arr[i][0] + offset
                    box_arr[i][2] = box_arr[i][3] + offset
                elif valign == 'middle':
                    offset = (box_arr[i][1]-box_arr[i][0])*(1-k_box/k_text)/2
                    box_arr[i][0] += offset
                    box_arr[i][3] += offset
                    box_arr[i][1] -= offset
                    box_arr[i][2] -= offset
                elif valign == 'bottom':
                    offset = (box_arr[i][0]-box_arr[i][1])*k_box/k_text
                    box_arr[i][0] = box_arr[i][1] + offset
                    box_arr[i][3] = box_arr[i][2] + offset
            elif align == 'left':
                offset = (box_arr[i][2]-box_arr[i][1])*k_text/k_box
                box_arr[i][2] = box_arr[i][1] + offset
                box_arr[i][3] = box_arr[i][0] + offset
            elif align == 'right':
                offset = (box_arr[i][0] - box_arr[i][3])*k_text/k_box
                box_arr[i][0] = box_arr[i][3] + offset
                box_arr[i][1] = box_arr[i][2] + offset
            elif align == 'center':
                offset = (box_arr[i][3] - box_arr[i][0])*(1-k_text/k_box)/2
                box_arr[i][0] += offset
                box_arr[i][1] += offset
                box_arr[i][3] -= offset
                box_arr[i][2] -= offset
        
        texture = Texture(np.stack(nim_arr), ttype=GL_TEXTURE_2D_ARRAY, s_tile=GL_CLAMP_TO_EDGE, t_tile=GL_CLAMP_TO_EDGE)
        texcoord = np.vstack(texcoord)
        
        light = BaseLight(ambient)
        self.add_model(light.get_model(GL_QUADS, box_arr,
            texture     = texture,
            texcoord    = texcoord,
            visible     = visible, 
            opacity     = False, 
            inside      = inside
        ), name)
    