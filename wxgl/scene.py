# -*- coding: utf-8 -*-
#
# Copyright 2020 xufive@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

"""
WxGL是一个基于pyopengl的三维数据可视化库

WxGL以wx为显示后端，提供matplotlib风格的交互绘图模式
同时，也可以和wxpython无缝结合，在wx的窗体上绘制三维模型
"""


import uuid
import wx
from wx import glcanvas
import numpy as np
from PIL import Image
from OpenGL.GL import *
from OpenGL.GLU import *

from . import region
from . import axes
from . import colormap
from . import fontmanager


class WxGLScene(glcanvas.GLCanvas):
    """GL场景类"""
    
    def __init__(self, parent, head='z+', zoom=1.0, proj='cone', mode='3D', style='black', **kwds):
        """构造函数
        
        parent      - 父级窗口对象
        head        - 观察者头部的指向，字符串
                        'x+'        - 头部指向x轴正方向
                        'y+'        - 头部指向y轴正方向
                        'z+'        - 头部指向z轴正方向
        zoom        - 视口缩放因子
        proj        - 投影模式，字符串
                        'ortho'     - 平行投影
                        'cone'      - 透视投影
        mode        - 2D/3D模式，字符串
        style       - 场景风格
                        'black'     - 背景黑色，文本白色
                        'white'     - 背景白色，文本黑色
                        'gray'      - 背景浅灰色，文本深蓝色
                        'blue'      - 背景深蓝色，文本淡青色
        kwds        - 关键字参数
                        elevation   - 仰角
                        azimuth     - 方位角
        """
        
        for key in kwds:
            if key not in ['elevation', 'azimuth']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        elevation = kwds.get('elevation', None)
        azimuth = kwds.get('azimuth', None)
        
        glcanvas.GLCanvas.__init__(self, parent, -1, style=glcanvas.WX_GL_RGBA|glcanvas.WX_GL_DOUBLEBUFFER|glcanvas.WX_GL_DEPTH_SIZE)
        
        self.fm = fontmanager.FontManager()                     # 字体管理对象
        self.cm = colormap.WxGLColorMap()                       # 调色板对象
        self.set_style(style)                                   # 设置风格
        
        self.parent = parent                                    # 父级窗口对象
        self.proj = proj                                        # 投影模式（平行投影/透视投影）
        self.mode = mode.upper()                                # 2D/3D模式
        
        if self.mode == '2D':
            head = 'y+'
        
        if head == 'x+':
            cam = [0, 5, 0]
        elif head == 'y+':
            cam = [0, 0, 5]
        else:
            cam = [5, 0, 0]
        
        aim = [0, 0, 0]
        view = [-1, 1, -1, 1, 3.2, 7]
        
        self.cam = np.array(cam, dtype=np.float)                # 相机位置
        self.aim = np.array(aim, dtype=np.float)                # 目标点位
        self.head = head                                        # 观察者头部的指向
        self.view = np.array(view, dtype=np.float)              # 视景体
        self.zoom = zoom                                        # 视口缩放因子
        self.up = None                                          # 向上的方向定义
        self.dist = None                                        # 相机位置与目标点位之间的距离
        self.elevation = None                                   # 仰角
        self.azimuth = None                                     # 方位角
        self.mpos = None                                        # 鼠标位置
        
        self.rotate_timer = wx.Timer()                          # 旋转定时器
        self.rotate_mode = 'h+'                                 # 旋转模式
        self.rotate_step = 1/180                                # 旋转步长
        
        self.size = self.GetClientSize()                        # OpenGL窗口的大小
        self.context = glcanvas.GLContext(self)                 # OpenGL上下文
        
        self.regions = dict()                                   # 存储视区信息
        self.subgraphs = dict()                                 # 存储子图信息
        self.store = {'zoom':zoom}                              # 存储相机姿态、缩放比例等
        
        self.set_camera(save=True)                              # 设置相机位置
        self.init_gl()                                          # 画布初始化
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_RIGHT_UP, self.on_right_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        
        self.rotate_timer.Bind(wx.EVT_TIMER, self.on_rotate_timer)
        
        if self.mode == '3D' and (elevation != None or azimuth != None):
            self.set_posture(elevation=elevation, azimuth=azimuth, save=True)
    
    def set_style(self, style):
        """设置风格"""
        
        assert style in ('black', 'white', 'gray', 'blue'), '期望参数style是"black", "white", "gray", "blue"其中之一'
        
        self.style = style
        if style == 'white':
            self.bg = [1.0, 1.0, 1.0, 1.0]
            self.tc = [0.1, 0.1, 0.1]
        elif style == 'gray':
            self.bg = [0.9, 0.9, 0.9, 1.0]
            self.tc = [0.0, 0.0, 0.3]
        elif style == 'blue':
            self.bg = [0.0, 0.0, 0.2, 1.0]
            self.tc = [0.9, 1.0, 1.0]
        else:
            self.bg = [0.0, 0.0, 0.0, 1.0]
            self.tc = [0.9, 0.9, 0.9]
    
    def on_rotate_timer(self, evt):
        """场景旋转定时器函数"""
        
        if self.rotate_mode == 'h+':
            a = self.azimuth + self.rotate_step
            self.set_posture(azimuth=np.degrees(a), save=False)
        elif self.rotate_mode == 'h-':
            a = self.azimuth - self.rotate_step
            self.set_posture(azimuth=np.degrees(a), save=False)
        elif self.rotate_mode == 'v+':
            e = self.elevation + self.rotate_step
            self.set_posture(elevation=np.degrees(e), save=False)
        else:
            e = self.elevation - self.rotate_step
            self.set_posture(elevation=np.degrees(e), save=False)
    
    def on_destroy(self, evt):
        """加载场景的应用程序关闭时回收GPU的缓存"""
        
        self.rotate_timer.Stop()
        for rid in self.regions:
            for buf_id in self.regions[rid].buffers:
                self.regions[rid].buffers[buf_id].delete()
            for item in self.regions[rid].textures:
                self.regions[rid].delete_texture(item)
            for name in self.regions[rid].timers:
                self.regions[rid].timers[name]['timer'].Unbind(wx.EVT_TIMER)
        
        evt.Skip()
        
    def on_resize(self, evt):
        """响应窗口尺寸改变事件"""
        
        if self.context:
            self.SetCurrent(self.context)
            self.size = self.GetClientSize()
            self.Refresh(False)
        
        evt.Skip()
        
    def on_erase(self, evt):
        """响应背景擦除事件"""
        
        pass
        
    def on_paint(self, evt):
        """响应重绘事件"""
        
        self.SetCurrent(self.context)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)    # 清除屏幕及深度缓存
        self.draw_gl()                                      # 绘图
        self.SwapBuffers()                                  # 切换缓冲区，以显示绘制内容
        evt.Skip()
        
    def on_left_down(self, evt):
        """响应鼠标左键按下事件"""
        
        self.CaptureMouse()
        self.mpos = evt.GetPosition()
        
    def on_left_up(self, evt):
        """响应鼠标左键弹起事件"""
        
        try:
            self.ReleaseMouse()
        except:
            pass
        
    def on_right_up(self, evt):
        """响应鼠标右键弹起事件"""
        
        self.stop_rotate()
        evt.Skip()
        
    def on_mouse_motion(self, evt):
        """响应鼠标移动事件"""
        
        if evt.Dragging() and evt.LeftIsDown():
            pos = evt.GetPosition()
            try:
                dx, dy = pos - self.mpos
            except:
                return
            self.mpos = pos
            
            if self.mode == '3D':
                elevation = self.elevation + 2*np.pi*dy/self.size[1]
                azimuth = self.azimuth - 2*np.pi*dx/self.size[0]
                
                self._set_posture(elevation=elevation, azimuth=azimuth, dist=self.dist)
            else:
                dx = (self.view[1]-self.view[0])*dx/self.size[0]
                dy = (self.view[3]-self.view[2])*dy/self.size[1]
                self.aim[0] -= dx
                self.aim[1] += dy
                self.cam[0] -= dx
                self.cam[1] += dy
                
                self.set_camera(cam=self.cam.tolist(), aim=self.aim.tolist(), head=self.head)
            
            self.Refresh(False)
        
    def on_mouse_wheel(self, evt):
        """响应鼠标滚轮事件"""
        
        if evt.WheelRotation < 0:
            self.zoom *= 1.1
            if self.zoom > 100:
                self.zoom = 100
        elif evt.WheelRotation > 0:
            self.zoom *= 0.9
            if self.zoom < 0.01:
                self.zoom = 0.01
        
        self.Refresh(False)
    
    def init_gl(self):
        """初始化GL"""
        
        self.SetCurrent(self.context)
        
        glClearColor(*self.bg,)                                     # 设置画布背景色
        glEnable(GL_DEPTH_TEST)                                     # 开启深度测试，实现遮挡关系        
        glDepthFunc(GL_LEQUAL)                                      # 设置深度测试函数
        glShadeModel(GL_SMOOTH)                                     # GL_SMOOTH(光滑着色)/GL_FLAT(恒定着色)
        glEnable(GL_BLEND)                                          # 开启混合        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)           # 设置混合函数
        glEnable(GL_ALPHA_TEST)                                     # 启用Alpha测试 
        glAlphaFunc(GL_GREATER, 0.05)                               # 设置Alpha测试条件为大于0.05则通过
        glFrontFace(GL_CW)                                          # 设置逆时针索引为正面（GL_CCW/GL_CW）
        glEnable(GL_LINE_SMOOTH)                                    # 开启线段反走样
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, (0.6,0.6,0.6,1.0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, (0.2,0.2,0.2,1.0))
        glLightfv(GL_LIGHT0, GL_POSITION, (6.0,0.0,2.0,1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.2,0.2,0.2,1.0))
        glEnable(GL_LIGHT0)
                
    def draw_gl(self):
        """绘制"""
        
        for rid in list(self.regions.keys()):
            if rid in self.regions:
                reg = self.regions[rid]
            else:
                return
            
            x0, y0 = int(reg.box[0]*self.size[0]), int(reg.box[1]*self.size[1])
            w_reg, h_reg = int(reg.box[2]*self.size[0]), int(reg.box[3]*self.size[1])
            k = w_reg/h_reg
            
            glViewport(x0, y0, w_reg, h_reg)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            
            if reg.fixed:
                proj = 'ortho'
                zoom, lookat = 1, (0,0,5,0,0,0,0,1,0)
                scale, translate = 1, (0,0,0)
            else:
                proj = self.proj
                zoom, lookat = self.zoom, (*self.cam, *self.aim, *self.up)
                scale, translate = reg.scale, reg.translate
            
            if k > 1:
                box = (-zoom*k, zoom*k, -zoom, zoom)
            else:
                box = (-zoom, zoom, -zoom/k, zoom/k)
            
            if proj == 'ortho':
                glOrtho(*box, self.view[4], self.view[5])
            else:
                glFrustum(*box, self.view[4], self.view[5])
            
            gluLookAt(*lookat,)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glScale(scale, scale, scale)
            glTranslate(*translate,)
            
            for name in reg.assembly:
                if reg.assembly[name]['display']:
                    for item in reg.assembly[name]['component']:
                        item['cmd'](item['args'])
        
    def set_camera(self, cam=None, aim=None, head=None, save=False):
        """设置相机位置、目标点位、观察者头部的指向"""
        
        if isinstance(cam, list) and len(cam)==3:
            self.cam = np.array(cam, dtype=np.float)
        if isinstance(aim, list) and len(aim)==3:
            self.aim = np.array(aim, dtype=np.float)
        if head in ['x+', 'y+', 'z+']:
            self.head = head
        
        self.dist = np.sqrt(np.power((self.cam-self.aim), 2).sum())
        if self.dist > 0:
            if self.head == 'z+':
                #  +-->y
                #  ↓
                #  x：0°方位角，逆时针为正
                self.elevation = np.arcsin((self.cam[2]-self.aim[2])/self.dist)
                self.azimuth = np.arccos((self.cam[0]-self.aim[0])/(self.dist*np.cos(self.elevation)))
                if self.cam[1] < self.aim[1]:
                    self.azimuth *= -1
                self.up = np.array([0,0,1], dtype=np.float)
            elif self.head == 'y+':
                #  +-->x
                #  ↓
                #  z：0°方位角，逆时针为正
                self.elevation = np.arcsin((self.cam[1]-self.aim[1])/self.dist)
                self.azimuth = np.arccos((self.cam[2]-self.aim[2])/(self.dist*np.cos(self.elevation)))
                if self.cam[0] < self.aim[0]:
                    self.azimuth *= -1
                self.up = np.array([0,1,0], dtype=np.float)
            elif self.head == 'x+':
                #  +-->z
                #  ↓
                #  y：0°方位角，逆时针为正
                self.elevation = np.arcsin((self.cam[0]-self.aim[0])/self.dist)
                self.azimuth = np.arccos((self.cam[1]-self.aim[1])/(self.dist*np.cos(self.elevation)))
                if self.cam[2] < self.aim[2]:
                    self.azimuth *= -1
                self.up = np.array([1,0,0], dtype=np.float)
        else:
            self.elevation = 0.0
            self.azimuth = 0.0
        
        if 0.5*np.pi < self.elevation or self.elevation < -.5*np.pi:
            self.up = -1*np.abs(self.up)
        else:
            self.up = np.abs(self.up)
        
        self.Refresh(False)
        if save:
            self.store.update({'cam':self.cam.tolist(), 'aim':self.aim.tolist(), 'head':self.head})
        
    def _set_posture(self, elevation, azimuth, dist):
        """设置仰角、方位角、相机位置与目标点位之间的距离
        
        elevation   - 仰角(弧度)
        azimuth     - 方位角(弧度)
        dist        - 相机位置与目标点位之间的距离
        """
        
        elevation %= 2*np.pi
        if elevation > np.pi:
            elevation -= 2*np.pi
        
        azimuth %= 2*np.pi
        if azimuth > np.pi:
            azimuth -= 2*np.pi
        
        self.elevation = elevation
        self.azimuth = azimuth
        self.dist = dist
        
        d = self.dist*np.cos(self.elevation)
        
        if self.head == 'z+':
            self.cam = np.array([d*np.cos(self.azimuth), d*np.sin(self.azimuth), self.dist*np.sin(self.elevation)+self.aim[2]])
            u, v, w = 'x', 'y', 'z'
        elif self.head == 'y+':
            self.cam = np.array([d*np.sin(self.azimuth), self.dist*np.sin(self.elevation)+self.aim[1], d*np.cos(self.azimuth)])
            u, v, w = 'z', 'x', 'y'
        elif self.head == 'x+':
            self.cam = np.array([self.dist*np.sin(self.elevation)+self.aim[0], d*np.cos(self.azimuth), d*np.sin(self.azimuth)])
            u, v, w = 'y', 'z', 'x'
        
        if 0.5*np.pi < self.elevation or self.elevation < -.5*np.pi:
            self.up = -1*np.abs(self.up)
        else:
            self.up = np.abs(self.up)
        
        for rid in self.regions:
            reg = self.regions[rid]
            if reg.grid_tick:
                gid = reg.grid_tick['gid']
                tick = reg.grid_tick['tick']
                
                if elevation < 0:
                    reg.show_model('%s_%s%s_%smax'%(gid,u,v,w))
                    reg.hide_model('%s_%s%s_%smin'%(gid,u,v,w))
                else:
                    reg.show_model('%s_%s%s_%smin'%(gid,u,v,w))
                    reg.hide_model('%s_%s%s_%smax'%(gid,u,v,w))
                
                if -np.pi <= azimuth < -np.pi/2:
                    reg.hide_model('%s_%s%s_%smin'%(gid,v,w,u))
                    reg.hide_model('%s_%s%s_%smin'%(gid,w,u,v))
                    reg.show_model('%s_%s%s_%smax'%(gid,v,w,u))
                    reg.show_model('%s_%s%s_%smax'%(gid,w,u,v))
                elif -np.pi/2 <= azimuth < 0:
                    reg.hide_model('%s_%s%s_%smax'%(gid,v,w,u))
                    reg.hide_model('%s_%s%s_%smin'%(gid,w,u,v))
                    reg.show_model('%s_%s%s_%smin'%(gid,v,w,u))
                    reg.show_model('%s_%s%s_%smax'%(gid,w,u,v))
                elif 0 <= azimuth < np.pi/2:
                    reg.hide_model('%s_%s%s_%smax'%(gid,v,w,u))
                    reg.hide_model('%s_%s%s_%smax'%(gid,w,u,v))
                    reg.show_model('%s_%s%s_%smin'%(gid,v,w,u))
                    reg.show_model('%s_%s%s_%smin'%(gid,w,u,v))
                elif np.pi/2 <= azimuth < np.pi:
                    reg.hide_model('%s_%s%s_%smin'%(gid,v,w,u))
                    reg.hide_model('%s_%s%s_%smax'%(gid,w,u,v))
                    reg.show_model('%s_%s%s_%smax'%(gid,v,w,u))
                    reg.show_model('%s_%s%s_%smin'%(gid,w,u,v))
                
                if -np.pi <= azimuth < -5*np.pi/6:
                    reg.hide_models(tick[w]['%s0%s0'%(u,v)])
                    reg.show_models(tick[w]['%s0%s1'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s1'%(u,v)])
                elif -5*np.pi/6 <= azimuth < -np.pi/2:
                    reg.hide_models(tick[w]['%s0%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s0%s1'%(u,v)])
                    reg.show_models(tick[w]['%s1%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s1'%(u,v)])
                elif -np.pi/2 <= azimuth < -np.pi/3:
                    reg.show_models(tick[w]['%s0%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s0%s1'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s1'%(u,v)])
                elif -np.pi/3 <= azimuth < 0:
                    reg.hide_models(tick[w]['%s0%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s0%s1'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s0'%(u,v)])
                    reg.show_models(tick[w]['%s1%s1'%(u,v)])
                elif 0 <= azimuth < np.pi/6:
                    reg.hide_models(tick[w]['%s0%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s0%s1'%(u,v)])
                    reg.show_models(tick[w]['%s1%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s1'%(u,v)])
                elif np.pi/6 <= azimuth < np.pi/2:
                    reg.hide_models(tick[w]['%s0%s0'%(u,v)])
                    reg.show_models(tick[w]['%s0%s1'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s1'%(u,v)])
                elif np.pi/2 <= azimuth < 2*np.pi/3:
                    reg.hide_models(tick[w]['%s0%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s0%s1'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s0'%(u,v)])
                    reg.show_models(tick[w]['%s1%s1'%(u,v)])
                elif 2*np.pi/3 <= azimuth < np.pi:
                    reg.show_models(tick[w]['%s0%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s0%s1'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s0'%(u,v)])
                    reg.hide_models(tick[w]['%s1%s1'%(u,v)])
                
                if -np.pi <= azimuth < -np.pi/2:
                    if elevation < 0:
                        reg.hide_models(tick[v]['%s0%s0'%(w,u)])
                        reg.show_models(tick[v]['%s1%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s0%s1'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s1'%(w,u)])
                    else:
                        reg.show_models(tick[v]['%s0%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s0%s1'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s1'%(w,u)])
                elif -np.pi/2 <= azimuth < 0:
                    if elevation < 0:
                        reg.hide_models(tick[v]['%s0%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s0%s1'%(w,u)])
                        reg.show_models(tick[v]['%s1%s1'%(w,u)])
                    else:
                        reg.hide_models(tick[v]['%s0%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s0'%(w,u)])
                        reg.show_models(tick[v]['%s0%s1'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s1'%(w,u)])
                elif 0 <= azimuth < np.pi/2:
                    if elevation < 0:
                        reg.hide_models(tick[v]['%s0%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s0%s1'%(w,u)])
                        reg.show_models(tick[v]['%s1%s1'%(w,u)])
                    else:
                        reg.hide_models(tick[v]['%s0%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s0'%(w,u)])
                        reg.show_models(tick[v]['%s0%s1'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s1'%(w,u)])
                elif np.pi/2 <= azimuth < np.pi:
                    if elevation < 0:
                        reg.hide_models(tick[v]['%s0%s0'%(w,u)])
                        reg.show_models(tick[v]['%s1%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s0%s1'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s1'%(w,u)])
                    else:
                        reg.show_models(tick[v]['%s0%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s0'%(w,u)])
                        reg.hide_models(tick[v]['%s0%s1'%(w,u)])
                        reg.hide_models(tick[v]['%s1%s1'%(w,u)])
                
                if azimuth < 0:
                    if elevation < 0:
                        reg.hide_models(tick[u]['%s0%s0'%(v,w)])
                        reg.show_models(tick[u]['%s0%s1'%(v,w)])
                        reg.hide_models(tick[u]['%s1%s0'%(v,w)])
                        reg.hide_models(tick[u]['%s1%s1'%(v,w)])
                    else:
                        reg.show_models(tick[u]['%s0%s0'%(v,w)])
                        reg.hide_models(tick[u]['%s0%s1'%(v,w)])
                        reg.hide_models(tick[u]['%s1%s0'%(v,w)])
                        reg.hide_models(tick[u]['%s1%s1'%(v,w)])
                else:
                    if elevation < 0:
                        reg.hide_models(tick[u]['%s0%s0'%(v,w)])
                        reg.hide_models(tick[u]['%s0%s1'%(v,w)])
                        reg.hide_models(tick[u]['%s1%s0'%(v,w)])
                        reg.show_models(tick[u]['%s1%s1'%(v,w)])
                    else:
                        reg.hide_models(tick[u]['%s0%s0'%(v,w)])
                        reg.hide_models(tick[u]['%s0%s1'%(v,w)])
                        reg.show_models(tick[u]['%s1%s0'%(v,w)])
                        reg.hide_models(tick[u]['%s1%s1'%(v,w)])
                
                reg.refresh()
        
    def set_posture(self, elevation=None, azimuth=None, dist=None, save=False):
        """设置仰角、方位角、相机位置与目标点位之间的距离
        
        elevation   - 仰角(度)
        azimuth     - 方位角(度)
        dist        - 相机位置与目标点位之间的距离
        save        - 是否保存相机姿态
        """
        
        if isinstance(elevation, (int,float)):
            elevation %= 360
            if elevation > 180:
                elevation -= 360
            elevation = np.radians(elevation)
        else:
            elevation = self.elevation
            
        if isinstance(azimuth, (int,float)):
            azimuth %= 360
            if azimuth > 180:
                azimuth -= 360
            azimuth = np.radians(azimuth)
        else:
            azimuth = self.azimuth
        
        if not isinstance(dist, (int,float)):
            dist = self.dist
        
        self._set_posture(elevation, azimuth, dist)
        self.Refresh(False)
        
        if save:
            self.store.update({'cam':self.cam.tolist()})
        
    def set_zoom(self, zoom, save=False):
        """设置视口缩放因子"""
        
        assert isinstance(zoom, (int, float)), '参数类型错误'
        
        self.zoom = zoom
        self.Refresh(False)
        
        if save:
            self.store.update({'zoom':zoom})
        
    def reset_posture(self):
        """还原观察姿态、视口缩放因子"""
        
        self.zoom = self.store['zoom']
        self.set_camera(cam=self.store['cam'], aim=self.store['aim'], head=self.store['head'])
        self.set_posture()
        self.stop_rotate()
        self.Refresh(False)
        
    def save_scene(self, fn, alpha=True, buffer='FRONT'):
        """保存场景为图像文件
        
        fn          - 保存的文件名
        alpha       - 是否使用透明通道
        buffer      - 显示缓冲区。默认使用前缓冲区（当前显示内容）
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
        
        data = glReadPixels(0, 0, self.size[0], self.size[1], gl_mode, GL_UNSIGNED_BYTE, outputType=None)
        img = Image.fromarray(data.reshape(data.shape[1], data.shape[0], -1), mode=pil_mode)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img.save(fn)
        
    def add_region(self, box, fixed=False):
        """添加视区
        
        box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
        fixed       - 是否锁定旋转缩放
        """
        
        rid = uuid.uuid1().hex
        reg = region.WxGLRegion(self, rid, box, fixed=fixed)
        self.regions.update({rid: reg})
        
        return reg
    
    def add_axes(self, pos, padding=(20,20,20,20)):
        """添加子图
        
        pos         - 三个数字组成的字符串或四元组，表示子图在场景中的位置和大小
        padding     - 四元组，上、右、下、左四个方向距离边缘的留白像素
        """
        
        return axes.WxAxes(self, pos, padding=padding)
    
    def auto_rotate(self, rotation='h+', **kwds):
        """自动旋转
        
        rotation    - 旋转模式
                        'h+'        - 水平顺时针旋转（默认方式）
                        'h-'        - 水平逆时针旋转
                        'v+'        - 垂直前翻旋转
                        'v-'        - 垂直后翻旋转
        kwds        - 关键字参数
                        elevation   - 初始仰角，以度（°）为单位，默认值为0
                        azimuth     - 初始方位角以度（°）为单位，默认值为0
                        step        - 帧增量，以度（°）为单位，默认值为5
                        interval    - 帧间隔，以ms为单位，默认值为20
        """
        
        assert rotation in ['h+', 'h-', 'v+', 'v-'], '期望参数rotation是"h+"/"h-"/"v+"/"v-"中的一项'
        
        for key in kwds:
            if key not in ['elevation', 'azimuth', 'step', 'interval']:
                raise KeyError('不支持的关键字参数：%s'%key)
        
        elevation = kwds.get('elevation', 0)
        azimuth = kwds.get('azimuth', 0)
        step = kwds.get('step', 1)
        interval = kwds.get('interval', 10)
        
        self.rotate_mode = rotation
        self.rotate_step = step/180
        
        self.set_posture(elevation=elevation, azimuth=azimuth, save=False)
        self.rotate_timer.Start(interval)
    
    def stop_rotate(self):
        """停止旋转"""
        
        self.rotate_timer.Stop()

        