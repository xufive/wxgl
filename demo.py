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
        
    def drawGL(self):
        """重写GL绘制方法"""
        
        vertexes_0 = np.array([
            -0.5, 0.5, 0.5,
			0.5, 0.5, 0.5,
			0.5, -0.5, 0.5,
			-0.5, -0.5, 0.5,
			-0.5, 0.5, -0.5,
			0.5, 0.5, -0.5,
			0.5, -0.5, -0.5,
			-0.5, -0.5, -0.5
        ])

        indexes_0 = np.array([
            0, 1, 2, 3,
            4, 5, 1, 0,
            3, 2, 6, 7,
            5, 4, 7, 6,
            1, 5, 6, 2,
            4, 0, 3, 7
        ], dtype=np.int)
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT) # 清除屏幕及深度缓存
        
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glColor3f(1.0,0.0,0.0)
        
        # ---------------------------------------------------
        vao_1 = glGenVertexArrays(1)
        glBindVertexArray(vao_1)
        
        indexes = (c_uint*len(indexes_0))(*indexes_0)
        ebo_index = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_index)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indexes, GL_STATIC_DRAW)
        #glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        
        vertexes = (c_float*len(vertexes_0))(*vertexes_0)
        vbo_vertex = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_vertex)
        glBufferData(GL_ARRAY_BUFFER, vertexes, GL_STATIC_DRAW)
        #glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        #glBindBuffer(GL_ARRAY_BUFFER, vbo_vertex)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        #glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        glBindVertexArray(0)
        
        # ---------------------------------------------------
        vao_2 = glGenVertexArrays(1)
        glBindVertexArray(vao_2)
        
        indexes = (c_uint*len(indexes_0))(*indexes_0)
        ebo_index = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_index)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indexes, GL_STATIC_DRAW)
        #glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        
        vertexes = 0.5 * vertexes_0
        vertexes = (c_float*len(vertexes))(*vertexes)
        vbo_vertex = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_vertex)
        glBufferData(GL_ARRAY_BUFFER, vertexes, GL_STATIC_DRAW)
        #glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        #glBindBuffer(GL_ARRAY_BUFFER, vbo_vertex)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        #glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        glBindVertexArray(0)
        
        # --------------------------------------------------
        glBindVertexArray(vao_1)
        glDrawElements(GL_QUADS, 24, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        glColor3f(0.0,0.0,1.0)
        
        glBindVertexArray(vao_2)
        glDrawElements(GL_QUADS, 24, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)


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
    