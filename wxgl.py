# -*- coding: utf-8 -*-


import wx
from wx import glcanvas
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *


class GLScene(glcanvas.GLCanvas):
    """GL场景类"""
    
    def __init__(self, parent, databox=None, bgColor=(1,1,1,1), isOrtho=True, view=(-3.2,3.2,-3.2,3.2,-15,15)):
        """
        构造函数
        
        bgColor     - OpenGL窗口的背景色，默认值为(1,1,1,1)
        isOrtho     - 布尔值，为真表示创建正交视景体，否则，创建透视视景体
        view        - 创建视景体的参数，自左至右分别是ledt/right/bottom/top/near/far，默认值为(-1,1,-1,1,-1,1)
        """
        
        glcanvas.GLCanvas.__init__(self, parent, -1, style=glcanvas.WX_GL_RGBA|glcanvas.WX_GL_DOUBLEBUFFER|glcanvas.WX_GL_DEPTH_SIZE)
        
        self.databox = databox
        self.bgColor = bgColor
        #self.isOrtho = isOrtho
        self.isOrtho = False
        #self.view = np.array(view)
        self.view = np.array((-0.5, 0.5, -0.5, 0.5, 1.0, 5.0))
        self.scale = np.array([1.0, 1.0, 1.0])
        self.eye = np.array([0.0, 0.2, 3.0])
        self.lookat = np.array([0.0, 0.0, 0.0])
        self.up = np.array([0.0, 1.0, 0.0])
        self.dist, self.phi, self.theta = self.getCamPosition()
        
        self.GLinitialized = False
        self.context = glcanvas.GLContext(self)
        self.size = self.GetClientSize()
        self.lastx = self.x = None
        self.lasty = self.y = None
        self.assembly = list()
        
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.Bind(wx.EVT_PAINT, self.onPaint)
        
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
        self.Bind(wx.EVT_RIGHT_UP, self.onRightUp)
        self.Bind(wx.EVT_MOTION, self.onMouseMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)
        
    def onEraseBackground(self, evt):
        """响应背景擦除事件"""
        
        pass
        
    def onResize(self, evt):
        """响应窗口尺寸改变事件"""
        
        if self.context:
            self.SetCurrent(self.context)
            self.size = self.GetClientSize()
            glViewport(0, 0, self.size[0], self.size[1])
            
        evt.Skip()
        
    def onPaint(self, evt):
        """响应重绘事件"""
        
        self.redraw()
        evt.Skip()
        
    def redraw(self):
        """重绘"""
        
        self.SetCurrent(self.context)
        if not self.GLinitialized:
            self.initGL()
            self.GLinitialized = True
        self.drawGL()
        self.SwapBuffers()
        
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
            
            dx = self.lastx - self.x
            dy = self.y - self.lasty
            
            self.phi += 2*np.pi*dy/self.size[1]
            self.phi %= 2*np.pi
            self.theta += 2*np.pi*dx/self.size[0]
            self.theta %= 2*np.pi
            
            self.eye[1] = self.dist*np.sin(self.phi)
            r = self.dist*np.cos(self.phi)
            self.eye[0] = r*np.sin(self.theta)
            self.eye[2] = r*np.cos(self.theta)
            
            if 0.5*np.pi < self.phi < 1.5*np.pi:
                self.up[1] = -1.0
            else:
                self.up[1] = 1.0
            
            self.Refresh(False)
        
    def onMouseWheel(self, evt):
        """响应鼠标滚轮事件"""
        
        if evt.WheelRotation > 0:
            self.scale *= 1.1
            self.redraw()
        elif evt.WheelRotation < 0:
            self.scale *= 0.9
            self.redraw()
        
    def getCamPosition(self):
        """计算眼睛和目标之间的距离、方位角和仰角"""
        
        dist = np.sqrt(np.power((self.eye-self.lookat), 2).sum())
        if dist > 0:
            phi = np.arcsin((self.eye[1]-self.lookat[1])/dist)
            theta = np.arcsin((self.eye[0]-self.lookat[0])/(dist*np.cos(phi)))
        else:
            phi = 0.0
            theta = 0.0
            
        return dist, phi, theta
        
    def initGL(self):
        """初始化GL"""
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT) # 清除屏幕及深度缓存
        glClearColor(self.bgColor[0], self.bgColor[1], self.bgColor[2], self.bgColor[3]) # 背景色填充
        
        glEnable(GL_DEPTH_TEST) # 开启深度测试，实现遮挡关系
        glDepthFunc(GL_LEQUAL) # 设置深度测试函数，GL_LEQUAL：在片段深度值小于等于缓冲区的深度值时通过测试
        
        #glEnable(GL_PERSPECTIVE_CORRECTION)
        #glHint(GL_PERSPECTIVE_CORRECTION_HINT,GL_NICEST) # 透视修正
        glEnable(GL_POLYGON_SMOOTH) # 开启多变形修正
        glEnable(GL_BLEND) # 开启混合
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE) # 设置混合因子
        glHint(GL_POLYGON_SMOOTH_HINT,GL_NICEST) # 多边形修正的行为控制
        
        #glEnable(GL_CULL_FACE) # 开启表面剔除，被剔除的表面将不被渲染
        #glCullFace(GL_BACK) # 参数可以是GL_FRONT，GL_BACK或者GL_FRONT_AND_BACK，分别表示剔除正面、剔除反面、剔除正反两面的多边形
        
        #glEnable(GL_BLEND) # 开启混合
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        #glEnable(GL_DEPTH_TEST)
        #glEnable(GL_COLOR_MATERIAL)
        #glEnable(GL_LIGHTING)
        
        self.initData()
        
    def drawGL(self):
        """绘制"""
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        width, height = self.size
        if width > height:
            if self.isOrtho:
                glOrtho(self.view[0]*width/height, self.view[1]*width/height, self.view[2], self.view[3], self.view[4], self.view[5])
            else:
                glFrustum(self.view[0]*width/height, self.view[1]*width/height, self.view[2], self.view[3], self.view[4], self.view[5])
        else:
            if self.isOrtho:
                glOrtho(self.view[0], self.view[1], self.view[2]*height/width, self.view[3]*height/width, self.view[4], self.view[5])
            else:
                glFrustum(self.view[0], self.view[1], self.view[2]*height/width, self.view[3]*height/width, self.view[4], self.view[5])
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        gluLookAt(
            self.eye[0], self.eye[1], self.eye[2], 
            self.lookat[0], self.lookat[1], self.lookat[2],
            self.up[0], self.up[1], self.up[2]
        )
        
        glScale(self.scale[0], self.scale[1], self.scale[2])
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT) # 清除屏幕及深度缓存
        
        for item in self.assembly:
            if item['cmd'] == 'glDrawElements':
                item['vbo'].bind()
                glInterleavedArrays(item['vertex_type'], 0, None)
                item['ebo'].bind()
                glDrawElements(item['gl_type'], int(item['ebo'].size/4), GL_UNSIGNED_INT, None) 
                item['vbo'].unbind()
                item['ebo'].unbind()
            else:
                item['cmd'](item['args'])
        
    def initData(self):
        """3D数据初始化(需要在派生类中重写)"""
        
        pass
     
    def wxglPolygonMode(self, args):
        """设置多边形模式：GL_POINT/GL_LINE/GL_FILL"""
        
        glPolygonMode(args[0], args[1])
     
    def wxglColor3f(self, args):
        """设置当前颜色：GL_POINT/GL_LINE/GL_FILL"""
        
        glColor3f(args[0],args[1],args[2])


