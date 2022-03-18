# -*- coding: utf-8 -*-
#
# MIT License
# 
# Copyright (c) 2021 Tianyuan Langzi
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
WxGL: 基于pyopengl的三维数据可视化库

WxGL以wx为显示后端，提供matplotlib风格的交互绘图模式
同时，也可以和wxpython无缝结合，在wx的窗体上绘制三维模型
"""


import os, time
from pynput import keyboard
import wx
from wx import glcanvas
import numpy as np
from PIL import Image
import imageio
import queue
import threading
from OpenGL.GL import *
from OpenGL.GLU import *

from . import region
from . import util


class Scene(glcanvas.GLCanvas):
    """GL场景类"""
    
    def __init__(self, parent, **kwds):
        """构造函数
        
        parent      - 父级窗口对象
        kwds        - 关键字参数
            proj        - 投影模式，'ortho' - 正射投影，'frustum' - 透视投影（默认）
            oecs        - 视点坐标系ECS原点，默认与目标坐标系OCS原点重合
            dist        - 相机与ECS原点的距离，默认5个长度单位
            azim        - 方位角，默认0°
            elev        - 高度角，默认0°
            near        - 视锥体前面距离相机的距离，默认3.0个长度单位
            far         - 视锥体后面距离相机的距离，默认1000个长度单位
            zoom        - 视口缩放因子，默认1.0
            smooth      - 直线、多边形和点的反走样开关
            azim_range  - 方位角限位器，默认-180°~180°
            elev_range  - 仰角限位器，默认-180°~180°
            style       - 场景风格，默认太空蓝
                'white'     - 珍珠白
                'black'     - 石墨黑
                'gray'      - 国际灰
                'blue'      - 太空蓝
                'royal'     - 宝石蓝
        """
        
        for key in kwds:
            if key not in ['proj', 'oecs', 'dist', 'azim', 'elev', 'near', 'far', 'zoom', 'smooth', 'azim_range', 'elev_range', 'style']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        self.parent = parent
        glcanvas.GLCanvas.__init__(self, self.parent, -1, style=glcanvas.WX_GL_RGBA|glcanvas.WX_GL_DOUBLEBUFFER|glcanvas.WX_GL_DEPTH_SIZE)
        
        self.proj = kwds.get('proj', 'frustum')                             # 投影模式
        self.oecs = kwds.get('oecs', [0.0, 0.0, 0.0])                       # 视点坐标系ECS原点
        self.dist = kwds.get('dist', 5.0)                                   # 相机与ECS原点的距离
        self.near = kwds.get('near', 3.0)                                   # 视锥体前面距离相机的距离
        self.far = kwds.get('far', 1000.0)                                  # 视锥体后面距离相机的距离
        self.zoom = kwds.get('zoom', 1.0)                                   # 视口缩放因子
        self.smooth = kwds.get('smooth', True)                              # 反走样开关
        self.azim_range = kwds.get('azim_range', (-180, 180))               # 方位角限位器
        self.elev_range = kwds.get('elev_range', (-180, 180))               # 仰角限位器
        self.style = self._set_style(kwds.get('style', 'blue'))             # 设置风格（背景和文本颜色）
        azim = kwds.get('azim', 0.0)                                        # 初始方位角
        elev = kwds.get('elev', 0.0)                                        # 初始高度角
        
        self.azim = 0                                                       # 方位角
        self.elev = 0                                                       # 高度角
        self.cam = [0.0, 0.0, 5.0]                                          # 相机位置
        self.up = [0.0, 1.0, 0.0]                                           # 指向相机上方的单位向量
        self.vmat = util.view_matrix(self.cam, self.up, self.oecs)          # 视点矩阵
        self.status = dict()                                                # 存储相机姿态、视锥体、缩放比例等设置参数的字典
        
        self._update_pos_and_up(azim=azim, elev=elev)                       # 更新相机位置和up向量
        self._save_status()                                                 # 保存当前的相机状态
        
        self.csize = self.GetClientSize()                                   # OpenGL窗口的大小
        self.context = glcanvas.GLContext(self)                             # OpenGL上下文
        self.regions = list()                                               # 视区列表
        self.mpos = wx._core.Point()                                        # 鼠标位置
        self.leftdown = False                                               # 鼠标左键按下
        self.ctr = False                                                    # Ctr键按下
        
        self.tn = 0                                                         # 计数器
        self.tstamp = None                                                  # 开始渲染时的时间戳
        self.tbase = 0                                                      # 开始渲染时的累计时长
        self.duration = 0;                                                  # 累计渲染时长，单位毫妙
        self.cam_cruise = None                                              # 相机巡航函数
        self.islive = False                                                 # 存在动画模型
        self.playing = False                                                # 动画播放中
        self.capturing = False                                              # 截屏中
        self.creating = False                                               # 动画文件生成中
        self.fn = 0                                                         # 录屏总帧数
        self.cn = 0                                                         # 已完成帧数
        self.q = None                                                       # PIL对象数据队列
        
        self.ticks_is_show = False                                          # 显示坐标轴及刻度网格
        self._init_gl()                                                     # 画布初始化
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)                   # 绑定canvas销毁事件
        self.Bind(wx.EVT_SIZE, self.on_resize)                              # 绑定canvas大小改变事件
        
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)                      # 绑定鼠标左键按下事件
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)                          # 绑定鼠标左键弹起事件                   
        self.Bind(wx.EVT_RIGHT_UP, self.on_right_up)                        # 绑定鼠标右键弹起事件                   
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)                      # 绑定鼠标移动事件
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)                   # 绑定鼠标滚轮事件
        
        monitor_k = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        monitor_k.start()
    
    def _set_style(self, style):
        """设置风格，返回背景色和前景色"""
        
        if not style in ('black', 'white', 'gray', 'blue', 'royal'):
            raise ValueError('不支持的风格选项：%s'%style)
        
        if style == 'black':
            return (0.0, 0.0, 0.0, 1.0), (0.9, 0.9, 0.9)
        if style == 'white':
            return (1.0, 1.0, 1.0, 1.0), (0.0, 0.0, 0.0)
        if style == 'gray':
            return (0.9, 0.9, 0.9, 1.0), (0.0, 0.0, 0.3)
        if style == 'blue':
            return (0.0, 0.0, 0.2, 1.0), (0.9, 1.0, 1.0)
        if style == 'royal':
            return (0.133, 0.302, 0.361, 1.0), (1.0, 1.0, 0.9)
    
    def _update_pos_and_up(self, oecs=None, dist=None, azim=None, elev=None):
        """根据当前ECS原点位置、距离、方位角、仰角等参数，重新计算相机位置和up向量"""
        
        if not oecs is None:
            self.oecs = oecs
        
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
    
    def _save_status(self):
        """保存当前的相机状态"""
        
        self.status.update({
            'oecs': self.oecs,
            'dist': self.dist,
            'azim': self.azim,
            'elev': self.elev,
            'near': self.near,
            'far': self.far,
            'zoom': self.zoom
        })
    
    def _init_gl(self):
        """初始化GL"""
        
        self.SetCurrent(self.context)
        
        glClearColor(*self.style[0],)                                       # 设置画布背景色
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
            glEnable(GL_POLYGON_SMOOTH)                                     # 开启多边形反走样
            glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)                       # 最高质量多边形反走样
            glEnable(GL_LINE_SMOOTH)                                        # 开启直线反走样
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)                          # 最高质量直线反走样
    
    def on_destroy(self, evt):
        """canvas销毁事件函数"""
        
        for reg in self.regions:
            reg.clear_buffer()
        
        evt.Skip()
    
    def on_resize(self, evt):
        """窗口改变事件函数"""
        
        self.SetCurrent(self.context)
        self.csize = self.GetClientSize()
        
        for reg in self.regions:
            reg.update_size()
        
        self.render()
        evt.Skip()
        
    def on_left_down(self, evt):
        """响应鼠标左键按下事件"""
        
        self.leftdown = True
        self.mpos = evt.GetPosition()
        
    def on_left_up(self, evt):
        """响应鼠标左键弹起事件"""
        
        self.leftdown = False
        
    def on_right_up(self, evt):
        """响应鼠标右键弹起事件"""
        
        x, y = evt.GetPosition()
        self.render_pick(x, self.csize[1]-y)
        
    def on_mouse_motion(self, evt):
        """响应鼠标移动事件"""
        
        if evt.Dragging() and self.leftdown:
            pos = evt.GetPosition()
            dx, dy = pos - self.mpos
            self.mpos = pos
            
            if self.ctr:
                oecs = [self.oecs[0]-dx/self.csize[0], self.oecs[1]+dy/self.csize[1], self.oecs[2]]
                self._update_pos_and_up(oecs=oecs)
            else:
                azim = self.azim - self.up[1]*(180*dx/self.csize[0])
                elev = self.elev + 90*dy/self.csize[1]
                self._update_pos_and_up(azim=azim, elev=elev)
            
            self.update_ticks()
            self.render()
        
    def on_mouse_wheel(self, evt):
        """响应鼠标滚轮事件"""
        
        if self.ctr:
            if evt.WheelRotation < 0:
                dist = self.dist * 1.01
            else:
                dist = self.dist * 0.99
            
            self._update_pos_and_up(dist=dist)
        else:
            if evt.WheelRotation < 0:
                self.zoom *= 1.05
                if self.zoom > 100:
                    self.zoom = 100
            else:
                self.zoom *= 0.95
                if self.zoom < 0.01:
                    self.zoom = 0.01
            
            for reg in self.regions:
                reg.pmat[:] = reg.get_pmat()
            
        self.render()
    
    def on_press(self, key):
        """键按下"""
        
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctr = True
    
    def on_release(self, key):
        """键弹起"""
        
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctr = False
        elif key == keyboard.Key.esc:
            wx.CallAfter(self.restore_posture)
    
    def render(self):
        """模型渲染器"""
        
        if self.cam_cruise:
            v = self.cam_cruise(self.duration)
            self.set_posture(azim=v.get('azim'), elev=v.get('elev'), dist=v.get('dist'))
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT) # 清除屏幕及深度缓存
        
        for reg in self.regions:
            glViewport(*reg.pos, *reg.size) # 设置视口
            
            for name, idx, zmean in reg.mnames[0]:
                self._render_core(reg.models[name][idx], reg.pmat, reg.vmat, reg.mmat)
            
            glDepthMask(False) # 对于半透明模型，禁用深度缓冲（锁定）
            if self.up[1] > 0 and -90 <= self.azim < 90 or self.up[1] < 0 and (self.azim < -90 or self.azim >= 90):
                for name, idx, zmean in reg.mnames[1]:
                    self._render_core(reg.models[name][idx], reg.pmat, reg.vmat, reg.mmat)
            else:
                for name, idx, zmean in reg.mnames[1][::-1]:
                    self._render_core(reg.models[name][idx], reg.pmat, reg.vmat, reg.mmat)
            glDepthMask(True) # 释放深度缓冲区
        
        self.SwapBuffers() # 切换缓冲区，以显示绘制内容
        
        if self.capturing:
            if self.cn < self.fn:
                im = self.get_scene_buffer(alpha=True, crop=True)
                self.q.put(im)
                self.cn += 1
            else:
                self.stop_record()
    
    def _render_core(self, m, mat_proj, mat_view, mat_model):
        """模型渲染核函数"""
        
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
                if 'o' in m.uniform[key]:
                    glUniformMatrix4fv(loc, 1, GL_FALSE, m.uniform[key]['o'], None)
                else:
                    args = m.uniform[key]['f'](self.duration)
                    mmat = np.dot(mat_model, util.model_matrix(*args))
                    glUniformMatrix4fv(loc, 1, GL_FALSE, mmat, None)
            elif tag == 'texture':
                eval('glActiveTexture(GL_TEXTURE%d)'%tsid)
                glBindTexture(m.uniform[key]['data'].ttype, m.uniform[key]['tid'])
                glUniform1i(loc, tsid)
                tsid += 1
            elif tag == 'picked':
                glUniform1i(loc, m.picked)
            elif tag == 'mvpmat':
                pvmmat = np.dot(np.dot(mat_model, mat_view), mat_proj)
                glUniformMatrix4fv(loc, 1, GL_FALSE, pvmmat, None)
            elif tag == 'campos':
                glUniform3f(loc, *self.cam)
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
    
    def render_pick(self, x, y):
        """拾取渲染器"""
        
        if self.cam_cruise:
            v = self.cam_cruise(self.duration)
            self.set_posture(azim=v.get('azim'), elev=v.get('elev'), dist=v.get('dist'))
        
        for reg in self.regions:
            glViewport(*reg.pos, *reg.size)
            name_hit, depth_hit, idx_hit = None, 1, 0
            
            for i in (0, 1):
                for name, idx, zmean in reg.mnames[i]:
                    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
                    self._render_core(reg.models[name][idx], reg.pmat, reg.vmat, reg.mmat)
                    
                    d = glReadPixels(x, y, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT, outputType=None)[0,0]
                    if d < depth_hit:
                        name_hit, depth_hit, idx_hit = name, d, idx
            
            if name_hit:
                reg.models[name_hit][idx_hit].picked = not reg.models[name_hit][idx_hit].picked
                break
        
        self.render()
    
    def update_ticks(self):
        """刷新坐标轴和刻度网格"""
        
        if not self.ticks_is_show:
            return
        
        for reg in self.regions: 
            if not reg.ticks:
                continue
            
            if -90 <= self.azim < 90 and self.up[1] > 0 or (self.azim <-90 or self.azim >= 90) and self.up[1] < 0:
                reg.show_model(reg.ticks['back'])
                reg.hide_model(reg.ticks['front'])
            else:
                reg.show_model(reg.ticks['front'])
                reg.hide_model(reg.ticks['back'])
            
            if 0 <= self.azim < 180 and self.up[1] > 0 or -180 <= self.azim < 0 and self.up[1] < 0:
                reg.show_model(reg.ticks['left'])
                reg.hide_model(reg.ticks['right'])
            else:
                reg.show_model(reg.ticks['right'])
                reg.hide_model(reg.ticks['left'])
            
            if self.elev < 0:
                reg.show_model(reg.ticks['top'])
                reg.hide_model(reg.ticks['bottom'])
            else:
                reg.hide_model(reg.ticks['top'])
                reg.show_model(reg.ticks['bottom'])
            
            if 0 <= self.azim < 90:
                reg.hide_model(reg.ticks['y_xmax_zmax'])
                reg.show_model(reg.ticks['y_xmin_zmax']) 
                reg.hide_model(reg.ticks['y_xmax_zmin']) 
                reg.hide_model(reg.ticks['y_xmin_zmin']) 
            elif 90 <= self.azim < 180:
                reg.show_model(reg.ticks['y_xmax_zmax'])
                reg.hide_model(reg.ticks['y_xmin_zmax']) 
                reg.hide_model(reg.ticks['y_xmax_zmin']) 
                reg.hide_model(reg.ticks['y_xmin_zmin']) 
            elif -90 <= self.azim < 0:
                reg.hide_model(reg.ticks['y_xmax_zmax'])
                reg.hide_model(reg.ticks['y_xmin_zmax']) 
                reg.hide_model(reg.ticks['y_xmax_zmin']) 
                reg.show_model(reg.ticks['y_xmin_zmin']) 
            else:
                reg.hide_model(reg.ticks['y_xmax_zmax'])
                reg.hide_model(reg.ticks['y_xmin_zmax']) 
                reg.show_model(reg.ticks['y_xmax_zmin']) 
                reg.hide_model(reg.ticks['y_xmin_zmin'])
            
            if self.up[1] > 0:
                if self.elev < 0:
                    reg.hide_model(reg.ticks['x_ymin_zmin'])
                    reg.hide_model(reg.ticks['x_ymin_zmax'])
                    reg.hide_model(reg.ticks['z_xmin_ymin'])
                    reg.hide_model(reg.ticks['z_xmax_ymin'])
                    
                    if 0 <= self.azim < 90:
                        reg.show_model(reg.ticks['x_ymax_zmax'])
                        reg.hide_model(reg.ticks['x_ymax_zmin'])
                        reg.show_model(reg.ticks['z_xmax_ymax'])
                        reg.hide_model(reg.ticks['z_xmin_ymax'])
                    elif 90 <= self.azim < 180:
                        reg.show_model(reg.ticks['x_ymax_zmin'])
                        reg.hide_model(reg.ticks['x_ymax_zmax'])
                        reg.show_model(reg.ticks['z_xmax_ymax'])
                        reg.hide_model(reg.ticks['z_xmin_ymax'])
                    elif -90 <= self.azim < 0:
                        reg.show_model(reg.ticks['x_ymax_zmax'])
                        reg.hide_model(reg.ticks['x_ymax_zmin'])
                        reg.show_model(reg.ticks['z_xmin_ymax'])
                        reg.hide_model(reg.ticks['z_xmax_ymax'])
                    else:
                        reg.show_model(reg.ticks['x_ymax_zmin'])
                        reg.hide_model(reg.ticks['x_ymax_zmax'])
                        reg.show_model(reg.ticks['z_xmin_ymax'])
                        reg.hide_model(reg.ticks['z_xmax_ymax'])
                else:
                    reg.hide_model(reg.ticks['x_ymax_zmin'])
                    reg.hide_model(reg.ticks['x_ymax_zmax'])
                    reg.hide_model(reg.ticks['z_xmin_ymax'])
                    reg.hide_model(reg.ticks['z_xmax_ymax'])
                    
                    if 0 <= self.azim < 90:
                        reg.show_model(reg.ticks['x_ymin_zmax'])
                        reg.hide_model(reg.ticks['x_ymin_zmin'])
                        reg.show_model(reg.ticks['z_xmax_ymin'])
                        reg.hide_model(reg.ticks['z_xmin_ymin'])
                    elif 90 <= self.azim < 180:
                        reg.show_model(reg.ticks['x_ymin_zmin'])
                        reg.hide_model(reg.ticks['x_ymin_zmax'])
                        reg.show_model(reg.ticks['z_xmax_ymin'])
                        reg.hide_model(reg.ticks['z_xmin_ymin'])
                    elif -90 <= self.azim < 0:
                        reg.show_model(reg.ticks['x_ymin_zmax'])
                        reg.hide_model(reg.ticks['x_ymin_zmin'])
                        reg.show_model(reg.ticks['z_xmin_ymin'])
                        reg.hide_model(reg.ticks['z_xmax_ymin'])
                    else:
                        reg.show_model(reg.ticks['x_ymin_zmin'])
                        reg.hide_model(reg.ticks['x_ymin_zmax'])
                        reg.show_model(reg.ticks['z_xmin_ymin'])
                        reg.hide_model(reg.ticks['z_xmax_ymin'])
            else:
                if self.elev < 0:
                    reg.hide_model(reg.ticks['x_ymin_zmin'])
                    reg.hide_model(reg.ticks['x_ymin_zmax'])
                    reg.hide_model(reg.ticks['z_xmin_ymin'])
                    reg.hide_model(reg.ticks['z_xmax_ymin'])
                    
                    if 0 <= self.azim < 90:
                        reg.show_model(reg.ticks['x_ymax_zmin'])
                        reg.hide_model(reg.ticks['x_ymax_zmax'])
                        reg.show_model(reg.ticks['z_xmin_ymax'])
                        reg.hide_model(reg.ticks['z_xmax_ymax'])
                    elif 90 <= self.azim < 180:
                        reg.show_model(reg.ticks['x_ymax_zmax'])
                        reg.hide_model(reg.ticks['x_ymax_zmin'])
                        reg.show_model(reg.ticks['z_xmin_ymax'])
                        reg.hide_model(reg.ticks['z_xmax_ymax'])
                    elif -90 <= self.azim < 0:
                        reg.show_model(reg.ticks['x_ymax_zmin'])
                        reg.hide_model(reg.ticks['x_ymax_zmax'])
                        reg.show_model(reg.ticks['z_xmax_ymax'])
                        reg.hide_model(reg.ticks['z_xmin_ymax'])
                    else:
                        reg.show_model(reg.ticks['x_ymax_zmax'])
                        reg.hide_model(reg.ticks['x_ymax_zmin'])
                        reg.show_model(reg.ticks['z_xmax_ymax'])
                        reg.hide_model(reg.ticks['z_xmin_ymax'])
                else:
                    reg.hide_model(reg.ticks['x_ymax_zmin'])
                    reg.hide_model(reg.ticks['x_ymax_zmax'])
                    reg.hide_model(reg.ticks['z_xmin_ymax'])
                    reg.hide_model(reg.ticks['z_xmax_ymax'])
                    
                    if 0 <= self.azim < 90:
                        reg.show_model(reg.ticks['x_ymin_zmin'])
                        reg.hide_model(reg.ticks['x_ymin_zmax'])
                        reg.show_model(reg.ticks['z_xmin_ymin'])
                        reg.hide_model(reg.ticks['z_xmax_ymin'])
                    elif 90 <= self.azim < 180:
                        reg.show_model(reg.ticks['x_ymin_zmax'])
                        reg.hide_model(reg.ticks['x_ymin_zmin'])
                        reg.show_model(reg.ticks['z_xmin_ymin'])
                        reg.hide_model(reg.ticks['z_xmax_ymin'])
                    elif -90 <= self.azim < 0:
                        reg.show_model(reg.ticks['x_ymin_zmin'])
                        reg.hide_model(reg.ticks['x_ymin_zmax'])
                        reg.show_model(reg.ticks['z_xmax_ymin'])
                        reg.hide_model(reg.ticks['z_xmin_ymin'])
                    else:
                        reg.show_model(reg.ticks['x_ymin_zmax'])
                        reg.hide_model(reg.ticks['x_ymin_zmin'])
                        reg.show_model(reg.ticks['z_xmax_ymin'])
                        reg.hide_model(reg.ticks['z_xmin_ymin'])
    
    def render_on_timer(self):
        """定时器事件函数"""
        
        self.duration = int((time.time() - self.tstamp) * 1000) + self.tbase
        self.tn += 1
        wx.CallAfter(self.render)
        
        if self.playing:
            wx.CallLater(10, self.render_on_timer)
    
    def start_animate(self):
        """开始动画"""
        
        self.render()
        if self.islive:
            self.tstamp = time.time()
            self.tbase = self.duration
            self.playing = True
            self.render_on_timer()
    
    def stop_animate(self):
        """停止动画"""
        
        self.playing = False
        #print(self.estimate())
    
    def pause_animate(self):
        """暂停/重启动画"""
        
        if self.playing:
            self.stop_animate()
        else:
            self.start_animate()
    
    def reset_timer(self):
        """复位和定时器相关的参数"""
        
        self.playing = False
        self.capturing = False
        self.creating = False
        self.tn = 0 
        self.duration = 0
        self.tbase = 0
    
    def estimate(self):
        """动画渲染帧频评估"""
        
        return 0 if self.duration == 0 else 1000*self.tn/self.duration
    
    def add_region(self, box, fixed=False, proj=None, zoom=None):
        """添加视区
        
        box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
        fixed       - 布尔型，是否锁定相机位置
        proj        - 投影模式，None表示使用场景对象的投影模式
        zoom        - 视口缩放因子，None表示使用场景对象的视口缩放因子
        """
        
        if proj is None:
            proj = self.proj
        
        if fixed and zoom is None:
            zoom = 1.0
        
        reg = region.Region(self, box, fixed, proj, zoom)
        self.regions.append(reg)
        
        return reg
    
    def set_posture(self, oecs=None, dist=None, azim=None, elev=None, save=False):
        """设置ECS原点位置、距离、方位角、仰角等参数
        
        save    - 保存当前设置
        """
        
        self._update_pos_and_up(oecs=oecs, dist=dist, azim=azim, elev=elev)
        
        if save:
            self._save_status()
    
    def set_style(self, style):
        """设置风格"""
        
        self.style = self._set_style(style)
        self._init_gl()
        self.render()
    
    def set_cam_cruise(self, func_cruise):
        """设置相机巡航函数"""
        
        self.cam_cruise = func_cruise
        if hasattr(func_cruise, '__call__'):
            self.islive = True
    
    def restore_posture(self):
        """还原观察姿态"""
        
        self.near = self.status['near']
        self.far = self.status['far']
        self.zoom = self.status['zoom']
        
        for reg in self.regions:
            reg.pmat[:] = reg.get_pmat()
        
        self.set_posture(oecs=self.status['oecs'], dist=self.status['dist'], azim=self.status['azim'], elev=self.status['elev'])
        #self.reset_timer()
        self.render()
        
    def get_scene_buffer(self, alpha=True, buffer='FRONT', crop=False):
        """以PIL对象的格式返回场景缓冲区数据
        
        alpha       - 是否使用透明通道
        buffer      - 显示缓冲区。默认使用前缓冲区（当前显示内容）
        crop        - 是否将宽高裁切为16的倍数
        """
        
        if alpha:
            gl_mode = GL_RGBA
            pil_mode = 'RGBA'
        else:
            gl_mode = GL_RGB
            pil_mode = 'RGB'
        
        if buffer == 'FRONT':
            glReadBuffer(GL_FRONT)
        elif buffer == 'BACK':
            glReadBuffer(GL_BACK)
        
        data = glReadPixels(0, 0, self.csize[0], self.csize[1], gl_mode, GL_UNSIGNED_BYTE, outputType=None)
        im = Image.fromarray(data.reshape(data.shape[1], data.shape[0], -1), mode=pil_mode)
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
        
        if crop:
            w, h = im.size
            nw, nh = 16*(w//16), 16*(h//16)
            x0, y0 = (w-nw)//2, (h-nh)//2
            x1, y1 = x0+nw, y0+nh
            im = im.crop((x0, y0, x1, y1))
        
        return im
        
    def save_scene(self, fn, alpha=True, buffer='FRONT', crop=False):
        """保存场景为图像文件
        
        fn          - 保存的文件名
        alpha       - 是否使用透明通道
        buffer      - 显示缓冲区。默认使用前缓冲区（当前显示内容）
        crop        - 是否将宽高裁切为16的倍数
        """
        
        im = self.get_scene_buffer(alpha=alpha, buffer=buffer, crop=crop)
        im.save(fn)
    
    def _create_gif_or_video(self, out_file, fps, loop=0, fn=50):
        """生成gif或视频文件的线程函数"""
        
        if os.path.splitext(out_file)[1] == '.gif':
            writer = imageio.get_writer(out_file, fps=fps, loop=loop)
        else:
            writer = imageio.get_writer(out_file, fps=fps)
        
        while not self.q.empty():
            im = np.array(self.q.get())
            writer.append_data(im)
        
        writer.close()
        self.creating = False
    
    def start_record(self, out_file, fps, loop=0, fn=50):
        """生成gif或视频文件
        
        out_file    - 文件名，支持gif和mp4、avi、wmv等格式
        fps         - 每秒帧数
        loop        - 循环播放次数（仅gif格式有效，0表示无限循环）
        fn          - 总帧数
        """
        
        self.cn = 0
        self.fn = fn
        self.q = queue.Queue()
        self.capturing = True
        self.start_animate()
        
        self.threading_record = threading.Thread(target=self._create_gif_or_video, args=(out_file, fps, loop, fn))
        self.threading_record.setDaemon(True)
        self.threading_record.start()
    
    def stop_record(self):
        """"""
        
        self.capturing = False
        self.creating = True
        self.stop_animate()
        
    
