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


import wx
from wx import glcanvas
import numpy as np
from PIL import Image
from OpenGL.GL import *
from OpenGL.GLU import *

from . import region


class GLScene(glcanvas.GLCanvas):
    """GL场景类"""
    
    def __init__(self, parent, font, bg=[0,0,0,0], cam=[5,0,0], aim=[0,0,0], head='z+', view=[-1,1,-1,1,3.5,10], mode='cone'):
        """构造函数
        
        parent      - 父级窗口对象
        font        - 字体文件
        bg          - OpenGL窗口的背景色
        cam         - 相机位置
        aim         - 目标点位
        head        - 观察者头部的指向
                        x+      - 头部指向x轴正方向
                        y+      - 头部指向y轴正方向
                        z+      - 头部指向z轴正方向
        view        - 视景体
        mode        - 投影模式
                        ortho   - 平行投影
                        cone    - 透视投影
        """
        
        glcanvas.GLCanvas.__init__(self, parent, -1, style=glcanvas.WX_GL_RGBA|glcanvas.WX_GL_DOUBLEBUFFER|glcanvas.WX_GL_DEPTH_SIZE)
        
        self.parent = parent                                    # 父级窗口对象
        self.font = font                                        # 字体文件
        self.bg = np.array(bg, dtype=np.float)                  # OpenGL窗口的背景色
        self.mode = mode                                        # 投影模式（平行投影/透视投影）
        
        self.cam = np.array(cam, dtype=np.float)                # 相机位置
        self.aim = np.array(aim, dtype=np.float)                # 目标点位
        self.head = head                                        # 观察者头部的指向
        self.up = None                                          # 向上的方向定义
        self.dist = None                                        # 相机位置与目标点位之间的距离
        self.elevation = None                                   # 仰角
        self.azimuth = None                                     # 方位角
        self.view = None                                        # 视景体
        self.zoom = None                                        # 视口缩放因子
        self.scale = None                                       # 模型矩阵缩放比例
        self.mpos = None                                        # 鼠标位置
        
        self.size = self.GetClientSize()                        # OpenGL窗口的大小
        self.context = glcanvas.GLContext(self)                 # OpenGL上下文
        
        self.regions = dict()                                   # 存储视口设置信息
        self.buffers = dict()                                   # 存储GPU缓冲区数据对象
        self.store = dict()                                     # 存储相机姿态、视口缩放因子、模型矩阵缩放比例等
        
        self.setView(view, save=True)                           # 设置视景体
        self.setZoom(1, save=True)                              # 设置视口缩放因子（0.1~10.0）
        self.setScale([1,1,1], save=True)                       # 设置模型矩阵缩放比例
        self.setCamera(save=True)                               # 设置相机位置
        self.initGL()                                           # 画布初始化
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onErase)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
        self.Bind(wx.EVT_RIGHT_UP, self.onRightUp)
        self.Bind(wx.EVT_MOTION, self.onMouseMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)

    def onDestroy(self, evt):
        """加载场景的应用程序关闭时回收GPU的缓存"""
        
        for id in self.buffers:
            self.buffers[id].delete()
        
        evt.Skip()
        
    def onErase(self, evt):
        """响应背景擦除事件"""
        
        pass
        
    def onResize(self, evt):
        """响应窗口尺寸改变事件"""
        
        if self.context:
            self.SetCurrent(self.context)
            self.size = self.GetClientSize()
            self.Refresh(False)
            
        evt.Skip()
        
    def onPaint(self, evt):
        """响应重绘事件"""
        
        self.SetCurrent(self.context)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)    # 清除屏幕及深度缓存
        self.drawGL()                                       # 绘图
        self.SwapBuffers()                                  # 切换缓冲区，以显示绘制内容
        
        evt.Skip()
        
    def onLeftDown(self, evt):
        """响应鼠标左键按下事件"""
        
        self.CaptureMouse()
        self.mpos = evt.GetPosition()
        
    def onLeftUp(self, evt):
        """响应鼠标左键弹起事件"""
        
        try:
            self.ReleaseMouse()
        except:
            pass

    def onRightUp(self, evt):
        """响应鼠标右键弹起事件"""
        
        pass
        
    def onMouseMotion(self, evt):
        """响应鼠标移动事件"""
        
        if evt.Dragging() and evt.LeftIsDown():
            pos = evt.GetPosition()
            dx, dy = pos - self.mpos
            self.mpos = pos
            
            if -0.5*np.pi < self.elevation < 0.5*np.pi:
                dx *= -1
            
            elevation = self.elevation + 2*np.pi*dy/self.size[1]
            azimuth = self.azimuth + 2*np.pi*dx/self.size[0]
            self._setPosture(elevation=elevation, azimuth=azimuth, dist=self.dist)
            
            self.Refresh(False)
        
    def onMouseWheel(self, evt):
        """响应鼠标滚轮事件"""
        
        if evt.WheelRotation < 0:
            self.zoom *= 1.1
            if self.zoom > 10:
                self.zoom = 10
        elif evt.WheelRotation > 0:
            self.zoom *= 0.9
            if self.zoom < 0.1:
                self.zoom = 0.1
        
        self.Refresh(False)
        
        # 更新父级窗口信息显示
        self.parent.st_port.SetLabel(u'%.2f'%self.zoom)
        
    def initGL(self):
        """初始化GL"""
        
        self.SetCurrent(self.context)
        
        glClearColor(self.bg[0],self.bg[1],self.bg[2],self.bg[3])   # 设置画布背景色
        glEnable(GL_DEPTH_TEST)                                     # 开启深度测试，实现遮挡关系        
        glDepthFunc(GL_LEQUAL)                                      # 设置深度测试函数
        glShadeModel(GL_SMOOTH)                                     # GL_SMOOTH(光滑着色)/GL_FLAT(恒定着色)
        glEnable(GL_BLEND)                                          # 开启混合        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)           # 设置混合函数
        glEnable(GL_ALPHA_TEST)                                     # 启用Alpha测试 
        glAlphaFunc(GL_GREATER, 0.05)                               # 设置Alpha测试条件为大于0.05则通过
        glFrontFace(GL_CW)                                          # 设置逆时针索引为正面（GL_CCW/GL_CW）
        
    def drawGL(self):
        """绘制"""
        
        width, height = self.size
        for key in self.regions:
            reg = self.regions[key]
            x0, y0 = int(reg.box[0]*width), int(reg.box[1]*height)
            w, h = int(reg.box[2]*width), int(reg.box[3]*height)
            
            glViewport(x0, y0, w, h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            
            if isinstance(reg.view, np.ndarray):
                view = reg.view
            else:
                view = self.view
            
            if reg.mode:
                mode = reg.mode
            else:
                mode = self.mode
            
            if isinstance(reg.scale, np.ndarray):
                zoom = 1.0
            else:
                zoom = self.zoom
            
            if w > h:
                if mode == 'ortho':
                    glOrtho(zoom*view[0]*w/h, zoom*view[1]*w/h, zoom*view[2], zoom*view[3], view[4], view[5])
                else:
                    glFrustum(zoom*view[0]*w/h, zoom*view[1]*w/h, zoom*view[2], zoom*view[3], view[4], view[5])
            else:
                if mode == 'ortho':
                    glOrtho(zoom*view[0], zoom*view[1], zoom*view[2]*h/w, zoom*view[3]*h/w, view[4], view[5])
                else:
                    glFrustum(zoom*view[0], zoom*view[1], zoom*view[2]*h/w, zoom*view[3]*h/w, view[4], view[5])
            
            if isinstance(reg.lookat, np.ndarray):
                gluLookAt(
                    reg.lookat[0], reg.lookat[1], reg.lookat[2], 
                    reg.lookat[3], reg.lookat[4], reg.lookat[5],
                    reg.lookat[6], reg.lookat[7], reg.lookat[8]
                )
            else:
                gluLookAt(
                    self.cam[0], self.cam[1], self.cam[2], 
                    self.aim[0], self.aim[1], self.aim[2],
                    self.up[0], self.up[1], self.up[2]
                )
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            if isinstance(reg.scale, np.ndarray):
                glScale(reg.scale[0], reg.scale[1], reg.scale[2])
            else:
                glScale(self.scale[0], self.scale[1], self.scale[2])
            
            for item in reg.assembly:
                item['cmd'](item['args'])
        
    def setCamera(self, cam=None, aim=None, head=None, save=False):
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
        
        self.Refresh(False)
        if save:
            self.store.update({'cam':self.cam.tolist(), 'aim':self.aim.tolist(), 'head':self.head})
        
        # 更新父级窗口信息显示
        self.parent.st_cam.SetLabel(u'[%.2f, %.2f, %.2f]'%(self.cam[0], self.cam[1], self.cam[2]))
        self.parent.st_aim.SetLabel(u'[%.2f, %.2f, %.2f]'%(self.aim[0], self.aim[1], self.aim[2]))
        self.parent.st_head.SetLabel(self.head)
        self.parent.st_elevation.SetLabel(u'%.2f°'%np.degrees(self.elevation))
        self.parent.st_azimuth.SetLabel(u'%.2f°'%np.degrees(self.azimuth))
        self.parent.st_dist.SetLabel(u'%.2f'%self.dist)
        
    def _setPosture(self, elevation, azimuth, dist):
        """设置仰角、方位角、相机位置与目标点位之间的距离
        
        elevation   - 仰角(弧度)
        azimuth     - 方位角(弧度)
        dist        - 相机位置与目标点位之间的距离
        """
        
        self.elevation = elevation
        self.azimuth = azimuth
        self.dist = dist
        
        d = self.dist*np.cos(self.elevation)
        
        if self.head == 'z+':
            self.cam = np.array([d*np.cos(self.azimuth), d*np.sin(self.azimuth), self.dist*np.sin(self.elevation)+self.aim[2]], dtype=np.float)
        elif self.head == 'y+':
            self.cam = np.array([d*np.sin(self.azimuth), self.dist*np.sin(self.elevation)+self.aim[1], d*np.cos(self.azimuth)], dtype=np.float)
        elif self.head == 'x+':
            self.cam = np.array([self.dist*np.sin(self.elevation)+self.aim[0], d*np.cos(self.azimuth), d*np.sin(self.azimuth)], dtype=np.float)
        
        if 0.5*np.pi < self.elevation or self.elevation < -.5*np.pi:
            self.up = -1*np.abs(self.up)
        else:
            self.up = np.abs(self.up)
        
        # 更新父级窗口信息显示
        self.parent.st_cam.SetLabel(u'[%.2f, %.2f, %.2f]'%(self.cam[0], self.cam[1], self.cam[2]))
        self.parent.st_aim.SetLabel(u'[%.2f, %.2f, %.2f]'%(self.aim[0], self.aim[1], self.aim[2]))
        self.parent.st_head.SetLabel(self.head)
        self.parent.st_elevation.SetLabel(u'%.2f°'%np.degrees(self.elevation))
        self.parent.st_azimuth.SetLabel(u'%.2f°'%np.degrees(self.azimuth))
        self.parent.st_dist.SetLabel(u'%.2f'%self.dist)
        
    def setPosture(self, elevation=None, azimuth=None, dist=None, save=False):
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
        
        self._setPosture(elevation, azimuth, dist)
        self.Refresh(False)
        
        if save:
            #self.store.update({'elevation':self.elevation, 'azimuth':self.azimuth, 'dist':self.dist})
            self.store.update({'cam':self.cam.tolist()})
        
    def setMode(self, mode_str):
        """设置投影模式"""
        
        assert mode_str in ['ortho', 'cone'], u'参数错误'
        
        self.mode = mode_str
        self.Refresh(False)
        
    def setView(self, view_list, save=False):
        """设置视景体"""
        
        assert isinstance(view_list, list) and len(view_list) == 6, u'参数类型错误'
            
        self.view = np.array(view_list, dtype=np.float)
        self.Refresh(False)
            
        if save:
            self.store.update({'view':self.view})
        
    def setScale(self, scale_list, save=False):
        """设置模型矩阵缩放比例"""
        
        assert isinstance(scale_list, list) and len(scale_list) == 3, u'参数类型错误'
        
        self.scale = np.array(scale_list, dtype=np.float)
        self.Refresh(False)
            
        if save:
            self.store.update({'scale':self.scale})
        
    def setZoom(self, zoom, save=False):
        """设置视口缩放因子"""
        
        assert isinstance(zoom, (int, float)), u'参数类型错误'
        
        self.zoom = zoom
        self.Refresh(False)
        
        if save:
            self.store.update({'zoom':zoom})
        
    def getMode(self):
        """获取投影模式"""
        
        return self.mode
        
    def getView(self):
        """获取视景体"""
        
        return self.view
        
    def getScale(self):
        """获取模型矩阵缩放比例"""
        
        return self.scale
        
    def getZoom(self):
        """获取视口缩放因子"""
        
        return self.zoom
        
    def getCamera(self):
        """获取相机信息"""
        
        return {
            'cam':          self.cam, 
            'aim':          self.aim, 
            'head':         self.head, 
            'elevation':    np.degrees(self.elevation), 
            'azimuth':      np.degrees(self.azimuth), 
            'dist':         self.dist
        }
        
    def restorePosture(self):
        """还原观察姿态、视口缩放因子、模型矩阵缩放比例"""
        
        self.zoom = self.store['zoom']
        self.view = self.store['view']
        self.scale = self.store['scale']
        self.setCamera(cam=self.store['cam'], aim=self.store['aim'], head=self.store['head'])
        
        self.Refresh(False)
        
        # 更新父级窗口信息显示
        self.parent.st_port.SetLabel(u'%.2f'%self.zoom)
        self.parent.st_scale.SetLabel(u'[%.2f, %.2f, %.2f]'%(self.scale[0],self.scale[1],self.scale[2]))
        
    def screenshot(self, fn, alpha=True, buffer='FRONT'):
        """屏幕截图
        
        fn          - 保存的文件名
        alpha       - 是否使用透明通道
        buffer      - 截屏数据选择的缓冲区。默认使用前缓冲区（当前显示内容）
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
        
    def addRegion(self, region_name, box, lookat=None, scale=None, view=None, mode=None):
        """添加视区
        
        region_name - 视区的名字
        box         - 四元组，元素值域[0,1]。四个元素分别表示视区左下角坐标、宽度、高度
        lookat      - 视点、参考点和向上的方向。若为None，表示使用父级场景的设置
        scale       - 模型矩阵缩放比例。若为None，表示使用父级场景的设置
        view        - 视景体。若为None，表示使用父级场景的设置
        mode        - 投影模式
                        None    - 使用父级设置
                        ortho   - 平行投影
                        cone    - 透视投影
        """
        
        reg = region.GLRegion(self, region_name, box, lookat=lookat, scale=scale, view=view, mode=mode)
        self.regions.update({region_name: reg})
        
        return reg
        
    def delRegion(self, region_name):
        """删除视区"""
        
        reg = self.regions.pop(region_name)
        del reg
        