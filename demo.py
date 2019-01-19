# -*- coding: utf-8 -*-


import wx
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo
from ctypes import sizeof, c_float, c_void_p, c_uint, string_at

from wxgl import *


class DemoScene(GLScene):
    """演示场景类"""
    
    def __init__(self, parent, databox=None):
        """构造函数"""
        
        GLScene.__init__(self, parent, databox=databox)
        
    def initData(self):
        """3D数据初始化(需要在派生类中重写)"""
        
        #    v4----- v5
        #   /|      /|
        #  v0------v1|
        #  | |     | |
        #  | v7----|-v6
        #  |/      |/
        #  v3------v2
        
        vertex_0 = np.array([
            -0.5, 0.5, 0.5,
			0.5, 0.5, 0.5,
			0.5, -0.5, 0.5,
			-0.5, -0.5, 0.5,
			-0.5, 0.5, -0.5,
			0.5, 0.5, -0.5,
			0.5, -0.5, -0.5,
			-0.5, -0.5, -0.5
        ], dtype=np.float32)

        face_0 = np.array([
            0, 1, 2, 3,
            4, 5, 1, 0,
            3, 2, 6, 7,
            5, 4, 7, 6,
            1, 5, 6, 2,
            4, 0, 3, 7
        ], dtype=np.int)
        
        vertex_1 = np.array([
            0.3, 0.6, 0.9, -0.35, 0.35, 0.35, 
			0.6, 0.9, 0.3, 0.35, 0.35, 0.35, 
			0.9, 0.3, 0.6, 0.35, -0.35, 0.35, 
			0.3, 0.9, 0.6, -0.35, -0.35, 0.35, 
			0.6, 0.3, 0.9, -0.35, 0.35, -0.35, 
			0.9, 0.6, 0.3, 0.35, 0.35, -0.35, 
			0.3, 0.9, 0.9, 0.35, -0.35, -0.35, 
			0.9, 0.9, 0.3, -0.35, -0.35, -0.35
        ], dtype=np.float32)
        
        face_1 = np.array([
            0, 1, 3, 1, 2, 3,
            4, 5, 0, 5, 1, 0,
            3, 2, 7, 2, 6, 7,
            5, 4, 6, 4, 7, 6,
            1, 5, 2, 5, 6, 2,
            4, 0, 7, 0, 3, 7
        ], dtype=np.int)
        
        vbo_0 = vbo.VBO(vertex_0)
        vbo_1 = vbo.VBO(vertex_1)
        ebo_0 = vbo.VBO(face_0, target=GL_ELEMENT_ARRAY_BUFFER)
        ebo_1 = vbo.VBO(face_1, target=GL_ELEMENT_ARRAY_BUFFER)
        
        #self.assembly.append({'cmd':self.wxglColor3f, 'args':[1.0,0.0,0.0]})
        #self.assembly.append({'cmd':self.wxglPolygonMode, 'args':[GL_FRONT_AND_BACK, GL_LINE]})
        #self.assembly.append({'cmd':'glDrawElements', 'vbo':vbo_0, 'ebo':ebo_0, 'vertex_type':GL_V3F, 'gl_type':GL_QUADS})
        #self.assembly.append({'cmd':self.wxglPolygonMode, 'args':[GL_FRONT_AND_BACK, GL_FILL]})
        #self.assembly.append({'cmd':'glDrawElements', 'vbo':vbo_1, 'ebo':ebo_1, 'vertex_type':GL_C3F_V3F, 'gl_type':GL_TRIANGLES})
        
        self.assembly = {'vbo_0':vbo_0, 'vbo_1':vbo_1, 'ebo_0':ebo_0, 'ebo_1':ebo_1}
        
    def drawGL(self):
        """重写GL绘制方法"""
        
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
                
        #self.assembly.append({'cmd':self.wxglColor3f, 'args':[1.0,0.0,0.0]})
        #self.assembly.append({'cmd':self.wxglPolygonMode, 'args':[GL_FRONT_AND_BACK, GL_LINE]})
        #self.assembly.append({'cmd':'glDrawElements', 'vbo':vbo_0, 'ebo':ebo_0, 'vertex_type':GL_V3F, 'gl_type':GL_QUADS})
        #self.assembly.append({'cmd':self.wxglPolygonMode, 'args':[GL_FRONT_AND_BACK, GL_FILL]})
        #self.assembly.append({'cmd':'glDrawElements', 'vbo':vbo_1, 'ebo':ebo_1, 'vertex_type':GL_C3F_V3F, 'gl_type':GL_TRIANGLES})
        
        glColor3f(1.0,0.0,0.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        
        self.assembly['vbo_0'].bind()
        glInterleavedArrays(GL_V3F, 0, None)
        self.assembly['ebo_0'].bind()
        glDrawElements(GL_QUADS, int(self.assembly['ebo_0'].size/4), GL_UNSIGNED_INT, None) 
        self.assembly['vbo_0'].unbind()
        self.assembly['ebo_0'].unbind()
        
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        self.assembly['vbo_1'].bind()
        glInterleavedArrays(GL_C3F_V3F, 0, None)
        self.assembly['ebo_1'].bind()
        glDrawElements(GL_TRIANGLES, int(self.assembly['ebo_1'].size/4), GL_UNSIGNED_INT, None) 
        self.assembly['vbo_1'].unbind()
        self.assembly['ebo_1'].unbind()
        

class mainFrame(wx.Frame):
    """程序主窗口类，继承自wx.Frame"""

    def __init__(self):
        """构造函数"""

        wx.Frame.__init__(self, None, -1, u'WxGL项目演示', style=wx.DEFAULT_FRAME_STYLE)
        self.Maximize()
        
        demo_center = DemoScene(self)

        panel_top = wx.Panel(self, -1)
        panel_top.SetBackgroundColour(wx.Colour(224, 224, 0))
        
        panel_left = wx.Panel(self, -1)
        panel_left.SetBackgroundColour(wx.Colour(224, 0, 224))
        
        panel_center = demo_center
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


if __name__ == "__main__":
    """测试代码"""
    
    app = wx.App()
    frame = mainFrame()
    frame.Show(True)
    app.MainLoop()
    