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

from region import *


class GLScene(glcanvas.GLCanvas):
    """GL场景类"""
    
    def __init__(self, parent, bg=[0,0,0,0], eye=[0,0,2], aim=[0,0,0], head='y+', view=[-1,1,-1,1,1,5], mode='cone'):
        """构造函数
        
        parent      - 父级窗口对象
        bg          - OpenGL窗口的背景色
        head        - 观察者头部的指向
                        x+      - 头部指向x轴正方向
                        x-      - 头部指向x轴负方向
                        y+      - 头部指向y轴正方向
                        y-      - 头部指向y轴负方向
                        z+      - 头部指向z轴正方向
                        z-      - 头部指向z轴负方向
        eye         - 眼睛的位置
        aim         - 视线方向参考点
        view        - 视景体
        mode        - 投影模式
                        ortho   - 平行投影
                        cone    - 透视投影
        """
        
        glcanvas.GLCanvas.__init__(self, parent, -1, style=glcanvas.WX_GL_RGBA|glcanvas.WX_GL_DOUBLEBUFFER|glcanvas.WX_GL_DEPTH_SIZE)
        
        self.bg = np.array(bg, dtype=np.float)                  # OpenGL窗口的背景色
        self.view = np.array(view, dtype=np.float)              # 视景体
        self.mode = mode                                        # 投影模式（平行投影/透视投影）
        self.eye = np.array(eye, dtype=np.float)                # 视点位置
        self.aim = np.array(aim, dtype=np.float)                # 视线方向参考点
        self.scale = np.array([1.0, 1.0, 1.0])                  # 模型矩阵缩放比例
        self.head = head                                        # 观察者头的指向
        self.up = None                                          # 向上的方向定义
        self.dist = None                                        # 视点与视线方向参考点之间的距离
        self.phi = None                                         # 仰角
        self.theta = None                                       # 方位角
        
        self.size = self.GetClientSize()                        # OpenGL窗口的大小
        self.context = glcanvas.GLContext(self)                 # OpenGL上下文
        
        self.x, self.y = None, None                             # 鼠标事件发生时的鼠标当前位置
        self.lastx, self.lasty = None, None                     # 最后一次记录的鼠标位置
        
        self.regions = dict()                                   # 存储视口设置信息
        self.buffers = dict()                                   # 存储GPU缓冲区数据对象
        
        self.getPosture()                                       # 计算up/dist/phi/theta
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
        self.x, self.y = self.lastx, self.lasty = evt.GetPosition()
        
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
            self.lastx, self.lasty = self.x, self.y
            self.x, self.y = evt.GetPosition()
            
            dy = self.y - self.lasty
            if 0.5*np.pi < self.phi < 1.5*np.pi:
                dx = self.x - self.lastx
            else:
                dx = self.lastx - self.x
            
            self.phi += 2*np.pi*dy/self.size[1]
            self.phi %= 2*np.pi
            self.theta += 2*np.pi*dx/self.size[0]
            self.theta %= 2*np.pi
            
            if self.head == 'y+':
                self.eye[1] = self.dist*np.sin(self.phi)
                r = self.dist*np.cos(self.phi)
                self.eye[0] = r*np.sin(self.theta)
                self.eye[2] = r*np.cos(self.theta)
            elif self.head == 'z+':
                self.eye[2] = self.dist*np.sin(self.phi)
                r = self.dist*np.cos(self.phi)
                self.eye[1] = r*np.sin(self.theta)
                self.eye[0] = r*np.cos(self.theta)
            elif self.head == 'x+':
                self.eye[0] = self.dist*np.sin(self.phi)
                r = self.dist*np.cos(self.phi)
                self.eye[2] = r*np.sin(self.theta)
                self.eye[1] = r*np.cos(self.theta)
            
            self.updateUP()
            self.Refresh(False)
        
    def onMouseWheel(self, evt):
        """响应鼠标滚轮事件"""
        
        if evt.WheelRotation > 0:
            self.scale *= 1.1
        elif evt.WheelRotation < 0:
            self.scale *= 0.9
        
        self.Refresh(False)
        
    def updateUP(self):
        """计算仰角或改变仰角时，重新定义向上的方向"""
        
        if 0.5*np.pi < self.phi < 1.5*np.pi:
            if self.head == 'x+':
                self.up = np.array([-1,0,0], dtype=np.float)
            elif self.head == 'x-':
                self.up = np.array([1,0,0], dtype=np.float)
            elif self.head == 'y+':
                self.up = np.array([0,-1,0], dtype=np.float)
            elif self.head == 'y-':
                self.up = np.array([0,1,0], dtype=np.float)
            elif self.head == 'z+':
                self.up = np.array([0,0,-1], dtype=np.float)
            elif self.head == 'z-':
                self.up = np.array([0,0,1], dtype=np.float)
        else:
            if self.head == 'x+':
                self.up = np.array([1,0,0], dtype=np.float)
            elif self.head == 'x-':
                self.up = np.array([-1,0,0], dtype=np.float)
            elif self.head == 'y+':
                self.up = np.array([0,1,0], dtype=np.float)
            elif self.head == 'y-':
                self.up = np.array([0,-1,0], dtype=np.float)
            elif self.head == 'z+':
                self.up = np.array([0,0,1], dtype=np.float)
            elif self.head == 'z-':
                self.up = np.array([0,0,-1], dtype=np.float)
        
    def getPosture(self):
        """计算仰角、方位角和视点与视线方向参考点之间的距离"""
        
        self.dist = np.sqrt(np.power((self.eye-self.aim), 2).sum())
        if self.dist > 0:
            if self.head == 'y+':
                self.phi = np.arcsin((self.eye[1]-self.aim[1])/self.dist)
                self.theta = np.arcsin((self.eye[0]-self.aim[0])/(self.dist*np.cos(self.phi)))
            elif self.head == 'z+':
                self.phi = np.arcsin((self.eye[2]-self.aim[2])/self.dist)
                self.theta = np.arcsin((self.eye[1]-self.aim[1])/(self.dist*np.cos(self.phi)))
            elif self.head == 'x+':
                self.phi = np.arcsin((self.eye[0]-self.aim[0])/self.dist)
                self.theta = np.arcsin((self.eye[2]-self.aim[2])/(self.dist*np.cos(self.phi)))
        else:
            self.phi = 0.0
            self.theta = 0.0
           
        self.updateUP()
        
    def initGL(self):
        """初始化GL"""
        
        self.SetCurrent(self.context)
        
        glClearColor(self.bg[0],self.bg[1],self.bg[2],self.bg[3])   # 设置画布背景色
        glEnable(GL_DEPTH_TEST)                                     # 开启深度测试，实现遮挡关系
        glDepthFunc(GL_LEQUAL)                                      # 设置深度测试函数
        glShadeModel(GL_SMOOTH)                                     # GL_SMOOTH(光滑着色)/GL_FLAT(恒定着色)
        glEnable(GL_BLEND)                                          # 开启混合
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)           # 设置混合函数
        glFrontFace(GL_CCW)                                         # 设置逆时针索引为正面（GL_CCW/GL_CW）
        
    def drawGL(self):
        """绘制"""
        
        width, height = self.size
        for key in self.regions:
            region = self.regions[key]
            x0, y0 = int(region.box[0]*width), int(region.box[1]*height)
            w, h = int(region.box[2]*width), int(region.box[3]*height)
            
            glViewport(x0, y0, w, h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            
            if isinstance(region.view, np.ndarray):
                view = region.view
            else:
                view = self.view
            
            if region.mode:
                mode = region.mode
            else:
                mode = self.mode
            
            if w > h:
                if mode == 'ortho':
                    glOrtho(view[0]*w/h, view[1]*w/h, view[2], view[3], view[4], view[5])
                else:
                    glFrustum(view[0]*w/h, view[1]*w/h, view[2], view[3], view[4], view[5])
            else:
                if mode == 'ortho':
                    glOrtho(view[0], view[1], view[2]*h/w, view[3]*h/w, view[4], view[5])
                else:
                    glFrustum(view[0], view[1], view[2]*h/w, view[3]*h/w, view[4], view[5])
            
            if isinstance(region.lookat, np.ndarray):
                gluLookAt(
                    region.lookat[0], region.lookat[1], region.lookat[2], 
                    region.lookat[3], region.lookat[4], region.lookat[5],
                    region.lookat[6], region.lookat[7], region.lookat[8]
                )
            else:
                gluLookAt(
                    self.eye[0], self.eye[1], self.eye[2], 
                    self.aim[0], self.aim[1], self.aim[2],
                    self.up[0], self.up[1], self.up[2]
                )
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            if isinstance(region.scale, np.ndarray):
                glScale(region.scale[0], region.scale[1], region.scale[2])
            else:
                glScale(self.scale[0], self.scale[1], self.scale[2])
            
            for item in region.assembly:
                item['cmd'](item['args'])
            
        
    def getMode(self):
        """获取投影模式"""
        
        return self.mode
        
    def setMode(self, mode_str):
        """设置投影模式"""
        
        assert mode_str in ['ortho', 'cone'], u'参数错误'
        
        self.mode = mode_str
        self.Refresh(False)
        
    def getView(self):
        """获取视景体"""
        
        return self.view
        
    def setView(self, view_list):
        """设置视景体"""
        
        if isinstance(view_list, list) and len(view_list) == 6:
            self.view = np.array(view_list, dtype=np.float)
        else:
            raise TypeError(u'参数类型错误')
            
        self.Refresh(False)
        
    def getEye(self):
        """获取视点位置"""
        
        return self.eye
        
    def setEye(self, eye_list):
        """设置视点位置"""
        
        if isinstance(eye_list, list) and len(eye_list) == 3:
            self.eye = np.array(eye_list, dtype=np.float)
        else:
            raise TypeError(u'参数类型错误')
        
        self.getPosture()
        self.Refresh(False)
        
    def getAim(self):
        """获取视线方向参考点位置"""
        
        return self.aim
        
    def setAim(self, aim_list):
        """设置视线方向参考点位置"""
        
        if isinstance(aim_list, list) and len(aim_list) == 3:
            self.aim = np.array(aim_list, dtype=np.float)
        else:
            raise TypeError(u'参数类型错误')
        
        self.getPosture()
        self.Refresh(False)
     
    def getHead(self):
        """获取观察者头部指向"""
        
        return self.head
        
    def setHead(self, head_str):
        """设置观察者头部指向"""
        
        assert head_str in ['x+', 'x-', 'y+', 'y-', 'z+', 'z-'], u'参数错误'
        
        self.head = head_str
        self.getPosture()
        self.Refresh(False)
        
    def getScale(self):
        """获取模型矩阵缩放比例"""
        
        return self.scale
        
    def setScale(self, scale_list):
        """设置视景体"""
        
        if isinstance(scale_list, list) and len(scale_list) == 3:
            self.scale = np.array(scale_list, dtype=np.float)
        else:
            raise TypeError(u'参数类型错误')
            
        self.Refresh(False)
        
    def addRegion(self, region_name, box, font, lookat=None, scale=None, view=None, mode=None):
        """添加视区"""
        
        region = GLRegion(self, region_name, box, font, lookat=lookat, scale=scale, view=view, mode=mode)
        self.regions.update({region_name: region})
        
        return region
        
    def delRegion(self, region_name):
        """删除视区"""
        
        self.regions.pop(region_name)
        
    def savePosture(self):
        """保存姿态"""
        
        pass
        
    def restorePosture(self):
        """还原姿态"""
        
        pass
        
    def screenshot(self, fn, alpha=True):
        """屏幕截图"""
        
        self.SwapBuffers()
        
        if alpha:
            gl_mode = GL_RGBA
            pil_mode = 'RGBA'
        else:
            gl_mode = GL_RGB
            pil_mode = 'RGB'
            
        data = glReadPixels(0, 0, self.size[0], self.size[1], gl_mode, GL_UNSIGNED_BYTE, outputType=None)
        img = Image.fromarray(data.reshape(data.shape[1], data.shape[0], -1), mode=pil_mode)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img.save(fn)
        