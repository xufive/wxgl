#!/usr/bin/env python3

import time
import numpy as np
from PIL import Image

from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGL.GL import shaders

from . import util

class BaseScene:
    """场景基类"""

    _DIST = 6.0
    _NEAR = 3.0
    _FAR = 1000.0

    def __init__(self, scheme, **kwds):
        """构造函数"""
        
        self.scheme = scheme                                            # 展示方案
        self.viewport = [None, None, None]                              # 主视区、标题区、调色板区视口
        self.mns = [[[],[]], [[],[]], [[],[]]]                          # 主视区、标题区、调色板区不透明/透明模型名列表

        self.csize = kwds.get('size', (960, 640))                       # 画布分辨率
        self.bg = util.format_color(kwds.get('bg', [0.0, 0.0, 0.0]))    # 背景色
        self.haxis = kwds.get('haxis', 'y').lower()                     # 高度轴
        self.fovy = kwds.get('fovy', 50.0)                              # 相机水平视野角度
        self.azim = kwds.get('azim', 0.0)                               # 方位角
        self.elev = kwds.get('elev', 0.0)                               # 高度角
        self.azim_range = kwds.get('azim_range', (-180.0, 180.0))       # 方位角变化范围
        self.elev_range = kwds.get('elev_range', (-180.0, 180.0))       # 高度角变化范围
        self.smooth = kwds.get('smooth', True)                          # 直线和点的反走样开关

        self.oecs = [0.0, 0.0, 0.0]                                     # 视点坐标系ECS原点
        self.dist = self._DIST                                          # 相机ECS原点的距离
        self.near = self._NEAR                                          # 相机与视椎体前端面的距离
        self.far = self._FAR                                            # 相机与视椎体后端面的距离
        self.aspect = self.csize[0]/self.csize[1]                       # 画布宽高比
        self.cam = None                                                 # 相机位置
        self.up = None                                                  # 指向相机上方的单位向量
        self.origin = None                                              # 初始位置和姿态
        self.mmat = np.eye(4, dtype=np.float32)                         # 模型矩阵
        self.vmat = np.eye(4, dtype=np.float32)                         # 视点矩阵
        self.pmat = np.eye(4, dtype=np.float32)                         # 投影矩阵

        self.gl_init_done = False                                       # GL初始化标志
        self.left_down = False                                          # 左键按下
        self.mouse_pos = None                                           # 鼠标位置
        self.scale = 1.0                                                # 眼睛位置自适应调整系数

        self.im_pil = None                                              # 缓冲区图像数据
        self.increment = True                                           # 计时器自动增量
        self.start= 1000 * time.time()                                  # 开始渲染时的时间戳
        self.duration = 0                                               # 累计渲染时长，单位毫秒
        self.tbase = 0                                                  # 累计渲染时长基数，单位毫秒
        self.playing = False                                            # 动画播放中

        self._update_cam_and_up()                                       # 更新眼睛位置和指向观察者上方的单位向量
        self._update_view_matrix()                                      # 更新视点矩阵
        self._update_proj_matrix()                                      # 更新投影矩阵

    def _update_cam_and_up(self, oecs=None, dist=None, azim=None, elev=None):
        """根据当前ECS原点位置、距离、方位角、仰角等参数，重新计算眼睛位置和up向量"""

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
 
        up = 1.0 if -90 <= self.elev <= 90 else -1.0
        azim, elev  = np.radians(self.azim), np.radians(self.elev)
        d = self.dist * np.cos(elev)

        if self.haxis == 'z':
            azim -= 0.5 * np.pi
            self.cam = [d*np.cos(azim)+self.oecs[0], d*np.sin(azim)+self.oecs[1], self.dist*np.sin(elev)+self.oecs[2]]
            self.up = [0.0, 0.0, up]
        else:
            self.cam = [d*np.sin(azim)+self.oecs[0], self.dist*np.sin(elev)+self.oecs[1], d*np.cos(azim)+self.oecs[2]]
            self.up = [0.0, up, 0.0]

    def _update_proj_matrix(self):
        """更新投影矩阵"""
 
        self.pmat[:] = util.proj_matrix(self.fovy, self.aspect, self.near, self.far)

    def _update_view_matrix(self):
        """更新视点矩阵"""
 
        self.vmat[:] = util.view_matrix(self.cam, self.up, self.oecs)

    def _get_buffer(self, mode='RGBA', crop=False, buffer='front', qt=False):
        """以PIL对象的格式返回场景缓冲区数据
 
        mode        - 'RGB'或'RGBA'
        crop        - 是否将宽高裁切为16的倍数
        buffer      - 'front'（前缓冲区）或'back'（后缓冲区）
        qt          - 使用Qt作为后端
        """

        gl_mode = GL_RGBA if mode=='RGBA' else GL_RGB
        glReadBuffer(GL_FRONT if buffer=='front' else GL_BACK)
        data = glReadPixels(0, 0, self.csize[0], self.csize[1], gl_mode, GL_UNSIGNED_BYTE, outputType=None)
        data = data.reshape(data.shape[1], data.shape[0], -1)
        im = Image.fromarray(data[31:, 49:] if qt else data, mode=mode)
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
 
        if crop:
            w, h = im.size
            nw, nh = 16*(w//16), 16*(h//16)
            x0, y0 = (w-nw)//2, (h-nh)//2
            x1, y1 = x0+nw, y0+nh
            im = im.crop((x0, y0, x1, y1))
 
        return im

    def _resize(self):
        """改变窗口"""
 
        if not self.scheme.models[1] and not self.scheme.models[2]:
            self.viewport[0] = (0, 0, *self.csize)
        elif self.scheme.models[1] and not self.scheme.models[2]:
            self.viewport[1] = (0, int(self.csize[1]*0.85), self.csize[0], int(self.csize[1]*0.15))
            self.viewport[0] = (0, 0, self.csize[0], int(self.csize[1]*0.85))
        elif not self.scheme.models[1] and self.scheme.models[2]:
            self.viewport[2] = (int(self.csize[0]*0.85), 0, int(self.csize[0]*0.15), self.csize[1])
            self.viewport[0] = (0, 0, int(self.csize[0]*0.85), self.csize[1])
        else:
            self.viewport[1] = (0, int(self.csize[1]*0.85), self.csize[0], int(self.csize[1]*0.15))
            self.viewport[2] = (int(self.csize[0]*0.85), 0, int(self.csize[0]*0.15), int(self.csize[1]*0.85))
            self.viewport[0] = (0, 0, int(self.csize[0]*0.85), int(self.csize[1]*0.85))

        if self.viewport[0][2] == 0:
            self.aspect = 1e-5
        elif self.viewport[0][3] == 0:
            self.aspect = self.viewport[0][2]
        else:
            self.aspect = self.viewport[0][2]/self.viewport[0][3]

        self._update_proj_matrix()

    def _paint(self):
        """绘制函数"""
 
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) # 清除屏幕及深度缓存

        if self.scheme.alive and self.playing:
            if self.increment:
                self.duration = self.tbase + 1000*time.time() - self.start

            if self.scheme.cruise_func:
                v = self.scheme.cruise_func(self.duration)
                self._update_cam_and_up(azim=v.get('azim'), elev=v.get('elev'), dist=v.get('dist'))
                self._update_view_matrix()

        for i in range(3):
            if self.scheme.models[i]:
                glViewport(*self.viewport[i])
                for mid, depth in self.mns[i][0]:
                    self._render(self.scheme.models[i][mid])

                glDepthMask(False) # 对于半透明模型，禁用深度缓冲（锁定）
                if (self.up[1]+self.up[2]) > 0 and -90 <= self.azim < 90 or (self.up[1]+self.up[2]) < 0 and (self.azim < -90 or self.azim >= 90):
                    for mid, depth in self.mns[i][1]:
                        self._render(self.scheme.models[i][mid])
                else:
                    for mid, depth in self.mns[i][1][::-1]:
                        self._render(self.scheme.models[i][mid])
                glDepthMask(True) # 释放深度缓冲区

    def _initialize_gl(self):
        """GL初始化函数"""
 
        glClearColor(*self.bg, 1.0)                                         # 设置画布背景色
        glEnable(GL_DEPTH_TEST)                                             # 开启深度测试，实现遮挡关系        
        glDepthFunc(GL_LEQUAL)                                              # 设置深度测试函数
        glShadeModel(GL_SMOOTH)                                             # GL_SMOOTH(光滑着色)/GL_FLAT(恒定着色)
        glEnable(GL_BLEND)                                                  # 开启混合        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)                   # 设置混合函数
        glEnable(GL_ALPHA_TEST)                                             # 启用Alpha测试 
        glAlphaFunc(GL_GREATER, 0.05)                                       # 设置Alpha测试条件为大于0.05则通过
        
        if self.smooth:
            glEnable(GL_POINT_SMOOTH)                                       # 开启点反走样
            glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)                         # 最高质量点反走样
            glEnable(GL_LINE_SMOOTH)                                        # 开启直线反走样
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)                          # 最高质量直线反走样

    def _timer(self):
        """定时函数"""

        if self.scheme.alive and self.playing:
            if self.increment:
                self.duration = self.tbase + 1000*time.time() - self.start

            if self.scheme.cruise_func:
                v = self.scheme.cruise_func(self.duration)
                self._update_cam_and_up(azim=v.get('azim'), elev=v.get('elev'), dist=v.get('dist'))
                self._update_view_matrix()

    def _home(self):
        """恢复初始位置和姿态"""

        self.fovy = self.origin['fovy']
        self._update_cam_and_up(dist=self.origin['dist'], azim=self.origin['azim'], elev=self.origin['elev'])
        self._update_view_matrix()
        self._update_proj_matrix()

        self.tn = 0
        self.start= 1000 * time.time()
        self.duration = 0
        self.tbase = 0

    def _pause(self):
        """动画/暂停"""

        if self.playing:
            self.playing = False
            self.tbase = self.duration
        else:
            self.start = 1000 * time.time()
            self.playing = True

    def _drag(self, dx, dy):
        """鼠标拖拽"""

        azim = self.azim - (180*dx/self.csize[0]) * (self.up[2] if self.haxis == 'z' else self.up[1])
        elev = self.elev + 90*dy/self.csize[1]
        self._update_cam_and_up(azim=azim, elev=elev)
        self._update_view_matrix()

    def _wheel(self, delta):
        """鼠标滚轮"""
        
        if delta > 0: # 滚轮前滚
            self.fovy *= 0.95
            self._update_proj_matrix()
        else: # 滚轮后滚
            self.fovy += (180 - self.fovy) / 180
            self._update_proj_matrix()

    def _assemble(self):
        """模型装配"""

        if self.scheme.expost:
            if 'grid' in self.scheme.expost:
                self.scheme._grid()
            if 'axes' in self.scheme.expost:
                self.scheme._axes()

        for i in range(3):
            for name in self.scheme.models[i]:
                m = self.scheme.models[i][name]

                if i == 1 and name == 'caption_text':
                    m.attribute['a_Position']['data'][:,0] /= self.viewport[i][2]/self.viewport[i][3]

                if i == 2 and name == 'cb_label':
                    m.attribute['a_Position']['data'][:,0] /= self.viewport[i][2]/self.viewport[i][3]
                    #m.attribute['a_Position']['data'][3::4,0] /= self.viewport[i][2]/self.viewport[i][3]

                for src, genre in m.shaders:
                    m.cshaders.append(shaders.compileShader(src, genre))
 
                m.program = shaders.compileProgram(*m.cshaders)
                glUseProgram(m.program)

                if m.indices:
                    m.indices.update({'ibo':vbo.VBO(m.indices['data'], target=GL_ELEMENT_ARRAY_BUFFER)})

                for key in m.attribute:
                    item = m.attribute[key]
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

                if m.opacity:
                    self.mns[i][0].append((name, m.depth[self.haxis]))
                else:
                    self.mns[i][1].append((name, m.depth[self.haxis]))
            
            self.mns[i][1].sort(key=lambda item:item[1])

        dx = self.scheme.r_x[1]-self.scheme.r_x[0]
        dy = self.scheme.r_y[1]-self.scheme.r_y[0]
        dz = self.scheme.r_z[1]-self.scheme.r_z[0]

        if self.haxis == 'z':
            if dx > 0 and dz > 0:
                if self.aspect > dx/dz:
                    self.scale = 2/dz if self.aspect > 1 else 2/(self.aspect*dz)
                else:
                    self.scale = 2*self.aspect/dx if self.aspect > 1 else 2/dx
            elif dx > 0 and dz <= 0:
                self.scale = 2*self.aspect/dx if self.aspect > 1 else 2/dx
            elif dx <= 0 and dz > 0:
                self.scale = 2/dz if self.aspect > 1 else 2/(self.aspect*dz)

            if self.scale * dy > 4:
                self.scale = 4/dy
        else:
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

        self.playing = self.scheme.alive
        self.dist = self._DIST/self.scale
        self.near = self._NEAR/self.scale
        self.far = self._FAR/self.scale
        self.oecs = [sum(self.scheme.r_x)/2, sum(self.scheme.r_y)/2, sum(self.scheme.r_z)/2]
        self.origin = {'fovy':self.fovy, 'azim':self.azim, 'elev':self.elev, 'dist':self.dist}

        self._update_cam_and_up()
        self._update_view_matrix()
        self._update_proj_matrix()
        
        self.start= 1000 * time.time()
        self.duration = 0
        self.tbase = 0
        
        self.gl_init_done = True

    def _render(self, m):
        """绘制单个模型"""

        if not m.visible or m.slide and not m.slide(self.duration):
            return
 
        glUseProgram(m.program)
        tsid = 0
 
        for key in m.attribute:
            loc = m.attribute[key].get('loc')
            bo = m.attribute[key]['bo']
            un = m.attribute[key]['un']
            usize = m.attribute[key]['usize']
            bo.bind()
            glVertexAttribPointer(loc, un, GL_FLOAT, GL_FALSE, un*usize, bo)
            glEnableVertexAttribArray(loc)
            bo.unbind()
 
        for key in m.uniform:
            tag = m.uniform[key]['tag']
            loc = m.uniform[key].get('loc')
 
            if tag == 'pmat' or tag == 'vmat':
                if 'v' in m.uniform[key]:
                    glUniformMatrix4fv(loc, 1, GL_FALSE, m.uniform[key]['v'], None)
                else:
                    glUniformMatrix4fv(loc, 1, GL_FALSE, m.uniform[key]['f'](self.duration), None)
            elif tag == 'mmat':
                if 'v' in m.uniform[key]:
                    glUniformMatrix4fv(loc, 1, GL_FALSE, m.uniform[key]['v'], None)
                else:
                    args = m.uniform[key]['f'](self.duration)
                    mmat = util.model_matrix(*args)
                    glUniformMatrix4fv(loc, 1, GL_FALSE, mmat, None)
            elif tag == 'texture':
                eval('glActiveTexture(GL_TEXTURE%d)'%tsid)
                glBindTexture(m.uniform[key]['data'].ttype, m.uniform[key]['tid'])
                glUniform1i(loc, tsid)
                tsid += 1
            elif tag == 'picked':
                glUniform1i(loc, m.picked)
            elif tag == 'campos':
                glUniform3f(loc, *self.cam)
            elif tag == 'ae':
                glUniform2f(loc, self.azim, self.elev)
            elif tag == 'tsize':
                k = 0.3/(32*self.scale)
                tw, th = m.uniform[key].get('v')
                glUniform2f(loc, tw*k/self.aspect, th*k)
            else:
                value = m.uniform[key].get('v')
                if value is None:
                    value = m.uniform[key].get('f')(self.duration)
                
                dtype = m.uniform[key]['dtype']
                ndim = m.uniform[key]['ndim']
                if ndim is None:
                    try:
                        eval('glUniform%s(loc, value)'%dtype)
                    except:
                        print('渲染函数出现异常，请通知xufive@gmail.com，如可能的话，请提供shader源码。')
                else:
                    eval('glUniform%s(loc, ndim, value)'%dtype)

        for glcmd, args in m.before:
            glcmd(*args)
 
        if m.indices:
            m.indices['ibo'].bind()
            glDrawElements(m.gltype, m.indices['n'], GL_UNSIGNED_INT, None)
            m.indices['ibo'].unbind()
        else:
            glDrawArrays(m.gltype, 0, m.vshape[0])
 
        for glcmd, args in m.after:
            glcmd(*args)
 
        glUseProgram(0)

    def clear_buffer(self):
        """删除纹理、顶点缓冲区等显存对象"""

        for i in range(3):
            for name in self.scheme.models[i]:
                m = self.scheme.models[i][name]
                for item in m.cshaders:
                    glDeleteShader(item)
                
                if m.program:
                    glDeleteProgram(m.program)
                
                if m.indices and 'ibo' in m.indices:
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

    def set_visible(self, name, visible):
        """设置部件或模型的可见性"""

        if name in self.scheme.widget:
            for mid in self.scheme.widget[name]:
                self.scheme.models[0][mid].visible = visible