if __name__ == "__main__":
    """测试代码"""
    
    class mainFrame(wx.Frame):
        """程序主窗口类，继承自wx.Frame"""

        def __init__(self):
            """构造函数"""

            wx.Frame.__init__(self, None, -1, u'WxGL项目演示', style=wx.DEFAULT_FRAME_STYLE)
            self.Maximize()
            
            demo = GLScene(self)

            panel_top = wx.Panel(self, -1)
            panel_top.SetBackgroundColour(wx.Colour(224, 224, 0))
            
            panel_left = wx.Panel(self, -1)
            panel_left.SetBackgroundColour(wx.Colour(224, 0, 224))
            
            panel_center = demo.canvas
            panel_center.SetBackgroundColour(wx.Colour(0, 224, 224))
            
            panel_right = wx.Panel(self, -1)
            panel_right.SetBackgroundColour(wx.Colour(224, 0, 0))
            
            panel_bottom = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
            panel_bottom.SetBackgroundColour(wx.Colour(0, 0, 224))
            
            sizer_mid = wx.BoxSizer()
            sizer_mid.Add(panel_left, 1, wx.EXPAND|wx.ALL, 0) 
            sizer_mid.Add(panel_center, 2, wx.EXPAND|wx.ALL, 0) 
            sizer_mid.Add(panel_right, 1, wx.EXPAND|wx.ALL, 0) 
            
            sizer_max = wx.BoxSizer(wx.VERTICAL) 
            sizer_max.Add(panel_top, 2, wx.EXPAND|wx.ALL, 0) 
            sizer_max.Add(sizer_mid, 5, wx.EXPAND|wx.ALL, 0) 
            sizer_max.Add(panel_bottom, 1, wx.EXPAND|wx.ALL, 0) 
            
            self.SetAutoLayout(True) 
            self.SetSizer(sizer_max) 
            self.Layout()


    app = wx.App()
    frame = mainFrame()
    frame.Show(True)
    app.MainLoop()
    