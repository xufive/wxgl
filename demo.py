# -*- coding: utf-8 -*-


import wx
import numpy as np
from OpenGL.GL import *
from OpenGL.arrays import vbo

from wxgl import *


class DemoScene(GLScene):
    """演示场景类"""
    
    def __init__(self, parent, databox=None):
        """构造函数"""
        
        GLScene.__init__(self, parent, databox=databox)
        
    def initData(self):
        """3D数据初始化(需要在派生类中重写)"""
        
        # 六面体数据
        # ------------------------------------------------------
        #    v4----- v5
        #   /|      /|
        #  v0------v1|
        #  | |     | |
        #  | v7----|-v6
        #  |/      |/
        #  v3------v2
        
        vertices_0 = np.array([
            -0.5, 0.5, 0.5,   0.5, 0.5, 0.5,   0.5, -0.5, 0.5,   -0.5, -0.5, 0.5, # v0-v1-v2-v3
			-0.5, 0.5, -0.5,  0.5, 0.5, -0.5,  0.5, -0.5, -0.5,  -0.5, -0.5, -0.5 # v4-v5-v6-v7
        ], dtype=np.float32)

        indices_0 = np.array([
            0, 1, 2, 3, # v0-v1-v2-v3 (front)
            4, 5, 1, 0, # v4-v5-v1-v0 (top)
            3, 2, 6, 7, # v3-v2-v6-v7 (bottom)
            5, 4, 7, 6, # v5-v4-v7-v6 (back)
            1, 5, 6, 2, # v1-v5-v6-v2 (right)
            4, 0, 3, 7  # v4-v0-v3-v7 (left)
        ], dtype=np.int)
        
        vertices_1 = np.array([
            0.3, 0.6, 0.9, -0.35, 0.35, 0.35,   # c0-v0
			0.6, 0.9, 0.3, 0.35, 0.35, 0.35,    # c1-v1
			0.9, 0.3, 0.6, 0.35, -0.35, 0.35,   # c2-v2 
			0.3, 0.9, 0.6, -0.35, -0.35, 0.35,  # c3-v3 
			0.6, 0.3, 0.9, -0.35, 0.35, -0.35,  # c4-v4 
			0.9, 0.6, 0.3, 0.35, 0.35, -0.35,   # c5-v5 
			0.3, 0.9, 0.9, 0.35, -0.35, -0.35,  # c6-v6 
			0.9, 0.9, 0.3, -0.35, -0.35, -0.35  # c7-v7
        ], dtype=np.float32)
        
        indices_1 = np.array([
            0, 1, 3, 1, 2, 3, # v0-v1-v3 v1-v2-v3 (front)
            4, 5, 0, 5, 1, 0, # v4-v5-v0 v5-v1-v0 (top)
            3, 2, 7, 2, 6, 7, # v3-v2-v7 v2-v6-v7 (bottom)
            5, 4, 6, 4, 7, 6, # v5-v4-v6 v4-v7-v6 (back)
            1, 5, 2, 5, 6, 2, # v1-v5-v2 v5-v6-v2 (right)
            4, 0, 7, 0, 3, 7  # v4-v0-v7 v0-v3-v7 (left)
        ], dtype=np.int)
        
        # 线数据
        # ------------------------------------------------------
        vertices_2 = np.array([[-0.7,0.7-i*0.01,-0.7,0.7,0.7-i*0.01,-0.7] for i in range(141)], dtype=np.float32).ravel() 
        
        indices_2 = np.array([i for i in range(282)], dtype=np.int)
        
        # 面数据
        # ------------------------------------------------------
        x = 0.8*np.ones((160,160))
        y, z = np.mgrid[-0.8:0.8:0.01, -0.8:0.8:0.01]
        c = np.random.random((160*160,3)).astype(np.float32)
        v = np.dstack((x,y,z)).astype(np.float32).reshape(160*160,3)
        vertices_3 = np.hstack((c,v))
        
        indices = list()
        for i in range(1, 160):
            for j in range(1,160):
                indices += [(i-1)*160+j-1, (i-1)*160+j, i*160+j, i*160+j-1]
        indices_3 = np.array(indices, dtype=np.int)
        
        x = -0.8*np.ones((1600,1600))
        y, z = np.mgrid[-0.8:0.8:0.001, -0.8:0.8:0.001]
        c = np.random.random((1600*1600,3)).astype(np.float32)
        v = np.dstack((x,y,z)).astype(np.float32).reshape(1600*1600,3)
        vertices_4 = np.hstack((c,v))
        
        indices = list()
        for i in range(1, 1600):
            for j in range(1,1600):
                indices += [(i-1)*1600+j-1, (i-1)*1600+j, i*1600+j, i*1600+j-1]
        indices_4 = np.array(indices, dtype=np.int)
        
        
        # 使用VBO将数据发送到GPU，描述组件
        # ------------------------------------------------------
        vbo_0 = vbo.VBO(vertices_0)
        vbo_1 = vbo.VBO(vertices_1)
        vbo_2 = vbo.VBO(vertices_2)
        vbo_3 = vbo.VBO(vertices_3)
        vbo_4 = vbo.VBO(vertices_4)
        ebo_0 = vbo.VBO(indices_0, target=GL_ELEMENT_ARRAY_BUFFER)
        ebo_1 = vbo.VBO(indices_1, target=GL_ELEMENT_ARRAY_BUFFER)
        ebo_2 = vbo.VBO(indices_2, target=GL_ELEMENT_ARRAY_BUFFER)
        ebo_3 = vbo.VBO(indices_3, target=GL_ELEMENT_ARRAY_BUFFER)
        ebo_4 = vbo.VBO(indices_4, target=GL_ELEMENT_ARRAY_BUFFER)
        
        self.assembly.append({'cmd':self.wxglColor3f, 'args':[1.0,0.0,0.0]})
        self.assembly.append({'cmd':self.wxglPolygonMode, 'args':[GL_FRONT_AND_BACK, GL_LINE]})
        self.assembly.append({'cmd':'glDrawElements', 'vbo':vbo_0, 'ebo':ebo_0, 'vertex_type':GL_V3F, 'gl_type':GL_QUADS})
        self.assembly.append({'cmd':self.wxglPolygonMode, 'args':[GL_FRONT_AND_BACK, GL_FILL]})
        self.assembly.append({'cmd':'glDrawElements', 'vbo':vbo_1, 'ebo':ebo_1, 'vertex_type':GL_C3F_V3F, 'gl_type':GL_TRIANGLES})
        self.assembly.append({'cmd':self.wxglColor3f, 'args':[0.0,1.0,0.0]})
        self.assembly.append({'cmd':'glDrawElements', 'vbo':vbo_2, 'ebo':ebo_2, 'vertex_type':GL_V3F, 'gl_type':GL_LINES})
        self.assembly.append({'cmd':self.wxglPolygonMode, 'args':[GL_FRONT_AND_BACK, GL_LINE]})
        self.assembly.append({'cmd':'glDrawElements', 'vbo':vbo_3, 'ebo':ebo_3, 'vertex_type':GL_C3F_V3F, 'gl_type':GL_QUADS})
        self.assembly.append({'cmd':self.wxglPolygonMode, 'args':[GL_FRONT_AND_BACK, GL_FILL]})
        self.assembly.append({'cmd':'glDrawElements', 'vbo':vbo_4, 'ebo':ebo_4, 'vertex_type':GL_C3F_V3F, 'gl_type':GL_QUADS})
        

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
    